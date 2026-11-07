"""Diagnostic (November 7): the sloop's shipyard hold during Play, frame by frame from the start. One player, standalone.
Writes Saved/SloopYardPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

world = unreal.EWEditorVerificationLibrary.get_play_worlds()[0]
state = {'frames': 0, 'seen': [], 'h': None}


def tick(_):
    ships = [s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)]
    state['seen'].append([(s.get_name(), str(s.get_editor_property('definition').get_name()) if s.get_editor_property('definition') else None,
                           s.get_editor_property('held_by_yard'), s.is_owned(), str(s.get_owner_name())) for s in ships])
    state['frames'] += 1
    if state['frames'] < 120:
        return
    unreal.unregister_slate_post_tick_callback(state['h'])
    first, last = state['seen'][0], state['seen'][-1]
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world() or unreal.EditorLevelLibrary.get_editor_world()
    in_editor = [(s.get_name(), s.get_editor_property('held_by_yard'), s.get_path_name()) for s in
                 unreal.GameplayStatics.get_all_actors_of_class(editor, unreal.EWShip)] if editor else None
    in_play = [s.get_path_name() for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)]
    Path(unreal.Paths.project_saved_dir(), 'SloopYardPlayResult.json').write_text(json.dumps(
        {'success': True, 'first_frame': first, 'last_frame': last, 'editor_world_same_session': in_editor, 'play_paths': in_play,
         'changes': [i for i in range(1, len(state['seen'])) if state['seen'][i] != state['seen'][i - 1]][:10]}, indent=1, default=str))
    unreal.log('EWPLAYCHECK SloopYard done')


state['h'] = unreal.register_slate_post_tick_callback(tick)
