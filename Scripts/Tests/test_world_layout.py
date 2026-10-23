"""Plain-Python tests for the owner's world-layout and cave rules (no Unreal).

Run from the repo root:
    python -m unittest Scripts.Tests.test_world_layout
or just:
    python -m unittest

These only import `world_layout` and `world_terrain` (Scripts/Setup) and never edit them; a failing rule here means
those scripts drifted from the owner's decisions, not that this file should be changed to match. See
`Docs/DELEGATED_TASKS.md` T12 and `Docs/VERIFICATION.md` for how this is run and recorded.
"""
import math
import os
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

import world_layout as W   # noqa: E402
import world_terrain as T  # noqa: E402

M = W.M  # cm per metre


class WorldLayoutRuleTests(unittest.TestCase):
    """The owner's spacing and region rules (Docs/METRIC_WORLD_SCALE_AND_ISLAND_SPACING_2026-10-15.md et al.)."""

    @classmethod
    def setUpClass(cls):
        cls.problems, cls.nearest = W.check(W.ISLANDS)

    def test_check_reports_no_problems(self):
        self.assertEqual(self.problems, [], f'world_layout.check() found problems: {self.problems}')

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_at_least_five_islands_per_region(self):
        for region in W.REGION_CENTRES:
            n = sum(1 for i in W.ISLANDS if i.region == region)
            self.assertGreaterEqual(n, 5, f'{region} has only {n} islands')

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_at_least_five_islands_round_the_starter(self):
        around = [i for i in W.ISLANDS if i.region == 'Plains' and i.key != 'Starter']
        self.assertGreaterEqual(len(around), 5, f'only {len(around)} islands round the starter')

    def test_every_pair_at_least_800m_apart(self):
        islands = W.ISLANDS
        for a_i, a in enumerate(islands):
            for b in islands[a_i + 1:]:
                if W.quick_gap(a, b) > 4 * W.MAX_GAP:
                    continue
                gap = W.shore_gap(a, b)
                self.assertGreaterEqual(gap, W.MIN_GAP - 1.0,
                                         f'{a.key} and {b.key} are {gap / M:.0f} m apart (< 800 m)')

    def test_every_island_has_a_neighbour_within_2000m(self):
        for i in W.ISLANDS:
            gap = self.nearest.get(i.key, 1e18)
            self.assertLessEqual(gap, W.MAX_GAP + 1.0,
                                  f'{i.key} is {gap / M:.0f} m from its nearest island (> 2,000 m)')

    def test_each_region_on_its_side_of_the_world(self):
        sides = {'Winter': lambda i: i.cy > 0, 'Swamp': lambda i: i.cy < 0,
                  'Desert': lambda i: i.cx > 0, 'Jungle': lambda i: i.cx < 0}
        for i in W.ISLANDS:
            check = sides.get(i.region)
            if check is None:
                continue  # Plains sits at the world centre; no side to check
            self.assertTrue(check(i), f'{i.key} lies on the wrong side of the world for {i.region}')

    def test_starter_island_geometry_unchanged(self):
        old = W.island('Starter').old
        self.assertEqual((old.cx, old.cy), (-800.0, -100.0))
        self.assertEqual((old.rx, old.ry), (5100.0, 4100.0))
        self.assertAlmostEqual(old.wobble, 0.03, places=6)


class WorldTerrainHeightTests(unittest.TestCase):
    """Fixed reference heights (Saved/CoastalTerrainResult.json `ground_cm`): spawn, dock landing, spring."""

    def assertHeightNear(self, x, y, expected_cm, tolerance_cm=1.0):
        got = T.height(x, y)
        self.assertAlmostEqual(got, expected_cm, delta=tolerance_cm,
                                msg=f'height({x}, {y}) = {got:.2f} cm, expected ~{expected_cm} cm')

    def test_spawn_height(self):
        self.assertHeightNear(150.0, 0.0, 67.2)

    def test_dock_landing_height(self):
        self.assertHeightNear(4000.0, 900.0, -27.2)

    def test_spring_height(self):
        self.assertHeightNear(-1700.0, 1500.0, -265.0)


class CaveRuleTests(unittest.TestCase):
    """Owner addition, October 15 night: one cave per island, all three kinds, footprints clear of the island's
    shore and every Port, and a walkable approach to the mouth."""

    @classmethod
    def setUpClass(cls):
        cls.caves = T.CAVES

    def test_every_island_has_exactly_one_cave(self):
        island_keys = {i.key for i in W.ISLANDS}
        self.assertEqual(set(self.caves.keys()), island_keys,
                          'CAVES does not have exactly one entry per island')
        missing = [key for key, cave in self.caves.items() if cave is None]
        self.assertEqual(missing, [], f'no cave was placed for: {missing}')

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_all_three_cave_kinds_occur(self):
        kinds = {cave.kind for cave in self.caves.values() if cave}
        self.assertEqual(kinds, set(T.CAVE_KINDS), f'only saw kinds {kinds}, expected {set(T.CAVE_KINDS)}')

    def test_cave_footprints_lie_on_their_own_island_and_off_every_port(self):
        for key, cave in self.caves.items():
            island = cave.island
            for x, y in cave.footprint():
                self.assertLess(island.distance(x, y), 0,
                                 f'{key} cave footprint point ({x:.0f}, {y:.0f}) is off its island {island.key}')
                self.assertFalse(W.near_port(x, y),
                                  f'{key} cave footprint point ({x:.0f}, {y:.0f}) falls inside a Port site')

    def test_approach_to_each_mouth_is_not_too_steep(self):
        # 3 m in front of the mouth: ground no more than 2 m below the floor. 6 m in front: no more than 4 m below.
        for key, cave in self.caves.items():
            for distance_m, max_drop_m in ((3.0, 2.0), (6.0, 4.0)):
                fx, fy = cave.world(distance_m * M, 0.0)
                ground = T.height_raw(fx, fy)
                drop = cave.floor - ground
                self.assertLessEqual(drop, max_drop_m * M + 1.0,
                                      f'{key} cave: ground {distance_m} m from the mouth is '
                                      f'{drop / M:.2f} m below the floor (> {max_drop_m} m)')


if __name__ == '__main__':
    unittest.main()
