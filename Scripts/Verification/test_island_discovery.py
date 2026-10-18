"""Run from repository root: python -m unittest discover -s Scripts/Verification -p 'test_island_discovery.py'"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Setup"))
from island_discovery import ANNOUNCEMENT_SECONDS, ISLAND_NAMES, IslandDiscovery, validate_world_keys
from world_layout import ISLANDS


class IslandDiscoveryTests(unittest.TestCase):
    def test_all_generated_islands_have_unique_names(self):
        validate_world_keys(island.key for island in ISLANDS)
        self.assertEqual(len(ISLAND_NAMES), 26)
        self.assertEqual(len(set(ISLAND_NAMES.values())), 26)

    def test_discover_once_and_hide_until_discovered(self):
        state = IslandDiscovery()
        self.assertIsNone(state.map_label("Winter1"))
        self.assertEqual(state.discover("Winter1"), "Frostfall Island")
        self.assertEqual(state.map_label("Winter1"), "Frostfall Island")
        self.assertIsNone(state.discover("Winter1"))
        self.assertEqual(ANNOUNCEMENT_SECONDS, 5.0)

    def test_independent_players(self):
        first, second = IslandDiscovery(), IslandDiscovery()
        first.discover("Starter")
        self.assertIsNone(second.map_label("Starter"))
        self.assertEqual(second.discover("Starter"), "Hearthshore")

    def test_save_load_never_reannounces(self):
        state = IslandDiscovery()
        state.discover("Starter")
        state.discover("Jungle5")
        restored = IslandDiscovery.restore(state.serialize())
        self.assertEqual(restored.serialize(), ["Jungle5", "Starter"])
        self.assertIsNone(restored.discover("Starter"))
        self.assertEqual(restored.discover("Swamp1"), "Mirehaven")

    def test_reject_bad_keys(self):
        state = IslandDiscovery()
        with self.assertRaises(KeyError):
            state.discover("NotAnIsland")
        with self.assertRaises(ValueError):
            IslandDiscovery.restore(["NotAnIsland"])
        with self.assertRaises(ValueError):
            validate_world_keys(["Starter", "Starter"])


if __name__ == "__main__":
    unittest.main()
