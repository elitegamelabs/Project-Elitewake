"""Make the survivor's one-handed tool swing: an overhead chop. Safe to run again.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

There is no chop among the project's animations (the spear sets are long acrobatic combos), so this builds one on
the mannequin skeleton from the standing idle: the right arm draws up and back over the head with the elbow bent
and the body leaning back, then whips down and forward to arm's length as the body leans into it, and recovers.
Only the spine, right arm and right hand are keyed; the legs keep the idle. The result is
/Game/Elitewake/Animations/Tools/AS_ToolChop_v1, 0.9 s, without root motion. Angles and timing are tuning.
"""
import json
import math
from pathlib import Path
import unreal

IDLE = '/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle'
FOLDER = '/Game/Elitewake/Animations/Tools'
NAME = 'AS_ToolChop_v1'
RATE = 30
FRAMES = 27                     # 0.9 s
# Keys (time 0-1, degrees) for each part; the mesh faces +Y, so turning about +X swings forward and up.
UPPER_ARM = [(0, 0), (.42, 160), (.56, 58), (.7, 52), (1, 0)]       # the shoulder: up overhead, then down to the front
FOREARM = [(0, 0), (.42, 80), (.52, 18), (.58, 4), (1, 0)]          # the elbow bends back behind the head, then straightens
WRIST = [(0, 0), (.42, 20), (.56, -85), (.72, -65), (1, 0)]        # the wrist cocks back, then turns the head over into the blow
LEAN = [(0, 0), (.42, 7), (.58, -14), (.75, -10), (1, 0)]           # the upper body leans back, then into the blow
BONES = (('spine_03', LEAN), ('upperarm_r', UPPER_ARM), ('lowerarm_r', FOREARM), ('hand_r', WRIST))
# From the spine to the right hand, each bone the parent of the next.
CHAIN_ROOT_PARENT = 'spine_02'
CHAIN = ('spine_03', 'spine_04', 'spine_05', 'clavicle_r', 'upperarm_r', 'lowerarm_r', 'hand_r')


def curve(keys, t):
    """Smooth (cosine) interpolation between keys."""
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


def about_x(degrees):
    half = math.radians(degrees) * .5
    return rotation_only(unreal.Quat(math.sin(half), 0.0, 0.0, math.cos(half)))


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    path = f'{FOLDER}/{NAME}'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    anim = tools.duplicate_asset(NAME, FOLDER, unreal.load_asset(IDLE))
    assert anim, path
    idle = unreal.load_asset(IDLE)
    poses = unreal.AnimPoseExtensions
    world, local = unreal.AnimPoseSpaces.WORLD, unreal.AnimPoseSpaces.LOCAL
    tracks = {bone: ([], [], []) for bone, _ in BONES}
    keyed = dict(BONES)
    math_ = unreal.MathLibrary
    for frame in range(FRAMES + 1):
        t = frame / FRAMES
        pose = poses.get_anim_pose_at_time(idle, frame / RATE, unreal.AnimPoseEvaluationOptions())
        # Walk the chain from the spine to the hand, rebuilding each bone's place in the mesh from its parent's,
        # and turn the keyed ones about their own joint on top of the idle.
        parent = poses.get_bone_pose(pose, CHAIN_ROOT_PARENT, world)
        for bone in CHAIN:
            here = math_.compose_transforms(poses.get_bone_pose(pose, bone, local), parent)
            if bone in keyed:
                spun = math_.compose_transforms(rotation_only(here.rotation), about_x(curve(keyed[bone], t)))
                here = rotation_only(spun.rotation, here.translation, here.scale3d)
                key = math_.compose_transforms(here, math_.invert_transform(parent))
                tracks[bone][0].append(key.translation)
                tracks[bone][1].append(key.rotation)
                tracks[bone][2].append(key.scale3d)
            parent = here
    controller = anim.get_editor_property('controller')
    controller.open_bracket(unreal.Text('Build tool chop'), True)
    controller.set_number_of_frames(unreal.FrameNumber(FRAMES), True)
    for bone, (positions, rotations, scales) in tracks.items():
        controller.set_bone_track_keys(bone, positions, rotations, scales, True)
    controller.close_bracket(True)
    anim.set_editor_property('enable_root_motion', False)
    assert unreal.EditorAssetLibrary.save_loaded_asset(anim)
    Path(unreal.Paths.project_saved_dir(), 'ToolSwingResult.json').write_text(json.dumps(
        {'success': True, 'length': anim.get_play_length(), 'frames': FRAMES + 1}, indent=2))
    unreal.log('Tool chop built')


if __name__ == '__main__':
    main()
