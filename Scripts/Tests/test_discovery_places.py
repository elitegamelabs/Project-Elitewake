"""The discovery journal's place table (Source/EW/World/EWPlacesTable.inl) matches the world data it is generated from."""
import os
import sys
import unittest

SETUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Setup')
sys.path.insert(0, os.path.normpath(SETUP))

import write_discovery_places as P  # noqa: E402


class DiscoveryPlacesTest(unittest.TestCase):
    def test_table_is_current(self):
        with open(P.OUT, encoding='utf-8') as f:
            self.assertEqual(f.read(), P.text(), 'run python Scripts/Setup/write_discovery_places.py')

    def test_counts(self):
        kinds = [p[2] for p in P.places()]
        self.assertEqual(kinds.count('Island'), 20)
        self.assertEqual(kinds.count('Freeport'), 5)
        self.assertEqual(kinds.count('Reef'), 3)
        self.assertEqual(kinds.count('Cave'), 20)

    def test_ids_and_names_unique(self):
        places = P.places()
        self.assertEqual(len({p[0] for p in places}), len(places))
        self.assertEqual(len({p[1] for p in places}), len(places))

    def test_no_quotes_or_backslashes(self):
        for p in P.places():
            for field in (p[0], p[1], p[11]):
                self.assertNotIn('"', field)
                self.assertNotIn('\\', field)

    def test_freeports_inside_their_islands(self):
        import math
        import world_layout as L
        for region, port in L.PORTS.items():
            island = port.island
            d = math.hypot(port.cx - island.cx, port.cy - island.cy)
            self.assertLess(d, max(island.rx, island.ry) + P.ISLAND_REACH, region)


if __name__ == '__main__':
    unittest.main()
