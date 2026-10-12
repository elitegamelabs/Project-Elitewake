"""Build the schooner from the owner's art (Art/Concepts/Boats/2026-10-11/Schooner-*): its hull, standing rigging,
the look of each sail on its rig, its definition, and moor it off the coastal dock. Safe to run again.
Run in the editor after build_ship_fittings.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

About 22 m long and 6.6 m in beam, half again the sloop's length. Like the sloop it is double-ended, the stern
rising to a post as the bow does. A raised aft deck carries the helm and the mizzen, with stairs up each side and
a breast rail. The main deck has a hatch with stairs down to a lower deck under it: twelve gunports, six a side, a
mast step at each mast, pillars, ribs and beams, and an aft bulkhead with a doorway into a small aft hold.

Three masts stand in the art's three sockets. The foremast carries the Large square topsail; the main and
mizzen carry gaff sails (Medium); three jibs (Small) set on stays out to the bowsprit. That is the design's
schooner rig: 2 Medium, 1 Large and 3 Small. Each mount sets how its sail looks, so the same items fit the sloop.

Coordinates are the ship's own, in cm, with the waterline at Z 0 and the lower deck above the swell. Sizes are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ship_fittings as fittings  # noqa: E402
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402
from ship_hull import Hull, tar_rope  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
DEFINITION = '/Game/Elitewake/Ships/DA_Ship_Schooner'
ITEMS = '/Game/Elitewake/Items/Testing'
MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
MOORING = (6400.0, -1500.0, -65.0)   # south of the dock, in deep water and clear of the swimming lane along Y 0
T = unreal.EWShipMountType

PORT_XS = (-480.0, -280.0, -80.0, 120.0, 320.0, 520.0)
PORT = (56.0, 105.0, 160.0)          # width, sill and head heights
QUARTERDECK = (-560.0, 150.0)        # front x, rise above the main deck
HULL = Hull(stern_x=-1100.0, bow_x=1100.0, beam=330.0, keel_z=-170.0,
            deck_z=300.0, floor_z=40.0,
            sheer_mid=395.0, sheer_rise=130.0, sheer_flat=100.0,
            beam_power=2.1, keel_flat=450.0, keel_power=2.2, full_mid=2.9, full_end=1.5, full_len=350.0,
            strakes=14, wales=(9, 12), tar_line=95.0,
            gunports=[(x, PORT[0], PORT[1], PORT[2]) for x in PORT_XS],
            quarterdeck=QUARTERDECK)
DECK_Z, FLOOR_Z, QD_Z = HULL.deck_z, HULL.floor_z, HULL.deck_z + QUARTERDECK[1]
UV_TILE = HULL.uv_tile
HATCH = (100.0, 360.0, 55.0)         # stairs down to the lower deck: aft x, forward x, half-width
GRATING = (-330.0, 130.0, 100.0)     # centre x, length, width
LOWER_BULKHEAD_X = -600.0
LADDER_X = -180.0                    # between two gunports, clear of the stairs to the aft deck
CAPSTAN = (780.0, -110.0)
FRAMES = range(-1040, 1060, 60)

# Rig.
FORE_X, FORE_TOP = 560.0, 2150.0
MAIN_X, MAIN_TOP = -60.0, 2050.0
MIZZEN_X, MIZZEN_TOP = -800.0, 1550.0
YARD_Z = 1900.0                      # the fore topsail's yard
BOOM_Z = 680.0                       # main and mizzen booms, above heads on the raised aft deck
BOWSPRIT = ((1010.0, 0.0, HULL.sheer(1010.0) + 30), (1650.0, 0.0, 640.0))   # resting on the stem head
# Jib stays: (on the bowsprit, on the foremast). The outer stay meets the foremast's head, in front of the
# topsail; the inner two meet it below the topsail's foot.
STAYS = {'FlyingJib': ((1650.0, 0.0, 640.0), (FORE_X + 10, 0.0, 2120.0)),
         'Jib': ((1450.0, 0.0, 610.0), (FORE_X + 10, 0.0, 1180.0)),
         'Staysail': ((1150.0, 0.0, 570.0), (FORE_X + 10, 0.0, 1050.0))}
# Each jib: tack and head along its stay, the clew, how full it is and how far its leech is sheeted to leeward.
JIBS = {'FlyingJib': (0.05, 0.62, (1000.0, 0.0, 760.0), 34.0, 70.0),
        'Jib': (0.05, 0.80, (850.0, 0.0, 520.0), 30.0, 40.0),
        'Staysail': (0.05, 0.85, (680.0, 0.0, 520.0), 24.0, 15.0)}
JIB_MOUNTS = {'FlyingJib': 1010.0, 'Jib': 930.0, 'Staysail': 850.0}


# ---- Hull --------------------------------------------------------------------------------------------------

def bulkhead(b, x, z0, z1, openings=(), thick=8.0, plank=20.0):
    """A bulkhead of horizontal planks across the hull at x from z0 to z1, each cut to the planking, with
    framed openings (y0, y1, z0, z1) left clear."""
    n = max(1, round((z1 - z0) / plank))
    for k in range(n):
        za, zb = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
        zm = (za + zb) / 2
        half = HULL.inner_y(x, zm) + 2
        edges = [-half] + [y for o in sorted(openings) if o[2] < zm < o[3] for y in o[:2]] + [half]
        for ya, yb in zip(edges[0::2], edges[1::2]):
            if yb - ya > 1:
                b.box((x, (ya + yb) / 2, zm), (thick, yb - ya, zb - za - 0.6))
    for y0, y1, oz0, oz1 in openings:
        for y in (y0 - 5, y1 + 5):
            b.box((x, y, (oz0 + oz1) / 2), (thick + 6, 10, oz1 - oz0))
        b.box((x, (y0 + y1) / 2, oz1 + 5), (thick + 6, y1 - y0 + 20, 10))


def quarterdeck(b):
    front, rise = QUARTERDECK
    HULL.deck(b, QD_Z, x_range=(HULL.stern_x, front), underside=False, tone_seed=11)
    bulkhead(b, front, DECK_Z, QD_Z)
    # Its front: a cabin door between two small windows, all closed, and a beam along the top.
    b.box((front + 6, 0.0, DECK_Z + 65), (4, 80, 130))
    for z in (DECK_Z + 25, DECK_Z + 105):
        b.box((front + 9, 0.0, z), (3, 74, 6), iron=1.0)
    for y in (-120.0, 120.0):
        b.box((front + 6, y, DECK_Z + 95), (3, 34, 26), tar=1.0)
        b.box((front + 7, y, DECK_Z + 95), (4, 42, 34))
    b.box((front + 2, 0.0, QD_Z - 6), (16, 2 * HULL.inner_y(front, QD_Z), 12))
    # Stairs up each side against the bulwark, and a breast rail between them.
    stair_y = HULL.inner_y(front, DECK_Z) - 55
    for side in (1, -1):
        HULL.stairs(b, front, front + 175, QD_Z, DECK_Z, 7, width=70.0, y=side * stair_y)
    rail_y = stair_y - 40
    for k in range(7):
        y = -rail_y + 2 * rail_y * k / 6
        b.box((front + 4, y, QD_Z + 45), (8, 8, 90))
    b.sweep([(front + 4, -rail_y - 4, QD_Z + 92), (front + 4, rail_y + 4, QD_Z + 92)], 10.0, 8.0, side=(1, 0, 0))


def grating(b):
    x, length, width = GRATING
    for y in (-width / 2, width / 2):
        b.box((x, y, DECK_Z + 5), (length + 10, 10, 10))
    for dx in (-length / 2, length / 2):
        b.box((x + dx, 0.0, DECK_Z + 5), (10, width, 10))
    for k in range(1, 6):
        b.box((x - length / 2 + length * k / 6, 0.0, DECK_Z + 5), (5, width, 8))
    for k in range(1, 4):
        b.box((x, -width / 2 + width * k / 4, DECK_Z + 5), (length, 5, 8))


def lower_deck(b):
    h = HULL
    h.floor(b, FLOOR_Z, inset=110.0)
    beams = [x for x in range(-1000, 1040, 80) if not HATCH[0] - 20 < x < HATCH[1] + 20]
    h.beams(b, beams + [HATCH[0] - 8, HATCH[1] + 8], DECK_Z)
    h.ribs(b, FRAMES, FLOOR_Z, DECK_Z - h.deck_thick - 10)
    h.stairs(b, HATCH[0] + 5, HATCH[1] - 5, DECK_Z, FLOOR_Z, 13)
    # The aft bulkhead and its doorway into the aft hold.
    bulkhead(b, LOWER_BULKHEAD_X, FLOOR_Z, DECK_Z - h.deck_thick, openings=[(-50.0, 50.0, FLOOR_Z, FLOOR_Z + 200)])
    # Pillars under the beams, and a step at the foot of each mast.
    for x in (-320.0, 480.0):
        for y in (-110.0, 110.0):
            b.box((x, y, (FLOOR_Z + DECK_Z - 18) / 2), (18, 18, DECK_Z - 18 - FLOOR_Z))
            b.box((x, y, FLOOR_Z + 4), (30, 30, 8), iron=1.0)
    for x in (FORE_X, MAIN_X):
        b.box((x, 0.0, FLOOR_Z + 5), (110, 110, 10))
        b.cylinder((x, 0.0, FLOOR_Z + 10), 34, 60, sides=8)
        for z in (FLOOR_Z + 22, FLOOR_Z + 58):
            b.cylinder((x, 0.0, z), 35.5, 5, sides=8, iron=1.0)


def hull_mesh():
    h = HULL
    b = Builder()
    h.outer_shell(b)
    h.inner_shell(b)
    h.rail_and_keel(b, straps=(700, 860, 1000), keel_size=(22.0, 18.0), post_size=(24.0, 26.0))
    h.deck(b, DECK_Z, [HATCH])
    quarterdeck(b)
    grating(b)
    lower_deck(b)
    h.bulwark_posts(b, range(-1050, 1060, 100))
    h.gunport_frames(b)
    h.studs(b, FRAMES)
    h.ladders(b, LADDER_X)
    h.capstan(b, *CAPSTAN, DECK_Z)
    h.mast(b, FORE_X, FORE_TOP, radius=19.0, top_radius=12.0)
    h.mast(b, MAIN_X, MAIN_TOP, radius=20.0, top_radius=12.0)
    h.mast(b, MIZZEN_X, MIZZEN_TOP, radius=16.0, top_radius=10.0)
    h.bowsprit(b, *BOWSPRIT, radius=(14.0, 9.0))
    return b


def rigging():
    """Standing rigging as tarred rope: the three jib stays, a stay from the main to the fore masthead, and
    shrouds, the foremast's led aft so they stay behind its topsail."""
    r = Builder()
    for low, high in STAYS.values():
        r.tube([high, low], 2.0, sides=6)
    r.tube([(MAIN_X + 10, 0.0, MAIN_TOP - 10), (FORE_X - 10, 0.0, FORE_TOP - 30)], 2.0, sides=6)
    HULL.shrouds(r, FORE_X, FORE_TOP - 100, (FORE_X - 20, FORE_X - 60, FORE_X - 100), radius=1.9, spread=13.0)
    HULL.shrouds(r, MAIN_X, MAIN_TOP - 90, (MAIN_X + 20, MAIN_X - 30, MAIN_X - 80), radius=1.9, spread=13.0)
    HULL.shrouds(r, MIZZEN_X, MIZZEN_TOP - 70, (MIZZEN_X + 20, MIZZEN_X - 30), radius=1.7, spread=11.0)
    return tar_rope(r)


