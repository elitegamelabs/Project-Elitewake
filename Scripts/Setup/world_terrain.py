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
sea floor: a slope cut by canyons down to basins a few hundred metres deep between the islands, ridges and sand waves
across them, shallow seamounts to dive on, and the open ocean round the archipelago falling to 1.5 km, the deepest
anywhere, with one trench reaching it between the islands (owner, October 17: dynamic sea-floor scenery and
geography; October 22: the ocean at most 1,500 m deep, was 2,000 m). All heights are tuning. Units: Unreal centimetres; the sea surface is at -65.
"""
import math
import random

import world_layout as W

SEA = -65.0
FLOOR = -6000.0          # the foot of an island's shelf, 60 m down
DEEP = SEA - 150000.0    # the deepest sea anywhere (owner, October 22: at most 1,500 m; was 2,000 m)
SHELF = 20000.0          # how far an island's own terrain reaches past its shore (cm)


def ground_spacing(island):
    """The island mesh's grid step, cm; keeps each large island mesh near a million vertices."""
    return 400.0 if island.key == 'Starter' else 300.0

PORT_LEVEL = SEA + 220.0  # a Port's paved site, cm
POND = (-1700.0, 1500.0)
POND_RADIUS, POND_SURFACE, POND_DEPTH = 700.0, 5.0, 457.0     # 15 ft deep (owner, November 1); coastal_layout.py matches
POND_FLAT = .4            # share of the radius over which the pond's floor lies flat at its full depth


def seabed(d):
    """Depth below the waterline at d cm offshore (owner, October 26: beaches that slope naturally into the water and level
    out into the sea). A gentle foreshore at the waterline deepening smoothly to the floor at SHELF."""
    # One unbroken curve: a gentle foreshore (about 8 degrees at the water) that keeps deepening without a flat step or a
    # sudden shelf break, reaching the 60 m floor at SHELF where the open sea floor takes over.
    d = min(d, SHELF)
    shelf = 450.0 * (1 - math.exp(-d / 3000.0)) + (SEA - FLOOR - 450.0) * (d / SHELF) ** 1.8
    return SEA - shelf


def land(inland):
    """Height at inland cm from the waterline: a long gentle beach (about 7 % at the water, easing off over some 15 m),
    then a gentle rise."""
    return SEA + 100.0 * (1 - math.exp(-inland / 1500.0)) + 0.02 * min(max(inland - 600.0, 0.0), 2500.0)


def bump(x, y, cx, cy, radius, height):
    return height * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / radius ** 2)


def cliff_of(island):
    """A steep section of coast on about half the islands outside the swamp: (angle, half width, height)."""
    rng = random.Random(sum(map(ord, island.key)) * 7919)
    if island.region in ('Swamp', 'Plains') or rng.random() < 0.45:
        return None
    return (rng.uniform(0, 2 * math.pi), rng.uniform(0.35, 0.7), min(island.peak * 0.7, 1800.0))


CLIFFS = {i.key: cliff_of(i) for i in W.ISLANDS}

# Every island is individually designed with its own combination of hills, ridges, valleys and plateaus, so none is a
# resized copy of another. Each non-starter island outside the Swamp draws a terrain plan from its region's list; its own
# seed sets each shape's size, place and heading. CLAUDE.md 5.1 (owner, November 1): several smaller, plausibly shaped
# hills, peaks or ridges spread round each island, never one dominant central mountain to trek over, so a walk across
# takes 6-17 minutes (estimate_walking_times.py). Shapes stand on a ring 35-70 % of the way out, spaced round the island;
# peaks are hill massifs, ridges spines running round the island rather than across it, plateaus flat-topped mesas with
# steep sides, and a valley cuts across near the middle without reaching the sea.
PLANS = {'Winter': [('peak', 'ridge', 'peak'), ('peak', 'valley', 'ridge'), ('ridge', 'peak', 'ridge', 'valley'), ('peak', 'peak', 'ridge'), ('ridge', 'plateau', 'peak')],
         'Jungle': [('ridge', 'valley', 'peak'), ('peak', 'valley', 'ridge'), ('plateau', 'valley', 'ridge'), ('ridge', 'ridge', 'peak'), ('peak', 'ridge', 'valley')],
         'Desert': [('plateau', 'ridge'), ('plateau', 'valley', 'plateau'), ('ridge', 'plateau', 'ridge'), ('plateau', 'plateau', 'valley'), ('ridge', 'valley', 'plateau')],
         'Plains': [('valley', 'ridge', 'plateau'), ('plateau', 'valley', 'ridge'), ('ridge', 'peak'), ('peak', 'valley', 'plateau'), ('plateau', 'ridge', 'valley')]}
