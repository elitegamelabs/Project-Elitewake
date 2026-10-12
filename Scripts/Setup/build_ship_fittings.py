"""Build the sloop's fittings from the owner's art and give them to the test items. Safe to run again.
Run in the editor after build_sloop_hull.py, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

- Mainsail (Medium): the gaff mainsail cloth from Art/Concepts/Sails/2026-10-11/Medium-Sail-v1.png on its boom
  and gaff, standing up from the boom so half sail lowers it; furled, the cloth is bundled on the boom.
- Headsail (Small): the jib from Small-Sail-v1.png hanked to the forestay, built along the stay so half sail
  shortens it down the stay; furled, it is rolled on the stay.
- Helm: a spoked ship's wheel on a timber stand.

The cloth is the art itself mapped corner to corner onto a gently filled sail; its alpha cuts the outline. Every
fitting is placed relative to its mount on DA_Ship_Sloop and the hull's rig positions. All sizes are tuning.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sloop_hull as hull  # noqa: E402
from ship_geometry import Builder, make_timber_material, material_builder, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
ART = Path(unreal.Paths.project_dir()).resolve() / 'Art/Concepts/Sails/2026-10-11'
ITEMS = '/Game/Elitewake/Items/Testing'
UV_TILE = hull.UV_TILE
TIMBER, CLOTH = 0, 1

# Corners of the sail cloth in the art, in pixels (image 1536 x 1024), found from each image's alpha.
MAIN_ART = {'tack': (134, 956), 'throat': (398, 172), 'peak': (1110, 10), 'clew': (1502, 944)}
JIB_ART = {'tack': (114, 986), 'head': (296, 10), 'clew': (1420, 910)}
ART_SIZE = (1536.0, 1024.0)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def art_uv(p):
    return (p[0] / ART_SIZE[0], p[1] / ART_SIZE[1])


def cloth(b, corners, art, belly, steps=18):
    """A four-cornered sail (tack, clew along the foot; throat, peak along the head) filled by the wind toward
    starboard, with the art stretched corner to corner."""
    tack, clew, throat, peak = corners
    a_tack, a_clew, a_throat, a_peak = (art_uv(c) for c in art)
    rows = []
    uvs = []
    for i in range(steps + 1):
        s = i / steps
        row, uv_row = [], []
        for j in range(steps + 1):
            t = j / steps
            p = lerp(lerp(tack, clew, s), lerp(throat, peak, s), t)
            depth = belly * math.sin(math.pi * s) * (0.55 + 0.45 * math.sin(math.pi * t))
            row.append((p[0], p[1] + depth, p[2]))
            uv_row.append(lerp(lerp(a_tack, a_clew, s), lerp(a_throat, a_peak, s), t))
        rows.append(row)
        uvs.append(uv_row)
    b.slot = CLOTH
    b.grid(rows, lambda i, j: (0, 1, 0), uv_of=lambda i, j, p: uvs[i][j])
    b.slot = TIMBER


def bundle(b, path, radius):
    """Sail cloth rolled up along a spar: a lumpy roll mapped to the middle of the art, where the cloth is solid."""
    b.slot = CLOTH
    b.tube(path, lambda k: radius * (1.0 + 0.18 * math.sin(k * 1.7)) * (1.0 - 0.45 * k / (len(path) - 1)),
           sides=10, uv_of=lambda k, s: (0.4 + 0.2 * s / 10, 0.4 + 0.2 * k / max(len(path) - 1, 1)))
    b.slot = TIMBER


def mainsail(furled):
    """In the mainsail's frame: origin on the mast at boom height, X forward, Z up."""
    b = Builder()
    b.tube([(-18, 0, -6), (-575, 0, -6)], lambda k: (8.0, 6.0)[k], sides=10)        # boom
    b.box((-22, 0, -6), (16, 30, 16))                                                # boom jaws on the mast
    if furled:
        b.tube([(-18, 0, 30), (-470, 0, 40)], lambda k: (6.0, 4.5)[k], sides=10)     # gaff lowered onto the boom
        bundle(b, [(-24 - 26 * k, 0, 15) for k in range(21)], 13.0)
    else:
        b.tube([(-18, 0, 516), (-470, 0, 778)], lambda k: (6.0, 4.5)[k], sides=10)   # gaff
        b.box((-22, 0, 516), (16, 30, 16))                                           # gaff jaws
        cloth(b, ((-16, 0, 8), (-560, 0, 8), (-16, 0, 512), (-455, 0, 770)),
              (MAIN_ART['tack'], MAIN_ART['clew'], MAIN_ART['throat'], MAIN_ART['peak']), belly=42)
    return b


def jib_frame():
    tack = lerp(hull.STAY_BOW, hull.STAY_TOP, 0.06)
    head = lerp(hull.STAY_BOW, hull.STAY_TOP, 0.70)
    clew = (225.0, 0.0, 445.0)
    rotation = unreal.MathLibrary.make_rot_from_zx(unreal.Vector(*[head[i] - tack[i] for i in range(3)]),
                                                   unreal.Vector(*[clew[i] - tack[i] for i in range(3)]))
    return unreal.Transform(location=unreal.Vector(*tack), rotation=rotation), tack, head, clew