# ---- Sails on this rig ---------------------------------------------------------------------------------------

def sail_looks(timber, sails):
    """Each sail mount's look: (mount location, mesh, furled mesh, look transform relative to the mount)."""
    def write(b, name, size):
        return write_static_mesh(b, f'{FOLDER}/{name}', [timber, sails[size]], UV_TILE, collision=False)

    looks = {}
    at = (FORE_X, 0.0, DECK_Z + 50)
    looks['ForeTopsail'] = (at, write(fittings.square_sail(False), 'SM_SchoonerTopsail_v1', 'Large'),
                            write(fittings.square_sail(True), 'SM_SchoonerTopsailFurled_v1', 'Large'),
                            unreal.Transform(location=unreal.Vector(24, 0, YARD_Z - at[2])))
    for mount_id, x, deck, gaff in (('Mainsail', MAIN_X, DECK_Z, dict(boom=600.0, throat=760.0, peak=(-560.0, 1050.0), belly=55.0)),
                                    ('MizzenSail', MIZZEN_X, QD_Z, dict(boom=300.0, throat=520.0, peak=(-290.0, 760.0), belly=34.0))):
        at = (x, 0.0, deck + 50)
        name = 'SM_Schooner' + mount_id
        looks[mount_id] = (at, write(fittings.gaff_sail(False, **gaff), name + '_v1', 'Medium'),
                           write(fittings.gaff_sail(True, **gaff), name + 'Furled_v1', 'Medium'),
                           unreal.Transform(location=unreal.Vector(0, 0, BOOM_Z - at[2])))
    for mount_id, (tack_t, head_t, clew, belly, sheet) in JIBS.items():
        low, high = STAYS[mount_id]
        frame_args = (low, high, tack_t, head_t, clew)
        frame, tack, _, _ = fittings.jib_frame(*frame_args)
        at = (JIB_MOUNTS[mount_id], 0.0, DECK_Z + 50)
        name = 'SM_Schooner' + mount_id
        looks[mount_id] = (at, write(fittings.jib(False, frame_args, belly, sheet), name + '_v1', 'Small'),
                           write(fittings.jib(True, frame_args), name + 'Furled_v1', 'Small'),
                           unreal.Transform(location=unreal.Vector(*[tack[i] - at[i] for i in range(3)]),
                                            rotation=frame.rotation.rotator()))
    return looks


