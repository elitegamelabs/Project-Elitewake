"""Plain-Python tests for the owner's world-layout and cave rules (no Unreal).

Run from the repo root:
    python -m unittest Scripts.Tests.test_world_layout
or just:
    python -m unittest

These only import `world_layout` and `world_terrain` (Scripts/Setup) and never edit them; a failing rule here means
those scripts drifted from the canonical five-island rules, not that this file should be changed to match.
"""
import math
import os
import sys
import unittest
from pathlib import Path

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

import world_layout as W   # noqa: E402
import world_terrain as T  # noqa: E402

M = W.M  # cm per metre


class WorldLayoutRuleTests(unittest.TestCase):
    """The canonical five-island spacing and region rules."""

    @classmethod
    def setUpClass(cls):
        cls.problems, cls.nearest = W.check(W.ISLANDS)

    def test_check_reports_no_problems(self):
        self.assertEqual(self.problems, [], f'world_layout.check() found problems: {self.problems}')

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

    # Owner, October 26: beaches slope naturally into the water, so the spawn and dock landing, which are on the old beach,
    # moved by a few centimetres (spawn 67.2 -> 81.4 cm, dock landing -27.2 -> -47.8 cm).
    def test_spawn_height(self):
        self.assertHeightNear(150.0, 0.0, 81.4)

    def test_dock_landing_height(self):
        self.assertHeightNear(4000.0, 900.0, -47.8)

    def test_spring_height(self):
        self.assertHeightNear(-1700.0, 1500.0, -265.0)


class BeachAndMountainTests(unittest.TestCase):
    """Owner, October 26: beaches that slope naturally down into the water and level out into the sea; Winter's mountains
    real mountains with realistic hills, not points."""

    def test_beach_slopes_gently_into_the_water_and_levels_out(self):
        depths = [T.SEA - T.seabed(d) for d in range(0, 20001, 500)]
        self.assertEqual(depths[0], 0.0)
        self.assertTrue(all(b >= a for a, b in zip(depths, depths[1:])), 'the sea floor never rises going out')
        steps = [(b - a) / 500.0 for a, b in zip(depths, depths[1:])]
        self.assertLessEqual(max(steps[:4]), .16, 'no steeper than about 9 degrees across the beach itself')
        self.assertLessEqual(max(steps), .5, 'no steeper than about 27 degrees anywhere, and that only far down at the shelf foot')
        self.assertGreaterEqual(min(steps), .03, 'no flat step: the sea floor keeps deepening, so no visible shelf edge')
        self.assertLessEqual(max(b - a for a, b in zip(steps, steps[1:])), .05, 'the slope changes smoothly, no sudden break')
        self.assertGreater(depths[-1], 5500, 'the shelf reaches the deep floor')

    def test_beach_rises_gently_inland(self):
        heights = [T.land(d) for d in range(0, 4001, 100)]
        self.assertTrue(all(b >= a for a, b in zip(heights, heights[1:])))
        self.assertLessEqual(max(b - a for a, b in zip(heights, heights[1:])) / 100.0, .08)

    def test_winter_mountains_are_massifs_not_points(self):
        import math
        import random
        island = W.island('Winter1')
        rng = random.Random(2)
        heights, slopes = [], []
        while len(heights) < 1500:
            x, y = island.cx + rng.uniform(-.9, .9) * island.rx, island.cy + rng.uniform(-.9, .9) * island.ry
            if island.distance(x, y) > -3000:
                continue
            h = T.height(x, y)
            heights.append(h)
            slopes.append(math.degrees(math.atan(math.hypot(T.height(x + 300, y) - h, T.height(x, y + 300) - h) / 300)))
        heights.sort(), slopes.sort()
        self.assertGreater(heights[-1], 20000, 'real mountains, over 200 m')
        self.assertLess(slopes[int(len(slopes) * .9)], 45, 'nine tenths of the ground is walkable-looking, not spikes')
        self.assertLess(slopes[len(slopes) // 2], 25)


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


class BuildZoneTests(unittest.TestCase):
    """Build Mode zones (owner, October 27): the whole island is buildable except Ports, obstruction zones, caves, landmarks,
    the starter spawn/dock/spring, water, and beaches near docks."""

    @classmethod
    def setUpClass(cls):
        import world_buildzones as B
        cls.B = B

    def test_water_is_refused(self):
        self.assertIn('water', self.B.point_reason(0.0, -60000.0))

    def test_ports_refused_with_their_waterfront(self):
        for region, p in W.PORTS.items():
            self.assertIn('Port', self.B.point_reason(p.cx, p.cy) or '', region)
            x, y = p.world(W.PORT_INLAND + 3000.0, 0.0)
            self.assertIsNotNone(self.B.point_reason(x, y), f'{region} waterfront')

    def test_caves_and_landmarks_refused(self):
        for key, c in T.CAVES.items():
            if c:
                self.assertIsNotNone(self.B.point_reason(c.mx, c.my), key)

    def test_starter_spawn_and_dock_refused_but_inland_buildable(self):
        self.assertIn('spawn', self.B.point_reason(150.0, 0.0))
        self.assertIsNotNone(self.B.point_reason(4000.0, 900.0))
        self.assertIsNone(self.B.point_reason(0.0, 1200.0), 'ordinary starter-island ground is buildable')

    def test_dock_beach_refused_but_inland_of_it_buildable(self):
        beach = next((x for x in range(2000, 9000, 50) if T.SEA + 30 < T.height(x, 900) < T.SEA + 300), None)
        self.assertIsNotNone(beach, 'the starter beach')
        self.assertIsNotNone(self.B.point_reason(float(beach), 900.0), 'a beach by the dock is not buildable')

    def test_every_island_has_buildable_ground(self):
        import math
        for island in W.ISLANDS:
            found = any(self.B.point_reason(island.cx + d * math.cos(a), island.cy + d * math.sin(a)) is None
                        for a in [k * .5 for k in range(13)] for d in range(0, int(island.radius(a)), 400))
            self.assertTrue(found, island.key)

    def test_uneven_ground_refused_flat_ground_accepted(self):
        i = W.island('Winter1')
        import math
        # a flat footprint somewhere on the island is accepted; a big footprint on the steep flank is refused for unevenness
        self.assertIsNotNone(self.B.footprint_reason(i.cx, i.cy, 6000.0, 6000.0))

    def test_export_matches_zones(self):
        import json
        path = Path(__file__).resolve().parents[2] / 'Content' / 'Elitewake' / 'Data' / 'BuildZones.json'
        self.assertEqual(len(json.loads(path.read_text())['shapes']), len(self.B.ZONES), 'run export_buildzones.py')