RING = (0.35, 0.7)          # how far out from the middle a plan's raised shapes stand (share of the island's radius)


def _plans():
    plans = {}
    for region, options in PLANS.items():
        order = list(options)
        random.Random(sum(map(ord, region)) * 31).shuffle(order)
        islands = [i for i in W.ISLANDS if i.region == region and i.key != 'Starter']
        for n, isl in enumerate(islands):
            plan = order[n % len(order)]
            rng = random.Random(sum(map(ord, isl.key)) * 104723)
            raised = sum(1 for k in plan if k != 'valley')
            base = rng.uniform(0, 2 * math.pi)
            shapes, slot = [], 0
            for kind in plan:
                if kind == 'valley':   # a valley runs right across, near the middle
                    a = rng.uniform(0, 2 * math.pi)
                    shapes.append(('valley', rng.uniform(-.1, .1) * isl.rx, rng.uniform(-.1, .1) * isl.ry, a,
                                   rng.uniform(.16, .26) * isl.ry, isl.peak * rng.uniform(.3, .5)))
                    continue
                at = base + 2 * math.pi * slot / raised + rng.uniform(-.3, .3)     # spaced evenly round the ring
                slot += 1
                d = rng.uniform(*RING)
                u, v = d * isl.rx * math.cos(at), d * isl.ry * math.sin(at)
                if kind == 'peak':
                    shapes.append(('peak', u, v, rng.uniform(.24, .34) * isl.rx, isl.peak * rng.uniform(.6, 1.0),
                                   rng.randint(4, 7), rng.uniform(0, 2 * math.pi)))
                elif kind == 'ridge':
                    # Along the ring (a quarter turn from the way out), so the spine rounds the island instead of crossing it.
                    shapes.append(('ridge', u, v, at + math.pi / 2 + rng.uniform(-.4, .4), rng.uniform(.3, .45) * isl.rx,
                                   rng.uniform(.14, .22) * isl.ry, isl.peak * rng.uniform(.4, .7), rng.uniform(0, 2 * math.pi)))
                else:
                    shapes.append(('plateau', u, v, rng.uniform(.16, .26) * isl.ry, isl.peak * rng.uniform(.35, .6)))
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
            # A massif, not a cone (owner, October 26): foothills ease in, the flanks climb steeply and the summit rounds off;
            # long spurs and gullies run down between ridgelines, a shoulder and a second top stand on its side, and the
            # whole is roughened by broad noise. Every feature is wider than six grid steps so the mesh holds it smoothly.
            _, u, v, r, height, spurs, phase = shape
            d = math.hypot(x - u, y - v)
            if d < r:
                f = d / r
                s = 1 - f
                body = s * s * (3 - 2 * s) * .85 + s ** 1.6 * .15
                ang = math.atan2(y - v, x - u)
                ridges = 1 + .3 * (4 * f * (1 - f)) * math.sin(spurs * ang + phase + 1.8 * f)
                top = .22 * math.exp(-((f - .45) / .22) ** 2) * (.5 + .5 * math.sin(2 * ang + phase * 1.7))   # a shoulder and a lesser summit
                rough = (noise(x, y, 14000.0, 21) - .5) * .30 * s * (1 - s * .5) + (noise(x, y, 6000.0, 23) - .5) * .10 * s * f
                h += height * max(0.0, body * ridges + top + rough)
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
RELIEF = {'Winter': (0.9, 1.8), 'Jungle': (2.2, 0.8), 'Desert': (1.3, 1.0), 'Plains': (1.2, 1.2), 'Swamp': (1.0, 1.0)}


