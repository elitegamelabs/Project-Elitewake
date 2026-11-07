"""How the tortoise's shell looks (T6: five vertebral, four costal and eleven marginal plates a side, dark seams,
growth rings). Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground with one player (EW_PLAY_PLAYERS=1). Run
unattended with run_play_check.py.

The nearest tortoise is held still (its movement stopped for the shot; a camera stand, never in play) and the
survivor hovers beside it and above it, looking at it: a side view and a top view. Screenshots in
Saved/Screenshots/Animals. Writes Saved/TortoiseLookPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'TortoiseLookPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Animals')
SHOTS.mkdir(parents=True, exist_ok=True)
world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
tortoises = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal)
             if str(a.get_editor_property('definition').get_editor_property('display_name')) == 'Tortoise']
assert tortoises, 'no tortoise in the world'
tortoise = min(tortoises, key=lambda a: (a.get_actor_location() - pawn.get_actor_location()).length())
checks, measured = [], {'tortoises': len(tortoises)}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'at': 0.0, 'shot': None, 'view': None}


def hold_still():
    # Animals wander on their own tick; pausing it keeps this one where it stands for the shots.
    tortoise.set_actor_tick_enabled(False)


def hold_view():
    eye_local, look_local = state['view']
    t = tortoise.get_actor_transform()
    move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
    move.set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    pawn.teleport(t.transform_location(unreal.Vector(*eye_local)), unreal.Rotator())
    move.stop_movement_immediately()
    pawn.set_actor_hidden_in_game(True)
    boom = pawn.get_component_by_class(unreal.SpringArmComponent)
    if boom:
        boom.set_editor_property('target_arm_length', 0.0)
    eye = pawn.get_actor_location() + unreal.Vector(0, 0, pawn.get_editor_property('base_eye_height'))
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, t.transform_location(unreal.Vector(*look_local))))


def view(label, eye, look):
    def begin():
        hold_still()
        state.update(view=(eye, look), at=time.monotonic(), shot=None)
        hold_view()

    def done():
        hold_view()
        if time.monotonic() - state['at'] < 2.0:
            return False
        if state['shot'] is None:
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / (label + ".png")}"')
            state['shot'] = time.monotonic()
            return False
        return time.monotonic() - state['shot'] > 1.0
    return begin, done


def warm_up():
    measured['at'] = str(tortoise.get_actor_location())
    unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / "warmup.png"}"')


# The eye is placed relative to the tortoise, in cm; the camera sits about base eye height above the eye point.
STEPS = [
    ('A tortoise is found and held still', warm_up, lambda: True, 3),
    ('Screenshot: tortoise_side', *view('tortoise_side', (0, -200, 20), (0, 0, 25)), 12),
    ('Screenshot: tortoise_top', *view('tortoise_top', (-25, 0, 170), (0, 0, 20)), 12),
    ('Screenshot: tortoise_three_quarter', *view('tortoise_three_quarter', (150, -150, 10), (0, 0, 20)), 12),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    pawn.set_actor_hidden_in_game(False)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured}, indent=2))
    unreal.log(f'EWPLAYCHECK TortoiseLook success={error is None} error={error}')


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
