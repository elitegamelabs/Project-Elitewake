"""Offline regression checks for the procedural tortoise mesh data."""
import math
import os
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETUP_DIR = os.path.join(ROOT, 'Scripts', 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

try:
    import unreal  # noqa: F401
except ImportError:
    unreal_stub = types.ModuleType('unreal')
    unreal_stub.Material = object
    unreal_stub.Paths = types.SimpleNamespace(project_dir=lambda: ROOT)
    sys.modules['unreal'] = unreal_stub

import unreal  # noqa: E402

if not hasattr(unreal, 'Paths') or not hasattr(unreal.Paths, 'project_dir'):
    unreal.Paths = types.SimpleNamespace(project_dir=lambda: ROOT)

from build_animals import tortoise  # noqa: E402


class TortoiseGeometryTests(unittest.TestCase):
    def test_shell_generator_returns_dense_valid_mesh_data(self):
        mesh = tortoise()

        self.assertGreater(len(mesh.verts), 3000)
        self.assertGreater(len(mesh.tris), 6000)
        self.assertEqual(len(mesh.colours), len(mesh.verts))
        self.assertGreater(len(set(mesh.colours)), 1000)
        self.assertTrue(all(math.isfinite(value) for vertex in mesh.verts for value in vertex))
        self.assertTrue(all(math.isfinite(value) for colour in mesh.colours for value in colour))
        self.assertTrue(all(len(triangle) == 3 and
                            all(0 <= index < len(mesh.verts) for index in triangle)
                            for triangle in mesh.tris))

        extents = [max(vertex[axis] for vertex in mesh.verts) -
                   min(vertex[axis] for vertex in mesh.verts) for axis in range(3)]
        self.assertGreater(extents[0], 100.0)
        self.assertGreater(extents[1], 70.0)
        self.assertGreater(extents[2], 50.0)


if __name__ == '__main__':
    unittest.main()
