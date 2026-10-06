"""Fresh Lvl_M5PickupTest PIE; standalone or in-process listen/client.

PIE-only water surfaces. Normal E/X input and owned-controller RPC rejection checks.
Checks authoritative hydration, replicated HUD and guards; restores state on completion.
"""
import unreal, json, os, datetime, traceback

lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert len(worlds) in (1, 2), 'Use fresh standalone or listen/client Play'
controllers = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
server = next(w for w, c in zip(worlds, controllers) if c.has_authority())
network = len(worlds) == 2
pc = next((c for c in controllers if not c.has_authority()), controllers[0])
local_world = worlds[controllers.index(pc)]
pawn = pc.get_controlled_pawn()
character_cls = unreal.load_class(None, '/Script/EW.EWCharacter')
water_cls = unreal.load_class(None, '/Script/EW.EWWaterSource')
pickup_cls = unreal.load_class(None, '/Script/EW.EWPickup')
def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']
player_id = pid(pawn)
server_pawn = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server, character_cls) if pid(p) == player_id)
stats = server_pawn.get_survival_component()
initial_hydration, initial_health = stats.get_hydration(), stats.get_health()
initial_inventory = server_pawn.get_inventory_component().get_used_slot_count()
saved_stats = [(p.get_survival_component(), p.get_survival_component().get_hydration())
               for p in unreal.GameplayStatics.get_all_actors_of_class(server, character_cls)]
def widget(name):
    cls = unreal.load_class(None, '/Script/EW.' + name)
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(local_world, cls, False) if w.get_owning_player() == pc)
prompt_widget, hud = widget('EWInteractionWidget'), widget('EWSurvivalWidget')
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
old_network = [(w, lib.get_verification_network_settings(w)) for w in worlds] if network else []
for w, _ in old_network: lib.set_verification_network_settings(w, 100, 1)
for c in controllers: lib.flush_verification_input(c)
pc.set_inventory_open(False)
for a in unreal.GameplayStatics.get_all_actors_of_class(server, pickup_cls): a.destroy_actor()
for w in worlds:
    for p in unreal.GameplayStatics.get_all_actors_of_class(w, character_cls):
        p.teleport(unreal.Vector(0, 0, 96) if pid(p) == player_id else unreal.Vector(-500, 500, 96), unreal.Rotator())
for c in controllers: c.set_control_rotation(unreal.Rotator())
source, walls = None, []
fixtures, steps = [], []
report = {'success': False, 'network': network, 'lag_ms': 100 if network else 0, 'loss_percent': 1 if network else 0,
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checkpoints': [], 'errors': []}
path = os.path.join(unreal.Paths.project_saved_dir(), 'WaterNetworkResult.json' if network else 'WaterPlayResult.json')
def valid(a):
    try: return a is not None and unreal.SystemLibrary.is_valid(a)
    except (TypeError, RuntimeError): return False
def step(action, delay=1): steps.append((action, delay))
def spawn(fresh=True, x=150):
    global source
    if valid(source): source.destroy_actor()
    source = lib.spawn_verification_water_source(server, unreal.Vector(x, 0, 160), fresh)
    assert source
    fixtures.append(source)
def peer():
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(local_world, water_cls) if a.get_name() == source.get_name())
def turn(yaw):
    for c in controllers: c.set_control_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0))
def tap(key): assert lib.send_verification_ui_key(pc, key)
def request(): assert lib.send_verification_interaction_request(pc, peer())
def check(label, value, prompt=None):
    values = [stats.get_hydration(), pawn.get_survival_component().get_hydration()]
    text, summary = str(prompt_widget.get_displayed_prompt()), str(hud.get_displayed_summary())
    assert all(abs(v - value) < .01 for v in values), label + ': hydration differs ' + str(values)
    assert 'Hydration ' + str(int(value)) + '%' in summary, label + ': rendered HUD differs ' + summary
    if prompt is not None:
        assert (prompt in text) if prompt else not text, label + ': unexpected prompt ' + text
    assert server_pawn.get_inventory_component().get_used_slot_count() == initial_inventory, 'Drinking mutated inventory'
    report['checkpoints'].append({'label': label, 'hydration': values, 'prompt': text, 'hud': summary})
