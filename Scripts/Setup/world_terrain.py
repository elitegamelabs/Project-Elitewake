"""Ground height everywhere in the world, from world_layout.py's islands. Plain Python (no Unreal): the terrain
builder makes its meshes from it, and the scripts that place trees, rocks, plants and animals stand them on it.

Each island: a beach of about 6 m of sand rising from the waterline, then ground shaped for its region (owner,
October 14-15):
  - Plains: rolling grassland, broad low hills and swales; the starter island keeps its exact shape, hills and pond.
  - Desert: sand dunes in long ridges with rocky rises.
  - Winter: rugged high ground, mountain peaks, rough slopes mixed with smoother ones.
  - Jungle: steep, broken hills.
  - Swamp: low wet ground barely above the sea, threaded with pools and channels that dip below the waterline
    (the sea fills them).
Some islands (by a hash of their name, so it is stable) have a cliff section where the land rises steeply straight
from a narrow beach (owner: cliffs on selected islands in every region). Offshore, a sandy shelf falls away to the
sea floor, about 60 m deep between islands and down to 500 m only in the open-sea basins far from any shore (owner:
500 m in selected deep areas). All heights are tuning. Units: Unreal centimetres; the sea surface is at -65.
"""
import math
import random

import world_layout as W

SEA = -65.0
FLOOR = -6000.0          # the sea floor between islands
DEEP = -50000.0          # the deepest basins (owner: 500 m)
SHELF = 20000.0          # how far an island's own terrain reaches past its shore (cm)
PORT_LEVEL = SEA + 220.0  # a Port's paved site, cm
POND = (-1700.0, 1500.0)
POND_RADIUS, POND_SURFACE, POND_DEPTH = 700.0, 5.0, 260.0


def seabed(d):
    """Depth below the waterline at d cm offshore: a sandy shelf, a drop-off, then the slope to the floor."""
    if d < 1500:
        return SEA - 0.3 * d
    if d < 4600:
        return SEA - 450 - 0.8 * (d - 1500)
    return SEA - 2930 - 0.25 * (d - 4600)


def land(inland):
    """Height at inland cm from the waterline: a 6 m beach, then a gentle rise."""
    if inland < 600:
        return SEA + inland / 600 * 80
    return 15 + min(inland - 600, 2500) * 0.02


def bump(x, y, cx, cy, radius, height):
    return height * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / radius ** 2)


def cliff_of(island):
    """A steep section of coast on about half the islands outside the swamp: (angle, half width, height)."""
    rng = random.Random(sum(map(ord, island.key)) * 7919)
    if island.region in ('Swamp', 'Plains') or rng.random() < 0.45:
        return None
    return (rng.uniform(0, 2 * math.pi), rng.uniform(0.35, 0.7), min(island.peak * 0.7, 1800.0))


CLIFFS = {i.key: cliff_of(i) for i in W.ISLANDS}

# Owner, October 15 (Design/World/ISLAND_TERRAIN_AND_REGIONAL_TREE_ASSIGNMENTS_2026-10-15.md): every island
# individually designed, with different combinations of mountains, hills, ridges, valleys and plateaus, so none is a
# resized copy of another. DECIDED (delegated, tuning): each island but the starter and the Swamp's draws a terrain plan
# from its region's list, no two islands of a region the same plan; its own seed sets each shape's size, place and
# heading. Peaks are sharp mountains, ridges long spines, plateaus flat-topped mesas with steep sides, valleys cut
# across the island (never down to the sea). The Swamp stays low wetland, varied by its pools and channels.
PLANS = {'Winter': [('peak', 'ridge'), ('peak', 'valley'), ('ridge', 'valley', 'peak'), ('peak', 'peak'), ('ridge', 'plateau')],
         'Jungle': [('ridge', 'valley'), ('peak', 'valley'), ('plateau', 'valley'), ('ridge', 'ridge'), ('peak', 'ridge', 'valley')],
         'Desert': [('plateau',), ('plateau', 'valley'), ('ridge', 'plateau'), ('plateau', 'plateau'), ('ridge', 'valley')],
         'Plains': [('valley',), ('plateau', 'valley'), ('ridge',), ('peak', 'valley'), ('plateau', 'ridge')]}


