"""One natural landmark per island, so each is known by sight from the sea. Plain Python (no Unreal): where each
landmark stands and its size; build_landmarks.py builds them and the dressing scripts keep off them.

Owner, October 15 (STARTER_ISLAND_CENTRAL_PLAINS_DIRECTION, METRIC_WORLD_SCALE..., REGIONAL_WORLD_AND_3D_ASSET
_REQUIREMENTS): islands have their own silhouettes, landmarks and skylines; do not clone one island across the world.
DECIDED (delegated): the landmark kinds and which island gets which, by region, cycling so neighbours differ:
  - sea stacks: two to four tall rock pillars standing in the shallows off the shore;
  - arch: a natural rock arch straddling the shoreline, one foot on the beach and one in the sea, walkable under;
  - stones: a ring of nine standing stones on the island's highest open ground;
  - spire: a lone rock pinnacle inland (Winter's capped with snow, the Desert's a hoodoo with a cap rock);
  - snag: the bleached trunk of a giant dead tree with bare branches (Swamp).
The starter island gets sea stacks off its west shore, away from the spawn and the dock. Sizes are tuning.
"""
import math
import random

import world_layout as W
import world_terrain as T

KINDS = {'Plains': ('stones', 'stacks', 'arch'), 'Desert': ('arch', 'spire', 'stacks'),
         'Winter': ('spire', 'stacks', 'arch'), 'Jungle': ('stacks', 'arch', 'spire'), 'Swamp': ('snag', 'snag', 'stacks')}


class Landmark:
    """`parts`: (x, y, ground z, size) per piece; `angle`: the shore direction it was placed on (radians)."""

    def __init__(self, island, kind, parts, angle, reach):
        self.island, self.kind, self.parts, self.angle, self.reach = island, kind, parts, angle, reach

    def near(self, x, y, margin=0.0):
        return any(math.hypot(x - px, y - py) < self.reach + margin for px, py, _, _ in self.parts)


def _clear(island, x, y, room):
    """Somewhere a landmark may stand: off the Ports and the caves, and on the starter island off its spawn, dock and
    spring."""
    if W.near_port(x, y, room) or T.near_cave(x, y, room):
        return False
    if island.key == 'Starter':
        return all(math.hypot(x - cx, y - cy) > r + room for cx, cy, r in T.STARTER_CLEAR)
    return True


def _stacks(island, rng):
    for k in rng.sample(range(36), 36):
        a = 2 * math.pi * k / 36
        if island.key == 'Starter' and math.cos(a) > -0.5:
            continue                                  # the starter's west shore only
        r = island.radius(a)
        out = r + rng.uniform(1600, 2400)
        cx, cy = island.cx + out * math.cos(a), island.cy + out * math.sin(a)
        if not _clear(island, cx, cy, 2500):
            continue
        parts = []
        for n in range(rng.randint(2, 4)):
            along = (n - 1) * rng.uniform(700, 1100)
            px, py = cx - along * math.sin(a), cy + along * math.cos(a)
            px += rng.uniform(-300, 300) * math.cos(a)
            py += rng.uniform(-300, 300) * math.sin(a)
            size = rng.uniform(1300, 2600) * (1.25 if n == 0 else 1.0)
            parts.append((px, py, T.height(px, py), size))
        if all(z < T.SEA - 150 for _, _, z, _ in parts):
            return Landmark(island, 'stacks', parts, a, 600)
    return None


def _arch(island, rng):
    for k in rng.sample(range(36), 36):
        a = 2 * math.pi * k / 36
        r = island.radius(a)
        inner, outer = r - 700, r + 1100
        ax, ay = island.cx + inner * math.cos(a), island.cy + inner * math.sin(a)
        bx, by = island.cx + outer * math.cos(a), island.cy + outer * math.sin(a)
        mx, my = (ax + bx) / 2, (ay + by) / 2
        if not _clear(island, mx, my, 2200) or T.CLIFFS.get(island.key) and abs(math.atan2(math.sin(a - T.CLIFFS[island.key][0]), math.cos(a - T.CLIFFS[island.key][0]))) < T.CLIFFS[island.key][1] + .3:
            continue
        za, zb = T.height(ax, ay), T.height(bx, by)
        if za < T.SEA + 30 or za > T.SEA + 250 or zb > T.SEA - 100:
            continue                                  # one foot on the beach, the other in the sea
        return Landmark(island, 'arch', [(ax, ay, za, 0.0), (bx, by, zb, 0.0)], a, 500)
    return None


def _stones(island, rng):
    best = None
    for _ in range(500):
        rr, t = math.sqrt(rng.random()) * island.reach(), rng.uniform(0, 2 * math.pi)
        x, y = island.cx + rr * math.cos(t), island.cy + rr * math.sin(t)
        if island.distance(x, y) > -2500 or not _clear(island, x, y, 1500):
            continue
        z = T.height(x, y)
        flat = max(abs(T.height(x + 700 * math.cos(b), y + 700 * math.sin(b)) - z) for b in (0, 1.57, 3.14, 4.71))
        if flat < 250 and (best is None or z > best[2]):
            best = (x, y, z)
    if not best:
        return None
    x, y, z = best
    parts = []
    for n in range(9):
        b = 2 * math.pi * n / 9 + rng.uniform(-.08, .08)
        px, py = x + 700 * math.cos(b), y + 700 * math.sin(b)
        parts.append((px, py, T.height(px, py), rng.uniform(.85, 1.2)))
    return Landmark(island, 'stones', parts, math.atan2(y - island.cy, x - island.cx), 250)


