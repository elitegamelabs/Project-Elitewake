"""Make the four core tools work in the hand: the torch's flame, the waterskin's held form and its full state,
and the survivor's animations for drawing a tool, lighting a torch, drinking and filling a waterskin.
Safe to run again. Run in the editor, outside Play, after build_held_tools.py:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

- SM_TorchFlame_v1 / M_TorchFlame_v1: three crossed planes of living flame on the torch head, white at the heart,
  orange at the edges, licking and flickering; shown only while the torch burns. Its light wavers in code.
- SM_HeldWaterskin_v1: a stitched hide skin gripped at the neck, its body hanging below the fist.
- DA_TestWaterskinFull: the waterskin full of fresh water. Filling at fresh water turns the empty skin in hand into
  it; drinking it turns it back. How much it holds is open (flask capacity, open question 11): for now one full
  drink, the same as drinking at the water itself.
- AS_Equip_v1, AS_Ignite_v1, AS_Drink_v1, AS_FillWaterskin_v1: keyed on the standing idle (anim_keying.py).
Chopping and mining keep the tool swing (AS_ToolChop_v1). Angles, timing, sizes and the torch's brightness are tuning.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anim_keying  # noqa: E402
from build_held_tools import GRIP  # noqa: E402
from ship_geometry import Builder, make_timber_material, material_builder, write_static_mesh  # noqa: E402

TOOLS = '/Game/Elitewake/World/Tools'
ITEMS = '/Game/Elitewake/Items/Testing'
ANIMS = '/Game/Elitewake/Animations/Tools'
CHARACTER = '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
TORCH_LIGHT = 40.0     # candelas at the torch head (tuning): enough to light a few metres around the survivor
FLAME_W, FLAME_H = 16.0, 30.0


def flame_mesh():
    """Three vertical planes crossed at 60 degrees, base at the origin, flame rising up +Z."""
    b = Builder()
    for k in range(3):
        a = math.pi * k / 3
        c, s = math.cos(a), math.sin(a)
        rows = [[(c * FLAME_W * (j / 4 - .5), s * FLAME_W * (j / 4 - .5), FLAME_H * i / 6) for j in range(5)] for i in range(7)]
        b.grid(rows, lambda i, j, c=c, s=s: (-s, c, 0), uv_of=lambda i, j, p: (j / 4, i / 6))
    return b


def flame_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{TOOLS}/M_TorchFlame_v1')
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('two_sided', True)
    fire = custom(
        'float x = UV.x * 2 - 1;  // across, -1..1\n'
        'float y = UV.y;          // up, 0 at the head\n'
        '// tongues of flame lick upward and sway\n'
        'float sway = .18 * sin(y * 7 - T * 9) * y + .08 * sin(y * 15 + T * 13) * y;\n'
        'float width = (1 - y) * (.75 + .25 * sin(T * 11 + y * 9)) * smoothstep(0, .12, y + .02);\n'
        'float body = saturate(1 - abs(x + sway) / max(width, .02));\n'
        'float lick = .65 + .35 * sin(y * 23 - T * 17 + x * 5) * sin(x * 13 + T * 7);\n'
        'float a = pow(body, 1.6) * lick * (1 - smoothstep(.55, 1, y));\n'
        '// white-yellow heart, orange body, red edges\n'
        'float3 heart = float3(1.0, .93, .6), mid = float3(1.0, .5, .1), edge = float3(.75, .14, .02);\n'
        'float3 c = lerp(edge, mid, saturate(body * 1.6));\n'
        'c = lerp(c, heart, saturate((body - .55) * 2.5) * (1 - y));\n'
        'return c * a * 6;',
        unreal.CustomMaterialOutputType.CMOT_FLOAT3, ['UV', 'T'])
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTextureCoordinate), '', fire, 'UV')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTime), '', fire, 'T')
    assert mel.connect_material_property(fire, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def waterskin_mesh():
    """Gripped at the origin by its neck: a stopper above the fist, the stitched hide body hanging below it."""
    b = Builder()
    profile = [(9.0, 1.2), (7.0, 1.8), (6.0, 2.2), (2.0, 2.0), (-3.0, 2.4), (-6.0, 5.0), (-11.0, 8.5), (-17.0, 10.0),
               (-23.0, 9.6), (-28.0, 7.5), (-31.0, 4.0), (-32.5, 1.0)]
    for (z0, r0), (z1, r1) in zip(profile, profile[1:]):
        b.tube([(0, 0, z0), (0, 0, z1)], lambda k, a=r0, c=r1: (a, c)[k], sides=14)
    b.tube([(0, 0, 9.0), (0, 0, 12.0)], 1.6, sides=10)                           # wooden stopper
    # A seam of stitching down one side, and a cord at the neck.
    b.tube([(0, 10.4 * .97, -17.0 + 6 * k / 6) for k in range(-6, 7)], .45, sides=5, iron=.0)
    b.tube([(2.3 * math.cos(2 * math.pi * k / 12), 2.3 * math.sin(2 * math.pi * k / 12), -3.0) for k in range(13)], .5, sides=5)
    return b


def leather_tone(b):
    """Dark hide: the timber material's tar channel darkens it toward brown leather."""
    for v in range(len(b.verts)):
        r, g, bl = b.colours[v]
        b.colours[v] = (.45, g, .35)
    return b


