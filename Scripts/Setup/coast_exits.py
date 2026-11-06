"""Where a swimmer can climb out of the sea onto each island, and where the coast traps them (owner, November 5: add
climb-out points; a swimmer should never be stuck against a steep shore). Plain Python, no Unreal:
    python Scripts/Setup/coast_exits.py [island keys...]          # prints every trapped stretch; exit code 1 if any
    python Scripts/Setup/coast_exits.py --plan [island keys...]   # places climb-outs, writes world_climbouts.py

On the island mesh's own grid (world_terrain.GRIDS, the heights the game's ground has): dry ground is walkable between
neighbouring vertices up to WALKABLE degrees (under the character's 44.76 degree floor, because the mesh's triangles run
steeper than its grid edges; the in-game walk of November 5 stalled on 45-51 degree faces where the edges read 44). A
swimmer climbs out where a bank vertex stands no more than STEP_OUT above the sea and joins the island's main walkable
ground. Every sea vertex along the coast must lie within EXIT_SWIM of such a climb-out, swimming. Inland ponds,
Saltreach's harbour (its piers have ladders and a slipway) and the sea caverns' pools (their walkways are checked in
Play) are not part of this test.

The planner (DECIDED, November 5, delegated): while any of an island's coast is trapped, it takes the farthest-trapped
stretch and traces climb-outs (world_terrain.Climb, `trace`) from its middle and the coast round it, setting off from
straight inland to nearly along the shore, and keeps the one that needs the least rock cut. A path turns step by step
towards ground a little above its own rising surface, so up a cliff face it becomes a ledge along the face; where a
sheer plateau rim leaves no ledge it cuts a ravine. It ends on ground a survivor can walk on that joins the island's
main ground (checked again 12 m on), or where it meets another climb-out at that one's height. Paths never run over
open water, never fill more than CLIMB_FILL or cut more than CLIMB_CUT, keep CLIMB_APART from each other and off caves
and Ports. Round by round the coast is surveyed again with every path cut in; a path that no longer works (another's
cut can leave its top on a cut-off ledge) is dropped and its place tried again.
"""
import heapq
import json
import math
import sys
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W   # noqa: E402
import world_terrain as T  # noqa: E402

WALKABLE = 38.0          # degrees between grid vertices
STEP_OUT = 45.0          # cm: the character's step
EXIT_SWIM = 15000.0      # cm: the farthest a swimmer along any coast should have to swim to a climb-out: a minute at 2.5 m/s (tuning)
BAND = 9000.0            # cm either side of the shore that the test looks at (the main ground is joined through it)
HARBOUR = 25000.0        # cm round a Port's middle left to its piers' ladders and slipway
CLIMB_MAX = 40000.0      # cm: the longest climb-out
CLIMB_CUT = 10000.0      # cm: the deepest cut along a climb-out's line (a ravine into a sheer plateau rim, where no ledge fits)
CLIMB_FILL = 800.0       # cm: the most it may be built up (a buttressed ledge across a sheer face)
OUT = Path(__file__).resolve().parent / 'world_climbouts.py'