def jib(furled):
    """In the jib's frame: origin at the tack on the forestay, Z up the stay, so lowering Z shortens the sail."""
    frame, tack, head, clew = jib_frame()
    local = lambda p: tuple(getattr(frame.inverse_transform_location(unreal.Vector(*p)), a) for a in 'xyz')
    b = Builder()
    if furled:
        bundle(b, [local(lerp(tack, head, k / 16)) for k in range(17)], 8.0)
    else:
        # A triangle: the head stands in for both upper corners.
        corners = (local(tack), local(clew), local(head), local(head))
        cloth(b, corners, (JIB_ART['tack'], JIB_ART['clew'], JIB_ART['head'], JIB_ART['head']), belly=28)
    return b


def wheel():
    """In the helm's frame: origin on the deck under the mount; the helmsman stands aft of the wheel."""
    b = Builder()
    b.box((0, 0, 3), (36, 56, 6))
    for y in (-22, 22):
        b.box((4, y, 66), (12, 8, 120))
    b.box((4, 0, 124), (18, 52, 14))
    cx, cz = -12.0, 128.0
    b.tube([(-4, 0, cz), (-22, 0, cz)], 9.0, sides=12)
    b.tube([(-8, 0, cz), (-16, 0, cz)], 10.0, sides=12, iron=1.0)
    rim = [(cx, 52 * math.cos(2 * math.pi * k / 24), cz + 52 * math.sin(2 * math.pi * k / 24)) for k in range(25)]
    b.tube(rim, 3.6, sides=8, capped=False)
    for k in range(8):
        a = 2 * math.pi * k / 8
        c, s = math.cos(a), math.sin(a)
        b.tube([(cx, 8 * c, cz + 8 * s), (cx, 60 * c, cz + 60 * s)], 2.4, sides=6)
        b.tube([(cx, 60 * c, cz + 60 * s), (cx, 75 * c, cz + 75 * s)], lambda q: (3.0, 2.6)[q], sides=8)
    return b


def import_art(name, source):
    path = f'{FOLDER}/{name}'
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        task = unreal.AssetImportTask()
        for k, v in {'filename': str(source), 'destination_path': FOLDER, 'destination_name': name,
                     'automated': True, 'replace_existing': False, 'save': True}.items():
            task.set_editor_property(k, v)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(path)
    assert isinstance(texture, unreal.Texture2D), path
    return texture


def cloth_materials():
    """Sailcloth: the art's colour, its alpha as the outline, seen from both sides."""
    mel = unreal.MaterialEditingLibrary
    textures = {'Medium': import_art('T_SailMedium_v1', ART / 'Medium-Sail-v1.png'),
                'Small': import_art('T_SailSmall_v1', ART / 'Small-Sail-v1.png')}
    base, node, _ = material_builder(f'{FOLDER}/M_SailCloth_v1')
    base.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    base.set_editor_property('two_sided', True)
    art = node(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name='Cloth', texture=textures['Medium'])
    assert mel.connect_material_property(art, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(art, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=0.9), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(base)
    assert unreal.EditorAssetLibrary.save_loaded_asset(base)
    instances = {}
    for size, texture in textures.items():
        path = f'{FOLDER}/MI_Sail{size}_v1'
        mi = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            f'MI_Sail{size}_v1', FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, base)
        mel.set_material_instance_texture_parameter_value(mi, 'Cloth', texture)
        mel.update_material_instance(mi)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
        instances[size] = mi
    return instances


def mount_location(definition, mount_id):
    m = next(m for m in definition.get_editor_property('mounts') if str(m.get_editor_property('mount_id')) == mount_id)
    return m.get_editor_property('transform').translation


def set_fitting(item_name, mesh, transform, furled=None):
    item = unreal.load_asset(f'{ITEMS}/{item_name}')
    assert item, item_name
    item.set_editor_property('fitting_mesh', mesh)
    item.set_editor_property('fitting_mesh_transform', transform)
    item.set_editor_property('fitting_furled_mesh', furled)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    definition = unreal.load_asset(hull.DEFINITION)
    timber = make_timber_material()
    sails = cloth_materials()
    write = lambda b, name, cloth_mi: write_static_mesh(b, f'{FOLDER}/{name}', [timber, cloth_mi], UV_TILE, collision=False)

    main_mesh = write(mainsail(False), 'SM_SailMain_v1', sails['Medium'])
    main_furled = write(mainsail(True), 'SM_SailMainFurled_v1', sails['Medium'])
    at = mount_location(definition, 'Mainsail')
    set_fitting('DA_TestSailMedium', main_mesh,
                unreal.Transform(location=unreal.Vector(hull.MAST_X - at.x, -at.y, hull.BOOM_Z - at.z)), main_furled)

    jib_mesh = write(jib(False), 'SM_SailJib_v1', sails['Small'])
    jib_furled = write(jib(True), 'SM_SailJibFurled_v1', sails['Small'])
    frame, tack, _, _ = jib_frame()
    at = mount_location(definition, 'Headsail')
    set_fitting('DA_TestSailSmall', jib_mesh,
                unreal.Transform(location=unreal.Vector(tack[0] - at.x, tack[1] - at.y, tack[2] - at.z),
                                 rotation=frame.rotation.rotator()), jib_furled)

    wheel_mesh = write_static_mesh(wheel(), f'{FOLDER}/SM_ShipWheel_v1', [timber], UV_TILE, collision=False)
    at = mount_location(definition, 'Helm')
    set_fitting('DA_TestShipHelm', wheel_mesh, unreal.Transform(location=unreal.Vector(0, 0, hull.DECK_Z - at.z)))

    Path(unreal.Paths.project_saved_dir(), 'ShipFittingsResult.json').write_text(json.dumps({'success': True}))
    unreal.log('Ship fittings built')


if __name__ == '__main__':
    main()
