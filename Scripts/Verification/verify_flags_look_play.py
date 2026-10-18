"""How the flags look (owner, October 17: plain clean white, fluttering in the wind; frayed and torn only by combat).
Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground with one player (EW_PLAY_PLAYERS=1: screenshots are the
player's own view), with the moored sloop bare. Run unattended with run_play_check.py. The survivor hoists a white flag
at each of the sloop's halyards; shots of the new masthead flag and ensign from the deck; then round shots tear the
ensign (wear about 0.7) and a shot of it torn. Screenshots in Saved/Screenshots/Flags. Writes
Saved/FlagsLookPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'FlagsLookPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Flags')
SHOTS.mkdir(parents=True, exist_ok=True)
world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop')
flag = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestFlagWhite')
checks, measured = [], {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'at': 0.0, 'shot': None, 'look': None, 'stand': None}
MAST, ENSIGN = 'MastheadFlag', 'MizzenFlag'   # her main and mizzen mastheads (the October 18 design)


def flag_at(mount):
    return next(c for c in ship.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith(f'Fitting_{mount}')).get_world_location()


def hold():
    stand, look = state['stand'], state['look']
    pawn.teleport(stand(), ship.get_actor_rotation())
    pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    eye = pawn.get_actor_location() + unreal.Vector(0, 0, pawn.get_editor_property('base_eye_height'))
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, look()))


def deck(x, y, rise=0.0):
    return lambda: ship.get_actor_transform().transform_location(unreal.Vector(x, y, ship.get_deck_height() + rise + 98))


def hoist(mount, x, y, rise=0.0):
    def begin():
        state.update(stand=deck(x, y, rise), look=lambda: ship.get_mount_world_transform(mount).translation, at=time.monotonic(), shot=None)
        hold()
        assert lib.send_verification_interaction_request(pc, ship), f'refused at {mount} (aimed {ship.find_aimed_mount(pawn)})'
    return begin


def up(mount):
    return lambda: ship.get_fitting(mount) == flag


def look(mount, x, y, label):
    def begin():
        state.update(stand=deck(x, y), look=lambda: flag_at(mount) + unreal.Vector(0, 0, 220), at=time.monotonic(), shot=None)
        hold()

    def done():
        hold()
        if time.monotonic() - state['at'] < 2.0:
            return False
        if state['shot'] is None:
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / (label + ".png")}"')
            state['shot'] = time.monotonic()
            return False
        return time.monotonic() - state['shot'] > 1.0
    return begin, done


def tear():
    for _ in range(1):
        ship.take_round_shot(flag_at(ENSIGN), ship.get_actor_right_vector(), None)
    ship.take_round_shot(ship.get_actor_transform().transform_location(unreal.Vector(500, 120, 60)), ship.get_actor_right_vector(), None)
    measured['ensign_wear'] = round(ship.get_flag_wear(ENSIGN), 2)
    measured['masthead_wear'] = round(ship.get_flag_wear(MAST), 2)


def grant():
    assert pawn.get_inventory_component().add_item(flag, 2) == 2
    unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / "warmup.png"}"')


STEPS = [
    ('Two white flags granted', grant, lambda: True, 3),
    ('Hoisted at the masthead halyard', hoist(MAST, 190, 40), up(MAST), 8),
    ('Hoisted at the mizzen halyard, on the stern deck', hoist(ENSIGN, -400, 30, 200), up(ENSIGN), 8),
    ('Screenshot: the new masthead flag from the deck', *look(MAST, 560, -80, 'masthead_new'), 10),
    ('Screenshot: the new ensign from amidships', *look(ENSIGN, 150, 110, 'ensign_new'), 10),
    ('Round shots tear the ensign', tear, lambda: ship.get_flag_wear(ENSIGN) > .6, 5),
    ('Screenshot: the torn ensign', *look(ENSIGN, 150, 110, 'ensign_torn'), 10),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured}, indent=2))
    unreal.log(f'EWPLAYCHECK FlagsLook success={error is None} error={error}')


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
