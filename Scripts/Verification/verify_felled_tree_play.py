"""Two-player check: server fells an existing coastal oak; client collides with and harvests the replicated log."""
import datetime, json, os, traceback
import unreal

lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Run as listen server plus one client'
controllers = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
server = next(w for w, c in zip(worlds, controllers) if c.has_authority())
client_world = next(w for w, c in zip(worlds, controllers) if not c.has_authority())
client = controllers[worlds.index(client_world)]
character_cls = unreal.load_class(None, '/Script/EW.EWCharacter')
tree_cls = unreal.load_class(None, '/Script/EW.EWHarvestTree')
trees = unreal.GameplayStatics.get_all_actors_of_class(server, tree_cls)
server_pawns = unreal.GameplayStatics.get_all_actors_of_class(server, character_cls)
client_pawns = unreal.GameplayStatics.get_all_actors_of_class(client_world, character_cls)

def player_id(pawn):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(
        pawn.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']

client_id = player_id(client.get_controlled_pawn())
owner = next(p for p in server_pawns if player_id(p) == client_id)
client_pawn = client.get_controlled_pawn()
peer = lambda actor: next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, tree_cls)
                          if a.get_name() == actor.get_name())
oak_candidates = [t for t in trees if str(t.get_actor_label()).lower().startswith('oak')]
assert oak_candidates, 'Coastal map needs its generated Plains oaks'
tree = min(oak_candidates, key=lambda t: unreal.Vector.distance(t.get_actor_location(), owner.get_actor_location()))
tree_name = tree.get_name()
wood = tree.get_editor_property('wood')
thatch = tree.get_editor_property('thatch')
hatchet = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatchet')
assert wood and thatch and hatchet
assert tree.get_editor_property('wood_remaining') == 12 and tree.get_editor_property('thatch_remaining') == 4, \
    'Use a fresh coastal map with the standard tree stock'
inventory = owner.get_inventory_component()
inventory.remove_item(wood, 100000)
inventory.remove_item(thatch, 100000)
inventory.remove_item(hatchet, 100000)
original_client_location = client_pawn.get_actor_location()
steps = []
report = {'success': False, 'checkpoints': [], 'errors': [], 'network': True}
path = os.environ.get('EW_PLAY_RESULT', unreal.Paths.project_saved_dir() + 'FelledTreePlayResult.json')

def check(label, passed, details=None):
    assert passed, label + ': ' + str(details)
    report['checkpoints'].append({'label': label, 'details': details})

def action(delay, fn):
    steps.append((delay, fn))

def fell():
    check('Server fells the nearest Oak once', tree.fell(unreal.Vector(1, 0, 0)), tree.get_actor_label())
    check('Second fall request is ignored', not tree.fell(unreal.Vector(0, 1, 0)))

def replicated_fall():
    client_tree = peer(tree)
    up = client_tree.get_actor_up_vector()
    blocker = client_tree.get_editor_property('Blocker')
    check('Client sees the tree lying after the server fall', client_tree.is_felled() and up.x > .95,
          {'up_x': up.x, 'up_y': up.y, 'up_z': up.z})
    check('Client receives a solid blocker aligned to the log',
          blocker.get_collision_enabled() == unreal.CollisionEnabled.QUERY_AND_PHYSICS
          and blocker.get_up_vector().x > .95, str(blocker.get_collision_enabled()))
    check('Fall leaves the tree stock untouched',
          tree.get_editor_property('wood_remaining') == 12 and tree.get_editor_property('thatch_remaining') == 4)

def begin_walk():
    location = tree.get_actor_location()
    start = unreal.Vector(location.x - 600, location.y, location.z + 96)
    client_pawn.teleport(start, unreal.Rotator())
    client.set_control_rotation(unreal.Rotator())
    report['walk_start_x'] = client_pawn.get_actor_location().x
    check('Client movement input begins', lib.send_verification_gameplay_key_state(client, 'W', True))

def end_walk():
    lib.send_verification_gameplay_key_state(client, 'W', False)
    end_x = client_pawn.get_actor_location().x
    report['walk_end_x'] = end_x
    check('Client moves into but cannot pass through the fallen log',
          report['walk_start_x'] + 100 < end_x < tree.get_actor_location().x - 35,
          {'start_x': report['walk_start_x'], 'end_x': end_x, 'tree_x': tree.get_actor_location().x})

def equip_and_chop():
    inventory.add_item(hatchet, 1)
    check('Client equips the hatchet', lib.send_verification_equipment_request(
        client, hatchet, unreal.EWEquipmentSlot.MAIN_HAND))

def request_strike():
    check('Client attack input accepted', lib.send_verification_attack(client, peer(tree)))

def check_strike(expected):
    wood_count = inventory.get_item_count(wood)
    thatch_count = inventory.get_item_count(thatch)
    check('Hatchet gives only the tree stock left at its established rate',
          wood_count == expected * 3 and thatch_count == expected,
          {'wood': wood_count, 'thatch': thatch_count, 'strikes': expected})
    if expected < 4:
        remaining = (tree.get_editor_property('wood_remaining'), tree.get_editor_property('thatch_remaining'))
        check('Each strike deducts exactly its accepted yield', remaining == (12 - expected * 3, 4 - expected), remaining)
    else:
        check('Empty log follows the existing actor cleanup',
              not any(a.get_name() == tree_name for a in unreal.GameplayStatics.get_all_actors_of_class(server, tree_cls)))

action(2.5, fell)
action(2.5, replicated_fall)
action(.1, begin_walk)
action(1.5, end_walk)
action(.2, equip_and_chop)
for hits in range(1, 5):
    action(.1, request_strike)
    action(1.2, lambda n=hits: check_strike(n))

index = 0
next_time = unreal.GameplayStatics.get_time_seconds(server) + 1
handle = None

def finish():
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
    lib.send_verification_gameplay_key_state(client, 'W', False)
    if client_pawn and not client_pawn.is_actor_being_destroyed():
        client_pawn.teleport(original_client_location, unreal.Rotator())
    report['success'] = not report['errors'] and index == len(steps)
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(path, 'w', encoding='utf-8') as result:
        json.dump(report, result, indent=2)

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
        delay, fn = steps[index]
        fn()
        index += 1
        next_time = now + delay
    except Exception:
        report['errors'].append(traceback.format_exc())
        finish()

handle = unreal.register_slate_post_tick_callback(tick)