def _plans():
    plans = {}
    for region, options in PLANS.items():
        order = list(options)
        random.Random(sum(map(ord, region)) * 31).shuffle(order)
        islands = [i for i in W.ISLANDS if i.region == region and i.key != 'Starter']
        for isl, plan in zip(islands, order):
            rng = random.Random(sum(map(ord, isl.key)) * 104723)
            shapes = []
            for kind in plan:
                a = rng.uniform(0, 2 * math.pi)
                u, v = rng.uniform(-.35, .35) * isl.rx, rng.uniform(-.35, .35) * isl.ry
                if kind == 'peak':
                    shapes.append(('peak', u, v, rng.uniform(.25, .4) * isl.rx, isl.peak * rng.uniform(.9, 1.4),
                                   rng.randint(4, 7), rng.uniform(0, 2 * math.pi)))
                elif kind == 'ridge':
                    shapes.append(('ridge', u, v, a, rng.uniform(.45, .8) * isl.rx, rng.uniform(.12, .2) * isl.ry,
                                   isl.peak * rng.uniform(.5, .9), rng.uniform(0, 2 * math.pi)))
                elif kind == 'plateau':
                    shapes.append(('plateau', u, v, rng.uniform(.25, .4) * isl.ry, isl.peak * rng.uniform(.45, .8)))
                else:   # a valley runs right across, near the middle
                    shapes.append(('valley', u * .4, v * .4, a, rng.uniform(.08, .14) * isl.ry, isl.peak * rng.uniform(.4, .7)))
            plans[isl.key] = (plan, shapes)
    return plans


TERRAIN_PLANS = _plans()


def shapes_height(i, lx, ly):
    """The island's own terrain plan at (lx, ly) from its centre, in its turned frame: what its peaks, ridges and
    plateaus add and its valleys take away."""
    plan = TERRAIN_PLANS.get(i.key)
    if not plan:
        return 0.0
    c, s = math.cos(-i.turn), math.sin(-i.turn)
    x, y = lx * c - ly * s, lx * s + ly * c
    h = 0.0
    for shape in plan[1]:
        kind = shape[0]
        if kind == 'peak':
            # Not a cone: spurs run down its flanks between gullies, and crags break up the slopes near the top.
            _, u, v, r, height, spurs, phase = shape
            d = math.hypot(x - u, y - v)
            if d < r:
                f = d / r
                spur = 1 + .35 * f * math.sin(spurs * math.atan2(y - v, x - u) + phase + 2.5 * f)
                crag = .1 * (1 - f) * abs(math.sin(x / 640 + phase) * math.sin(y / 560 - phase))
                h += height * ((1 - f) ** 1.4 * spur + crag)
        elif kind == 'ridge':
            _, u, v, a, half, width, height, phase = shape
            dx, dy = x - u, y - v
            along = dx * math.cos(a) + dy * math.sin(a)
            # The spine wanders from side to side and rises and dips along its length.
            across = -dx * math.sin(a) + dy * math.cos(a) - width * .8 * math.sin(along / half * 2.2 + phase)
            height = height * (1 + .2 * math.sin(along / half * 3.7 + phase * 2))
            t = max(-1.0, min(1.0, along / half))
            off = math.hypot(across, along - t * half)
            h += height * math.exp(-(off / width) ** 2) * (1 - .5 * t * t)
        elif kind == 'plateau':
            _, u, v, r, height = shape
            d = math.hypot(x - u, y - v)
            edge = min(1.0, max(0.0, (r - d) / (r * .18)))
            h += height * edge * edge * (3 - 2 * edge)
        else:
            _, u, v, a, width, depth = shape
            across = -(x - u) * math.sin(a) + (y - v) * math.cos(a)
            h -= depth * math.exp(-(across / width) ** 2)
    return h
