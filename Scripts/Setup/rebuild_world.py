"""Rebuild the coastal map's world from the scripts, in order, in one editor, then close it.
Run in a rendering editor (the terrain script rebuilds the ocean), outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
Optionally set EW_REBUILD_FROM to a step's name to start part-way, or EW_REBUILD_ONLY to a comma-separated list of
steps to run just those. Writes Saved/WorldRebuildResult.json after each
step, so a failure shows where it stopped; the editor closes either way.

The order (Docs/REPORTS/2026-10-15_Claude.md, "Rebuild order for the coastal map"): ground first, then what is cut
into it (caves) or stands on it, then what lives there and the climate, Ports and the sloop.
"""
import json
import os
import runpy
import time
import traceback
from pathlib import Path
import unreal

HERE = Path(__file__).resolve().parent
RESULT = Path(unreal.Paths.project_saved_dir(), 'WorldRebuildResult.json')
STEPS = ['build_coastal_terrain', 'build_caves', 'build_cave_webs', 'build_landmarks', 'build_grass', 'build_coastal_flora',
         'build_coastal_rocks', 'build_reefs', 'build_seabed_life', 'build_fish', 'place_animals', 'build_regions', 'build_ports', 'restore_sloop', 'tune_rendering']


def main():
    start, only = os.environ.get('EW_REBUILD_FROM'), os.environ.get('EW_REBUILD_ONLY')
    steps = STEPS[STEPS.index(start):] if start else STEPS
    if only:
        steps = [s for s in STEPS if s in only.split(',')]
    done, error = [], None
    for step in steps:
        began = time.time()
        unreal.log(f'EWREBUILD starting {step}')
        try:
            runpy.run_path(str(HERE / f'{step}.py'), run_name='__main__')
        except BaseException as failure:   # an assert or SystemExit stops the rebuild where it failed
            error = f'{step}: {failure!r}\n{traceback.format_exc()[-2000:]}'
        done.append({'step': step, 'seconds': round(time.time() - began, 1), 'ok': error is None})
        RESULT.write_text(json.dumps({'success': False if error else None, 'steps': done, 'error': error}, indent=2))
        if error:
            break
    RESULT.write_text(json.dumps({'success': error is None, 'steps': done, 'error': error,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWREBUILD finished success={error is None}')
    unreal.SystemLibrary.quit_editor()


main()
