"""Client acceptance for the dinghy's rule (design reference: ordinary damage cannot sink the dinghy). Needs Play in
/Game/Elitewake/Maps/Test/Lvl_ShipsTest as a listen server plus one client. Run unattended with run_play_check.py.

  1. The dinghy's hull is struck until it is destroyed (AEWShip::TakeRoundShot, server, Play only): she stays afloat
     on server and client, while a sloop holed the same way goes down.
Writes Saved/DinghyUnsinkablePlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'DinghyUnsinkablePlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
checks = []
state = {'handle': None, 't': time.monotonic(), 'hit': False}


def ship_named(world, ship_id):
    return next((s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
                 if str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id), None)


def destroy(target):
    t = target.get_actor_transform()
    extent = target.get_editor_property('definition').get_editor_property('hull_extent')
    k = 0
    while target.get_hull_health() > 0 and k < 100:
        target.take_round_shot(t.transform_location(unreal.Vector(-100 + 10 * k, extent.y, extent.z - 10)), target.get_actor_right_vector(), None)
        k += 1


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK DinghyUnsinkable success={error is None} error={error}')


def tick(delta):
    try:
        if time.monotonic() - state['t'] < 1.0:
            return
        dinghy, sloop = ship_named(server_world, 'Dinghy'), ship_named(server_world, 'Sloop')
        assert dinghy and sloop, 'the ships test map needs a dinghy and a sloop'
        if not state['hit']:
            destroy(dinghy)
            destroy(sloop)
            state.update(hit=True, t=time.monotonic())
            return
        if time.monotonic() - state['t'] < 3.0:
            return
        peer = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if s.get_name() == dinghy.get_name())
        assert dinghy.get_hull_health() == 0 and not dinghy.is_sinking() and not peer.is_sinking(), 'the dinghy is sinking'
        assert sloop.is_sinking(), 'the sloop, holed the same way, is not sinking'
        checks.append('A dinghy with her hull destroyed stays afloat on server and client, while a sloop holed the same way goes down')
        finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
