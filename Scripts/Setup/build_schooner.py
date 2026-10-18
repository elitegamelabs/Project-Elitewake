"""Build the schooner from the owner's art (Art/Concepts/Boats/2026-10-11/Schooner-*): its hull, standing rigging,
the look of each sail on its rig, its definition, and moor it off the coastal dock. Safe to run again.
Run in the editor after build_ship_fittings.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

About 22 m long and 6.6 m in beam, half again the sloop's length. Like the sloop it is double-ended, the stern
rising to a post as the bow does. A raised aft deck carries the helm and the mizzen, with stairs up each side and
a breast rail; under it is the captain's cabin, entered by a doorway from the main deck and lit by windows in the
hull sides and its front, and by a skylight grating in the deck above. The main deck has a hatch with stairs down to a lower deck under it: twelve gunports, six a side, a
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
from build_sloop_hull import capstan_head  # noqa: E402
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402
from ship_hull import Hull, tar_rope  # noqa: E402
from ship_gunports import cover_meshes, gunport  # noqa: E402
from ship_flags import ENSIGN_FLAG, MASTHEAD_FLAG, ensign_staff, flag_mount, masthead_staff  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
DEFINITION = '/Game/Elitewake/Ships/DA_Ship_Schooner'
ITEMS = '/Game/Elitewake/Items/Testing'
MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'  # ships and sea life live in the test map (owner, October 14)
MOORING = (6400.0, -1500.0, -65.0)   # south of the dock, in deep water and clear of the swimming lane along Y 0
T = unreal.EWShipMountType

PORT_XS = (-480.0, -280.0, -80.0, 120.0, 320.0, 520.0)
PORT = (56.0, 105.0, 160.0)          # width, sill and head heights
QUARTERDECK = (-560.0, 220.0)        # front x, rise above the main deck: standing room in the cabin under it
# Railing hardpoints (owner, October 17: the schooner has four, two a side): (centre x, the deck they stand on), on the
# main deck clear of the shrouds' channels and the quarterdeck's step. Her lower-deck gunports stay.
RAILINGS = ((-330.0, 300.0), (230.0, 300.0))
RAILING_LENGTH = 330.0               # the opening in the bulwark a railing module fills (build_railings.LENGTH)
RAILING_HEIGHT = 66.0                # the module's built height (build_railings.HEIGHT); scaled to each bulwark
# The captain's cabin under the raised aft deck: lights (windows) in the hull sides, a doorway and two windows in
# its front, a skylight grating in the deck above, and beams overhead clear of the skylight.
CABIN_WINDOWS = (-660.0, -770.0, -880.0)
CABIN_WINDOW = (40.0, 400.0, 450.0)  # width, sill and head heights
CABIN_DOOR = (90.0, 205.0)           # width, height
SKYLIGHT = (-715.0, -645.0, 30.0)    # aft x, forward x, half-width
CABIN_BEAMS = (-620.0, -740.0, -860.0, -960.0)
HULL = Hull(stern_x=-1100.0, bow_x=1100.0, beam=330.0, keel_z=-170.0,
            deck_z=300.0, floor_z=40.0,
            sheer_mid=395.0, sheer_rise=130.0, sheer_flat=100.0,
            beam_power=2.1, keel_flat=450.0, keel_power=2.2, full_mid=2.9, full_end=1.5, full_len=350.0,
            strakes=14, wales=(9, 12), tar_line=95.0,
            gunports=[(x, PORT[0], PORT[1], PORT[2]) for x in PORT_XS]
                     + [(x, *CABIN_WINDOW) for x in CABIN_WINDOWS]
                     + [(x, RAILING_LENGTH, floor + 3, 2000.0, 'gap') for x, floor in RAILINGS],
            quarterdeck=QUARTERDECK)
DECK_Z, FLOOR_Z, QD_Z = HULL.deck_z, HULL.floor_z, HULL.deck_z + QUARTERDECK[1]
UV_TILE = HULL.uv_tile
HATCH = (100.0, 360.0, 55.0)         # stairs down to the lower deck: aft x, forward x, half-width
GRATING = (-330.0, 130.0, 100.0)     # centre x, length, width
LOWER_BULKHEAD_X = -600.0
# The boarding ladder, centred on the stern above the rudder's head (owner, October 16: one ladder at the middle of
# the stern, on the centreline); it replaces the ladders on both sides.
STERN_LADDER = HULL.stern_ladder_line(80.0)
CAPSTAN = (780.0, -110.0)
FRAMES = range(-1040, 1060, 60)
# Shrouds for each mast, (x where each meets its channel); the foremast's are led aft, behind its topsail.
FORE_SHROUDS = (540.0, 500.0, 460.0)
MAIN_SHROUDS = (-20.0, -60.0, -100.0)
MIZZEN_SHROUDS = (-780.0, -830.0)

# Rig.
FORE_X, FORE_TOP = 560.0, 2150.0
MAIN_X, MAIN_TOP = -60.0, 2050.0
MIZZEN_X, MIZZEN_TOP = -800.0, 1700.0
YARD_Z = 1900.0                      # the fore topsail's yard
BOOM_Z = 760.0                       # main and mizzen booms, above heads on the raised aft deck
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

def quarterdeck(b):
    """The raised aft deck and, under it, the captain's cabin."""
    front, rise = QUARTERDECK
    HULL.raised_deck(b, front, rise, 1, (HULL.stern_x, front), beams=CABIN_BEAMS, skylight=SKYLIGHT, door=CABIN_DOOR,
                     side_lights=CABIN_WINDOWS, side_light=CABIN_WINDOW)


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
    HULL.bulkhead(b, LOWER_BULKHEAD_X, FLOOR_Z, DECK_Z - h.deck_thick, openings=[(-50.0, 50.0, FLOOR_Z, FLOOR_Z + 200)])
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
    h.stern_ladder(b, STERN_LADDER)
    h.capstan(b, *CAPSTAN, DECK_Z)
    h.mast(b, FORE_X, FORE_TOP, radius=19.0, top_radius=12.0)
    h.mast(b, MAIN_X, MAIN_TOP, radius=20.0, top_radius=12.0)
    h.mast(b, MIZZEN_X, MIZZEN_TOP, radius=16.0, top_radius=10.0)
    flags(b)
    h.bowsprit(b, *BOWSPRIT, radius=(14.0, 9.0))
    # Working detail: channels with deadeyes for each mast's shrouds, pin rails at the masts, the rudder on the
    # stern and an anchor catted at each bow.
    for xs in (FORE_SHROUDS, MAIN_SHROUDS, MIZZEN_SHROUDS):
        h.channels(b, xs)
    for x in (FORE_X, MAIN_X, MIZZEN_X):
        h.pin_rail(b, x)
    h.rudder(b, -140.0, 60.0, 110.0, 80.0, 16.0)
    for side in (1, -1):
        h.cathead_and_anchor(b, 880.0, side, 1.3)
    return b