# ---- Assets ------------------------------------------------------------------------------------------------

def data_asset(folder, name, cls):
    asset = unreal.load_asset(f'{folder}/{name}')
    if asset:
        return asset
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', cls)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    assert asset, name
    return asset


def large_sail_item():
    """The Large sail test fitting, alongside the Small and Medium ones from create_sloop_test_assets.py."""
    item = data_asset(ITEMS, 'DA_TestSailLarge', unreal.EWItemDefinition)
    for k, v in {'item_id': 'Test.SailLarge', 'display_name': 'Large Sail', 'category': unreal.EWItemCategory.MISCELLANEOUS,
                 'max_stack_size': 1, 'unit_weight': 45.0, 'fitting_mount_type': T.SAIL,
                 'fitting_sail_size': unreal.EWSailSize.LARGE,
                 'description': 'Ship fitting test fixture. Weight is test tuning; recipe, station cost and art pending.'}.items():
        item.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    return item


def mount(mount_id, kind, location, yaw=0.0, sail=unreal.EWSailSize.NONE, look=None):
    m = unreal.EWShipMount()
    m.set_editor_property('mount_id', mount_id)
    m.set_editor_property('type', kind)
    m.set_editor_property('sail_size', sail)
    m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(*location), rotation=unreal.Rotator(0, 0, yaw)))
    if look:
        mesh, furled, transform = look
        m.set_editor_property('fitted_mesh', mesh)
        m.set_editor_property('fitted_furled_mesh', furled)
        m.set_editor_property('fitted_mesh_transform', transform)
    return m


