"""Build the sloop's hull mesh in Unreal from the owner's concept art (Art/Concepts/Boats/2026-10-11/Sloop-*).
Safe to run again. Run in the editor, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

A bare double-ended hull in weathered oak: the stern mirrors the bow, both sweeping up in a deep curve to a post.
Planked sides with seams and two wales, a tarred bottom, low bulwarks with a rail and posts, one gunport each side. A flat deck
has a cargo hatch with a coaming and stairs down into a cramped hold of ribs, floorboards, deck beams and a post.
Boarding ladders on both sides, a capstan near the bow, the mast and bowsprit are part of the hull, as are the
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

MESH = '/Game/Elitewake/World/Ships/SM_SloopHull_v2'
RIGGING = '/Game/Elitewake/World/Ships/SM_SloopRigging_v1'
DEFINITION = '/Game/Elitewake/Ships/DA_Ship_Sloop'
CAPSTAN_HEAD = '/Game/Elitewake/World/Ships/SM_CapstanHead_v1'
MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'

GUNPORT = (-140.0, 48.0, 268.0, 306.0)  # centre x, width, bottom z, top z: in the bulwark
HULL = Hull(stern_x=-700.0, bow_x=700.0,     # about 14 m overall, ends alike
            beam=250.0,                      # 5 m beam
            keel_z=-110.0, deck_z=250.0,
            floor_z=30.0,                    # hold floor top, above the swell
            sheer_mid=315.0, sheer_rise=115.0,
            gunports=[GUNPORT])
STERN_X, BOW_X, BEAM, KEEL_Z, DECK_Z, FLOOR_Z = HULL.stern_x, HULL.bow_x, HULL.beam, HULL.keel_z, HULL.deck_z, HULL.floor_z
UV_TILE = HULL.uv_tile
HATCH = (-280.0, -40.0, 50.0)  # hatch opening: aft x, forward x, half-width
LADDER_X = -360.0       # aft of the gunports
CAPSTAN = (480.0, -70.0)
# Rig: one mast with a gaff mainsail and a jib on the forestay out to the bowsprit.
MAST_X, MAST_TOP = 120.0, 1420.0
BOOM_Z = 460.0                       # boom height, above the heads of crew on deck
STAY_TOP = (MAST_X + 8, 0.0, MAST_TOP - 30)
STAY_BOW = (925.0, 0.0, 500.0)       # bowsprit end, where the forestay and the jib's tack meet
FRAMES = range(-640, 660, 60)
MOORING_YAW = 90.0     # bow toward open water
MOORING_Y = 2350.0     # clear of the dock's end, lying along the heading
SHROUD_XS = (MAST_X - 30, MAST_X + 30)


def hull_mesh():
    h = HULL
    b = Builder()
    h.outer_shell(b)
    h.inner_shell(b)
    h.rail_and_keel(b)
    h.deck(b, DECK_Z, [HATCH])
    # A cramped hold: floorboards, deck beams framing the hatch with 2 m of headroom beneath, ribs, bulwark posts.
    h.floor(b, FLOOR_Z)
    h.beams(b, (-580, -490, -400, HATCH[0] - 8, HATCH[1] + 8, 60, 200, 290, 380, 470), DECK_Z)
    h.ribs(b, FRAMES, FLOOR_Z, DECK_Z - h.deck_thick - 10)
    h.bulwark_posts(b, range(-630, 640, 90))
    h.stairs(b, HATCH[0] + 5, HATCH[1] - 5, DECK_Z, FLOOR_Z, 10)  # down from the hatch; the mast stands forward of them
    h.gunport_frames(b)
    h.studs(b, FRAMES)
    h.ladders(b, LADDER_X)
    h.capstan(b, *CAPSTAN, DECK_Z)
    # The mast steps on the hold floor and rises through the deck; the bowsprit reaches out over the bow,
    # starting clear of heads on the foredeck.
    h.mast(b, MAST_X, MAST_TOP)
    h.bowsprit(b, (BOW_X - 70, 0.0, h.sheer(BOW_X - 70) + 30), STAY_BOW)
    # Working detail: the shrouds' channels and deadeyes, a pin rail at the mast, a rudder on the stern and an
    # anchor catted at each bow.
    h.channels(b, SHROUD_XS)
    h.pin_rail(b, MAST_X)
    h.rudder(b, -80.0, 40.0, 70.0, 50.0, 12.0)
    for side in (1, -1):
        h.cathead_and_anchor(b, 560.0, side, 1.0)
    return b


def rigging():
    """Standing rigging: a forestay to the bowsprit and two shrouds a side to their deadeyes, with ratlines,
    as tarred rope."""
    r = Builder()
    r.tube([STAY_TOP, STAY_BOW], 1.8, sides=6)
    HULL.shrouds(r, MAST_X, MAST_TOP - 90, SHROUD_XS)
    return tar_rope(r)


# ---- Assets ------------------------------------------------------------------------------------------------

def capstan_head(timber):
    """The capstan's turning head, the same on every hull with a capstan."""
    b = Builder()
    Hull.capstan_head(b)
    return write_static_mesh(b, CAPSTAN_HEAD, [timber], UV_TILE, collision=False)


def mount(mount_id, kind, location, yaw=0.0, sail=unreal.EWSailSize.NONE):
    m = unreal.EWShipMount()
    m.set_editor_property('mount_id', mount_id)
    m.set_editor_property('type', kind)
    m.set_editor_property('sail_size', sail)
    m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(*location), rotation=unreal.Rotator(0, 0, yaw)))
    return m


def update_definition(hull, rig, capstan):
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
        'hold_floor_height': FLOOR_Z,
        'anchor_point': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z + 40),
        'capstan_mesh': capstan, 'capstan_location': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z),
        'cargo_hatch_point': unreal.Vector((HATCH[0] + HATCH[1]) / 2, 0, DECK_Z + 5),
        'boarding_points': [unreal.Vector(LADDER_X, side * (HULL.half_beam(LADDER_X) + 30), 60) for side in (-1, 1)],
        'mounts': [
            mount('Helm', t.HELM, (-520, 0, DECK_Z + 50)),
            mount('Mainsail', t.SAIL, (MAST_X, 0, DECK_Z + 50), sail=unreal.EWSailSize.MEDIUM),
            mount('Headsail', t.SAIL, (560, 0, DECK_Z + 50), sail=unreal.EWSailSize.SMALL),
            mount('PortCannon', t.CANNON, (GUNPORT[0], -(deck_y(GUNPORT[0]) - 45), DECK_Z + 40), yaw=-90),
            mount('StarboardCannon', t.CANNON, (GUNPORT[0], deck_y(GUNPORT[0]) - 45, DECK_Z + 40), yaw=90),
        ],
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
    hull = write_static_mesh(b, MESH, [timber], UV_TILE)
    rig = write_static_mesh(rigging(), RIGGING, [timber], UV_TILE, collision=False)
    report = {'vertices': len(b.verts), 'triangles': len(b.tris), 'definition': update_definition(hull, rig, capstan_head(timber))}
    moor()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'SloopHullResult.json').write_text(json.dumps(report, indent=2))
    unreal.log('Sloop hull built')


if __name__ == '__main__':
    main()
