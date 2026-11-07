"""The three open-ocean reefs (owner, October 31: "like 3 reefs out in the ocean"). Plain Python (no Unreal): where each
reef lies and where its corals grow; build_reefs.py builds them.

Each reef crowns one of the seamounts that rise in the open water between the islands (world_terrain.SEAMOUNT_SITES): the
three shallowest, 12 to 20 m under the surface, each more than 2 km from any shore and far from every port, and in
three different directions from the starter. A reef is a patch about 60 m across on the seamount's top, thick with corals
in the middle and thinning at its edges. Sizes and counts are tuning.
(Before November 6 this file placed one reef off each island's shore; that layout was never built into the map.)
"""
import math
import random

import world_layout as W
import world_terrain as T

COUNT = 3                         # owner, October 31
CORALS = 70                       # per reef (tuning)
KINDS = ('branching', 'mound', 'fan', 'pillar')
SPREAD = 1500.0                   # cm: the corals' scatter about the reef's centre (one standard deviation)
EDGE = 3200.0                     # cm: no coral farther from the centre than this
SHALLOWEST, DEEPEST = 300.0, 2600.0   # cm under the surface where a coral may stand


class Reef:
    def __init__(self, key, site, corals):
        self.key = key
        self.seamount = site[2]          # its index in world_terrain.SEAMOUNT_SITES (mesh SM_Seamount_<index + 1>_v1)
        self.cx, self.cy = site[0], site[1]
        self.corals = corals
        # The nearest island, for the record only (an open-ocean reef belongs to no island).
        self.island = min(W.ISLANDS, key=lambda i: math.hypot(i.cx - self.cx, i.cy - self.cy))

    def near(self, x, y, margin=0.0):
        return any(math.hypot(x - c[0], y - c[1]) < 300 + margin for c in self.corals)


def _corals(site, rng):
    out, tries = [], 0
    while len(out) < CORALS and tries < CORALS * 60:
        tries += 1
        dx, dy = rng.gauss(0, SPREAD), rng.gauss(0, SPREAD)
        if math.hypot(dx, dy) > EDGE:
            continue
        x, y = site[0] + dx, site[1] + dy
        if not T.SEA - DEEPEST < T.height(x, y) < T.SEA - SHALLOWEST:
            continue
        if any(math.hypot(x - c[0], y - c[1]) < 160 for c in out):
            continue
        kind = rng.choices(KINDS, weights=(4, 3, 2, 2))[0]
        out.append((x, y, kind, rng.uniform(.7, 1.5), rng.uniform(0, 360), rng.randrange(5)))
    return out


def _sites():
    """The shallowest seamount tops, clear of every port."""
    tops = sorted((T.SEA - T.height(x, y), x, y, n) for n, (x, y, _, _) in enumerate(T.SEAMOUNT_SITES))
    return [(x, y, n) for depth, x, y, n in tops if depth < DEEPEST and not W.near_port(x, y, 60000)][:COUNT]


def _reefs():
    rng = random.Random(6006)
    return [Reef(f'Ocean{n + 1}', site, _corals(site, rng)) for n, site in enumerate(_sites())]


REEFS = _reefs()


def near_reef(x, y, margin=500.0):
    return any(r.near(x, y, margin) for r in REEFS)


if __name__ == '__main__':
    for r in REEFS:
        depths = [T.height(c[0], c[1]) - T.SEA for c in r.corals]
        shore = min(math.hypot(i.cx - r.cx, i.cy - r.cy) - i.reach() for i in W.ISLANDS)
        print(f'{r.key:7s} at ({r.cx / 100:7.0f}, {r.cy / 100:7.0f}) m, nearest {r.island.key:8s} {shore / 100:5.0f} m off its shore, '
              f'{len(r.corals)} corals, {-max(depths) / 100:.1f}-{-min(depths) / 100:.1f} m deep, kinds {sorted({c[2] for c in r.corals})}')
    print(len(REEFS), 'reefs')
