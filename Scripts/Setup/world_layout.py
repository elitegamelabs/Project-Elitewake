"""The world's islands: where each lies, which region it belongs to, and its shape. Plain Python (no Unreal), shared
by the world setup scripts and checked on its own:
    python Scripts/Setup/world_layout.py          # prints the layout and checks it; exit code 1 if a rule fails

Owner direction, October 15 (Docs/METRIC_WORLD_SCALE_AND_ISLAND_SPACING_2026-10-15.md,
Art/REGIONAL_WORLD_AND_3D_ASSET_REQUIREMENTS_2026-10-15.md, Docs/STARTER_ISLAND_CENTRAL_PLAINS_DIRECTION_2026-10-15.md):
  - five regions: Plains in the centre, Winter north (+Y), Swamp south (-Y), Desert east (+X), Jungle west (-X);
  - at least five islands in every region; the starter island is in Central Plains with at least five islands round it;
  - islands separated by open sea, 800 m to 2,000 m between shorelines.
DECIDED (delegated): "every pair of islands 800-2,000 m apart" cannot hold literally for 25+ islands (they cannot
all lie within 2 km of one another and 800 m apart); the layout keeps every pair at least 800 m apart and every
island's nearest neighbour within 2,000 m. Listed for the owner in Docs/OPEN_QUESTIONS_2026-10-15.md.

Units are Unreal centimetres (1 m = 100). The starter island keeps its exact shape, place and features so its trees,
pond, dock and the sloop's mooring stay where they are; every other island is generated from a seed and has its own
silhouette (harmonics), size, orientation, height and, on some, a cove. Island sizes and heights are tuning.
"""
import math
import random
import sys

M = 100.0                       # cm per metre
MIN_GAP, MAX_GAP = 800 * M, 2000 * M
REGION_CENTRES = {'Plains': (0.0, 0.0), 'Winter': (0.0, 5600 * M), 'Swamp': (0.0, -5600 * M),
                  'Desert': (5600 * M, 0.0), 'Jungle': (-5600 * M, 0.0)}
ISLANDS_PER_REGION = {'Plains': 6, 'Winter': 5, 'Swamp': 5, 'Desert': 5, 'Jungle': 5}   # Plains: starter + 5
REGION_SPREAD = 2300 * M        # how far a region's islands lie from its centre
SEED = 1015


class Island:
    """One island. Its shore lies at radius(angle) from its centre; `features` are hills (x, y, radius, height in cm,
    relative to the centre) the terrain raises. `cove` (angle, depth 0-1, width radians) notches the shore."""

    def __init__(self, key, region, cx, cy, rx, ry, turn=0.0, wobble=0.04, harmonics=(), cove=None, features=(), peak=600.0):
        self.key, self.region = key, region
        self.cx, self.cy, self.rx, self.ry = cx, cy, rx, ry
        self.turn, self.wobble, self.harmonics, self.cove = turn, wobble, harmonics, cove
        self.features, self.peak = list(features), peak

    def radius(self, angle):
        a = angle - self.turn
        edge = 1.0 / math.sqrt((math.cos(a) / self.rx) ** 2 + (math.sin(a) / self.ry) ** 2)
        shape = self.wobble * (0.6 * math.sin(3 * a + 1.3) + 0.4 * math.sin(7 * a + 0.4))
        for k, amp, phase in self.harmonics:
            shape += amp * math.sin(k * a + phase)
        if self.cove:
            ca, depth, width = self.cove
            d = math.atan2(math.sin(a - ca), math.cos(a - ca))
            shape -= depth * math.exp(-(d / width) ** 2)
        return edge * (1.0 + shape)

    def distance(self, x, y):
        """Signed distance in cm from the shore along the way out from the centre (negative inside)."""
        dx, dy = x - self.cx, y - self.cy
        return math.hypot(dx, dy) - self.radius(math.atan2(dy, dx))

    def outline(self, n=160):
        return [(self.cx + self.radius(2 * math.pi * k / n) * math.cos(2 * math.pi * k / n),
                 self.cy + self.radius(2 * math.pi * k / n) * math.sin(2 * math.pi * k / n)) for k in range(n)]

    def reach(self):
        """The farthest the shore gets from the centre, in cm."""
        if not hasattr(self, '_reach'):
            self._reach = max(self.radius(2 * math.pi * k / 90) for k in range(90))
        return self._reach


def starter():
    """The existing island, unchanged (build_coastal_terrain.py MAIN_SHORE and its hills and pond)."""
    return Island('Starter', 'Plains', -800.0, -100.0, 5100.0, 4100.0, wobble=0.03,
                  features=[(-2500, -1600, 1600, 700), (-2700, 1400, 1200, 420)], peak=700.0)


def shore_gap(a, b, n=160):
    """Shortest open-water gap between two islands' shorelines, in cm."""
    pa, pb = a.outline(n), b.outline(n)
    return min(math.hypot(x1 - x2, y1 - y2) for x1, y1 in pa for x2, y2 in pb)


def quick_gap(a, b):
    return math.hypot(a.cx - b.cx, a.cy - b.cy) - a.reach() - b.reach()


