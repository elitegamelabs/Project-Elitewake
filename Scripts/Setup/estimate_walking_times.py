"""Offline estimate of how long a walk across each compact island takes. The owner accepted the current
roughly 5-14 minute scale on November 3; this screen allows a little measurement variation without resizing islands.
Plain Python, no Unreal:
    python Scripts/Setup/estimate_walking_times.py [island keys...]

The quickest path from one shore to the opposite one, along the island's long axis and across it, on the island mesh's own
grid (world_terrain.GRIDS: 3-4 m between vertices, the heights the game's ground has): a step between neighbouring vertices
is walkable when its slope is under WALKABLE degrees (the character's walkable floor is 44.76); water below the sea surface
is swum at SWIM_SPEED, and a swimmer climbs out only where the bank stands no more than STEP_OUT above the water (the
character's 45 cm step); flat ground is walked at WALK_SPEED. Route ends slide to the nearest dry ground. Trees and rocks
are not counted. A screening tool before the expensive world rebuild, run one island per process; it also writes the paths
to Saved/WalkingPaths.json for the in-game measurement (Scripts/Verification/measure_walking_routes_play.py), which walks
them and is the evidence.
"""
import hashlib
import heapq
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W   # noqa: E402
import world_terrain as T  # noqa: E402

WALKABLE = 44.0         # degrees: just under the character's walkable floor
STEP_OUT = 45.0         # cm: the highest bank a swimmer climbs out onto
WALK_SPEED = 450.0      # cm/s on open ground (measured October-November: 4-5 m/s in a straight line)
SWIM_SPEED = 250.0      # cm/s
INSET = 2000.0          # cm inland of the shore where a route starts and ends (as measure_walking_routes_play.py)
TARGET_MINUTES = (4.0, 16.0)
PATHS = Path(__file__).resolve().parents[2] / 'Saved' / 'WalkingPaths.json'


def signature():
    """What the paths were worked out from: the layout and terrain sources."""
    here = Path(__file__).resolve().parent
    digest = hashlib.sha1()
    for name in ('world_layout.py', 'world_terrain.py', 'world_islands.py', 'estimate_walking_times.py'):
        digest.update((here / name).read_bytes())
    return digest.hexdigest()


# The starter island keeps its exact shape (Saltreach, the arrival). Its across route starts beside a cove inlet here; in
# game it measured 6.65 min along and 6.2 min across (November 1), so it is reported, not judged.
KEPT = {'Starter'}


def centroid(island):
    pts = island.outline(240)
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def reach(island, x, y, angle):
    """From (x, y), how far along angle the land runs (stopping INSET short of the shore), cm."""
    c, s, d = math.cos(angle), math.sin(angle), 0.0
    while island.distance(x + (d + 500) * c, y + (d + 500) * s) < -INSET:
        d += 500
    return d


def routes(island):
    """(name, start, end): coast to coast along the island's longest axis through its middle, and across it at right
    angles. The in-game measurement walks the same routes (measure_walking_routes_play.py)."""
    x, y = centroid(island)
    a = max((math.pi * k / 72 for k in range(72)), key=lambda t: reach(island, x, y, t) + reach(island, x, y, t + math.pi))
    out = []
    for name, angle in (('long axis', a), ('across', a + math.pi / 2)):
        r1, r2 = reach(island, x, y, angle), reach(island, x, y, angle + math.pi)
        c, s = math.cos(angle), math.sin(angle)
        out.append((name, (x + r1 * c, y + r1 * s), (x - r2 * c, y - r2 * s)))
    return out