class Coast:
    """One island's grid round its shore, with heights from `height` (world_terrain.height by default)."""

    def __init__(self, key, height=None):
        height = height or T.height
        self.island = island = W.island(key)
        x0, y0, sx, sy, nx, ny = T.GRIDS[key]
        self.x0, self.y0, self.sx, self.sy, self.nx, self.ny = x0, y0, sx, sy, nx + 1, ny + 1
        n = self.nx * self.ny
        self.band = band = bytearray(n)
        self.h = h = [0.0] * n
        for i in range(self.nx):
            x = x0 + i * sx
            for j in range(self.ny):
                y = y0 + j * sy
                if abs(island.distance(x, y)) <= BAND:
                    k = i * self.ny + j
                    band[k] = 1
                    h[k] = height(x, y)
        self.steps = [(di, dj, math.hypot(di * sx, dj * sy)) for di in (-1, 0, 1) for dj in (-1, 0, 1) if di or dj]
        self._sea()
        self._ground()
        self._coast()
        self.dist = [math.inf] * n
        self._swim([k for k in range(n) if self.exit[k]])

    def xy(self, k):
        i, j = divmod(k, self.ny)
        return self.x0 + i * self.sx, self.y0 + j * self.sy

    def vertex(self, x, y):
        i, j = round((x - self.x0) / self.sx), round((y - self.y0) / self.sy)
        return i * self.ny + j if 0 <= i < self.nx and 0 <= j < self.ny else None

    def on_main(self, x, y):
        """Whether the vertex nearest (x, y) and all round it lie on the island's main walkable ground."""
        k = self.vertex(x, y)
        return k is not None and self.comp[k] in self.main and all(self.comp[m] in self.main for m, _ in self.neighbours(k))

    def works(self, points):
        """Whether a climb-out's foot has a step-out from the sea and its top lies on the main ground."""
        foot = self.vertex(*points[0])
        near = [foot] + [m for m, _ in self.neighbours(foot)] if foot is not None else []
        near += [n for m in near for n, _ in self.neighbours(m)]
        top = self.vertex(*points[-1])
        return any(self.exit[m] for m in near) and top is not None and self.comp[top] in self.main

    def neighbours(self, k):
        i, j = divmod(k, self.ny)
        for di, dj, run in self.steps:
            a, b = i + di, j + dj
            if 0 <= a < self.nx and 0 <= b < self.ny:
                m = a * self.ny + b
                if self.band[m]:
                    yield m, run

    def _sea(self):
        """Water joined to the band's outer edge (inland ponds and lakes are left out)."""
        h, n = self.h, len(self.h)
        self.sea = sea = bytearray(n)
        queue = deque()
        for k in range(n):
            if self.band[k] and h[k] < T.SEA and self.island.distance(*self.xy(k)) > BAND - 2 * max(self.sx, self.sy):
                sea[k] = 1
                queue.append(k)
        while queue:
            k = queue.popleft()
            for m, _ in self.neighbours(k):
                if not sea[m] and h[m] < T.SEA:
                    sea[m] = 1
                    queue.append(m)

    def _ground(self):
        """The island's main walkable ground: the largest set of dry vertices joined by walkable steps."""
        h, n = self.h, len(self.h)
        limit = math.tan(math.radians(WALKABLE))
        self.comp = comp = [0] * n
        sizes = [0]
        queue = deque()
        for k in range(n):
            if self.band[k] and h[k] >= T.SEA and not comp[k]:
                label = len(sizes)
                sizes.append(0)
                comp[k] = label
                queue.append(k)
                while queue:
                    a = queue.popleft()
                    sizes[label] += 1
                    for m, run in self.neighbours(a):
                        if not comp[m] and h[m] >= T.SEA and abs(h[m] - h[a]) / run <= limit:
                            comp[m] = label
                            queue.append(m)
        # The band is a ring round the shore, so the main ground may reach it in several pieces: every piece that runs on
        # inland past the band's inner edge counts, and the largest piece in any case.
        self.main = {max(range(1, len(sizes)), key=lambda c: sizes[c])} if len(sizes) > 1 else set()
        edge = BAND - 2 * max(self.sx, self.sy)
        for k in range(n):
            if comp[k] and comp[k] not in self.main and self.island.distance(*self.xy(k)) < -edge:
                self.main.add(comp[k])

    def _coast(self):
        h, n = self.h, len(self.h)
        caves = [c for c in T.CAVES.values() if c and c.island is self.island and c.kind == 'sea']
        port = W.port_on(self.island)
        self.exit = bytearray(n)
        self.coast = []
        for k in range(n):
            if not self.sea[k]:
                continue
            near_land = False
            for m, _ in self.neighbours(k):
                if h[m] >= T.SEA:
                    near_land = True
                    if self.comp[m] in self.main and h[m] - T.SEA <= STEP_OUT:
                        self.exit[k] = 1
            if not near_land:
                continue
            x, y = self.xy(k)
            if any(c.inside(x, y) and c.local(x, y)[0] >= 0 for c in caves):
                continue
            if port and math.hypot(x - port.cx, y - port.cy) < HARBOUR:
                continue
            self.coast.append(k)

    def _swim(self, sources):
        """Lower each sea vertex's swim to a climb-out with new climb-outs at `sources`."""
        dist, heap = self.dist, []
        for k in sources:
            if dist[k] > 0.0:
                dist[k] = 0.0
            heap.append((0.0, k))
        heapq.heapify(heap)
        while heap:
            d, k = heapq.heappop(heap)
            if d > dist[k]:
                continue
            for m, run in self.neighbours(k):
                if self.sea[m] and d + run < dist[m]:
                    dist[m] = d + run
                    heapq.heappush(heap, (d + run, m))

    def trapped(self):
        return [k for k in self.coast if self.dist[k] > EXIT_SWIM]

    def stretches(self):
        """Runs of trapped coast: their middle (x, y), length along the coast in m, farthest swim in m (None when no
        climb-out is reachable at all)."""
        trapped = set(self.trapped())
        out, seen = [], set()
        for k in trapped:
            if k in seen:
                continue
            group, queue = [], deque([k])
            seen.add(k)
            while queue:
                a = queue.popleft()
                group.append(a)
                i, j = divmod(a, self.ny)
                for di in range(-3, 4):
                    for dj in range(-3, 4):
                        m = (i + di) * self.ny + j + dj
                        if m in trapped and m not in seen:
                            seen.add(m)
                            queue.append(m)
            pts = [self.xy(a) for a in group]
            worst = max(self.dist[a] for a in group)
            out.append({'at': (round(sum(p[0] for p in pts) / len(pts)), round(sum(p[1] for p in pts) / len(pts))),
                        'length_m': round(len(group) * (self.sx + self.sy) / 2 / 100.0),
                        'worst_swim_m': None if worst == math.inf else round(worst / 100.0)})
        return sorted(out, key=lambda s: -s['length_m'])

    def report(self):
        finite = [self.dist[k] for k in self.coast if self.dist[k] < math.inf]
        return {'island': self.island.key, 'coast': len(self.coast), 'trapped': self.stretches(),
                'worst_swim_m': round(max(finite) / 100.0) if finite else None,
                'unreachable': sum(1 for k in self.coast if self.dist[k] == math.inf)}


