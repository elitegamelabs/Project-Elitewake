"""Arrival evidence captures (CLAUDE.md Phase 1, slice 1; sections 9.4 and 12): pictures to review, not pass/fail.
Run through run_play_check.py on /Game/Elitewake/Maps/Lvl_CoastalPlayground with EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1920x1080,
EW_PLAY_RESULT=ArrivalCaptures.json. Late morning is 10.5, night 22.0 (as the Phase 0 baseline). Writes
Saved/Screenshots/Arrival/*.png.

  01 gameplay camera at the spawn, with the HUD, as the survivor arrives;
  02 the same a few seconds later, with the arrival's one prompt;
  03 / 04 the 70-degree eye-level view from the spawn, late morning / night, no UI;
  05 the old east-beach spawn from the same 70-degree eye-level camera (the "before");
  06 25 m along the track looking on toward Saltreach (human scale), no UI;
  07 the spring from 3 m (interaction scale), no UI;
  08 the reverse view from the spawn, back along the beach, no UI;
  09 diagnostic: straight down from 60 m over the spawn, track, spring and oaks.
There is no Plains weather to capture (only the Winter's snowfall exists).
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import arrival_layout as A  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'Arrival'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
clock = unreal.EWDayNightSubsystem.get_for_world(world)
report = {'shots': [], 'notes': []}
cam = {}
EYE = 170.0
DAY, NIGHT = 10.5, 22.0


def shot(name, ui):
    unreal.SystemLibrary.execute_console_command(world, f'Shot {"showui " if ui else ""}filename="{shots / (name + ".png")}"')
    report['shots'].append(name + '.png')
    return 1.5


def hour(h):
    clock.set_hour(h)
    report['notes'].append(f'hour {h}')
    return 4.0


def make_camera():
    cam['a'] = lib.spawn_verification_camera(pc, pawn.get_actor_location(), pawn.get_actor_rotation(), 70.0)


def place(x, y, z, yaw, pitch=-1.0, park=True):
    if park:   # the survivor waits a few metres behind, so the world streams in round the camera
        b = math.radians(yaw)
        pawn.teleport(unreal.Vector(x - 600 * math.cos(b), y - 600 * math.sin(b), T.height(x, y) + 120), unreal.Rotator(0, 0, yaw))
    cam['a'].set_actor_location_and_rotation(unreal.Vector(x, y, z), unreal.Rotator(0, pitch, yaw), False, False)
    pc.set_view_target_with_blend(cam['a'], 0.0)
    return 5.0


def eye(x, y):
    return T.height(x, y) + EYE


def gameplay_view():
    report['notes'].append(f'arrival prompt visible in 01: {bool(pc.get_arrival_prompt_widget().is_prompt_visible())}')


def prompt_view():
    report['notes'].append(f'arrival prompt in 02: {str(pc.get_arrival_prompt_widget().get_displayed_prompt())!r}')


sx, sy = A.SPAWN
route = A.smoothed_route()
along = next(p for p in route if math.hypot(p[0] - sx, p[1] - sy) >= 2500)
ahead = next(p for p in route if math.hypot(p[0] - sx, p[1] - sy) >= 6000)
spring_yaw = A.bearing(sx, sy, *A.SPRING)
steps = [
    lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'),
    lambda: hour(DAY),
    gameplay_view, lambda: shot('01_arrival_gameplay_day', True),
    lambda: 4.0,
    prompt_view, lambda: shot('02_arrival_gameplay_day_prompt', True),
    make_camera,
    lambda: place(sx, sy, eye(sx, sy), A.SPAWN_YAW), lambda: shot('03_arrival_eye70_day', False),
    lambda: hour(NIGHT), lambda: shot('04_arrival_eye70_night', False), lambda: hour(DAY),
    lambda: place(150.0, 0.0, eye(150.0, 0.0), 0.0), lambda: shot('05_old_spawn_eye70_day_before', False),
    lambda: place(along[0], along[1], eye(*along), A.bearing(along[0], along[1], *ahead)), lambda: shot('06_track_25m_day', False),
    lambda: place(A.SPRING[0] - 300 * math.cos(math.radians(spring_yaw)), A.SPRING[1] - 300 * math.sin(math.radians(spring_yaw)),
                  eye(*A.SPRING), spring_yaw, -28.0), lambda: shot('07_spring_3m_day', False),
    lambda: place(sx, sy, eye(sx, sy), A.SPAWN_YAW + 180.0), lambda: shot('08_arrival_reverse_day', False),
    lambda: place(sx - 1500, sy + 600, T.height(sx, sy) + 6000, A.SPAWN_YAW, -89.0), lambda: shot('09_diagnostic_topdown_60m', False),
    lambda: pc.set_view_target_with_blend(pawn, 0.0),
]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    (saved / 'ArrivalCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWARRIVALCAPTURE success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(steps):
            finish()
            return
        wait = steps[state['i']]()
        state['i'] += 1
        state['at'] = time.monotonic() + (wait if isinstance(wait, float) else .5)
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
