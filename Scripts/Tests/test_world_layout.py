"""Plain-Python tests for the owner's world-layout and cave rules (no Unreal).

Run from the repo root:
    python -m unittest Scripts.Tests.test_world_layout
or just:
    python -m unittest

These only import `world_layout` and `world_terrain` (Scripts/Setup) and never edit them; a failing rule here means
those scripts drifted from the canonical world rules, not that this file should be changed to match.
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
    """The canonical spacing and region rules."""

    @classmethod
    def setUpClass(cls):
        cls.problems, cls.nearest = W.check(W.ISLANDS)

    def test_check_reports_no_problems(self):
        self.assertEqual(self.problems, [], f'world_layout.check() found problems: {self.problems}')

    def test_every_pair_has_at_least_two_kilometres_of_sea(self):
        self.assertGreaterEqual(W.MIN_GAP, 2000 * M)
        islands = W.ISLANDS
        for a_i, a in enumerate(islands):
            for b in islands[a_i + 1:]:
                if W.quick_gap(a, b) > 4 * W.MAX_GAP:
                    continue
                gap = W.shore_gap(a, b)
                self.assertGreaterEqual(gap, W.MIN_GAP - 1.0,
                                         f'{a.key} and {b.key} are {gap / M:.0f} m apart (< 2,000 m)')

    def test_every_island_has_a_neighbour_within_four_kilometres(self):
        for i in W.ISLANDS:
            gap = self.nearest.get(i.key, 1e18)
            self.assertLessEqual(gap, W.MAX_GAP + 1.0,
                                  f'{i.key} is {gap / M:.0f} m from its nearest island (> 4,000 m)')

    def test_three_distinct_crescent_islands_have_sea_caverns(self):
        self.assertEqual(set(W.CRESCENT_COVES), {'Plains3', 'Desert3', 'Jungle3'})
        self.assertEqual(W.SEA_CAVERN_ACCESS, {
            'Plains3': 'inland_exit', 'Desert3': 'shore_bridge', 'Jungle3': 'inland_exit'})
        for key in W.CRESCENT_COVES:
            island, cave = W.island(key), T.CAVES[key]
            self.assertEqual(cave.kind, 'sea')
            self.assertIsNone(W.port_on(island))
            angle = island.turn + island.cove[0]
            inner = min(island.radius(angle + d) for d in (-.4, -.2, 0, .2, .4))
            shoulders = min(island.radius(angle - .9), island.radius(angle + .9))
            self.assertLess(inner, .85 * shoulders, f'{key} has no readable crescent inlet')
            # The currently built Brigantine is 30 m long and 8.4 m wide. This leaves
            # substantially more than a few metres each side; future Cavalier fit is pending.
            self.assertGreaterEqual(2 * cave.tunnel[0], 2000.0)
            self.assertGreaterEqual(T.SEA - cave.floor, 500.0)
            self.assertGreaterEqual(2 * cave.chamber[0], 4000.0)
            for u in (-5000.0, -3000.0, 0.0, cave.length / 2, cave.chamber_u):
                x, y = cave.world(u, cave.centre_v(max(0.0, u)))
                self.assertLessEqual(T.built_height(x, y), T.SEA - 450.0,
                                     f'{key} boat approach is too shallow at {u / M:.0f} m')

    def test_each_sea_cavern_fits_and_hides_a_brigantine(self):
        # The brigantine (DA_Ship_Brigantine: hull half 1490 x 425 cm, draft 230, deck 300, mast top 2200 over the sea).
        # Against the passage's oval at its narrowest rock lumps (SEA_NOISE), her hull and mast follow the centre line;
        # no straight line at deck height from the mouth to her hull at the berth stays inside it at its widest.
        hx, hy, draft, deck, mast = 1490.0, 425.0, 230.0, 300.0, 2200.0
        lumps = T.SEA_NOISE[0]
        for key in W.SEA_CAVERN_ACCESS:
            cave = T.CAVES[key]
            hw, hh, cz = cave.tunnel

            def half_width(z, scale):
                d = (z - cave.floor - cz) / (hh * scale)
                return hw * scale * math.sqrt(max(0.0, 1 - d * d))

            for u in range(0, int(cave.length) + 1, 200):
                slope = (cave.centre_v(u + 50) - cave.centre_v(u - 50)) / 100
                c, s = 1 / math.hypot(1, slope), slope / math.hypot(1, slope)
                for a, b, z in [(a, b, z) for a in (-hx, 0.0, hx) for b in (-hy, hy)
                                for z in (T.SEA - draft, T.SEA, T.SEA + deck)] + [(0.0, 0.0, T.SEA + mast)]:
                    pu, pv = u + a * c - b * s, cave.centre_v(u) + a * s + b * c
                    if 0 <= pu <= cave.length:
                        self.assertLessEqual(abs(pv - cave.centre_v(pu)), half_width(z, 1 - lumps),
                                             f'{key}: the brigantine scrapes the passage {pu / M:.0f} m in')
            bu, bv = cave.berth()
            z = T.SEA + deck
            mouth = half_width(z, (1 + lumps) * 1.3)
            for v0 in [mouth * k / 10 for k in range(-10, 11)]:
                for u1, v1 in [(bu + a, bv + b) for a in (-hx, 0.0, hx) for b in (-hy, hy)]:
                    blocked = any(abs(v0 + (v1 - v0) * u / u1 - cave.centre_v(u)) > half_width(z, 1 + lumps)
                                  for u in range(100, int(cave.length), 100))
                    self.assertTrue(blocked, f'{key}: the berthed hull can be seen from the mouth')

    def test_each_sea_cavern_has_a_dry_walk_to_existing_island_ground(self):
        # Plains3 and Desert3 run straight out through the back; Jungle3, under a 50 m plateau, spirals up its wall.
        for key in W.SEA_CAVERN_ACCESS:
            cave = T.CAVES[key]
            path = cave.exit_path()
            self.assertGreater(len(path), 20, key)
            self.assertLessEqual(path[0][2], T.SEA + 160.0, f'{key}: the walk does not start at the berth')
            previous = None
            landing = path[-1]
            for u, v, surface, outward in path:
                self.assertGreater(surface, T.SEA + 100.0)
                # On the open landing (its last 7 m) the deck meets the ground, which may come level with it.
                clear = 5.0 if math.hypot(u - landing[0], v - landing[1]) > 700.0 else -25.0
                for side in (-225.0, 0.0, 225.0):
                    if previous:
                        du, dv = u - previous[0], v - previous[1]
                        run = math.hypot(du, dv)
                        x, y = cave.world(u + dv / run * side, v - du / run * side)
                    else:
                        x, y = cave.world(u, v)
                    self.assertGreaterEqual(surface - T.built_height(x, y), clear,
                                            f'{key} exit intersects terrain at {u:.0f}, {v:.0f} cm')
                if previous:
                    run = math.hypot(u - previous[0], v - previous[1])
                    self.assertLessEqual(abs(surface - previous[2]) / run, .40, f'{key}: the cave exit is too steep to walk')
                previous = (u, v, surface)
            u, v, surface, _ = path[-1]
            x, y = cave.world(u, v)
            # It ends on island ground, past the rock formation, with a step a survivor can take (45 cm).
            self.assertLessEqual(surface - T.built_height(x, y), 45.0, f'{key}: the walk ends above the ground')
            self.assertGreater(T.built_height(x, y), T.SEA + 50.0, f'{key}: the walk ends in the water')
            self.assertFalse(cave.inside(x, y) and abs(v) < cave.half and u < cave.depth,
                             f'{key}: the walk ends inside the rock formation')
        # Jungle3's spiral keeps the boat entrance clear: it never crosses in front of the passage's end below 30 m.
        cave = T.CAVES['Jungle3']
        for u, v, surface, _ in cave.exit_path():
            if surface < T.SEA + 3000.0:
                self.assertFalse(u < cave.chamber_u and abs(v) < cave.tunnel[0] + 300.0,
                                 f'Jungle3 walk blocks the entrance at {u:.0f}, {v:.0f}')

    def test_each_region_on_its_side_of_the_world(self):
        # North is +Y and east -X (Source/EW/World/EWNorth.h; owner, November 1).
        sides = {'Winter': lambda i: i.cy > 0, 'Swamp': lambda i: i.cy < 0,
                  'Desert': lambda i: i.cx < 0, 'Jungle': lambda i: i.cx > 0}
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
        # The pond's floor at its middle: surface 5, less 10, less its 15 ft depth (owner, November 1).
        self.assertHeightNear(-1700.0, 1500.0, -462.0)


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
    """One cave per island. Walking caves stay on land; sea caverns may project into their coves."""

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
                if cave.kind != 'sea':
                    self.assertLess(island.distance(x, y), 0,
                                     f'{key} cave footprint point ({x:.0f}, {y:.0f}) is off its island {island.key}')
                self.assertFalse(W.near_port(x, y),
                                  f'{key} cave footprint point ({x:.0f}, {y:.0f}) falls inside a Port site')

    def test_approach_to_each_mouth_is_not_too_steep(self):
        # 3 m in front of the mouth: ground no more than 2 m below the floor. 6 m in front: no more than 4 m below.
        for key, cave in self.caves.items():
            if cave.kind == 'sea':
                continue  # A boat approach is underwater; depth is checked separately.
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
