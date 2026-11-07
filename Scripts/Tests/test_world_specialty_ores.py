"""The mined island specialties (CLAUDE.md 5.7): each on its planned islands, absent from the rest of its region."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
import world_specialty_ores as O  # noqa: E402
import world_terrain as T  # noqa: E402
from world_islands import ISLANDS  # noqa: E402


class SpecialtyOresTest(unittest.TestCase):
    def test_every_planned_island_has_its_full_count(self):
        for ore, (_, _, _, isles, _, count) in O.ORES.items():
            self.assertEqual(set(O.PLAN[ore]), set(isles), ore)
            for key in isles:
                self.assertEqual(len(O.PLAN[ore][key]), count, f'{ore} on {key}')

    def test_specialty_absent_from_the_rest_of_its_region(self):
        islands = {i.key: i for i in W.ISLANDS}
        for ore, (_, _, _, isles, _, _) in O.ORES.items():
            regions = [islands[k].region for k in isles]
            self.assertEqual(len(regions), len(set(regions)), f'{ore} is on two islands of one region')

    def test_matches_the_island_plan(self):
        words = {'CopperOre': 'copper ore', 'IronOre': 'iron ore', 'SulfurOre': 'sulfur ore', 'Salt': 'salt', 'Amber': 'amber',
                 'BogIron': 'bog iron'}
        for ore, (_, _, _, isles, _, _) in O.ORES.items():
            for key in isles:
                self.assertIn(words[ore], ISLANDS[key]['specialty'], f'{ore} on {key} is not in its plan')

    def test_sulfur_desert_only_and_needs_a_metal_pick(self):
        islands = {i.key: i for i in W.ISLANDS}
        self.assertEqual({islands[k].region for k in O.PLAN['SulfurOre']}, {'Desert'})
        self.assertEqual(O.ORES['SulfurOre'][2], 'METAL')

    def test_nodes_on_land_of_their_island_and_apart(self):
        islands = {i.key: i for i in W.ISLANDS}
        for ore, isles in O.PLAN.items():
            for key, nodes in isles.items():
                for x, y in nodes:
                    self.assertLess(islands[key].distance(x, y), -500, f'{ore} on {key} too near the shore')
                    self.assertGreater(T.height(x, y), T.SEA + 30, f'{ore} on {key} under water')
        everyone = [(x, y) for isles in O.PLAN.values() for nodes in isles.values() for x, y in nodes]
        for i, (x, y) in enumerate(everyone):
            for x2, y2 in everyone[i + 1:]:
                self.assertGreater(math.hypot(x - x2, y - y2), 250)


if __name__ == '__main__':
    unittest.main()
