"""Shared ship's hold: a client stores cargo, the host takes some out, and reach is enforced.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the
sloop from Scripts/Setup/create_sloop_test_assets.py. Run unattended with run_play_check.py.

  1. The client holds Interact at the cargo hatch; the server agrees and the client's hold screen opens.
  2. The client stores a stack of Wood (granted in Play only) through the owned transfer request.
  3. The host, aboard the same ship, sees the stack and takes part of it out: the hold is shared.
  4. The client walks away from the ship; its hold screen closes by itself.
  5. A transfer request from out of reach is refused.
Writes Saved/ShipCargoPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ShipCargoPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host_pc = next(c for c in pcs if c.has_authority())
server_world, client_world = worlds[pcs.index(host_pc)], worlds[pcs.index(client)]
host = host_pc.get_controlled_pawn()
pawn = client.get_controlled_pawn()

def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']

crew = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
ship = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)[0]
peer = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if a.get_name() == ship.get_name())
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
assert wood, 'DA_TestWood is missing.'

settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'aim': None, 'handle': None, 'memo': {}}
DECK = 100 + 98

def hold_count(s):
    return s.get_cargo().get_item_count(wood)

def stand_near_hatch(character, side_offset):
    hatch = ship.get_cargo_hatch_world()
    forward = ship.get_actor_forward_vector()
    right = ship.get_actor_right_vector()
    spot = unreal.Vector(hatch.x - forward.x * 120 + right.x * side_offset, hatch.y - forward.y * 120 + right.y * side_offset,
                         ship.get_actor_location().z + DECK)
    return spot

def keep_aim():
    if state['aim']:
        hatch = ship.get_cargo_hatch_world()
        eye = crew.get_actor_location() + unreal.Vector(0, 0, crew.get_editor_property('base_eye_height'))
        rotation = unreal.MathLibrary.find_look_at_rotation(eye, hatch)
        crew.get_controller().set_control_rotation(rotation)
        client.set_control_rotation(rotation)

def entry_index(inventory, item):
    for i, entry in enumerate(inventory.get_inventory_entries()):
        if entry.get_editor_property('item_definition') == item:
            return i
    return -1

def open_hold():
    assert hold_count(ship) == 0, 'The hold must start empty'
    assert crew.get_inventory_component().add_item(wood, 40) == 40
    spot = stand_near_hatch(crew, 0)
    for p in (crew, pawn):
        assert p.teleport(spot, ship.get_actor_rotation())
    state['aim'] = True
    keep_aim()
    assert lib.send_verification_interaction_request(client, peer)

def store():
    state['aim'] = None
    index = entry_index(pawn.get_inventory_component(), wood)
    assert index >= 0, 'client copy shows no wood'
    assert lib.send_verification_container_transfer(client, peer, True, index, 40)

def host_takes():
    spot = stand_near_hatch(host, 120)
    assert host.teleport(spot, ship.get_actor_rotation())
    index = entry_index(ship.get_cargo(), wood)
    assert index >= 0, 'host sees no wood in the hold'
    assert lib.send_verification_container_transfer(host_pc, ship, False, index, 15)

def walk_away():
    beach = unreal.Vector(3000, 0, 300)
    for p in (crew, pawn):
        assert p.teleport(beach, unreal.Rotator(0, 0, 0))
    state['memo']['away_at'] = time.monotonic()

def far_request():
    crew.get_inventory_component().add_item(wood, 5)
    index = entry_index(pawn.get_inventory_component(), wood) if pawn.get_inventory_component().get_item_count(wood) else 0
    assert lib.send_verification_container_transfer(client, peer, True, max(index, 0), 5)
    state['memo']['far_at'] = time.monotonic()

def far_refused():
    if time.monotonic() - state['memo']['far_at'] < 1.5:
        return False
    assert hold_count(ship) == 25, f'hold changed to {hold_count(ship)}'
    return crew.get_inventory_component().get_item_count(wood) == 5

STEPS = [
    ('Client holds Interact at the hatch; the hold screen opens on the client', open_hold,
     lambda: client.get_open_container() == peer and client.is_inventory_open(), 6),
    ('Client stores 40 Wood; server and client agree on the hold and the ship load', store,
     lambda: hold_count(ship) == 40 and hold_count(peer) == 40 and crew.get_inventory_component().get_item_count(wood) == 0
     and ship.get_load() > 0 and abs(peer.get_load() - ship.get_load()) < 0.01, 6),
    ('Host aboard sees the stack and takes 15 out; the hold is shared', host_takes,
     lambda: host.get_inventory_component().get_item_count(wood) == 15 and hold_count(ship) == 25 and hold_count(peer) == 25, 6),
    ('Client leaves the ship; its hold screen closes by itself', walk_away,
     lambda: client.get_open_container() is None and not client.is_inventory_open(), 6),
    ('A transfer request from out of reach is refused', far_request, far_refused, 6),
]

def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    RESULT.write_text(json.dumps({
        'success': error is None, 'checks': checks, 'error': error,
        'state': {'hold_server': hold_count(ship), 'hold_client': hold_count(peer),
                  'crew_wood': crew.get_inventory_component().get_item_count(wood),
                  'host_wood': host.get_inventory_component().get_item_count(wood),
                  'client_screen': str(client.get_open_container())},
    }, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK ShipCargo success={error is None} error={error}')

def tick(delta):
    keep_aim()
    description, begin, done, timeout = STEPS[state['index']]
    try:
        if not state['begun']:
            begin()
            state.update(begun=True, deadline=time.monotonic() + timeout)
            return
        if done():
            checks.append(description)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
        elif time.monotonic() > state['deadline']:
            raise TimeoutError(f'not done within {timeout} s')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')

state['handle'] = unreal.register_slate_post_tick_callback(tick)
