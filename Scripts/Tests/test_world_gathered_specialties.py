"""The gathered island specialties (CLAUDE.md 5.7): each on its planned island, absent from the rest of its region."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_gathered_specialties as G  # noqa: E402
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402


class GatheredSpecialtiesTest(unittest.TestCase):
    def test_full_counts_on_planned_islands(self):
        if not G._forest_trees():
            self.skipTest('Saved/ForestPlan.json not present (run forest_plan.py)')
        for key, spec in G.ITEMS.items():
            isles, count = spec[4], spec[7]
            self.assertEqual(set(G.PLAN[key]), set(isles), key)
            for island in isles:
                self.assertEqual(len(G.PLAN[key][island]), count, f'{key} on {island}')

    def test_one_island_per_region(self):
        islands = {i.key: i for i in W.ISLANDS}
        for key, spec in G.ITEMS.items():
            regions = [islands[k].region for k in spec[4]]
            self.assertEqual(len(regions), len(set(regions)), key)

    def test_on_land_and_apart(self):
        islands = {i.key: i for i in W.ISLANDS}
        everyone = []
        for key, isles in G.PLAN.items():
            for island, nodes in isles.items():
                for x, y in nodes:
                    self.assertLess(islands[island].distance(x, y), -200, f'{key} on {island} off the island')
                    self.assertGreater(T.height(x, y), T.SEA + 15, f'{key} on {island} under water')
                    everyone.append((x, y))
        for i, (x, y) in enumerate(everyone):
            for x2, y2 in everyone[i + 1:]:
                self.assertGreater(math.hypot(x - x2, y - y2), 350)

    def test_food_items_spoil(self):
        for key, spec in G.ITEMS.items():
            if spec[3]:
                self.assertEqual(spec[2], 'BERRIES', key)
                self.assertGreater(spec[3]['fresh'], 0, key)


if __name__ == '__main__':
    unittest.main()
