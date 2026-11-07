"""Fresh Lvl_M5PickupTest PIE: Metal-gated finite resource, replicated depletion and timed respawn."""
import datetime
import json
import math
import os
import traceback

import unreal

lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert len(worlds) in (1, 2) and all('Lvl_M5PickupTest' in w.get_name() for w in worlds)
controllers = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
server = next(w for w, c in zip(worlds, controllers) if c.has_authority())
network = len(worlds) == 2
pc = next((c for c in controllers if not c.has_authority()), controllers[0])
local_world = worlds[controllers.index(pc)]
character_cls = unreal.load_class(None, '/Script/EW.EWCharacter')
node_cls = unreal.load_class(None, '/Script/EW.EWMineable')
pickup_cls = unreal.load_class(None, '/Script/EW.EWPickup')
widget_cls = unreal.load_class(None, '/Script/EW.EWInteractionWidget')
stone = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestStone')
generic_pick = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestPickaxe')
metal_pick = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestMetalPickaxe')
assert stone and generic_pick and metal_pick

def player_id(pawn):
    state = pawn.get_editor_property('PlayerState')
    return json.loads(unreal.ToolsetLibrary.get_object_properties(state, ['PlayerId']))['PlayerId']

server_pawns = unreal.GameplayStatics.get_all_actors_of_class(server, character_cls)
local_pawn = pc.get_controlled_pawn()
owner = next(p for p in server_pawns if player_id(p) == player_id(local_pawn))
widget = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(local_world, widget_cls, False)
              if w.get_owning_player() == pc)
inventory = owner.get_inventory_component()
equipment = owner.get_equipment_component()
node = None
fixtures = []
steps = []
report = {'success': False, 'network': network, 'checkpoints': [], 'errors': [],
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
result = os.path.join(unreal.Paths.project_saved_dir(), 'ResourceMiningLifecyclePlayResult.json')
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
old_network = [(w, lib.get_verification_network_settings(w)) for w in worlds] if network else []
for w, _ in old_network:
    lib.set_verification_network_settings(w, 100, 1)

def valid(actor):
    try:
        return actor is not None and unreal.SystemLibrary.is_valid(actor)
    except (TypeError, RuntimeError):
        return False

def peers():
    return [next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, node_cls)
                 if a.get_name() == node.get_name()) for w in worlds]

def step(action, delay=0.5):
    steps.append((action, delay))

def prepare():
    local_player_id = player_id(pc.get_controlled_pawn())
    for pickup in unreal.GameplayStatics.get_all_actors_of_class(server, pickup_cls):
        pickup.destroy_actor()
    for pawn in server_pawns:
        inv = pawn.get_inventory_component()
        inv.remove_item(stone, 100000)
        inv.remove_item(generic_pick, 100)
        inv.remove_item(metal_pick, 100)
        pawn.get_equipment_component().unequip_item(unreal.EWEquipmentSlot.MAIN_HAND)
    for w in worlds:
        for pawn in unreal.GameplayStatics.get_all_actors_of_class(w, character_cls):
            pawn.teleport(unreal.Vector(0, 0, 96) if player_id(pawn) == local_player_id
                          else unreal.Vector(-500, 500, 96), unreal.Rotator())
            pawn.set_actor_rotation(unreal.Rotator(), False)
    for controller in controllers:
        controller.set_control_rotation(unreal.Rotator())
        lib.flush_verification_input(controller)
    inventory.add_item(generic_pick, 1)
    assert lib.send_verification_equipment_request(pc, generic_pick, unreal.EWEquipmentSlot.MAIN_HAND)

def spawn_node():
    global node
    node = lib.spawn_verification_mineable(
        server, unreal.Vector(150, 0, 160), stone, 4, 8, unreal.EWPickaxeTier.METAL,
        True, 2.0, True, 4, 8)
    assert node
    fixtures.append(node)

def aim_at_node():
    for w, controller in zip(worlds, controllers):
        pawn = controller.get_controlled_pawn()
        eye = pawn.get_actor_location() + unreal.Vector(0, 0, 64)
        delta = peers()[worlds.index(w)].get_actor_location() - eye
        yaw = math.degrees(math.atan2(delta.y, delta.x))
        pitch = math.degrees(math.atan2(delta.z, math.hypot(delta.x, delta.y)))
        rotation = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0)
        pawn.set_actor_rotation(rotation, False)
        controller.set_control_rotation(rotation)

def assert_node_is_aimed():
    server_target = lib.get_verification_interaction_target(owner)
    client_target = lib.get_verification_interaction_target(pc.get_controlled_pawn())
    assert server_target == node, f'server trace target was {server_target}'
    assert client_target == peers()[worlds.index(local_world)], f'client trace target was {client_target}'

