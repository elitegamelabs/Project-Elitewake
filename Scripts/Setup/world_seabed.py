"""Where the sea floor's life grows: seagrass meadows, kelp forests, corals, sea fans and sponges on every island's
underwater slopes and on the seamounts (owner, October 17: dynamic sea-floor scenery, corals and aquatic plants).
Plain Python (no Unreal); build_seabed_life.py builds and lays them.

The canonical world guide in CLAUDE.md keeps each kind to the depths it suits, and each
region's water favours its own: kelp forests in the cold Winter sea, corals thickest in the warm Jungle and Desert
seas, seagrass meadows thickest in the sheltered Plains and the murky Swamp. The glowing major reefs (world_reefs.py)
stay as they are and nothing else grows on them. Everything grows in patches, never as an even carpet. All counts,
depths and sizes are tuning; the looks need owner visual review.
"""
import math
import random

import world_layout as W
import world_terrain as T
from world_landmarks import near_landmark
from world_reefs import REEFS

# Per kind: the depths it grows at (m) and how far out from the shore it is looked for (cm).
DEPTHS = {'Seagrass': (1.5, 14.0), 'Kelp': (5.0, 28.0), 'Coral': (2.0, 30.0), 'Fan': (8.0, 45.0), 'Sponge': (10.0, 60.0)}
# Per region: how many of each per metre of shoreline (before patchiness and depth thin them out).
PER_METRE = {
    'Plains': {'Seagrass': 9.0, 'Kelp': .4, 'Coral': .8, 'Fan': .25, 'Sponge': .4},
    'Jungle': {'Seagrass': 5.0, 'Coral': 2.6, 'Fan': .8, 'Sponge': .5},
    'Desert': {'Seagrass': 3.0, 'Coral': 2.4, 'Fan': .9, 'Sponge': .35},
    'Swamp': {'Seagrass': 11.0, 'Coral': .25, 'Sponge': .7},
    'Winter': {'Seagrass': 2.0, 'Kelp': 4.5, 'Fan': .2, 'Sponge': .6},
}
# On a seamount's top and flanks, per square metre within diving depth.
SEAMOUNT_PER_M2 = {'Coral': .05, 'Fan': .02, 'Sponge': .02, 'Kelp': .02, 'Seagrass': .08}
SHORE_OUT = (300.0, 9000.0)   # cm offshore searched
KELP_TOP_CLEAR = 250.0        # cm of water kept over a kelp's tip


def patches(x, y, kind):
    """0-1: meadows and forests with gaps and clearings, at two scales; each kind its own."""
    seed = sum(map(ord, kind))
    return min(1.0, max(0.0, (T.noise(x, y, 2500, seed) - .3) * 1.8 + (T.noise(x, y, 600, seed + 1) - .5) * .6))


def _clear(x, y):
    return not (W.near_port(x, y, 1200) or T.near_cave(x, y, 600) or near_landmark(x, y, 600)
                or any(r.near(x, y, 600) for r in REEFS))


def _spot(kind, x, y, z, rng):
    depth = (T.SEA - z) / 100
    lo, hi = DEPTHS[kind]
    if not lo <= depth <= hi:
        return None
    if kind == 'Kelp':
        scale = min(3.2, (T.SEA - z - KELP_TOP_CLEAR) / 600.0 * rng.uniform(.65, 1.0))
        if scale < .5:
            return None
    else:
        scale = rng.uniform(.7, 1.4) if kind != 'Seagrass' else rng.uniform(.75, 1.3)
    return (x, y, z, scale, rng.uniform(0, 360))


def island_life(island, ground):
    """{kind: [(x, y, z, scale, yaw)]} round one island; `ground(x, y)` gives the built sea floor height."""
    rng = random.Random(sum(map(ord, island.key)) * 4093)
    shore = 2 * math.pi * island.reach() / 100
    out = {}
    for kind, per in PER_METRE[island.region].items():
        placed = []
        for _ in range(int(shore * per * 2.2)):
            a = rng.uniform(0, 2 * math.pi)
            r = island.radius(a) + rng.uniform(*SHORE_OUT)
            x, y = island.cx + r * math.cos(a), island.cy + r * math.sin(a)
            if rng.random() > patches(x, y, kind) or not _clear(x, y):
                continue
            z = ground(x, y)
            spot = z is not None and _spot(kind, x, y, z, rng)
            if spot:
                placed.append(spot)
        out[kind] = placed
    return out


def seamount_life(index, ground):
    """{kind: [...]} on one seamount (world_terrain.SEAMOUNT_SITES), its region the nearest island's."""
    mx, my, top, radius = T.SEAMOUNT_SITES[index]
    region = min(W.ISLANDS, key=lambda i: i.distance(mx, my)).region
    rng = random.Random(9001 + index)
    area = math.pi * (radius * .9 / 100) ** 2
    out = {}
    for kind, per in SEAMOUNT_PER_M2.items():
        if kind == 'Kelp' and region not in ('Winter', 'Plains'):
            continue
        if kind == 'Coral' and region == 'Winter':
            continue
        placed = []
        for _ in range(int(area * per * 2.0)):
            a, d = rng.uniform(0, 2 * math.pi), radius * .9 * math.sqrt(rng.random())
            x, y = mx + d * math.cos(a), my + d * math.sin(a)
            if rng.random() > patches(x, y, kind):
                continue
            z = ground(x, y)
            spot = z is not None and _spot(kind, x, y, z, rng)
            if spot:
                placed.append(spot)
        out[kind] = placed
    return region, out