def generate(seed=SEED):
    rng = random.Random(seed)
    islands = [starter()]
    for region, count in ISLANDS_PER_REGION.items():
        rcx, rcy = REGION_CENTRES[region]
        made, tries = (1 if region == 'Plains' else 0), 0
        while made < count:
            tries += 1
            assert tries < 40000, f'could not place {region} islands'
            # Sizes (tuning): 120 m to 340 m across the long way, a little smaller round the starter.
            long_r = rng.uniform(60, 170) * M * (0.8 if region == 'Plains' else 1.0)
            short_r = long_r * rng.uniform(0.55, 0.9)
            if region == 'Plains':
                # Round the starter: a ring 1.0-1.6 km out, so each is 0.8-2 km of sea from it.
                ang, dist = rng.uniform(0, 2 * math.pi), rng.uniform(1050, 1650) * M
                cx, cy = rcx + dist * math.cos(ang), rcy + dist * math.sin(ang)
            else:
                ang, dist = rng.uniform(0, 2 * math.pi), REGION_SPREAD * math.sqrt(rng.random())
                cx, cy = rcx + dist * math.cos(ang), rcy + dist * math.sin(ang)
            harmonics = [(k, rng.uniform(0.02, 0.09), rng.uniform(0, 2 * math.pi)) for k in rng.sample([2, 4, 5, 6, 9], 3)]
            cove = (rng.uniform(0, 2 * math.pi), rng.uniform(0.25, 0.45), rng.uniform(0.18, 0.35)) if rng.random() < 0.4 else None
            peak = {'Winter': rng.uniform(1800, 3800), 'Jungle': rng.uniform(900, 2200), 'Desert': rng.uniform(400, 1400),
                    'Swamp': rng.uniform(80, 250), 'Plains': rng.uniform(400, 1200)}[region]
            features = []
            for _ in range(rng.randint(1, 3)):
                fa, fd = rng.uniform(0, 2 * math.pi), rng.uniform(0, 0.5) * short_r
                features.append((fd * math.cos(fa), fd * math.sin(fa), rng.uniform(0.25, 0.5) * long_r, peak * rng.uniform(0.5, 1.0)))
            isle = Island(f'{region}{made + 1}', region, cx, cy, long_r, short_r, rng.uniform(0, math.pi),
                          rng.uniform(0.02, 0.06), harmonics, cove, features, peak)
            # Far enough from every island; checked roughly first, then along the shores.
            if any(quick_gap(isle, o) < MIN_GAP - 50 * M for o in islands):
                continue
            if any(shore_gap(isle, o, 60) < MIN_GAP for o in islands if quick_gap(isle, o) < MIN_GAP + 400 * M):
                continue
            # ...and near enough to one already placed, so no island is left more than 2 km from its neighbours.
            if not any(shore_gap(isle, o, 60) < MAX_GAP - 50 * M for o in islands if quick_gap(isle, o) < MAX_GAP):
                continue
            islands.append(isle)
            made += 1
    return islands


def check(islands):
    """The owner's rules, measured along the shorelines. Returns a list of problems (empty when it passes)."""
    problems = []
    for region in REGION_CENTRES:
        n = sum(1 for i in islands if i.region == region)
        if n < 5:
            problems.append(f'{region} has {n} islands; at least five are required')
    around = [i for i in islands if i.region == 'Plains' and i.key != 'Starter']
    if len(around) < 5:
        problems.append(f'only {len(around)} islands round the starter')
    nearest = {}
    for a_i, a in enumerate(islands):
        for b in islands[a_i + 1:]:
            if quick_gap(a, b) > 4 * MAX_GAP:
                continue
            g = shore_gap(a, b)
            if g < MIN_GAP:
                problems.append(f'{a.key} and {b.key} are {g / M:.0f} m apart (less than 800 m)')
            nearest[a.key] = min(nearest.get(a.key, 1e18), g)
            nearest[b.key] = min(nearest.get(b.key, 1e18), g)
    for i in islands:
        if nearest.get(i.key, 1e18) > MAX_GAP:
            problems.append(f'{i.key} is {nearest.get(i.key, 1e18) / M:.0f} m from its nearest island (more than 2,000 m)')
    for i in islands:
        cx, cy = REGION_CENTRES[i.region]
        if i.region != 'Plains':
            dx, dy = cx / max(abs(cx) + abs(cy), 1), cy / max(abs(cx) + abs(cy), 1)
            if i.cx * dx + i.cy * dy <= 0:
                problems.append(f'{i.key} lies on the wrong side of the world for {i.region}')
    return problems, nearest


ISLANDS = generate()


def island(key):
    return next(i for i in ISLANDS if i.key == key)


def region_of(x, y):
    """The region of the island nearest to (x, y)."""
    return min(ISLANDS, key=lambda i: i.distance(x, y)).region


def bounds(margin=1500 * M):
    xs = [i.cx for i in ISLANDS]
    ys = [i.cy for i in ISLANDS]
    r = max(i.reach() for i in ISLANDS)
    return (min(xs) - r - margin, max(xs) + r + margin, min(ys) - r - margin, max(ys) + r + margin)


if __name__ == '__main__':
    problems, nearest = check(ISLANDS)
    for i in ISLANDS:
        print(f'{i.key:10s} {i.region:7s} centre ({i.cx / M:7.0f}, {i.cy / M:7.0f}) m  size {2 * i.rx / M:4.0f} x {2 * i.ry / M:4.0f} m  '
              f'peak {i.peak / M:4.1f} m  cove {"yes" if i.cove else "no "}  nearest shore {nearest.get(i.key, 0) / M:5.0f} m')
    x0, x1, y0, y1 = bounds()
    print(f'{len(ISLANDS)} islands; world {(x1 - x0) / M / 1000:.1f} x {(y1 - y0) / M / 1000:.1f} km')
    print('PASS' if not problems else 'FAIL:\n  ' + '\n  '.join(problems))
    sys.exit(1 if problems else 0)