def survey(key):
    return Coast(key).report()


def survey_all(keys=None, workers=8):
    keys = [i.key for i in W.ISLANDS if not keys or i.key in keys]
    with ProcessPoolExecutor(max_workers=min(workers, len(keys))) as pool:
        return list(pool.map(survey, keys))


# ---- Planning ---------------------------------------------------------------------------------------------------

def _clear_site(island, x, y):
    if W.near_port(x, y, 3000.0) or T.near_cave(x, y, 1500.0):
        return False
    return True


def trace(coast, x, y, heading, avoid=()):
    """A climb-out from the water at (x, y) setting off along heading, as (cost, points), or None.
    Step by step it turns towards the ground that lies a little above the path's own rising surface, so up a cliff face it
    becomes a ledge along the face rather than a trench into it, until it meets ground a survivor can walk on."""
    island, ground = coast.island, T.height       # with the climb-outs placed so far cut in
    c, s = math.cos(heading), math.sin(heading)
    foot = None
    for k in range(0, 17):                       # where the ground first rises out of the water, within 8 m
        if ground(x + k * 50.0 * c, y + k * 50.0 * s) >= T.SEA - 20.0:
            foot = k * 50.0
            break
    if foot is None:
        return None
    pts = [(x + foot * c, y + foot * s)]
    if any(math.hypot(pts[0][0] - ox, pts[0][1] - oy) < CLIMB_APART for ox, oy in avoid):
        return None
    u, cut, fill = 0.0, 0.0, 0.0
    while u < CLIMB_MAX:
        px, py = pts[-1]
        z = T.climb_profile(u + TRACE_STEP)
        best = None
        for turn in TRACE_TURNS if len(pts) > 1 else (0,):
            a = heading + math.radians(turn)
            qx, qy = px + TRACE_STEP * math.cos(a), py + TRACE_STEP * math.sin(a)
            h = ground(qx, qy)
            if (u > 500.0 and h < T.SEA) or z - h > CLIMB_FILL or h - z > CLIMB_CUT or not _clear_site(island, qx, qy):
                continue
            if any(math.hypot(qx - ox, qy - oy) < TRACE_APART for ox, oy in pts[:-4]):
                continue                             # never folds back over itself
            pull = 0.0
            other = min(avoid, key=lambda o: math.hypot(qx - o[0], qy - o[1])) if avoid else None
            gap = math.hypot(qx - other[0], qy - other[1]) if other else math.inf
            if gap < CLIMB_APART:
                # Near another climb-out it may only go on to join it, at that one's own height (T.height has the
                # climb-outs placed so far cut in while planning).
                level = T.height(*other)
                if u <= 500.0 or abs(level - z) > 300.0:
                    continue
                if gap < T.CLIMB_HALF and abs(level - z) <= 60.0:
                    pts.append((qx, qy))
                    return cut + 3.0 * fill + 2000.0 * (u + TRACE_STEP), [(round(px), round(py)) for px, py in pts]
                pull = gap
            score = abs(h - z - TRACE_BIAS) + TRACE_TURN_COST * abs(turn) + pull
            if best is None or score < best[0]:
                best = (score, a, qx, qy, h)
        if best is None:
            return None
        _, heading, qx, qy, h = best
        pts.append((qx, qy))
        u += TRACE_STEP
        cut += max(0.0, h - z) * TRACE_STEP
        fill += max(0.0, z - h) * TRACE_STEP
        if u >= 600.0 and abs(h - z) <= 60.0:
            # The top: the ground ahead walkable and well clear of the sea.
            c, s = math.cos(heading), math.sin(heading)
            ahead = [ground(qx + d * c, qy + d * s) for d in (300.0, 600.0, 900.0)]
            if all(abs(b - a) / 300.0 <= math.tan(math.radians(28.0)) for a, b in zip([h] + ahead, ahead)) \
                    and min(ahead) > T.SEA + 50.0 and coast.on_main(qx, qy) and coast.on_main(qx + 1200.0 * c, qy + 1200.0 * s) \
                    and broad(qx, qy, c, s):
                return cut + 3.0 * fill + 2000.0 * u, [(round(px), round(py)) for px, py in pts]
    return None


