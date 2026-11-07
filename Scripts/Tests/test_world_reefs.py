"""The three open-ocean reefs (owner, October 31): plan checks without Unreal."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
import world_reefs as R  # noqa: E402
import world_terrain as T  # noqa: E402


class WorldReefsTest(unittest.TestCase):
    def test_three_reefs_in_open_ocean(self):
        self.assertEqual(len(R.REEFS), 3)
        for reef in R.REEFS:
            shore = min(math.hypot(i.cx - reef.cx, i.cy - reef.cy) - i.reach() for i in W.ISLANDS)
            self.assertGreater(shore, 100000, f'{reef.key} is {shore / 100:.0f} m from a shore')
            self.assertFalse(W.near_port(reef.cx, reef.cy, 150000), reef.key)

    def test_reefs_apart(self):
        for a in R.REEFS:
            for b in R.REEFS:
                if a is not b:
                    self.assertGreater(math.hypot(a.cx - b.cx, a.cy - b.cy), 300000)

    def test_corals_under_water_on_their_seamount(self):
        for reef in R.REEFS:
            self.assertGreaterEqual(len(reef.corals), 40, reef.key)
            self.assertEqual({c[2] for c in reef.corals}, set(R.KINDS), reef.key)
            mx, my, _, radius = T.SEAMOUNT_SITES[reef.seamount]
            for x, y, *_ in reef.corals:
                depth = T.SEA - T.height(x, y)
                self.assertTrue(R.SHALLOWEST < depth < R.DEEPEST, f'{reef.key} coral {depth / 100:.1f} m deep')
                self.assertLess(math.hypot(x - mx, y - my), radius)


if __name__ == '__main__':
    unittest.main()
