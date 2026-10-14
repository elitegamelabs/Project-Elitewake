"""Build the brigantine from the owner's art (Art/Concepts/Boats/2026-10-11/Brigantine-*): its hull, standing
rigging, the look of each sail on its rig, its definition, and anchor it off the coast. Safe to run again.
Run in the editor after build_schooner.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

About 30 m long and 8.4 m in beam: stout and ocean-going, clearly larger than the schooner, double-ended like
the other hulls. As in the art it has a raised forecastle at the bow (crew quarters beneath, with a doorway aft)
and a raised quarterdeck at the stern carrying the helm, with the captain's cabin beneath it, both reached by
stairs up each side. Two masts stand in the art's two sockets on the main deck. Under the main deck a single gun
deck carries the prologue brigantine's 24 cannons, twelve a side, reached by stairs through the main hatch.

The rig: the foremast is square-rigged with a course and a topsail; the mainmast carries a gaff mainsail with a
square topsail above it (four Large sail mounts, matching the prologue brigantine's four large sails), and two
Small headsails set on stays to the bowsprit. Like the other hulls it carries channels with deadeyes, ratlines,
pin rails, a rudder and catted anchors. Coordinates are the ship's own, in cm, with the waterline at Z 0 and
the gun deck above the swell. Sizes are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ship_fittings as fittings  # noqa: E402
from build_schooner import data_asset, large_sail_item, mount  # noqa: E402
from build_sloop_hull import capstan_head  # noqa: E402
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402
from ship_hull import Hull, tar_rope  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
MOORING = (7500.0, -4500.0, -65.0)   # south-east of the island, in deep water clear of the other ships
T = unreal.EWShipMountType
L, M, S = unreal.EWSailSize.LARGE, unreal.EWSailSize.MEDIUM, unreal.EWSailSize.SMALL

PORT_XS = tuple(-990.0 + 180.0 * k for k in range(12))
PORT = (64.0, 115.0, 180.0)          # width, sill and head heights
QUARTERDECK = (-900.0, 220.0)        # front x, rise above the main deck
FORECASTLE = (1050.0, 200.0)         # back x, rise above the main deck
CABIN_WINDOWS = (-1000.0, -1130.0, -1260.0)
FORECASTLE_WINDOWS = (1150.0, 1260.0)
HULL = Hull(stern_x=-1500.0, bow_x=1500.0, beam=420.0, keel_z=-230.0,
            deck_z=300.0, floor_z=50.0,
            sheer_mid=400.0, sheer_rise=120.0, sheer_flat=200.0,
            beam_power=2.6, keel_flat=650.0, keel_power=2.3, full_mid=3.2, full_end=1.7, full_len=600.0,
            strakes=16, wales=(10, 13), tar_line=100.0,
            gunports=[(x, *PORT) for x in PORT_XS]
                     + [(x, 40.0, 400.0, 450.0) for x in CABIN_WINDOWS + FORECASTLE_WINDOWS],
            quarterdeck=QUARTERDECK, forecastle=FORECASTLE)
DECK_Z, FLOOR_Z = HULL.deck_z, HULL.floor_z
QD_Z, FC_Z = DECK_Z + QUARTERDECK[1], DECK_Z + FORECASTLE[1]
UV_TILE = HULL.uv_tile
HATCH = (100.0, 400.0, 60.0)         # stairs down to the gun deck: aft x, forward x, half-width
GRATING = (-200.0, 140.0, 110.0)     # centre x, length, width
SKYLIGHT = (-1080.0, -1010.0, 35.0)
LOWER_BULKHEADS = (-1080.0, 1080.0)  # the gun deck's ends, with doorways into small holds fore and aft
LADDER_X = 0.0                       # midway between two gunports
CAPSTAN = (520.0, -170.0)
FRAMES = range(-1440, 1460, 60)

# Rig.
FORE_X, FORE_TOP = 700.0, 2450.0
MAIN_X, MAIN_TOP = -450.0, 2750.0
BOOM_Z = 760.0                       # above heads on the raised quarterdeck
BOWSPRIT_END = (2350.0, 0.0, 720.0)
SQUARES = {  # mount: (mast x, yard height, head width, foot width, drop)
    'ForeCourse': (FORE_X, 1350.0, 1300.0, 1450.0, 680.0),
    'ForeTopsail': (FORE_X, 2100.0, 1000.0, 1250.0, 680.0),
    'MainTopsail': (MAIN_X, 2550.0, 900.0, 1100.0, 520.0),
}
MAIN_GAFF = dict(boom=900.0, throat=850.0, peak=(-860.0, 1250.0), belly=70.0)
STAYS = {'Jib': ((2350.0, 0.0, 720.0), (FORE_X + 10, 0.0, 2420.0)),
         'Staysail': ((1950.0, 0.0, 660.0), (FORE_X + 10, 0.0, 2250.0))}
JIBS = {'Jib': (0.05, 0.62, (1250.0, 0.0, 800.0), 40.0, 60.0),
        'Staysail': (0.05, 0.70, (1050.0, 0.0, 760.0), 32.0, 25.0)}
FORE_SHROUDS = (690.0, 650.0, 610.0, 570.0)
MAIN_SHROUDS = (-470.0, -510.0, -550.0, -590.0)
# Where each sail mount sits: two per mast, either side of it; the headsails on the forecastle.
SAIL_MOUNTS = {'ForeCourse': ((FORE_X + 60, 0.0, DECK_Z + 50), L), 'ForeTopsail': ((FORE_X - 60, 0.0, DECK_Z + 50), L),
               'Mainsail': ((MAIN_X - 60, 0.0, DECK_Z + 50), L), 'MainTopsail': ((MAIN_X + 60, 0.0, DECK_Z + 50), L),
               'Jib': ((1260.0, 0.0, FC_Z + 50), S), 'Staysail': ((1150.0, 0.0, FC_Z + 50), S)}


# ---- Hull --------------------------------------------------------------------------------------------------

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


def gun_deck(b):
    h = HULL
    h.floor(b, FLOOR_Z, inset=110.0)
    beams = [x for x in range(-1360, 1380, 80) if not HATCH[0] - 20 < x < HATCH[1] + 20]
    h.beams(b, beams + [HATCH[0] - 8, HATCH[1] + 8], DECK_Z)
    h.ribs(b, FRAMES, FLOOR_Z, DECK_Z - h.deck_thick - 10)
    h.stairs(b, HATCH[0] + 5, HATCH[1] - 5, DECK_Z, FLOOR_Z, 13)
    for x in LOWER_BULKHEADS:
        h.bulkhead(b, x, FLOOR_Z, DECK_Z - h.deck_thick, openings=[(-50.0, 50.0, FLOOR_Z, FLOOR_Z + 200)])
    for x in (-250.0, 550.0):
        for y in (-140.0, 140.0):
            b.box((x, y, (FLOOR_Z + DECK_Z - 18) / 2), (20, 20, DECK_Z - 18 - FLOOR_Z))
            b.box((x, y, FLOOR_Z + 4), (32, 32, 8), iron=1.0)
    for x in (FORE_X, MAIN_X):
        b.box((x, 0.0, FLOOR_Z + 5), (120, 120, 10))
        b.cylinder((x, 0.0, FLOOR_Z + 10), 38, 60, sides=8)
        for z in (FLOOR_Z + 22, FLOOR_Z + 58):
            b.cylinder((x, 0.0, z), 39.5, 5, sides=8, iron=1.0)


def hull_mesh():
    h = HULL
    b = Builder()
    h.outer_shell(b)
    h.inner_shell(b)
    h.rail_and_keel(b, straps=(950, 1150, 1350), keel_size=(28.0, 22.0), post_size=(30.0, 32.0))
    h.deck(b, DECK_Z, [HATCH])
    # The captain's cabin under the quarterdeck, and the crew's quarters under the forecastle.
    h.raised_deck(b, QUARTERDECK[0], QUARTERDECK[1], 1, (h.stern_x, QUARTERDECK[0]), beams=(-950.0, -1150.0, -1250.0, -1350.0),
                  skylight=SKYLIGHT, side_lights=CABIN_WINDOWS)
    h.raised_deck(b, FORECASTLE[0], FORECASTLE[1], -1, (FORECASTLE[0], h.bow_x), beams=(1120.0, 1220.0, 1320.0),
                  side_lights=FORECASTLE_WINDOWS, steps=10, tone_seed=13)
    grating(b)
    gun_deck(b)
    h.bulwark_posts(b, range(-1450, 1460, 100))
    h.gunport_frames(b)
    h.studs(b, FRAMES)
    h.ladders(b, LADDER_X)
    h.capstan(b, *CAPSTAN, DECK_Z)
    h.mast(b, FORE_X, FORE_TOP, radius=24.0, top_radius=14.0)
    h.mast(b, MAIN_X, MAIN_TOP, radius=26.0, top_radius=15.0)
    heel = (1380.0, 0.0, h.sheer(1380.0) + 30)
    h.bowsprit(b, heel, BOWSPRIT_END, radius=(18.0, 11.0))
    for xs in (FORE_SHROUDS, MAIN_SHROUDS):
        h.channels(b, xs)
    for x in (FORE_X, MAIN_X):
        h.pin_rail(b, x, length=140.0)
    h.rudder(b, -200.0, 60.0, 150.0, 110.0, 20.0)
    for side in (1, -1):
        h.cathead_and_anchor(b, 1300.0, side, 1.6)
    return b


def rigging():
    """Standing rigging as tarred rope: two headsail stays to the bowsprit, a stay from the main to the fore
    masthead, and shrouds with ratlines down to their deadeyes."""
    r = Builder()
    for low, high in STAYS.values():
        r.tube([high, low], 2.4, sides=6)
    r.tube([(MAIN_X + 12, 0.0, MAIN_TOP - 10), (FORE_X - 12, 0.0, FORE_TOP - 30)], 2.4, sides=6)
    HULL.shrouds(r, FORE_X, FORE_TOP - 100, FORE_SHROUDS, radius=2.2, spread=16.0)
    HULL.shrouds(r, MAIN_X, MAIN_TOP - 100, MAIN_SHROUDS, radius=2.2, spread=17.0)
    return tar_rope(r)


# ---- Sails on this rig ---------------------------------------------------------------------------------------

def sail_looks(timber, sails):
    """Each sail mount's look: (mesh, furled mesh, look transform relative to the mount)."""
    def write(b, name, size):
        return write_static_mesh(b, f'{FOLDER}/{name}', [timber, sails[size]], UV_TILE, collision=False)

    looks = {}
    for mount_id, (mast_x, yard_z, head, foot, drop) in SQUARES.items():
        at = SAIL_MOUNTS[mount_id][0]
        name = 'SM_Brigantine' + mount_id
        looks[mount_id] = (write(fittings.square_sail(False, head, foot, drop, belly=90.0), name + '_v1', 'Large'),
                           write(fittings.square_sail(True, head, foot, drop), name + 'Furled_v1', 'Large'),
                           unreal.Transform(location=unreal.Vector(mast_x + 30 - at[0], -at[1], yard_z - at[2])))
    at = SAIL_MOUNTS['Mainsail'][0]
    # The gaff mainsail is cut like the Medium art; the mount is Large, so a Large sail sets here in that shape.
    looks['Mainsail'] = (write(fittings.gaff_sail(False, **MAIN_GAFF), 'SM_BrigantineMainsail_v1', 'Medium'),
                         write(fittings.gaff_sail(True, **MAIN_GAFF), 'SM_BrigantineMainsailFurled_v1', 'Medium'),
                         unreal.Transform(location=unreal.Vector(MAIN_X - at[0], -at[1], BOOM_Z - at[2])))
    for mount_id, (tack_t, head_t, clew, belly, sheet) in JIBS.items():
        low, high = STAYS[mount_id]
        frame_args = (low, high, tack_t, head_t, clew)
        frame, tack, _, _ = fittings.jib_frame(*frame_args)
        at = SAIL_MOUNTS[mount_id][0]
        name = 'SM_Brigantine' + mount_id
        looks[mount_id] = (write(fittings.jib(False, frame_args, belly, sheet), name + '_v1', 'Small'),
                           write(fittings.jib(True, frame_args), name + 'Furled_v1', 'Small'),
                           unreal.Transform(location=unreal.Vector(*[tack[i] - at[i] for i in range(3)]),
                                            rotation=frame.rotation.rotator()))
    return looks


