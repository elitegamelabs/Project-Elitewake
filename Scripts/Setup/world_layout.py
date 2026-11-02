"""The canonical five-island world: where each island lies, which region it belongs to, and its shape.

Plain Python (no Unreal), shared by the world setup scripts and checked on its own:
    python Scripts/Setup/world_layout.py          # prints the layout and checks it; exit code 1 if a rule fails

Current owner direction:
  - five regions: Plains in the centre, Winter north (+Y), Swamp south (-Y), Desert east (-X), Jungle west (+X).
    North is +Y and east -X, a quarter turn clockwise as Unreal's yaw turns, so the compass, the map and the sun agree
    (Source/EW/World/EWNorth.h; owner, November 1: Desert and Jungle swapped sides to match);
  - exactly one large, distinct island per region during the current production phase;
  - the Plains island is the universal starting island;
  - islands separated by open sea, 800 m to 2,000 m between shorelines.

Units are Unreal centimetres (1 m = 100). Every other island is generated from a seed and has its own silhouette
(harmonics), size, orientation, height and cove. Island sizes and heights are tuning. There is no alternate
high-island-count build path in this module.
"""
import math
import random
import sys

M = 100.0                       # cm per metre
MIN_GAP, MAX_GAP = 800 * M, 2000 * M
REGION_CENTRES = {'Plains': (0.0, 0.0), 'Winter': (0.0, 7000 * M), 'Swamp': (0.0, -7000 * M),
                  'Desert': (-7000 * M, 0.0), 'Jungle': (7000 * M, 0.0)}
ISLANDS_PER_REGION = {'Plains': 1, 'Winter': 1, 'Swamp': 1, 'Desert': 1, 'Jungle': 1}
DESERT_X, JUNGLE_X = -390000.0, 280000.0     # cm: centres along X (tuning; the Plains island reaches about 2 km toward -X)


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


class StarterIsland(Island):
    """The first island: its old shape (build_coastal_terrain.py MAIN_SHORE, the beach spawn, dock, pond and sloop
    on its east end) joined to a larger island to its west. Its shore is whichever of the two reaches farther."""

    def __init__(self, old, west):
        super().__init__('Starter', 'Plains', old.cx, old.cy, west.rx, west.ry, features=old.features + west.features,
                         peak=west.peak)
        self.old, self.west = old, west

    def radius(self, angle):
        # Along this bearing from the old centre: the old shore, or where the ray leaves the western island.
        c, s = math.cos(angle), math.sin(angle)
        ox, oy = self.cx - self.west.cx, self.cy - self.west.cy
        best, lo, hi = 0.0, 0.0, 2.0 * (self.west.reach() + math.hypot(ox, oy))
        if self.west.distance(self.cx, self.cy) < 0:
            for _ in range(40):
                mid = (lo + hi) / 2
                if self.west.distance(self.cx + mid * c, self.cy + mid * s) < 0:
                    lo = mid
                else:
                    hi = mid
            best = lo
        return max(self.old.radius(angle), best)


def shore_gap(a, b, n=160):
    """Shortest open-water gap between two islands' shorelines, in cm."""
    pa, pb = a.outline(n), b.outline(n)
    return min(math.hypot(x1 - x2, y1 - y2) for x1, y1 in pa for x2, y2 in pb)


def quick_gap(a, b):
    return math.hypot(a.cx - b.cx, a.cy - b.cy) - a.reach() - b.reach()


def _organic(key, region, cx, cy, rx, ry, turn, seed, peak, hills, cove):
    """An island with a hand-set size and an irregular shore: eight harmonics of its own, a cove or two, ridges and hills of its own."""
    rng = random.Random(seed)
    harmonics = [(k, rng.uniform(0.035, 0.11) / (1 + 0.12 * k), rng.uniform(0, 2 * math.pi)) for k in (2, 3, 4, 5, 6, 8, 11, 14)]
    features = []
    for n in range(hills):
        fa, fd = rng.uniform(0, 2 * math.pi), rng.uniform(0.05, 0.6) * min(rx, ry)
        features.append((fd * math.cos(fa), fd * math.sin(fa), rng.uniform(0.18, 0.34) * min(rx, ry), peak * (1.0 if n == 0 else rng.uniform(0.35, 0.8))))
    return Island(key, region, cx, cy, rx, ry, turn, rng.uniform(0.04, 0.07), harmonics, cove, features, peak)


