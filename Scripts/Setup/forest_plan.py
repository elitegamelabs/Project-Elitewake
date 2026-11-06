"""Where every forest tree and bush stands (owner, November 6: trees densely populated throughout, strategically placed,
with lots of bushes, and plenty of open ground to move through, like a real forest; trees of every size, thickness,
shape and kind). Plain Python, no Unreal; build_forests.py places the result in the map.
    python Scripts/Setup/forest_plan.py            # writes Saved/ForestPlan.json (all cores, a few minutes)

DECIDED (owner-delegated, all tuning):
- Stands, not scatter. A smooth noise field over each island marks forest (above STAND), with clearings and meadows
  between; trees thin out toward a stand's edge, where saplings and bushes gather, and a few lone trees stand in the open.
  How much of each region is forest: COVER.
- Each region's own mix (CLAUDE.md 5.2: the primary tree leads, secondary species add variety; birch never in the Swamp):
  MIX. The Desert keeps its palms near the shore and water, in groves.
- Every tree its own size: an age (sapling, young, grown, old, giant), then its own girth and height on top, a lean
  (more on slopes and at the edge) and a turn. Six models of each species (build_forests.py).
- Trunks keep their species' spacing apart (SPACING, metres), so the floor between them stays open to walk.
- Kept off: beaches (7 m inland), steep ground, ports and villages, caves, climb-outs, landmarks, and the starter's
  old ground with its own authored oaks. build_forests.py also keeps them off rocks and gatherable plants.
"""
import json
import math
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from world_landmarks import near_landmark  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / 'Saved' / 'ForestPlan.json'
MIX = {'Plains': {'Oak': .68, 'Ash': .2, 'Birch': .12},
       'Winter': {'Birch': .62, 'Spruce': .38},
       'Swamp': {'Spruce': .8, 'Ash': .2},
       'Desert': {'Palm': 1.0},
       'Jungle': {'Ash': .58, 'Maravai': .42}}
SPACING = {'Oak': 9.0, 'Maravai': 8.0, 'Ash': 6.0, 'Birch': 5.0, 'Spruce': 5.5, 'Palm': 6.0}   # metres between trunks
VARIANTS = 6
# The noise level above which ground is forest, per region (lower = more forest). Jungle is the densest, the Plains the
# most open, the Desert only groves.
STAND = {'Plains': .53, 'Winter': .47, 'Swamp': .5, 'Jungle': .38, 'Desert': .6}
LONE = {'Plains': .05, 'Winter': .02, 'Swamp': .03, 'Jungle': .05, 'Desert': .01}   # chance of a lone tree in the open
MAX_TREES = 14000          # per island: a budget for the minimum machine (CLAUDE.md 9.6), measured in Play
MAX_BUSHES = 9000
CELL = 400.0               # cm: candidate spacing
BEACH = 700.0              # cm inland from the shore before trees start
SLOPE = math.tan(math.radians(34))
# Ages: (share, scale range). Girth and height then vary on their own.
AGES = [('sapling', .1, (.38, .58)), ('young', .22, (.62, .85)), ('grown', .5, (.85, 1.18)),
        ('old', .14, (1.18, 1.42)), ('giant', .04, (1.42, 1.72))]


def _hash(ix, iy, seed):
    n = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFF) / float(0xFFFFFF)


def _value(x, y, size, seed):
    gx, gy = x / size, y / size
    ix, iy = math.floor(gx), math.floor(gy)
    fx, fy = gx - ix, gy - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


def forest_level(x, y, seed):
    """0-1: how much this ground is forest. Broad stands about 300 m across, broken by smaller clearings."""
    return .62 * _value(x, y, 32000.0, seed) + .28 * _value(x, y, 11000.0, seed + 7) + .1 * _value(x, y, 4000.0, seed + 13)