def update_definition(hull, rig, looks):
    d = data_asset('/Game/Elitewake/Ships', 'DA_Ship_Schooner', unreal.EWShipDefinition)
    sizes = {'ForeTopsail': unreal.EWSailSize.LARGE, 'Mainsail': unreal.EWSailSize.MEDIUM, 'MizzenSail': unreal.EWSailSize.MEDIUM,
             'FlyingJib': unreal.EWSailSize.SMALL, 'Jib': unreal.EWSailSize.SMALL, 'Staysail': unreal.EWSailSize.SMALL}
    mounts = [mount('Helm', T.HELM, (-900.0, 0.0, QD_Z + 50))]
    mounts += [mount(mid, T.SAIL, looks[mid][0], sail=sizes[mid], look=looks[mid][1:]) for mid in sizes]
    # Twelve cannon hardpoints at the lower deck's gunports, facing out.
    for side, name in ((-1, 'Port'), (1, 'Starboard')):
        for k, x in enumerate(PORT_XS):
            y = side * (HULL.inner_y(x, (PORT[1] + PORT[2]) / 2) - 60)
            mounts.append(mount(f'{name}Cannon{k + 1}', T.CANNON, (x, y, FLOOR_Z + 40), yaw=side * 90))
    values = {
        'ship_id': 'Schooner', 'display_name': 'Schooner',
        'hull_mesh': hull, 'rigging_mesh': rig, 'hull_mesh_transform': unreal.Transform(),
        'hull_extent': unreal.Vector(HULL.bow_x - 10, HULL.beam + 5, -HULL.keel_z + 5),
        'hull_draft': -HULL.keel_z, 'deck_height': DECK_Z, 'hold_floor_height': FLOOR_Z,
        'anchor_point': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z + 40),
        'cargo_hatch_point': unreal.Vector((HATCH[0] + HATCH[1]) / 2, 0, DECK_Z + 5),
        'boarding_points': [unreal.Vector(LADDER_X, side * (HULL.half_beam(LADDER_X) + 30), 60) for side in (-1, 1)],
        # Crew: the twelve cannons' crews plus the player and the Surgeon. Speed, turning and hold are tuning.
        'crew_capacity': 14, 'top_speed': 800.0, 'turn_rate': 22.0, 'cargo_slots': 40, 'weight_capacity': 4000.0,
        'mounts': mounts,
    }
    for k, v in values.items():
        d.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(d)
    return d


