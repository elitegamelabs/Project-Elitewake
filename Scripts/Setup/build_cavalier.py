"""Build the Cavalier, the capital-class ship (owner, November 7: Art/Reference/Ships/Hulls/Cavalier/cavalier.png; CLAUDE.md 4
and 7.1: roughly the brigantine's footprint, three traversable levels, the helm inside, 14 knots, a Large yard). Its hull, its
standing rigging and its definition (DA_Ship_Cavalier). Safe to run again; the map is not touched (no yard sells her yet; Play
checks spawn her with EW_PLAY_SHIPS=Cavalier). Run in the editor after build_ship_fittings.py, outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"
EW_QUIT_WHEN_DONE=1 closes the editor at the end.

From the owner's sheet: about 32 m long and 9 m in beam, taller than the brigantine, three masts and a long bowsprit.
  - UPPER DECK: a stern cabin across her full width under a raised aft deck, with glazed windows forward and in her sides and
    the ship's wheel standing inside it; a bow chaser cannon on the open deck forward; a hatch with stairs down amidships, a
    grating, a capstan, three empty sail hardpoints (fore, main, mizzen: removable sail assemblies, no masts on the hull),
    railing hardpoints a side, deck-staff flags.
  - INTERNAL DECK 1, the gun deck: five cannons a side behind square gunports with sliding covers; the surgeon's cabin forward
    (his bed with a curtain, shelves, the treatment table); the chart room aft (the chart table, a chest, barrels); lanterns.
  - INTERNAL DECK 2, the lower deck: bunks down both sides, barrels, crates and coiled rope amidships, storerooms fore and aft.
    DECIDED (November 7): reached by a steep companion stair, not a ladder (CLAUDE.md 4 says "by ladder"), because the ship's
    climbing works for the boarding ladder over her stern only; a stair is walkable today.
A boarding ladder at the centre of her stern. Sizes, crew, hold and handling are tuning.

Coordinates are the ship's own, in cm, with the waterline at Z 0 and every floor above the swell. The stairs climb toward
the stern (Hull.stairs): their feet are at the hatches' forward ends; nothing hangs or stands over them.
"""
import json
import os
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ship_fittings as fittings  # noqa: E402
from build_schooner import RAILING_LENGTH, data_asset, large_sail_item, mount, railing_mounts  # noqa: E402
from build_sloop_hull import capstan_head  # noqa: E402
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402
from ship_hull import Hull, tar_rope  # noqa: E402
from ship_gunports import glass_material, gunport, square_cover  # noqa: E402
from ship_flags import ENSIGN_FLAG, MASTHEAD_FLAG, deck_staff, flag_mount  # noqa: E402
from ship_interior import Room, materials as interior_materials  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
T = unreal.EWShipMountType

LOWER_Z, GUN_Z, DECK_Z = 40.0, 285.0, 530.0    # the lower deck, the gun deck and the upper deck (tops of their floors)
PORT_XS = (-900.0, -450.0, 0.0, 450.0, 900.0)   # five square gunports a side on the gun deck (the owner's sheet)
PORT = (72.0, GUN_Z + 62.0, GUN_Z + 132.0)      # width, sill and head heights
RAILINGS = ((-560.0, DECK_Z), (620.0, DECK_Z))  # railing hardpoints a side on the upper deck: (centre x, deck)
QUARTERDECK = (-1000.0, 240.0)                  # the stern cabin: its front x and the raised deck's rise over the upper deck
CABIN_WINDOWS = (-1130.0, -1290.0, -1450.0)
CABIN_WINDOW = (44.0, DECK_Z + 100.0, DECK_Z + 155.0)
HULL = Hull(stern_x=-1600.0, bow_x=1600.0, beam=450.0, keel_z=-330.0,
            deck_z=DECK_Z, floor_z=LOWER_Z,
            sheer_mid=DECK_Z + 100.0, sheer_rise=170.0, sheer_flat=320.0,
            beam_power=2.6, keel_flat=700.0, keel_power=2.3, full_mid=3.3, full_end=1.7, full_len=650.0,
            strakes=22, wales=(14, 18), tar_line=230.0,     # dark lower hull up to under the gunports, as on the sheet
            gunports=[(x, *PORT) for x in PORT_XS]
                     + [(x, RAILING_LENGTH, floor + 3, 2000.0, 'gap') for x, floor in RAILINGS]
                     + [(x, *CABIN_WINDOW) for x in CABIN_WINDOWS],
            quarterdeck=QUARTERDECK)
