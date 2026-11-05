"""Visible Play check of the Plains3 preview's actual character movement along its exit ramp.

Run from the editor console while Play is active in Lvl_PlainsCavernExitPreview.
Writes Saved/PlainsCavernExitPlayResult.json and two screenshots. This is a
walking/collision check; it does not claim ship entry or final-world terrain.
"""
import json
import math
import sys
import time
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_terrain as T  # noqa: E402

cave = T.CAVES['Plains3']
root = Path(unreal.Paths.project_saved_dir())
shots = root / 'Screenshots' / 'PlainsCavernExit'
shots.mkdir(parents=True, exist_ok=True)
result = root / 'PlainsCavernExitPlayResult.json'
world = next(w for w in unreal.EWEditorVerificationLibrary.get_play_worlds()
             if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
lib = unreal.EWEditorVerificationLibrary
state = {'started': time.monotonic(), 'begun': False, 'finished': False,
         'min_clearance_cm': 1e9, 'max_height_error_cm': 0.0, 'farthest_u_cm': 0.0,
         'frames': 0, 'screenshots': [], 'handle': None}


def shot(name):
    path = shots / f'{name}.png'
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{path}"')
    state['screenshots'].append(str(path))


def finish(error=None):
    if state['finished']:
        return
    state['finished'] = True
    lib.send_verification_gameplay_key_state(pc, 'W', False)
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report = {'success': error is None, 'error': error,
              'farthest_u_cm': round(state['farthest_u_cm']),
              'target_u_cm': round(cave.depth + 500),
              'max_height_error_cm': round(state['max_height_error_cm']),
              'seconds': round(time.monotonic() - state['started'], 1),
              'frames': state['frames'], 'screenshots': state['screenshots'],
              'preview_only': True, 'sailing_verified': False}
    result.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK PlainsExit success={error is None} error={error}')


def tick(delta):
    try:
        now = time.monotonic()
        if not state['begun']:
            u = cave.chamber_u + 300.0
            v, surface = cave.inland_exit_profile(u)
            x, y = cave.world(u, v)
            yaw = math.degrees(cave.heading)
            assert pawn.teleport(unreal.Vector(x - cave.mx, y - cave.my, surface + 105),
                                 unreal.Rotator(0, 0, yaw))
            pc.set_control_rotation(unreal.Rotator(0, -7, yaw))
            state['begun'] = True
            state['move_after'] = now + 1.0
            shot('start')
            return
        if now < state['move_after']:
            return
        if not state.get('moving'):
            assert lib.send_verification_gameplay_key_state(pc, 'W', True)
            state['moving'] = True
        location = pawn.get_actor_location()
        u, v = cave.local(location.x + cave.mx, location.y + cave.my)
        state['farthest_u_cm'] = max(u, state['farthest_u_cm'])
        state['frames'] += 1
        if cave.chamber_u <= u <= cave.depth + 700:
            _, surface = cave.inland_exit_profile(u)
            state['max_height_error_cm'] = max(state['max_height_error_cm'],
                                               abs(location.z - 96.0 - surface))
        if u >= cave.depth + 500:
            shot('island_landing')
            assert state['max_height_error_cm'] < 130, 'character left the walkable ramp'
            finish()
        elif now - state['started'] > 45:
            finish(f'character stopped before island landing at u={u:.0f} cm')
    except Exception as exc:
        finish(repr(exc))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
