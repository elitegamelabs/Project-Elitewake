"""Where each island's mined specialty lies (CLAUDE.md 5.7, owner, November 1: each island has its own specialty, present
on it and absent from the rest of its region). Plain Python (no Unreal); build_specialty_ores.py builds the deposits.

The mined specialties (November 7):
    copper ore   P2 Copper Downs, D4 Copper Canyon, J2 Gem Ridge     on hill slopes
    iron ore     P2 Copper Downs, W3 Iron Cliffs, D4 Copper Canyon   on hill slopes
    sulfur ore   D2 Sulfur Flats (Desert only, CLAUDE.md 4)          on low flats (vents and evaporite)
    salt         D3 Salt Pans                                        on low flats near the shore
    amber        D4 Copper Canyon                                    on hill slopes
    bog iron     S2 Bog Fen                                          on wet low ground
Coal (W1) and the cave and mountainside gems are build_crystals.py's. Clay, peat, resin, herbs and the like are gathered,
not mined, and come later.

Deposits lie in short veins (three to five nodes a few metres apart along a line), the veins spread over suitable ground
of the island, clear of caves, climb-outs, ports and landmarks, and apart from each other. Counts are tuning.
"""
import math
import random

import world_layout as W
import world_terrain as T
from world_landmarks import near_landmark

# Ore: (item key, display name, description, pickaxe tier, islands, habitat, nodes per island)
ORES = {
    'CopperOre': ('Copper Ore', 'Green-streaked rock rich in copper, for smelting.', 'NONE',
                  ('Plains2', 'Desert4', 'Jungle2'), 'slope', 14),
    'IronOre': ('Iron Ore', 'Rust-red rock rich in iron, for smelting.', 'NONE',
                ('Plains2', 'Winter3', 'Desert4'), 'slope', 14),
    'SulfurOre': ('Sulfur Ore', 'Yellow crusted rock from the desert vents: the base of gunpowder.', 'METAL',
                  ('Desert2',), 'flat', 16),
    'Salt': ('Salt', 'White salt crust from the pans, for preserving food.', 'NONE',
             ('Desert3',), 'flat', 16),
    'Amber': ('Amber', 'Golden fossil resin from the canyon sandstone.', 'NONE',
              ('Desert4',), 'slope', 8),
    'BogIron': ('Bog Iron', 'Rusty lumps of iron from the bog: poor ore, but ore.', 'NONE',
                ('Swamp2',), 'low', 14),
}
VEIN = (3, 5)            # nodes per vein
STEP = 450.0             # cm between nodes along a vein
APART = 3500.0           # cm between veins' starts on one island


def _fits(habitat, island, x, y):
    inland = -island.distance(x, y)
    if inland < 600 or T.near_cave(x, y, 700) or T.near_climb(x, y, 400) or W.near_port(x, y, 3000) or near_landmark(x, y, 600):
        return False
    z = T.height(x, y)
    slope = max(abs(T.height(x + 200, y) - z), abs(T.height(x, y + 200) - z)) / 200
    if habitat == 'slope':
        return z > T.SEA + 1500 and .15 < slope < .9            # up the hills, not on the flats or a cliff face
    if habitat == 'flat':
        return T.SEA + 60 < z < T.SEA + 1200 and slope < .12
    if habitat == 'low':
        return T.SEA + 30 < z < T.SEA + 300 and slope < .2
    return z > T.SEA + 30


def plan_island(ore, island, count, habitat, rng, taken=()):
    """[(x, y)] for one ore on one island: veins of a few nodes in a line, clear of another ore's nodes (`taken`)."""
    nodes, starts, tries = [], [], 0
    reach = island.reach()
    while len(nodes) < count and tries < 20000:
        tries += 1
        x, y = island.cx + rng.uniform(-reach, reach), island.cy + rng.uniform(-reach, reach)
        if not _fits(habitat, island, x, y) or any(math.hypot(x - sx, y - sy) < APART for sx, sy in starts):
            continue
        heading = rng.uniform(0, 2 * math.pi)
        vein = []
        for k in range(rng.randint(*VEIN)):
            vx = x + math.cos(heading) * STEP * k + rng.uniform(-80, 80)
            vy = y + math.sin(heading) * STEP * k + rng.uniform(-80, 80)
            if not _fits(habitat, island, vx, vy) or any(math.hypot(vx - tx, vy - ty) < 1500 for tx, ty in taken):
                break
            vein.append((vx, vy))
        if len(vein) < 2:
            continue
        starts.append((x, y))
        nodes += vein[:count - len(nodes)]
    return nodes


def _plan():
    out, taken = {}, {}
    islands = {i.key: i for i in W.ISLANDS}
    for ore, (_, _, _, isles, habitat, count) in ORES.items():
        rng = random.Random(sum(map(ord, ore)) * 7919)
        out[ore] = {}
        for key in isles:
            out[ore][key] = plan_island(ore, islands[key], count, habitat, rng, taken.get(key, []))
            taken.setdefault(key, []).extend(out[ore][key])
    return out


PLAN = _plan()


if __name__ == '__main__':
    for ore, isles in PLAN.items():
        for key, nodes in isles.items():
            zs = [T.height(x, y) - T.SEA for x, y in nodes]
            print(f'{ore:10s} {key:8s} {len(nodes):3d} nodes, {min(zs) / 100:5.1f}-{max(zs) / 100:5.1f} m above the sea')
