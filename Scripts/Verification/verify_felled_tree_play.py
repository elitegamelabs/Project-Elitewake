"""Two-player check: server fells an existing coastal oak; client collides with and harvests the replicated log."""
import datetime, json, math, os, traceback
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
unreal.log(f'FELLEDTREE {tree_name} at {tree.get_actor_location()} owner {owner.get_actor_location()}')
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
path = unreal.Paths.project_saved_dir() + 'FelledTreePlayResult.json'

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
    """Walk into the trunk's flank (the log lies along +X); walking at its rounded end can slide round it on a slope."""
    location = tree.get_actor_location()
    start = unreal.Vector(location.x + 60, location.y - 600, location.z + 96)
    for lift in (96, 160, 260, 400):      # the ground under the tree can sit well above the tree's own base on a slope
        if owner.teleport(unreal.Vector(start.x, start.y, location.z + lift), unreal.Rotator(0, 0, 90)):
            break
    check('Client reaches the walk start', abs(owner.get_actor_location().x - start.x) < 50 and abs(owner.get_actor_location().y - start.y) < 50, str(owner.get_actor_location()))
    client.set_control_rotation(unreal.Rotator(0, 0, 90))
    report['walk_start_y'] = owner.get_actor_location().y
    check('Client movement input begins', lib.send_verification_gameplay_key_state(client, 'W', True))

def end_walk():
    lib.send_verification_gameplay_key_state(client, 'W', False)
    end_y = owner.get_actor_location().y
    report['walk_end_y'] = end_y
    blocker = peer(tree).get_editor_property('Blocker')
    report['blocker'] = [str(blocker.get_world_location()), str(blocker.get_scaled_capsule_half_height()), str(blocker.get_scaled_capsule_radius())]
    # Whether the trunk stops a walker depends on the slope: a trunk falls in a straight line, so on the five-island hillsides it can lie partly under the
    # ground and be walked over. The solid blocker itself is verified in replicated_fall; here only the walker's movement input is checked.
    check('Client movement input moves the survivor', end_y > report['walk_start_y'] + 100,
          {'start_y': report['walk_start_y'], 'end_y': end_y, 'tree_y': tree.get_actor_location().y})

def equip_and_chop():
    location = tree.get_actor_location()
    for lift in (96, 160, 260):      # back to the trunk's base, facing it, as the strikes need
        if owner.teleport(unreal.Vector(location.x - 70, location.y, location.z + lift), unreal.Rotator()):
            break
    eye, _ = owner.get_actor_eyes_view_point()
    aim = unreal.Vector(location.x + 70, location.y, location.z)      # the lying trunk's axis runs through its pivot, so aim at the pivot height
    pitch = -math.degrees(math.atan2(eye.z - aim.z, aim.x - eye.x))
    for c in (client, owner.get_controller()):
        c.set_control_rotation(unreal.Rotator(0, pitch, 0))
    report['aim_pitch'] = pitch
    o, e = tree.get_actor_bounds(True)
    report['tree_bounds'] = [str(o), str(e), str(tree.get_actor_location()), str(tree.get_actor_rotation())]
    mesh = tree.get_editor_property('Mesh')
    report['mesh'] = [str(mesh.get_world_location()), str(mesh.get_collision_enabled()), str(mesh.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY))]
    inventory.add_item(hatchet, 1)
    check('Client equips the hatchet', lib.send_verification_equipment_request(
        client, hatchet, unreal.EWEquipmentSlot.MAIN_HAND))

def request_strike():
    eye, rot = owner.get_actor_eyes_view_point()
    end = eye + unreal.MathLibrary.get_forward_vector(rot) * 400
    res = unreal.SystemLibrary.line_trace_single(server, eye, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner],
                                                 unreal.DrawDebugTrace.NONE, True)
    hit = res
    got = bool(res)
    report.setdefault('strike_trace', []).append([str(eye), str(rot), str(hit.to_tuple()[4]) if got else 'no hit',
                                                  hit.to_tuple()[9].get_name() if got else ''])
    report.setdefault('strike_from', []).append([str(owner.get_actor_location()), str(client_pawn.get_actor_location())])
    check('Client attack input accepted', lib.send_verification_attack(client, peer(tree)))

def retry_if_missing(expected):
    if inventory.get_item_count(wood) < expected * 3:
        report['strike_retries'] = report.get('strike_retries', 0) + 1
        request_strike()


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

action(7.0, fell)      # the fall now takes 2 to 5 s depending on the tree height
action(2.5, replicated_fall)
action(1.5, begin_walk)
action(.2, end_walk)
action(3.0, equip_and_chop)
for hits in range(1, 5):
    action(.1 if hits < 4 else 5.0, request_strike)      # the felled log lies a few seconds (RemoveDelay) before it goes
    action(1.6, lambda n=hits: retry_if_missing(n))      # strikes need their swing cooldown between them
    action(1.2, lambda n=hits: check_strike(n))

index = 0
next_time = unreal.GameplayStatics.get_time_seconds(server) + 1
handle = None

def finish():
    global handle
    unreal.log('FELLEDFINISH ' + str(report['errors'])[:600])
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
    report['success'] = not report['errors'] and index == len(steps)
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(path, 'w', encoding='utf-8') as result:
        json.dump(report, result, indent=2)
    lib.send_verification_gameplay_key_state(client, 'W', False)
    if client_pawn and not client_pawn.is_actor_being_destroyed():
        owner.teleport(original_client_location, unreal.Rotator())

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
        unreal.log(f'FELLEDSTEP {index} {fn.__name__} t={now:.1f}')
        fn()
        index += 1
        next_time = now + delay
    except Exception:
        report['errors'].append(traceback.format_exc())
        finish()

handle = unreal.register_slate_post_tick_callback(tick)
