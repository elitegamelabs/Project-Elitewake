"""Wading ashore (single-player Play session). Owner, October 27: swimming in, there is nowhere to climb up onto the sand; the
sea floor should slope up so a survivor wades in, the water going down their legs the further they go.
At 8 points round every island the survivor starts 30 m offshore, swimming, and holds forward toward the island for 12 s. Records
where they end: standing on land (walking, above the waterline) or still in the water / stuck, with the water depth at the end.
Writes Saved/WadeAshorePlayResult.json (look-only: it never fails on stuck spots, it lists them)."""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
survival = pawn.get_survival_component()
trials = []
for isle in W.ISLANDS:
    for k in range(8):
        a = k * math.pi / 4 + .2
        r = isle.radius(a)
        sx, sy = isle.cx + (r + 3000) * math.cos(a), isle.cy + (r + 3000) * math.sin(a)
        if W.near_port(sx, sy, 1500) or any(math.hypot(sx - o.cx, sy - o.cy) < 0 for o in ()):
            continue
        trials.append((isle.key, k, sx, sy, math.degrees(a) + 180))
state = {'i': 0, 'phase': 0, 'at': time.monotonic() + 14, 'handle': None, 'dir': unreal.Vector(1, 0, 0), 'hold_until': 0.0}
results = []


def tick(delta):
    survival.restore_health(1000.0)
    survival.set_hunger(100.0)
    survival.set_hydration(100.0)
    if time.monotonic() < state['hold_until']:
        pawn.add_movement_input(state['dir'], 1.0, False)
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(trials):
            finish()
            return
        key, k, sx, sy, yaw = trials[state['i']]
        if state['phase'] == 0:
            pawn.teleport(unreal.Vector(sx, sy, T.SEA - 20), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            state['dir'] = unreal.MathLibrary.get_forward_vector(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            state['hold_until'] = time.monotonic() + 12.5
            state['phase'] = 1
            state['at'] = time.monotonic() + 12.5
        else:
            loc = pawn.get_actor_location()
            mode = str(pawn.character_movement.movement_mode)
            ground = T.height(loc.x, loc.y)
            ashore = 'WALKING' in mode.upper() and loc.z - 90 > T.SEA + 10
            results.append({'island': key, 'angle_index': k, 'ashore': ashore, 'mode': mode, 'z': round(loc.z),
                            'x': round(loc.x), 'y': round(loc.y), 'ground_z_layout': round(ground),
                            'start_dist_m': round(math.hypot(loc.x - sx, loc.y - sy) / 100, 1)})
            state['phase'] = 0
            state['i'] += 1
            state['at'] = time.monotonic() + .3
    except Exception as exc:
        finish(repr(exc))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    by = {}
    for r in results:
        by.setdefault(r['island'], []).append(r['ashore'])
    summary = {k: f'{sum(v)}/{len(v)} ashore' for k, v in by.items()}
    (saved / 'WadeAshorePlayResult.json').write_text(json.dumps({'success': error is None, 'error': error, 'summary': summary, 'trials': results}, indent=2))
    unreal.log(f'EWPLAYCHECK WadeAshore success={error is None} {summary}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