# How much higher and steeper each region's hills are than world_layout's base features (tuning): Winter mountains,
# Jungle's broken hills, Desert's rises among the dunes, Plains' rolling ground.
RELIEF = {'Winter': (3.6, 0.7), 'Jungle': (2.2, 0.8), 'Desert': (1.3, 1.0), 'Plains': (1.2, 1.2), 'Swamp': (1.0, 1.0)}


def starter_land(x, y, inland, ripple):
    """The starter island exactly as it was built before the five-region world (dunes, two hills, the pond)."""
    dunes = min(1.0, max(0.0, (inland - 1500) / 1500)) * (45 * math.sin(x / 650 + 1) * math.sin(y / 1100))
    h = land(inland) + dunes + bump(x, y, -3300, -1700, 1600, 700) + bump(x, y, -3500, 1300, 1200, 420)
    spring = math.hypot(x - POND[0], y - POND[1])
    if spring < POND_RADIUS + 300:
        blend = min(1.0, max(0.0, (spring - POND_RADIUS - 50) / 250))
        if spring < POND_RADIUS:
            floor = POND_SURFACE - 10 - POND_DEPTH * (1 - (spring / POND_RADIUS) ** 2)
        else:
            floor = min(20.0, POND_SURFACE - 10 + (spring - POND_RADIUS) * 0.3)
        h = floor * (1 - blend) + h * blend
    return h


def starter_ground(i, x, y, d, ripple):
    """The starter island (world_layout.StarterIsland): its old ground exactly as built on the old island, the
    Plains' rolling land on the new ground to the west, blended over about 25 m; the old east end (the beach spawn,
    dock and moorings) is never blended."""
    d_old = i.old.distance(x, y)
    old = starter_land(x, y, max(-d_old, 0.0), ripple)
    w = min(1.0, max(0.0, (d_old + 2000.0) / 2500.0)) * (1.0 - min(1.0, max(0.0, (x - 1000.0) / 2500.0)))
    if w <= 0.0:
        return old
    w = w * w * (3 - 2 * w)
    return old * (1 - w) + island_land(i, x, y, -d) * w


def island_land(i, x, y, inland):
    """Ground on island i at inland cm from its shore."""
    lx, ly = x - i.cx, y - i.cy
    rise = min(1.0, inland / 2500.0)          # region shapes grow in past the beach
    h = land(inland)
    tall, wide = RELIEF[i.region]
    for fx, fy, radius, height in i.features:
        h += bump(lx, ly, fx, fy, radius * wide, height * tall) * rise
    if i.region == 'Plains':
        h += rise * (220 * math.sin(lx / 2300 + 1.1) * math.sin(ly / 1900 + .4) + 60 * math.sin((lx + ly) / 900))
    elif i.region == 'Desert':
        ridge = math.sin((lx * .8 + ly * .6) / 700 + math.sin(ly / 1900) * 2)
        h += rise * (260 * ridge * ridge + 80 * math.sin(lx / 430))
    elif i.region == 'Winter':
        h += rise * (420 * abs(math.sin(lx / 520 + .7) * math.sin(ly / 430 + 1.9)) + 180 * abs(math.sin((lx - ly) / 300)))
    elif i.region == 'Jungle':
        h += rise * (200 * abs(math.sin(lx / 640) * math.cos(ly / 560 + .3)) + 80 * math.sin(lx / 260) * math.sin(ly / 310))
    if i.region != 'Swamp' and i.key in TERRAIN_PLANS:
        # The island's own plan; a valley floor stays above the sea (a little over the beach's top).
        h = max(h + rise * shapes_height(i, lx, ly), min(h, SEA + 120.0))
    if i.region == 'Swamp':
        # Low ground with pools and winding channels that fall below the waterline.
        channel = abs(math.sin(lx / 900 + 2 * math.sin(ly / 1300)) * math.sin(ly / 1100 + 1.3 * math.sin(lx / 1700)))
        # About a metre above the sea (lower and the ocean's surface reads over it), the pools well below it.
        h = SEA + 60 + min(inland, 600) / 600 * 100 + rise * (40 * math.sin(lx / 330) * math.sin(ly / 290))
        h -= rise * 300 * max(0.0, 0.35 - channel) / 0.35
        h = min(h, SEA + 160 + i.peak * rise * 0.6)
    cliff = CLIFFS.get(i.key)
    port = W.port_on(i)
    if port and cliff:
        # No cliff across a Port's waterfront.
        along, across = port.local(x, y)
        if along > -W.PORT_PAD and abs(across) < W.PORT_PAD * 1.6:
            cliff = None
    if cliff:
        ca, half, height = cliff
        a = math.atan2(ly, lx)
        d = math.atan2(math.sin(a - ca), math.cos(a - ca))
        side = max(0.0, 1.0 - abs(d) / half)
        if side > 0:
            # Past a 2-3 m strip of beach the ground climbs steeply to the cliff top.
            climb = min(1.0, max(0.0, (inland - 250) / 900))
            h = max(h, land(inland) + height * side ** .6 * climb ** .7)
    if port:
        # The Port's site: levelled 2.2 m above the sea, easing back into the island's ground.
        d = math.hypot(x - port.cx, y - port.cy)
        if d < W.PORT_PAD + 2500:
            w = 1.0 if d < W.PORT_PAD else 1.0 - (d - W.PORT_PAD) / 2500.0
            w = w * w * (3 - 2 * w)
            h = h * (1 - w) + PORT_LEVEL * w
    return h


