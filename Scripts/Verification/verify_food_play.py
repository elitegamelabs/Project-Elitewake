"""Fresh Lvl_M5PickupTest standalone or in-process listen/client Play.
Exercises Slate R/X and hotbar keyboard/controller chords, ordinary owned food RPCs,
replicated effects, freshness batches and inedible conversion. An editor-only clock
offset checks expiry without changing the saved 1200-second policy. Restores state.
"""
import unreal, json, os, time, traceback
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert len(worlds) in (1, 2)
controllers = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
server = next(w for w, c in zip(worlds, controllers) if c.has_authority())
pc = next((c for c in controllers if not c.has_authority()), controllers[0])
world = worlds[controllers.index(pc)]
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']
owner_id = pid(pc.get_controlled_pawn())
def characters(w): return unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWCharacter)
owner = next(p for p in characters(server) if pid(p) == owner_id)
inv = owner.get_inventory_component(); survival = owner.get_survival_component()
assert all(not p.get_inventory_component().get_inventory_entries() for p in characters(server)), 'Use fresh empty Play'
berry = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestAzulBerry')
toxic = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestToxicBerry')
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
assert berry and toxic and berry.get_editor_property('fresh_lifetime_seconds') == 1200
assert str(berry.get_editor_property('item_id')) == 'Test.AzulBerry'
assert 'Azren' in str(berry.get_editor_property('display_name'))
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
saved_stats = [(p.get_survival_component(), p.get_survival_component().get_hunger(), p.get_survival_component().get_health()) for p in characters(server)]
old_network = [(w, lib.get_verification_network_settings(w)) for w in worlds] if len(worlds) == 2 else []
for w, _ in old_network: assert lib.set_verification_network_settings(w, 100, 1)
for c in controllers: lib.flush_verification_input(c)
pc.set_inventory_open(False)
for a in unreal.GameplayStatics.get_all_actors_of_class(server, unreal.EWPickup): a.destroy_actor()
for w in worlds:
    for p in characters(w): p.teleport(unreal.Vector(0, 0, 96) if pid(p) == owner_id else unreal.Vector(-500, 500, 96), unreal.Rotator())
for c in controllers: c.set_control_rotation(unreal.Rotator())
survival.set_hunger(50); survival.apply_damage(50)
fixtures = []; steps = []
report = {'success': False, 'network': len(worlds) == 2, 'clock_offset_for_expiry': True, 'checkpoints': [], 'errors': []}
path = os.path.join(unreal.Paths.project_saved_dir(), 'FoodNetworkResult.json' if old_network else 'FoodPlayResult.json')
def widget(name):
    return next((w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.load_class(None, '/Script/EW.' + name), False) if w.get_owning_player() == pc and w.is_in_viewport()), None)
def step(fn, delay=1.25): steps.append((fn, delay))
def key(name): assert lib.send_verification_ui_key(pc, name)
def spawn(count):
    node = lib.spawn_verification_hand_gatherable(server, unreal.Vector(150, 0, 160), berry, count)
    assert node
    node.set_editor_property('gathering_kind', unreal.EWHandGatheringKind.BERRIES); node.force_net_update(); fixtures.append(node)
def check(label, berries, residue, hunger, health, slots=None):
    rows = []
    for w in worlds:
        p = next(p for p in characters(w) if pid(p) == owner_id)
        i = p.get_inventory_component(); s = p.get_survival_component()
        row = [i.get_item_count(berry), i.get_item_count(toxic), s.get_hunger(), s.get_health(), s.get_carried_weight(), i.get_used_slot_count()]
        assert row[:2] == [berries, residue], label + str(row)
        assert abs(row[2] - hunger) < .01 and abs(row[3] - health) < .01, label + str(row)
        assert abs(row[4] - (berries + residue) * .01) < .001, label + str(row)
        if slots is not None: assert row[5] == slots, label + str(row)
        rows.append(row)
        for other in characters(w):
            if pid(other) != owner_id: assert not other.get_inventory_component().get_inventory_entries(), 'Other inventory mutated'
    report['checkpoints'].append({'label': label, 'world_values': rows})
def panel():
    ui = widget('EWInventoryWidget'); assert ui and ui.is_showing_details()
    assert ui.is_food_action_visible()
    assert 'Azren' in str(ui.get_displayed_details())
    assert ui.get_displayed_food_freshness() > 0, 'Inventory freshness bar missing'
    screenshot = os.path.join(unreal.Paths.project_saved_dir(), 'Screenshots', 'FoodInventoryNetwork.png' if old_network else 'FoodInventoryStandalone.png')
    unreal.SystemLibrary.execute_console_command(world, 'Shot showui filename="' + screenshot + '"')
    report['checkpoints'].append({'label': 'Azren details, Eat button and live freshness bar visible'})
