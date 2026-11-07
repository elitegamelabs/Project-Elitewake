"""Plain-Python checks of the forest plan's rules (owner, November 6: dense, varied forests with open ground)."""
import os
import random
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

import forest_plan as F  # noqa: E402
import world_layout as W  # noqa: E402


class ForestPlanTests(unittest.TestCase):

    def test_each_region_led_by_its_primary_tree(self):
        primary = {'Plains': 'Oak', 'Winter': 'Birch', 'Swamp': 'Spruce', 'Desert': 'Palm', 'Jungle': 'Ash'}  # CLAUDE.md 4
        for region, mix in F.MIX.items():
            self.assertEqual(max(mix, key=mix.get), primary[region], region)
            self.assertAlmostEqual(sum(mix.values()), 1.0, places=6)
        self.assertNotIn('Birch', F.MIX['Swamp'], 'birch never belongs to the Swamp')
        self.assertEqual(set(F.MIX), {i.region for i in W.ISLANDS})

    def test_ages_cover_saplings_to_giants(self):
        self.assertAlmostEqual(sum(share for _, share, _ in F.AGES), 1.0, places=6)
        self.assertLess(F.AGES[0][2][1], .6)
        self.assertGreater(F.AGES[-1][2][1], 1.5)

    def test_forest_level_makes_stands_and_open_ground(self):
        """Over an island the noise leaves both forest and open ground in every region, with more forest in the Jungle
        than on the Plains."""
        rng = random.Random(3)
        share = {}
        for region, stand in F.STAND.items():
            levels = [F.forest_level(rng.uniform(-6e5, 6e5), rng.uniform(-6e5, 6e5), 31 * k) for k in range(1, 5) for _ in range(500)]
            self.assertTrue(all(0.0 <= v <= 1.0 for v in levels))
            share[region] = sum(v > stand for v in levels) / len(levels)
            self.assertTrue(.03 < share[region] < .97, f'{region}: {share[region]:.2f} forest')
        self.assertGreater(share['Jungle'], share['Plains'])

    def test_trunks_keep_walking_room(self):
        """Grown trees keep at least 5 m between trunks, so the forest floor stays open to walk through."""
        self.assertGreaterEqual(min(F.SPACING.values()), 5.0)


if __name__ == '__main__':
    unittest.main()
