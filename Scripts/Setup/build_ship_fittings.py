"""Build the sloop's fittings from the owner's art and give them to the test items. Safe to run again.
Run in the editor after build_sloop_hull.py, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

- Mainsail (Medium): the gaff mainsail cloth from Art/Concepts/Sails/2026-10-11/Medium-Sail-v1.png on its boom
  and gaff, standing up from the boom so half sail lowers it; furled, the cloth is bundled on the boom.
- Headsail (Small): the jib from Small-Sail-v1.png hanked to the forestay, built along the stay so half sail
  shortens it down the stay; furled, it is rolled on the stay.
- Helm: a spoked ship's wheel on a timber stand; the wheel turns with the rudder.

The cloth is the art itself mapped corner to corner onto a gently filled sail; its alpha cuts the outline. Every
fitting is placed relative to its mount on DA_Ship_Sloop and the hull's rig positions. All sizes are tuning.
The sail builders here (gaff, square and jib) are shared: build_schooner.py sizes them to its own rig.
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

# Corners of the sail cloth in the art, in pixels (image 1536 x 1024): found from each image's alpha with the
# thin corner rope loops eroded away, so the cloth's own edges meet the mast, boom, gaff and stay.
MAIN_ART = {'tack': (186, 940), 'throat': (416, 208), 'peak': (1086, 54), 'clew': (1460, 928)}
JIB_ART = {'tack': (176, 968), 'head': (330, 80), 'clew': (1348, 906)}
ART_SIZE = (1536.0, 1024.0)
# The Large square sail (image 1254 x 1254): head along the yard, foot below.
SQUARE_ART = {'head_port': (82, 130), 'head_starboard': (1174, 150), 'foot_port': (56, 1098), 'foot_starboard': (1210, 1142)}
SQUARE_ART_SIZE = (1254.0, 1254.0)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def art_uv(p, size=ART_SIZE):
    return (p[0] / size[0], p[1] / size[1])


def cloth(b, corners, art, belly, steps=18, sheet=0.0, axis=1, art_size=ART_SIZE):
    """A four-cornered sail (tack, clew along the foot; throat, peak along the head) filled by the wind toward
    starboard (or forward, for axis 0), with the art stretched corner to corner. `sheet` carries the aft edge
    that far to leeward, as when a jib is sheeted out past the sails inside it."""
    tack, clew, throat, peak = corners
    a_tack, a_clew, a_throat, a_peak = (art_uv(c, art_size) for c in art)
    rows = []
    uvs = []
    for i in range(steps + 1):
        s = i / steps
        row, uv_row = [], []
        for j in range(steps + 1):
            t = j / steps
            p = lerp(lerp(tack, clew, s), lerp(throat, peak, s), t)
            depth = belly * math.sin(math.pi * s) * (0.55 + 0.45 * math.sin(math.pi * t)) + sheet * s
            q = list(p)
            q[axis] += depth
            row.append(tuple(q))
            uv_row.append(lerp(lerp(a_tack, a_clew, s), lerp(a_throat, a_peak, s), t))
        rows.append(row)
        uvs.append(uv_row)
    b.slot = CLOTH
    # The cloth's vertex colours tell its material where each point lies on the sail (red along the foot, green up
    # it), which way it bellies (blue: 1 toward Y, 0 toward X) and how deep the belly was built (alpha, in metres),
    # so the wind can fill it or let it go slack (cloth_materials).
    b.grid(rows, lambda i, j: tuple(1 if k == axis else 0 for k in range(3)), uv_of=lambda i, j, p: uvs[i][j],
           colour_of=lambda i, j: (i / steps, j / steps, 1.0 if axis == 1 else 0.0, min(belly / 100.0, 1.0)))
    b.slot = TIMBER


def bundle(b, path, radius):
    """Sail cloth rolled up along a spar: a lumpy roll mapped to the middle of the art, where the cloth is solid."""
    b.slot = CLOTH
    b.tube(path, lambda k: radius * (1.0 + 0.18 * math.sin(k * 1.7)) * (1.0 - 0.45 * k / (len(path) - 1)),
           sides=10, uv_of=lambda k, s: (0.4 + 0.2 * s / 10, 0.4 + 0.2 * k / max(len(path) - 1, 1)))
    b.slot = TIMBER


def gaff_sail(furled, boom=575.0, throat=516.0, peak=(-470.0, 778.0), belly=42.0):
    """A gaff sail in its own frame: origin on the mast at boom height, X forward, Z up. `boom` is the boom's
    length, `throat` the height of the gaff's jaws on the mast and `peak` where the gaff ends (x, z)."""
    b = Builder()
    b.tube([(-18, 0, -6), (-boom, 0, -6)], lambda k: (8.0, 6.0)[k], sides=10)        # boom
    b.box((-22, 0, -6), (16, 30, 16))                                                # boom jaws on the mast
    if furled:
        b.tube([(-18, 0, 30), (peak[0], 0, 40)], lambda k: (6.0, 4.5)[k], sides=10)  # gaff lowered onto the boom
        bundle(b, [(-24 - (boom - 55) / 20 * k, 0, 15) for k in range(21)], 13.0)
    else:
        b.tube([(-18, 0, throat), (peak[0], 0, peak[1])], lambda k: (6.0, 4.5)[k], sides=10)   # gaff
        b.box((-22, 0, throat), (16, 30, 16))                                        # gaff jaws
        cloth(b, ((-16, 0, 8), (-(boom - 15), 0, 8), (-16, 0, throat - 4), (peak[0] + 15, 0, peak[1] - 8)),
              (MAIN_ART['tack'], MAIN_ART['clew'], MAIN_ART['throat'], MAIN_ART['peak']), belly=belly)
    return b