def full(): survival.set_hunger(100); survival.restore_health(100)
def damaged(): survival.set_hunger(50); survival.apply_damage(50)
def clock(seconds): assert lib.advance_verification_food_clock(owner, seconds)
def offset_check():
    value = pc.get_controlled_pawn().get_inventory_component().get_food_freshness(berry)
    assert .4 < value < .51, 'Freshness clock/bar value differs: ' + str(value)
    report['checkpoints'].append({'label': 'Real clock offset updates replicated freshness', 'freshness': value})
def chord():
    assert lib.send_verification_ui_key_event(pc, 'Gamepad_LeftShoulder', True)
    key('Gamepad_FaceButton_Bottom')
    assert lib.send_verification_ui_key_event(pc, 'Gamepad_LeftShoulder', False)
step(lambda: check('Fresh empty inventory; no automatic grant', 0, 0, 50, 50, 0))
step(lambda: spawn(5)); step(lambda: key('E')); step(lambda: check('E gathers authored Azren', 5, 0, 50, 50, 1))
step(lambda: key('I')); step(lambda: key('Enter')); step(panel)
step(lambda: key('R')); step(lambda: check('Inventory R eats one berry', 4, 0, 56.25, 55))
step(lambda: key('Gamepad_FaceButton_Left')); step(lambda: check('Inventory X eats one berry', 3, 0, 62.5, 60))
step(full); step(lambda: key('R')); step(lambda: check('No-benefit inventory use preserves units', 3, 0, 100, 100))
step(lambda: key('One')); step(lambda: key('I')); step(damaged)
step(lambda: key('One')); step(lambda: check('Keyboard hotbar consumes one berry', 2, 0, 56.25, 55))
step(chord); step(lambda: check('Controller LB+A consumes one berry', 1, 0, 62.5, 60))
step(lambda: lib.send_verification_food_request(pc, toxic)); step(lambda: lib.send_verification_food_request(pc, wood))
step(lambda: check('Toxic/resource/unowned requests preserve stats and units', 1, 0, 62.5, 60))
step(lambda: survival.apply_damage(100)); step(lambda: lib.send_verification_food_request(pc, berry))
step(lambda: check('Dead survivor cannot eat', 1, 0, 62.5, 0))
step(lambda: survival.restore_health(100)); step(lambda: clock(600)); step(offset_check)
step(lambda: spawn(2)); step(lambda: key('E')); step(lambda: check('Later pickup has its own fresh batch', 3, 0, 62.5, 100, 2))
step(lambda: clock(601)); step(lambda: check('Only old batch converts; quantity/weight conserved', 2, 1, 62.5, 100, 2))
step(lambda: clock(600)); step(lambda: check('Later batch expires independently', 0, 3, 62.5, 100, 2))
step(lambda: key('One')); step(lambda: lib.send_verification_food_request(pc, toxic))
step(lambda: check('Expired shortcut and toxic resource cannot heal/feed', 0, 3, 62.5, 100))
index = 0; next_time = time.monotonic() + 1; handle = None
def finish():
    unreal.unregister_slate_post_tick_callback(handle)
    pc.set_inventory_open(False)
    for c in controllers: lib.flush_verification_input(c)
    for p in characters(server):
        i = p.get_inventory_component(); i.remove_item(berry, 100000); i.remove_item(toxic, 100000)
        p.get_hotbar_component().bind_item(0, None)
    for s, hunger, health in saved_stats:
        s.set_hunger(hunger); s.restore_health(100000)
        s.apply_damage(s.get_health() - health)
    for a in fixtures:
        if unreal.SystemLibrary.is_valid(a): a.destroy_actor()
    for w, old in old_network: lib.set_verification_network_settings(w, old.x, old.y)
    settings.set_editor_property('bThrottleCPUWhenNotForeground', throttle)
    report['success'] = not report['errors'] and index == len(steps)
    with open(path, 'w') as f: json.dump(report, f, indent=2)
def tick(delta):
    global index, next_time
    try:
        assert all(w in lib.get_play_worlds() for w in worlds), 'Play ended'
        if time.monotonic() < next_time: return
        if index == len(steps): finish(); return
        fn, delay = steps[index]; fn(); index += 1; next_time = time.monotonic() + delay
    except Exception:
        report['errors'].append(traceback.format_exc()); finish()
handle = unreal.register_slate_post_tick_callback(tick)
