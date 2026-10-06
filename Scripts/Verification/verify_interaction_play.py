"""Fresh Lvl_M5PickupTest PIE, standalone or in-process listen/client.

PIE-only fixtures; normal Slate input and owned-controller RPCs, never Python RPC bypass.
Checks prompts, authority, holds/cancellation and single-use competition. Restores settings.
"""
import unreal, json, os, traceback, datetime

def valid(obj):
    # Destroyed PIE objects may have already lost their Python wrapper's native instance.
    try: return obj is not None and unreal.SystemLibrary.is_valid(obj)
    except (TypeError, RuntimeError): return False

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
station_cls = unreal.load_class(None, '/Script/EW.EWStation')
pickup_cls = unreal.load_class(None, '/Script/EW.EWPickup')
widget_cls = unreal.load_class(None, '/Script/EW.EWInteractionWidget')
def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']
player_id = pid(pawn)
server_pawn = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server, character_cls) if pid(p) == player_id)
server_pc = server_pawn.get_controller()
widget = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(local_world, widget_cls, False) if w.get_owning_player() == pc)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
old_network = [(w, lib.get_verification_network_settings(w)) for w in worlds] if network else []
for w, _ in old_network: lib.set_verification_network_settings(w, 100, 1)
for c in controllers: lib.flush_verification_input(c)
pc.set_inventory_open(False)
for p in unreal.GameplayStatics.get_all_actors_of_class(server, pickup_cls): p.destroy_actor()
for w in worlds:
    for p in unreal.GameplayStatics.get_all_actors_of_class(w, character_cls):
        p.teleport(unreal.Vector(0, 0, 96) if pid(p) == player_id else unreal.Vector(-500, 500, 96), unreal.Rotator())
for c in controllers: c.set_control_rotation(unreal.Rotator())
initial_inventory = server_pawn.get_inventory_component().get_used_slot_count()
target = None
wall = None
mismatch = None
fixtures = []
pressed = set()
saved_state = None
steps = []
report = {'success': False, 'network': network, 'lag_ms': 100 if network else 0, 'loss_percent': 1 if network else 0,
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checkpoints': [], 'errors': []}
path = os.path.join(unreal.Paths.project_saved_dir(), 'InteractionNetworkResult.json' if network else 'InteractionPlayResult.json')

def step(action, delay=1): steps.append((action, delay))
def key(name, down=True, controller=None):
    c = controller or pc
    assert lib.send_verification_ui_key_event(c, name, down)
    token = (controllers.index(c), name)
    if down: pressed.add(token)
    else: pressed.discard(token)
def tap(name, controller=None): key(name, True, controller); key(name, False, controller)
def spawn(hold=False, resource=False, single=False, x=150):
    global target
    if valid(target): target.destroy_actor()
    target = lib.spawn_verification_interactable(server, unreal.Vector(x, 0, 160), resource, hold, single, 1.2)
    assert target
    fixtures.append(target)
def peer(w):
    return next((s for s in unreal.GameplayStatics.get_all_actors_of_class(w, station_cls) if s.get_name() == target.get_name()), None)
def check(label, expected=0, prompt=None):
    values = [peer(w).get_acknowledgement_count() if peer(w) else None for w in worlds]
    text = str(widget.get_displayed_prompt())
    report['checkpoints'].append({'label': label, 'counts': values, 'prompt': text, 'progress': widget.get_displayed_progress()})
    assert all(v == expected for v in values), label + ': authoritative/replicated counts differ ' + str(values)
    if prompt is not None: assert prompt in text, label + ': unexpected prompt ' + text
def no_prompt(label):
    check(label)
    assert not str(widget.get_displayed_prompt()), label + ': prompt should be hidden'
def request(local_target=None):
    assert lib.send_verification_interaction_request(pc, local_target or peer(local_world))
def spawn_mismatch():
    global mismatch
    mismatch = lib.spawn_verification_interactable(server, unreal.Vector(150,200,160))
    fixtures.append(mismatch)
def request_mismatch():
    other = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(local_world, station_cls) if s.get_name() == mismatch.get_name())
    assert lib.send_verification_interaction_request(pc, other)