def _spire(island, rng):
    for _ in range(400):
        rr, t = math.sqrt(rng.random()) * island.reach(), rng.uniform(0, 2 * math.pi)
        x, y = island.cx + rr * math.cos(t), island.cy + rr * math.sin(t)
        d = island.distance(x, y)
        if not -4000 < d < -1500 or not _clear(island, x, y, 1500):
            continue
        z = T.height(x, y)
        if max(abs(T.height(x + 500 * math.cos(b), y + 500 * math.sin(b)) - z) for b in (0, 1.57, 3.14, 4.71)) < 300:
            return Landmark(island, 'spire', [(x, y, z, rng.uniform(2200, 3400))], t, 700)
    return None


def _snag(island, rng):
    for _ in range(400):
        rr, t = math.sqrt(rng.random()) * island.reach(), rng.uniform(0, 2 * math.pi)
        x, y = island.cx + rr * math.cos(t), island.cy + rr * math.sin(t)
        if not -3500 < island.distance(x, y) < -900 or not _clear(island, x, y, 1200):
            continue
        z = T.height(x, y)
        if z > T.SEA + 40:
            return Landmark(island, 'snag', [(x, y, z, rng.uniform(1600, 2200))], t, 400)
    return None


BUILD = {'stacks': _stacks, 'arch': _arch, 'stones': _stones, 'spire': _spire, 'snag': _snag}


def _landmark(island, index):
    rng = random.Random(sum(map(ord, island.key)) * 7027)
    order = ('stacks',) if island.key == 'Starter' else KINDS[island.region][index % 3:] + KINDS[island.region][:index % 3]
    for kind in order + ('stacks', 'spire'):
        found = BUILD[kind](island, rng)
        if found:
            return found
    return None


def _landmarks():
    found, count = {}, {}
    for island in W.ISLANDS:
        count[island.region] = count.get(island.region, -1) + 1
        found[island.key] = _landmark(island, count[island.region])
    return found


LANDMARKS = _landmarks()


# Sand and sandstone pillars (owner, October 16, BIOME_TERRAIN_FOLIAGE_AND_GLOBAL_SUN: occasional tall sandstone or
# sand pillars, permitted on any island where they fit, not on every island). DECIDED (delegated, tuning): three to
# five on each Desert island, standing 9-20 m out of the dunes at least 40 m apart; one each on two Plains islands
# with open ground. Some are hoodoos under a cap rock.
PILLAR_ISLANDS = {'Starter': 1}


def _pillars(island, rng, count):
    parts = []
    for _ in range(600):
        if len(parts) >= count:
            break
        rr, t = math.sqrt(rng.random()) * island.reach(), rng.uniform(0, 2 * math.pi)
        x, y = island.cx + rr * math.cos(t), island.cy + rr * math.sin(t)
        if not island.distance(x, y) < -1800 or not _clear(island, x, y, 1500) or near_landmark(x, y, 1500):
            continue
        if any(math.hypot(x - px, y - py) < 4000 for px, py, _, _ in parts):
            continue
        z = T.height(x, y)
        if z < T.SEA + 100 or max(abs(T.height(x + 400 * math.cos(b), y + 400 * math.sin(b)) - z) for b in (0, 1.57, 3.14, 4.71)) > 350:
            continue
        parts.append((x, y, z, rng.uniform(900, 2000)))
    return Landmark(island, 'pillars', parts, 0.0, 450) if parts else None


def _all_pillars():
    found = {}
    for island in W.ISLANDS:
        count = PILLAR_ISLANDS.get(island.key) or (random.Random(sum(map(ord, island.key)) * 389).randint(3, 5) if island.region == 'Desert' else 0)
        if count:
            found[island.key] = _pillars(island, random.Random(sum(map(ord, island.key)) * 9151), count)
    return found


def near_landmark(x, y, margin=300.0):
    """True on or beside a landmark or a pillar: keep trees, rocks, plants and animals off it."""
    return any(m and m.near(x, y, margin) for m in LANDMARKS.values()) or any(m and m.near(x, y, margin) for m in PILLARS.values())


PILLARS = {}
PILLARS = _all_pillars()


if __name__ == '__main__':
    for key, m in LANDMARKS.items():
        print(f'{key:10s} {m.kind if m else "NONE":7s} parts {len(m.parts) if m else 0}  '
              + ' '.join(f'({x / 100:.0f},{y / 100:.0f} z{z / 100:.1f} s{s:.0f})' for x, y, z, s in (m.parts[:3] if m else [])))