def generate():
    """The Plains island (the starter, grown to about 2 km) in the middle and one island each for Winter (north), Swamp (south), Desert (east) and Jungle (west)."""
    old = Island('Starter', 'Plains', -800.0, -100.0, 5100.0, 4100.0, wobble=0.03,
                 features=[(-2500, -1600, 1600, 700), (-2700, 1400, 1200, 420)], peak=700.0)
    # The old east end keeps the beach spawn, dock, pond and sloop mooring; the island grows west from it, about 2 km across, with a notched, irregular shore.
    west = _organic('StarterWest', 'Plains', -99000.0, -400.0, 101000.0, 82000.0, 0.15, 7101, 2600.0, 6, (math.pi * 0.9, 0.3, 0.22))
    west.cx = 3000.0 - west.radius(0.0)      # its east shore lands 30 m east of the old centre, just inside the old east end
    west.features = [(x + west.cx - old.cx, y + west.cy - old.cy, r, h) for x, y, r, h in west.features]
    islands = [StarterIsland(old, west)]
    islands.append(_organic('Winter1', 'Winter', -60000.0, 280000.0, 118000.0, 82000.0, 0.45, 7202, 11000.0, 5, (-math.pi / 2, 0.35, 0.25)))
    islands.append(_organic('Swamp1', 'Swamp', -30000.0, -270000.0, 100000.0, 80000.0, 2.6, 7303, 260.0, 4, (math.pi / 3, 0.4, 0.3)))
    # Desert east (-X) and Jungle west (+X), each keeping its own shape, seed and size; their coves still face the Plains.
    islands.append(_organic('Desert1', 'Desert', DESERT_X, -30000.0, 110000.0, 84000.0, 1.2, 7404, 4600.0, 5, (0.0, 0.3, 0.2)))
    islands.append(_organic('Jungle1', 'Jungle', JUNGLE_X, 20000.0, 102000.0, 92000.0, 0.9, 7505, 6800.0, 6, (math.pi - 0.3, 0.35, 0.24)))
    return islands


def check(islands):
    """The owner's rules, measured along the shorelines. Returns a list of problems (empty when it passes)."""
    problems = []
    for region, expected in ISLANDS_PER_REGION.items():
        n = sum(1 for i in islands if i.region == region)
        if n != expected:
            problems.append(f'{region} has {n} islands; exactly {expected} are required')
    around = [i for i in islands if i.region == 'Plains' and i.key != 'Starter']
    if len(around) != ISLANDS_PER_REGION['Plains'] - 1:
        problems.append(f'{len(around)} islands round the starter; {ISLANDS_PER_REGION["Plains"] - 1} are required')
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


# ---- Ports ----------------------------------------------------------------------------------------------------
# One Port in each region. With one island per region, every island carries its regional Port. Waterfronts face
# the world's centre except Saltreach Freeport on the Plains starter island, whose established approach faces
# south-west.
PORT_PAD = 3800.0        # cm: radius of the level, paved Port site (tuning)
PORT_INLAND = 2600.0     # cm: how far inland of the shore the site's middle lies


class Port:
    """A Port's site: its island, the bearing its waterfront faces (radians), the shore point there, and the site's
    middle on land."""

    def __init__(self, region, island):
        self.region, self.island = region, island
        self.facing = math.atan2(-island.cy, -island.cx) if (island.cx or island.cy) else 0.0
        r = island.radius(self.facing)
        self.shore = (island.cx + r * math.cos(self.facing), island.cy + r * math.sin(self.facing))
        self.cx = island.cx + (r - PORT_INLAND) * math.cos(self.facing)
        self.cy = island.cy + (r - PORT_INLAND) * math.sin(self.facing)

    def local(self, x, y):
        """(along, across) in cm in the Port's frame: along points out to sea through the waterfront."""
        dx, dy = x - self.cx, y - self.cy
        c, s = math.cos(self.facing), math.sin(self.facing)
        return dx * c + dy * s, -dx * s + dy * c

    def world(self, along, across):
        c, s = math.cos(self.facing), math.sin(self.facing)
        return self.cx + along * c - across * s, self.cy + along * s + across * c


def _ports():
    ports = {region: Port(region, i) for region in REGION_CENTRES for i in ISLANDS if i.region == region}
    starter_port = ports['Plains']
    starter_port.facing = -2.3
    r = starter_port.island.radius(starter_port.facing)
    starter_port.shore = (starter_port.island.cx + r * math.cos(starter_port.facing),
                          starter_port.island.cy + r * math.sin(starter_port.facing))
    starter_port.cx = starter_port.island.cx + (r - PORT_INLAND) * math.cos(starter_port.facing)
    starter_port.cy = starter_port.island.cy + (r - PORT_INLAND) * math.sin(starter_port.facing)
    return ports


PORTS = _ports()


def port_on(island):
    return next((p for p in PORTS.values() if p.island is island), None)


def near_port(x, y, margin=1500.0):
    """True within a Port's site (plus a margin) or its waterfront: keep trees, rocks and animals off it."""
    for p in PORTS.values():
        along, across = p.local(x, y)
        if math.hypot(along, across) < PORT_PAD + margin or (0 < along < PORT_INLAND + 6000 and abs(across) < 1800):
            return True
    return False


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
    for region, port in PORTS.items():
        print(f'Port of the {region}: {port.island.key}, waterfront facing {math.degrees(port.facing):.0f} degrees')
    print('PASS' if not problems else 'FAIL:\n  ' + '\n  '.join(problems))
    sys.exit(1 if problems else 0)
