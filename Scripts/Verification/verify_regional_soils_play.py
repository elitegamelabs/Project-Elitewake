"""Screenshots of each region's own ground (owner, October 16: CLAUDE.md):
Winter frozen earth and snow, Plains loam and grass, Jungle dark loam with leaf litter and moss, Swamp black wet
peat with puddles, Desert rippled sand, hardpan and sandstone.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground (EW_PLAY_PLAYERS=1 is enough). Run unattended with
run_play_check.py. On each region's biggest island, at noon, it finds a spot a third of the way from the middle to
the shore (ground, not sea) and photographs the ground from 4 m up looking down and out, the survivor hidden.
Shots in Saved/Screenshots/RegionalSoils/<region>.png. Judging the soils is a person's; the check proves each island
has ground there and that the terrain material compiled (a failed one draws the engine's grey default instead).
Writes Saved/RegionalSoilsPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'RegionalSoilsPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'RegionalSoils')
SHOTS.mkdir(parents=True, exist_ok=True)
REGIONS = ('Plains', 'Winter', 'Jungle', 'Swamp', 'Desert')
world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
measured = {}
state = {'queue': list(REGIONS), 'phase': 'place', 'at': 0.0, 'handle': None}


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 60000), unreal.Vector(x, y, -5000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    hit = hit[0] if isinstance(hit, tuple) else hit
    return hit.to_tuple()[4].z if hit else None


def spot(region):
    isl = next(i for i in W.ISLANDS if i.region == region)
    for a in range(0, 360, 30):
        x = isl.cx + math.cos(math.radians(a)) * isl.rx * .35
        y = isl.cy + math.sin(math.radians(a)) * isl.ry * .35
        z = ground(x, y)
        if z is not None and z > 30:
            return isl.key, a, unreal.Vector(x, y, z)
    raise AssertionError(f'no ground found on {isl.key}')


def hold(eye, look):
    move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
    move.set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    move.stop_movement_immediately()
    pawn.set_actor_location(eye, False, True)
    pawn.set_actor_hidden_in_game(True)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, look))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': list(measured), 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWPLAYCHECK RegionalSoils success={error is None} error={error}')


def tick(delta):
    try:
        if not state['queue']:
            return finish()
        region = state['queue'][0]
        now = time.monotonic()
        if state['phase'] == 'place':
            key, angle, at = spot(region)
            out = unreal.Vector(math.cos(math.radians(angle)), math.sin(math.radians(angle)), 0)
            state['view'] = (at + unreal.Vector(0, 0, 400) - out * 300, at + out * 900)
            measured[region] = {'island': key, 'ground_cm': round(at.z)}
            hold(*state['view'])
            state.update(phase='settle', at=now)
        elif state['phase'] == 'settle' and now - state['at'] < 2.5:
            hold(*state['view'])
        elif state['phase'] == 'settle':
            hold(*state['view'])
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / (region + ".png")}"')
            state.update(phase='wait', at=now)
        elif state['phase'] == 'wait' and now - state['at'] > 1.0:
            state['queue'].pop(0)
            state['phase'] = 'place'
    except Exception as error:
        finish(repr(error))


unreal.EWDayNightSubsystem.get_for_world(world).set_hour(12.0)
unreal.SystemLibrary.execute_console_command(world, 'r.MotionBlurQuality 0')
state['handle'] = unreal.register_slate_post_tick_callback(tick)
