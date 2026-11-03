"""Offline estimate of how long a walk across each island takes (CLAUDE.md 5.1 and 5.7: 6-17 minutes, preferably in every
direction), from the terrain the world is generated from (world_terrain.height). Plain Python, no Unreal:
    python Scripts/Setup/estimate_walking_times.py [island keys...]

The quickest path on a 10 m grid from one shore to the opposite one, along the island's long axis and across it: a step
is walkable when its slope is under WALKABLE degrees (the character's walkable floor is 44.76 degrees; the grid smooths
the 3 m terrain mesh, so the limit here is lower), water below the sea surface is swum at SWIM_SPEED, and flat ground is
walked at WALK_SPEED. A screening tool before the expensive world rebuild; the in-game measurement
(Scripts/Verification/measure_walking_routes_play.py) is the evidence.
"""
import heapq
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W   # noqa: E402
import world_terrain as T  # noqa: E402

CELL = 1000.0           # cm
WALKABLE = 38.0         # degrees
WALK_SPEED = 450.0      # cm/s on open ground (measured October-November: 4-5 m/s in a straight line)
SWIM_SPEED = 250.0      # cm/s
INSET = 2000.0          # cm inland of the shore where a route starts and ends (as measure_walking_routes_play.py)
TARGET_MINUTES = (6.0, 17.0)
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
    """(seconds, path) along the quickest walkable path, the path as world (x, y) points every CELL; (None, []) when no
    path joins them on the island."""
    reach = island.reach() + 2 * CELL
    n = int(2 * reach / CELL) + 1
    x0, y0 = island.cx - reach, island.cy - reach
    heights = {}

    def z(i, j):
        key = (i, j)
        if key not in heights:
            x, y = x0 + i * CELL, y0 + j * CELL
            heights[key] = T.height(x, y) if island.distance(x, y) < 0 else None    # off the island: no route
        return heights[key]

    def cell(p):
        return (round((p[0] - x0) / CELL), round((p[1] - y0) / CELL))

    def on_land(c):
        """The nearest cell to c that is dry land on the island (a route end can sit by an inlet)."""
        for radius in range(0, 12):
            ring = [(c[0] + di, c[1] + dj) for di in range(-radius, radius + 1) for dj in range(-radius, radius + 1)
                    if max(abs(di), abs(dj)) == radius]
            dry = [r for r in ring if z(*r) is not None and z(*r) > T.SEA]
            if dry:
                return min(dry, key=lambda r: math.hypot(r[0] - c[0], r[1] - c[1]))
        return c

    s, e = on_land(cell(start)), on_land(cell(end))
    best = {s: 0.0}
    came = {}
    queue = [(0.0, s)]
    limit = math.tan(math.radians(WALKABLE))
    steps = [(di, dj) for di in (-1, 0, 1) for dj in (-1, 0, 1) if di or dj]
    while queue:
        t, (i, j) = heapq.heappop(queue)
        if (i, j) == e:
            path, at = [], e
            while at in came or at == s:
                path.append((x0 + at[0] * CELL, y0 + at[1] * CELL))
                if at == s:
                    break
                at = came[at]
            return t, path[::-1]
        if t > best.get((i, j), 1e18):
            continue
        here = z(i, j)
        if here is None:
            continue
        for di, dj in steps:
            ni, nj = i + di, j + dj
            if not (0 <= ni < n and 0 <= nj < n):
                continue
            there = z(ni, nj)
            if there is None:
                continue
            run = CELL * math.hypot(di, dj)
            wet = max(here, there) < T.SEA
            if not wet and abs(there - here) / run > limit:
                continue
            nt = t + run / (SWIM_SPEED if wet else WALK_SPEED)
            if nt < best.get((ni, nj), 1e18):
                best[(ni, nj)] = nt
                came[(ni, nj)] = (i, j)
                heapq.heappush(queue, (nt, (ni, nj)))
    return None, []


def estimate(keys=None):
    result = {}
    for island in W.ISLANDS:
        if keys and island.key not in keys:
            continue
        result[island.key] = {}
        for name, start, end in routes(island):
            t, _ = walk_time(island, start, end)
            result[island.key][name] = None if t is None else round(t / 60.0, 1)
    return result


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
