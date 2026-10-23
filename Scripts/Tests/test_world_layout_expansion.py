"""Regression tests for the additive 26-to-40 island layout migration."""
import os
import hashlib
import json
import random
import sys
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402


def frozen(value):
    if isinstance(value, dict):
        return tuple((key, frozen(item)) for key, item in sorted(value.items()))
    if isinstance(value, (tuple, list)):
        return tuple(frozen(item) for item in value)
    if hasattr(value, '__dict__'):
        return type(value).__name__, frozen({key: item for key, item in vars(value).items() if key != '_reach'})
    return value


class WorldLayoutExpansionTests(unittest.TestCase):
    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')
    def test_exactly_eight_islands_per_region(self):
        self.assertEqual(len(W.ISLANDS), 40)
        for region, expected in W.ISLANDS_PER_REGION.items():
            self.assertEqual(sum(i.region == region for i in W.ISLANDS), expected, region)
        self.assertEqual(len({i.key for i in W.ISLANDS}), 40)

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_first_twenty_six_records_match_legacy_generator(self):
        legacy = W.generate_legacy()
        self.assertEqual(len(legacy), 26)
        self.assertEqual([i.key for i in W.ISLANDS[:26]], [i.key for i in legacy])
        for original, current in zip(legacy, W.ISLANDS[:26]):
            self.assertEqual(frozen(vars(current)), frozen(vars(original)), original.key)

    def test_original_layout_matches_pre_expansion_commit_fingerprint(self):
        payload = json.dumps(frozen(W.generate_legacy()), sort_keys=True, separators=(',', ':'))
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(),
                         '53c230d473a1046b42f749929ea589b527626b73f6bf87ec75c46bdfa59a988a')

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_fourteen_new_keys_are_stable_and_additive(self):
        expected = {f'Plains{i}' for i in (7, 8)}
        expected |= {f'{region}{i}' for region in ('Winter', 'Swamp', 'Desert', 'Jungle') for i in (6, 7, 8)}
        added = {i.key for i in W.ISLANDS[26:]}
        self.assertEqual(added, expected)
        regenerated = W.generate()
        self.assertEqual([frozen(vars(i)) for i in regenerated], [frozen(vars(i)) for i in W.ISLANDS])

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_existing_port_island_keys_do_not_move(self):
        legacy = W.generate_legacy()
        expected = {
            region: max((i for i in legacy if i.region == region and i.key != 'Starter'),
                        key=lambda i: i.rx * i.ry).key
            for region in W.REGION_CENTRES
        }
        self.assertEqual(W.LEGACY_PORT_ISLAND_KEYS, expected)
        self.assertEqual({region: port.island.key for region, port in W.PORTS.items()}, expected)

    def test_spacing_and_region_orientation_pass_for_all_forty(self):
        problems, nearest = W.check(W.ISLANDS)
        self.assertEqual(problems, [])
        self.assertEqual(set(nearest), {i.key for i in W.ISLANDS})

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_new_non_swamp_islands_receive_distinct_terrain_plans(self):
        for region in ('Plains', 'Winter', 'Jungle', 'Desert'):
            islands = [i for i in W.ISLANDS if i.region == region and i.key != 'Starter']
            plans = [T.TERRAIN_PLANS[i.key][0] for i in islands]
            self.assertEqual(len(plans), 7 if region == 'Plains' else 8, region)
            self.assertEqual(len(set(plans)), len(plans), region)
            self.assertTrue(all(i.key in T.TERRAIN_PLANS for i in islands[5:]), region)

    @unittest.skipIf(W.FIVE_ISLAND_WORLD, 'owner, Oct 21-22: the five-island test world replaces the 26/40-island layout')

    def test_original_terrain_plan_assignments_remain_stable(self):
        expected = {}
        for region, options in T.PLANS.items():
            order = list(options)
            random.Random(sum(map(ord, region)) * 31).shuffle(order)
            islands = [i for i in W.generate_legacy() if i.region == region and i.key != 'Starter']
            expected.update((island.key, plan) for island, plan in zip(islands, order))
        actual = {key: value[0] for key, value in T.TERRAIN_PLANS.items() if key in expected}
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