def data_asset(name):
    path = f'{ITEMS}/{name}'
    asset = unreal.load_asset(path)
    if asset:
        return asset
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ITEMS, unreal.EWItemDefinition, factory)
    assert asset, name
    return asset


def save(asset, values):
    for k, v in values.items():
        asset.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
    return asset


def animations():
    """Keys are (time 0-1, degrees). About X an arm swings forward and up and the spine leans back; about Z it twists."""
    a = {}
    a['equip'] = anim_keying.build(f'{ANIMS}/AS_Equip_v1', 24, {
        'upperarm_r': [('x', [(0, 0), (.35, 62), (.7, 30), (1, 0)])],
        'lowerarm_r': [('x', [(0, 0), (.35, 55), (.7, 30), (1, 0)])],
        'spine_03': [('z', [(0, 0), (.35, -10), (1, 0)])]}, 'Draw a tool')
    a['ignite'] = anim_keying.build(f'{ANIMS}/AS_Ignite_v1', 39, {
        'upperarm_r': [('x', [(0, 0), (.25, 70), (.8, 70), (1, 0)])],
        'lowerarm_r': [('x', [(0, 0), (.25, 70), (.8, 70), (1, 0)])],
        # The other hand strikes at the torch head three times.
        'upperarm_l': [('x', [(0, 0), (.3, 72), (.8, 72), (1, 0)]), ('z', [(0, 0), (.3, -28), (.8, -28), (1, 0)])],
        'lowerarm_l': [('x', [(0, 0), (.3, 40), (.4, 75), (.5, 40), (.6, 75), (.7, 40), (.8, 60), (1, 0)])]}, 'Light a torch')
    a['drink'] = anim_keying.build(f'{ANIMS}/AS_Drink_v1', 45, {
        'upperarm_r': [('x', [(0, 0), (.3, 78), (.75, 82), (1, 0)])],
        'lowerarm_r': [('x', [(0, 0), (.3, 115), (.75, 115), (1, 0)])],
        'spine_04': [('x', [(0, 0), (.35, 9), (.75, 12), (1, 0)])]}, 'Drink from a waterskin')
    a['fill'] = anim_keying.build(f'{ANIMS}/AS_FillWaterskin_v1', 45, {
        'spine_03': [('x', [(0, 0), (.3, -38), (.75, -38), (1, 0)])],
        'spine_04': [('x', [(0, 0), (.3, -14), (.75, -14), (1, 0)])],
        'upperarm_r': [('x', [(0, 0), (.3, 28), (.5, 20), (.75, 28), (1, 0)])],
        'lowerarm_r': [('x', [(0, 0), (.3, 18), (.75, 18), (1, 0)])]}, 'Fill a waterskin')
    return a


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    flame = write_static_mesh(flame_mesh(), f'{TOOLS}/SM_TorchFlame_v1', [flame_material()], 30.0, collision=False)
    timber = make_timber_material()
    skin_mesh = write_static_mesh(leather_tone(waterskin_mesh()), f'{TOOLS}/SM_HeldWaterskin_v1', [timber], 30.0, collision=False)

    torch = save(unreal.load_asset(f'{ITEMS}/DA_TestInnTorch'), {
        'held_flame_mesh': flame, 'held_light_intensity': TORCH_LIGHT, 'held_light_offset': unreal.Vector(0, 0, 52)})
    empty = unreal.load_asset(f'{ITEMS}/DA_TestHideWaterFlask')
    assert empty, 'no waterskin item'
    full = data_asset('DA_TestWaterskinFull')
    shared = {'held_mesh': skin_mesh, 'held_mesh_transform': GRIP, 'equipment_slot': unreal.EWEquipmentSlot.MAIN_HAND,
              'category': empty.get_editor_property('category'), 'max_stack_size': 1, 'icon': empty.get_editor_property('icon'),
              'unit_weight': empty.get_editor_property('unit_weight')}   # a full skin's weight is open; it weighs as the empty one
    save(full, {**shared, 'item_id': 'Test.WaterskinFull', 'display_name': 'Waterskin (Full)', 'emptied_version': empty,
                'description': 'A waterskin full of fresh water. Left Mouse drinks it. How much it holds is still open.'})
    save(empty, {**shared, 'display_name': 'Waterskin', 'filled_version': full,
                 'description': 'A stitched hide waterskin. Hold it at fresh water and press E to fill it.'})

    anims = animations()
    blueprint = unreal.load_asset(CHARACTER)
    defaults = unreal.get_default_object(unreal.load_object(None, f'{CHARACTER}.BP_ThirdPersonCharacter_C'))
    for prop, key in (('equip_animation', 'equip'), ('ignite_animation', 'ignite'), ('drink_animation', 'drink'), ('fill_animation', 'fill')):
        defaults.set_editor_property(prop, anims[key])
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    assert unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    Path(unreal.Paths.project_saved_dir(), 'CoreToolsResult.json').write_text(json.dumps({
        'success': True, 'torch_light': torch.get_editor_property('held_light_intensity'),
        'animations': {k: round(v.get_play_length(), 2) for k, v in anims.items()}}, indent=2))
    unreal.log('Core tools built')


if __name__ == '__main__':
    main()
