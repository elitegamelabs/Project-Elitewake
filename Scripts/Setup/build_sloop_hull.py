"""Build the sloop's hull mesh in Unreal from the owner's ship design sheet (owner, October 18:
Art/Concepts/Boats/2026-10-18/Ship-Design-Sheet-v1.webp, its second column; it supersedes the October 11 concepts).
Safe to run again. Run in the editor, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

As the sheet draws her: two masts, the main forward of amidships with crosstrees and a shorter mizzen standing on a
raised stern deck, a long bowsprit, turned baluster rails with brass caps along her bulwarks, a brass strip along her
sides, dark tarred planking up to the wale and a broad rounded stern with the boarding ladder centred on it. Under the
stern deck, a lantern-lit cabin (a bed across the stern, a table and stools on a rug, a barrel and a sea chest), with
a door and two windows onto the main deck and glazed lights in her sides; below the main deck, a hold furnished with
benches, shelves, crates, barrels and a chest, lit by two lanterns. The helm stands on the stern deck. Details the
sheet does not settle (exact sizes, which furniture where) are DECIDED (delegated) and tuning.

A bare double-ended hull in weathered oak: the stern mirrors the bow, both sweeping up in a deep curve to a post.
Planked sides with seams and two wales, a tarred bottom, low bulwarks with a rail and posts, a railing hardpoint each side. A flat deck
has a cargo hatch with a coaming and stairs down into a cramped hold of ribs, floorboards, deck beams and a post.
A boarding ladder centred on the stern, a capstan near the bow, the mast and bowsprit are part of the hull, as are the
working details of a real vessel: channels with deadeyes and chainplates for the shrouds, a pin rail at the mast,
a rudder hung on the stern and an anchor catted at each bow. The standing rigging (shrouds with ratlines, and the
forestay) is a separate mesh drawn without collision. Sails, the helm and cannons
are fittings, built by build_ship_fittings.py, which reads the rig's positions from here.

Coordinates are the ship's own, in cm: X forward to the bow, Y to starboard, Z up, the waterline at Z 0. The hold
floor sits above the waves so the sea neither shows nor counts as swimmable inside. All sizes are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402
from ship_hull import Hull, tar_rope  # noqa: E402
from ship_flags import MASTHEAD_FLAG, flag_mount, masthead_staff  # noqa: E402
from ship_interior import RED_RUG, Room, materials  # noqa: E402

MESH = '/Game/Elitewake/World/Ships/SM_SloopHull_v2'
RIGGING = '/Game/Elitewake/World/Ships/SM_SloopRigging_v1'
DEFINITION = '/Game/Elitewake/Ships/DA_Ship_Sloop'
CAPSTAN_HEAD = '/Game/Elitewake/World/Ships/SM_CapstanHead_v1'
MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'  # ships and sea life live in the test map (owner, October 14)

# No hull gunports (owner, October 17): a railing hardpoint each side amidships instead, where the bulwark is open
# from the deck up for 3.3 m under the continuous top rail; a railing module (build_railings.py) fills the gap.
RAILING_X = 40.0
RAILING_GAP = (RAILING_X, 330.0, 253.0, 2000.0, 'gap')   # centre x, length, bottom z, top z, kind: cut out of the bulwark
QUARTERDECK = (-360.0, 200.0)     # the raised stern deck: its front x and its rise over the main deck
HULL = Hull(stern_x=-700.0, bow_x=700.0,     # about 14 m overall
            beam=250.0,                      # 5 m beam
            keel_z=-110.0, deck_z=250.0,
            floor_z=30.0,                    # hold floor top, above the swell
            sheer_mid=315.0, sheer_rise=115.0,
            stern_power=4.0,                 # a broad, rounded stern (the sheet), the bow still fine
            stern_keel_power=4.5, stern_full_len=480.0,   # her bottom stays low and full well aft
            tar_line=210.0,                  # dark tarred planking up to the wale (the sheet)
            gunports=[RAILING_GAP], quarterdeck=QUARTERDECK)
STERN_X, BOW_X, BEAM, KEEL_Z, DECK_Z, FLOOR_Z = HULL.stern_x, HULL.bow_x, HULL.beam, HULL.keel_z, HULL.deck_z, HULL.floor_z
QD_Z = DECK_Z + QUARTERDECK[1]
CABIN_WINDOWS = (-470.0, -600.0)
UV_TILE = HULL.uv_tile
HATCH = (-280.0, -40.0, 50.0)  # hatch opening: aft x, forward x, half-width
# The boarding ladder, centred on the stern above the rudder's head (owner, October 16: one ladder at the middle of
# the stern, on the centreline); it replaces the ladders on both sides.
STERN_LADDER = HULL.stern_ladder_line(60.0)
CAPSTAN = (480.0, -70.0)
# Rig (the sheet): a main mast with a gaff mainsail and a jib on the forestay out to the bowsprit, and a mizzen on the
# stern deck with a small gaff sail. Booms stand above the heads of crew on the stern deck.
MAST_X, MAST_TOP = 270.0, 1420.0
MIZZEN_X, MIZZEN_TOP = -420.0, 1180.0
BOOM_Z = 690.0
MIZZEN_BOOM_Z = QD_Z + 200.0
MAIN_GAFF = dict(boom=520.0, throat=470.0, peak=(-430.0, 690.0), belly=40.0)
MIZZEN_GAFF = dict(boom=230.0, throat=380.0, peak=(-220.0, 470.0), belly=28.0)
HELM_X = -575.0
STAY_TOP = (MAST_X + 8, 0.0, MAST_TOP - 30)
STAY_BOW = (1000.0, 0.0, 520.0)      # bowsprit end, where the forestay and the jib's tack meet
FRAMES = range(-640, 660, 60)
MOORING_YAW = 90.0     # bow toward open water
HULL_HEALTH = 1000.0   # tuning: ten round shot
MOORING_Y = 2350.0     # clear of the dock's end, lying along the heading
SHROUD_XS = (MAST_X - 30, MAST_X + 30)
MIZZEN_SHROUDS = (MIZZEN_X - 25, MIZZEN_X + 25)


def flags(b):
    """Her two flags (owner, October 17: the sloop has 2 flag positions), one at each masthead (DECIDED, delegated,
    October 18: with the sheet's masts, one flag per masthead gives the owner's counts exactly). Draws them into b;
    returns each flag's (belay, hoist, scale)."""
    return {'MastheadFlag': (*masthead_staff(b, MAST_X, MAST_TOP, DECK_Z, 15.0), MASTHEAD_FLAG),
            'MizzenFlag': (*masthead_staff(b, MIZZEN_X, MIZZEN_TOP, QD_Z, 12.0), MASTHEAD_FLAG)}


