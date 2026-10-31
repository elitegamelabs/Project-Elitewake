"""Build the schooner's bare hull in Unreal (owner, October 18: ship proportions, aft captain's quarters, modular sail
hardpoints; ChatGPT's layout study Art/Reference/Ships/Hulls/Schooner/LayoutSheet-v2.png; the look follows the design
sheet Art/Concepts/Boats/2026-10-18/Ship-Design-Sheet-v1.webp), its definition and its moorings. Safe to run again.
Run in the editor after build_ship_fittings.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

About 22 m long and 4.6 m in beam, the sloop's width but longer and taller (4.4 m from keel to rail against the sloop's
3.6 m). A bare hull like every base hull: NO masts. Two empty sail hardpoints, a socket each, take the removable sail
assemblies (their own masts and yards, no flags): a Large one forward and a Medium one aft of amidships.

Aft, the captain's quarters fill the full width for about an eighth of her length (2.5 m), with a door and two
windows onto the main deck and glazed lights in her sides, a bed across the stern, a table, stools and a chest on a
rug, under a lantern. Over them the raised aft deck carries the ship's wheel; a staircase climbs to it up each side
against the bulwark, with fixed safety railings along both stairs and round the deck (the modular outer railings are
separate). Under the main deck a lower deck has twelve square gunports, six a side, each with its sliding glass cover
and its cannon place, a hatch and stairs down, pillars, ribs and beams, a bulkhead with a doorway into a small aft
hold, and barrels, crates and a chest under three lanterns. Four railing hardpoints along the main deck, a boarding
ladder at the centre of her stern, a capstan and a bowsprit with its bobstay. Her two flags fly from a jackstaff at the
bow and an ensign staff on the raised aft deck. Sizes are tuning; CLAUDE.md holds the current rules.

Coordinates are the ship's own, in cm, with the waterline at Z 0 and the lower deck above the swell.
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
from ship_flags import ENSIGN_FLAG, MASTHEAD_FLAG, deck_staff, flag_mount  # noqa: E402
from ship_interior import Room, materials  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
DEFINITION = '/Game/Elitewake/Ships/DA_Ship_Schooner'
ITEMS = '/Game/Elitewake/Items/Testing'
MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'  # ships and sea life live in the test map (owner, October 14)
MOORING = (6400.0, -1500.0, -65.0)   # south of the dock, in deep water and clear of the swimming lane along Y 0
T = unreal.EWShipMountType

PORT_XS = (-480.0, -280.0, -80.0, 120.0, 320.0, 520.0)
PORT = (56.0, 85.0, 140.0)           # width, sill and head heights
QUARTERDECK = (-825.0, 210.0)        # front x (the quarters fill an eighth of her length, 2.75 m), rise above the main deck
# Railing hardpoints (owner, October 17: the schooner has four, two a side): (centre x, the deck they stand on), on the
# main deck clear of the sail sockets and the quarterdeck's stairs. Her lower-deck gunports stay.
RAILINGS = ((-300.0, 260.0), (230.0, 260.0))
RAILING_LENGTH = 330.0               # the opening in the bulwark a railing module fills (build_railings.LENGTH)
RAILING_HEIGHT = 66.0                # the module's built height (build_railings.HEIGHT); scaled to each bulwark
# The captain's quarters under the raised aft deck: lights (windows) in the hull sides, a doorway and two windows in
# its front, and beams overhead.
CABIN_WINDOWS = (-900.0, -980.0)
CABIN_WINDOW = (36.0, 355.0, 400.0)  # width, sill and head heights
CABIN_DOOR = (90.0, 190.0)           # width, height
CABIN_BEAMS = (-860.0, -940.0, -1020.0)
HULL = Hull(stern_x=-1100.0, bow_x=1100.0, beam=230.0, keel_z=-110.0,    # the sloop's width, longer and taller
            deck_z=260.0, floor_z=20.0,
            sheer_mid=330.0, sheer_rise=110.0, sheer_flat=100.0,
            beam_power=2.1, keel_flat=420.0, keel_power=2.2, full_mid=2.9, full_end=1.5, full_len=360.0,
            stern_power=4.0, stern_keel_power=4.5, stern_full_len=550.0,     # a broad, rounded stern
            strakes=14, wales=(9, 12), tar_line=150.0,
            gunports=[(x, PORT[0], PORT[1], PORT[2]) for x in PORT_XS]
                     + [(x, *CABIN_WINDOW) for x in CABIN_WINDOWS]
                     + [(x, RAILING_LENGTH, floor + 3, 2000.0, 'gap') for x, floor in RAILINGS],
            quarterdeck=QUARTERDECK)
DECK_Z, FLOOR_Z, QD_Z = HULL.deck_z, HULL.floor_z, HULL.deck_z + QUARTERDECK[1]
UV_TILE = HULL.uv_tile
HATCH = (100.0, 360.0, 55.0)         # stairs down to the lower deck: aft x, forward x, half-width
GRATING = (-330.0, 130.0, 100.0)     # centre x, length, width
LOWER_BULKHEAD_X = -620.0
# The boarding ladder, centred on the stern above the rudder's head (owner, October 16: one ladder at the middle of
# the stern, on the centreline); it replaces the ladders on both sides.
STERN_LADDER = HULL.stern_ladder_line(80.0)
CAPSTAN = (740.0, -90.0)
FRAMES = range(-1040, 1060, 60)
HELM_X = -900.0                      # the wheel stands on top of the captain's quarters (owner, October 18)

# Her two empty sail hardpoints (owner, October 18: ChatGPT's layout shows two): where each socket stands and the
# assembly a Large or Medium sail fits in it (see build_sloop_hull.ASSEMBLIES for the fields).
ASSEMBLIES = {
    'Foresail': dict(size='Large', x=620.0, height=1300.0, yard=1050.0, head=720.0, foot=800.0, drop=700.0, belly=80.0, radius=18.0, top_radius=11.0),
    'Mainsail': dict(size='Medium', x=-170.0, height=1150.0, yard=950.0, head=580.0, foot=660.0, drop=580.0, belly=70.0, radius=16.0, top_radius=10.0),
}
BOWSPRIT = ((1010.0, 0.0, HULL.sheer(1010.0) + 30), (1330.0, 0.0, 490.0))   # resting on the stem head


# ---- Hull --------------------------------------------------------------------------------------------------

def quarterdeck(b):
    """The raised aft deck and, under it, the captain's quarters, with fixed safety rails along both stairs."""
    front, rise = QUARTERDECK
    HULL.raised_deck(b, front, rise, 1, (HULL.stern_x, front), beams=CABIN_BEAMS, door=CABIN_DOOR,
                     side_lights=CABIN_WINDOWS, side_light=CABIN_WINDOW)
    HULL.stair_rails(b, front, rise, 1)