def mainsail(furled):
    """A gaff mainsail (the schooner's rig builds its own; the sloop now uses square-yard assemblies)."""
    return gaff_sail(furled)


def square_sail(furled, head=900.0, foot=1000.0, drop=760.0, belly=70.0):
    """A square sail in its own frame: origin on the middle of its yard, Y across, hanging down to its foot and
    filled forward by a following wind; furled, it is bundled on the yard."""
    b = Builder()
    yard = head / 2 + 40
    b.tube([(0, -yard, 0), (0, yard, 0)], 7.0, sides=10)                             # yard
    b.box((-10, 0, 0), (14, 34, 18))                                                 # parrel on the mast
    if furled:
        bundle(b, [(6, -head / 2 + head / 20 * k, -8) for k in range(21)], 16.0)
    else:
        cloth(b, ((6, -foot / 2, -drop), (6, foot / 2, -drop), (6, -head / 2, -6), (6, head / 2, -6)),
              (SQUARE_ART['foot_port'], SQUARE_ART['foot_starboard'], SQUARE_ART['head_port'], SQUARE_ART['head_starboard']),
              belly=belly, axis=0, art_size=SQUARE_ART_SIZE)
    return b


def sail_assembly(height, yard_z, yard_half, radius=14.0, top_radius=9.0, deck_to_mount=50.0, socket_top=34.0):
    """A removable sail assembly's mast (owner, October 18: the mast belongs to the assembly, the hull has only the
    empty socket; the sheet's masts with brass bands, a cap and lifts to the yard's ends). In the mount's frame, origin
    at the hardpoint, Z up: `height` and `yard_z` are above the deck, `yard_half` is half the yard's length. A plug
    reaches down into the socket's collar."""
    b = Builder()
    base = socket_top - deck_to_mount - 12.0               # the plug's foot, inside the collar
    top = height - deck_to_mount
    b.tube([(0, 0, base), (0, 0, base + 14), (0, 0, top - 30), (0, 0, top)],
           lambda k: (radius * .8, radius, top_radius * 1.05, top_radius)[k], sides=14)
    b.alpha = .5
    for f in (.12, .38, .66, .9):
        z = base + (top - base) * f
        r = radius + (top_radius - radius) * f
        b.tube([(0, 0, z - 3), (0, 0, z + 3)], r + 2.0, sides=14)
    b.alpha = 1.0
    b.box((0, 0, top + 6), (2.4 * top_radius, 2.4 * top_radius, 12), iron=1.0)         # the iron cap
    first = len(b.colours)
    # Lifts from the masthead to the yard's ends. The yard runs fore and aft at zero trim, like every sail on the
    # shared trim model (angle 0 is along the ship; the sail swings out from it).
    for sign in (-1, 1):
        b.tube([(0, 0, top - 12), (sign * yard_half * .5, 0, (top + yard_z) / 2 + 20), (sign * (yard_half - 6), 0, yard_z + 6)], 1.3, sides=5)
    for k in range(first, len(b.colours)):
        b.colours[k] = (1.0, 0.0, 0.5)
    return b


