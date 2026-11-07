"""Where each island's gathered specialty lies (CLAUDE.md 5.7, owner, November 1: every island has its own specialty, present
on it and absent from the rest of its region). Plain Python (no Unreal); build_gathered_specialties.py places them.

Gathered by hand with E (AEWHandGatherable), November 7:
    clay, sand       P3 Clay Shore         clay on low ground by the water, sand on the beach band
    reeds            S1 River Isle         wet low ground
    peat             S2 Bog Fen            wet low ground
    resin            S3 Resin Woods        at the foot of spruces
    mushrooms        S4 Mushroom Hollows   under the trees
    dates, coconuts  D1 Oasis Isle         under the palms (food)
    wild fruit       J1 Waterfall Basin    under the trees (food)
    spices           J3 Spice Isle         inland
    vines            J4 Vine Woods         under the trees
The mined specialties are world_specialty_ores.py's. Forest trees come from the forest plan (Saved/ForestPlan.json, written by
forest_plan.py). Counts and yields are tuning.
"""
import json
import math
import random
from pathlib import Path

import world_layout as W
import world_terrain as T
from world_landmarks import near_landmark

# Key: (display name, description, gathering kind, food, islands, habitat, tree species or None, nodes per island, (yield range))
ITEMS = {
    'Clay': ('Clay', 'Wet river clay for bricks, pots and caulking.', 'LOOSE_STONES', None, ('Plains3',), 'low', None, 16, (3, 6)),
    'Sand': ('Sand', 'Clean shore sand, for glass and mortar.', 'LOOSE_STONES', None, ('Plains3',), 'shore', None, 14, (4, 8)),
    'Reeds': ('Reeds', 'Long river reeds for thatch, mats and baskets.', 'PLANT_FIBER', None, ('Swamp1',), 'low', None, 18, (3, 6)),
    'Peat': ('Peat', 'Dense bog turf that dries into slow-burning fuel.', 'LOOSE_STONES', None, ('Swamp2',), 'low', None, 16, (3, 6)),
    'Resin': ('Spruce Resin', 'Sticky spruce resin: the base of pitch for caulking a hull.', 'PLANT_FIBER', None,
              ('Swamp3',), 'trees', 'Spruce', 18, (2, 4)),
    'Mushrooms': ('Mushrooms', 'Pale woodland mushrooms, prized by cooks and healers.', 'PLANT_FIBER', None,
                  ('Swamp4',), 'trees', None, 18, (2, 5)),
    'Dates': ('Dates', 'Sweet oasis dates. Restores a little hunger; keeps for an hour.', 'BERRIES',
              dict(hunger=1 / 12, health=.03, fresh=3600), ('Desert1',), 'trees', 'Palm', 16, (3, 6)),
    'Coconuts': ('Coconut', 'A ripe coconut: food and drink in one. Keeps for two hours.', 'BERRIES',
                 dict(hunger=1 / 8, health=.04, fresh=7200), ('Desert1',), 'trees', 'Palm', 12, (1, 3)),
    'WildFruit': ('Wild Fruit', 'Ripe jungle fruit. Restores some hunger; keeps for 20 minutes.', 'BERRIES',
                  dict(hunger=1 / 10, health=.04, fresh=1200), ('Jungle1',), 'trees', None, 18, (3, 6)),
    'Spices': ('Spices', 'Fragrant bark and seed spices: a valuable trade good.', 'PLANT_FIBER', None,
               ('Jungle3',), 'inland', None, 16, (2, 4)),
    'Vines': ('Vines', 'Tough jungle vines, twisted into rope.', 'PLANT_FIBER', None, ('Jungle4',), 'trees', None, 18, (3, 6)),
}
APART = 900.0            # cm between nodes of one island


def _forest_trees():
    path = Path(__file__).resolve().parents[2] / 'Saved' / 'ForestPlan.json'
    if not path.exists():
        return {}
    plan = json.loads(path.read_text())
    return {key: [(t[0], t[2], t[3]) for t in v['trees']] for key, v in plan.items()}


def _fits(habitat, island, x, y):
    inland = -island.distance(x, y)
    if T.near_cave(x, y, 600) or T.near_climb(x, y, 400) or W.near_port(x, y, 3000) or near_landmark(x, y, 500):
        return False
    z = T.height(x, y)
    if habitat == 'shore':
        return 300 < inland < 2500 and T.SEA + 20 < z < T.SEA + 250
    if habitat == 'low':
        return inland > 400 and T.SEA + 30 < z < T.SEA + 400
    return inland > 600 and z > T.SEA + 40


def plan_island(key, island, habitat, species, count, rng, trees, taken=()):
    nodes, tries = [], 0
    reach = island.reach()
    candidates = [(x, y) for kind, x, y in trees.get(island.key, []) if species in (None, kind)] if habitat == 'trees' else None
    while len(nodes) < count and tries < 20000:
        tries += 1
        if candidates:
            tx, ty = rng.choice(candidates)
            a = rng.uniform(0, 2 * math.pi)
            x, y = tx + math.cos(a) * rng.uniform(150, 350), ty + math.sin(a) * rng.uniform(150, 350)   # at the tree's foot
        else:
            x, y = island.cx + rng.uniform(-reach, reach), island.cy + rng.uniform(-reach, reach)
        if not _fits('inland' if habitat == 'trees' else habitat, island, x, y):
            continue
        if any(math.hypot(x - nx, y - ny) < APART for nx, ny in nodes) or any(math.hypot(x - tx, y - ty) < 400 for tx, ty in taken):
            continue
        nodes.append((x, y))
    return nodes


def _plan():
    trees = _forest_trees()
    islands = {i.key: i for i in W.ISLANDS}
    out, taken = {}, {}
    for key, (_, _, _, _, isles, habitat, species, count, _) in ITEMS.items():
        rng = random.Random(sum(map(ord, key)) * 4241)
        out[key] = {}
        for k in isles:
            out[key][k] = plan_island(key, islands[k], habitat, species, count, rng, trees, taken.get(k, []))
            taken.setdefault(k, []).extend(out[key][k])
    return out


PLAN = _plan()


if __name__ == '__main__':
    for key, isles in PLAN.items():
        for island, nodes in isles.items():
            print(f'{key:10s} {island:8s} {len(nodes):3d} of {ITEMS[key][7]}')