def blocker():
    # This editor-only geometry helper deliberately does not replicate. Place equivalent
    # local query geometry in each PIE world to verify both presentation and authority.
    for w in worlds:
        a = lib.spawn_verification_box(w, unreal.Vector(75, 0, 160), unreal.Vector(10, 100, 100), unreal.Rotator())
        walls.append(a)
        fixtures.append(a)
def remove_walls():
    for a in walls:
        if valid(a): a.destroy_actor()
    walls.clear()
def close_menu(): tap('I'); turn(0)
def compete():
    for p in unreal.GameplayStatics.get_all_actors_of_class(server, character_cls):
        p.get_survival_component().set_hydration(8)
        p.teleport(unreal.Vector(0, -60 if pid(p) == player_id else 60, 96), unreal.Rotator())
    pawn.teleport(unreal.Vector(0, -60, 96), unreal.Rotator())
    source.set_actor_scale3d(unreal.Vector(1, 3, 1))
    turn(0)
def competing_requests():
    for c, w in zip(controllers, worlds):
        a = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, water_cls) if a.get_name() == source.get_name())
        assert lib.send_verification_interaction_request(c, a)
def check_competition():
    values = [p.get_survival_component().get_hydration() for p in unreal.GameplayStatics.get_all_actors_of_class(server, character_cls)]
    assert all(v == 100 for v in values), 'Shared source hydration differs: ' + str(values)
    check('Shared source independently hydrates survivors', 100, '')

step(spawn); step(lambda: stats.set_hydration(12)); step(lambda: check('Standing fresh-water E prompt and low HUD', 12, 'E: Drink fresh water'))
step(lambda: tap('E')); step(lambda: check('E instantly refills authoritative hydration and HUD', 100, ''))
step(request); step(lambda: check('Repeated request at full is harmless', 100, ''))
if network:
    step(lambda: pawn.get_survival_component().set_hydration(0))
    step(lambda: check('Client cannot mutate hydration directly', 100, ''))
step(lambda: stats.set_hydration(0)); step(lambda: tap('Gamepad_FaceButton_Left')); step(lambda: check('Controller X drinks from empty', 100, ''))
step(lambda: stats.set_hydration(12)); step(lambda: check('Source reusable; X prompt returns', 12, 'X: Drink fresh water'))
step(lambda: spawn(False)); step(request); step(lambda: check('Salt water grants no hydration', 12, ''))
step(spawn); step(lambda: source.set_editor_property('bAvailable', False)); step(request); step(lambda: check('Unavailable water rejected', 12, ''))
step(lambda: spawn(x=450)); step(request); step(lambda: check('Distant water rejected', 12, ''))
step(spawn); step(blocker); step(request); step(lambda: check('Obstructed water rejected', 12, '')); step(remove_walls)
step(lambda: turn(90)); step(request); step(lambda: check('Unaimed water rejected', 12, '')); step(lambda: turn(0))
step(lambda: tap('I')); step(request); step(lambda: check('Inventory-open request rejected', 12, '')); step(close_menu)
step(lambda: stats.apply_damage(100)); step(request); step(lambda: check('Dead survivor request rejected', 12, '')); step(lambda: stats.restore_health(100))
step(compete); step(competing_requests); step(check_competition)

index, next_time, handle = 0, unreal.GameplayStatics.get_time_seconds(server) + 1, None
def finish():
    unreal.unregister_slate_post_tick_callback(handle)
    for c in controllers: lib.flush_verification_input(c)
    if pc.get_interaction_component().is_menu_blocked(): tap('I')
    for component, hydration in saved_stats: component.set_hydration(hydration)
    stats.restore_health(max(0, initial_health - stats.get_health()))
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
