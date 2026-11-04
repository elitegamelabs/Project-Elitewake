"""Play-mode preview and clearance check for the three sheltered sea caverns.

Run after rebuild_world.py on Lvl_CoastalPlayground with run_play_check.py and one
player. Writes Saved/SeaCavernsPlayResult.json and six fixed-direction screenshots
in Saved/Screenshots/SeaCaverns. This checks the generated terrain and cave actors;
a human must still sail a real ship through each entrance and judge visibility.
"""
import json
import math
import sys
import time
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

ROOT = Path(unreal.Paths.project_saved_dir())
RESULT = ROOT / 'SeaCavernsPlayResult.json'
SHOTS = ROOT / 'Screenshots' / 'SeaCaverns'
SHOTS.mkdir(parents=True, exist_ok=True)
world = next(w for w in unreal.EWEditorVerificationLibrary.get_play_worlds()
             if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
keys = tuple(W.CRESCENT_COVES)
actors = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)}
report = {'map': '/Game/Elitewake/Maps/Lvl_CoastalPlayground', 'caverns': {}, 'screenshots': [],
          'error': None, 'success': False}
views = []


def inspect(key):
    cave = T.CAVES[key]
    label = f'Cave of {key}: rock'
    actor = actors.get(label)
    assert actor, f'{label} is missing from the Play map'
    assert actor.static_mesh_component.get_editor_property('static_mesh'), f'{label} has no mesh'
    origin, extent = actor.get_actor_bounds(False)
    assert math.hypot(actor.get_actor_location().x - cave.mx, actor.get_actor_location().y - cave.my) < 100
    assert extent.x > 3000 and extent.y > 3000, f'{label} is too small for a covered boat berth'
    samples = []
    for u in (-5000.0, -3000.0, 0.0, cave.length / 2, cave.chamber_u):
        x, y = cave.world(u, cave.centre_v(max(0.0, u)))
        depth = T.SEA - T.built_height(x, y)
        samples.append({'metres_in': round(u / 100), 'depth_m': round(depth / 100, 2)})
        assert depth >= 450, f'{key}: only {depth / 100:.1f} m of water at {u / 100:.0f} m'
    report['caverns'][key] = {'actor': label, 'water_depths': samples,
                              'entrance_width_m': round(2 * cave.tunnel[0] / 100),
                              'chamber_length_m': round(2 * cave.chamber[0] / 100),
                              'chamber_width_m': round(2 * cave.chamber[1] / 100),
                              'overhead_clearance_m': round((cave.tunnel[1] + cave.tunnel[2] + cave.floor - T.SEA) / 100)}
    a = cave.heading + math.pi  # from the sea, looking into the mouth
    x, y = cave.world(-9000, 0)
    views.append((key, 'approach', x, y, T.SEA + 700, math.degrees(a), -2.0))
    x, y = cave.world(cave.chamber_u, 0)
    views.append((key, 'inside', x, y, T.SEA + 500, math.degrees(a), 0.0))


state = {'view': 0, 'phase': 'place', 'at': 0.0, 'handle': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error,
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SeaCaverns success={error is None} error={error}')


def tick(delta):
    try:
        if state['view'] >= len(views):
            finish()
            return
        key, view, x, y, z, yaw, pitch = views[state['view']]
        now = time.monotonic()
        if state['phase'] == 'place':
            pawn.teleport(unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
            state.update(phase='shoot', at=now + .6)
        elif state['phase'] == 'shoot' and now >= state['at']:
            shot = SHOTS / f'{key}_{view}.png'
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shot}"')
            report['screenshots'].append(str(shot))
            state.update(phase='saved', at=now + 2.0)
        elif state['phase'] == 'saved' and now >= state['at']:
            state.update(phase='place', view=state['view'] + 1)
    except Exception as exc:
        finish(repr(exc))


try:
    for key in keys:
        inspect(key)
except Exception as exc:
    report.update(error=repr(exc), finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SeaCaverns success=False error={exc!r}')
else:
    state['handle'] = unreal.register_slate_post_tick_callback(tick)