# ---- Assets ------------------------------------------------------------------------------------------------

def update_definition(hull, rig, looks, capstan):
    d = data_asset('/Game/Elitewake/Ships', 'DA_Ship_Brigantine', unreal.EWShipDefinition)
    mounts = [mount('Helm', T.HELM, (-1250.0, 0.0, QD_Z + 50))]
    mounts += [mount(mid, T.SAIL, at, sail=size, look=looks[mid]) for mid, (at, size) in SAIL_MOUNTS.items()]
    for side, name in ((-1, 'Port'), (1, 'Starboard')):
        for k, x in enumerate(PORT_XS):
            y = side * (HULL.inner_y(x, (PORT[1] + PORT[2]) / 2) - 65)
            mounts.append(mount(f'{name}Cannon{k + 1}', T.CANNON, (x, y, FLOOR_Z + 40), yaw=side * 90))
    values = {
        'ship_id': 'Brigantine', 'display_name': 'Brigantine',
        'hull_mesh': hull, 'rigging_mesh': rig, 'hull_mesh_transform': unreal.Transform(),
        'hull_extent': unreal.Vector(HULL.bow_x - 10, HULL.beam + 5, -HULL.keel_z + 5),
        'hull_draft': -HULL.keel_z, 'deck_height': DECK_Z, 'hold_floor_height': FLOOR_Z,
        'anchor_point': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z + 40),
        'capstan_mesh': capstan, 'capstan_location': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z),
        'cargo_hatch_point': unreal.Vector((HATCH[0] + HATCH[1]) / 2, 0, DECK_Z + 5),
        'boarding_points': [unreal.Vector(LADDER_X, side * (HULL.half_beam(LADDER_X) + 30), 60) for side in (-1, 1)],
        # Crew up to 25 (confirmed). Speed, turning and hold are tuning: bigger and slower to turn than the schooner.
        'crew_capacity': 25, 'top_speed': 750.0, 'turn_rate': 16.0, 'cargo_slots': 60, 'weight_capacity': 8000.0,
        'mounts': mounts,
    }
    for k, v in values.items():
        d.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(d)
    return d


def moor(definition):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    ship = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip) and a.get_editor_property('definition') == definition), None)
    if not ship:
        ship = actors.spawn_actor_from_class(unreal.EWShip, unreal.Vector(*MOORING))
        ship.set_editor_property('definition', definition)
    ship.set_actor_label('Brigantine')
    ship.set_actor_location(unreal.Vector(*MOORING), False, False)
    assert level.save_current_level()


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = make_timber_material()
    sails = fittings.cloth_materials()
    b = hull_mesh()
    hull = write_static_mesh(b, f'{FOLDER}/SM_BrigantineHull_v1', [timber], UV_TILE)
    rig = write_static_mesh(rigging(), f'{FOLDER}/SM_BrigantineRigging_v1', [timber], UV_TILE, collision=False)
    looks = sail_looks(timber, sails)
    large_sail_item()
    definition = update_definition(hull, rig, looks, capstan_head(timber))
    moor(definition)
    Path(unreal.Paths.project_saved_dir(), 'BrigantineResult.json').write_text(json.dumps(
        {'success': True, 'vertices': len(b.verts), 'triangles': len(b.tris), 'mounts': len(definition.get_editor_property('mounts'))}, indent=2))
    unreal.log('Brigantine built')


if __name__ == '__main__':
    main()
