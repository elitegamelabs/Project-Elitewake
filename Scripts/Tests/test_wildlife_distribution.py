"""Offline checks for additive wildlife population coverage on the expanded layout."""
import os
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

import wildlife_distribution as D  # noqa: E402
import world_layout as W  # noqa: E402


class WildlifeDistributionTests(unittest.TestCase):
    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')
    def test_expansion_targets_only_the_fourteen_new_islands(self):
        targets = D.expansion_islands()
        self.assertEqual(len(targets), 14)
        self.assertTrue(all(i.key not in D.LEGACY_ISLAND_KEYS for i in targets))
        self.assertEqual({i.key for i in targets}, {i.key for i in W.ISLANDS[26:]})
        self.assertEqual(len(D.expansion_islands(existing_added_keys=(i.key for i in targets))), 0)

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_existing_per_island_population_rules_are_extended_consistently(self):
        legacy = W.generate_legacy()
        original_total = sum(sum(D.target_counts(island).values()) for island in legacy)
        additions = D.expansion_islands()
        added_total = sum(sum(D.target_counts(island).values()) for island in additions)
        self.assertEqual(original_total, 87)
        self.assertEqual(added_total, 45)
        self.assertEqual(sum(D.target_counts(i)['Alligator'] for i in additions if i.region == 'Swamp'), 6)
        self.assertEqual(sum(D.target_counts(i)['Tortoise'] for i in additions if i.region == 'Jungle'), 3)

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_population_deficits_preserve_existing_counts_and_are_idempotent(self):
        island = next(i for i in W.ISLANDS if i.key == 'Swamp6')
        self.assertEqual(D.missing_counts(island, {}), {'Alligator': 2, 'Cottonmouth': 2})
        self.assertEqual(D.missing_counts(island, {'Alligator': 1}), {'Alligator': 1, 'Cottonmouth': 2})
        self.assertEqual(D.missing_counts(island, {'Alligator': 4, 'Cottonmouth': 2}),
                         {'Alligator': 0, 'Cottonmouth': 0})
        self.assertEqual(D.missing_counts(next(i for i in W.ISLANDS if i.key == 'Winter6'), {}), {})


if __name__ == '__main__':
    unittest.main()