# The Desert's dunes (owner, October 16, BIOME_TERRAIN_FOLIAGE_AND_GLOBAL_SUN: irregular natural sand dunes):
# transverse dunes across the prevailing wind, each a long gentle windward slope up to a crest and a short steep
# slip face down its lee side, crests 3-7 m high and about 45 m apart, wandering and rising and falling along their
# length. Tuning.
DUNE_WIND = 0.6            # radians: the direction the dunes march
DUNE_SPACING = 4500.0      # cm between crests
DUNE_CREST = 0.78          # where along each dune its crest stands (the rest is the slip face)


def dunes(lx, ly):
    along = lx * math.cos(DUNE_WIND) + ly * math.sin(DUNE_WIND)
    across = -lx * math.sin(DUNE_WIND) + ly * math.cos(DUNE_WIND)
    p = along / DUNE_SPACING + .35 * math.sin(across / 2600) + .15 * math.sin(across / 900 + 1.3)
    f = p - math.floor(p)
    profile = (f / DUNE_CREST) ** 1.6 if f < DUNE_CREST else ((1 - f) / (1 - DUNE_CREST)) ** 1.2
    crest = 300 + 400 * (.5 + .5 * math.sin(across / 3100 + math.floor(p) * 1.3))
    return crest * profile


def starter_land(x, y, inland, ripple):
    """The starter island exactly as it was built before the five-region world (dunes, two hills, the pond)."""
    dunes = min(1.0, max(0.0, (inland - 1500) / 1500)) * (45 * math.sin(x / 650 + 1) * math.sin(y / 1100))
    h = land(inland) + dunes + bump(x, y, -3300, -1700, 1600, 700) + bump(x, y, -3500, 1300, 1200, 420)
    spring = math.hypot(x - POND[0], y - POND[1])
    if spring < POND_RADIUS + 300:
        blend = min(1.0, max(0.0, (spring - POND_RADIUS - 50) / 250))
        if spring < POND_RADIUS:
            # A flat floor at the full depth over the middle 40 % (the island's 4 m grid then shows the whole 15 ft), rising
            # to the banks.
            floor = POND_SURFACE - 10 - POND_DEPTH * min(1.0, (1 - (spring / POND_RADIUS) ** 2) / (1 - POND_FLAT ** 2))
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
        h += bump(lx, ly, fx, fy, radius * wide, height * tall) * rise * (.8 + .4 * noise(lx, ly, 14000.0, 31) if i.region == 'Winter' else 1.0)
    if i.region == 'Plains':
        h += rise * (220 * math.sin(lx / 2300 + 1.1) * math.sin(ly / 1900 + .4) + 60 * math.sin((lx + ly) / 900))
    elif i.region == 'Desert':
        h += rise * dunes(lx, ly)
    elif i.region == 'Winter':
        # Owner, October 26: the hills looked unreal, a sawtooth of creases. Creases (abs of a sine) and features under a
        # few grid steps wide alias on the 300 cm mesh, so these are smooth, broad swells with a little noise.
        # Owner, October 26 (again): realistic hills. Rolling ground from three octaves of noise, not a regular pattern.
        h += rise * (700 * (noise(lx, ly, 4200.0, 7) - .5) + 330 * (noise(lx, ly, 1900.0, 8) - .5) + 110 * (noise(lx, ly, 900.0, 9) - .5) + 300)
    elif i.region == 'Jungle':
        h += rise * (520 * (noise(lx, ly, 3800.0, 11) - .5) + 260 * (noise(lx, ly, 1700.0, 12) - .5) + 90 * (noise(lx, ly, 850.0, 13) - .5) + 160)
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


# ---- The open sea floor ----------------------------------------------------------------------------------------
# DECIDED (delegated; owner, October 17: dynamic sea-floor scenery, deeper sand, geography, the ocean at most 2 km).
# Past an island's shelf the floor falls away down a slope cut by canyons, deeper the farther from any shore: a few
# hundred metres in the middle of the channels between islands, the full 2 km only in the open ocean round the
# archipelago and in one trench. Ridges cross the basins, long sand waves cover their floors, and seamounts rise to
# within diving depth. Every size here is tuning.
OPEN_SEA = 250000.0               # cm from the nearest shore where the open ocean reaches its full depth
SLOPE_START = 15000.0             # cm offshore where the floor starts to fall from the shelf's foot
CANYONS = 38000.0                 # cm of shoreline per canyon down an island's slope
SEAMOUNTS = 7
SEAMOUNT_TOPS = (1000.0, 2800.0)  # cm under the surface: within diving depth, under any keel
TRENCH_HALF_WIDTH = 30000.0


