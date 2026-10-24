"""Run one Play acceptance script unattended, then close the editor.

Starts the editor on a map, begins an in-process listen-server Play session, runs the check script,
waits for its result file, stops Play, waits for Play to finish shutting down, and quits. Stopping
Play before quitting avoids the engine assertion seen when the editor closed mid-teardown.

Set these environment variables, then launch the editor (close any other editor first). Launch from
PowerShell or cmd: Git Bash rewrites values that start with "/" into Windows paths.
  EW_PLAY_MAP      e.g. /Game/Elitewake/Maps/Lvl_CoastalPlayground
  EW_PLAY_CHECK    absolute path of the Play script, e.g. .../Scripts/Verification/verify_ship_sailing_play.py
  EW_PLAY_RESULT   result file name in Saved/, e.g. ShipSailingPlayResult.json
  EW_PLAY_PLAYERS  optional, default 2 (listen server plus one client)
  EW_PLAY_TIMEOUT  optional seconds, default 180
  EW_PLAY_STANDALONE optional, 1 plays one survivor with no network (Single Player)
  EW_PLAY_WINDOW   optional, e.g. 1280x720 for the Play window size

  UnrealEditor.exe EW.uproject <map> -unattended -ExecCmds="py <path>/run_play_check.py"

Pass the map on the command line so it opens with the editor. -unattended keeps dialogs from
blocking the run. (-ExecutePythonScript closes the editor as soon as the script returns.)

Writes Saved/PlayCheckRun.json with the outcome.
"""
import json
import os
import runpy
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
map_path = os.environ['EW_PLAY_MAP']
check = os.environ['EW_PLAY_CHECK']
result = saved / os.environ['EW_PLAY_RESULT']
players = int(os.environ.get('EW_PLAY_PLAYERS', '2'))
timeout = float(os.environ.get('EW_PLAY_TIMEOUT', '180'))

unreal.SystemLibrary.execute_console_command(None, 'ew.NeedsDepletion 0')   # checks read exact hunger and thirst; verify_needs_play turns depletion back on
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
started = time.time()
if result.exists():
    result.unlink()
state = {'step': 'wait_editor', 'at': time.monotonic() + 5.0, 'outcome': None, 'handle': None}

def report(outcome):
    (saved / 'PlayCheckRun.json').write_text(json.dumps({
        'map': map_path, 'check': check, 'result_file': str(result), 'outcome': outcome,
        'seconds': round(time.time() - started, 1)}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYRUN {outcome}')

def tick(delta):
    try:
        advance()
    except Exception as error:
        unreal.log_error(f'EWPLAYRUN runner error: {error!r}')
        if state['step'] not in ('stop', 'wait_stop', 'quit'):
            state.update(step='stop', outcome=f'runner error: {error!r}')

def advance():
    now = time.monotonic()
    step = state['step']
    if step == 'wait_editor' and now >= state['at']:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        if not world or map_path.rsplit('/', 1)[-1] not in world.get_path_name():
            # Opening the map now, after the editor is running, if it was not given on the command line.
            state['loads'] = state.get('loads', 0) + 1
            if state['loads'] > 2:
                raise RuntimeError(f'Could not open {map_path}')
            unreal.EditorLoadingAndSavingUtils.load_map(map_path)
            state['at'] = now + 3.0
            return
        if not lib.start_verification_play_session(players):
            raise RuntimeError('Could not start Play')
        state.update(step='wait_play', at=now + 120.0)
    elif step == 'wait_play':
        worlds = lib.get_play_worlds()
        pawns = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
        # A survivor for each player, or the title screen's controller, which has none.
        # ...and every survivor's PlayerState has reached every machine (a big map can hold it back a second or two).
        known = all(c.get_editor_property('PlayerState') for w in worlds
                    for c in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWCharacter))
        if len(worlds) == players and known and all(pc and (pc.get_controlled_pawn() or isinstance(pc, unreal.EWTitlePlayerController)) for pc in pawns):
            state.update(step='settle', at=now + 3.0)
        elif now >= state['at']:
            state.update(step='stop', outcome='Play session did not start')
    elif step == 'settle' and now >= state['at']:
        runpy.run_path(check)
        state.update(step='wait_result', at=now + timeout)
    elif step == 'wait_result':
        try:
            final = json.loads(result.read_text(encoding='utf-8')) if result.exists() and result.stat().st_mtime >= started else None
        except ValueError:
            final = None   # caught mid-write; read it again next tick
        # Some checks save progress after every checkpoint; only a success, a finish time or an error is final.
        if final and (final.get('success') or final.get('finished_utc') or final.get('error') or final.get('errors')):
            state.update(step='stop', outcome='passed' if final.get('success') else 'failed')
        elif now >= state['at']:
            state.update(step='stop', outcome='timed out')
    elif step == 'stop':
        lib.stop_verification_play_session()
        state.update(step='wait_stop', at=now + 30.0)
    elif step == 'wait_stop':
        if not lib.get_play_worlds():
            state.update(step='quit', at=now + 3.0)
        elif now >= state['at']:
            state.update(step='quit', at=now)
    elif step == 'quit' and now >= state['at']:
        report(state['outcome'])
        unreal.unregister_slate_post_tick_callback(state['handle'])
        unreal.SystemLibrary.quit_editor()

state['handle'] = unreal.register_slate_post_tick_callback(tick)
