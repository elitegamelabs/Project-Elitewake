"""Offline checks for the twenty-island wildlife placement plan."""
import os
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

import wildlife_distribution as D  # noqa: E402
import world_islands as I  # noqa: E402
import world_layout as W  # noqa: E402


class WildlifeDistributionTests(unittest.TestCase):
    """CLAUDE.md 5.6-5.7 (owner, November 1): each island its own mix, species only in their region."""

    def test_species_stay_in_their_region_and_mixes_differ(self):
        plans = {island.key: D.target_counts(island) for island in W.ISLANDS}
        for island in W.ISLANDS:
            self.assertLessEqual(set(plans[island.key]), I.REGION_SPECIES[island.region], island.key)
        for region in W.REGION_CENTRES:
            mixes = [frozenset(plans[i.key]) for i in W.ISLANDS if i.region == region and plans[i.key]]
            self.assertEqual(len(mixes), len(set(mixes)), f'two {region} islands carry the same mix')

    def test_large_animals_where_the_plan_puts_them(self):
        self.assertIn('Lion', D.target_counts(W.island('Plains2')))
        self.assertIn('Bear', D.target_counts(W.island('Winter1')))
        self.assertIn('GiantCrocodile', D.target_counts(W.island('Swamp3')))
        self.assertIn('Elephant', D.target_counts(W.island('Jungle4')))
        self.assertNotIn('SquirrelMonkey', D.target_counts(W.island('Starter')), 'monkeys belong in the Jungle')

    def test_population_deficits_are_idempotent(self):
        island = W.island('Swamp2')
        self.assertEqual(D.missing_counts(island, {}), D.target_counts(island))
        self.assertEqual(D.missing_counts(island, {'Alligator': 4}), {'Alligator': 6, 'Boar': 8})
        self.assertEqual(set(D.missing_counts(island, D.target_counts(island)).values()), {0})


if __name__ == '__main__':
    unittest.main()
