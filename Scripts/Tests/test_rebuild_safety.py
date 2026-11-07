"""Read-only world-rebuild guard behavior, using disposable test files."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SETUP = Path(__file__).resolve().parents[1] / 'Setup'
sys.path.insert(0, str(SETUP))

from rebuild_safety import GIB, PACKAGE_TAG, check_map_and_space  # noqa: E402


class RebuildSafetyTests(unittest.TestCase):
    def test_valid_map_with_headroom_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            map_file = Path(directory) / 'Map.umap'
            map_file.write_bytes(b'map data' + PACKAGE_TAG)
            with patch('rebuild_safety.shutil.disk_usage') as usage:
                usage.return_value.free = 150 * GIB
                self.assertEqual(check_map_and_space(map_file), 150 * GIB)

    def test_invalid_map_stops_before_next_step(self):
        with tempfile.TemporaryDirectory() as directory:
            map_file = Path(directory) / 'Map.umap'
            map_file.write_bytes(b'incomplete map')
            with patch('rebuild_safety.shutil.disk_usage') as usage:
                usage.return_value.free = 150 * GIB
                with self.assertRaisesRegex(RuntimeError, 'map package is incomplete'):
                    check_map_and_space(map_file)

    def test_low_space_stops_before_next_step(self):
        with tempfile.TemporaryDirectory() as directory:
            map_file = Path(directory) / 'Map.umap'
            map_file.write_bytes(b'map data' + PACKAGE_TAG)
            with patch('rebuild_safety.shutil.disk_usage') as usage:
                usage.return_value.free = 119 * GIB
                with self.assertRaisesRegex(RuntimeError, 'at least 120 GiB'):
                    check_map_and_space(map_file)


if __name__ == '__main__':
    unittest.main()