def _smooth(a, b, v):
    t = min(1.0, max(0.0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def plan_island(key):
    island = W.island(key)
    region = island.region
    rng = random.Random(sum(map(ord, key)) * 92821)
    seed = sum(map(ord, key)) * 31
    stand, mix = STAND[region], MIX[region]
    kinds, weights = list(mix), list(mix.values())
    reach = island.reach()
    trees, bushes = [], []
    cells = {}                       # 10 m grid -> trunks (x, y, spacing cm)

    def crowded(x, y, gap):
        cx, cy = int(x // 1000), int(y // 1000)
        for i in range(cx - 1, cx + 2):
            for j in range(cy - 1, cy + 2):
                for px, py, pg in cells.get((i, j), ()):
                    if math.hypot(x - px, y - py) < max(gap, pg) * .5 + min(gap, pg) * .5:
                        return True
        return False

    steps = int(2 * reach / CELL)
    order = [(i, j) for i in range(steps) for j in range(steps)]
    rng.shuffle(order)               # no row-by-row bias in who gets the space
    for i, j in order:
        if len(trees) >= MAX_TREES and len(bushes) >= MAX_BUSHES:
            break
        x = island.cx - reach + (i + rng.random()) * CELL
        y = island.cy - reach + (j + rng.random()) * CELL
        inland = -island.distance(x, y)
        if inland < 300:
            continue
        level = forest_level(x, y, seed)
        edge = _smooth(stand - .06, stand + .1, level)          # 0 in the open, 1 deep in a stand
        if region == 'Desert':
            edge *= _smooth(3500.0, 1500.0, inland)            # palms keep near the shore (and its oases)
        roll = rng.random()
        tree_p = LONE[region] + (1 - LONE[region]) * edge * .9
        bush_p = .02 + .45 * math.exp(-((level - stand) / .05) ** 2) + .1 * edge   # thickest along the forest's edge
        if region == 'Desert':
            bush_p *= .35
        want_tree = roll < tree_p and inland > BEACH and len(trees) < MAX_TREES
        want_bush = not want_tree and rng.random() < bush_p and len(bushes) < MAX_BUSHES
        if not (want_tree or want_bush):
            continue
        if W.near_port(x, y) or T.near_cave(x, y) or T.near_climb(x, y) or near_landmark(x, y):
            continue
        if key == 'Starter' and island.old.distance(x, y) < 1500:
            continue                   # the starter's old ground keeps its own oaks and plants
        z = T.height(x, y)
        if z < T.SEA + 60:
            continue
        gx, gy = T.height(x + 200, y) - z, T.height(x, y + 200) - z
        slope = math.hypot(gx, gy) / 200
        if slope > SLOPE:
            continue
        if want_bush:
            bushes.append([round(x), round(y), round(z), round(rng.uniform(0, 360)), round(rng.uniform(.7, 1.6) * (1.2 if edge > .3 else 1), 2)])
            continue
        kind = rng.choices(kinds, weights)[0]
        r, age, scale = rng.random(), None, None
        for name, share, span in AGES:
            r -= share
            if r <= 0:
                age, scale = name, rng.uniform(*span)
                break
        if age is None:
            age, scale = 'grown', 1.0
        if edge < .5 and age in ('old', 'giant'):
            age, scale = 'grown', rng.uniform(.85, 1.15)         # the biggest trees stand deep in the stands
        gap = SPACING[kind] * 100 * (.45 if age == 'sapling' else .7 if age == 'young' else 1.0) * min(1.3, max(.8, scale))
        if crowded(x, y, gap):
            continue
        girth = scale * rng.uniform(.82, 1.22)
        height = scale * rng.uniform(.9, 1.12)
        lean = rng.uniform(0, 3.0 + 6.0 * min(1.0, slope / SLOPE) + (3.0 if edge < .4 else 0))
        heading = rng.uniform(0, 2 * math.pi)
        trees.append([kind, rng.randrange(VARIANTS), round(x), round(y), round(z), round(rng.uniform(0, 360)),
                      round(lean * math.cos(heading), 1), round(lean * math.sin(heading), 1), round(girth, 3), round(height, 3)])
        cells.setdefault((int(x // 1000), int(y // 1000)), []).append((x, y, gap))
    return key, {'trees': trees, 'bushes': bushes}


def plan(keys=None, workers=14):
    keys = [i.key for i in W.ISLANDS if not keys or i.key in keys]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return dict(pool.map(plan_island, keys))


if __name__ == '__main__':
    found = plan(sys.argv[1:] or None)
    OUT.write_text(json.dumps(found))
    for key, v in found.items():
        by = {}
        for t in v['trees']:
            by[t[0]] = by.get(t[0], 0) + 1
        print(key, len(v['trees']), 'trees', by, len(v['bushes']), 'bushes')
