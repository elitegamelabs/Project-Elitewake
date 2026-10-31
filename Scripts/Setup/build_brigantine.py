"""Build the brigantine's bare hull in Unreal (owner, October 18: ship proportions, captain's quarters and modular sail
hardpoints; ChatGPT's layout study Art/Reference/Ships/Hulls/Brigantine/LayoutSheet-v2.png; the look follows the design
sheet Art/Concepts/Boats/2026-10-18/Ship-Design-Sheet-v1.webp), its definition and its moorings. Safe to run again.
Run in the editor after build_ship_fittings.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

About 30 m long and 8.4 m in beam, wider and taller than the schooner (about 6 m from keel to rail against her 4.4 m).
A bare hull like every base hull: NO masts. Three empty sail hardpoints, a socket each, take the removable sail
assemblies (their own masts and yards, no flags): Large ones forward and amidships, a Medium one aft.

Aft, the captain's quarters fill the full width for 6.5 m, longer than the schooner's (owner, October 18), with the
ship's wheel standing INSIDE them: a berth across the stern, a table and a chest on a rug, lanterns, a door and two
windows (Codex's sealed panes) onto the main deck and glazed lights in her sides. Over them a raised deck with a
balustrade, reached by a staircase up each side against the bulwark, with fixed safety rails. The main deck is flush
to the bow as in the layout sheet (no forecastle). Under it a single gun deck carries six round gunports, three a
side, each with its sliding glass cover and its cannon place, with stairs through the main hatch, pillars, ribs and
beams, bulkheads with doorways into small holds fore and aft, stores and lanterns, and the surgeon's table aft-port.
Three railing hardpoints a side, a boarding ladder at the centre of her stern, a capstan and a bowsprit with its
bobstay. Her three flags fly from deck staffs: a jack at the bow and two on the raised aft deck. Sizes are tuning;
CLAUDE.md records the delegated choices.

Coordinates are the ship's own, in cm, with the waterline at Z 0 and the gun deck above the swell.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ship_fittings as fittings  # noqa: E402
from build_schooner import RAILING_LENGTH, data_asset, large_sail_item, mount, railing_mounts  # noqa: E402
from build_sloop_hull import capstan_head  # noqa: E402
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402
from ship_hull import Hull, tar_rope  # noqa: E402
from ship_gunports import cover_meshes, gunport  # noqa: E402
from ship_flags import ENSIGN_FLAG, MASTHEAD_FLAG, deck_staff, flag_mount  # noqa: E402
from ship_interior import Room, materials as interior_materials  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'  # ships and sea life live in the test map (owner, October 14)
MOORING = (7500.0, -4500.0, -65.0)   # south-east of the island, in deep water clear of the other ships
T = unreal.EWShipMountType

# Owner, October 17: six individually crafted permanent circular hull gunports, three a side, each with its own
# cannon, above the waterline.
PORT_XS = (-660.0, 0.0, 660.0)
PORT = (64.0, 115.0, 180.0)          # width, sill and head heights: a round port 64 cm across
# Three railing hardpoints a side (owner, October 17): on the raised aft deck and two on the main deck, clear of the
# sail sockets' pin rails and the quarters' stairs. (centre x, the deck they stand on.)
RAILINGS = ((-1120.0, 520.0), (-360.0, 300.0), (560.0, 300.0))
QUARTERDECK = (-850.0, 220.0)        # front x (the quarters are 6.5 m long), rise above the main deck
CABIN_WINDOWS = (-950.0, -1080.0, -1210.0)
CABIN_WINDOW = (40.0, 400.0, 450.0)  # width, sill and head heights
HULL = Hull(stern_x=-1500.0, bow_x=1500.0, beam=420.0, keel_z=-230.0,
            deck_z=300.0, floor_z=50.0,
            sheer_mid=400.0, sheer_rise=120.0, sheer_flat=200.0,
            beam_power=2.6, keel_flat=650.0, keel_power=2.3, full_mid=3.2, full_end=1.7, full_len=600.0,
            strakes=16, wales=(10, 13), tar_line=100.0,
            gunports=[(x, *PORT, 'round') for x in PORT_XS]
                     + [(x, RAILING_LENGTH, floor + 3, 2000.0, 'gap') for x, floor in RAILINGS]
                     + [(x, *CABIN_WINDOW) for x in CABIN_WINDOWS],
            quarterdeck=QUARTERDECK)
DECK_Z, FLOOR_Z = HULL.deck_z, HULL.floor_z
QD_Z = DECK_Z + QUARTERDECK[1]
UV_TILE = HULL.uv_tile
HATCH = (220.0, 520.0, 60.0)         # stairs down to the gun deck: aft x, forward x, half-width (clear of the main socket)
GRATING = (-180.0, 140.0, 110.0)     # centre x, length, width
LOWER_BULKHEADS = (-1080.0, 1080.0)  # the gun deck's ends, with doorways into small holds fore and aft
# The boarding ladder, centred on the stern above the rudder's head (owner, October 16: one ladder at the middle of
# the stern, on the centreline).
STERN_LADDER = HULL.stern_ladder_line(80.0)
CAPSTAN = (760.0, -150.0)
FRAMES = range(-1440, 1460, 60)
HELM_X = -1080.0                     # the wheel stands inside the captain's quarters (owner, October 18)

# Her three empty sail hardpoints (ChatGPT's layout: three sockets on the main deck): where each socket stands and
# the assembly a Large or Medium sail fits in it (see build_sloop_hull.ASSEMBLIES for the fields). Spaced so the
# yards, which lie fore and aft at zero trim, clear each other.
ASSEMBLIES = {
    'Foresail': dict(size='Large', x=1000.0, height=1750.0, yard=1450.0, head=840.0, foot=960.0, drop=820.0, belly=90.0, radius=22.0, top_radius=13.0),
    'Mainsail': dict(size='Large', x=90.0, height=1850.0, yard=1550.0, head=820.0, foot=940.0, drop=850.0, belly=90.0, radius=24.0, top_radius=14.0),
    'Aftsail': dict(size='Medium', x=-700.0, height=1500.0, yard=1200.0, head=600.0, foot=680.0, drop=600.0, belly=70.0, radius=18.0, top_radius=11.0),
}
PIN_RAILS = ('Foresail', 'Mainsail')   # the aft socket's sides are taken by the quarters' stairs
BOWSPRIT = ((1380.0, 0.0, HULL.sheer(1380.0) + 30), (2350.0, 0.0, 720.0))


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


def quarters(b):
    """The captain's quarters under the raised aft deck, with the wheel standing in them (owner, October 18): a berth
    across the stern, a table and a chest to either side of the wheel on a rug, clear room to step off the wheel, and
    lanterns. Returns its lanterns."""
    front, rise = QUARTERDECK
    HULL.raised_deck(b, front, rise, 1, (HULL.stern_x, front), beams=(-940.0, -1040.0, -1160.0, -1260.0, -1360.0),
                     side_lights=CABIN_WINDOWS, side_light=CABIN_WINDOW)
    HULL.stair_rails(b, front, rise, 1)
    room = Room(b, DECK_Z)
    room.bed(-1290.0, 0.0, yaw=90.0, length=180.0, width=90.0)
    room.rug(-1070.0, 0.0, length=200.0, width=150.0)
    room.table(-950.0, -230.0, length=80.0, width=56.0)
    room.chest(-955.0, 240.0, yaw=90.0)
    for x, y in ((-960.0, 160.0), (-960.0, -160.0), (-1220.0, 150.0), (-1220.0, -150.0)):
        room.lantern(x, y, QD_Z - HULL.deck_thick - 14)
    return room.lights


def gun_deck(b):
    """The gun deck under the main deck. Returns its lanterns."""
    h = HULL
    h.floor(b, FLOOR_Z, inset=110.0)
    beams = [x for x in range(-1360, 1380, 80) if not HATCH[0] - 20 < x < HATCH[1] + 20]
    h.beams(b, beams + [HATCH[0] - 8, HATCH[1] + 8], DECK_Z)
    h.ribs(b, FRAMES, FLOOR_Z, DECK_Z - h.deck_thick - 10)
    h.stairs(b, HATCH[0] + 5, HATCH[1] - 5, DECK_Z, FLOOR_Z, 13)
    for x in LOWER_BULKHEADS:
        h.bulkhead(b, x, FLOOR_Z, DECK_Z - h.deck_thick, openings=[(-50.0, 50.0, FLOOR_Z, FLOOR_Z + 200)])
    # Pillars under the beams (no mast steps: the masts belong to the sail assemblies).
    for x in (-330.0, 550.0):
        for y in (-140.0, 140.0):
            b.box((x, y, (FLOOR_Z + DECK_Z - 18) / 2), (20, 20, DECK_Z - 18 - FLOOR_Z))
            b.box((x, y, FLOOR_Z + 4), (32, 32, 8), iron=1.0)
    room = Room(b, FLOOR_Z)
    # The treatment station is aft-port on the first deck below the weather deck (visual prop only).
    room.surgeon_table(-1300.0, -90.0, yaw=90.0, length=130.0, width=70.0)
    # Stores in the forward hold, clear of its doorway.
    for y in (-110.0, 110.0):
        room.barrel(1180.0, y, height=90.0, radius=28.0)
    room.crate(1180.0, 0.0, size=60.0)
    room.chest(-1180.0, 110.0, yaw=90.0)
    for x, y in ((-700.0, 120.0), (-200.0, -120.0), (300.0, 120.0), (800.0, -120.0)):
        room.lantern(x, y, DECK_Z - h.deck_thick - 14)
    return room.lights


LIGHTS = []


def hull_mesh():
    h = HULL
    b = Builder()
    h.outer_shell(b)
    h.inner_shell(b)
    h.rail_and_keel(b, straps=(950, 1150, 1350), keel_size=(28.0, 22.0), post_size=(30.0, 32.0))
    h.deck(b, DECK_Z, [HATCH])
    lights = quarters(b)
    grating(b)
    lights += gun_deck(b)
    h.bulwark_posts(b, range(-1450, 1460, 100))
    h.gunport_frames(b)
    h.studs(b, FRAMES)
    h.stern_ladder(b, STERN_LADDER)
    h.capstan(b, *CAPSTAN, DECK_Z)
    # The three empty sail hardpoints: a socket each, with pin rails at the two clear of the stairs. No masts.
    for mount_id, a_ in ASSEMBLIES.items():
        h.sail_socket(b, a_['x'], 0.0, DECK_Z, radius=30.0)
        if mount_id in PIN_RAILS:
            h.pin_rail(b, a_['x'], length=140.0)
    flags(b)
    h.bowsprit(b, *BOWSPRIT, radius=(18.0, 11.0))
    h.rudder(b, -200.0, 60.0, 150.0, 110.0, 20.0)
    for side in (1, -1):
        h.cathead_and_anchor(b, 1300.0, side, 1.6)
    # Turned balusters with brass caps along her bulwarks, open over the railing hardpoints (the modular outer
    # railings), and a brass strip along each side.
    h.balustrade(b, HULL.stern_x + 50, HULL.bow_x - 90, skip=[(x - RAILING_LENGTH / 2, x + RAILING_LENGTH / 2) for x, _ in RAILINGS])
    h.brass_band(b)
    LIGHTS[:] = lights
    return b


def rigging():
    """The standing rigging a bare hull has: the bowsprit's bobstay down to the stem and a shroud to each side of the
    bow (the masts' own stays and shrouds belong to the sail assemblies), as tarred rope."""
    r = Builder()
    tip = BOWSPRIT[1]
    r.tube([tip, (HULL.bow_x - 10.0, 0.0, HULL.sheer(HULL.bow_x - 10) - 160.0)], 2.4, sides=6)
    for side in (-1, 1):
        r.tube([tip, (HULL.bow_x - 170.0, side * (HULL.half_beam(HULL.bow_x - 170) - 4), HULL.sheer(HULL.bow_x - 170) + 4)], 2.4, sides=6)
    return tar_rope(r)


# ---- Assets ------------------------------------------------------------------------------------------------

def flags(b):
    """Her three flags (owner, October 17: the brigantine has 3 flag positions; with no masts and no flags on sail
    assemblies they fly from deck staffs, DECIDED, delegated): a jack at the bow, the ensign at the stern on the raised
    aft deck to port, and a pennant across from it to starboard. Draws them into b; returns each flag's
    (belay, hoist, scale)."""
    return {'JackFlag': (*deck_staff(b, HULL.bow_x - 260, 110.0, DECK_Z, rake=30.0, height=360.0), MASTHEAD_FLAG),
            'EnsignFlag': (*deck_staff(b, -1400.0, -(HULL.half_beam(-1400.0) - 45), QD_Z), ENSIGN_FLAG),
            'PennantFlag': (*deck_staff(b, -1360.0, HULL.half_beam(-1360.0) - 45, QD_Z, height=380.0), MASTHEAD_FLAG)}


def update_definition(hull, rig, looks, capstan):
    d = data_asset('/Game/Elitewake/Ships', 'DA_Ship_Brigantine', unreal.EWShipDefinition)
    sizes = {'Large': unreal.EWSailSize.LARGE, 'Medium': unreal.EWSailSize.MEDIUM}
    mounts = [mount('Helm', T.HELM, (HELM_X, 0.0, DECK_Z + 50))]
    mounts += [mount(mid, T.SAIL, (a_['x'], 0.0, DECK_Z + 50), sail=sizes[a_['size']], look=looks[mid][:3], mast=looks[mid][3])
               for mid, a_ in ASSEMBLIES.items()]
    cover = cover_meshes(make_timber_material())['round'](PORT[0] + 8)
    for side, name in ((-1, 'Port'), (1, 'Starboard')):
        for k, x in enumerate(PORT_XS):
            y = side * (HULL.inner_y(x, (PORT[1] + PORT[2]) / 2) - 65)
            mounts.append(gunport(mount(f'{name}Cannon{k + 1}', T.CANNON, (x, y, FLOOR_Z + 40), yaw=side * 90), HULL, (x, *PORT), side, cover))
    mounts += railing_mounts(HULL, RAILINGS)
    mounts += [flag_mount(mid, belay, hoist, scale) for mid, (belay, hoist, scale) in flags(Builder()).items()]
    values = {
        'ship_id': 'Brigantine', 'display_name': 'Brigantine',
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
        # Crew up to 25 (confirmed). Speed, turning and hold are tuning: bigger and slower to turn than the schooner.
        'hull_health': 4000.0, 'crew_capacity': 25, 'top_speed': 12 * 51.4444, 'turn_rate': 16.0, 'cargo_slots': 60, 'weight_capacity': 8000.0,
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
    hull = write_static_mesh(b, f'{FOLDER}/SM_BrigantineHull_v1', interior_materials(timber), UV_TILE)
    rig = write_static_mesh(rigging(), f'{FOLDER}/SM_BrigantineRigging_v1', [timber], UV_TILE, collision=False)
    looks = fittings.sail_assembly_looks(ASSEMBLIES, DECK_Z, timber, sails, 'Brigantine')
    large_sail_item()
    definition = update_definition(hull, rig, looks, capstan_head(timber))
    moor(definition)
    Path(unreal.Paths.project_saved_dir(), 'BrigantineResult.json').write_text(json.dumps(
        {'success': True, 'vertices': len(b.verts), 'triangles': len(b.tris), 'lanterns': len(LIGHTS),
         'mounts': len(definition.get_editor_property('mounts'))}, indent=2))
    unreal.log('Brigantine built')


if __name__ == '__main__':
    main()
