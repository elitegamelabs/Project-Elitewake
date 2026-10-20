"""Build the sloop's bare hull in Unreal (owner, October 18: ship proportions and modular sail hardpoints; ChatGPT's
layout study Art/Reference/Ships/Hulls/Sloop/LayoutSheet-v1.png; the look follows the design sheet
Art/Concepts/Boats/2026-10-18/Ship-Design-Sheet-v1.webp). Safe to run again. Run in the editor, outside Play, with no
unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

A low, long hull in dark tarred planking under warm oak with brass, 13 m... about 14 m long and 4.6 m in beam, about
3.6 m from keel to rail (lowered from 4.25 m, owner: reduce the oversized sloop, keeping a hold you can stand in).
A bare hull: NO masts. She has two empty sail hardpoints, a socket each (an iron plate and a brass-banded collar) that
a removable sail assembly (its own mast, yard, cloth and rigging; no flags) stands in: a Medium one forward of
amidships and a Small one near the bow. A flat deck with a hatch and stairs down into the hold, no captain's quarters
and no raised deck (owner: the sloop has below-deck access but none); the helm stands on the open deck aft. Baluster
rails with brass caps run round her bulwarks, open over the two railing hardpoints (the modular outer rails); a boarding
ladder at the centre of her stern, a capstan and a long bowsprit at the bow, a rudder and an anchor each side.
Below, one furnished hold lit by two lanterns. Her two flags fly from a jackstaff at the bow and an ensign staff at
the stern. Sizes are tuning; Docs/OPEN_QUESTIONS records the delegated choices.

Coordinates are the ship's own, in cm: X forward to the bow, Y to starboard, Z up, the waterline at Z 0. The hold
floor sits above the waves so the sea neither shows nor counts as swimmable inside.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402
from ship_hull import Hull, tar_rope  # noqa: E402
from ship_flags import ENSIGN_FLAG, MASTHEAD_FLAG, deck_staff, flag_mount  # noqa: E402
from ship_interior import Room, materials  # noqa: E402

MESH = '/Game/Elitewake/World/Ships/SM_SloopHull_v2'
RIGGING = '/Game/Elitewake/World/Ships/SM_SloopRigging_v1'
DEFINITION = '/Game/Elitewake/Ships/DA_Ship_Sloop'
CAPSTAN_HEAD = '/Game/Elitewake/World/Ships/SM_CapstanHead_v1'
MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'  # ships and sea life live in the test map (owner, October 14)

# No hull gunports (owner, October 17): a railing hardpoint each side amidships instead, where the bulwark is open
# from the deck up for 3.3 m under the continuous top rail; a railing module (build_railings.py) fills the gap.
RAILING_X = -140.0
RAILING_GAP = (RAILING_X, 330.0, 228.0, 2000.0, 'gap')   # centre x, length, bottom z, top z, kind: cut out of the bulwark
HULL = Hull(stern_x=-700.0, bow_x=700.0,     # about 14 m overall
            beam=230.0,                      # 4.6 m beam
            keel_z=-75.0, deck_z=225.0,
            floor_z=10.0,                    # hold floor top, above the swell: 2 m of headroom to the deck beams
            sheer_mid=285.0, sheer_rise=100.0,
            stern_power=4.0,                 # a broad, rounded stern (the sheet), the bow still fine
            stern_keel_power=4.5, stern_full_len=480.0,   # her bottom stays low and full well aft
            tar_line=150.0,                  # dark tarred planking up to the wale (the sheet)
            gunports=[RAILING_GAP])
STERN_X, BOW_X, BEAM, KEEL_Z, DECK_Z, FLOOR_Z = HULL.stern_x, HULL.bow_x, HULL.beam, HULL.keel_z, HULL.deck_z, HULL.floor_z
UV_TILE = HULL.uv_tile
HATCH = (-300.0, -60.0, 50.0)  # hatch opening: aft x, forward x, half-width
# The boarding ladder, centred on the stern above the rudder's head (owner, October 16: one ladder at the middle of
# the stern, on the centreline); it replaces the ladders on both sides.
STERN_LADDER = HULL.stern_ladder_line(60.0)
CAPSTAN = (500.0, -70.0)
FRAMES = range(-640, 660, 60)
MOORING_YAW = 90.0     # bow toward open water
HULL_HEALTH = 1000.0   # tuning: ten round shot
MOORING_Y = 2350.0     # clear of the dock's end, lying along the heading
HELM_X = -540.0        # the helm stands on the open deck aft (no captain's quarters on the sloop)
# Her two empty sail hardpoints (owner, October 18: ChatGPT's layout shows two): where each socket stands and the
# assembly a Medium or Small sail fits in it: mast and yard heights above the deck, the sail's head and foot widths and
# drop (cm). build_ship_fittings.sail_assembly_looks makes the assemblies from these.
ASSEMBLIES = {
    'Mainsail': dict(size='Medium', x=140.0, height=1000.0, yard=800.0, head=560.0, foot=640.0, drop=520.0, belly=70.0),
    'Headsail': dict(size='Small', x=440.0, height=780.0, yard=620.0, head=380.0, foot=440.0, drop=400.0, belly=55.0),
}
MAST_X = ASSEMBLIES['Mainsail']['x']     # the pin rail stands at the main hardpoint


def flags(b):
    """Her two flags (owner, October 17: the sloop has 2 flag positions): a jackstaff at the bow and an ensign staff at
    the stern (DECIDED, delegated, October 18: sail assemblies carry no flags and the hull has no masts, so the flags fly
    from deck staffs). Draws them into b; returns each flag's (belay, hoist, scale)."""
    x = STERN_X + 80
    return {'JackFlag': (*deck_staff(b, BOW_X - 170, 90.0, DECK_Z, rake=30.0, height=330.0), MASTHEAD_FLAG),
            'EnsignFlag': (*deck_staff(b, x, -(HULL.half_beam(x) - 34), DECK_Z), ENSIGN_FLAG)}


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
    # The treatment station sits aft-port in the first deck below the weather deck (visual prop only).
    room.surgeon_table(-520.0, -105.0, length=110.0, width=55.0)
    # Hung from the beams over the sides, clear of the walkway down the middle.
    for x, side in ((-120.0, 1), (360.0, -1)):
        room.lantern(x, side * 105.0, DECK_Z - HULL.deck_thick - 14)
    return room.lights


