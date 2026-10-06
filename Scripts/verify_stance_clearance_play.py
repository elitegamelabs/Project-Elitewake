"""Temporary Play course: real stance inputs, blocked transitions, crawl and turn clearance.

Run in fresh single-player or listen-server/client Play. Network mode adds
100 ms outgoing lag and 1% packet loss on both drivers, then restores them.
The fixture is spawned only in PIE.
All actions, geometry and callbacks are cleaned up on success, failure or Play exit.
"""
import unreal, json, os, traceback, math

worlds = unreal.EWEditorVerificationLibrary.get_play_worlds()
assert len(worlds) in (1, 2), 'Use single-player or one listen server/client.'
network = len(worlds) == 2
controllers = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
controller = next((c for c in controllers if c and not c.has_authority()), controllers[0])
world = worlds[controllers.index(controller)]
pawn = controller.get_controlled_pawn()
peers = [pawn]
network_settings = []
if network:
    def player_id(actor):
        state = actor.get_editor_property('PlayerState')
        return json.loads(unreal.ToolsetLibrary.get_object_properties(state, ['PlayerId']))['PlayerId']
    owner_id = player_id(pawn)
    character_class = unreal.load_class(None, '/Script/EW.EWCharacter')
    peers = [next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, character_class)
                  if player_id(a) == owner_id) for w in worlds]
    for w in worlds:
        old = unreal.EWEditorVerificationLibrary.get_verification_network_settings(w)
        assert old.x >= 0, 'Network driver missing'
        network_settings.append((w, old))
        assert unreal.EWEditorVerificationLibrary.set_verification_network_settings(w, 100, 1)
subsystem = unreal.EWEditorVerificationLibrary.get_player_input_subsystem(controller)
stance = pawn.get_editor_property('stance_action')
move = pawn.get_editor_property('move_action')
sprint = pawn.get_editor_property('sprint_action')
jump = pawn.get_editor_property('jump_action')
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
previous_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
unreal.WidgetLibrary.set_focus_to_game_viewport()
active = {}
geometry = []
obstacle = None
report = {'success': False, 'network': network, 'outgoing_lag_ms': 100 if network else 0,
          'packet_loss_percent': 1 if network else 0, 'checkpoints': [], 'errors': []}
path = os.path.join(unreal.Paths.project_saved_dir(), 'M2ClearanceNetworkResult.json' if network else 'M2ClearancePlayResult.json')

def box(location, extent):
    actors = []
    for w in worlds:
        actor = unreal.EWEditorVerificationLibrary.spawn_verification_box(w, unreal.Vector(*location),
            unreal.Vector(*extent), unreal.Rotator())
        assert actor, 'Play fixture did not spawn'
        geometry.append(actor)
        actors.append(actor)
    return actors

box((0, 0, 4980), (2000, 2000, 20))
for peer in peers:
    assert peer.teleport(unreal.Vector(0, 0, 5090), unreal.Rotator()), 'Could not enter test course'
controller.set_control_rotation(unreal.Rotator())

def press(action, x=1, y=0): active[action] = unreal.Vector(x, y, 0)
def release(action): active.pop(action, None)

def obstacle_at(location, extent):
    global obstacle
    clear_obstacle()
    obstacle = box(location, extent)

def clear_obstacle():
    global obstacle
    if obstacle:
        for actor in obstacle:
            actor.destroy_actor()
            geometry.remove(actor)
        obstacle = None

def reset_position():
    for peer in peers:
        assert peer.teleport(unreal.Vector(0, 0, 5000 + peer.get_editor_property('capsule_component').get_scaled_capsule_half_height() + 2.15), unreal.Rotator())
    controller.set_control_rotation(unreal.Rotator())

def check(label, state, half_height, max_x=None, max_yaw=None, speed=None):
    capsule = pawn.get_editor_property('capsule_component')
    mesh = pawn.get_editor_property('mesh')
    anim = mesh.get_anim_instance()
    location = pawn.get_actor_location()
    velocity = pawn.get_velocity()
    actual_speed = math.hypot(velocity.x, velocity.y)
    row = {'label': label, 'state': str(pawn.get_locomotion_state()), 'prone': pawn.is_prone,
           'half_height_cm': capsule.get_scaled_capsule_half_height(), 'position': [location.x, location.y, location.z],
           'yaw': pawn.get_actor_rotation().yaw, 'speed_cm_s': actual_speed,
           'root_height_cm': mesh.get_socket_location('root').z - 5000}
    report['checkpoints'].append(row)
    assert pawn.get_locomotion_state() == state, label + ': wrong stance'
    assert abs(row['half_height_cm'] - half_height) < .1, label + ': wrong collision size'
    assert anim.get_editor_property('EWIsProne') == pawn.is_prone, label + ': animation differs'
    if state != unreal.EWLocomotionState.AIRBORNE:
        assert -1 < row['root_height_cm'] < 6, label + ': feet/body anchor moved away from floor'
    if max_x is not None: assert location.x < max_x, label + ': body passed through wall'
    if max_yaw is not None: assert abs(row['yaw']) < max_yaw, label + ': body turned through wall'
    if speed is not None: assert abs(actual_speed-speed) < 8, label + ': wrong speed'
    if network:
        rows = []
        row['peers'] = rows
        for peer in peers:
            peer_capsule = peer.get_editor_property('capsule_component')
            peer_anim = peer.get_editor_property('mesh').get_anim_instance()
            peer_location = peer.get_actor_location()
            peer_row = {'authority': peer.has_authority(), 'state': str(peer.get_locomotion_state()),
                        'half_height_cm': peer_capsule.get_scaled_capsule_half_height(),
                        'position': [peer_location.x, peer_location.y, peer_location.z]}
            rows.append(peer_row)
            assert peer.get_locomotion_state() == state, label + ': authoritative stance differs'
            assert abs(peer_row['half_height_cm']-half_height) < .1, label + ': authoritative collider differs'
            assert peer_anim.get_editor_property('EWIsProne') == peer.is_prone, label + ': remote animation differs'
            if max_x is not None: assert peer_location.x < max_x, label + ': authoritative body passed through wall'
            if max_yaw is not None: assert abs(peer.get_actor_rotation().yaw) < max_yaw, label + ': authoritative turn clips'