def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def noise(x, y, scale, seed):
    """Smooth value noise, 0-1, with features about `scale` cm across (turned by its seed, so it has no grain)."""
    a = seed * 2.39996
    c, s = math.cos(a), math.sin(a)
    qx, qy = (x * c - y * s) / scale + seed * 17.3, (x * s + y * c) / scale - seed * 9.1
    ix, iy = math.floor(qx), math.floor(qy)
    fx, fy = qx - ix, qy - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def _shore_gap(x, y):
    return min(i.distance(x, y) for i in W.ISLANDS)


def _between_islands(x, y, within=150000):
    """Open water with shores on more than one side: at least three islands within `within` cm."""
    return sum(1 for i in W.ISLANDS if i.distance(x, y) < within) >= 3


def _seamounts():
    """Where the seamounts stand: the most open water between the islands, well apart and clear of the trench
    (stable, by a fixed seed)."""
    x0, x1, y0, y1 = W.bounds(0)
    rng = random.Random(1717)
    spots = []
    for gx in range(int(x0), int(x1), 25000):
        for gy in range(int(y0), int(y1), 25000):
            x, y = gx + rng.uniform(-8000, 8000), gy + rng.uniform(-8000, 8000)
            g = _shore_gap(x, y)
            if g > 35000 and _between_islands(x, y) and _trench_weight(x, y) == 0 and math.hypot(x - TRENCH[0][0], y - TRENCH[0][1]) > 80000:
                spots.append((g + rng.uniform(0, 15000), x, y))
    spots.sort(reverse=True)
    out = []
    for _, x, y in spots:
        if all(math.hypot(x - m[0], y - m[1]) > 200000 for m in out):
            out.append((x, y, rng.uniform(*SEAMOUNT_TOPS), rng.uniform(16000, 26000)))
        if len(out) == SEAMOUNTS:
            break
    return out


def _trench():
    """The trench: from the widest open water among the islands straight out to the open ocean."""
    x0, x1, y0, y1 = W.bounds(0)
    best = None
    for gx in range(int(x0) + 100000, int(x1) - 100000, 20000):
        for gy in range(int(y0) + 100000, int(y1) - 100000, 20000):
            g = _shore_gap(gx, gy)
            if (best is None or g > best[0]) and _between_islands(gx, gy):
                best = (g, gx, gy)
    _, sx, sy = best
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = sx - cx, sy - cy
    n = math.hypot(dx, dy) or 1.0
    reach = max(x1 - x0, y1 - y0)
    return (sx, sy), (sx + dx / n * reach, sy + dy / n * reach)


TRENCH = _trench()


def _trench_weight(x, y):
    (ax, ay), (bx, by) = TRENCH
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy)))
    wander = (noise(x, y, 90000, 61) - .5) * 40000
    across = math.hypot(x - ax - vx * t, y - ay - vy * t) + wander
    # It opens from nothing at its head over its first 300 m.
    head = _smooth(t * math.hypot(vx, vy) / 30000)
    return head * _smooth(1 - abs(across) / TRENCH_HALF_WIDTH)


SEAMOUNT_SITES = _seamounts()