QD_Z = DECK_Z + QUARTERDECK[1]
UV_TILE = HULL.uv_tile
HATCH_UPPER = (180.0, 520.0, 60.0)    # stairs from the upper deck to the gun deck: aft x, forward x, half-width
HATCH_GUN = (-520.0, -200.0, 60.0)    # stairs from the gun deck to the lower deck
GRATING = (-260.0, 160.0, 120.0)      # on the upper deck: centre x, length, width
GUN_BULKHEADS = (-1130.0, 1110.0)     # the chart room aft and the surgeon's cabin forward, off the gun deck
LOWER_BULKHEADS = (-1180.0, 1150.0)   # storerooms fore and aft on the lower deck
STERN_LADDER = HULL.stern_ladder_line(80.0)
CAPSTAN = (880.0, -170.0)
FRAMES = range(-1540, 1560, 60)
HELM_X = -1250.0                      # the wheel inside the stern cabin
CHASER = (1330.0, 0.0)                # the bow chaser on the open upper deck, facing forward

# Her three empty sail hardpoints (fore, main, mizzen): the assemblies they take (see build_sloop_hull.ASSEMBLIES).
ASSEMBLIES = {
    'Foresail': dict(size='Large', x=1080.0, height=2050.0, yard=1700.0, head=900.0, foot=1040.0, drop=900.0, belly=95.0, radius=24.0, top_radius=14.0),
    'Mainsail': dict(size='Large', x=120.0, height=2250.0, yard=1880.0, head=920.0, foot=1060.0, drop=960.0, belly=95.0, radius=27.0, top_radius=15.0),
    'Mizzensail': dict(size='Medium', x=-760.0, height=1750.0, yard=1420.0, head=660.0, foot=760.0, drop=680.0, belly=75.0, radius=20.0, top_radius=12.0),
}
PIN_RAILS = ('Foresail', 'Mainsail', 'Mizzensail')
BOWSPRIT = ((1480.0, 0.0, HULL.sheer(1480.0) + 30), (2650.0, 0.0, DECK_Z + 480.0))
LIGHTS = []


def grating(b):
    x, length, width = GRATING
    for y in (-width / 2, width / 2):
        b.box((x, y, DECK_Z + 5), (length + 10, 10, 10))
    for dx in (-length / 2, length / 2):
        b.box((x + dx, 0.0, DECK_Z + 5), (10, width, 10))
    for k in range(1, 6):
        b.box((x - length / 2 + length * k / 6, 0.0, DECK_Z + 5), (5, width, 8))


def stern_cabin(b):
    """The stern cabin under the raised aft deck, the ship's wheel standing in it, and its furniture. Returns its lanterns."""
    front, rise = QUARTERDECK
    HULL.raised_deck(b, front, rise, 1, (HULL.stern_x, front), beams=(-1100.0, -1220.0, -1340.0, -1460.0),
                     side_lights=CABIN_WINDOWS, side_light=CABIN_WINDOW)
    HULL.stair_rails(b, front, rise, 1)
    room = Room(b, DECK_Z)
    room.bed(-1500.0, 0.0, yaw=90.0, length=190.0, width=95.0)
    room.rug(-1250.0, 0.0, length=220.0, width=170.0)
    room.table(-1100.0, -260.0, length=90.0, width=60.0)
    room.chest(-1110.0, 270.0, yaw=90.0)
    for x, y in ((-1120.0, 170.0), (-1120.0, -170.0), (-1420.0, 170.0), (-1420.0, -170.0)):
        room.lantern(x, y, QD_Z - HULL.deck_thick - 14)
    return room.lights


