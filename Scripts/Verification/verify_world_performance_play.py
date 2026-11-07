"""How fast the bigger world draws (October 15 night: islands 3x wider, about 10,000 trees, 6,500 plants, 3,200 rocks
and 1.8 million grass blades, no World Partition). Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground with one
survivor (EW_PLAY_PLAYERS=1). Run unattended with run_play_check.py.

At each place the survivor stands looking inland for 5 s after settling, and the average frame time is measured;
a screenshot of each goes to Saved/Screenshots/WorldPerformance/. It passes when every place averages at least
MIN_FPS. Measured in the editor's Play window on this PC, so it is a warning light, not a promise for players' PCs.
Writes Saved/WorldPerformancePlayResult.json.
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

MIN_FPS = 30.0
lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'WorldPerformancePlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'WorldPerformance')
SHOTS.mkdir(parents=True, exist_ok=True)
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()


def inland_of(key, fraction):
    """A place on an island part-way in from its shore (toward the world's centre), facing its middle."""
    i = W.island(key)
    a = math.atan2(-i.cy, -i.cx) if (i.cx or i.cy) else 0.0
    r = i.radius(a) * fraction
    x, y = i.cx + r * math.cos(a), i.cy + r * math.sin(a)
    return x, y, math.degrees(a + math.pi)


def biggest(region):
    return max((i for i in W.ISLANDS if i.region == region), key=lambda i: i.rx * i.ry).key


PLACES = [('starter_beach', (150.0, 0.0, 180.0))] + [
    (f'{region.lower()}_{key}', inland_of(key, .55)) for region, key in
    (('Jungle', biggest('Jungle')), ('Winter', biggest('Winter')), ('Plains', W.PORTS['Plains'].island.key))]
state = {'index': 0, 'phase': 'place', 'at': time.monotonic(), 'frames': [], 'handle': None}
measured = {}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    slow = {k: v for k, v in measured.items() if v['fps'] < MIN_FPS}
    if error is None and slow:
        error = f'below {MIN_FPS:.0f} fps: {slow}'
    RESULT.write_text(json.dumps({'success': error is None, 'checks': list(measured), 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK WorldPerformance success={error is None} {measured}')


def tick(delta):
    try:
        if state['index'] >= len(PLACES):
            finish()
            return
        name, (x, y, yaw) = PLACES[state['index']]
        now = time.monotonic()
        if state['phase'] == 'place':
            z = max(T.height(x, y), T.SEA) + 120
            assert pawn.teleport(unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw)), f'no room at {name}'
            pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=yaw))
            state.update(phase='settle', at=now + 4.0)
        elif state['phase'] == 'settle' and now >= state['at']:
            state.update(phase='measure', at=now + 5.0, frames=[])
        elif state['phase'] == 'measure':
            state['frames'].append(delta)
            if now >= state['at']:
                frames = sorted(state['frames'])
                avg = sum(frames) / len(frames)
                measured[name] = {'fps': round(1.0 / avg, 1), 'worst_ms': round(frames[-1] * 1000, 1),
                                  'p95_ms': round(frames[int(len(frames) * .95) - 1] * 1000, 1), 'frames': len(frames)}
                unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (name + ".png")}"')
                state.update(phase='place', index=state['index'] + 1, at=now + 1.0)
    except Exception as error:
        finish(repr(error))


settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
state['handle'] = unreal.register_slate_post_tick_callback(tick)