def broad(x, y, c, s):
    """Whether the ground at a path's top, heading (c, s), is broad enough to walk on: from the line 3 m and 6 m to either
    side, and on for 12 m, no steeper than TOP_SLOPE (on November 5 two paths whose tops ended on a knife-edge ridge, gentle
    only along their line, stopped the survivor in Play)."""
    limit = math.tan(math.radians(TOP_SLOPE))
    for ahead in (0.0, 400.0, 800.0, 1200.0):
        px, py = x + ahead * c, y + ahead * s
        row = [T.height(px - side * s, py + side * c) for side in (-600.0, -300.0, 0.0, 300.0, 600.0)]
        if any(abs(b - a) / 300.0 > limit for a, b in zip(row, row[1:])):
            return False
    return True


TOP_SLOPE = 30.0          # degrees: the steepest ground round a path's top, across it and ahead
TRACE_STEP = 500.0        # cm between a climb-out's points
TRACE_TURNS = tuple(range(-50, 51, 10))   # degrees it may turn at each point
TRACE_TURN_COST = 4.0     # cm of height mismatch a degree of turning is worth (keeps the path smooth)
TRACE_BIAS = 200.0        # cm: it follows ground this much above its surface (a ledge cut into the face, not built out)
TRACE_APART = 2000.0      # cm: how close it may come back to its own earlier points
CLIMB_APART = 2 * (T.CLIMB_HALF + T.CLIMB_SIDE) + 500.0   # cm: how close it may come to another climb-out