def floor_at(x, y, nearest_gap):
    """The sea floor between islands: 60 m deep, falling to 500 m only well out in the open sea."""
    far = min(1.0, max(0.0, (nearest_gap - 90000) / 60000))
    far = far * far * (3 - 2 * far)
    return FLOOR + (DEEP - FLOOR) * far


def height_raw(x, y):
    """Ground (or sea floor) height in cm at (x, y), before the caves' notches."""
    best, nearest = None, 1e18
    for i in W.ISLANDS:
        dx, dy = x - i.cx, y - i.cy
        if abs(dx) > i.reach() + SHELF + 60000 or abs(dy) > i.reach() + SHELF + 60000:
            nearest = min(nearest, math.hypot(dx, dy) - i.reach())
            continue
        d = i.distance(x, y)
        nearest = min(nearest, d)
        ripple = 30 * math.sin(x / 700 + 0.5) * math.sin(y / 900 + 1.1) + 15 * math.sin((x + y) / 330)
        if d > 0:
            h = seabed(d) + ripple
        elif i.key == 'Starter':
            h = starter_ground(i, x, y, d, ripple)
        else:
            h = island_land(i, x, y, -d)
        best = h if best is None else max(best, h)
    floor = floor_at(x, y, nearest)
    return floor if best is None else max(best, floor)


# ---- Caves ----------------------------------------------------------------------------------------------------
# Owner, October 14 (WORLD_STRUCTURE_OWNER_DECISIONS): one cave system per island, entrances varied between inland
# hills, cliff faces and coastal rock formations; Winter's partway up the mountains (Art/REGIONAL_WORLD_..._10-15).
# A cave is a rock formation (build_caves.py) with a winding passage and a chamber hollowed out of it and its own
# flat rock floor. The ground under the formation is notched down below that floor so the island's own surface
# never shows through it. DECIDED (delegated): which kind each island gets (cliff where the island has a cliff;
# mountain-side in Winter and Jungle; coastal rock in the Swamp; Plains and Desert alternate); every size is tuning.
TUNNEL = (260.0, 300.0, 150.0)   # passage half-width, half-height, and its centre above the floor (cm)
CAVE_KINDS = ('inland', 'cliff', 'coastal')


