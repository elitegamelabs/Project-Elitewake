"""Plain-Python tests for the climb-outs (owner, November 5: a swimmer must never be stuck against a steep coast) and
the starter island's straight shores (no Unreal).

The full coast survey (coast_exits.py, a few minutes on all cores) runs when EW_SLOW_TESTS=1; the rest is quick.
"""
import math
import os
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

import coast_exits as C    # noqa: E402
import world_layout as W   # noqa: E402
import world_terrain as T  # noqa: E402
from world_climbouts import CLIMB_OUTS  # noqa: E402


def _along(climb, u):
    for k, (a, b) in enumerate(zip(climb.line, climb.line[1:])):
        if climb.start[k] <= u <= climb.start[k + 1]:
            t = (u - climb.start[k]) / (climb.start[k + 1] - climb.start[k])
            return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
    return climb.line[-1]


class StarterShoreTests(unittest.TestCase):
    """The starter's long straight shores have a beach and a shelf, not a sheer wall (in-game walk, November 5)."""

    def test_no_sheer_wall_beside_the_straight_shores(self):
        starter = W.island('Starter')
        segs, _ = starter._oblique()
        self.assertTrue(segs)
        for x1, y1, x2, y2 in segs:
            n = math.hypot(x2 - x1, y2 - y1)
            nx, ny = -(y2 - y1) / n, (x2 - x1) / n
            for t in (.4, .6, .8):
                mx, my = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
                port = W.PORTS['Plains']
                if math.hypot(mx - starter.old.cx, my - starter.old.cy) < starter.OLD_END_KEPT[1] + 4000 or \
                        math.hypot(mx - port.cx, my - port.cy) < starter.HARBOUR_KEPT[1] + 4000:
                    continue    # left as built by the arrival and Saltreach (the survey checks a swimmer gets out there)
                # Across the shore, 4 m apart, the ground never drops more than a steep beach would.
                heights = [T.height(mx + d * nx, my + d * ny) for d in range(-4000, 4001, 400)]
                worst = max(abs(b - a) for a, b in zip(heights, heights[1:]))
                self.assertLess(worst, 400.0, f'a {worst / 100:.0f} m step across the shore at ({mx / 100:.0f}, {my / 100:.0f}) m')

    def test_shore_itself_is_unchanged(self):
        """The fix measures distance differently near those shores; it does not move the shore."""
        starter = W.island('Starter')
        for k in range(0, 360, 3):
            a = math.radians(k)
            r = starter.radius(a)
            inside = starter.distance(starter.cx + (r - 50) * math.cos(a), starter.cy + (r - 50) * math.sin(a))
            outside = starter.distance(starter.cx + (r + 50) * math.cos(a), starter.cy + (r + 50) * math.sin(a))
            self.assertLess(inside, 0)
            self.assertGreater(outside, 0)

    def test_arrival_and_harbour_ground_unchanged(self):
        """The old east end and Saltreach's harbour measure exactly as before the fix."""
        starter = W.island('Starter')
        port = W.PORTS['Plains']
        for cx, cy, r in ((starter.old.cx, starter.old.cy, starter.OLD_END_KEPT[0]),
                          (port.cx, port.cy, starter.HARBOUR_KEPT[0])):
            for k in range(24):
                for f in (.3, .6, .95):
                    x, y = cx + f * r * math.cos(k * math.pi / 12), cy + f * r * math.sin(k * math.pi / 12)
                    self.assertEqual(starter.distance(x, y), W.Island.distance(starter, x, y))


class ClimbOutTests(unittest.TestCase):

    def test_paths_rise_gently_from_the_water(self):
        for key, paths in CLIMB_OUTS.items():
            for points in paths:
                climb = T.Climb(points)
                fx, fy = climb.points[0]
                foot = T.height(fx, fy)
                self.assertLessEqual(foot - T.SEA, C.STEP_OUT, f'{key}: foot at ({fx}, {fy}) stands too high')
                u, prev = 0.0, foot
                while u + 300 <= climb.length:
                    x, y = _along(climb, u + 300)
                    z = T.height(x, y)
                    self.assertLessEqual((z - prev) / 300, math.tan(math.radians(C.WALKABLE)),
                                         f'{key}: too steep at ({x:.0f}, {y:.0f})')
                    u, prev = u + 300, z

    def test_paths_kept_apart_and_off_caves_and_ports(self):
        for key, paths in CLIMB_OUTS.items():
            for n, a in enumerate(paths):
                for x, y in a:
                    self.assertFalse(W.near_port(x, y, 3000.0), f'{key}: a climb-out at Saltreach or a village')
                    self.assertFalse(T.near_cave(x, y, 1500.0), f'{key}: a climb-out at a cave')
                for b in paths[n + 1:]:
                    joins = any(min(math.hypot(e[0] - q[0], e[1] - q[1]) for q in other) <= T.CLIMB_HALF + 50
                                for e, other in ((a[-1], b), (b[-1], a)))
                    if joins:
                        continue                   # one ends on the other (coast_exits.trace)
                    gap = min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in a for q in b)
                    self.assertGreaterEqual(gap, C.CLIMB_APART - 1, f'{key}: two climb-outs {gap / 100:.0f} m apart')


@unittest.skipUnless(os.environ.get('EW_SLOW_TESTS') == '1', 'set EW_SLOW_TESTS=1 for the full coast survey')
class CoastSurveyTests(unittest.TestCase):

    def test_no_coast_traps_a_swimmer(self):
        for r in C.survey_all(workers=14):
            self.assertFalse(r['trapped'], f"{r['island']}: {r['trapped'][:3]}")
            self.assertEqual(r['unreachable'], 0, r['island'])


if __name__ == '__main__':
    unittest.main()
