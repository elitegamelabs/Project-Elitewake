"""An elephant pushes a tree over with a second player in the world (listen server plus one client, EW_PLAY_PLAYERS=2).
The server stands an elephant 4.3 m from the nearest tree, facing it. Checks: the tree is knocked over on the server; the client's own
copy of the tree is felled too; after the time a player-felled tree would have faded it still lies there in both worlds with its wood
(not fading); the client sees the elephant stand near the fallen tree's place. Writes Saved/ElephantTreePushMultiplayerPlayResult.json."""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
tree_cls = unreal.load_class(None, '/Script/EW.EWHarvestTree')
report = {'checks': []}
state = {'t0': time.monotonic() + 14, 'phase': 0, 'handle': None, 'side': 0}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def sw():
    return unreal.GameplayStatics.get_time_seconds(server_world)


def trees(w):
    return unreal.GameplayStatics.get_all_actors_of_class(w, tree_cls)


def mirror(name):
    return next((t for t in trees(client_world) if t.get_name() == name), None)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    unreal.SystemLibrary.execute_console_command(server_world, 'slomo 1')
    report.update(success=error is None, error=error)
    (saved / 'ElephantTreePushMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ElephantTreePushMultiplayer success={error is None} error={error}')


def stand():
    t = state['tree'].get_actor_location()
    ang = math.radians(state['side'])
    state['elephant'].set_actor_location_and_rotation(unreal.Vector(t.x - math.cos(ang) * 430, t.y - math.sin(ang) * 430, t.z + 40),
                                                      unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(ang)), False, True)
    # keep both players close, as in the single-player check, so the animal stays awake and the client has the tree relevant
    state['host'].teleport(unreal.Vector(t.x + 900, t.y + 900, t.z + 400), unreal.Rotator())
    state['guest'].teleport(unreal.Vector(t.x + 900, t.y - 900, t.z + 400), unreal.Rotator())


def tick(delta):
    if time.monotonic() < state['t0']:
        return
    try:
        p = state['phase']
        if p == 0:
            elephants = [a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWAnimal)
                         if 'Elephant' in str(a.get_editor_property('definition').get_editor_property('display_name'))]
            check('an elephant exists', elephants)
            elephant = elephants[0]
            home = elephant.get_actor_location()
            standing = [t for t in trees(server_world) if not t.is_felled()]
            tree = min(standing, key=lambda t: math.hypot(t.get_actor_location().x - home.x, t.get_actor_location().y - home.y))
            host_pc = next(c for c in pcs if c.has_authority())
            state.update(elephant=elephant, tree=tree, name=tree.get_name(), host=host_pc.get_controlled_pawn(), guest=next(
                c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if c != host_pc.get_controlled_pawn()))
            check('the client has the same tree, standing', mirror(state['name']) is not None and not mirror(state['name']).is_felled())
            stand()
            unreal.SystemLibrary.execute_console_command(server_world, 'slomo 3')
            state.update(phase=1, start=sw(), restood=sw())
        elif p == 1:
            if state['tree'].is_felled():
                state.update(phase=2, felled_at=sw())
                unreal.SystemLibrary.execute_console_command(server_world, 'slomo 1')
                return
            if sw() - state['restood'] > 4:
                state['restood'] = sw()
                state['side'] += 70
                stand()
            if sw() - state['start'] > 240:
                raise AssertionError('the elephant never knocked the tree over')
        elif p == 2:
            copy = mirror(state['name'])
            check('the client sees the tree felled', copy is not None and copy.is_felled())
            if sw() - state['felled_at'] < 14:
                return
            copy = mirror(state['name'])
            check('server: the felled tree still lies there after the usual fade time', state['tree'].get_editor_property('wood_remaining') == 12 and not state['tree'].is_fading())
            check('client: it still lies there too, not fading', copy is not None and not copy.is_fading(), fade=copy.get_fade() if copy else None)
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
