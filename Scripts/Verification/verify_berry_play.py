"""Fresh Lvl_M5PickupTest PIE, standalone or in-process listen/client.
Normal Slate E/X and ordinary owned-controller RPCs. PIE-only finite resource pools;
checks authoritative/replicated conservation, prompts, weight and invalid requests.
"""
import unreal, json, os, traceback, datetime
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert len(worlds) in (1, 2) and all('Lvl_M5PickupTest' in w.get_name() for w in worlds)
controllers = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
server = next(w for w, c in zip(worlds, controllers) if c.has_authority())
network = len(worlds) == 2
pc = next((c for c in controllers if not c.has_authority()), controllers[0])
local_world = worlds[controllers.index(pc)]
character_cls = unreal.load_class(None, '/Script/EW.EWCharacter')
pickup_cls = unreal.load_class(None, '/Script/EW.EWPickup')
node_cls = unreal.load_class(None, '/Script/EW.EWHandGatherable')
berry = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestAzulBerry')
sticks = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestSticks')
assert berry and sticks, 'Run create_berry_test_asset.py first'
def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']
player_id = pid(pc.get_controlled_pawn())
server_pawns = unreal.GameplayStatics.get_all_actors_of_class(server, character_cls)
server_pawn = next(p for p in server_pawns if pid(p) == player_id)
widget_cls = unreal.load_class(None, '/Script/EW.EWInteractionWidget')
prompt_widget = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(local_world, widget_cls, False) if w.get_owning_player() == pc)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
old_network = [(w, lib.get_verification_network_settings(w)) for w in worlds] if network else []
for w, _ in old_network: lib.set_verification_network_settings(w, 100, 1)
for c in controllers: lib.flush_verification_input(c)
pc.set_inventory_open(False)
for p in server_pawns: assert not p.get_inventory_component().get_inventory_entries(), 'Use fresh empty Play'
for a in unreal.GameplayStatics.get_all_actors_of_class(server, pickup_cls): a.destroy_actor()
for w in worlds:
    for p in unreal.GameplayStatics.get_all_actors_of_class(w, character_cls):
        p.teleport(unreal.Vector(0, 0, 96) if pid(p) == player_id else unreal.Vector(-500, 500, 96), unreal.Rotator())
for c in controllers: c.set_control_rotation(unreal.Rotator())
node, fixtures, walls, steps = None, [], [], []
report = {'success': False, 'network': network, 'lag_ms': 100 if network else 0, 'loss_percent': 1 if network else 0,
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checkpoints': [], 'errors': []}
path = os.path.join(unreal.Paths.project_saved_dir(), 'BerryNetworkResult.json' if network else 'BerryPlayResult.json')
def valid(a):
    try: return a is not None and unreal.SystemLibrary.is_valid(a)
    except (TypeError, RuntimeError): return False
def step(action, delay=1): steps.append((action, delay))
def spawn(item=berry, quantity=10, x=150):
    global node
    if valid(node): node.destroy_actor()
    node = lib.spawn_verification_hand_gatherable(server, unreal.Vector(x, 0, 160), item, quantity, item == sticks)
    assert node
    fixtures.append(node)
    if item == berry:
        node.set_editor_property('gathering_kind',unreal.EWHandGatheringKind.BERRIES); node.force_net_update()
def nodes(w): return unreal.GameplayStatics.get_all_actors_of_class(w, node_cls)
def peer(w): return next(a for a in nodes(w) if a.get_name() == node.get_name())
def request(): assert lib.send_verification_interaction_request(pc, peer(local_world))
def tap(name): assert lib.send_verification_ui_key(pc, name)
def turn(yaw):
    for c in controllers: c.set_control_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0))
def empty():
    for p in server_pawns:
        for item in (berry, sticks): p.get_inventory_component().remove_item(item, 100000)
def check(label, total_berry, total_sticks, remaining, prompt=None):
    rows = []
    for w in worlds:
        rows.append({str(pid(p)): [p.get_inventory_component().get_item_count(berry), p.get_inventory_component().get_item_count(sticks)]
                     for p in unreal.GameplayStatics.get_all_actors_of_class(w, character_cls)})
    assert all(r == rows[0] for r in rows), label + ': player inventory replication differs ' + str(rows)
    assert all(sum(v[0] for v in r.values()) == total_berry and sum(v[1] for v in r.values()) == total_sticks for r in rows), label + ': totals differ ' + str(rows)
    pools = [sum(a.get_editor_property('quantity') for a in nodes(w)) for w in worlds]
    assert all(v == remaining for v in pools), label + ': resource pool differs ' + str(pools)
    text = str(prompt_widget.get_displayed_prompt())
    if prompt is not None: assert (prompt in text) if prompt else not text, label + ': unexpected prompt ' + text
    weight = server_pawn.get_inventory_component().get_total_weight()
    assert abs(weight - server_pawn.get_survival_component().get_carried_weight()) < .001, 'Survival weight differs'
    report['checkpoints'].append({'label': label, 'inventory_by_world': rows, 'remaining_by_world': pools, 'prompt': text, 'owner_weight': weight})
