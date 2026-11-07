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
  EW_PLAY_STARTER_KIT optional, default 1: the map's test starter kit (ew.TestStarterKit); 0 is the normal, empty-handed start
  EW_PLAY_YARD_SHIPS optional, default sold: ships the map holds for the shipyard (AEWShip::bHeldByYard, the moored sloop since
                   November 1) are let go before the check, as if sold, so the ship checks written for a sloop anyone may use
                   still work her; held leaves them as the game has them (verify_voyage_ready_play needs that)

  UnrealEditor.exe EW.uproject <map> -unattended -ExecCmds="py <path>/run_play_check.py"

Pass the map on the command line so it opens with the editor. -unattended keeps dialogs from
blocking the run. (-ExecutePythonScript closes the editor as soon as the script returns.)

Writes Saved/PlayCheckRun.json with the outcome.
"""
import json
import os
import re
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
# A check may declare the settings it needs in its own text (e.g. "EW_PLAY_STARTER_KIT=0 and EW_PLAY_YARD_SHIPS=held" in
# verify_voyage_ready_play.py's header); they apply unless the environment sets them (November 7: run without them, the first-
# voyage check failed because the runner had let the yard's sloop go).
check_text = Path(check).read_text(encoding='utf-8', errors='ignore')
for name in ('EW_PLAY_YARD_SHIPS', 'EW_PLAY_STARTER_KIT', 'EW_PLAY_SHIPS'):
    declared = re.search(rf'{name}=([\w,]+)', check_text)
    if declared and name not in os.environ:
        os.environ[name] = declared.group(1)
        unreal.log(f'EWPLAYRUN {name}={declared.group(1)} (declared by the check)')
yard_ships = os.environ.get('EW_PLAY_YARD_SHIPS', 'sold')

unreal.SystemLibrary.execute_console_command(None, 'ew.NeedsDepletion 0')   # checks read exact hunger and thirst; verify_needs_play turns depletion back on
unreal.SystemLibrary.execute_console_command(None, f"ew.TestStarterKit {os.environ.get('EW_PLAY_STARTER_KIT', '1')}")   # the checks were written with the kit
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
started = time.time()
if result.exists():
    result.unlink()
state = {'step': 'wait_editor', 'at': time.monotonic() + 5.0, 'outcome': None, 'handle': None}

def spawn_missing_ships(wanted):
    """EW_PLAY_SHIPS (e.g. Schooner,Brigantine): ship classes a check needs. Any the map does not have (the schooner and
    brigantine were parked off the map on October 12 while their designs are reworked) is spawned for the check, on the
    server, in deep open water near the moored sloop and clear of other ships; the check moves it where it wants."""
    import sys as _sys
    _sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
    import math as _math
    import world_terrain as _T
    worlds, pcs = lib.get_play_worlds(), None
    server = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
    ships = list(unreal.GameplayStatics.get_all_actors_of_class(server, unreal.EWShip))
    have = {str(s.get_editor_property('definition').get_editor_property('ship_id')) for s in ships if s.get_editor_property('definition')}
    anchor = next((s for s in ships if s.get_editor_property('definition') and
                   str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop'), ships[0] if ships else None)
    water = [a for a in unreal.GameplayStatics.get_all_actors_of_class(server, unreal.WaterBody)]
    spawned = []
    for ship_id in wanted:
        if ship_id in have:
            continue
        definition = unreal.load_asset(f'/Game/Elitewake/Ships/DA_Ship_{ship_id}')
        assert definition, f'no ship definition for {ship_id}'
        at, rot = anchor.get_actor_location(), anchor.get_actor_rotation()
        spot = None
        for radius in (5000, 7000, 9000, 12000, 15000):
            for k in range(24):
                a = 2 * _math.pi * k / 24
                x, y = at.x + _math.cos(a) * radius, at.y + _math.sin(a) * radius
                hit = unreal.SystemLibrary.line_trace_single(server, unreal.Vector(x, y, _T.SEA + 3000), unreal.Vector(x, y, _T.SEA - 20000),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, water, unreal.DrawDebugTrace.NONE, True)
                floor = hit.to_tuple()[4].z if hit else _T.SEA - 20000
                clear = all(_math.hypot(x - s.get_actor_location().x, y - s.get_actor_location().y) > 3000 for s in ships)
                if _T.SEA - floor > 1200 and clear:
                    spot = unreal.Vector(x, y, at.z)
                    break
            if spot:
                break
        assert spot, f'no deep open water near the sloop for the {ship_id}'
        ship = lib.spawn_verification_ship(server, definition, spot, rot)
        assert ship, f'could not spawn the {ship_id}'
        ships.append(ship)
        spawned.append(ship.get_name())
        unreal.log(f'EWPLAYRUN spawned a {ship_id} for this check at {spot}')
    return spawned


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
        # A big world takes a while to load into each Play world (the twenty-island map: well over two minutes for a
        # listen server and client); EW_PLAY_START_WAIT overrides, seconds.
        state.update(step='wait_play', at=now + float(os.environ.get('EW_PLAY_START_WAIT', '360')))
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
        if yard_ships == 'sold':
            for world in lib.get_play_worlds():
                for ship in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip):
                    # Every copy, the client's too: the map's value is on both, and a property set from Python is not
                    # sent to clients.
                    if ship.get_editor_property('held_by_yard'):
                        ship.set_editor_property('held_by_yard', False)
                        unreal.log(f"EWPLAYRUN let go of the yard's {ship.get_actor_label()} for this check")
        wanted = [n for n in os.environ.get('EW_PLAY_SHIPS', '').split(',') if n]
        state['spawned'] = spawn_missing_ships(wanted) if wanted else []
        state.update(step='ships', at=now + 15.0)
    elif step == 'ships':
        # A ship spawned for the check reaches every client before the check looks for its copies.
        # (A spawned ship has another name on each client: count ships instead.)
        counts = [len(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWShip)) for w in lib.get_play_worlds()]
        if state['spawned'] and len(set(counts)) > 1 and now < state['at']:
            return
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
