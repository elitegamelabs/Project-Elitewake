"""Model the hand tools a survivor holds and give them to their items. Safe to run again.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Each tool is built in the ship timber material (oak with vertex-coloured tar and iron), gripped at the origin with
its handle running up +Z and its working edge toward +X: the stone hatchet (a knapped flint head lashed to its haft),
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
from ship_geometry import Builder, make_timber_material, material_builder, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/World/Tools'
FLINT_MATERIAL = f'{FOLDER}/M_Flint_v1'
ITEMS = '/Game/Elitewake/Items/Testing'
TORCH_LIGHT = 40.0   # candelas at the torch head (tuning; build_core_tools.py uses the same)
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


def stone_hatchet():
    """The first tool (owner, October 31: Phase 1's stone tool): a knapped flint head bound into a split haft with fibre
    cord. The head is material slot 1 (flint); its faces are left uneven, as struck flakes leave them."""
    b = Builder()
    length = 50.0
    haft(b, length)
    b.slot = 1
    top, h = length - 6, 6.0
    edge, back, thick = 10.5, -3.5, 2.6
    pts = {'eb': (edge, 0, top + h * 1.2), 'em': (edge + .8, .3, top), 'ef': (edge, 0, top - h * 1.1),
           'tb': (back, thick, top + h * .55), 'tm': (back + 1.5, thick * 1.15, top + .4), 'tf': (back, thick * .9, top - h * .5),
           'sb': (back, -thick * .9, top + h * .5), 'sm': (back + 1.2, -thick * 1.1, top - .3), 'sf': (back, -thick, top - h * .55)}
    ids = {k: b.vertex(p) for k, p in pts.items()}
    for a, c, d, e, hint in (('eb', 'em', 'tm', 'tb', (0, 1, 0)), ('em', 'ef', 'tf', 'tm', (0, 1, 0)),
                             ('eb', 'em', 'sm', 'sb', (0, -1, 0)), ('em', 'ef', 'sf', 'sm', (0, -1, 0)),
                             ('tb', 'tm', 'sm', 'sb', (-1, 0, 0)), ('tm', 'tf', 'sf', 'sm', (-1, 0, 0))):
        b.quad(ids[a], ids[c], ids[d], ids[e], hint)
    b.tri(ids['eb'], ids['tb'], ids['sb'], (0, 0, 1))
    b.tri(ids['ef'], ids['tf'], ids['sf'], (0, 0, -1))
    b.slot = 0
    lashing(b, length - 7, 2.3, turns=6)
    return b


def flint_material():
    """Dark grey-brown flint, matte with a faint sheen where flakes came off, a chalky pale rind in patches (world-space noise, no texture)."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(FLINT_MATERIAL)
    position = node(unreal.MaterialExpressionWorldPosition)
    noise = """
struct N { float h(float2 p) { return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }
  float n(float2 p) { float2 i = floor(p), f = frac(p); f = f * f * (3.0 - 2.0 * f);
    return lerp(lerp(h(i), h(i + float2(1, 0)), f.x), lerp(h(i + float2(0, 1)), h(i + float2(1, 1)), f.x), f.y); } } m;
float flake = m.n(P.xy / 2.3 + P.z / 3.1), rind = m.n(P.yz / 1.9 + 17.0);
"""
    colour = custom(noise + 'float3 c = lerp(float3(.05, .048, .045), float3(.11, .1, .09), flake);\n'
                    'return lerp(c, float3(.42, .39, .33), step(.87, rind));', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P',))
    rough = custom(noise + 'return lerp(lerp(.6, .78, flake), .9, step(.87, rind));', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('P',))
    for n in (colour, rough):
        assert mel.connect_material_expressions(position, '', n, 'P')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


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


TOOLS = {'DA_TestWoodenAxe': ('SM_WoodenAxe_v1', stone_hatchet),
         'DA_TestHatchet': ('SM_IronHatchet_v1', lambda: axe(True)),
         'DA_TestWoodenPickaxe': ('SM_WoodenPickaxe_v1', lambda: pickaxe(False)),
         'DA_TestPickaxe': ('SM_IronPickaxe_v1', lambda: pickaxe(True)),
         'DA_TestWoodenShovel': ('SM_WoodenShovel_v1', shovel),
         'DA_TestInnTorch': ('SM_Torch_v1', torch)}


# Display names the tools go by (the first is the stone tool of Phase 1; the rest keep theirs).
NAMES = {'DA_TestWoodenAxe': 'Stone Hatchet'}


def build_tool(item_name, timber, flint):
    """Model one tool and give it its held mesh and grip; returns the item (unsaved) and the mesh."""
    mesh_name, build = TOOLS[item_name]
    item = unreal.load_asset(f'{ITEMS}/{item_name}')
    assert item, item_name
    materials = [timber, flint] if build is stone_hatchet else [timber]
    mesh = write_static_mesh(build(), f'{FOLDER}/{mesh_name}', materials, 40.0, collision=False)
    if item_name in NAMES:
        item.set_editor_property('display_name', NAMES[item_name])
    item.set_editor_property('held_mesh', mesh)
    item.set_editor_property('held_mesh_transform', GRIP)
    return item, mesh


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber, flint = make_timber_material(), flint_material()
    report = {}
    for item_name, (mesh_name, build) in TOOLS.items():
        item, mesh = build_tool(item_name, timber, flint)
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