def check_initial_stock():
    copies = peers()
    counts = [int(a.get_editor_property('remaining')) for a in copies]
    assert all(4 <= count <= 8 for count in counts), f'initial stock out of range: {counts}'
    assert all(a.get_editor_property('mesh').is_visible() for a in copies), 'initial resource art is hidden'
    assert not node.can_mine(owner), 'generic pickaxe bypassed the Metal minimum'
    report['checkpoints'].append({'name': '4-8 stock and Metal gate', 'stocks': counts, 'generic_pick_rejected': True})

def generic_attack_did_not_mine():
    assert int(node.get_editor_property('remaining')) in range(4, 9), 'generic pickaxe mined a restricted node'
    assert inventory.get_item_count(stone) == 0, 'generic pickaxe yielded the restricted resource'
    prompt = str(widget.get_displayed_prompt())
    assert not prompt, f'a rock shows no prompt, even for the wrong tool: {prompt!r}'
    report['checkpoints'].append({'name': 'generic pickaxe rejected', 'stock': int(node.get_editor_property('remaining'))})

def equip_metal_pick():
    inventory.add_item(metal_pick, 1)
    assert lib.send_verification_equipment_request(pc, metal_pick, unreal.EWEquipmentSlot.MAIN_HAND)

def check_metal_pick():
    assert equipment.get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) == metal_pick, 'Metal test pick did not equip'
    assert node.can_mine(owner), 'Metal pick did not satisfy the minimum tier'
    prompt = str(widget.get_displayed_prompt())
    assert not prompt, f'a rock shows no prompt: {prompt!r}'
    report['checkpoints'].append({'name': 'Metal pick accepted'})

def mine_deposit():
    assert lib.send_verification_attack(pc, peers()[controllers.index(pc)])

def swing_generic_pick():
    assert lib.send_verification_attack(pc, peers()[controllers.index(pc)])

def check_depleted():
    copies = peers()
    stocks = [int(a.get_editor_property('remaining')) for a in copies]
    assert all(count == 0 for count in stocks), f'deposit did not deplete on every machine: {stocks}'
    assert all(not a.get_editor_property('mesh').is_visible() for a in copies), 'depleted deposit still visible'
    assert all(a.get_editor_property('mesh').get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION for a in copies), 'depleted deposit still collides'
    assert inventory.get_item_count(stone) in range(4, 9), 'harvested node did not award its complete 4-8 stock'
    assert not node.is_actor_being_destroyed(), 'timed deposit was destroyed instead of retained'
    report['checkpoints'].append({'name': 'depletion hides and disables collision', 'stocks': stocks,
                                  'harvested': inventory.get_item_count(stone)})

def check_respawn():
    copies = peers()
    stocks = [int(a.get_editor_property('remaining')) for a in copies]
    assert all(count in range(4, 9) for count in stocks), f'respawn stock out of range: {stocks}'
    assert all(a.get_editor_property('mesh').is_visible() for a in copies), 'respawn did not restore visibility'
    assert all(a.get_editor_property('mesh').get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION for a in copies), 'respawn did not restore collision'
    report['checkpoints'].append({'name': 'timed respawn replicates', 'stocks': stocks})

step(prepare, 0.5)
step(spawn_node, 0.5)
step(aim_at_node, 0.5)
step(assert_node_is_aimed, 0.5)
step(check_initial_stock)
step(swing_generic_pick, 0.5)
step(generic_attack_did_not_mine)
step(equip_metal_pick, 0.5)
step(check_metal_pick)
step(mine_deposit, 0.75)
step(check_depleted, 2.75)
step(check_respawn)

index = 0
next_time = unreal.GameplayStatics.get_time_seconds(server) + 1
handle = None

def finish(error=None):
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)
    for controller in controllers:
        lib.flush_verification_input(controller)
    for pawn in server_pawns:
        pawn.get_equipment_component().unequip_item(unreal.EWEquipmentSlot.MAIN_HAND)
        pawn.get_inventory_component().remove_item(generic_pick, 100)
        pawn.get_inventory_component().remove_item(metal_pick, 100)
        pawn.get_inventory_component().remove_item(stone, 100000)
    for fixture in fixtures:
        if valid(fixture):
            fixture.destroy_actor()
    for w, old in old_network:
        lib.set_verification_network_settings(w, old.x, old.y)
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    if error:
        report['errors'].append(error)
    report['success'] = not report['errors'] and index == len(steps)
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(result, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def tick(delta):
    global index, next_time
    try:
        assert all(w in lib.get_play_worlds() for w in worlds), 'Play ended during verification'
        now = unreal.GameplayStatics.get_time_seconds(server)
        if now < next_time:
            return
        if index == len(steps):
            finish()
            return
        action, delay = steps[index]
        action()
        index += 1
        next_time = now + delay
    except Exception:
        finish(traceback.format_exc())

handle = unreal.register_slate_post_tick_callback(tick)