def sail_assembly_looks(assemblies, deck_z, timber, sails, prefix):
    """Write each hardpoint's removable sail assembly (owner, October 18): the square-yard sail with its yard, furled
    or set, and the assembly's own mast. `assemblies` is a hull's ASSEMBLIES (mast and yard heights above the deck, the
    sail's head and foot widths and drop); the mount stands 50 cm above the deck. Returns {mount: (sail mesh, furled
    mesh, the sail's look transform relative to the mount, mast mesh)}."""
    out = {}
    for mount_id, a in assemblies.items():
        cloth = sails['Large']                       # the square sail's art (the cloth's picture is a square sail)
        name = f'{FOLDER}/SM_{prefix}{mount_id}'
        sail = write_static_mesh(square_sail(False, a['head'], a['foot'], a['drop'], a['belly']), name + '_v1', [timber, cloth], UV_TILE, collision=False)
        furled = write_static_mesh(square_sail(True, a['head'], a['foot'], a['drop']), name + 'Furled_v1', [timber, cloth], UV_TILE, collision=False)
        mast = write_static_mesh(sail_assembly(a['height'], a['yard'], a['head'] / 2 + 40, a.get('radius', 14.0), a.get('top_radius', 9.0)),
                                 name + 'Mast_v1', [timber], UV_TILE, collision=False)
        # Turned a quarter so its yard runs fore and aft (zero trim is along the ship), clear of the mast beside it.
        out[mount_id] = (sail, furled, unreal.Transform(location=unreal.Vector(0, 24, a['yard'] - 50), rotation=unreal.Rotator(0, 0, 90)), mast)
    return out


def jib_frame(stay_bow=None, stay_top=None, tack_t=0.04, head_t=0.68, clew=None):
    """A jib's frame on its stay: origin at the tack, Z up the stay, X toward the clew."""
    stay_bow = stay_bow or hull.STAY_BOW
    stay_top = stay_top or hull.STAY_TOP
    tack = lerp(stay_bow, stay_top, tack_t)
    head = lerp(stay_bow, stay_top, head_t)
    clew = clew or (hull.MAST_X + 140, 0.0, 445.0)
    rotation = unreal.MathLibrary.make_rot_from_zx(unreal.Vector(*[head[i] - tack[i] for i in range(3)]),
                                                   unreal.Vector(*[clew[i] - tack[i] for i in range(3)]))
    return unreal.Transform(location=unreal.Vector(*tack), rotation=rotation), tack, head, clew


def jib(furled, frame_args=(), belly=28.0, sheet=0.0):
    """In the jib's frame: origin at the tack on its stay, Z up the stay, so lowering Z shortens the sail."""
    frame, tack, head, clew = jib_frame(*frame_args)
    local = lambda p: tuple(getattr(frame.inverse_transform_location(unreal.Vector(*p)), a) for a in 'xyz')
    b = Builder()
    if furled:
        bundle(b, [local(lerp(tack, head, k / 16)) for k in range(17)], 8.0)
    else:
        # A triangle: the head stands in for both upper corners.
        corners = (local(tack), local(clew), local(head), local(head))
        cloth(b, corners, (JIB_ART['tack'], JIB_ART['clew'], JIB_ART['head'], JIB_ART['head']), belly=belly, sheet=sheet)
    return b


WHEEL_HUB = (-12.0, 0.0, 128.0)     # where the wheel turns, in the helm's frame
WHEEL_TURN = 270.0                  # degrees the wheel turns with the rudder hard over (tuning)


def wheel_stand():
    """In the helm's frame: origin on the deck under the mount; the helmsman stands aft of the wheel. The stand
    and its axle; the wheel turns on it (wheel_spokes)."""
    b = Builder()
    b.box((0, 0, 3), (36, 56, 6))
    for y in (-22, 22):
        b.box((4, y, 66), (12, 8, 120))
    b.box((4, 0, 124), (18, 52, 14))
    b.tube([(-4, 0, WHEEL_HUB[2]), (-22, 0, WHEEL_HUB[2])], 9.0, sides=12)
    return b