def crosstrees(b, x, top, span):
    """The trestle- and crosstrees near a masthead, spreading the upper shrouds (the sheet)."""
    z = top - 130
    b.box((x, 0.0, z), (34, 26, 10))
    b.box((x, 0.0, z + 8), (14, span, 8))


def cabin(b):
    """The cabin under the stern deck, as the sheet furnishes it. Returns its lanterns."""
    room = Room(b, DECK_Z)
    room.bed(-568.0, 0.0, yaw=90.0)
    room.rug(-485.0, 45.0, length=130.0, width=110.0, tone=RED_RUG)
    room.table(-480.0, 62.0, length=80.0, width=56.0)
    room.stool(-480.0, 0.0 - 5.0)
    room.stool(-420.0, 100.0)
    room.barrel(-395.0, -110.0, height=80.0, radius=26.0)
    room.chest(-500.0, -120.0)
    room.lantern(-520.0, 0.0, QD_Z - HULL.deck_thick - 14)
    return room.lights


def hold(b):
    """The hold below the main deck, furnished as the sheet's lower room. Returns its lanterns."""
    room = Room(b, FLOOR_Z)
    port = lambda x: -(HULL.inner_y(x, FLOOR_Z + 60) - 32)
    starboard = lambda x: HULL.inner_y(x, FLOOR_Z + 60) - 26
    room.bench(140.0, port(140.0), length=170.0)
    room.shelf(150.0, starboard(150.0), length=130.0, height=140.0)
    room.chest(-150.0, starboard(-150.0) - 10)
    for x, y in ((430.0, -60.0), (430.0, 60.0)):
        room.crate(x, y, size=60.0)
    room.crate(430.0, 0.0, size=45.0)
    for x, side in ((360.0, -1), (360.0, 1), (-380.0, 1)):
        room.barrel(x, side * (HULL.inner_y(x, FLOOR_Z + 40) - 40), height=85.0, radius=28.0)
    room.bench(-400.0, port(-400.0), length=140.0)
    for x in (-160.0, 380.0):
        room.lantern(x, 0.0, DECK_Z - HULL.deck_thick - 14)
    return room.lights


LIGHTS = []