def rigging():
    """Standing rigging as tarred rope: the three jib stays, a stay from the main to the fore masthead, and
    shrouds with ratlines down to their deadeyes."""
    r = Builder()
    for low, high in STAYS.values():
        r.tube([high, low], 2.0, sides=6)
    r.tube([(MAIN_X + 10, 0.0, MAIN_TOP - 10), (FORE_X - 10, 0.0, FORE_TOP - 30)], 2.0, sides=6)
    HULL.shrouds(r, FORE_X, FORE_TOP - 100, FORE_SHROUDS, radius=1.9, spread=13.0)
    HULL.shrouds(r, MAIN_X, MAIN_TOP - 90, MAIN_SHROUDS, radius=1.9, spread=13.0)
    HULL.shrouds(r, MIZZEN_X, MIZZEN_TOP - 70, MIZZEN_SHROUDS, radius=1.7, spread=11.0)
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
                                    ('MizzenSail', MIZZEN_X, QD_Z, dict(boom=300.0, throat=560.0, peak=(-290.0, 820.0), belly=34.0))):
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


def plain_railing():
    mesh = unreal.load_asset('/Game/Elitewake/World/Ships/SM_RailingPlain_v1')
    assert mesh, 'Run Scripts/Setup/build_railings.py first.'
    return mesh


def railing_mounts(hull, rails):
    """Railing hardpoints along both sides at `rails` ((x, deck z) each), every module scaled to its bulwark's
    height, and behind each the two cannon places a two-cannon railing opens (owner, October 17)."""
    out = []
    for side, name in ((-1, 'Port'), (1, 'Starboard')):
        for n, (x, floor) in enumerate(rails):
            rail = f'{name}Railing{n + 1}'
            m = unreal.EWShipMount()
            m.set_editor_property('mount_id', rail)
            m.set_editor_property('type', T.RAILING)
            tall = max(.8, (hull.sheer(x) - floor - 2) / RAILING_HEIGHT)
            m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(x, side * (hull.half_beam(x) - 6), floor),
                                                                rotation=unreal.Rotator(0, 0, side * 90), scale=unreal.Vector(1, 1, tall)))
            # A plain railing stands here until another module replaces it (owner, October 17).
            m.set_editor_property('empty_mesh', plain_railing())
            out.append(m)
            for k, dx in enumerate((80.0, -80.0)):
                c = mount(f'{name}Rail{n + 1}Cannon{k + 1}', T.CANNON, (x + dx, side * (hull.inner_y(x + dx, floor + 40) - 45), floor + 40), yaw=side * 90)
                c.set_editor_property('parent_mount', rail)
                c.set_editor_property('parent_slot', k + 1)
                out.append(c)
    return out


