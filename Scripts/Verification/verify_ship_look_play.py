"""How a ship looks against the owner's design sheet (owner, October 18: Art/Concepts/Boats/2026-10-18/
Ship-Design-Sheet-v1.webp). Needs Play in /Game/Elitewake/Maps/Test/Lvl_ShipsTest with one player
(EW_PLAY_PLAYERS=1). Set EW_LOOK_SHIP to the ship's id (default Sloop). Run unattended with run_play_check.py.

The survivor hovers (flying: a camera stand, never in play) at set places round the ship and inside her, looking at
her: a raised three-quarter view from the bow, her side, her stern and ladder, her deck from above, her cabin under the
stern deck and her hold. Also checks her lanterns' lights are lit inside. Screenshots in Saved/Screenshots/ShipLook/<id>.
Writes Saved/ShipLookPlayResult.json.
"""
import json
import os
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
SHIP_ID = os.environ.get('EW_LOOK_SHIP', 'Sloop')
RESULT = Path(unreal.Paths.project_saved_dir(), 'ShipLookPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'ShipLook', SHIP_ID)
SHOTS.mkdir(parents=True, exist_ok=True)
world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == SHIP_ID)
d = ship.get_editor_property('definition')
E = d.get_editor_property('hull_extent')
DECK = d.get_editor_property('deck_height')
FLOOR = d.get_editor_property('hold_floor_height')
checks, measured = [], {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'at': 0.0, 'shot': None, 'view': None}


def hold_view():
    eye_local, target_local, hide = state['view']
    t = ship.get_actor_transform()
    move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
    move.set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    at = t.transform_location(unreal.Vector(*eye_local))
    assert pawn.teleport(at, unreal.Rotator()) or (pawn.get_actor_location() - at).length() < 30, f'no room for the camera at {eye_local}'
    move.stop_movement_immediately()
    pawn.set_actor_hidden_in_game(hide)
    eye = pawn.get_actor_location() + unreal.Vector(0, 0, pawn.get_editor_property('base_eye_height'))
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, t.transform_location(unreal.Vector(*target_local))))


def view(label, eye, target, hide=False):
    def begin():
        state.update(view=(eye, target, hide), at=time.monotonic(), shot=None)
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
    return label, begin, done


def lanterns():
    lights = [c for c in ship.get_components_by_class(unreal.PointLightComponent) if c.get_name().startswith('Lantern')]
    want = len(d.get_editor_property('lantern_lights'))
    measured['lanterns'] = {'defined': want, 'lit': len(lights)}
    assert want > 0 and len(lights) == want and all(l.is_visible() for l in lights), measured['lanterns']
    unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / "warmup.png"}"')
    return True


L, B = E.x, E.y
STEPS = [('Her lanterns are lit inside', lambda: None, lanterns, 5)] + [
    (f'Screenshot: {label}', begin, done, 12) for label, begin, done in (
        view('three_quarter_bow', (L * 1.5, -B * 4.5, DECK + 900), (L * .1, 0, DECK + 300), hide=True),
        view('side_port', (0, -B * 6.5, DECK + 250), (0, 0, DECK + 350), hide=True),
        view('stern_ladder', (-L * 2.3, -B * .6, DECK + 120), (-L, 0, DECK - 20), hide=True),
        view('deck_from_above', (-L * .2, -B * .4, DECK + 1500), (L * .05, 0, DECK), hide=True),
        view('cabin', (-L * .681, -B * .216, DECK + 95), (-L * .823, B * .2, DECK + 40), hide=True),
        view('hold', (-L * .174, B * .43, FLOOR + 95), (L * .6, 0, FLOOR + 40), hide=True),
    )]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    pawn.set_actor_hidden_in_game(False)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured}, indent=2))
    unreal.log(f'EWPLAYCHECK ShipLook success={error is None} error={error}')


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
