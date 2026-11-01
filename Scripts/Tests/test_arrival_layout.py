"""The Plains arrival (CLAUDE.md Phase 1, slice 1) measured on the ground the terrain builder makes: the spawn's first view
holds a 3-6 m route, an oak group, a low freshwater cue and a distant Saltreach cue, with the sea off to one side."""
import math
import os
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)
import arrival_layout as A  # noqa: E402
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

HALF_FOV = 35.0                 # the guide's 70-degree horizontal view
EYE = 170.0                     # cm, a survivor's eye above the ground
S = A.SPAWN


def in_view(x, y, margin=0.0):
    return abs(A.relative(A.SPAWN_YAW, A.bearing(S[0], S[1], x, y))) <= HALF_FOV - margin


def visible_water(yaw, eye, maxd=30000):
    """Distance in cm to the first water surface seen along a bearing from the spawn's eye, or None."""
    r = math.radians(yaw)
    c, s = math.cos(r), math.sin(r)
    steepest = -1e9
    for d in range(100, maxd, 100):
        h = T.height(S[0] + d * c, S[1] + d * s)
        slope = (max(h, T.SEA) - eye) / d
        if h < T.SEA and slope >= steepest:
            return d
        steepest = max(steepest, slope)
    return None


class ArrivalLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ground = T.height(*S)
        cls.eye = cls.ground + EYE
        cls.route = A.smoothed_route()

    def test_spawn_stands_on_the_plains_beach(self):
        island = min(W.ISLANDS, key=lambda i: i.distance(*S))
        self.assertEqual(island.region, 'Plains')
        self.assertGreater(self.ground, T.SEA + 40, 'spawn must be dry')
        inland = -island.distance(*S)
        self.assertTrue(600 <= inland <= 3000, f'spawn {inland / 100:.0f} m inland; a beach start is 6-30 m from the water')

    def test_sea_is_to_one_side_not_ahead(self):
        rays = {a: visible_water(A.SPAWN_YAW + a, self.eye) for a in range(-int(HALF_FOV), int(HALF_FOV) + 1)}
        wet = [a for a, d in rays.items() if d is not None]
        self.assertLessEqual(len(wet) / len(rays), .2, f'water fills {len(wet)} of {len(rays)} degrees of the view')
        self.assertTrue(all(a >= 20 for a in wet) or all(a <= -20 for a in wet), f'water seen at {wet}')
        nearest = min((d, a) for a, d in ((a, visible_water(A.SPAWN_YAW + a, self.eye, 15000)) for a in range(-180, 180, 2)) if d)
        self.assertGreaterEqual(abs(nearest[1]), 30, f'nearest sea {nearest[0] / 100:.0f} m at {nearest[1]} degrees')

    def test_saltreach_lighthouse_reads_in_the_first_view(self):
        lx, ly, lz = A.SALTREACH_LIGHT
        self.assertTrue(in_view(lx, ly, 5), 'lighthouse outside the 70-degree view')
        distance = math.hypot(lx - S[0], ly - S[1])
        self.assertTrue(45000 <= distance <= 70000, f'Saltreach {distance / 100:.0f} m away')
        # The top 8 m of the lighthouse clear the ground between (trees and buildings are checked in Play).
        target = lz - 800
        n = int(distance / 200)
        for k in range(1, n - 10):
            f = k / n
            line = self.eye + (target - self.eye) * f
            ground = T.height(S[0] + (lx - S[0]) * f, S[1] + (ly - S[1]) * f)
            self.assertGreater(line, ground + 20, f'ground hides the lighthouse {f * distance / 100:.0f} m out')

    def test_route_is_a_traversable_track_to_saltreach(self):
        self.assertTrue(300 <= A.ROUTE_WIDTH <= 600)
        start, end = self.route[0], self.route[-1]
        self.assertLess(math.hypot(start[0] - S[0], start[1] - S[1]), 300)
        port = W.PORTS['Plains']
        self.assertLess(math.hypot(end[0] - port.cx, end[1] - port.cy), 6000, 'route stops short of Saltreach')
        for a, b in zip(self.route, self.route[1:]):
            run = math.hypot(b[0] - a[0], b[1] - a[1])
            self.assertLess(abs(T.height(*b) - T.height(*a)) / run, .2, f'steep at {a}')
            nx, ny = -(b[1] - a[1]) / run, (b[0] - a[0]) / run
            for w in (-A.ROUTE_WIDTH / 2, 0, A.ROUTE_WIDTH / 2):
                self.assertGreater(T.height(a[0] + nx * w, a[1] + ny * w), T.SEA + 40, f'wet at {a}')
        # Its first 20 m are in the first view.
        ahead = next(p for p in self.route if math.hypot(p[0] - S[0], p[1] - S[1]) > 2000)
        self.assertTrue(in_view(*ahead, 10))

    def test_oak_group_frames_the_view_without_blocking(self):
        self.assertTrue(3 <= len(A.OAKS) <= 5)
        lx, ly, _ = A.SALTREACH_LIGHT
        sight = A.bearing(S[0], S[1], lx, ly)
        for x, y, scale in A.OAKS:
            d = math.hypot(x - S[0], y - S[1])
            self.assertTrue(2000 <= d <= 6000, f'oak {d / 100:.0f} m away')
            self.assertTrue(in_view(x, y))
            self.assertGreater(abs(A.relative(sight, A.bearing(S[0], S[1], x, y))), 8, 'oak in the line to Saltreach')
            self.assertGreater(A.distance_to_route(x, y), A.ROUTE_WIDTH / 2 + 400, 'oak on the route')
            self.assertGreater(T.height(x, y), T.SEA + 60)
        for i, a in enumerate(A.OAKS):
            for b in A.OAKS[i + 1:]:
                self.assertGreater(math.hypot(a[0] - b[0], a[1] - b[1]), 600, 'oaks crowd together')
        spacings = sorted(math.hypot(a[0] - b[0], a[1] - b[1]) for i, a in enumerate(A.OAKS) for b in A.OAKS[i + 1:])
        self.assertGreater(spacings[-1] - spacings[0], 300, 'oaks evenly spaced like a grid')

    def test_spring_is_a_low_freshwater_cue_beside_the_route(self):
        x, y = A.SPRING
        d = math.hypot(x - S[0], y - S[1])
        self.assertTrue(1000 <= d <= 4000, f'spring {d / 100:.0f} m away')
        self.assertTrue(in_view(x, y, 5))
        self.assertGreater(A.distance_to_route(x, y), A.ROUTE_WIDTH / 2 + A.SPRING_RADIUS + 150)
        e = 150.0
        slope = math.hypot(T.height(x + e, y) - T.height(x - e, y), T.height(x, y + e) - T.height(x, y - e)) / (2 * e)
        self.assertLess(slope, .1, 'spring on a slope')
        self.assertGreater(T.height(x, y), T.SEA + 60)

    def test_first_resources_can_be_gathered_into_a_stone_hatchet(self):
        kinds = {kind for _, kind, *_ in A.FIRST_RESOURCES}
        self.assertTrue({'LOOSE_STICKS', 'PLANT_FIBER', 'LOOSE_STONES', 'BERRIES'} <= kinds)
        held = {}
        for label, kind, item, x, y, quantity in A.FIRST_RESOURCES:
            held[item] = held.get(item, 0) + quantity
            d = math.hypot(x - S[0], y - S[1])
            self.assertTrue(1000 <= d <= 7000, f'{label} {d / 100:.0f} m from the spawn')
            self.assertGreater(A.distance_to_route(x, y), A.ROUTE_WIDTH / 2 + 250, f'{label} on the track')
            self.assertGreater(math.hypot(x - A.SPRING[0], y - A.SPRING[1]), A.SPRING_RADIUS + 250, f'{label} in the spring')
            for ox, oy, _ in A.OAKS:
                self.assertGreater(math.hypot(x - ox, y - oy), 400, f'{label} inside an oak')
            self.assertGreater(T.height(x, y), T.SEA + 60, f'{label} wet')
        for item, need in A.STONE_HATCHET.items():
            self.assertGreaterEqual(held.get(item, 0), 2 * need, f'not enough {item} for a hatchet and a mistake')
        for i, a in enumerate(A.FIRST_RESOURCES):
            for b in A.FIRST_RESOURCES[i + 1:]:
                self.assertGreater(math.hypot(a[3] - b[3], a[4] - b[4]), 250, f'{a[0]} crowds {b[0]}')
        # At least one of each kind needed for the hatchet lies within the first view.
        for kind in ('LOOSE_STICKS', 'PLANT_FIBER', 'LOOSE_STONES'):
            self.assertTrue(any(in_view(x, y) for _, k, _, x, y, _ in A.FIRST_RESOURCES if k == kind), f'no {kind} in view')

    def test_generators_keep_clear_of_the_arrival(self):
        self.assertTrue(A.near_arrival(*S))
        self.assertTrue(A.near_arrival(*A.SPRING))
        mid = self.route[len(self.route) // 2]
        self.assertTrue(A.near_arrival(*mid))
        for x, y, _ in A.OAKS:
            self.assertFalse(A.near_arrival(x, y))
        self.assertFalse(A.near_arrival(0.0, 0.0))


if __name__ == '__main__':
    unittest.main()