def wheel_spokes():
    """The wheel itself, centred on its hub, turning about X: iron hub, eight spokes with handles, and the rim."""
    b = Builder()
    b.tube([(4, 0, 0), (-4, 0, 0)], 10.0, sides=12, iron=1.0)
    rim = [(0, 52 * math.cos(2 * math.pi * k / 24), 52 * math.sin(2 * math.pi * k / 24)) for k in range(25)]
    b.tube(rim, 3.6, sides=8, capped=False)
    for k in range(8):
        a = 2 * math.pi * k / 8
        c, s = math.cos(a), math.sin(a)
        b.tube([(0, 8 * c, 8 * s), (0, 60 * c, 60 * s)], 2.4, sides=6)
        b.tube([(0, 60 * c, 60 * s), (0, 75 * c, 75 * s)], lambda q: (3.0, 2.6)[q], sides=8)
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
                'Small': import_art('T_SailSmall_v1', ART / 'Small-Sail-v1.png'),
                'Large': import_art('T_SailLarge_v1', ART / 'Large-Sail-v1.png')}
    base, node, custom = material_builder(f'{FOLDER}/M_SailCloth_v1')
    base.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    base.set_editor_property('two_sided', True)
    art = node(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name='Cloth', texture=textures['Medium'])
    assert mel.connect_material_property(art, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    # Wind in the cloth (owner, October 16: sails catching the wind billow out; sails not catching it go slack but keep
    # moving). Fill comes from the ship per sail (AEWShip::ShowSailFill, custom primitive data 0): +1 full with the
    # belly the way it was built, -1 full the other way, 0 slack. The belly is shaped as it was built, deepest in the
    # middle and held at the spars; slack cloth lies flat and flaps more loosely. Amounts are tuning.
    fill = node(unreal.MaterialExpressionScalarParameter, parameter_name='Fill', default_value=1.0,
                use_custom_primitive_data=True, primitive_data_index=0)
    wind = custom('float s = V.r, t = V.g;'
                  ' float w = sin(3.14159 * s) * (0.55 + 0.45 * sin(3.14159 * t));'
                  ' float belly = A * 100.0;'
                  ' float slack = 1.0 - saturate(abs(F));'
                  ' float flap = w * (2.0 + 16.0 * slack) * sin(T * (5.0 + 4.0 * slack) + s * 7.0 + t * 5.0)'
                  '            * (0.6 + 0.4 * sin(T * 1.3 + s * 3.0));'
                  ' float push = belly * w * (clamp(F, -1.0, 1.0) - 1.0) + flap;'
                  ' float3 n = V.b > 0.75 ? float3(0, 1, 0) : float3(1, 0, 0);'
                  ' return n * push;',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('V', 'A', 'F', 'T'))
    colours = node(unreal.MaterialExpressionVertexColor)
    assert mel.connect_material_expressions(colours, '', wind, 'V')
    assert mel.connect_material_expressions(colours, 'A', wind, 'A')
    assert mel.connect_material_expressions(fill, '', wind, 'F')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTime), '', wind, 'T')
    to_world = node(unreal.MaterialExpressionTransform,
                    transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
                    transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    assert mel.connect_material_expressions(wind, '', to_world, '')
    assert mel.connect_material_property(to_world, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
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


def set_fitting(item_name, mesh, transform, furled=None, turning=None):
    """`turning` is (mesh, pivot location in the fitting's frame, rotator at full starboard rudder) for a part
    that turns with the rudder."""
    item = unreal.load_asset(f'{ITEMS}/{item_name}')
    assert item, item_name
    item.set_editor_property('fitting_mesh', mesh)
    item.set_editor_property('fitting_mesh_transform', transform)
    item.set_editor_property('fitting_furled_mesh', furled)
    turning_mesh, pivot, turn = turning or (None, (0, 0, 0), unreal.Rotator())
    item.set_editor_property('fitting_turning_mesh', turning_mesh)
    item.set_editor_property('fitting_turning_pivot', unreal.Transform(location=unreal.Vector(*pivot)))
    item.set_editor_property('fitting_turn_at_full', turn)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    definition = unreal.load_asset(hull.DEFINITION)
    timber = make_timber_material()
    sails = cloth_materials()
    write = lambda b, name, cloth_mi: write_static_mesh(b, f'{FOLDER}/{name}', [timber, cloth_mi], UV_TILE, collision=False)

    # The sloop's two removable sail assemblies; the same meshes are the Medium and Small items' own look.
    looks = sail_assembly_looks(hull.ASSEMBLIES, hull.DECK_Z, timber, sails, 'Sloop')
    for mount_id, item in (('Mainsail', 'DA_TestSailMedium'), ('Headsail', 'DA_TestSailSmall')):
        sail, furled, look, _mast = looks[mount_id]
        set_fitting(item, sail, look, furled)

    wheel_mesh = write_static_mesh(wheel_stand(), f'{FOLDER}/SM_ShipWheel_v1', [timber], UV_TILE, collision=False)
    spokes = write_static_mesh(wheel_spokes(), f'{FOLDER}/SM_ShipWheelSpokes_v1', [timber], UV_TILE, collision=False)
    at = mount_location(definition, 'Helm')
    set_fitting('DA_TestShipHelm', wheel_mesh, unreal.Transform(location=unreal.Vector(0, 0, -50)),   # on the deck under its mount
                turning=(spokes, WHEEL_HUB, unreal.Rotator(roll=WHEEL_TURN, pitch=0, yaw=0)))

    Path(unreal.Paths.project_saved_dir(), 'ShipFittingsResult.json').write_text(json.dumps({'success': True}))
    unreal.log('Ship fittings built')


if __name__ == '__main__':
    main()