LIGHTS = []


def hull_mesh():
    h = HULL
    b = Builder()
    h.outer_shell(b)
    h.inner_shell(b)
    h.rail_and_keel(b)
    h.deck(b, DECK_Z, [HATCH])
    # A hold: floorboards, deck beams framing the hatch with 2 m of headroom beneath, ribs, bulwark posts.
    h.floor(b, FLOOR_Z)
    h.beams(b, (-580, -490, -400, HATCH[0] - 8, HATCH[1] + 8, 60, 200, 340, 420, 500), DECK_Z)
    h.ribs(b, FRAMES, FLOOR_Z, DECK_Z - h.deck_thick - 10)
    h.bulwark_posts(b, range(-630, 640, 90))
    h.stairs(b, HATCH[0] + 5, HATCH[1] - 5, DECK_Z, FLOOR_Z, 10)  # down from the hatch
    h.studs(b, FRAMES)
    h.stern_ladder(b, STERN_LADDER)
    h.capstan(b, *CAPSTAN, DECK_Z)
    # The two empty sail hardpoints: a socket each, and a pin rail at the main one. No masts (they belong to the
    # sail assemblies); the bowsprit reaches out over the bow, starting clear of heads on the foredeck.
    for a_ in ASSEMBLIES.values():
        h.sail_socket(b, a_['x'], 0.0, DECK_Z)
    flags(b)
    h.bowsprit(b, (BOW_X - 70, 0.0, h.sheer(BOW_X - 70) + 30), (BOW_X + 240, 0.0, 430.0))
    h.pin_rail(b, MAST_X)
    # Turned balusters with brass caps along her bulwarks, open over the railing hardpoints, and a brass strip
    # along each side (the sheet).
    h.balustrade(b, STERN_X + 40, BOW_X - 70, skip=[(RAILING_X - 175, RAILING_X + 175)])
    h.brass_band(b)
    LIGHTS[:] = hold(b)
    h.rudder(b, -60.0, 30.0, 60.0, 45.0, 11.0)
    for side in (1, -1):
        h.cathead_and_anchor(b, 560.0, side, 1.0)
    return b


