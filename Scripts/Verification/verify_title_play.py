"""Play acceptance for splash -> main menu -> normal single-player coast."""
import json
import os
import shutil
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
result = saved / 'TitlePlayResult.json'
save_file = saved / 'SaveGames' / 'Survivor.sav'
save_backup = save_file.with_suffix('.sav.titlecheckbackup')
save_generated = save_file.with_suffix('.sav.titlecheckgenerated')
assert not save_backup.exists(), f'Previous title-check backup needs manual recovery: {save_backup}'
assert not save_generated.exists(), f'Previous title-check save needs manual recovery: {save_generated}'
if save_file.exists():
    save_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(save_file), str(save_backup))

checks = []
state = {'step': 'splash', 'deadline': time.monotonic() + 8.0, 'handle': None, 'memo': {}}


def worlds():
    return lib.get_play_worlds()


def title_pc():
    for world in worlds():
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        if isinstance(pc, unreal.EWTitlePlayerController):
            return pc
    return None


def current_survivor():
    for world in worlds():
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        if isinstance(pc, unreal.EWPlayerController):
            pawn = pc.get_controlled_pawn()
            if isinstance(pawn, unreal.EWCharacter):
                return world, pc, pawn
    return None


def finish(error=None):
    if state['handle'] is not None:
        unreal.unregister_slate_post_tick_callback(state['handle'])
        state['handle'] = None
    # Restore a real player's slot even when an assertion fails. Preserve any save created by the
    # test rather than deleting it if the startup flow unexpectedly writes one.
    if save_backup.exists():
        if save_file.exists():
            shutil.move(str(save_file), str(save_generated))
            error = error or f'Title flow unexpectedly wrote a save; preserved it at {save_generated.name}'
        shutil.move(str(save_backup), str(save_file))
    result.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error,
                                  'measured': state['memo']}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Title success={error is None} error={error}')


def tick(delta):
    try:
        step = state['step']
        if step == 'splash':
            pc = title_pc()
            if not pc:
                if time.monotonic() > state['deadline']:
                    raise TimeoutError('title controller did not appear')
                return
            title = pc.get_title_widget()
            if not (title and title.is_in_viewport() and title.is_splash_screen()):
                raise AssertionError('splash art is not the visible title screen')
            assert title.get_editor_property('art'), 'title art did not load'
            assert title.get_editor_property('prompt_art'), 'bottom-center prompt art did not load'
            state['title_pc'] = pc
            checks.append('Title art and Press Any Key prompt load on the splash screen')
            assert lib.send_verification_ui_key(pc, 'Enter'), 'could not send splash key input'
            state.update(step='menu', deadline=time.monotonic() + 5.0)
        elif step == 'menu':
            pc = title_pc()
            title = pc.get_title_widget() if pc else None
            if not (title and title.is_in_viewport() and title.is_main_menu_screen()):
                if time.monotonic() > state['deadline']:
                    raise TimeoutError('splash input did not advance to the main menu')
                return
            assert not title.is_multiplayer_available(), 'Multiplayer must remain unavailable'
            rect = title.get_single_player_button_rect()
            size = unreal.WidgetLayoutLibrary.get_viewport_size(pc) / unreal.WidgetLayoutLibrary.get_viewport_scale(pc)
            x, y, width, height = rect.x, rect.y, rect.z, rect.w
            assert width > 0 and height > 0, f'Single Player panel has no visible bounds: {rect}'
            centre = [(x + width / 2) / size.x, (y + height / 2) / size.y]
            assert .2 < centre[0] < .36 and .40 < centre[1] < .72, f'Single Player panel moved unexpectedly: {centre}'
            state['memo']['single_player_panel_centre'] = [round(v, 3) for v in centre]
            checks.append('Splash input opens the two-panel menu with Single Player in its expected panel')
            # Native EW.Title routed-input automation separately verifies a real pointer click inside this
            # rectangle and rejects keyboard/wheel input on the menu and clicks on disabled Multiplayer.
            title.start_single_player()
            state.update(step='coast', deadline=time.monotonic() + 20.0)
        elif step == 'coast':
            found = current_survivor()
            if not found:
                if time.monotonic() > state['deadline']:
                    raise TimeoutError('Single Player did not load a normal survivor on the coastal map')
                return
            world, _, pawn = found
            path = world.get_outer().get_path_name()
            assert 'Lvl_CoastalPlayground' in path, f'Single Player loaded an unexpected world: {path}'
            state['memo']['world'] = path
            state['memo']['survivor'] = pawn.get_name()
            checks.append('Single Player opens the coastal map with a normal playable survivor')
            finish()
    except Exception as error:
        finish(f'{state["step"]}: {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