def plan(key, rounds=6):
    """Climb-outs for one island so that no coast is trapped: [points of each path]. Round by round it surveys the coast
    with the paths so far cut in, and adds paths for what is still trapped, each kept clear of the others."""
    island = W.island(key)
    added, dropped = [], []
    for _ in range(rounds):
        T.set_climbs(added)
        coast = Coast(key)
        # With every path cut in, each must still lead from a step-out at the water onto the main ground; a path that
        # does not (another one's rock cut can leave its top on a cut-off ledge) is dropped and its place tried again.
        failed = [pts for pts in added if not coast.works(pts)]
        if failed:
            added = [pts for pts in added if pts not in failed]
            dropped += failed
            continue
        tried, new = set(), 0
        while True:
            trapped = [k for k in coast.trapped() if k not in tried]
            if not trapped:
                break
            target = max(trapped, key=lambda k: coast.dist[k])
            tried.add(target)
            tx, ty = coast.xy(target)
            # The candidates: the target and coast round it, setting off from straight inland to nearly along the shore.
            best = None
            near = [k for k in coast.coast if math.hypot(coast.xy(k)[0] - tx, coast.xy(k)[1] - ty) < 6000.0]
            avoid = [q for pts in added for q in pts] + [pts[0] for pts in dropped]
            for k in near[::max(1, len(near) // 12)] + [target]:
                x, y = coast.xy(k)
                inland = math.atan2(island.cy - y, island.cx - x)
                for turn in range(-5, 6):
                    found = trace(coast, x, y, inland + math.radians(15.0 * turn), avoid)
                    if found and (best is None or found[0] < best[0]):
                        best = found
            if best is None:
                continue
            points = best[1]
            added.append(points)
            new += 1
            # Its foot is a way out (checked by the next round's survey): the coast within EXIT_SWIM of it is freed.
            (ax, ay), (bx, by) = points[0], points[1]
            n = math.hypot(bx - ax, by - ay)
            foot = coast.vertex(ax - 100.0 * (bx - ax) / n, ay - 100.0 * (by - ay) / n)
            sources = [m for m, _ in coast.neighbours(foot)] + [foot] if foot is not None else []
            coast._swim([m for m in sources if coast.sea[m]])
        if not new:
            break
    T.set_climbs(added)
    added = [pts for pts in added if Coast(key).works(pts)] if added else added
    T.set_climbs(None)
    return added


def _plan_one(key):
    return key, plan(key)


def write(climbs):
    lines = ['"""Climb-outs along the coasts (owner, November 5), placed by coast_exits.py --plan; do not edit by hand.',
             'Each: the path points (x, y) in cm from its foot at the water to its top (world_terrain.Climb)."""',
             'CLIMB_OUTS = {']
    for key in sorted(climbs):
        if climbs[key]:
            lines.append(f'    {key!r}: [')
            lines += [f'        {[tuple(p) for p in c]!r},' for c in climbs[key]]
            lines.append('    ],')
    lines.append('}')
    OUT.write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--plan':
        keys = [i.key for i in W.ISLANDS if not args[1:] or i.key in args[1:]]
        try:
            from world_climbouts import CLIMB_OUTS
            climbs = {k: list(v) for k, v in CLIMB_OUTS.items()}
        except ImportError:
            climbs = {}
        with ProcessPoolExecutor(max_workers=min(14, len(keys))) as pool:
            for key, found in pool.map(_plan_one, keys):
                climbs[key] = found
                print(f'{key}: {len(found)} climb-outs')
        write(climbs)
        sys.exit(0)
    results = survey_all(args or None, workers=14)
    bad = 0
    for r in results:
        total = sum(s['length_m'] for s in r['trapped'])
        bad += bool(r['trapped'])
        print(f"{r['island']:9s} coast vertices {r['coast']:6d}  trapped {total:5d} m in {len(r['trapped']):3d} stretches"
              f"  worst swim {r['worst_swim_m']} m  unreachable {r['unreachable']}")
        for s in r['trapped'][:6]:
            print(f"    at ({s['at'][0] / 100:.0f}, {s['at'][1] / 100:.0f}) m  {s['length_m']} m long  worst {s['worst_swim_m']} m")
    sys.exit(1 if bad else 0)