def rigging():
    """The standing rigging a bare hull has: the bowsprit's bobstay down to the stem and a shroud to each side of the bow
    (the masts' own stays and shrouds belong to the sail assemblies), as tarred rope."""
    r = Builder()
    tip = (BOW_X + 240.0, 0.0, 430.0)
    r.tube([tip, (BOW_X - 10.0, 0.0, HULL.sheer(BOW_X - 10) - 90.0)], 1.8, sides=6)
    for side in (-1, 1):
        r.tube([tip, (BOW_X - 110.0, side * (HULL.half_beam(BOW_X - 110) - 4), HULL.sheer(BOW_X - 110) + 4)], 1.8, sides=6)
    return tar_rope(r)


# ---- Assets ------------------------------------------------------------------------------------------------

def capstan_head(timber):
    """The capstan's turning head, the same on every hull with a capstan."""
    b = Builder()
    Hull.capstan_head(b)
    return write_static_mesh(b, CAPSTAN_HEAD, [timber], UV_TILE, collision=False)


PLAIN_RAILING = '/Game/Elitewake/World/Ships/SM_RailingPlain_v1'


def mount(mount_id, kind, location, yaw=0.0, sail=unreal.EWSailSize.NONE, parent='', slot=0, empty=None, look=None, mast=None):
    m = unreal.EWShipMount()
    if look:
        mesh, furled, transform = look
        m.set_editor_property('fitted_mesh', mesh)
        m.set_editor_property('fitted_furled_mesh', furled)
        m.set_editor_property('fitted_mesh_transform', transform)
    if mast:
        m.set_editor_property('mast_mesh', mast)
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


def update_definition(hull, rig, capstan, looks):
    definition = unreal.load_asset(DEFINITION)
    assert definition, DEFINITION
    deck_y = lambda x: HULL.inner_y(x, DECK_Z)
    t = unreal.EWShipMountType
    sizes = {'Medium': unreal.EWSailSize.MEDIUM, 'Small': unreal.EWSailSize.SMALL}
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
            mount('Helm', t.HELM, (HELM_X, 0, DECK_Z + 50)),
        ] + [mount(mid, t.SAIL, (a_['x'], 0, DECK_Z + 50), sail=sizes[a_['size']], look=looks[mid][:3], mast=looks[mid][3])
             for mid, a_ in ASSEMBLIES.items()] + [
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
    import build_ship_fittings as fittings   # it reads this hull, so it is imported only here
    b = hull_mesh()
    timber = make_timber_material()
    hull = write_static_mesh(b, MESH, materials(timber), UV_TILE)
    looks = fittings.sail_assembly_looks(ASSEMBLIES, DECK_Z, timber, fittings.cloth_materials(), 'Sloop')
    rig = write_static_mesh(rigging(), RIGGING, [timber], UV_TILE, collision=False)
    report = {'vertices': len(b.verts), 'triangles': len(b.tris), 'lanterns': len(LIGHTS),
              'definition': update_definition(hull, rig, capstan_head(timber), looks)}
    moor()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'SloopHullResult.json').write_text(json.dumps(report, indent=2))
    unreal.log('Sloop hull built')


if __name__ == '__main__':
    main()
