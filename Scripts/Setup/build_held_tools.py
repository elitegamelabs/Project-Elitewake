"""Model the hand tools a survivor holds and give them to their items. Safe to run again.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Each tool is built in the ship timber material (oak with vertex-coloured tar and iron), gripped at the origin with
its handle running up +Z and its working edge toward +X: the wooden axe (a hardwood wedge lashed to its haft),
wooden pickaxe and wooden shovel from the starter kit, the iron hatchet and iron pickaxe, and the inn torch (a
tarred head on a stick, lit by a warm light while held). The item's held transform seats the grip in the right hand.
All six become main-hand items. Sizes are tuning.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/World/Tools'
ITEMS = '/Game/Elitewake/Items/Testing'
TORCH_LIGHT = 12.0   # candelas at the torch head (tuning)
# The grip in the right hand (hand_r, whose X runs up the forearm, Y to the survivor's left and Z forward with the
# arm at rest): the haft leaves the fist up and forward at 45 degrees, the working edge facing forward (tuning, set
# by looking at the survivor holding each tool).
GRIP = unreal.Transform(location=unreal.Vector(-8.5, 1.5, 0.0),
                        rotation=unreal.MathLibrary.make_rot_from_zx(unreal.Vector(1, 0, 1), unreal.Vector(-1, 0, 1)))


def haft(b, length, radius=1.8, below=8.0):
    """A wooden handle from a little below the grip to `length` above it, slightly swelled at the butt."""
    b.tube([(0, 0, -below), (0, 0, -below + 3), (0, 0, length)], lambda k: (radius * 1.25, radius * 1.1, radius)[k], sides=10)


def lashing(b, z, radius, turns=5):
    """Cord wound round the haft where a head is bound on."""
    for k in range(turns):
        zz = z + (k - turns / 2) * 1.1
        b.tube([(radius * math.cos(a), radius * math.sin(a), zz + a * .15)
                for a in [i * math.pi / 6 for i in range(13)]], .55, sides=5, capped=False)


def wedge(b, top, blade_x, back_x, height, thick, iron):
    """An axe head: a wedge from a thick back to a thin cutting edge at +X, centred on the haft's top."""
    h = height / 2
    pts = {'eb': (blade_x, 0, top + h * 1.15), 'ef': (blade_x, 0, top - h * 1.15),
           'tb': (back_x, thick, top + h * .6), 'tf': (back_x, thick, top - h * .6),
           'sb': (back_x, -thick, top + h * .6), 'sf': (back_x, -thick, top - h * .6)}
    ids = {k: b.vertex(p, 0.0, iron) for k, p in pts.items()}
    b.quad(ids['eb'], ids['ef'], ids['tf'], ids['tb'], (0, 1, 0))
    b.quad(ids['eb'], ids['ef'], ids['sf'], ids['sb'], (0, -1, 0))
    b.quad(ids['tb'], ids['tf'], ids['sf'], ids['sb'], (-1, 0, 0))
    b.tri(ids['eb'], ids['tb'], ids['sb'], (0, 0, 1))
    b.tri(ids['ef'], ids['tf'], ids['sf'], (0, 0, -1))


def axe(iron):
    b = Builder()
    length = 42.0 if iron else 55.0
    haft(b, length)
    wedge(b, length - 6, 13.0 if iron else 11.0, -4.0, 9.0 if iron else 8.0, 2.4 if iron else 3.2, 1.0 if iron else 0.0)
    if not iron:
        lashing(b, length - 6, 2.4)
    return b


def pickaxe(iron):
    b = Builder()
    length = 62.0
    haft(b, length)
    # A curved double pick across the top: points to +X and -X, drooping toward their tips.
    span, droop = (26.0, 7.0) if iron else (22.0, 6.0)
    path = [(-span, 0, length - 4 - droop), (-span * .5, 0, length - 1), (0, 0, length + 1), (span * .5, 0, length - 1), (span, 0, length - 4 - droop)]
    b.tube(path, lambda k: (.5, 1.9, 2.6, 1.9, .5)[k], sides=8, iron=1.0 if iron else 0.0)
    if not iron:
        lashing(b, length - 2, 2.4)
    return b


def shovel():
    b = Builder()
    length = 80.0
    haft(b, length, radius=1.7, below=4.0)
    b.box((0, 0, length - 2), (11, 3.0, 3.0))                       # T grip at the top
    # The blade below the hand, a broad wooden spade, flat toward +X.
    b.sweep([(0, 0, -6), (0, 0, -20)], 3.4, 4.0)                      # socket
    b.box((1.2, 0, -32), (2.2, 19, 22))
    return b


def torch():
    b = Builder()
    haft(b, 40.0, radius=1.9)
    # Tarred rag wound round the head.
    start = len(b.verts)
    b.tube([(0, 0, 32), (0, 0, 36), (0, 0, 44), (0, 0, 48)], lambda k: (2.4, 4.0, 4.2, 3.0)[k], sides=10)
    for v in range(start, len(b.verts)):
        b.colours[v] = (1.0, 0.0, .4)
    return b


TOOLS = {'DA_TestWoodenAxe': ('SM_WoodenAxe_v1', lambda: axe(False)),
         'DA_TestHatchet': ('SM_IronHatchet_v1', lambda: axe(True)),
         'DA_TestWoodenPickaxe': ('SM_WoodenPickaxe_v1', lambda: pickaxe(False)),
         'DA_TestPickaxe': ('SM_IronPickaxe_v1', lambda: pickaxe(True)),
         'DA_TestWoodenShovel': ('SM_WoodenShovel_v1', shovel),
         'DA_TestInnTorch': ('SM_Torch_v1', torch)}


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = make_timber_material()
    report = {}
    for item_name, (mesh_name, build) in TOOLS.items():
        item = unreal.load_asset(f'{ITEMS}/{item_name}')
        assert item, item_name
        mesh = write_static_mesh(build(), f'{FOLDER}/{mesh_name}', [timber], 40.0, collision=False)
        item.set_editor_property('held_mesh', mesh)
        item.set_editor_property('held_mesh_transform', GRIP)
        # Every hand tool goes in the main hand, the shovel and the torch included (DECIDED, delegated).
        item.set_editor_property('equipment_slot', unreal.EWEquipmentSlot.MAIN_HAND)
        lit = item_name == 'DA_TestInnTorch'
        item.set_editor_property('held_light_intensity', TORCH_LIGHT if lit else 0.0)
        item.set_editor_property('held_light_offset', unreal.Vector(0, 0, 52) if lit else unreal.Vector())
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
        report[item_name] = {'mesh': mesh_name, 'slot': str(item.get_editor_property('equipment_slot'))}
    Path(unreal.Paths.project_saved_dir(), 'HeldToolsResult.json').write_text(json.dumps({'success': True, 'tools': report}, indent=2))
    unreal.log('Held tools built')


if __name__ == '__main__':
    main()
