"""How the gunport covers look from outside the hull (owner, October 17: sliding dark opaque glass covers; the cannon
runs out when its port opens). Needs Play in /Game/Elitewake/Maps/Test/Lvl_ShipsTest with one player
(EW_PLAY_PLAYERS=1). Run unattended with run_play_check.py. The survivor fits and mans a cannon at the brigantine's middle
starboard port; a camera off her starboard side shoots her ports shut, then that one open with its cannon run out, and
the schooner's square ports. Screenshots in Saved/Screenshots/Gunports. Writes Saved/GunportsLookPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'GunportsLookPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Gunports')
SHOTS.mkdir(parents=True, exist_ok=True)
GUN = 'StarboardCannon2'
world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()


def ship_named(ship_id):
    return next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
                if str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id)


brig, schooner = ship_named('Brigantine'), ship_named('Schooner')
cannon = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestCannon')
checks, measured = [], {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'at': 0.0, 'shot': None, 'sent': 0.0, 'camera': None}


def stand_by_gun():
    at = brig.get_actor_transform().inverse_transform_location(brig.get_mount_world_transform(GUN).translation)
    for dx, fy in ((60, .5), (-60, .5), (60, .3), (120, .4)):
        if pawn.teleport(brig.get_actor_transform().transform_location(unreal.Vector(at.x + dx, at.y * fy, at.z - 40 + 98)), brig.get_actor_rotation()):
            break
    eye = pawn.get_actor_location() + unreal.Vector(0, 0, pawn.get_editor_property('base_eye_height'))
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, brig.get_mount_world_transform(GUN).translation))


def grant():
    assert pawn.get_inventory_component().add_item(cannon, 1) == 1
    unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / "warmup.png"}"')


def press():
    stand_by_gun()
    state['sent'] = time.monotonic()
    assert lib.send_verification_interaction_request(pc, brig)


def until(cond):
    def done():
        stand_by_gun() if brig.get_cannon_gunner(GUN) is None else None
        if cond():
            return True
        if time.monotonic() - state['sent'] > 1.5:
            state['sent'] = time.monotonic()
            assert lib.send_verification_interaction_request(pc, brig)
        return False
    return done


def view(ship, out, along, up, label):
    """The survivor hovers (flying, a camera stand) `out` cm off the ship's starboard side, `along` cm forward of her middle, looking at her side
    `up` cm above the water; the camera behind them sees her ports."""
    def place():
        t = ship.get_actor_transform()
        spot = t.transform_location(unreal.Vector(along, out, up + 60))
        move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
        # Hovering at the ports' height (a test camera stand, never in play): flying, held in place.
        move.set_movement_mode(unreal.MovementMode.MOVE_FLYING)
        pawn.teleport(spot, unreal.Rotator())
        move.stop_movement_immediately()
        eye = pawn.get_actor_location() + unreal.Vector(0, 0, pawn.get_editor_property('base_eye_height'))
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, t.transform_location(unreal.Vector(along, 0, up))))

    def begin():
        place()
        state.update(at=time.monotonic(), shot=None)

    def done():
        place()
        if time.monotonic() - state['at'] < 1.5:
            return False
        if state['shot'] is None:
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / (label + ".png")}"')
            state['shot'] = time.monotonic()
            return False
        return time.monotonic() - state['shot'] > 1.0
    return begin, done


def leave():
    assert lib.send_verification_interaction_request(pc, brig)


def open_port():
    assert lib.send_verification_gameplay_key(pc, 'Up')


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured}, indent=2))
    unreal.log(f'EWPLAYCHECK GunportsLook success={error is None} error={error}')


STEPS = [
    ('A cannon granted', grant, lambda: True, 3),
    ("Fitted at the brigantine's middle starboard port", press, until(lambda: brig.get_fitting(GUN) == cannon), 10),
    ('Screenshot: her starboard ports, all shut', *view(brig, 1000, 0, 150, 'brigantine_shut'), 10),
    ('Manned', press, until(lambda: brig.get_cannon_gunner(GUN) == pawn), 10),
    ('Up opens the middle port', open_port, lambda: brig.get_gunport_opening(GUN) >= .99, 5),
    ('The gunner leaves the cannon; the port stays open', leave, lambda: brig.get_cannon_gunner(GUN) is None and brig.is_gunport_open(GUN), 5),
    ('Screenshot: the middle port open, its cannon run out', *view(brig, 700, 0, 150, 'brigantine_open'), 10),
    ("Screenshot: the schooner's square ports, shut", *view(schooner, 800, 0, 130, 'schooner_shut'), 10),
]


def tick(delta):
    description, begin, done, timeout = STEPS[state['index']]
    try:
        if not state['begun']:
            begin()
            state.update(begun=True, deadline=time.monotonic() + timeout)
            return
        if done():
            checks.append(description)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
        elif time.monotonic() > state['deadline']:
            raise TimeoutError(f'not done within {timeout} s')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


unreal.SystemLibrary.execute_console_command(world, 'r.MotionBlurQuality 0')
state['handle'] = unreal.register_slate_post_tick_callback(tick)