def gun_deck(b):
    """Internal deck 1: the gun deck, with the surgeon's cabin forward and the chart room aft. Returns its lanterns."""
    h = HULL
    h.deck(b, GUN_Z, [HATCH_GUN], tone_seed=11)
    beams = [x for x in range(-1500, 1500, 80) if not HATCH_UPPER[0] - 20 < x < HATCH_UPPER[1] + 20]
    h.beams(b, beams + [HATCH_UPPER[0] - 8, HATCH_UPPER[1] + 8], DECK_Z)
    h.ribs(b, FRAMES, GUN_Z, DECK_Z - h.deck_thick - 10)
    h.stairs(b, HATCH_UPPER[0] + 5, HATCH_UPPER[1] - 5, DECK_Z, GUN_Z, 13)
    for x in GUN_BULKHEADS:
        h.bulkhead(b, x, GUN_Z, DECK_Z - h.deck_thick, openings=[(-55.0, 55.0, GUN_Z, GUN_Z + 205)])
    for x in (-420.0, 640.0):
        for y in (-150.0, 150.0):
            b.box((x, y, (GUN_Z + DECK_Z - 18) / 2), (20, 20, DECK_Z - 18 - GUN_Z))
    room = Room(b, GUN_Z)
    # The surgeon's cabin forward: his bed behind a curtain, shelves of jars, the treatment table (a visual prop).
    room.bed(1270.0, 150.0, yaw=0.0, length=180.0, width=80.0)
    b.box((1200.0, 60.0, GUN_Z + 100), (90, 4, 190))                 # the curtain beside the bed (a placeholder panel)
    room.shelf(1300.0, -230.0, yaw=0.0, length=140.0, height=160.0)
    room.surgeon_table(1200.0, -80.0, yaw=0.0, length=130.0, width=70.0)
    # The chart room aft: the chart table, a chest and the purser's barrels.
    room.table(-1280.0, 0.0, length=120.0, width=80.0)
    room.chest(-1400.0, 200.0, yaw=90.0)
    for y in (-200.0, -120.0):
        room.barrel(-1420.0, y, height=90.0, radius=28.0)
    # Shot and powder by the guns.
    for x in (-760.0, 0.0, 760.0):          # beside the guns, clear of both stairs
        room.crate(x, 200.0, size=50.0)
    for x, y in ((-900.0, 140.0), (-300.0, -140.0), (300.0, 140.0), (900.0, -140.0), (1250.0, 0.0), (-1300.0, 160.0)):
        room.lantern(x, y, DECK_Z - h.deck_thick - 14)
    return room.lights


def lower_deck(b):
    """Internal deck 2: the lower deck, with bunks down both sides and stores amidships. Returns its lanterns."""
    h = HULL
    h.floor(b, LOWER_Z, inset=120.0)
    beams = [x for x in range(-1460, 1460, 80) if not HATCH_GUN[0] - 20 < x < HATCH_GUN[1] + 20]
    h.beams(b, beams + [HATCH_GUN[0] - 8, HATCH_GUN[1] + 8], GUN_Z)
    h.ribs(b, FRAMES, LOWER_Z, GUN_Z - h.deck_thick - 10)
    h.stairs(b, HATCH_GUN[0] + 5, HATCH_GUN[1] - 5, GUN_Z, LOWER_Z, 13)
    for x in LOWER_BULKHEADS:
        h.bulkhead(b, x, LOWER_Z, GUN_Z - h.deck_thick, openings=[(-55.0, 55.0, LOWER_Z, LOWER_Z + 205)])
    room = Room(b, LOWER_Z)
    # Bunks down both sides, in pairs, clear of the stair.
    for x in (-1000.0, -780.0, 200.0, 420.0, 760.0, 980.0):
        for y in (-1, 1):
            room.bed(x, y * (h.inner_y(x, LOWER_Z + 60) - 60), yaw=0.0, length=190.0, width=80.0)
    # Stores amidships and in the storerooms.
    for x, y in ((-60.0, -60.0), (-60.0, 60.0), (40.0, 0.0)):
        room.barrel(x, y, height=95.0, radius=30.0)
    for x, y in ((560.0, 0.0), (620.0, 70.0)):
        room.crate(x, y, size=62.0)
    for k, y in enumerate((-90.0, 0.0, 90.0)):
        room.barrel(1250.0, y, height=90.0, radius=28.0)
        room.crate(-1300.0, y, size=58.0, yaw=15.0 * k)
    for x in (-160.0, 500.0):          # coiled rope (a low drum of tarred line)
        b.cylinder((x, -170.0, LOWER_Z), 38.0, 24.0, sides=14)
    for x, y in ((-900.0, 150.0), (-300.0, 150.0), (350.0, -150.0), (900.0, -150.0)):   # off the centreline, clear of heads on the stair
        room.lantern(x, y, GUN_Z - h.deck_thick - 14)
    return room.lights


