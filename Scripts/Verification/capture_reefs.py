"""The three open-ocean reefs, evidence captures for owner visual review (November 6): for each reef, a view down from the
surface by day, the same at night (the corals glow), and a diver's view among the corals. One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check capture_reefs.py -Result ReefCaptures.json -Players 1 -Standalone 1
Writes Saved/Screenshots/Reefs/*.png and Saved/ReefCaptures.json ('success' only means the pictures were taken).
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_terrain as T  # noqa: E402
from world_reefs import REEFS  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
clock = unreal.EWDayNightSubsystem.get_for_world(world)
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Reefs')
SHOTS.mkdir(parents=True, exist_ok=True)
for old in SHOTS.glob('*.png'):
    old.unlink()
RESULT = Path(unreal.Paths.project_saved_dir(), 'ReefCaptures.json')
report = {'shots': []}


def floor(x, y):
    corals = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor) if a.get_actor_label().startswith('Reef ')]
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, T.SEA - 100), unreal.Vector(x, y, T.SEA - 5000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [pawn] + corals, unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else T.SEA - 2000


def plan():
    steps = []
    for reef in REEFS:
        z = floor(reef.cx, reef.cy)
        # From 25 m off, a little above the corals, looking at the reef's middle.
        ox, oy = reef.cx - 2500, reef.cy
        for hour, name in ((12.0, 'day'), (23.0, 'night')):
            steps.append((reef.key, name, hour, unreal.Vector(ox, oy, z + 450), unreal.Vector(reef.cx, reef.cy, z + 80)))
        # Floating at the surface above it, looking down at the glow (night).
        steps.append((reef.key, 'surface_night', 23.0, unreal.Vector(reef.cx - 900, reef.cy, T.SEA - 60), unreal.Vector(reef.cx, reef.cy, z)))
    return steps


STEPS = plan()
state = {'i': 0, 'phase': 'place', 'at': time.monotonic() + 2.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ReefCaptures success={error is None} error={error}')


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(STEPS):
            finish()
            return
        key, name, hour, eye, target = STEPS[state['i']]
        if state['phase'] == 'place':
            clock.set_hour(hour)
            pawn.teleport(eye, unreal.Rotator())
            state.update(phase='aim', at=time.monotonic() + 1.0)
        elif state['phase'] == 'aim':
            here, _ = pawn.get_actor_eyes_view_point()
            look = unreal.MathLibrary.find_look_at_rotation(here, target)
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=look.pitch, yaw=look.yaw))
            state.update(phase='shoot', at=time.monotonic() + 2.5)
        else:
            path = SHOTS / f'{key}_{name}.png'
            unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{path}"')
            report['shots'].append(path.name)
            state.update(i=state['i'] + 1, phase='place', at=time.monotonic() + 2.0)
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
