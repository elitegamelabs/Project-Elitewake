"""Check that every ship is explicitly marked on a client's map, even under rock.

Run via run_play_check.py with two players after rebuilding and recompiling. The
map image alone cannot reveal a boat inside a covered sea cavern.
"""
import json
import time
from pathlib import Path

import unreal


worlds = unreal.EWEditorVerificationLibrary.get_play_worlds()
client_world = next(w for w in worlds if not unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
server_world = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
client = unreal.GameplayStatics.get_player_controller(client_world, 0)
result = Path(unreal.Paths.project_saved_dir()) / 'ShipMapMarkersPlayResult.json'
started = time.monotonic()
state = {'handle': None, 'opened': False}


def finish(error=None, count=0):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    if client.is_map_open():
        unreal.EWEditorVerificationLibrary.send_verification_gameplay_key(client, 'M')
    result.write_text(json.dumps({
        'success': error is None,
        'error': error,
        'server_ships': count,
        'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }, indent=2))


def tick(delta):
    try:
        ships = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
        assert ships, 'No ships exist on the Play map'
        if not state['opened']:
            assert unreal.EWEditorVerificationLibrary.send_verification_gameplay_key(client, 'M')
            state['opened'] = True
            return
        ui = next((w for w in unreal.WidgetLibrary.get_all_widgets_of_class(
            client_world, unreal.EWMapWidget, False) if w.get_owning_player() == client and w.is_in_viewport()), None)
        if ui and ui.has_map_capture() and ui.get_ship_marker_count() == len(ships):
            finish(count=len(ships))
        elif time.monotonic() - started > 30:
            raise AssertionError(f'Client map knows {ui.get_ship_marker_count() if ui else 0} of {len(ships)} ships')
    except Exception as exc:
        finish(repr(exc))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
