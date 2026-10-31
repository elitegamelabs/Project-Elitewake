"""F9's item spawner (testing only, owner, October 30), with a second player (listen server plus one client, EW_PLAY_PLAYERS=2).
  - the client presses F9 (a real key): the spawner opens with the craftable items first, then every other item, the mouse showing;
  - the client moves the cursor with the d-pad and presses A twice (real keys): exactly two of that item reach their pack on the server;
  - the host's spawner gives one item through the tile's click path: one more in the host's pack;
  - B closes the client's spawner, F9 the host's.
Saves Saved/Screenshots/Menus/item_spawner.png. Writes Saved/ItemSpawnerMultiplayerPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
report = {'checks': []}
state = {'phase': 'start', 'at': time.monotonic() + 14, 'handle': None}
shots = saved / 'Screenshots' / 'Menus'
shots.mkdir(parents=True, exist_ok=True)


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def server_pawn(pc):
    return next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(pc.get_controlled_pawn()))


def count(pawn, item):
    return pawn.get_inventory_component().get_item_count(item)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    for pc in (host, client):
        pc.set_item_spawner_open(False)
    report.update(success=error is None, error=error)
    (saved / 'ItemSpawnerMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ItemSpawnerMultiplayer success={error is None} error={error}')


def wait(phase, seconds=1.5):
    state.update(phase=phase, at=time.monotonic() + seconds)


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 'start':
            assert lib.send_verification_gameplay_key(client, 'F9'), 'F9 was not taken'
            wait('open', 1.5)
        elif p == 'open':
            spawner = client.get_item_spawner_widget()
            check('F9 opens the spawner on the client, the mouse showing', client.is_item_spawner_open() and spawner and spawner.is_in_viewport()
                  and client.get_editor_property('bShowMouseCursor'))
            total, craftable = spawner.get_item_count(), spawner.get_craftable_count()
            report['items'] = [str(spawner.get_item(i).get_name()) for i in range(total)]
            check('it lists the craftable items first, then every other item', craftable >= 10 and total >= 40, craftable=craftable, total=total)
            assert lib.send_verification_ui_key(client, 'Gamepad_DPad_Right')
            check('the d-pad moves the cursor', spawner.get_cursor() == 1, cursor=spawner.get_cursor())
            item = spawner.get_item(1)
            mate = server_pawn(client)
            state.update(item=item, mate=mate, before=count(mate, item))
            assert lib.send_verification_ui_key(client, 'Gamepad_FaceButton_Bottom')
            assert lib.send_verification_ui_key(client, 'Gamepad_FaceButton_Bottom')
            wait('given', 1.5)
        elif p == 'given':
            got = count(state['mate'], state['item']) - state['before']
            check("two presses of A give exactly two of the item, in the client's pack on the server", got == 2, item=state['item'].get_name(), got=got)
            # (In the editor both players share one keyboard focus, so the client closes before the host opens.)
            assert lib.send_verification_ui_key(client, 'Gamepad_FaceButton_Right')
            wait('closed', 1.0)
        elif p == 'closed':
            check("B closes the client's spawner and gives back the game", not client.is_item_spawner_open() and not client.get_editor_property('bShowMouseCursor'),
                  open=client.is_item_spawner_open(), cursor=client.get_editor_property('bShowMouseCursor'))
            host.set_item_spawner_open(True)
            wait('host', 1.0)
        elif p == 'host':
            spawner = host.get_item_spawner_widget()
            item = spawner.get_item(spawner.get_craftable_count())      # the first of the other items
            pawn = host.get_controlled_pawn()
            before = count(pawn, item)
            spawner.give(spawner.get_craftable_count())
            check('a click on a tile gives one (the host)', count(pawn, item) == before + 1, item=item.get_name())
            unreal.SystemLibrary.execute_console_command(server_world, f'Shot showui filename="{shots / "item_spawner.png"}"')
            wait('shot', 1.0)
        elif p == 'shot':
            assert lib.send_verification_ui_key(host, 'F9')
            check("F9 closes the host's spawner", not host.is_item_spawner_open())
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