def moor(definition, large_sail):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    ship = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip) and a.get_editor_property('definition') == definition), None)
    if not ship:
        ship = actors.spawn_actor_from_class(unreal.EWShip, unreal.Vector(*MOORING))
        ship.set_editor_property('definition', definition)
    ship.set_actor_label('Schooner')
    ship.set_actor_location(unreal.Vector(*MOORING), False, False)
    # This test map's starter kit stocks each ship's hold with its fittings; add the Large sail.
    kit = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWStarterKit)), None)
    if kit:
        cargo = list(kit.get_editor_property('ship_cargo'))
        if not any(e.get_editor_property('item') == large_sail for e in cargo):
            entry = unreal.EWStarterKitItem()
            entry.set_editor_property('item', large_sail)
            entry.set_editor_property('quantity', 1)
            kit.set_editor_property('ship_cargo', cargo + [entry])
    assert level.save_current_level()


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = make_timber_material()
    sails = fittings.cloth_materials()
    b = hull_mesh()
    hull = write_static_mesh(b, f'{FOLDER}/SM_SchoonerHull_v1', [timber], UV_TILE)
    rig = write_static_mesh(rigging(), f'{FOLDER}/SM_SchoonerRigging_v1', [timber], UV_TILE, collision=False)
    looks = sail_looks(timber, sails)
    large_sail = large_sail_item()
    definition = update_definition(hull, rig, looks)
    moor(definition, large_sail)
    Path(unreal.Paths.project_saved_dir(), 'SchoonerResult.json').write_text(json.dumps(
        {'success': True, 'vertices': len(b.verts), 'triangles': len(b.tris), 'mounts': len(definition.get_editor_property('mounts'))}, indent=2))
    unreal.log('Schooner built')


if __name__ == '__main__':
    main()