def hull_mesh():
    h = HULL
    b = Builder()
    h.outer_shell(b)
    h.inner_shell(b)
    h.rail_and_keel(b)
    h.deck(b, DECK_Z, [HATCH])
    # The raised stern deck and the cabin under it: its door and windows onto the main deck, stairs up each side.
    h.raised_deck(b, QUARTERDECK[0], QUARTERDECK[1], 1, (STERN_X, QUARTERDECK[0]), beams=(-430.0, -520.0, -610.0),
                  door=(90.0, 180.0), side_lights=CABIN_WINDOWS, side_light=(36.0, DECK_Z + 95, DECK_Z + 140), steps=8)
    # A cramped hold: floorboards, deck beams framing the hatch with 2 m of headroom beneath, ribs, bulwark posts.
    h.floor(b, FLOOR_Z)
    h.beams(b, (-580, -490, -400, HATCH[0] - 8, HATCH[1] + 8, 60, 200, 340, 420, 500), DECK_Z)
    h.ribs(b, FRAMES, FLOOR_Z, DECK_Z - h.deck_thick - 10)
    h.bulwark_posts(b, range(-630, 640, 90))
    h.stairs(b, HATCH[0] + 5, HATCH[1] - 5, DECK_Z, FLOOR_Z, 10)  # down from the hatch; the mast stands forward of them
    h.studs(b, FRAMES)
    h.stern_ladder(b, STERN_LADDER)
    h.capstan(b, *CAPSTAN, DECK_Z)
    # The mast steps on the hold floor and rises through the deck; the bowsprit reaches out over the bow,
    # starting clear of heads on the foredeck.
    h.mast(b, MAST_X, MAST_TOP)
    h.mast(b, MIZZEN_X, MIZZEN_TOP, radius=12.0, top_radius=8.0)
    crosstrees(b, MAST_X, MAST_TOP, 150.0)
    crosstrees(b, MIZZEN_X, MIZZEN_TOP, 110.0)
    flags(b)
    h.bowsprit(b, (BOW_X - 70, 0.0, h.sheer(BOW_X - 70) + 30), STAY_BOW)
    # Working detail: the shrouds' channels and deadeyes, a pin rail at the mast, a rudder on the stern and an
    # anchor catted at each bow.
    h.channels(b, SHROUD_XS)
    h.channels(b, MIZZEN_SHROUDS)
    h.pin_rail(b, MAST_X)
    # Turned balusters with brass caps along her bulwarks, open over the railing hardpoints, and a brass strip
    # along each side (the sheet).
    h.balustrade(b, STERN_X + 40, BOW_X - 70, skip=[(RAILING_X - 175, RAILING_X + 175)])
    h.brass_band(b)
    LIGHTS[:] = cabin(b) + hold(b)
    h.rudder(b, -80.0, 40.0, 70.0, 50.0, 12.0)
    for side in (1, -1):
        h.cathead_and_anchor(b, 560.0, side, 1.0)
    return b


def rigging():
    """Standing rigging: a forestay to the bowsprit and two shrouds a side to their deadeyes, with ratlines,
    as tarred rope."""
    r = Builder()
    r.tube([STAY_TOP, STAY_BOW], 1.8, sides=6)
    r.tube([(MIZZEN_X + 8, 0.0, MIZZEN_TOP - 20), (MAST_X - 10, 0.0, MAST_TOP - 150)], 1.6, sides=6)   # mizzen stay
    HULL.shrouds(r, MAST_X, MAST_TOP - 90, SHROUD_XS)
    HULL.shrouds(r, MIZZEN_X, MIZZEN_TOP - 70, MIZZEN_SHROUDS, radius=1.5, spread=10.0)
    return tar_rope(r)


# ---- Assets ------------------------------------------------------------------------------------------------

def capstan_head(timber):
    """The capstan's turning head, the same on every hull with a capstan."""
    b = Builder()
    Hull.capstan_head(b)
    return write_static_mesh(b, CAPSTAN_HEAD, [timber], UV_TILE, collision=False)


PLAIN_RAILING = '/Game/Elitewake/World/Ships/SM_RailingPlain_v1'


def mount(mount_id, kind, location, yaw=0.0, sail=unreal.EWSailSize.NONE, parent='', slot=0, empty=None, look=None):
    m = unreal.EWShipMount()
    if look:
        mesh, furled, transform = look
        m.set_editor_property('fitted_mesh', mesh)
        m.set_editor_property('fitted_furled_mesh', furled)
        m.set_editor_property('fitted_mesh_transform', transform)
    m.set_editor_property('mount_id', mount_id)
    m.set_editor_property('type', kind)
    m.set_editor_property('sail_size', sail)
    m.set_editor_property('parent_mount', parent)
    m.set_editor_property('parent_slot', slot)
    if empty:
        mesh = unreal.load_asset(empty)
        assert mesh, 'Run Scripts/Setup/build_railings.py first.'
        m.set_editor_property('empty_mesh', mesh)
    m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(*location), rotation=unreal.Rotator(0, 0, yaw)))
    return m


def mizzen_look(timber):
    """The mizzen's small gaff sail, as this rig shapes it (a look on the mount, as the schooner's sails are)."""
    import build_ship_fittings as fittings   # it reads this rig, so it is imported only here
    sails = fittings.cloth_materials()
    write = lambda b, name: write_static_mesh(b, f'/Game/Elitewake/World/Ships/{name}', [timber, sails['Small']], UV_TILE, collision=False)
    at_z = QD_Z + 50
    return (write(fittings.gaff_sail(False, **MIZZEN_GAFF), 'SM_SloopMizzen_v1'), write(fittings.gaff_sail(True, **MIZZEN_GAFF), 'SM_SloopMizzenFurled_v1'),
            unreal.Transform(location=unreal.Vector(0, 0, MIZZEN_BOOM_Z - at_z)))


