"""Verify splash -> main menu -> Single Player -> regular coastal survivor.

Run in one-player Play from /Game/Elitewake/Maps/Lvl_Title using run_play_check.py.
Writes Saved/TitleToCoastPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
RESULT = saved / 'TitleToCoastPlayResult.json'
checks = []
state = {'step': 0, 'deadline': time.monotonic() + 60, 'handle': None}


def world():
    worlds = lib.get_play_worlds()
    return worlds[0] if worlds else None


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK TitleToCoast success={error is None} error={error}')


def tick(delta):
    try:
        w = world()
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if state['step'] == 0 and isinstance(pc, unreal.EWTitlePlayerController) and pc.get_title_widget():
            title = pc.get_title_widget()
            assert title.is_splash_screen(), str(title.get_screen())
            assert title.get_editor_property('art')
            assert title.get_editor_property('logo_art')
            assert title.get_editor_property('prompt_art')
            title.start_journey()
            state['step'] = 1
        elif state['step'] == 1 and isinstance(pc, unreal.EWTitlePlayerController):
            title = pc.get_title_widget()
            if title and title.is_main_menu_screen():
                assert title.get_editor_property('main_menu_art')
                assert not title.is_multiplayer_available()
                checks.append('Any key advances the splash to the menu; Multiplayer reports disabled')
                title.start_single_player()
                checks.append('Single Player starts directly without the character creator')
                state['step'] = 2
        elif state['step'] == 2 and pc and not isinstance(pc, unreal.EWTitlePlayerController) and pc.get_controlled_pawn():
            pawn = pc.get_controlled_pawn()
            assert 'Lvl_CoastalPlayground' in w.get_path_name(), w.get_path_name()
            assert isinstance(pawn, unreal.EWCharacter), pawn.get_class().get_path_name()
            checks.append('The coastal map opens with the normal EW survivor pawn')
            finish()
            return
        if time.monotonic() > state['deadline']:
            raise TimeoutError(f'stuck at step {state["step"]}')
    except Exception as error:
        finish(f'step {state["step"]}: {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
