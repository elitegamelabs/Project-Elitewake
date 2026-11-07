"""The canonical world (CLAUDE.md 5.1 and 5.7; owner, November 1): twenty islands, four per region, each its own organic shape
and land area, one village per region, and relief of several smaller hills spread round each island, never one dominant
central mountain. Walking times are screened by Scripts/Setup/estimate_walking_times.py and measured in game."""
import math
import os
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)
import world_islands as I  # noqa: E402
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

M = W.M


class TwentyIslandTests(unittest.TestCase):
    def test_four_islands_per_region_and_the_plan_keys(self):
        for region in W.REGION_CENTRES:
            self.assertEqual(sum(1 for i in W.ISLANDS if i.region == region), 4, region)
        self.assertEqual(sorted(i.key for i in W.ISLANDS), sorted(I.ISLANDS))
        for i in W.ISLANDS:
            self.assertEqual(i.region, I.ISLANDS[i.key]['region'], i.key)
        self.assertEqual(W.check(W.ISLANDS)[0], [])

    def test_one_port_per_region_at_its_village(self):
        self.assertEqual(set(W.PORTS), set(W.REGION_CENTRES))
        for region, port in W.PORTS.items():
            self.assertEqual(port.island.key, I.VILLAGES[region], region)
        self.assertEqual(W.PORTS['Plains'].island.key, 'Starter', 'Saltreach stays on the starter island')

    def test_village_island_is_the_region_island_nearest_the_centre(self):
        for region, key in I.VILLAGES.items():
            if region == 'Plains':
                continue
            nearest = min((i for i in W.ISLANDS if i.region == region), key=lambda i: math.hypot(i.cx, i.cy))
            self.assertEqual(nearest.key, key, region)

    def test_coasts_are_irregular_not_ellipses(self):
        for i in W.ISLANDS:
            if i.key == 'Starter':
                continue
            dev = max(abs(i.radius(a) / (1.0 / math.sqrt((math.cos(a - i.turn) / i.rx) ** 2 + (math.sin(a - i.turn) / i.ry) ** 2)) - 1)
                      for a in [2 * math.pi * k / 360 for k in range(360)])
            self.assertGreater(dev, 0.12, f'{i.key} is nearly an ellipse')

    def test_no_two_outlines_are_alike(self):
        def signature(i):
            r = [i.radius(2 * math.pi * k / 72) for k in range(72)]
            m = sum(r) / len(r)
            return [x / m for x in r]
        signatures = {i.key: signature(i) for i in W.ISLANDS}
        for a in W.ISLANDS:
            for b in W.ISLANDS:
                if a.key >= b.key:
                    continue
                sa, sb = signatures[a.key], signatures[b.key]
                # the same shape turned: compare against every rotation
                best = min(sum((sa[k] - sb[(k + s) % 72]) ** 2 for k in range(72)) for s in range(72))
                self.assertGreater(best, 0.05, f'{a.key} and {b.key} are the same shape turned')

    def test_land_areas_differ(self):
        areas = sorted(sum(.5 * i.radius(2 * math.pi * k / 360) ** 2 * (2 * math.pi / 360) for k in range(360)) / 1e10
                       for i in W.ISLANDS if i.key != 'Starter')
        self.assertTrue(all(b - a > .005 for a, b in zip(areas, areas[1:])), f'two islands share a land area: {areas}')

    def test_hills_spread_round_the_island_none_in_the_middle(self):
        # CLAUDE.md 5.1: several smaller hills, never one dominant central mountain.
        for key, (plan, shapes) in T.TERRAIN_PLANS.items():
            i = W.island(key)
            raised = [s for s in shapes if s[0] != 'valley']
            self.assertGreaterEqual(len(raised), 2, f'{key} has fewer than two hills')
            for s in raised:
                out = math.hypot(s[1] / i.rx, s[2] / i.ry)
                self.assertGreater(out, .3, f'{key}: a {s[0]} stands in the middle')
        for i in W.ISLANDS:
            if i.key == 'Starter':
                continue
            for x, y, radius, height in i.features:
                self.assertGreater(math.hypot(x, y) / min(i.rx, i.ry), .25, f'{i.key}: a hill in the middle')

    def test_plains_island_keeps_the_spawn_headland(self):
        starter = W.island('Starter')
        self.assertLess(starter.distance(-800.0, -100.0), 0, 'the old centre is no longer on the Plains island')


if __name__ == '__main__':
    unittest.main()