def update_definition(hull, rig, capstan, mizzen=None):
    definition = unreal.load_asset(DEFINITION)
    assert definition, DEFINITION
    deck_y = lambda x: HULL.inner_y(x, DECK_Z)
    t = unreal.EWShipMountType
    values = {
        'hull_mesh': hull,
        'rigging_mesh': rig,
        'hull_mesh_transform': unreal.Transform(),
        'hull_extent': unreal.Vector(BOW_X - 10, BEAM + 5, -KEEL_Z + 5),
        'hull_draft': -KEEL_Z,
        'deck_height': DECK_Z,
        'hull_health': HULL_HEALTH,
        'hold_floor_height': FLOOR_Z,
        'anchor_point': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z + 40),
        'capstan_mesh': capstan, 'capstan_location': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z),
        'cargo_hatch_point': unreal.Vector((HATCH[0] + HATCH[1]) / 2, 0, DECK_Z + 5),
        # The climber hangs just aft of the rungs: each point lies 18 cm out from the rung line.
        'boarding_points': [unreal.Vector(STERN_LADDER[0][0] - 18, 0, STERN_LADDER[0][2])],
        'ladder_tops': [unreal.Vector(STERN_LADDER[1][0] - 18, 0, STERN_LADDER[1][2])],
        'lantern_lights': [unreal.Vector(*p) for p in LIGHTS],
        'mounts': [
            mount('Helm', t.HELM, (HELM_X, 0, QD_Z + 50)),
            mount('Mainsail', t.SAIL, (MAST_X, 0, DECK_Z + 50), sail=unreal.EWSailSize.MEDIUM),
            mount('Headsail', t.SAIL, (600, 0, DECK_Z + 50), sail=unreal.EWSailSize.SMALL),
            mount('MizzenSail', t.SAIL, (MIZZEN_X, 0, QD_Z + 50), sail=unreal.EWSailSize.SMALL, look=mizzen),
            # The railing hardpoints, and behind each the two cannon places a two-cannon railing opens.
            # A plain railing stands at each until another module replaces it (owner, October 17).
            mount('PortRailing', t.RAILING, (RAILING_X, -(HULL.half_beam(RAILING_X) - 6), DECK_Z), yaw=-90, empty=PLAIN_RAILING),
            mount('StarboardRailing', t.RAILING, (RAILING_X, HULL.half_beam(RAILING_X) - 6, DECK_Z), yaw=90, empty=PLAIN_RAILING),
        ] + [mount(f'{name}Cannon{k + 1}', t.CANNON, (RAILING_X + dx, side * (deck_y(RAILING_X + dx) - 45), DECK_Z + 40),
                   yaw=side * 90, parent=f'{name}Railing', slot=k + 1)
             for name, side in (('Port', -1), ('Starboard', 1)) for k, dx in enumerate((80.0, -80.0))]
        + [flag_mount(mid, belay, hoist, scale) for mid, (belay, hoist, scale) in flags(Builder()).items()],
    }
    for k, v in values.items():
        definition.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
    return {k: str(v) for k, v in values.items() if k != 'mounts'}


def moor():
    """Moor the sloop clear of the dock with its bow to open water (+Y here: 60 m of deep water ahead; facing +X it
    met the islet's shallows within 10 m). It floats with its waterline (local Z 0) on the sea's surface."""
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert level.load_level(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    sloop = unreal.load_asset(DEFINITION)
    for ship in [a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip) and a.get_editor_property('definition') == sloop]:
        p = ship.get_actor_location()
        ship.set_actor_location_and_rotation(unreal.Vector(p.x, MOORING_Y, -65), unreal.Rotator(roll=0, pitch=0, yaw=MOORING_YAW), False, False)
        ship.set_actor_label('Sloop')
    assert level.save_current_level()


def main():
    lib = unreal.EWEditorVerificationLibrary
    assert not lib.get_play_worlds(), 'Stop Play first'
    b = hull_mesh()
    timber = make_timber_material()
    hull = write_static_mesh(b, MESH, materials(timber), UV_TILE)
    rig = write_static_mesh(rigging(), RIGGING, [timber], UV_TILE, collision=False)
    report = {'vertices': len(b.verts), 'triangles': len(b.tris), 'lanterns': len(LIGHTS),
              'definition': update_definition(hull, rig, capstan_head(timber), mizzen_look(timber))}
    moor()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'SloopHullResult.json').write_text(json.dumps(report, indent=2))
    unreal.log('Sloop hull built')


if __name__ == '__main__':
    main()