class Cave:
    """One island's cave in its own frame: u runs in from the mouth (u = 0) along `heading`, v across it."""

    def __init__(self, island, kind, mx, my, heading, floor, scale, bend):
        self.island, self.kind = island, kind
        self.mx, self.my, self.heading, self.floor, self.scale, self.bend = mx, my, heading, floor, scale, bend
        self.cell = 200.0 if island.key == 'Starter' else 400.0       # the island mesh's grid
        self.margin = 1.5 * self.cell                                  # notch past the hollow
        self.length = 1400.0 * scale                                   # passage
        self.chamber = (600.0 * scale, 500.0 * max(scale, .8), 450.0)  # chamber half-sizes (u, v, z)
        self.chamber_u = self.length + 450.0 * scale
        self.chamber_z = 200.0                                         # chamber centre above the floor
        self.depth = self.chamber_u + self.chamber[0] + self.margin + self.cell + 200.0   # formation, mouth to back
        self.half = max(abs(bend) + TUNNEL[0], self.chamber[1]) + self.margin + self.cell + 200.0

    def local(self, x, y):
        dx, dy = x - self.mx, y - self.my
        c, s = math.cos(self.heading), math.sin(self.heading)
        return dx * c + dy * s, -dx * s + dy * c

    def world(self, u, v):
        c, s = math.cos(self.heading), math.sin(self.heading)
        return self.mx + u * c - v * s, self.my + u * s + v * c

    def centre_v(self, u):
        """The passage's centre line: it swings `bend` to one side and back before the chamber."""
        return self.bend * math.sin(math.pi * min(1.0, max(0.0, u / self.length)))

    def path(self, step=150.0):
        """The walk in, world (x, y) from just outside the mouth to the chamber's middle."""
        pts, u = [], -300.0
        while u < self.chamber_u:
            pts.append(self.world(u, self.centre_v(u)))
            u += step
        return pts + [self.world(self.chamber_u, 0.0)]

    def hollow(self, u, v):
        """Plan distance (cm) outside the hollow: negative inside the passage or the chamber."""
        cu, cv, _ = self.chamber
        q = math.hypot((u - self.chamber_u) / cu, v / cv)
        best = (q - 1.0) * min(cu, cv)
        if -400.0 <= u <= self.length + cu:
            best = min(best, abs(v - self.centre_v(u)) - TUNNEL[0])
        return best

    def inside(self, x, y, margin=0.0):
        """Within the rock formation's footprint (plus a margin; the mouth's approach is kept clear too)."""
        u, v = self.local(x, y)
        return -margin - 600.0 <= u <= self.depth + margin and abs(v) <= self.half + margin

    def notch(self, x, y, h):
        u, v = self.local(x, y)
        if -2 * self.cell < u < 0:
            # A doorstep: the ground before the mouth rises gently (about 12 cm a metre, tuning) to just under the rock
            # floor, so a survivor walking in meets the floor with a small step even where the island's coarse grid
            # would sag below it (the bigger islands of October 15 night put some mouths at beach level).
            across = abs(v - self.centre_v(0.0))
            side = 1.0 - min(1.0, max(0.0, (across - TUNNEL[0]) / self.cell))
            if side > 0:
                return max(h, h + (self.floor - 15.0 + 0.12 * u - h) * side) if self.floor - 15.0 + 0.12 * u > h else h
            return h
        if u < 0 or u > self.depth or abs(v) > self.half or self.hollow(u, v) > self.margin:
            return h
        # Just under the rock floor near the mouth (deeper further in), so the ground before the mouth, which the
        # island mesh's grid joins to these points, stays level with the floor rather than dipping into a ledge; at
        # the mouth itself it is set there even where the hillside lies lower, so the doorstep meets it.
        if u < 1.5 * self.cell and abs(v - self.centre_v(u)) < TUNNEL[0] + self.cell:
            return self.floor - 15.0
        return min(h, self.floor - 15.0 - 120.0 * min(1.0, max(0.0, u - 1.5 * self.cell) / 300.0))

    def footprint(self):
        return [self.world(u, v) for u in (0.0, self.depth * .5, self.depth) for v in (-self.half, 0.0, self.half)] + \
               [self.world(u, v) for u in (self.depth * .25, self.depth * .75) for v in (-self.half, self.half)]