def floor_at(x, y, nearest_gap, nearest=None):
    """The sea floor away from the shelves: slope, canyons, basins, ridges, sand waves, seamounts and the trench."""
    g = nearest_gap
    # The slope from the shelf's foot down to the open ocean's 2 km.
    fall = _smooth((g - SLOPE_START) / (OPEN_SEA - SLOPE_START)) ** 1.25
    depth = (SEA - FLOOR) + (SEA - DEEP - (SEA - FLOOR)) * fall
    # Basins and rises: the depth itself wanders by up to 15 %.
    depth *= .85 + .3 * (noise(x, y, 120000, 7) * .75 + noise(x, y, 40000, 8) * .25)
    # Canyons cut down the slope off each island, a few hundred metres apart round its shore.
    if nearest is not None and SLOPE_START < g < 110000:
        a = math.atan2(y - nearest.cy, x - nearest.cx)
        count = max(5, round(2 * math.pi * nearest.reach() / CANYONS))
        phase = _hash(len(nearest.key), ord(nearest.key[0]), 5) * 6.283
        groove = (.5 + .5 * math.cos(a * count + phase + (noise(x, y, 30000, 9) - .5) * 2.5)) ** 8
        band = _smooth((g - SLOPE_START) / 15000) * _smooth((110000 - g) / 40000)
        depth += groove * band * min(depth * .6, 9000)
    # Ridges across the deep floor, standing up to a quarter of the depth.
    warp = (noise(x, y, 50000, 24) - .5) * 60000
    ridge = 1 - abs(2 * (noise(x + warp, y - warp, 70000, 23) * .7 + noise(x, y, 23000, 29) * .3) - 1)
    depth -= ridge ** 3 * depth * .25 * _smooth((g - 40000) / 40000)
    # Sand waves: long low dunes on the floor, crests a few metres high.
    swell = math.sin((x * .8 + y * .6) / 4000 + noise(x, y, 40000, 31) * 5)
    depth -= (1.5 + swell) * 150 * _smooth((g - SLOPE_START) / 20000)
    z = SEA - depth
    # The trench, down to the deepest water, never cutting into a shelf.
    trench = _trench_weight(x, y)
    if trench > 0:
        z = z + (DEEP - z) * trench * _smooth((g - 30000) / 40000)
    # Seamounts: steep cones with rounded tops a diver can reach.
    for mx, my, top, radius in SEAMOUNT_SITES:
        d = math.hypot(x - mx, y - my)
        if d < radius * 2.0:
            # A little past 1 at the middle, so every top is flat at its depth whatever the noise does.
            rise = math.exp(-(d / radius) ** 2 * 2.2) * 1.12 * (1 + .12 * (noise(x, y, 6000, 41) - .5))
            z = max(z, z + ((SEA - top) - z) * min(1.0, rise))
            # Rock: knobs and ledges over its flanks and top, a metre or two.
            if rise > .02:
                z += (noise(x, y, 1400, 43) - .5) * 350 * min(1.0, rise * 3) + (noise(x, y, 450, 44) - .5) * 120 * min(1.0, rise * 3)
    return max(DEEP, min(z, SEA - 600))


def height_raw(x, y):
    """Ground (or sea floor) height in cm at (x, y), before the caves' notches."""
    best, nearest, closest = None, 1e18, None
    for i in W.ISLANDS:
        d = i.distance(x, y)
        if d < nearest:
            nearest, closest = d, i
        if d > SHELF * 1.5:
            continue
        ripple = 30 * math.sin(x / 700 + 0.5) * math.sin(y / 900 + 1.1) + 15 * math.sin((x + y) / 330)
        if d > 0:
            # Past the shelf the island's own slope gives way to the open sea floor (floor_at).
            h = seabed(d) + ripple - max(0.0, d - SHELF) * 2
        elif i.key == 'Starter':
            h = starter_ground(i, x, y, d, ripple)
        else:
            h = island_land(i, x, y, -d)
        best = h if best is None else max(best, h)
    floor = floor_at(x, y, nearest, closest)
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
        self.cell = ground_spacing(island)       # the island mesh's grid
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


# Each region's code in the terrain's vertex alpha, for its own soils (owner, October 16:
# CLAUDE.md); M_CoastalTerrain_v1 reads it.
REGION_CODES = {'Winter': .1, 'Plains': .3, 'Jungle': .5, 'Swamp': .7, 'Desert': .9}


def region_code(x, y):
    """The nearest island's region code (REGION_CODES), for the terrain's vertex alpha."""
    return REGION_CODES[min(W.ISLANDS, key=lambda k: k.distance(x, y)).region]


# ---- The ground as built --------------------------------------------------------------------------------------

def grid_of(island):
    """The island mesh's grid as build_coastal_terrain.py builds it: (x0, y0, step x, step y, cells x, cells y)."""
    reach = island.reach() + SHELF
    spacing = ground_spacing(island)
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

