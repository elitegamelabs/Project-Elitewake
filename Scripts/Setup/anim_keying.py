"""Key new upper-body animations onto the mannequin skeleton, on top of its standing idle. Used by
build_tool_swing.py and build_crew_animations.py; not run on its own.

A part is turned about an axis of the mesh's own space (the mesh faces +Y, its left is +X, up is +Z), at its own
joint, by an angle that follows keys over the animation's time. The upper body is walked from the spine outward,
each bone placed from its parent's new place, so a turned spine carries the arms with it. The hips and legs can be
keyed too (a squat: the pelvis dropped with the pseudo-axis 'drop', in cm, and the thighs, calves and feet turned so
the feet stay planted). Only keyed bones get tracks; everything else keeps the idle.
"""
import math
import unreal

IDLE = '/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle'
RATE = 30
# The body, each bone after its parent.
PARENTS = {'pelvis': 'root', 'spine_01': 'pelvis', 'spine_02': 'spine_01',
           'thigh_l': 'pelvis', 'calf_l': 'thigh_l', 'foot_l': 'calf_l',
           'thigh_r': 'pelvis', 'calf_r': 'thigh_r', 'foot_r': 'calf_r',
           'spine_03': 'spine_02', 'spine_04': 'spine_03', 'spine_05': 'spine_04',
           'clavicle_r': 'spine_05', 'upperarm_r': 'clavicle_r', 'lowerarm_r': 'upperarm_r', 'hand_r': 'lowerarm_r',
           'clavicle_l': 'spine_05', 'upperarm_l': 'clavicle_l', 'lowerarm_l': 'upperarm_l', 'hand_l': 'lowerarm_l'}
ORDER = list(PARENTS)
AXES = {'x': (1.0, 0.0, 0.0), 'y': (0.0, 1.0, 0.0), 'z': (0.0, 0.0, 1.0)}


def curve(keys, t):
    """Smooth (cosine) interpolation between (time 0-1, degrees) keys."""
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            u = .5 - .5 * math.cos(math.pi * u)
            return v0 + (v1 - v0) * u
    return keys[-1][1]


def rotation_only(quat, location=None, scale=None):
    t = unreal.Transform()
    t.set_editor_property('rotation', quat)
    if location is not None:
        t.set_editor_property('translation', location)
    if scale is not None:
        t.set_editor_property('scale3d', scale)
    return t


def turn(axis, degrees):
    x, y, z = AXES[axis]
    half = math.radians(degrees) * .5
    s = math.sin(half)
    return rotation_only(unreal.Quat(x * s, y * s, z * s, math.cos(half)))


def build(path, frames, parts, label):
    """Write `path` (made from the idle, or rewritten), `frames` long at RATE, from the idle with `parts` turned:
    {bone: [(axis, keys), ...]}. Returns the animation."""
    folder, name = path.rsplit('/', 1)
    idle = unreal.load_asset(IDLE)
    # Rewritten in place if it exists (the survivor's blueprint holds it, so it cannot be deleted while loaded).
    anim = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name, folder, idle)
    assert anim, path
    poses, math_ = unreal.AnimPoseExtensions, unreal.MathLibrary
    world, local = unreal.AnimPoseSpaces.WORLD, unreal.AnimPoseSpaces.LOCAL
    tracks = {bone: ([], [], []) for bone in parts}
    for frame in range(frames + 1):
        t = frame / frames
        pose = poses.get_anim_pose_at_time(idle, frame / RATE, unreal.AnimPoseEvaluationOptions())
        placed = {'root': poses.get_bone_pose(pose, 'root', world)}
        for bone in ORDER:
            parent = placed[PARENTS[bone]]
            here = math_.compose_transforms(poses.get_bone_pose(pose, bone, local), parent)
            if bone in parts:
                spun = rotation_only(here.rotation)
                at = here.translation
                for axis, keys in parts[bone]:
                    if axis == 'drop':
                        at = unreal.Vector(at.x, at.y, at.z - curve(keys, t))
                    else:
                        spun = math_.compose_transforms(spun, turn(axis, curve(keys, t)))
                here = rotation_only(spun.rotation, at, here.scale3d)
                key = math_.compose_transforms(here, math_.invert_transform(parent))
                tracks[bone][0].append(key.translation)
                tracks[bone][1].append(key.rotation)
                tracks[bone][2].append(key.scale3d)
            placed[bone] = here
    controller = anim.get_editor_property('controller')
    controller.open_bracket(unreal.Text(label), True)
    controller.set_number_of_frames(unreal.FrameNumber(frames), True)
    for bone, (positions, rotations, scales) in tracks.items():
        controller.set_bone_track_keys(bone, positions, rotations, scales, True)
    controller.close_bracket(True)
    anim.set_editor_property('enable_root_motion', False)
    assert unreal.EditorAssetLibrary.save_loaded_asset(anim)
    return anim
