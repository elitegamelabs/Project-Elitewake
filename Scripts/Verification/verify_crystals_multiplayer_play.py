"""Mining a crystal with a second player (listen server plus one client, EW_PLAY_PLAYERS=2). The client, holding a Metal pickaxe,
mines a ruby node in the starter cave through the real attack request. Checks: the client's own world has the same nodes; the node
empties on the server and is hidden in the client's world; the client's pack holds 4 to 8 rubies (the server's count agrees); a
second player (the host) with a wooden pickaxe gets nothing from another ruby node. Writes Saved/CrystalsMultiplayerPlayResult.json."""
import json
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
cave = T.CAVES['Starter']
metal = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestMetalPickaxe')
wooden = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenPickaxe')
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 14, 'handle': None, 'strikes': 0}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def nodes(w, kind):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWMineable)
            if str(a.get_actor_label()).startswith(f'{kind} Node ') and 'Starter cave' in str(a.get_actor_label())]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'CrystalsMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK CrystalsMultiplayer success={error is None} error={error}')


def face(survivor, controller, node, distance=150.0):
    loc, fwd = node.get_actor_location(), node.get_actor_forward_vector()
    for lift in (110, 160, 220):
        if survivor.teleport(unreal.Vector(loc.x + fwd.x * distance, loc.y + fwd.y * distance, cave.floor + lift), unreal.Rotator()):
            break
    eye, _ = survivor.get_actor_eyes_view_point()
    controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(loc.x + fwd.x * 35, loc.y + fwd.y * 35, loc.z + fwd.z * 35)))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            owner = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            state['owner'] = owner
            state['host_pawn'] = host.get_controlled_pawn()
            for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWAnimal):
                a.destroy_actor()
            rubies = nodes(server_world, 'Ruby')
            check('rubies in the starter cave on the server and the client', len(rubies) >= 2 and len(nodes(client_world, 'Ruby')) == len(rubies), count=len(rubies))
            state['rubies'] = rubies
            state['item'] = rubies[0].get_editor_property('resource')
            owner.get_inventory_component().add_item(metal, 1)
            check('the client holds a metal pickaxe', lib.send_verification_equipment_request(client, metal, unreal.EWEquipmentSlot.MAIN_HAND))
            state['host_pawn'].get_inventory_component().add_item(wooden, 1)
            state['at'] = time.monotonic() + 2.0
            state['phase'] = 1
        elif p == 1:
            face(state['owner'], client, state['rubies'][0])
            state['at'] = time.monotonic() + 1.5
            state['phase'] = 2
        elif p == 2:
            node = state['rubies'][0]
            if node.get_editor_property('remaining') > 0 and state['strikes'] < 14:
                mine = next(n for n in nodes(client_world, 'Ruby') if n.get_name() == node.get_name())     # an attack names the client's own copy of the node
                lib.send_verification_attack(client, mine)
                state['strikes'] += 1
                state['at'] = time.monotonic() + 1.7
                return
            got = state['owner'].get_inventory_component().get_item_count(state['item'])
            check('server: the client emptied the node for 4 to 8 rubies', node.get_editor_property('remaining') == 0 and 4 <= got <= 8, got=got, strikes=state['strikes'])
            mirror = next(n for n in nodes(client_world, 'Ruby') if n.get_name() == node.get_name())
            check('client: the emptied node is hidden in its own world', not mirror.get_editor_property('mesh').is_visible())
            check('client: its own pack agrees', client.get_controlled_pawn().get_inventory_component().get_item_count(state['item']) == got)
            check('the host wooden pickaxe is equipped', lib.send_verification_equipment_request(host, wooden, unreal.EWEquipmentSlot.MAIN_HAND))
            face(state['host_pawn'], host, state['rubies'][1])
            state['host_pawn'].get_inventory_component().remove_item(state['item'], 100000)
            state.update(phase=3, at=time.monotonic() + 2.0, strikes=0)
        elif p == 3:
            if state['strikes'] < 3:
                lib.send_verification_attack(host, state['rubies'][1])
                state['strikes'] += 1
                state['at'] = time.monotonic() + 1.7
                return
            check('a wooden pickaxe gets nothing from a ruby, for the host too', state['host_pawn'].get_inventory_component().get_item_count(state['item']) == 0
                  and state['rubies'][1].get_editor_property('remaining') > 0)
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
