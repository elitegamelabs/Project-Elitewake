"""Screenshots for the dense foliage and the Winter trees' partial snow (owner, October 16:
CLAUDE.md), close up and at gameplay distance.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground (EW_PLAY_PLAYERS=1 is enough). Run unattended with
run_play_check.py. For an oak (Plains), ash and Maravai (Jungle), birch (Winter) and spruce (Swamp): finds the tree of
that kind with the fewest others round it, and photographs it from the sun's side at 12 m and at
40 m, at noon, the survivor hidden. Writes the shots to Saved/Screenshots/TreeFoliage/<kind>_<near|far>.png and the
trees it used to Saved/TreeFoliagePlayResult.json. Judging density and the snow is a person's (an automatic
count could not tell snowy leaves from the snowy hills behind them).
"""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'TreeFoliagePlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'TreeFoliage')
SHOTS.mkdir(parents=True, exist_ok=True)
KINDS = ('Oak', 'Ash', 'Maravai', 'Birch', 'Spruce')
DISTANCES = (('near', 1200.0), ('far', 4000.0))

world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
trees = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHarvestTree))
clock = unreal.EWDayNightSubsystem.get_for_world(world)


def kind(t):
    return next((k for k in KINDS if t.get_actor_label().startswith(k)), None)


def loneliest(name):
    mine = [t for t in trees if kind(t) == name]
    assert mine, f'no {name} trees'
    sample = mine[::max(1, len(mine) // 300)]
    others = [t.get_actor_location() for t in trees]
    def crowd(t):
        p = t.get_actor_location()
        return sum(1 for q in others if 1 < (q - p).length() < 1500)
    return min(sample, key=crowd)


def view(tree, distance):
    p = tree.get_actor_location()
    _, extent = tree.get_actor_bounds(False)
    # From the sun's side, so the crown is lit (a crown seen against the sun reads as a dark shape).
    sun = next(iter(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.DirectionalLight)), None)
    if sun:
        f = sun.get_actor_forward_vector()
        away = unreal.Vector(-f.x, -f.y, 0)
    else:
        away = unreal.Vector(1, 0, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    middle = p + unreal.Vector(0, 0, extent.z)
    eye = middle + away * distance + unreal.Vector(0, 0, distance * .12)
    # Never inside a hill: at least 3 m over the ground where the camera stands.
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(eye.x, eye.y, 60000), unreal.Vector(eye.x, eye.y, -5000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    hit = hit[0] if isinstance(hit, tuple) else hit
    if hit:
        eye.z = max(eye.z, hit.to_tuple()[4].z + 300)
    return eye, middle


state = {'queue': [(k, d, cm) for k in KINDS for d, cm in DISTANCES], 'phase': 'place', 'at': 0.0, 'handle': None, 'used': {}}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': list(state['used']), 'error': error, 'trees': state['used'],
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWPLAYCHECK TreeFoliage success={error is None} error={error}')


def hold(eye, middle):
    pawn.get_component_by_class(unreal.CharacterMovementComponent).set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    pawn.set_actor_location(eye, False, True)
    pawn.set_actor_hidden_in_game(True)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, middle))


def tick(delta):
    try:
        if not state['queue']:
            return finish()
        name, label, distance = state['queue'][0]
        now = time.monotonic()
        if state['phase'] == 'place':
            unreal.SystemLibrary.execute_console_command(world, 'r.MotionBlurQuality 0')
            if name not in state['used']:
                tree = loneliest(name)
                state['used'][name] = {'label': tree.get_actor_label(), 'at': [round(v) for v in tree.get_actor_location().to_tuple()]}
                state['tree'] = tree
            state['view'] = view(state['tree'], distance)
            hold(*state['view'])
            state.update(phase='settle', at=now)
        elif state['phase'] == 'settle' and now - state['at'] < 2.0:
            hold(*state['view'])   # held in the air, while distant detail streams in
        elif state['phase'] == 'settle':
            hold(*state['view'])
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / f"{name}_{label}.png"}"')
            state.update(phase='wait', at=now)
        elif state['phase'] == 'wait' and now - state['at'] > 1.0:
            state['queue'].pop(0)
            state['phase'] = 'place'
    except Exception as error:
        finish(repr(error))


clock.set_hour(12.0)   # noon: the crowns lit from high up
unreal.SystemLibrary.execute_console_command(world, 'r.MotionBlurQuality 0')   # the camera jumps between trees
state['handle'] = unreal.register_slate_post_tick_callback(tick)
