"""A hosted game keeps each player's survivor (owner, October 30: friends keep their progress when they rejoin), with a second player
(listen server plus one client, EW_PLAY_PLAYERS=2). In a packaged hosted game this runs on its own when a player leaves, every minute
and when they join again (AEWGameMode::Logout, the save timer, HandleStartingNewPlayer); the editor's Play does not keep hosted games,
so the check calls the same server functions:
  - host and client get different save slots;
  - the client's survivor (four wood, 77 Copper, standing on the Freeport's high street) is saved on the host, without the world;
  - everything changes (pack emptied, purse emptied, carried off elsewhere);
  - the host gives the survivor back: the wood, the purse and the place return, and the client sees its purse.
  - a client-equipped fur jacket returns after server save/restore, without a spare copy in the pack.
The test slot is deleted afterwards. Writes Saved/ServerSurvivorMultiplayerPlayResult.json."""
import json
import time
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
report = {'checks': []}
state = {'phase': 'start', 'at': time.monotonic() + 14, 'handle': None}
WOOD = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
JACKET = unreal.load_asset('/Game/Elitewake/Items/Armor/DA_FurJacket')
CHEST = unreal.EWEquipmentSlot.CHEST


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    slot = state.get('slot')
    if slot and unreal.GameplayStatics.does_save_game_exist(slot, 0):
        unreal.GameplayStatics.delete_game_in_slot(slot, 0)
    report.update(success=error is None, error=error)
    (saved / 'ServerSurvivorMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ServerSurvivorMultiplayer success={error is None} error={error}')


def wood(owner):
    return sum(e.quantity for e in owner.get_inventory_component().get_inventory_entries() if e.item_definition == WOOD)


def jacket_in_pack(owner):
    return sum(e.quantity for e in owner.get_inventory_component().get_inventory_entries() if e.item_definition == JACKET)


def jacket_equipped(owner):
    return any(e.get_editor_property('item_definition') == JACKET and e.get_editor_property('slot') == CHEST
               for e in owner.get_equipment_component().get_equipment_entries())


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        mode = unreal.GameplayStatics.get_game_mode(server_world)
        if p == 'start':
            owner = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            remote = owner.get_controller()
            state.update(owner=owner, remote=remote)
            slot, host_slot = mode.player_slot(remote), mode.player_slot(host)
            report['slots'] = [slot, host_slot]
            check('each player has a save slot of their own', slot and host_slot and slot != host_slot, slot=slot, host=host_slot)
            state['slot'] = slot
            pack = owner.get_inventory_component()
            for e in list(pack.get_inventory_entries()):
                pack.remove_item(e.item_definition, e.quantity)
            pack.add_item(WOOD, 4)
            pack.add_item(JACKET, 1)
            check('the client requests its jacket through the equipment interface',
                  lib.send_verification_equipment_request(client, JACKET, CHEST))
            owner.get_wallet_component().set_copper(77)
            x, y = W.PORTS['Plains'].world(0, -200)
            owner.teleport(unreal.Vector(x, y, T.PORT_LEVEL + 120), unreal.Rotator())
            state.update(phase='save', at=time.monotonic() + 2.0)
        elif p == 'save':
            owner, remote = state['owner'], state['remote']
            check('the host sees the client jacket before saving', jacket_equipped(owner))
            check('the client sees its jacket before saving', jacket_equipped(client.get_controlled_pawn()))
            state['spot'] = owner.get_actor_location()
            check('the host saves the client survivor', mode.save_player_survivor(remote))
            save = unreal.EWSurvivorSave.load_save(state['slot'])
            check('only the survivor is kept (the world is the host\'s own save)', save and not save.get_editor_property('has_ships')
                  and not save.get_editor_property('has_world_state') and len(save.get_editor_property('built_pieces')) == 0)
            owner.get_inventory_component().remove_item(WOOD, 4)
            check('the client removes its jacket after the saved checkpoint',
                  lib.send_verification_equipment_request(client, None, CHEST, True))
            owner.get_wallet_component().set_copper(0)
            x, y = W.PORTS['Plains'].world(-12000, 0)
            owner.teleport(unreal.Vector(x, y, 20000), unreal.Rotator())
            state.update(phase='changed', at=time.monotonic() + 1.5)
        elif p == 'changed':
            owner, remote = state['owner'], state['remote']
            check('the survivor has lost it all', wood(owner) == 0 and owner.get_wallet_component().get_copper() == 0)
            check('the jacket was taken off after saving', not jacket_equipped(owner))
            check('the host gives the survivor back', mode.restore_player_survivor(remote))
            check('the wood and the purse are back', wood(owner) == 4 and owner.get_wallet_component().get_copper() == 77,
                  wood=wood(owner), copper=owner.get_wallet_component().get_copper())
            gap = (owner.get_actor_location() - state['spot']).length()
            check('and the survivor stands where they were', gap < 50, gap=gap)
            check('the jacket is equipped again with no duplicate in the pack',
                  jacket_equipped(owner) and jacket_in_pack(owner) == 0,
                  equipped=jacket_equipped(owner), spare=jacket_in_pack(owner))
            state.update(phase='client', at=time.monotonic() + 1.5)
        elif p == 'client':
            check('the client sees its purse back', client.get_controlled_pawn().get_wallet_component().get_copper() == 77)
            check('the client sees the restored jacket', jacket_equipped(client.get_controlled_pawn()))
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
