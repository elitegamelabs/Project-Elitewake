"""Controller button icons, evidence captures (owner, November 1): the same prompts drawn for the keyboard, an Xbox pad and a
PlayStation pad. Run through run_play_check_once.ps1 on /Game/Elitewake/Maps/Lvl_CoastalPlayground:
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check capture_controller_icons.py -Result ControllerIconsCaptures.json -Players 1 -Window 1920x1080
Writes Saved/Screenshots/ControllerIcons/*.png. The Options choice is set for the session only (not saved), so the captures do
not depend on which pad is plugged in. Checks the words behind each picture: the arrival prompt and the build hint name the
pad's own buttons and never mix the families. 'success' covers those words; the pictures are for owner visual review.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'ControllerIcons'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
report = {'shots': [], 'words': {}}
Choice = unreal.EWButtonIconsChoice
XBOX_WORDS = ('LB', 'RB', 'A:', 'B:', 'X:', 'Y,')
PLAYSTATION_WORDS = ('L1', 'R1', 'Cross', 'Circle', 'Square', 'Triangle')


def hotbar():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWHotbarWidget, False) if w.is_in_viewport())


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / (name + ".png")}"')
    report['shots'].append(name + '.png')
    return 1.5


def use(device, choice=None):
    def go():
        if choice is not None:
            pc.set_button_icons_choice(choice, False)
        # A key from the device marks it as the one in use (AEWPlayerController::RecordInputDevice).
        lib.send_verification_gameplay_key(pc, 'Gamepad_RightThumbstick' if device == 'pad' else 'LeftShift')   # unused on foot: only the device counts
        return 2.0
    return go


def read(name, want, forbid):
    def go():
        arrival = str(pc.get_arrival_prompt_widget().get_displayed_prompt())
        build = str(hotbar().get_build_hint())
        report['words'][name] = {'arrival': arrival, 'build_hint': build, 'hotbar_icons': hotbar().get_shown_icon_family()}
        assert build == want, f'{name}: build hint {build!r}, expected {want!r}'
        joined = arrival + ' ' + build
        assert not any(w in joined for w in forbid), f'{name}: the other family shows in {joined!r}'
        return .5
    return go


steps = [lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'), lambda: 3.0,
         use('keys'), read('keyboard', 'Build: B', ()), lambda: shot('01_keyboard'),
         use('pad', Choice.XBOX), read('xbox', 'Build: hold LB + D-pad Right', PLAYSTATION_WORDS), lambda: shot('02_xbox'),
         use('pad', Choice.PLAY_STATION), read('playstation', 'Build: hold L1 + D-pad Right', XBOX_WORDS), lambda: shot('03_playstation'),
         lambda: pc.set_button_icons_choice(Choice.AUTOMATIC, False)]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    (saved / 'ControllerIconsCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWCONTROLLERICONS success={error is None} error={error}')


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