def flags(b):
    """Her flags from deck staffs: a jack at the bow and the ensign and a pennant on the raised aft deck."""
    return {'JackFlag': (*deck_staff(b, HULL.bow_x - 300, 120.0, DECK_Z, rake=30.0, height=380.0), MASTHEAD_FLAG),
            'EnsignFlag': (*deck_staff(b, -1500.0, -(HULL.half_beam(-1500.0) - 45), QD_Z), ENSIGN_FLAG),
            'PennantFlag': (*deck_staff(b, -1460.0, HULL.half_beam(-1460.0) - 45, QD_Z, height=400.0), MASTHEAD_FLAG)}


def hull_mesh():
    h = HULL
    b = Builder()
    h.outer_shell(b)
    h.inner_shell(b)
    h.rail_and_keel(b, straps=(1050, 1250, 1450), keel_size=(32.0, 24.0), post_size=(34.0, 36.0))
    h.deck(b, DECK_Z, [HATCH_UPPER])
    lights = stern_cabin(b)
    grating(b)
    lights += gun_deck(b)
    lights += lower_deck(b)
    h.bulwark_posts(b, range(-1550, 1560, 100))
    h.gunport_frames(b)
    h.studs(b, FRAMES)
    h.stern_ladder(b, STERN_LADDER)
    h.capstan(b, *CAPSTAN, DECK_Z)
    for mount_id, a_ in ASSEMBLIES.items():
        h.sail_socket(b, a_['x'], 0.0, DECK_Z, radius=32.0)
        if mount_id in PIN_RAILS:
            h.pin_rail(b, a_['x'], length=150.0)
    flags(b)
    h.bowsprit(b, *BOWSPRIT, radius=(20.0, 12.0))
    h.rudder(b, -260.0, 60.0, 170.0, 120.0, 22.0)
    for side in (1, -1):
        h.cathead_and_anchor(b, 1400.0, side, 1.8)
    h.balustrade(b, HULL.stern_x + 50, HULL.bow_x - 90, skip=[(x - RAILING_LENGTH / 2, x + RAILING_LENGTH / 2) for x, _ in RAILINGS])
    h.brass_band(b)
    LIGHTS[:] = lights
    return b


def rigging():
    """The standing rigging of the bare hull: the bowsprit's bobstay and a shroud each side of the bow."""
    r = Builder()
    tip = BOWSPRIT[1]
    r.tube([tip, (HULL.bow_x - 10.0, 0.0, HULL.sheer(HULL.bow_x - 10) - 180.0)], 2.6, sides=6)
    for side in (-1, 1):
        r.tube([tip, (HULL.bow_x - 190.0, side * (HULL.half_beam(HULL.bow_x - 190) - 4), HULL.sheer(HULL.bow_x - 190) + 4)], 2.6, sides=6)
    return tar_rope(r)