def quarters(b):
    """The captain's quarters, furnished (owner, October 18: the sheet shows a bed across the stern, a table and a
    chest on a rug): a berth across the stern, a table and a chest to the sides of a clear way in from the door.
    Returns its lanterns."""
    room = Room(b, DECK_Z)
    room.bed(-945.0, 0.0, yaw=90.0, length=170.0, width=90.0)
    room.rug(-860.0, 0.0, length=100.0, width=120.0)
    room.table(-870.0, -112.0, length=70.0, width=50.0)
    room.chest(-872.0, 118.0, yaw=90.0)
    for y in (-125.0, 125.0):
        room.lantern(-905.0, y, QD_Z - HULL.deck_thick - 14)
    return room.lights


def hold(b):
    """The lower deck's furnishings: crates, barrels and a chest in the forward hold and the aft hold, clear of the
    twelve cannon places and the walkway. Returns its lanterns."""
    room = Room(b, FLOOR_Z)
    for y in (-60.0, 60.0):
        room.crate(770.0, y, size=55.0)
    for y in (-95.0, 95.0):
        room.barrel(700.0, y, height=85.0, radius=26.0)
    room.chest(-720.0, 112.0, yaw=90.0)
    room.barrel(-740.0, -120.0, height=85.0, radius=26.0)
    room.crate(-800.0, 60.0, size=50.0)
    # Aft-port on the first deck below the weather deck; visual station only, not an interaction.
    room.surgeon_table(-900.0, -50.0, length=130.0, width=60.0)
    for x, y in ((-300.0, 105.0), (300.0, -105.0), (-760.0, -75.0)):
        room.lantern(x, y, DECK_Z - HULL.deck_thick - 14)
    return room.lights


LIGHTS = []


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
    beams = [x for x in range(-1080, 1120, 80) if not HATCH[0] - 20 < x < HATCH[1] + 20]
    h.beams(b, beams + [HATCH[0] - 8, HATCH[1] + 8], DECK_Z)
    h.ribs(b, FRAMES, FLOOR_Z, DECK_Z - h.deck_thick - 10)
    h.stairs(b, HATCH[0] + 5, HATCH[1] - 5, DECK_Z, FLOOR_Z, 13)
    # The aft bulkhead and its doorway into the aft hold.
    HULL.bulkhead(b, LOWER_BULKHEAD_X, FLOOR_Z, DECK_Z - h.deck_thick, openings=[(-50.0, 50.0, FLOOR_Z, FLOOR_Z + 200)])
    # Pillars under the beams (no mast steps: the masts belong to the sail assemblies).
    for x in (-320.0, 480.0):
        for y in (-110.0, 110.0):
            b.box((x, y, (FLOOR_Z + DECK_Z - 18) / 2), (18, 18, DECK_Z - 18 - FLOOR_Z))
            b.box((x, y, FLOOR_Z + 4), (30, 30, 8), iron=1.0)


