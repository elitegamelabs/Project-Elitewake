"""Captures the HUD and the inventory at three interface sizes (Part 8, 62): 80%, 100% and 150%. One player:
    Scripts/Verification/run_play_check_once.ps1 -Check capture_interface_scale.py -Result InterfaceScaleCaptureResult.json -Players 1 -Standalone 1 -Kit 1
Saved/Screenshots/InterfaceScale/Hud_<size>.png, Menu_<size>.png. The saved size is put back afterwards. Visual review pending.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'InterfaceScale'
shots.mkdir(parents=True, exist_ok=True)
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
found = unreal.EWGameInstance.get_interface_scale()
steps = []
for size in (.8, 1.0, 1.5):
    steps += [(lambda s=size: unreal.EWGameInstance.set_interface_scale(s), 1.5),
              (lambda s=size: shot(f'Hud_{int(s * 100)}'), 1.0),
              (lambda: pc.set_inventory_open(True), 1.5),
              (lambda s=size: shot(f'Menu_{int(s * 100)}'), 1.0),
              (lambda: pc.set_inventory_open(False), 1.0)]
state = {'index': 0, 'at': time.monotonic() + 8, 'handle': None}


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / (name + ".png")}"')


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    unreal.EWGameInstance.set_interface_scale(found)
    (saved / 'InterfaceScaleCaptureResult.json').write_text(json.dumps({'success': error is None, 'error': error, 'restored': found}, indent=2))
    unreal.log(f'EWPLAYCHECK InterfaceScaleCapture success={error is None} error={error}')


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        if state['index'] >= len(steps):
            finish()
            return
        action, wait = steps[state['index']]
        action()
        state['index'] += 1
        state['at'] = time.monotonic() + wait
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
