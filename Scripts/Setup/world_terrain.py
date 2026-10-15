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
    elif i.region == 'Swamp':
        # Low ground with pools and winding channels that fall below the waterline.
        channel = abs(math.sin(lx / 900 + 2 * math.sin(ly / 1300)) * math.sin(ly / 1100 + 1.3 * math.sin(lx / 1700)))
        # About a metre above the sea (lower and the ocean's surface reads over it), the pools well below it.
        h = SEA + 60 + min(inland, 600) / 600 * 100 + rise * (40 * math.sin(lx / 330) * math.sin(ly / 290))
        h -= rise * 300 * max(0.0, 0.35 - channel) / 0.35
        h = min(h, SEA + 160 + i.peak * rise * 0.6)
    cliff = CLIFFS.get(i.key)
    if cliff:
        ca, half, height = cliff
        a = math.atan2(ly, lx)
        d = math.atan2(math.sin(a - ca), math.cos(a - ca))
        side = max(0.0, 1.0 - abs(d) / half)
        if side > 0:
            # Past a 2-3 m strip of beach the ground climbs steeply to the cliff top.
            climb = min(1.0, max(0.0, (inland - 250) / 900))
            h = max(h, land(inland) + height * side ** .6 * climb ** .7)
    return h


def floor_at(x, y, nearest_gap):
    """The sea floor between islands: 60 m deep, falling to 500 m only well out in the open sea."""
    far = min(1.0, max(0.0, (nearest_gap - 90000) / 60000))
    far = far * far * (3 - 2 * far)
    return FLOOR + (DEEP - FLOOR) * far


def height(x, y):
    """Ground (or sea floor) height in cm at (x, y)."""
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
            h = starter_land(x, y, -d, ripple)
        else:
            h = island_land(i, x, y, -d)
        best = h if best is None else max(best, h)
    floor = floor_at(x, y, nearest)
    return floor if best is None else max(best, floor)


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