def check_mismatch():
    check('Mismatched target rejected')
    assert mismatch.get_acknowledgement_count() == 0
    mismatch.destroy_actor()
def held():
    global saved_state
    saved_state = server_pc.get_interaction_component().get_hold_state()
    assert saved_state.target == target, 'Server did not start hold'
    check('hold in progress', 0, 'Hold E:')
    assert 0 < widget.get_displayed_progress() < 1, 'No server-timed local progress'
def repeated():
    state = server_pc.get_interaction_component().get_hold_state()
    assert state.start_time == saved_state.start_time and state.revision == saved_state.revision, 'Repeated request restarted hold'
    check('repeated begin cannot accelerate/reset hold')
def blocker():
    global wall
    wall = lib.spawn_verification_box(server, unreal.Vector(75, 0, 160), unreal.Vector(10, 100, 100), unreal.Rotator())
    fixtures.append(wall)
def remove_wall():
    global wall
    if valid(wall): wall.destroy_actor()
    wall = None
def turn(yaw): pc.set_control_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0)); server_pc.set_control_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0))
def move_away():
    server_pawn.teleport(unreal.Vector(-500, 0, 96), unreal.Rotator())
    pawn.teleport(unreal.Vector(-500, 0, 96), unreal.Rotator())
def reset_position():
    server_pawn.teleport(unreal.Vector(0, 0, 96), unreal.Rotator())
    if valid(pawn): pawn.teleport(unreal.Vector(0, 0, 96), unreal.Rotator())
    turn(0)
def cancelled(label):
    check(label)
    assert not server_pc.get_interaction_component().get_hold_state().target, label + ': server hold still active'
def destroyed():
    assert not server_pc.get_interaction_component().get_hold_state().target
    assert not str(widget.get_displayed_prompt())
    report['checkpoints'].append({'label':'Destroyed target clears hold and prompt'})
def competing():
    for w in worlds:
        for p in unreal.GameplayStatics.get_all_actors_of_class(w, character_cls):
            p.teleport(unreal.Vector(0, -30 if pid(p) == player_id else 30, 96), unreal.Rotator())
    for c in controllers: c.set_control_rotation(unreal.Rotator())
    target.set_actor_scale3d(unreal.Vector(1, 5, 2))
def start_competition():
    key('E')
    for c, w in zip(controllers, worlds):
        if c != pc: assert lib.send_verification_interaction_request(c, peer(w))
def stop_competition():
    key('E', False)
    for c in controllers:
        if c != pc: assert lib.send_verification_interaction_request(c, None, True)
def finish_competition():
    check('single-use competition completes exactly once', 1)
    assert all(not c.get_interaction_component().get_hold_state().target for c in controllers), 'Competing hold left active'
    assert server_pawn.get_inventory_component().get_used_slot_count() == initial_inventory, 'Fixture granted inventory'

