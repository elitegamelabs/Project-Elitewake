"""The twenty-island plan's rules (CLAUDE.md 5.6, 5.7; owner-approved November 1)."""
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_islands as P  # noqa: E402


class WorldIslandPlanTests(unittest.TestCase):
    def test_twenty_islands_four_per_region(self):
        self.assertEqual(len(P.ISLANDS), 20)
        self.assertEqual(Counter(i['region'] for i in P.ISLANDS.values()), {r: 4 for r in P.REGIONS})

    def test_exactly_one_village_per_region(self):
        villages = Counter(i['region'] for i in P.ISLANDS.values() if i['village'])
        self.assertEqual(villages, {r: 1 for r in P.REGIONS})
        self.assertEqual(P.VILLAGES['Plains'], 'Starter', 'Saltreach is the Plains village')

    def test_every_island_has_its_own_reason_to_visit(self):
        for region in P.REGIONS:
            islands = [i for i in P.ISLANDS.values() if i['region'] == region]
            for island in islands:
                self.assertTrue(island['specialty'], f'{island["name"]} has no specialty')
                others = {s for o in islands if o is not island for s in o['specialty']}
                self.assertTrue(set(island['specialty']) - others, f'{island["name"]} offers nothing its region lacks')

    def test_species_stay_in_their_region(self):
        for island in P.ISLANDS.values():
            outside = set(island['wildlife']) - P.REGION_SPECIES[island['region']]
            self.assertFalse(outside, f'{island["name"]} has species from another region: {sorted(outside)}')

    def test_island_mixes_differ_within_a_region(self):
        for region in P.REGIONS:
            mixes = [frozenset(i['wildlife']) for i in P.ISLANDS.values() if i['region'] == region]
            self.assertEqual(len(set(mixes)), len(mixes), f'two {region} islands share the same wildlife mix')

    def test_sulfur_is_desert_only(self):
        for island in P.ISLANDS.values():
            if any('sulfur' in s for s in island['specialty']):
                self.assertEqual(island['region'], 'Desert', f'sulfur on {island["name"]}')

    def test_elephants_only_in_the_jungle(self):
        for island in P.ISLANDS.values():
            if 'Elephant' in island['wildlife']:
                self.assertEqual(island['region'], 'Jungle')

    def test_crossing_target(self):
        self.assertEqual(P.CROSSING_MINUTES, (6, 17))

    def test_inland_water_depths_in_feet(self):
        self.assertAlmostEqual(P.POND_DEPTH_CM / 30.48, 15, places=1)
        self.assertAlmostEqual(P.LAKE_DEPTH_CM / 30.48, 50, places=1)

    def test_the_starter_pond_follows_the_rule(self):
        import coastal_layout, world_terrain
        self.assertEqual(coastal_layout.POND_DEPTH, P.POND_DEPTH_CM)
        self.assertEqual(world_terrain.POND_DEPTH, P.POND_DEPTH_CM)


if __name__ == '__main__':
    unittest.main()
