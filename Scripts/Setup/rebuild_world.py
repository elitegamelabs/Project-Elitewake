"""Rebuild the coastal map's world from the scripts, in order, in one editor, then close it.
Run in a rendering editor (the terrain script rebuilds the ocean), outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
Optionally set EW_REBUILD_FROM to a step's name to start part-way, or EW_REBUILD_ONLY to a comma-separated list of
steps to run just those. Writes Saved/WorldRebuildResult.json after each
step, so a failure shows where it stopped; the editor closes either way.

The order: ground first, then what is cut into it (caves) or stands on it, then what lives there and the climate,
Ports and the sloop; then Phase 1's Plains and Saltreach work, which clears or replaces some of what the world steps
put back (trees in Saltreach, piranhas in the arrival pond, the boars round the arrival) and holds the sloop for the
yard. Reefs are not rebuilt here: the owner's three open-ocean reefs (October 31) replace build_reefs.py's layout.
"""
import json
import os
import runpy
import sys
import time
import traceback
from pathlib import Path
import unreal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rebuild_safety import check_map_and_space  # noqa: E402

RESULT = Path(unreal.Paths.project_saved_dir(), 'WorldRebuildResult.json')
MAP_FILE = Path(unreal.Paths.project_content_dir(), 'Elitewake', 'Maps', 'Lvl_CoastalPlayground.umap')
STEPS = ['build_coastal_terrain', 'build_caves', 'build_cave_webs', 'build_landmarks', 'build_grass', 'build_coastal_flora',
         'build_coastal_rocks', 'build_seabed_life', 'build_fish', 'place_animals', 'add_spiders', 'build_crystals', 'build_regions',
         'build_ports', 'add_port_merchants', 'build_freeport', 'build_saltreach_welcome', 'restore_sloop', 'build_voyage_ready',
         'build_arrival', 'build_first_resources', 'build_plains_threat', 'tune_rendering', 'clear_climbouts']


def main():
    start, only = os.environ.get('EW_REBUILD_FROM'), os.environ.get('EW_REBUILD_ONLY')
    steps = STEPS[STEPS.index(start):] if start else STEPS
    if only:
        steps = [s for s in STEPS if s in only.split(',')]
    done, error = [], None
    # A progress window in the editor naming each step, so the owner can follow along (owner, November 4). The editor
    # redraws it only between steps: a long step leaves it, and the window, still until that step ends.
    task = unreal.ScopedSlowTask(len(steps), 'Rebuilding the world')
    task.make_dialog(True)
    for n, step in enumerate(steps, 1):
        began = time.time()
        task.enter_progress_frame(1, f'Rebuilding the world: step {n} of {len(steps)}, {step}')
        unreal.log(f'EWREBUILD starting {step}')
        try:
            check_map_and_space(MAP_FILE)
            runpy.run_path(str(HERE / f'{step}.py'), run_name='__main__')
            check_map_and_space(MAP_FILE)
        except BaseException as failure:   # an assert or SystemExit stops the rebuild where it failed
            error = f'{step}: {failure!r}\n{traceback.format_exc()[-2000:]}'
        done.append({'step': step, 'seconds': round(time.time() - began, 1), 'ok': error is None})
        RESULT.write_text(json.dumps({'success': False if error else None, 'steps': done, 'error': error}, indent=2))
        if error:
            break
    del task
    RESULT.write_text(json.dumps({'success': error is None, 'steps': done, 'error': error,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWREBUILD finished success={error is None}')
    unreal.SystemLibrary.quit_editor()


main()