step(lambda: spawn(resource=True)); step(lambda: check('Tree inspect prompt', prompt='Inspect Tree'))
step(lambda: tap('E')); step(lambda: check('E acknowledges Tree without yield', 1))
step(lambda: spawn(resource=True))
step(lambda: target.set_editor_property('resource_type', unreal.EWResourceNodeType.ROCK)); step(lambda: check('Rock inspect prompt', prompt='Inspect Rock'))
step(lambda: spawn()); step(lambda: tap('Gamepad_FaceButton_Left')); step(lambda: check('Controller X input and prompt', 1, 'X:'))
step(lambda: target.set_editor_property('station_type', unreal.EWStationType.SMITHY)); step(lambda: check('Smithy inspect prompt', 1, 'Inspect Smithy'))
step(lambda: tap('Gamepad_FaceButton_Top')); step(lambda: tap('I')); step(lambda: check('Keyboard close after controller menu restores E prompt',1,'E:'))
step(lambda: tap('I')); step(lambda: tap('Gamepad_FaceButton_Top')); step(lambda: check('Controller close after keyboard menu restores X prompt',1,'X:'))
step(lambda: tap('F')); step(lambda: lib.send_verification_ui_analog(pc,0)); step(lambda: check('Idle controller sample retains keyboard prompt',1,'E:'))
step(lambda: spawn(x=450)); step(lambda: no_prompt('Out-of-range prompt hidden')); step(request); step(lambda: check('Forged out-of-range request rejected'))
step(spawn); step(blocker); step(request); step(lambda: check('Through-wall request rejected')); step(remove_wall)
step(spawn); step(spawn_mismatch); step(request_mismatch); step(check_mismatch)
step(lambda: lib.set_verification_interaction_available(target, False)); step(request); step(lambda: no_prompt('CanInteract false rejects action and prompt'))
step(spawn); step(lambda: tap('I')); step(lambda: no_prompt('Inventory hides prompt')); step(request); step(lambda: check('Forged request while inventory open rejected')); step(lambda: tap('I'))
step(lambda: spawn(hold=True)); step(lambda: key('E'), .55); step(held, .05); step(request, .2); step(repeated, 1); step(lambda: key('E', False)); step(lambda: check('Server-timed hold completes once', 1))
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: key('E', False), 1.6); step(lambda: cancelled('Release cancels hold'))
step(lambda: spawn(hold=True)); step(lambda: key('Gamepad_FaceButton_Left'), 1.6); step(lambda: key('Gamepad_FaceButton_Left',False)); step(lambda: check('Controller X held interaction completes',1,'Hold X:'))
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: key('W'), .1); step(lambda: key('W',False), 1.4); step(lambda: key('E',False)); step(lambda: check('Walking while aimed/in range permits hold',1)); step(reset_position)
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: turn(90), 1.6); step(lambda: cancelled('Looking away cancels hold')); step(lambda: key('E', False)); step(lambda: turn(0))
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(blocker, 1.6); step(lambda: cancelled('New obstruction cancels hold')); step(lambda: key('E', False)); step(remove_wall)
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(move_away, 1.6); step(lambda: cancelled('Leaving range cancels hold')); step(lambda: key('E', False)); step(reset_position)
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: tap('I'), 1.6); step(lambda: cancelled('Opening inventory cancels hold')); step(lambda: key('E', False)); step(lambda: tap('I'))
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: lib.flush_verification_input(pc), 1.6); step(lambda: cancelled('Input flush cancels hold')); step(lambda: key('E', False))
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: server_pawn.get_survival_component().apply_damage(100), 1.6); step(lambda: cancelled('Death cancels hold')); step(lambda: key('E', False)); step(lambda: server_pawn.get_survival_component().restore_health(100))
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: server_pc.un_possess(), 1.6); step(lambda: cancelled('Pawn change cancels hold')); step(lambda: key('E', False)); step(lambda: server_pc.possess(server_pawn), 1.6); step(reset_position)
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: lib.set_verification_interaction_available(target, False), 1.6); step(lambda: cancelled('Unavailable target cancels hold')); step(lambda: key('E', False))
step(lambda: spawn(hold=True)); step(lambda: key('E'), .35); step(lambda: target.destroy_actor(), 1.6); step(destroyed); step(lambda: key('E',False))
step(lambda: spawn(hold=True, single=True)); step(competing); step(start_competition, 2); step(stop_competition); step(finish_competition)

index = 0
next_time = unreal.GameplayStatics.get_time_seconds(server) + 1
handle = None
def finish():
    unreal.unregister_slate_post_tick_callback(handle)
    for i, name in list(pressed): key(name, False, controllers[i])
    if not server_pc.get_controlled_pawn(): server_pc.possess(server_pawn)
    server_pawn.get_survival_component().restore_health(100)
    for c in controllers:
        lib.flush_verification_input(c)
        # Use Slate to close any panel so its ordinary RPC path stays intact.
        if c.get_interaction_component().is_menu_blocked(): tap('I', c)
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
