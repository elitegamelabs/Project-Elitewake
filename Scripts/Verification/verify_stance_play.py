"""Run in a fresh single-player editor Play session; inject normal stance inputs.

Results are written under Saved/M2StancePlayResult.json. The callback releases
every injected action and restores editor throttling when it finishes.
"""
import unreal, json, math, os, traceback

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world, 'Start a fresh Play session first.'
assert len(unreal.EWEditorVerificationLibrary.get_play_worlds()) == 1, 'Use a single-player Play session.'
controller = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = controller.get_controlled_pawn()
subsystem = unreal.EWEditorVerificationLibrary.get_player_input_subsystem(controller)
assert pawn and subsystem
fixture = unreal.EWEditorVerificationLibrary.spawn_verification_box(world,
    unreal.Vector(0, 0, 4980), unreal.Vector(2000, 2000, 20), unreal.Rotator())
assert fixture and pawn.teleport(unreal.Vector(0, 0, 5090), unreal.Rotator()), 'Could not enter clear verification area.'
controller.set_control_rotation(unreal.Rotator())
stance = pawn.get_editor_property('stance_action')
move = pawn.get_editor_property('move_action')
perspective = pawn.get_editor_property('toggle_perspective_action')
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
previous_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
unreal.WidgetLibrary.set_focus_to_game_viewport()
report = {'success': False, 'checkpoints': [], 'errors': []}
result_path = os.path.join(unreal.Paths.project_saved_dir(), 'M2StancePlayResult.json')
active_actions = {}

def inject(action, x=1, y=0):
    active_actions[action] = unreal.Vector(x, y, 0)

def release(action):
    active_actions.pop(action, None)

def check(label, state, max_head=None, speed=None):
    movement = pawn.get_editor_property('character_movement')
    mesh = pawn.get_editor_property('mesh')
    anim = mesh.get_anim_instance()
    velocity = pawn.get_velocity()
    actual_speed = math.hypot(velocity.x, velocity.y)
    capsule = pawn.get_editor_property('capsule_component')
    floor_z = pawn.get_actor_location().z - capsule.get_scaled_capsule_half_height()
    head_height = mesh.get_socket_location('head').z - floor_z
    root = mesh.get_socket_location('root')
    origin = pawn.get_actor_location()
    root_drift = math.hypot(root.x - origin.x, root.y - origin.y)
    checkpoint = {'label': label, 'state': str(pawn.get_locomotion_state()), 'prone': pawn.is_prone,
                  'animation_prone': anim.get_editor_property('EWIsProne'),
                  'animation_crouching': anim.get_editor_property('EWIsCrouching'),
                  'head_height_cm': head_height, 'speed_cm_s': actual_speed,
                  'root_displacement_cm': root_drift,
                  'capsule_half_height_cm': capsule.get_scaled_capsule_half_height(),
                  'mesh_scale': str(mesh.get_editor_property('RelativeScale3D'))}
    report['checkpoints'].append(checkpoint)
    assert pawn.get_locomotion_state() == state, label + ': wrong locomotion state'
    assert anim.get_editor_property('EWIsProne') == pawn.is_prone, label + ': animation stance differs'
    assert mesh.get_editor_property('RelativeScale3D').is_near_equal(unreal.Vector(1, 1, 1), 0.001), label + ': mesh scaled'
    if max_head is not None:
        assert 0 < head_height < max_head, label + ': incorrect visual posture'
    if speed is not None:
        assert abs(actual_speed - speed) < 8, label + ': incorrect movement speed'
        assert root_drift < 1, label + ': animation root drifts outside the capsule'

def check_prone_camera():
    check('first-person prone', S.PRONE)
    camera = pawn.get_editor_property('FirstPersonCamera')
    capsule = pawn.get_editor_property('capsule_component')
    height = camera.get_world_location().z - pawn.get_actor_location().z + capsule.get_scaled_capsule_half_height()
    assert camera.is_active(), 'First-person camera inactive'
    assert abs(height - 40) < 1, 'Prone eye height is incorrect'
    report['prone_eye_height_cm'] = height

S = unreal.EWLocomotionState
steps = [
    (lambda: check('standing', S.STANDING), 0.2),
    (lambda: inject(stance), 0.10),
    (lambda: release(stance), 0.6),
    (lambda: check('tap crouch idle', S.CROUCHING, 145), 0.1),
    (lambda: inject(move, 0, 1), 0.8),
    (lambda: check('crouch walking', S.CROUCHING, 145, 300), 0.1),
    (lambda: release(move), 0.4),
    (lambda: inject(stance), 0.8),
    (lambda: release(stance), 0.5),
    (lambda: check('hold prone idle', S.PRONE, 75), 0.1),
    (lambda: inject(move, 0, 1), 0.8),
    (lambda: check('prone crawling', S.PRONE, 75, 150), 0.1),
    (lambda: release(move), 0.4),
    (lambda: inject(stance), 0.1),
    (lambda: release(stance), 0.5),
    (lambda: check('prone to crouch', S.CROUCHING, 145), 0.1),
    (lambda: inject(stance), 0.1),
    (lambda: release(stance), 0.5),
    (lambda: check('crouch to stand', S.STANDING), 0.1),
    (lambda: inject(perspective), 0.1),
    (lambda: release(perspective), 0.3),
    (lambda: inject(stance), 0.8),
    (lambda: release(stance), 0.5),
    (check_prone_camera, 0.1),
]
index = 0
next_time = unreal.GameplayStatics.get_time_seconds(world) + 0.2
handle = None

def finish():
    for action in [stance, move, perspective]:
        release(action)
    settings.set_editor_property('bThrottleCPUWhenNotForeground', previous_throttle)
    if unreal.SystemLibrary.is_valid(fixture): fixture.destroy_actor()
    report['success'] = not report['errors'] and index == len(steps)
    with open(result_path, 'w') as f:
        json.dump(report, f, indent=2)
    unreal.unregister_slate_post_tick_callback(handle)

def tick(delta):
    global index, next_time
    try:
        if world not in unreal.EWEditorVerificationLibrary.get_play_worlds():
            report['errors'].append('Play ended before verification finished.')
            finish()
            return
        for action, value in list(active_actions.items()):
            subsystem.inject_input_vector_for_action(action, value, [], [])
        now = unreal.GameplayStatics.get_time_seconds(world)
        if now < next_time:
            return
        if index == len(steps):
            finish()
            return
        action, wait = steps[index]
        action()
        index += 1
        next_time = now + wait
    except Exception:
        report['errors'].append(traceback.format_exc())
        finish()

handle = unreal.register_slate_post_tick_callback(tick)