def _cave_kind(island, index):
    if island.key == 'Starter':
        return 'inland'
    if CLIFFS.get(island.key) and not W.port_on(island):
        return 'cliff'
    if island.region in ('Winter', 'Jungle'):
        return 'inland'
    if island.region == 'Swamp':
        return 'coastal'
    return ('coastal', 'inland')[index % 2]


STARTER_CLEAR = [(150.0, 0.0, 2200.0), (4000.0, 900.0, 2200.0), (-1700.0, 1500.0, 2000.0)]   # spawn, dock, spring
STARTER_HILLS = [(-3300.0, -1700.0, 1600.0), (-3500.0, 1300.0, 1200.0)]                     # starter_land's bumps


def _fits(cave):
    i = cave.island
    for x, y in cave.footprint():
        if i.distance(x, y) > -150 or W.near_port(x, y, 800):
            return False
    if i.key != 'Starter' and cave.inside(i.cx, i.cy, 300):
        return False   # the island's middle stays open ground
    if i.key == 'Starter':
        for x, y in cave.footprint() + [(cave.mx, cave.my)]:
            if any(math.hypot(x - cx, y - cy) < r for cx, cy, r in STARTER_CLEAR):
                return False
    # The approach climbs to the mouth no steeper than a survivor can walk (about 34 degrees, tuning).
    for u, drop in ((-300.0, 200.0), (-600.0, 400.0)):
        fx, fy = cave.world(u, 0.0)
        if not cave.floor - drop <= height_raw(fx, fy) <= cave.floor + 40:
            return False
    return True


def _floor(mx, my, a):
    """A cave's floor: the ground at its mouth, but never more than 30 cm above the ground just in front, so the
    way in has no ledge to climb; and clear of the sea."""
    front = height_raw(mx + 50 * math.cos(a), my + 50 * math.sin(a))
    return max(min(height_raw(mx, my), front + 30), SEA + 25)


def _candidates(island, kind, rng, scale):
    bend = rng.choice((-1, 1)) * rng.uniform(120, 220) * scale
    out = []
    if kind == 'coastal':
        for k in range(48):
            a = 2 * math.pi * k / 48
            r = island.radius(a) - 700.0
            mx, my = island.cx + r * math.cos(a), island.cy + r * math.sin(a)
            floor = _floor(mx, my, a)
            out.append((rng.random(), Cave(island, kind, mx, my, a + math.pi, floor, scale, bend)))
    elif kind == 'cliff':
        ca, half, _ = CLIFFS[island.key]
        for k in range(-6, 7):
            a = ca + half * .6 * k / 6
            r = island.radius(a) - 260.0
            mx, my = island.cx + r * math.cos(a), island.cy + r * math.sin(a)
            floor = _floor(mx, my, a)
            out.append((abs(k) + rng.random() * .5, Cave(island, kind, mx, my, a + math.pi, floor, scale, bend)))
    else:
        if island.key == 'Starter':
            hills = STARTER_HILLS
        else:
            _, wide = RELIEF[island.region]
            hills = [(island.cx + fx, island.cy + fy, radius * wide) for fx, fy, radius, _ in sorted(island.features, key=lambda f: -f[3])]
        for hx, hy, reach in hills:
            top = height_raw(hx, hy)
            for k in range(24):
                a = 2 * math.pi * k / 24
                for f in (.7, .9, 1.1, 1.3):
                    mx, my = hx + f * reach * math.cos(a), hy + f * reach * math.sin(a)
                    if island.distance(mx, my) > -900:
                        continue
                    floor = _floor(mx, my, a)
                    part = (floor - SEA) / max(1.0, top - SEA)       # how far up the hill the mouth is
                    out.append((abs(part - .4) + rng.random() * .1, Cave(island, kind, mx, my, a + math.pi, floor, scale, bend)))
    return [c for _, c in sorted(out, key=lambda t: t[0])]


