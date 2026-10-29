"""The Port general merchant sells the pack for Copper (listen server plus one client, EW_PLAY_PLAYERS=2).
The client stands before a Port merchant holding Wood x10, Ore x3 and a Repair Kit (no sell value): the merchant's prompt names the
total, one request pays it into the purse, sells the valued items, keeps the unvalued ones, and the client's purse agrees.
A second request with nothing left to sell changes nothing. Writes Saved/PortMerchantMultiplayerPlayResult.json."""
import json
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
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 14, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def count(owner, path):
    item = unreal.load_asset(path)
    return sum(e.quantity for e in owner.get_inventory_component().get_inventory_entries() if e.item_definition == item)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'PortMerchantMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK PortMerchantMultiplayer success={error is None} error={error}')


def stand_before(merchant, survivor, controller):
    loc, fwd = merchant.get_actor_location(), merchant.get_actor_forward_vector()
    if 'spot' not in state:
        for dist in (150, 110, 200, 90):
            for lift in (100, 140, 60):
                spot = unreal.Vector(loc.x + fwd.x * dist, loc.y + fwd.y * dist, loc.z + lift)
                if survivor.teleport(spot, unreal.Rotator()):
                    state['spot'] = spot
                    break
            if 'spot' in state:
                break
    else:
        survivor.teleport(state['spot'], unreal.Rotator())
    eye, _ = survivor.get_actor_eyes_view_point()
    controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(loc.x, loc.y, loc.z + 80)))


WOOD = '/Game/Elitewake/Items/Testing/DA_TestWood'
ORE = '/Game/Elitewake/Items/Testing/DA_TestOre'
KIT = '/Game/Elitewake/Items/Testing/DA_TestRepairKit'


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            merchants = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWMerchant)
            check('a merchant waits at each of the five Ports', len(merchants) == 5, found=len(merchants))
            check('the client sees them too', len(unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWMerchant)) == 5)
            owner = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            state['owner'] = owner
            state['merchant'] = merchants[0]
            state['mine'] = next(m for m in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWMerchant) if m.get_name() == merchants[0].get_name())
            pack = owner.get_inventory_component()
            pack.add_item(unreal.load_asset(WOOD), 10)
            pack.add_item(unreal.load_asset(ORE), 3)
            pack.add_item(unreal.load_asset(KIT), 1)
            owner.get_wallet_component().set_copper(0)
            state['worth'] = 10 * unreal.load_asset(WOOD).get_editor_property('sell_value_copper') + 3 * unreal.load_asset(ORE).get_editor_property('sell_value_copper')
            check('the test items are worth something', state['worth'] > 0, worth=state['worth'])
            stand_before(state['merchant'], owner, client)
            state.update(phase=1, at=time.monotonic() + 2.0, tries=0)
        elif p == 1:
            stand_before(state['merchant'], state['owner'], client)
            state.update(phase=15, at=time.monotonic() + 1.5)
        elif p == 15:
            report['prompt'] = str(state['merchant'].get_interaction_prompt(state['owner']))
            check('the client asks the merchant', lib.send_verification_interaction_request(client, state['mine']))
            state.update(phase=2, at=time.monotonic() + 1.5)
        elif p == 2:
            owner = state['owner']
            if owner.get_wallet_component().get_copper() == 0 and state['tries'] < 5:
                state['tries'] += 1
                report['retries'] = state['tries']
                stand_before(state['merchant'], owner, client)
                state.update(phase=15, at=time.monotonic() + 2.0)
                return
            check('the sale pays the total', owner.get_wallet_component().get_copper() == state['worth'], copper=owner.get_wallet_component().get_copper(), worth=state['worth'])
            check('the valued items are gone', count(owner, WOOD) == 0 and count(owner, ORE) == 0)
            check('the unvalued item stays', count(owner, KIT) == 1)
            check('the client\'s purse agrees', client.get_controlled_pawn().get_wallet_component().get_copper() == state['worth'])
            report['again_refused'] = not state['merchant'].interact(owner)
            state.update(phase=3, at=time.monotonic() + 1.0)
        elif p == 3:
            owner = state['owner']
            check('selling with nothing valued changes nothing', report['again_refused'] and owner.get_wallet_component().get_copper() == state['worth'])
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
