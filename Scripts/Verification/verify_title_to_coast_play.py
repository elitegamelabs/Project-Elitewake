"""End-to-end acceptance from the title screen to the coast.

Needs Play in /Game/Elitewake/Maps/Lvl_Title with one player. Run unattended with run_play_check.py.

  1. Start the journey from the title, choose the woman with the second colouring, and Set Sail.
  2. The coast loads, and the survivor there wears the chosen look.
Writes Saved/TitleToCoastPlayResult.json, then removes the saved look the test made.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
RESULT = saved / 'TitleToCoastPlayResult.json'
roster = unreal.load_asset('/Game/Elitewake/Characters/DA_BodyRoster')
woman = roster.get_editor_property('bodies')[1].get_editor_property('mesh')
checks = []
state = {'step': 0, 'deadline': time.monotonic() + 30, 'handle': None}


def world():
    worlds = lib.get_play_worlds()
    return worlds[0] if worlds else None


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    (saved / 'SaveGames' / 'Appearance.sav').unlink(missing_ok=True)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK TitleToCoast success={error is None} error={error}')


def tick(delta):
    try:
        w = world()
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if state['step'] == 0 and isinstance(pc, unreal.EWTitlePlayerController) and pc.get_title_widget():
            pc.get_title_widget().start_journey()
            state['step'] = 1
        elif state['step'] == 1 and isinstance(pc, unreal.EWTitlePlayerController) and pc.get_creator_widget():
            creator = pc.get_creator_widget()
            creator.select_body(1)
            creator.select_tone(1)
            creator.set_sail()
            checks.append('From the title, the creator: the woman, the second colouring, Set Sail')
            state['step'] = 2
        elif state['step'] == 2 and pc and not isinstance(pc, unreal.EWTitlePlayerController) and pc.get_controlled_pawn():
            survivor = pc.get_controlled_pawn()
            look = survivor.get_appearance()
            mesh = survivor.get_editor_property('mesh').get_editor_property('skeletal_mesh_asset')
            if mesh == woman and look.tone == 1:
                assert 'Lvl_CoastalPlayground' in w.get_path_name(), w.get_path_name()
                checks.append('The coast loads and the survivor wears the chosen look')
                finish()
                return
        if time.monotonic() > state['deadline']:
            raise TimeoutError(f'stuck at step {state["step"]}')
    except Exception as error:
        finish(f'step {state["step"]}: {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