def _cave(island, index):
    rng = random.Random(sum(map(ord, island.key)) * 104729)
    first = _cave_kind(island, index)
    others = tuple(k for k in CAVE_KINDS if k != first and (k != 'cliff' or CLIFFS.get(island.key)))
    for scale in (1.0, .8, .65):
        for kind in (first,) + others:
            for cave in _candidates(island, kind, rng, scale):
                if _fits(cave):
                    return cave
    return None


def _caves():
    found, count = {}, {}
    for island in W.ISLANDS:
        count[island.region] = count.get(island.region, -1) + 1
        found[island.key] = _cave(island, count[island.region])
    return found


CAVES = _caves()


def near_cave(x, y, margin=500.0):
    """True on or near a cave's rock formation or in front of its mouth: keep trees, rocks and animals off it."""
    return any(c and c.inside(x, y, margin) for c in CAVES.values())


def height(x, y):
    """Ground (or sea floor) height in cm at (x, y): the islands as shaped, notched under each cave's formation."""
    h = height_raw(x, y)
    for c in CAVES.values():
        if c and abs(x - c.mx) < c.depth + c.half + 1000 and abs(y - c.my) < c.depth + c.half + 1000:
            h = c.notch(x, y, h)
    return h


def cover(x, y, z):
    """What the ground is covered with, for the terrain's vertex colour: (snow, grass, mud), each 0-1."""
    i = min(W.ISLANDS, key=lambda k: k.distance(x, y))
    d = i.distance(x, y)
    if d > 1500:
        return (0.0, 0.0, 0.0)
    inside = min(1.0, max(0.0, (1500 - d) / 1000))
    return {'Winter': (inside, 0.0, 0.0), 'Plains': (0.0, inside, 0.0), 'Jungle': (0.0, inside, 0.0),
            'Swamp': (0.0, inside * 0.4, inside), 'Desert': (0.0, 0.0, 0.0)}[i.region]


# ---- The ground as built --------------------------------------------------------------------------------------

def grid_of(island):
    """The island mesh's grid as build_coastal_terrain.py builds it: (x0, y0, step x, step y, cells x, cells y)."""
    reach = island.reach() + SHELF
    spacing = 200.0 if island.key == 'Starter' else 400.0
    x0, x1, y0, y1 = island.cx - reach, island.cx + reach, island.cy - reach, island.cy + reach
    nx, ny = max(2, int(round((x1 - x0) / spacing))), max(2, int(round((y1 - y0) / spacing)))
    return x0, y0, (x1 - x0) / nx, (y1 - y0) / ny, nx, ny


GRIDS = {i.key: grid_of(i) for i in W.ISLANDS}
_corner = {}


def built_height(x, y):
    """Ground height as the island meshes have it: the height function at the mesh's own grid corners, blended
    across the cell, so a cliff or a channel sharper than the grid is met where the mesh actually is."""
    best = None
    for i in W.ISLANDS:
        x0, y0, sx, sy, nx, ny = GRIDS[i.key]
        fx, fy = (x - x0) / sx, (y - y0) / sy
        if not (0 <= fx < nx and 0 <= fy < ny):
            continue
        ix, iy = int(fx), int(fy)
        tx, ty = fx - ix, fy - iy
        h = []
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            key = (i.key, ix + dx, iy + dy)
            if key not in _corner:
                _corner[key] = height(x0 + (ix + dx) * sx, y0 + (iy + dy) * sy)
            h.append(_corner[key])
        z = (h[0] * (1 - tx) + h[1] * tx) * (1 - ty) + (h[2] * (1 - tx) + h[3] * tx) * ty
        best = z if best is None else max(best, z)
    return best if best is not None else height(x, y)