def update_definition(hull, rig, looks, capstan):
    d = data_asset('/Game/Elitewake/Ships', 'DA_Ship_Cavalier', unreal.EWShipDefinition)
    sizes = {'Large': unreal.EWSailSize.LARGE, 'Medium': unreal.EWSailSize.MEDIUM}
    mounts = [mount('Helm', T.HELM, (HELM_X, 0.0, DECK_Z + 50))]
    mounts += [mount(mid, T.SAIL, (a_['x'], 0.0, DECK_Z + 50), sail=sizes[a_['size']], look=looks[mid][:3], mast=looks[mid][3])
               for mid, a_ in ASSEMBLIES.items()]
    # Her own cover mesh (the shared SM_GunportCoverSquare_v1 is the schooner's, at her port size).
    cover = write_static_mesh(square_cover(PORT[0] + 8, PORT[2] - PORT[1] + 8), f'{FOLDER}/SM_CavalierGunportCover_v1',
                              [glass_material(), make_timber_material()], 60.0)
    for side, name in ((-1, 'Port'), (1, 'Starboard')):
        for k, x in enumerate(PORT_XS):
            y = side * (HULL.inner_y(x, (PORT[1] + PORT[2]) / 2) - 65)
            mounts.append(gunport(mount(f'{name}Cannon{k + 1}', T.CANNON, (x, y, GUN_Z + 40), yaw=side * 90), HULL, (x, *PORT), side, cover))
    mounts.append(mount('BowChaser', T.CANNON, (CHASER[0], CHASER[1], DECK_Z + 40), yaw=0.0))
    mounts += railing_mounts(HULL, RAILINGS)
    mounts += [flag_mount(mid, belay, hoist, scale) for mid, (belay, hoist, scale) in flags(Builder()).items()]
    values = {
        'ship_id': 'Cavalier', 'display_name': 'Cavalier',
        'hull_mesh': hull, 'rigging_mesh': rig, 'hull_mesh_transform': unreal.Transform(),
        'hull_extent': unreal.Vector(HULL.bow_x - 10, HULL.beam + 5, -HULL.keel_z + 5),
        'hull_draft': -HULL.keel_z, 'deck_height': DECK_Z, 'hold_floor_height': LOWER_Z,
        'anchor_point': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z + 40),
        'capstan_mesh': capstan, 'capstan_location': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z),
        'cargo_hatch_point': unreal.Vector((HATCH_UPPER[0] + HATCH_UPPER[1]) / 2, 0, DECK_Z + 5),
        'boarding_points': [unreal.Vector(STERN_LADDER[0][0] - 18, 0, STERN_LADDER[0][2])],
        'ladder_tops': [unreal.Vector(STERN_LADDER[1][0] - 18, 0, STERN_LADDER[1][2])],
        'lantern_lights': [unreal.Vector(*p) for p in LIGHTS],
        # The capital class (CLAUDE.md 7.1): 14 knots; crew, hull, hold and turning are tuning.
        'hull_health': 5500.0, 'crew_capacity': 35, 'top_speed': 14 * 51.4444, 'turn_rate': 13.0, 'cargo_slots': 80, 'weight_capacity': 11000.0,
        'mounts': mounts,
    }
    for k, v in values.items():
        d.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(d)
    return d


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = make_timber_material()
    sails = fittings.cloth_materials()
    b = hull_mesh()
    hull = write_static_mesh(b, f'{FOLDER}/SM_CavalierHull_v1', interior_materials(timber), UV_TILE)
    rig = write_static_mesh(rigging(), f'{FOLDER}/SM_CavalierRigging_v1', [timber], UV_TILE, collision=False)
    looks = fittings.sail_assembly_looks(ASSEMBLIES, DECK_Z, timber, sails, 'Cavalier')
    large_sail_item()
    definition = update_definition(hull, rig, looks, capstan_head(timber))
    mast_top = max(a_['height'] for a_ in ASSEMBLIES.values()) + DECK_Z
    Path(unreal.Paths.project_saved_dir(), 'CavalierResult.json').write_text(json.dumps(
        {'success': True, 'vertices': len(b.verts), 'triangles': len(b.tris), 'lanterns': len(LIGHTS),
         'mounts': len(definition.get_editor_property('mounts')),
         'length_m': (HULL.bow_x - HULL.stern_x) / 100, 'bowsprit_tip_m': BOWSPRIT[1][0] / 100, 'beam_m': 2 * HULL.beam / 100,
         'draft_m': -HULL.keel_z / 100, 'mast_top_above_water_m': mast_top / 100}, indent=2))
    unreal.log('Cavalier built')


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
