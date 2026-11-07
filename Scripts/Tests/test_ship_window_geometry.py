"""Offline geometry checks for the generated ship window panes (does not import Unreal assets)."""
import os
import sys
import types
import unittest

SETUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Setup')
if SETUP_DIR not in sys.path:
    sys.path.insert(0, SETUP_DIR)

try:
    import unreal  # noqa: F401
except ImportError:
    # ship_geometry's pure-Python Builder methods do not call Unreal; asset writing does.
    unreal_stub = types.ModuleType('unreal')
    unreal_stub.Material = object
    sys.modules['unreal'] = unreal_stub

from ship_geometry import Builder, WINDOW_GLASS  # noqa: E402
from ship_hull import Hull  # noqa: E402


class RecordingBuilder(Builder):
    def __init__(self):
        super().__init__()
        self.glass_boxes = []

    def box(self, centre, size, iron=0.0, tar=0.0):
        if self.slot == WINDOW_GLASS:
            self.glass_boxes.append((tuple(centre), tuple(size)))
        super().box(centre, size, iron=iron, tar=tar)


class ShipWindowGeometryTests(unittest.TestCase):
    def test_raised_cabin_has_six_closed_glass_panes_and_restores_material_slot(self):
        hull = Hull(-1200.0, 1200.0, 330.0, -250.0, 200.0, 50.0, 130.0, 70.0)
        mesh = RecordingBuilder()
        edge, facing = -800.0, 1
        side_lights = (-850.0, -950.0)
        hull.raised_deck(mesh, edge, 180.0, facing, (-1150.0, -600.0),
                         beams=(-750.0, -900.0), side_lights=side_lights,
                         side_light=(40.0, 290.0, 320.0), steps=2)

        self.assertEqual(len(mesh.glass_boxes), 6, 'two front panes and two panes on each side light')
        self.assertEqual(mesh.slot, 0, 'window generation must restore the caller material slot')
        glass_triangles = sum(slot == WINDOW_GLASS for slot in mesh.slots)
        self.assertEqual(glass_triangles, 72, 'six closed box panes should contribute twelve triangles each')

        front = {(centre, size) for centre, size in mesh.glass_boxes if centre[0] == edge + 2 * facing}
        self.assertEqual(front, {
            ((-798.0, -130.0, 317.5), (4.0, 40.0, 45.0)),
            ((-798.0, 130.0, 317.5), (4.0, 40.0, 45.0)),
        })
        side_x = {centre[0] for centre, _ in mesh.glass_boxes if centre[0] != edge + 2 * facing}
        self.assertEqual(side_x, set(side_lights))


if __name__ == '__main__':
    unittest.main()
