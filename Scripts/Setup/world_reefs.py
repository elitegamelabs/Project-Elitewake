"""The five major reefs: one off each canonical island. Plain Python (no Unreal): where each reef lies and where
its corals grow; build_reefs.py builds them.

Each reef sits on the sandy shelf 17 to 30 m from shore where the sea is about 3 to 20 m deep, clear of its island's
Port, cave and landmarks. A reef is a patch about 45 m long along the shore and 13 m deep across it, thick with
corals in the middle and thinning at its edges. Sizes and counts are tuning.
"""
import math
import random

import world_layout as W
import world_terrain as T
from world_landmarks import near_landmark

PER_REGION = {'Plains': 1, 'Winter': 1, 'Swamp': 1, 'Desert': 1, 'Jungle': 1}
CORALS = 70                       # per reef (tuning)
KINDS = ('branching', 'mound', 'fan', 'pillar')
OUT = (1700.0, 3000.0)            # cm beyond the shore


class Reef:
    def __init__(self, key, island, angle, corals):
        self.key, self.island, self.angle, self.corals = key, island, angle, corals
        r = island.radius(angle) + sum(OUT) / 2
        self.cx, self.cy = island.cx + r * math.cos(angle), island.cy + r * math.sin(angle)

    def near(self, x, y, margin=0.0):
        return any(math.hypot(x - c[0], y - c[1]) < 300 + margin for c in self.corals)


def _site_clear(island, a):
    for along in (-2600, 0, 2600):
        for out in (OUT[0] - 500, OUT[1] + 500):
            r = island.radius(a) + out
            x = island.cx + r * math.cos(a) - along * math.sin(a)
            y = island.cy + r * math.sin(a) + along * math.cos(a)
            if W.near_port(x, y, 1500) or T.near_cave(x, y, 1000) or near_landmark(x, y, 1200):
                return False
            if not T.SEA - 2600 < T.height(x, y) < T.SEA - 250:
                return False
    return True


def _corals(island, a, rng):
    out = []
    tries = 0
    while len(out) < CORALS and tries < CORALS * 40:
        tries += 1
        along = rng.gauss(0, 1300)
        across = rng.uniform(*OUT)
        if abs(along) > 2300:
            continue
        r = island.radius(a) + across
        x = island.cx + r * math.cos(a) - along * math.sin(a)
        y = island.cy + r * math.sin(a) + along * math.cos(a)
        if any(math.hypot(x - c[0], y - c[1]) < 160 for c in out):
            continue
        kind = rng.choices(KINDS, weights=(4, 3, 2, 2))[0]
        out.append((x, y, kind, rng.uniform(.7, 1.5), rng.uniform(0, 360), rng.randrange(5)))
    return out


def _reefs():
    rng = random.Random(6006)
    found = []
    for region, count in PER_REGION.items():
        # Every island has a Port, so choose a different, clear section of its shore.
        options = [i for i in W.ISLANDS if i.region == region]
        rng.shuffle(options)
        for island in options:
            if sum(1 for r in found if r.island.region == region) >= count:
                break
            angles = [2 * math.pi * k / 24 for k in range(24)]
            rng.shuffle(angles)
            a = next((a for a in angles if _site_clear(island, a)), None)
            if a is None:
                continue
            n = sum(1 for r in found if r.island.region == region) + 1
            found.append(Reef(f'{region}{n}', island, a, _corals(island, a, rng)))
    return found


REEFS = _reefs()


def near_reef(x, y, margin=500.0):
    return any(r.near(x, y, margin) for r in REEFS)


if __name__ == '__main__':
    for r in REEFS:
        depths = [T.height(c[0], c[1]) - T.SEA for c in r.corals]
        print(f'{r.key:8s} off {r.island.key:8s} at ({r.cx / 100:7.0f}, {r.cy / 100:7.0f}) m  {len(r.corals)} corals, '
              f'{-max(depths) / 100:.1f}-{-min(depths) / 100:.1f} m deep')
    print(len(REEFS), 'reefs')