def walk_time(island, start, end):
    """(seconds, path) along the quickest walkable path on the island mesh's grid, the path as world (x, y) points, one per
    vertex; (None, []) when no path joins them."""
    x0, y0, sx, sy, nx, ny = T.GRIDS[island.key]
    heights = {}

    def z(i, j):
        key = i * (ny + 1) + j
        h = heights.get(key)
        if h is None:
            h = heights[key] = T.height(x0 + i * sx, y0 + j * sy)
        return h

    def on_land(p):
        """The nearest dry vertex to p (a route end can sit by an inlet or on a beach below a cliff)."""
        ci, cj = round((p[0] - x0) / sx), round((p[1] - y0) / sy)
        for radius in range(0, 40):
            ring = [(ci + di, cj + dj) for di in range(-radius, radius + 1) for dj in range(-radius, radius + 1)
                    if max(abs(di), abs(dj)) == radius and 0 <= ci + di <= nx and 0 <= cj + dj <= ny]
            dry = [c for c in ring if z(*c) > T.SEA]
            if dry:
                return min(dry, key=lambda c: (c[0] - ci) ** 2 + (c[1] - cj) ** 2)
        return ci, cj

    s0, e0 = on_land(start), on_land(end)
    s_key, e_key = s0[0] * (ny + 1) + s0[1], e0[0] * (ny + 1) + e0[1]
    best = {s_key: 0.0}
    came = {}
    queue = [(0.0, s0[0], s0[1])]
    limit = math.tan(math.radians(WALKABLE))
    steps = [(di, dj, math.hypot(di * sx, dj * sy)) for di in (-1, 0, 1) for dj in (-1, 0, 1) if di or dj]
    while queue:
        t, i, j = heapq.heappop(queue)
        key = i * (ny + 1) + j
        if key == e_key:
            path, at = [], key
            while True:
                path.append((x0 + (at // (ny + 1)) * sx, y0 + (at % (ny + 1)) * sy))
                if at == s_key:
                    break
                at = came[at]
            return t, path[::-1]
        if t > best.get(key, 1e18):
            continue
        here = z(i, j)
        for di, dj, run in steps:
            ni, nj = i + di, j + dj
            if not (0 <= ni <= nx and 0 <= nj <= ny):
                continue
            there = z(ni, nj)
            wet_here, wet_there = here < T.SEA, there < T.SEA
            if wet_here and wet_there:
                speed = SWIM_SPEED
            elif wet_here:
                if there - T.SEA > STEP_OUT:
                    continue                          # a bank too high to climb out onto
                speed = SWIM_SPEED
            elif wet_there:
                speed = SWIM_SPEED                    # into the water: always possible
            else:
                if abs(there - here) / run > limit:
                    continue
                speed = WALK_SPEED
            nt = t + run / speed
            nkey = ni * (ny + 1) + nj
            if nt < best.get(nkey, 1e18):
                best[nkey] = nt
                came[nkey] = key
                heapq.heappush(queue, (nt, ni, nj))
    return None, []


def _island_routes(key):
    island = W.island(key)
    out = {}
    for name, start, end in routes(island):
        t, path = walk_time(island, start, end)
        out[name] = {'minutes': None if t is None else round(t / 60.0, 1), 'start': start, 'end': end,
                     'path': [[round(x), round(y)] for x, y in path[::3]] + ([[round(path[-1][0]), round(path[-1][1])]] if path else [])}
    return key, out


def estimate(keys=None, workers=8):
    """Every island's routes, one island per process; writes the paths for the in-game walk."""
    keys = [i.key for i in W.ISLANDS if not keys or i.key in keys]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        found = dict(pool.map(_island_routes, keys))
    if len(keys) == len(W.ISLANDS):
        PATHS.write_text(json.dumps({'signature': signature(), 'routes': found}))
    return {k: {name: r['minutes'] for name, r in v.items()} for k, v in found.items()}


def saved_paths():
    """The paths written by the last full estimate, if the layout and terrain have not changed since."""
    try:
        data = json.loads(PATHS.read_text())
    except (OSError, ValueError):
        return None
    return data['routes'] if data.get('signature') == signature() else None


def judge(minutes):
    if minutes is None:
        return 'BLOCKED'
    return 'ok' if TARGET_MINUTES[0] <= minutes <= TARGET_MINUTES[1] else ('short' if minutes < TARGET_MINUTES[0] else 'long')


if __name__ == '__main__':
    found = estimate(sys.argv[1:] or None)
    bad = 0
    for key, r in found.items():
        verdicts = {name: 'kept' if key in KEPT else judge(m) for name, m in r.items()}
        bad += sum(v not in ('ok', 'kept') for v in verdicts.values())
        print(f'{key:9s} ' + '  '.join(f'{name:9s} {r[name] if r[name] is not None else "-":>5} min {verdicts[name]:7s}' for name in r))
    out = Path(__file__).resolve().parents[2] / 'Saved' / 'WalkingTimeEstimate.json'
    out.write_text(json.dumps(found, indent=2))
    print('PASS' if not bad else f'{bad} route(s) outside {TARGET_MINUTES[0]:.0f}-{TARGET_MINUTES[1]:.0f} minutes')
    sys.exit(1 if bad else 0)