def hull_mesh():
    h = HULL
    b = Builder()
    h.outer_shell(b)
    h.inner_shell(b)
    h.rail_and_keel(b, straps=(560, 700, 820), keel_size=(22.0, 18.0), post_size=(24.0, 26.0))
    h.deck(b, DECK_Z, [HATCH])
    quarterdeck(b)
    grating(b)
    lower_deck(b)
    h.bulwark_posts(b, range(-1050, 1060, 100))
    h.gunport_frames(b)
    h.studs(b, FRAMES)
    h.stern_ladder(b, STERN_LADDER)
    h.capstan(b, *CAPSTAN, DECK_Z)
    # The two empty sail hardpoints: a socket each, and a pin rail at each. No masts.
    for a_ in ASSEMBLIES.values():
        h.sail_socket(b, a_['x'], 0.0, DECK_Z)
        h.pin_rail(b, a_['x'])
    flags(b)
    h.bowsprit(b, *BOWSPRIT, radius=(14.0, 9.0))
    h.rudder(b, -100.0, 50.0, 100.0, 70.0, 14.0)
    for side in (1, -1):
        h.cathead_and_anchor(b, 880.0, side, 1.3)
    # Turned balusters with brass caps along her bulwarks and round the raised deck, open over the railing hardpoints
    # (the modular outer railings), and a brass strip along each side.
    h.balustrade(b, HULL.stern_x + 40, HULL.bow_x - 70, skip=[(x - RAILING_LENGTH / 2, x + RAILING_LENGTH / 2) for x, _ in RAILINGS])
    h.brass_band(b)
    LIGHTS[:] = quarters(b) + hold(b)
    return b


def rigging():
    """The standing rigging a bare hull has: the bowsprit's bobstay down to the stem and a shroud to each side of the
    bow (the masts' own stays and shrouds belong to the sail assemblies), as tarred rope."""
    r = Builder()
    tip = BOWSPRIT[1]
    r.tube([tip, (HULL.bow_x - 10.0, 0.0, HULL.sheer(HULL.bow_x - 10) - 110.0)], 2.0, sides=6)
    for side in (-1, 1):
        r.tube([tip, (HULL.bow_x - 130.0, side * (HULL.half_beam(HULL.bow_x - 130) - 4), HULL.sheer(HULL.bow_x - 130) + 4)], 2.0, sides=6)
    return tar_rope(r)


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


def mount(mount_id, kind, location, yaw=0.0, sail=unreal.EWSailSize.NONE, look=None, mast=None):
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
    if mast:
        m.set_editor_property('mast_mesh', mast)
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
    """Her two flags (DECIDED, delegated, October 18: the owner named the sloop, brigantine and Cavalier only; with no
    masts and no flags on sail assemblies they fly from deck staffs): a jackstaff at the bow and an ensign staff at the
    stern, on top of the raised aft deck, to port of the helm. Draws them into b; returns each flag's (belay, hoist, scale)."""
    x = HULL.stern_x + 55
    return {'JackFlag': (*deck_staff(b, HULL.bow_x - 190, 100.0, DECK_Z, rake=30.0, height=330.0), MASTHEAD_FLAG),
            'EnsignFlag': (*deck_staff(b, x, -(HULL.half_beam(x) - 30), QD_Z), ENSIGN_FLAG)}


def update_definition(hull, rig, looks, capstan):
    d = data_asset('/Game/Elitewake/Ships', 'DA_Ship_Schooner', unreal.EWShipDefinition)
    sizes = {'Large': unreal.EWSailSize.LARGE, 'Medium': unreal.EWSailSize.MEDIUM}
    mounts = [mount('Helm', T.HELM, (HELM_X, 0.0, QD_Z + 50))]
    mounts += [mount(mid, T.SAIL, (a_['x'], 0.0, DECK_Z + 50), sail=sizes[a_['size']], look=looks[mid][:3], mast=looks[mid][3])
               for mid, a_ in ASSEMBLIES.items()]
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
        'lantern_lights': [unreal.Vector(*p) for p in LIGHTS],
        # Crew: the twelve cannons' crews plus the player and the Surgeon. Speed, turning and hold are tuning.
        'hull_health': 2500.0, 'crew_capacity': 14, 'top_speed': 10 * 51.4444, 'turn_rate': 22.0, 'cargo_slots': 40, 'weight_capacity': 4000.0,
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
    hull = write_static_mesh(b, f'{FOLDER}/SM_SchoonerHull_v1', materials(timber), UV_TILE)
    rig = write_static_mesh(rigging(), f'{FOLDER}/SM_SchoonerRigging_v1', [timber], UV_TILE, collision=False)
    looks = fittings.sail_assembly_looks(ASSEMBLIES, DECK_Z, timber, sails, 'Schooner')
    large_sail = large_sail_item()
    definition = update_definition(hull, rig, looks, capstan_head(timber))
    moor(definition, large_sail)
    Path(unreal.Paths.project_saved_dir(), 'SchoonerResult.json').write_text(json.dumps(
        {'success': True, 'vertices': len(b.verts), 'triangles': len(b.tris), 'lanterns': len(LIGHTS),
         'mounts': len(definition.get_editor_property('mounts'))}, indent=2))
    unreal.log('Schooner built')


if __name__ == '__main__':
    main()
