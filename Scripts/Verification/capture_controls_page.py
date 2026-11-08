"""Capture the Options' Controls page for keyboard and for a controller (owner, November 7). Single player on the coast:
    Scripts/Verification/run_play_check_once.ps1 -Check capture_controls_page.py -Result ControlsCaptureResult.json -Players 1 -Standalone 1
Screenshots (with the interface) in Saved/Screenshots/Controls.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
SHOTS = saved / 'Screenshots' / 'Controls'
SHOTS.mkdir(parents=True, exist_ok=True)
state = {'step': 0, 'at': time.monotonic() + 8.0, 'h': None}
report = {'shots': []}


def pc():
    return unreal.GameplayStatics.get_player_controller(lib.get_play_worlds()[0], 0)


def key(name):
    assert lib.send_verification_ui_key(pc(), name), name


def shot(name):
    unreal.SystemLibrary.execute_console_command(pc().get_world(), f'Shot showui filename="{SHOTS / (name + ".png")}"')
    report['shots'].append(name)


STEPS = [
    lambda: pc().set_options_menu_open(True),
    lambda: (key('Down'), key('Down'), key('Enter')),          # OPTIONS
    lambda: [key('Down') for _ in range(15)] and key('Enter'),  # CONTROLS
    lambda: key('Up'),                                          # a keyboard key: keyboard view
    lambda: shot('Controls_Keyboard'),
    lambda: key('Gamepad_DPad_Up'),                             # a controller button: controller view
    lambda: shot('Controls_Controller'),
    lambda: None,
]


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        STEPS[state['step']]()
        state['step'] += 1
        state['at'] = time.monotonic() + 1.5
        if state['step'] == len(STEPS):
            finish()
    except Exception as e:      # noqa: BLE001
        finish(repr(e))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    (saved / 'ControlsCaptureResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ControlsCapture success={error is None} error={error}')


state['h'] = unreal.register_slate_post_tick_callback(tick)