def blocker():
    for w in worlds:
        a = lib.spawn_verification_box(w, unreal.Vector(75, 0, 160), unreal.Vector(10, 100, 100), unreal.Rotator())
        walls.append(a); fixtures.append(a)
def remove_walls():
    for a in walls:
        if valid(a): a.destroy_actor()
    walls.clear()
def close_menu(): tap('I'); turn(0)
def competition():
    for w in worlds:
        for p in unreal.GameplayStatics.get_all_actors_of_class(w, character_cls):
            p.teleport(unreal.Vector(0, -60 if pid(p) == player_id else 60, 96), unreal.Rotator())
    node.set_actor_scale3d(unreal.Vector(1, 5, 2)); turn(0)
def competing_requests():
    for c, w in zip(controllers, worlds): assert lib.send_verification_interaction_request(c, peer(w))

step(spawn); step(lambda: check('Berry E prompt; fresh inventory', 0, 0, 10, 'E: Gather Azul Berry'))
step(lambda: tap('E')); step(lambda: check('E gathers finite berry pool exactly once', 10, 0, 0, ''))
step(empty); step(spawn); step(lambda: tap('Gamepad_FaceButton_Left')); step(lambda: check('X gathers berries',10,0,0,''))
step(lambda: spawn(sticks, 6)); step(lambda: tap('Gamepad_FaceButton_Left')); step(lambda: check('X collects sticks and updates weight', 10, 6, 0, ''))
step(lambda: spawn(sticks, 6)); step(lambda: check('Controller collect prompt', 10, 6, 6, 'X: Collect Sticks'))
step(lambda: spawn(x=450)); step(request); step(lambda: check('Distant gather rejected', 10, 6, 10, ''))
step(spawn); step(blocker); step(request); step(lambda: check('Obstructed gather rejected', 10, 6, 10, '')); step(remove_walls)
step(lambda: turn(90)); step(request); step(lambda: check('Unaimed gather rejected', 10, 6, 10, '')); step(lambda: turn(0))
step(lambda: tap('I')); step(request); step(lambda: check('Inventory-open gather rejected', 10, 6, 10, '')); step(close_menu)
step(lambda: server_pawn.get_survival_component().apply_damage(100)); step(request); step(lambda: check('Dead survivor gather rejected', 10, 6, 10, '')); step(lambda: server_pawn.get_survival_component().restore_health(100))
step(empty); step(lambda: server_pawn.get_inventory_component().add_item(berry, 11997)); step(spawn); step(lambda: tap('E'))
step(lambda: check('Partial capacity preserves seven units', 12000, 0, 7))
step(request); step(lambda: check('Full inventory preserves world remainder', 12000, 0, 7))
step(lambda: server_pawn.get_inventory_component().remove_item(berry, 7)); step(request); step(lambda: check('Freed capacity collects remainder once', 12000, 0, 0, ''))
step(empty); step(spawn); step(competition); step(competing_requests); step(lambda: check('Competing requests conserve one shared pool', 10, 0, 0, ''))

index, next_time, handle = 0, unreal.GameplayStatics.get_time_seconds(server) + 1, None
def finish():
    unreal.unregister_slate_post_tick_callback(handle)
    for c in controllers: lib.flush_verification_input(c)
    if pc.get_interaction_component().is_menu_blocked(): tap('I')
    server_pawn.get_survival_component().restore_health(100)
    empty()
    for a in fixtures:
        if valid(a): a.destroy_actor()
    for w, old in old_network: lib.set_verification_network_settings(w, old.x, old.y)
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    report['success'] = not report['errors'] and index == len(steps)
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(path, 'w') as f: json.dump(report, f, indent=2)
def tick(delta):
    global index, next_time
    try:
        assert all(w in lib.get_play_worlds() for w in worlds), 'Play ended during verification'
        now = unreal.GameplayStatics.get_time_seconds(server)
        if now < next_time: return
        if index == len(steps): finish(); return
        action, delay = steps[index]; action(); index += 1; next_time = now + delay
    except Exception:
        report['errors'].append(traceback.format_exc()); finish()
handle = unreal.register_slate_post_tick_callback(tick)
