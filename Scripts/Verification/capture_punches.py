"""Bare-hand punch pictures for owner review (owner, November 3): one player, so the screen is the puncher's.
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check capture_punches.py -Result PunchCaptures.json -Players 1 -Standalone 1 -Window 1920x1080
Third person from behind and from the side, and first person, each arm at its reach (the hooks about 0.4 s in, the
first-person jabs 0.3 s in). Writes Saved/Screenshots/Punches/*.png and Saved/PunchCaptures.json. verify_punches_play.py
checks the buttons, arms and what each machine shows.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'Punches'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
SPOT = unreal.Vector(150, 0, 120)
report = {'shots': [], 'played': []}


def setup(first, yaw):
    def go():
        pawn.teleport(SPOT, unreal.Rotator(0, 0, 0))
        pawn.set_first_person_view(first)
        pc.set_control_rotation(unreal.Rotator(0, -4 if first else -8, yaw))
        return 2.0
    return go


def punch(key, name, wait):
    def go():
        pawn.get_editor_property('mesh').get_anim_instance().montage_stop(0.0, None)
        lib.send_verification_gameplay_key(pc, key)
        return wait
    def shoot():
        unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / (name + ".png")}"')
        report['shots'].append(name + '.png')
        anim = pawn.get_last_swing_animation()
        report['played'].append({'shot': name, 'key': key, 'animation': anim.get_name() if anim else None})
        return 1.5
    return [go, shoot]


steps = [lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'),
         setup(False, 0.0), *punch('RightMouseButton', '01_third_behind_right', .40), *punch('LeftMouseButton', '02_third_behind_left', .45),
         setup(False, 75.0), *punch('RightMouseButton', '03_third_side_right', .40), *punch('LeftMouseButton', '04_third_side_left', .45),
         setup(True, 0.0), *punch('RightMouseButton', '05_first_right', .30), *punch('LeftMouseButton', '06_first_left', .30),
         setup(False, 0.0)]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    (saved / 'PunchCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPUNCHCAPTURE success={error is None} error={error}')


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