def flags(b):
    """Her three flags (not named by the owner; DECIDED, delegated: one at each of her fore and main mastheads and the
    ensign at the stern, to port of the boarding ladder; her mizzen flies none, so the count grows with the ship).
    Draws them into b; returns each flag's (belay, hoist, scale)."""
    x = HULL.stern_x + 80
    return {'ForeFlag': (*masthead_staff(b, FORE_X, FORE_TOP, DECK_Z, 19.0), MASTHEAD_FLAG),
            'MainFlag': (*masthead_staff(b, MAIN_X, MAIN_TOP, DECK_Z, 20.0), MASTHEAD_FLAG),
            'EnsignFlag': (*ensign_staff(b, x, -(HULL.half_beam(x) - 35), QD_Z), ENSIGN_FLAG)}


def update_definition(hull, rig, looks, capstan):
    d = data_asset('/Game/Elitewake/Ships', 'DA_Ship_Schooner', unreal.EWShipDefinition)
    sizes = {'ForeTopsail': unreal.EWSailSize.LARGE, 'Mainsail': unreal.EWSailSize.MEDIUM, 'MizzenSail': unreal.EWSailSize.MEDIUM,
             'FlyingJib': unreal.EWSailSize.SMALL, 'Jib': unreal.EWSailSize.SMALL, 'Staysail': unreal.EWSailSize.SMALL}
    mounts = [mount('Helm', T.HELM, (-900.0, 0.0, QD_Z + 50))]
    mounts += [mount(mid, T.SAIL, looks[mid][0], sail=sizes[mid], look=looks[mid][1:]) for mid in sizes]
    # Twelve cannon hardpoints at the lower deck's gunports, facing out, each port with its sliding glass cover.
    cover = cover_meshes(make_timber_material())['square'](PORT[0] + 10, PORT[2] - PORT[1] + 10)
    for side, name in ((-1, 'Port'), (1, 'Starboard')):
        for k, x in enumerate(PORT_XS):
            y = side * (HULL.inner_y(x, (PORT[1] + PORT[2]) / 2) - 60)
            mounts.append(gunport(mount(f'{name}Cannon{k + 1}', T.CANNON, (x, y, FLOOR_Z + 40), yaw=side * 90), HULL, (x, *PORT), side, cover))
    mounts += railing_mounts(HULL, RAILINGS)
    mounts += [flag_mount(mid, belay, hoist, scale) for mid, (belay, hoist, scale) in flags(Builder()).items()]
    values = {
        'ship_id': 'Schooner', 'display_name': 'Schooner',
        'hull_mesh': hull, 'rigging_mesh': rig, 'hull_mesh_transform': unreal.Transform(),
        'hull_extent': unreal.Vector(HULL.bow_x - 10, HULL.beam + 5, -HULL.keel_z + 5),
        'hull_draft': -HULL.keel_z, 'deck_height': DECK_Z, 'hold_floor_height': FLOOR_Z,
        'anchor_point': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z + 40),
        'capstan_mesh': capstan, 'capstan_location': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z),
        'cargo_hatch_point': unreal.Vector((HATCH[0] + HATCH[1]) / 2, 0, DECK_Z + 5),
        # The climber hangs just aft of the rungs: each point lies 18 cm out from the rung line.
        'boarding_points': [unreal.Vector(STERN_LADDER[0][0] - 18, 0, STERN_LADDER[0][2])],
        'ladder_tops': [unreal.Vector(STERN_LADDER[1][0] - 18, 0, STERN_LADDER[1][2])],
        # Crew: the twelve cannons' crews plus the player and the Surgeon. Speed, turning and hold are tuning.
        'hull_health': 2500.0, 'crew_capacity': 14, 'top_speed': 800.0, 'turn_rate': 22.0, 'cargo_slots': 40, 'weight_capacity': 4000.0,
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
    definition = update_definition(hull, rig, looks, capstan_head(timber))
    moor(definition, large_sail)
    Path(unreal.Paths.project_saved_dir(), 'SchoonerResult.json').write_text(json.dumps(
        {'success': True, 'vertices': len(b.verts), 'triangles': len(b.tris), 'mounts': len(definition.get_editor_property('mounts'))}, indent=2))
    unreal.log('Schooner built')


if __name__ == '__main__':
    main()
