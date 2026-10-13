"""Acceptance for the title screen and the character creator.

Needs Play in /Game/Elitewake/Maps/Lvl_Title with one player (Scripts/Setup/build_title.py). Run unattended with
run_play_check.py and EW_PLAY_PLAYERS=1.

  1. The title art fills the screen and "Start your journey" sits in the upper middle of it, as painted.
  2. Enter starts the journey: after the fade, the character creator shows, with every body and colouring in the
     roster on offer, and the survivor stands on the dock in front of the creator camera.
  3. Choosing the woman, the fifth colouring and a taller height changes the survivor shown.
  4. Back returns to the title; starting again comes back to the creator.
  5. Set Sail keeps the chosen look in the game instance (the test stays on the title map instead of sailing).
Writes Saved/TitlePlayResult.json, then removes the saved look the test made.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'TitlePlayResult.json')
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
assert isinstance(pc, unreal.EWTitlePlayerController), f'not the title controller: {pc}'
roster = unreal.load_asset('/Game/Elitewake/Characters/DA_BodyRoster')
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def title_shown():
    title = pc.get_title_widget()
    if not title or not title.is_in_viewport():
        return False
    rect = title.get_start_button_rect()
    left, top, width, height = rect.x, rect.y, rect.z, rect.w
    size = unreal.WidgetLayoutLibrary.get_viewport_size(pc) / unreal.WidgetLayoutLibrary.get_viewport_scale(pc)
    if width <= 0:
        return False
    centre_x, centre_y = (left + width / 2) / size.x, (top + height / 2) / size.y
    assert .4 < centre_x < .6 and .25 < centre_y < .45, f'button centre at {centre_x:.2f}, {centre_y:.2f}'
    assert title.get_editor_property('art'), 'no title art'
    state['memo'].update(button_centre=[round(centre_x, 3), round(centre_y, 3)])
    return True


def press_enter():
    assert lib.send_verification_ui_key(pc, 'Enter')


def creator_shown():
    creator, preview = pc.get_creator_widget(), pc.get_preview()
    if not (creator and creator.is_in_viewport() and preview):
        return False
    assert creator.get_body_choice_count() == len(roster.get_editor_property('bodies'))
    assert creator.get_tone_choice_count() == len(roster.get_editor_property('tones'))
    view = pc.get_view_target()
    assert view and 'CreatorCamera' in [str(t) for t in view.tags], f'viewing {view}'
    assert preview.get_editor_property('body').get_editor_property('skeletal_mesh_asset'), 'the survivor has no body'
    assert pc.get_title_widget() is None or not pc.get_title_widget().is_in_viewport()
    return True


def customise():
    creator = pc.get_creator_widget()
    creator.select_body(1)
    creator.select_tone(4)
    for _ in range(3):
        creator.nudge_height(1)


def customised():
    creator, preview = pc.get_creator_widget(), pc.get_preview()
    look = creator.get_appearance()
    body = preview.get_editor_property('body')
    woman = roster.get_editor_property('bodies')[1].get_editor_property('mesh')
    assert look.body == 1 and look.tone == 4 and abs(look.height - 1.06) < .001, look
    assert body.get_editor_property('skeletal_mesh_asset') == woman, body.get_editor_property('skeletal_mesh_asset')
    assert abs(body.get_editor_property('relative_scale3d').z - 1.06) < .001
    state['memo']['look'] = [look.body, look.tone, round(look.height, 2)]
    return True


def back():
    pc.get_creator_widget().go_back()


def title_again():
    title = pc.get_title_widget()
    return bool(title and title.is_in_viewport() and not pc.get_preview())


def set_sail():
    pc.set_editor_property('stay_on_set_sail', True)
    creator = pc.get_creator_widget()
    creator.select_body(1)
    creator.select_tone(4)
    creator.set_sail()


def kept():
    instance = unreal.GameplayStatics.get_game_instance(world)
    if not (pc.has_set_sail() and instance.has_chosen_appearance()):
        return False
    look = instance.get_chosen_appearance()
    assert look.body == 1 and look.tone == 4, look
    return True


STEPS = [
    ('The title art fills the screen with "Start your journey" in the upper middle', lambda: None, title_shown, 6),
    ('Enter starts the journey: the creator offers every body and colouring, the survivor on the dock in view', press_enter, creator_shown, 5),
    ('Choosing the woman, the fifth colouring and +6% height changes the survivor shown', customise, customised, 3),
    ('Back returns to the title', back, title_again, 3),
    ('', press_enter, creator_shown, 5),
    ('Set Sail keeps the chosen look in the game instance', set_sail, kept, 3),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    # Leave no saved look behind: it would dress every later Play session.
    Path(unreal.Paths.project_saved_dir(), 'SaveGames', 'Appearance.sav').unlink(missing_ok=True)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': [c for c in checks if c], 'error': error,
                                  'measured': state['memo']}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Title success={error is None} error={error}')


def tick(delta):
    description, begin, done, timeout = STEPS[state['index']]
    try:
        if not state['begun']:
            begin()
            state.update(begun=True, deadline=time.monotonic() + timeout)
            return
        if done():
            checks.append(description)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
        elif time.monotonic() > state['deadline']:
            raise TimeoutError(f'not done within {timeout} s')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