S = unreal.EWLocomotionState
steps = [
    (lambda: check('standing', S.STANDING, 90), .1),
    (lambda: press(stance), .1), (lambda: release(stance), .5),
    (lambda: check('crouch clearance', S.CROUCHING, 60), .1),
    (lambda: obstacle_at((0, 0, 5160), (250, 250, 10)), .1),
    (lambda: press(stance), .1), (lambda: release(stance), .5),
    (lambda: check('blocked crouch to stand', S.CROUCHING, 60), .1),
    (clear_obstacle, .1),
    (lambda: press(stance), .1), (lambda: release(stance), .5),
    (lambda: obstacle_at((90, 0, 5045), (10, 250, 45)), .1),
    (lambda: press(stance), .8), (lambda: release(stance), .5),
    (lambda: check('blocked prone entry', S.STANDING, 90), .1),
    (clear_obstacle, .1),
    (lambda: press(stance), .8), (lambda: release(stance), .5),
    (lambda: check('prone clearance', S.PRONE, 28), .1),
    (lambda: obstacle_at((0, 0, 5075), (250, 250, 10)), .1),
    (lambda: press(stance), .1), (lambda: release(stance), .5),
    (lambda: check('blocked prone to crouch', S.PRONE, 28), .1),
    (lambda: press(sprint), .5),
    (lambda: check('blocked prone sprint exit', S.PRONE, 28), .1),
    (lambda: release(sprint), .2),
    (lambda: press(jump), .1), (lambda: release(jump), .4),
    (lambda: check('blocked prone jump exit', S.PRONE, 28), .1),
    (lambda: press(move, 0, 1), .8),
    (lambda: check('crawl under low roof', S.PRONE, 28, speed=150), .1),
    (lambda: release(move), .4), (reset_position, .3),
    (clear_obstacle, .1),
    (lambda: obstacle_at((200, 0, 5050), (10, 250, 50)), .1),
    (lambda: press(move, 0, 1), 1.5),
    (lambda: check('crawl body stops at wall', S.PRONE, 28, max_x=86), .1),
    (lambda: release(move), .4), (clear_obstacle, .1), (reset_position, .3),
    (lambda: obstacle_at((0, 70, 5050), (250, 10, 50)), .1),
    (lambda: press(move, 1, 0), .7),
    (lambda: check('turn blocked by side wall', S.PRONE, 28, max_yaw=30), .1),
    (lambda: release(move), .4), (clear_obstacle, .1), (reset_position, .3),
    (lambda: press(move, 0, 1), .8),
    (lambda: check('open-space crawl', S.PRONE, 28, speed=150), .1),
    (lambda: release(move), .4),
    (lambda: press(stance), .1), (lambda: release(stance), .5),
    (lambda: check('open-space prone to crouch', S.CROUCHING, 60), .1),
    (lambda: press(sprint), .6),
    (lambda: check('open-space sprint exit', S.STANDING, 90), .1),
    (lambda: release(sprint), .2),
    (lambda: press(stance), .8), (lambda: release(stance), .5),
    (lambda: press(jump), .2),
    (lambda: check('open-space prone jump', S.AIRBORNE, 90), .1),
    (lambda: release(jump), 1.2),
    (lambda: check('landing after prone jump', S.STANDING, 90), .1),
]
index = 0
next_time = unreal.GameplayStatics.get_time_seconds(world) + .6
handle = None

def finish():
    active.clear()
    for actor in list(geometry):
        if unreal.SystemLibrary.is_valid(actor): actor.destroy_actor()
    settings.set_editor_property('bThrottleCPUWhenNotForeground', previous_throttle)
    for w, old in network_settings:
        if w in unreal.EWEditorVerificationLibrary.get_play_worlds():
            unreal.EWEditorVerificationLibrary.set_verification_network_settings(w, old.x, old.y)
    report['success'] = not report['errors'] and index == len(steps)
    with open(path, 'w') as output: json.dump(report, output, indent=2)
    unreal.unregister_slate_post_tick_callback(handle)

def tick(delta):
    global index, next_time
    try:
        if world not in unreal.EWEditorVerificationLibrary.get_play_worlds():
            report['errors'].append('Play ended before verification completed.')
            finish()
            return
        for action, value in list(active.items()): subsystem.inject_input_vector_for_action(action, value, [], [])
        now = unreal.GameplayStatics.get_time_seconds(world)
        if now < next_time: return
        if index == len(steps):
            finish()
            return
        action, delay = steps[index]
        action()
        index += 1
        next_time = now + delay
    except Exception:
        report['errors'].append(traceback.format_exc())
        finish()

handle = unreal.register_slate_post_tick_callback(tick)
