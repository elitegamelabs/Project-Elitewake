"""Offline checks for the canonical five-island wildlife population plan."""
import os
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

import wildlife_distribution as D  # noqa: E402
import world_layout as W  # noqa: E402


class WildlifeDistributionTests(unittest.TestCase):
    def test_population_plan_covers_all_five_islands(self):
        plans = {island.region: D.target_counts(island) for island in W.ISLANDS}
        self.assertEqual(set(plans), set(W.REGION_CENTRES))
        self.assertEqual(sum(sum(plan.values()) for plan in plans.values()), 146)
        self.assertEqual(plans['Plains']['Lion'], 1)
        self.assertEqual(plans['Winter'], {'Bear': 2})
        self.assertEqual(plans['Swamp'], {'Alligator': 14, 'Cottonmouth': 14, 'GiantCrocodile': 1})
        self.assertEqual(plans['Jungle']['Elephant'], 2)

    def test_population_deficits_are_idempotent(self):
        island = W.island('Swamp1')
        self.assertEqual(D.missing_counts(island, {}),
                         {'Alligator': 14, 'Cottonmouth': 14, 'GiantCrocodile': 1})
        self.assertEqual(D.missing_counts(island, {'Alligator': 9, 'Cottonmouth': 14}),
                         {'Alligator': 5, 'Cottonmouth': 0, 'GiantCrocodile': 1})
        self.assertEqual(D.missing_counts(island, D.target_counts(island)),
                         {'Alligator': 0, 'Cottonmouth': 0, 'GiantCrocodile': 0})


if __name__ == '__main__':
    unittest.main()
