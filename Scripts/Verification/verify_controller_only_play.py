"""Play: the game from a controller alone (November 7, controller-complete play; CLAUDE.md 6.5). Single player on the coast,
with the test starter kit (EW_PLAY_STARTER_KIT=1). Every input below is a controller button or stick, sent through the
game's real input path; nothing uses the keyboard or mouse:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_controller_only_play.py -Result ControllerOnlyPlayResult.json -Players 1 -Standalone 1 -Kit 1
  move (left stick), look (right stick), jump (A), sprint (click the left stick), crouch (tap B), prone (hold B), up from prone (tap, tap),
  first / third person (click the right stick), hotbar slots 1-4 (d-pad) and 5-8 (LB + X/Y/B/A), interact (X),
  inventory (Y opens, B closes), map (View opens, B closes), pause (Menu opens, B closes), Build Mode (LB + d-pad right
  enters with the piece wheel open, A chooses, d-pad right turns the piece, R3 demolish, B leaves).
Writes Saved/ControllerOnlyPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ControllerOnlyPlayResult.json')
T = '/Game/Elitewake/Items/Testing'
EXTRA = [unreal.load_asset(f'{T}/DA_Test{n}') for n in ('Stone', 'Wood', 'Fiber', 'Sticks')]
checks, memo = [], {}
state = {'i': 0, 'started': False, 'deadline': 0.0, 'h': None, 't0': 0.0}


def world():
    return lib.get_play_worlds()[0]


def pc():
    return unreal.GameplayStatics.get_player_controller(world(), 0)


def me():
    return pc().get_controlled_pawn()


HELD = set()


def press(key):
    assert lib.send_verification_gameplay_key_state(pc(), key, True), key
    HELD.add(key)


def release(key):
    assert lib.send_verification_gameplay_key_state(pc(), key, False), key
    HELD.discard(key)


def release_all():
    """A step can finish the moment the game reacts, before its button is let go: let go of everything first."""
    for key in list(HELD):
        release(key)


def axis(key, value):
    assert lib.send_verification_gameplay_axis(pc(), key, value), key


def ui(key):
    assert lib.send_verification_ui_key(pc(), key), key


def flag(obj, name):
    """A yes/no state whether Python shows it as a function or as the property behind it (bIsSprinting, bIsProne...)."""
    value = getattr(obj, name)
    return value() if callable(value) else bool(value)


def elapsed():
    return time.monotonic() - state['t0']


# Each step: (label, start (once), until (each tick, True when done), seconds allowed).
def ready_start():
    pass


def ready():
    p = me()
    if not isinstance(p, unreal.EWCharacter):
        return False
    memo['start'] = p.get_actor_location()
    # All eight hotbar slots hold something: the kit's tools, then four resources.
    inv, bar = p.get_inventory_component(), p.get_hotbar_component()
    for item in EXTRA:
        inv.add_item(item, 3)
    kit = [unreal.load_asset(f'{T}/DA_Test{n}') for n in ('WoodenAxe', 'WoodenPickaxe', 'HideWaterFlask', 'InnTorch')]
    owned = [i for i in kit + EXTRA if i and inv.get_item_count(i) > 0]
    memo['owned'] = [i.get_name() for i in owned]
    bound = 0
    for slot, item in enumerate(owned[:8]):
        bar.bind_item(slot, item)
        bound += 1
    memo['bound'] = bound
    return True


def move_start():
    memo['before_move'] = me().get_actor_location()


def moving():
    axis('Gamepad_LeftY', 1.0)
    if elapsed() < 1.5:
        return False
    axis('Gamepad_LeftY', 0.0)
    d = me().get_actor_location() - memo['before_move']
    memo['moved_cm'] = round((d.x ** 2 + d.y ** 2) ** .5)
    assert memo['moved_cm'] > 100, f'the left stick moved the survivor only {memo["moved_cm"]} cm'
    return True


def look_start():
    memo['yaw'] = pc().get_control_rotation().yaw


def looking():
    axis('Gamepad_RightX', 1.0)
    if elapsed() < .6:
        return False
    axis('Gamepad_RightX', 0.0)
    turned = abs(((pc().get_control_rotation().yaw - memo['yaw']) + 180) % 360 - 180)
    memo['turned_deg'] = round(turned, 1)
    assert turned > 10, f'the right stick turned the view only {turned:.1f} degrees'
    return True


def jump_start():
    memo['z'] = me().get_actor_location().z
    press('Gamepad_FaceButton_Bottom')


def jumped():
    if elapsed() > .1:
        release('Gamepad_FaceButton_Bottom')
    if me().get_movement_component().is_falling() or me().get_actor_location().z > memo['z'] + 20:
        release('Gamepad_FaceButton_Bottom')
        return True
    return False


def sprint_start():
    press('Gamepad_LeftThumbstick')


def sprinting():
    axis('Gamepad_LeftY', 1.0)
    if elapsed() > .1:
        release('Gamepad_LeftThumbstick')
    if flag(me(), 'is_sprinting'):
        memo['sprint_speed'] = round(me().get_velocity().length())
        return True
    return False


def sprint_stop_start():
    axis('Gamepad_LeftY', 0.0)


def sprint_stopped():
    axis('Gamepad_LeftY', 0.0)
    return not flag(me(), 'is_sprinting') and me().get_velocity().length() < 50


def crouch_start():
    press('Gamepad_FaceButton_Right')


def crouched():
    if elapsed() > .1 and not memo.get('crouch_released'):
        release('Gamepad_FaceButton_Right')
        memo['crouch_released'] = True
    return me().get_editor_property('bIsCrouched')


def stand_start():
    press('Gamepad_FaceButton_Right')


def stood():
    if elapsed() > .1 and not memo.get('stand_released'):
        release('Gamepad_FaceButton_Right')
        memo['stand_released'] = True
    return memo.get('stand_released') and not me().get_editor_property('bIsCrouched')


def prone_start():
    press('Gamepad_FaceButton_Right')


def prone():
    if elapsed() > .8 and not memo.get('prone_released'):
        release('Gamepad_FaceButton_Right')
        memo['prone_released'] = True
    return memo.get('prone_released') and flag(me(), 'is_prone')


def up_start():
    memo['up_phase'] = 0


def up():
    """From prone a tap of B rises to a crouch, and another tap stands (as on the keyboard)."""
    phase, t = memo['up_phase'], elapsed()
    if phase == 0:
        press('Gamepad_FaceButton_Right'); memo['up_phase'] = 1
    elif phase == 1 and t > .1:
        release('Gamepad_FaceButton_Right'); memo['up_phase'] = 2
    elif phase == 2 and not flag(me(), 'is_prone') and me().get_editor_property('bIsCrouched'):
        press('Gamepad_FaceButton_Right'); memo['up_phase'] = 3; memo['up_t'] = t
    elif phase == 3 and t > memo['up_t'] + .1:
        release('Gamepad_FaceButton_Right'); memo['up_phase'] = 4
    elif phase == 4 and not me().get_editor_property('bIsCrouched') and not flag(me(), 'is_prone'):
        return True
    return False


def view_start():
    memo['first_person'] = flag(me(), 'is_first_person')
    press('Gamepad_RightThumbstick')


def view_toggled():
    if elapsed() > .1:
        release('Gamepad_RightThumbstick')
    return flag(me(), 'is_first_person') != memo['first_person']


def view_back_start():
    press('Gamepad_RightThumbstick')


def view_back():
    if elapsed() > .1:
        release('Gamepad_RightThumbstick')
    return flag(me(), 'is_first_person') == memo['first_person']


SLOT_KEYS = [(None, 'Gamepad_DPad_Left'), (None, 'Gamepad_DPad_Up'), (None, 'Gamepad_DPad_Right'), (None, 'Gamepad_DPad_Down'),
             ('Gamepad_LeftShoulder', 'Gamepad_FaceButton_Left'), ('Gamepad_LeftShoulder', 'Gamepad_FaceButton_Top'),
             ('Gamepad_LeftShoulder', 'Gamepad_FaceButton_Right'), ('Gamepad_LeftShoulder', 'Gamepad_FaceButton_Bottom')]


def hotbar_start():
    memo['slots'] = []
    memo['slot'] = 0
    memo['slot_at'] = 0.0


def hotbar():
    """Each slot in turn: press its button (with LB held for 5-8), release, and read the selected slot."""
    i = memo['slot']
    bar = me().get_hotbar_component()
    if i == len(SLOT_KEYS):
        expected = list(range(min(8, memo['bound'])))
        assert memo['slots'][:len(expected)] == expected, f'the controller selected slots {memo["slots"]}, expected {expected}'
        return True
    held, button = SLOT_KEYS[i]
    phase = memo.get('slot_phase', 0)
    if phase == 0:
        if held:
            press(held)
        press(button)
        memo['slot_phase'] = 1
    elif phase == 1:
        release(button)
        if held:
            release(held)
        memo['slot_phase'] = 2
    else:
        memo['slots'].append(bar.get_selected_slot())
        memo['slot'] = i + 1
        memo['slot_phase'] = 0
    return False


def pickup_start():
    """A test interactable at eye height straight ahead, the view level (as verify_interaction_play places it)."""
    p = me()
    yaw = pc().get_control_rotation().yaw
    pc().set_control_rotation(unreal.Rotator(0, 0, yaw))
    forward = unreal.MathLibrary.get_forward_vector(unreal.Rotator(0, 0, yaw))
    memo['target'] = lib.spawn_verification_interactable(world(), p.get_actor_location() + forward * 150 + unreal.Vector(0, 0, 64), False, False, False, 1.0)
    assert memo['target'], 'no test interactable'


def picked():
    """X uses what the survivor faces."""
    t = elapsed()
    if t > .5 and not memo.get('x_pressed'):
        memo['prompt'] = str(pc().get_interaction_widget().get_displayed_prompt())
        press('Gamepad_FaceButton_Left')
        memo['x_pressed'] = t
    if memo.get('x_pressed') and t > memo['x_pressed'] + .15 and not memo.get('x_released'):
        release('Gamepad_FaceButton_Left')
        memo['x_released'] = True
    count = memo['target'].get_acknowledgement_count()
    if count > 0:
        memo['interactions'] = count
        memo['target'].destroy_actor()
        return True
    if t > 4:
        raise AssertionError(f"X did not interact; the prompt read: {memo.get('prompt')!r}")
    return False


def inventory_start():
    pc().set_control_rotation(unreal.Rotator(0, 0, pc().get_control_rotation().yaw))
    press('Gamepad_FaceButton_Top')


def inventory_open():
    if elapsed() > .1:
        release('Gamepad_FaceButton_Top')
    return pc().is_inventory_open()


def inventory_close_start():
    ui('Gamepad_FaceButton_Right')


def inventory_closed():
    return not pc().is_inventory_open()


def map_start():
    press('Gamepad_Special_Left')


def map_open():
    if elapsed() > .1:
        release('Gamepad_Special_Left')
    return pc().is_map_open()


def map_close_start():
    press('Gamepad_FaceButton_Right')


def map_closed():
    if elapsed() > .1:
        release('Gamepad_FaceButton_Right')
    return not pc().is_map_open()


def pause_start():
    press('Gamepad_Special_Right')


def paused():
    if elapsed() > .1:
        release('Gamepad_Special_Right')
    return pc().is_options_menu_open()


def unpause_start():
    ui('Gamepad_FaceButton_Right')


def unpaused():
    return not pc().is_options_menu_open()


def build_start():
    press('Gamepad_LeftShoulder')
    press('Gamepad_DPad_Right')


def build_on():
    if elapsed() > .1 and not memo.get('build_released'):
        release('Gamepad_DPad_Right')
        release('Gamepad_LeftShoulder')
        memo['build_released'] = True
    b = pc().get_build_component()
    if b.get_mode() != unreal.EWBuildMode.OFF:
        assert b.is_dial_open(), 'entering Build Mode did not open the piece wheel at once'
        return True
    return False


def choose_start():
    press('Gamepad_FaceButton_Bottom')


def chosen():
    if elapsed() > .1:
        release('Gamepad_FaceButton_Bottom')
    return not pc().get_build_component().is_dial_open()


def demolish_start():
    press('Gamepad_RightThumbstick')


def demolishing():
    if elapsed() > .1:
        release('Gamepad_RightThumbstick')
    perspective_kept = flag(me(), 'is_first_person') == memo['first_person']
    if pc().get_build_component().get_mode() == unreal.EWBuildMode.DEMOLISH:
        assert perspective_kept, 'R3 in Build Mode also switched the camera'
        return True
    return False


def leave_start():
    press('Gamepad_FaceButton_Right')


def left():
    if elapsed() > .1:
        release('Gamepad_FaceButton_Right')
    b = pc().get_build_component()
    if b.get_mode() == unreal.EWBuildMode.OFF:
        return True
    if elapsed() > .5 and not memo.get('second_b'):          # B closes a wheel first; B again leaves
        press('Gamepad_FaceButton_Right')
        memo['second_b'] = elapsed()
    if memo.get('second_b') and elapsed() > memo['second_b'] + .1:
        release('Gamepad_FaceButton_Right')
    return False


STEPS = [
    ('Single player on the coast with the kit', ready_start, ready, 30),
    ('X interacts with what the survivor faces', pickup_start, picked, 6),
    ('Left stick moves the survivor', move_start, moving, 6),
    ('Right stick turns the view', look_start, looking, 4),
    ('A jumps', jump_start, jumped, 3),
    ('Clicking the left stick sprints', sprint_start, sprinting, 4),
    ('Letting the stick go stops the sprint', sprint_stop_start, sprint_stopped, 6),
    ('Tapping B crouches', crouch_start, crouched, 3),
    ('Tapping B again stands', stand_start, stood, 3),
    ('Holding B lies prone', prone_start, prone, 4),
    ('From prone, a tap of B crouches and another stands', up_start, up, 5),
    ('Clicking the right stick switches first / third person', view_start, view_toggled, 3),
    ('Clicking it again switches back', view_back_start, view_back, 3),
    ('The d-pad selects hotbar slots 1-4 and LB + X/Y/B/A slots 5-8', hotbar_start, hotbar, 10),
    ('Y opens the inventory', inventory_start, inventory_open, 3),
    ('B closes the inventory', inventory_close_start, inventory_closed, 3),
    ('View opens the map', map_start, map_open, 3),
    ('B closes the map', map_close_start, map_closed, 3),
    ('Menu pauses', pause_start, paused, 3),
    ('B resumes', unpause_start, unpaused, 3),
    ('LB + d-pad right enters Build Mode with the piece wheel open', build_start, build_on, 3),
    ('A chooses a piece and closes the wheel', choose_start, chosen, 3),
    ('Clicking the right stick in Build Mode demolishes (not the camera)', demolish_start, demolishing, 3),
    ('B leaves Build Mode', leave_start, left, 4),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    clean = {k: (str(v) if not isinstance(v, (int, float, str, list, bool, type(None))) else v) for k, v in memo.items()}
    RESULT.write_text(json.dumps({'success': error is None, 'error': error, 'checks': checks, 'measured': clean}, indent=2))
    unreal.log(f'EWPLAYCHECK ControllerOnly success={error is None} error={error}')


def tick(_):
    try:
        label, start, until, seconds = STEPS[state['i']]
        if not state['started']:
            # Let go of everything, then wait a moment, so the next press is seen as a new press.
            if HELD:
                release_all()
                state['gap'] = time.monotonic() + .15
            if time.monotonic() < state.get('gap', 0.0):
                return
            state.update(started=True, deadline=time.monotonic() + seconds, t0=time.monotonic())
            start()
        if until():
            checks.append(label)
            state.update(i=state['i'] + 1, started=False)
            if state['i'] == len(STEPS):
                finish()
            return
        if time.monotonic() > state['deadline']:
            raise TimeoutError('timed out')
    except Exception as error:      # noqa: BLE001
        finish(f'step {state["i"] + 1} ({STEPS[state["i"]][0]}): {error!r}')


state['h'] = unreal.register_slate_post_tick_callback(tick)
