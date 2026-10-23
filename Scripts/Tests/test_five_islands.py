"""The five-island test world (owner, October 21-22): one island per region, each about 1,500 to 2,500 m across with an organic, irregular coast, and no two alike."""
import math
import os
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)
import world_layout as W  # noqa: E402

M = W.M


@unittest.skipUnless(W.FIVE_ISLAND_WORLD, 'five-island world not selected')
class FiveIslandTests(unittest.TestCase):
    def test_one_island_per_region(self):
        self.assertEqual(sorted(i.region for i in W.ISLANDS), sorted(W.REGION_CENTRES))
        self.assertEqual(W.check(W.ISLANDS)[0], [])

    def test_each_island_is_1500_to_2500_m_across(self):
        for i in W.ISLANDS:
            widths = [2 * i.radius(2 * math.pi * k / 180) for k in range(180)]
            longest = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a in i.outline(90) for b in i.outline(90))
            self.assertGreaterEqual(longest / M, 1500, i.key)
            self.assertLessEqual(longest / M, 2500, i.key)

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
        for a in W.ISLANDS:
            for b in W.ISLANDS:
                if a is b:
                    continue
                sa, sb = signature(a), signature(b)
                # the same shape turned: compare against every rotation
                best = min(sum((sa[k] - sb[(k + s) % 72]) ** 2 for k in range(72)) for s in range(72))
                self.assertGreater(best, 0.05, f'{a.key} and {b.key} are the same shape turned')

    def test_plains_island_keeps_the_spawn_headland(self):
        starter = W.island('Starter')
        self.assertLess(starter.distance(-800.0, -100.0), 0, 'the old centre is no longer on the Plains island')


if __name__ == '__main__':
    unittest.main()
