"""Bare-hand punches for each arm (owner, November 3). Safe to run again. Run in the editor, with source control off:
    UnrealEditor-Cmd.exe EW.uproject -nullrhi -unattended -SCCProvider=None -run=pythonscript -script=<this file>

  - Third person: the right arm's punch is the mannequin's MM_Attack_01 (a right hook), the left arm's MM_Attack_02 (a left
    hook); Scripts/Art/inspect_punch_arms.py measured which hand each throws. MM_Attack_03, a 1.7 s combination that the
    one-second swing pace cut short, is no longer a bare-hand punch.
  - First person: a straight jab per arm, AS_PunchFP_Right_v1 and AS_PunchFP_Left_v1, the fist driven out in front of the
    eyes, where the survivor's own camera sees it (the hooks pass outside the view). Each is built from its arm's hook: the
    body holds a fighting stance, the punching hand and fingers take the hook's closed fist, and the shoulder and
    elbow are solved (two-bone IK, elbow down and a little out) so the fist follows a guard - full reach - guard path in
    front of the head. Both stand in the right hook's opening guard (the left hand forward). 0.8 s, inside the one-second pace.
  - The character blueprint's punch lists are set to match (AEWCharacter::AttackAnimations, LeftPunchAnimations,
    FirstPersonRightPunchAnimations, FirstPersonLeftPunchAnimations).
Writes Saved/PunchesResult.json. Every distance and time is tuning; owner visual review pending.
"""
import json
import math
from pathlib import Path
import unreal

HOOKS = {'right': '/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01',
         'left': '/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_02'}
FOLDER = '/Game/Elitewake/Animations/Combat'
CHARACTER = '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
FPS, LENGTH = 30, 0.8
# The fist's path in front of the head (cm; the mannequin faces +Y, its right side is -X): (time s, forward, up, outward).
PATH = [(0.12, 26.0, -8.0, 12.0), (0.26, 64.0, 4.0, 5.0), (0.34, 64.0, 4.0, 5.0), (0.56, 26.0, -8.0, 12.0)]
REACH = .97              # of the arm's full length, so the elbow never locks straight
Pose = unreal.AnimPoseExtensions
WORLD, LOCAL = unreal.AnimPoseSpaces.WORLD, unreal.AnimPoseSpaces.LOCAL


# ---- Small vector and quaternion maths (w, x, y, z) ------------------------------------------------------------
def v(t): return (t.x, t.y, t.z)
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def norm(a): n = length(a); return mul(a, 1.0 / n) if n > 1e-9 else a
def q(u): return (u.w, u.x, u.y, u.z)
def uq(a): return unreal.Quat(a[1], a[2], a[3], a[0])
def qmul(a, b):
    aw, ax, ay, az = a; bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw)
def qinv(a): return (a[0], -a[1], -a[2], -a[3])
def qrot(a, p): return qmul(qmul(a, (0.0,) + tuple(p)), qinv(a))[1:]
def between(a, b):
    """The shortest rotation taking direction a to direction b."""
    a, b = norm(a), norm(b)
    c = cross(a, b); w = 1.0 + dot(a, b)
    if w < 1e-6:
        axis = norm(cross(a, (1.0, 0.0, 0.0)) if abs(a[0]) < .9 else cross(a, (0.0, 1.0, 0.0)))
        return (0.0,) + axis
    n = math.sqrt(w * w + dot(c, c))
    return (w / n, c[0] / n, c[1] / n, c[2] / n)
def slerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0: b, d = tuple(-x for x in b), -d
    if d > .9995:
        r = tuple(x + (y - x) * t for x, y in zip(a, b)); n = math.sqrt(sum(x * x for x in r)); return tuple(x / n for x in r)
    th = math.acos(d); s = math.sin(th)
    return tuple((math.sin((1 - t) * th) * x + math.sin(t * th) * y) / s for x, y in zip(a, b))
def ease(t): return t * t * (3 - 2 * t)


def pose_at(anim, t):
    return Pose.get_anim_pose_at_time(anim, t, unreal.AnimPoseEvaluationOptions())


def children_of(bones, parent_of, root):
    out, todo = [], [root]
    while todo:
        b = todo.pop()
        out.append(b)
        todo += [c for c in bones if parent_of.get(c) == b]
    return out


def jab(side, hook):
    s = 'r' if side == 'right' else 'l'
    out_sign = -1.0 if side == 'right' else 1.0          # the right side is -X
    length_s = unreal.AnimationLibrary.get_sequence_length(hook)
    # Both jabs stand in the right hook's opening guard, the left hand forward: the left hook opens with that shoulder
    # turned back, too far for the arm to carry the fist out in front of the eyes.
    stance = pose_at(unreal.load_asset(HOOKS['right']), 0.0)
    bones = [str(b) for b in Pose.get_bone_names(stance)]
    # The fist: the frame where this hand reaches farthest forward of the chest.
    best, fist_t = -1e9, 0.0
    for k in range(61):
        t = length_s * k / 60
        p = pose_at(hook, t)
        reach = Pose.get_bone_pose(p, f'hand_{s}', WORLD).translation.y - Pose.get_bone_pose(p, 'spine_05', WORLD).translation.y
        if reach > best:
            best, fist_t = reach, t
    fist = pose_at(hook, fist_t)
    parent_of = {}
    for b in bones:
        chain = [str(x) for x in unreal.AnimationLibrary.find_bone_path_to_root(hook, b)]
        parent_of[b] = chain[1] if len(chain) > 1 else None
    hand_tree = children_of(bones, parent_of, f'hand_{s}')
    U, L, H, C = f'upperarm_{s}', f'lowerarm_{s}', f'hand_{s}', f'clavicle_{s}'
    cs = {b: Pose.get_bone_pose(stance, b, WORLD) for b in (U, L, H, C, 'head')}
    shoulder, elbow0, wrist0 = v(cs[U].translation), v(cs[L].translation), v(cs[H].translation)
    upper_len, lower_len = length(sub(elbow0, shoulder)), length(sub(wrist0, elbow0))
    head = v(cs['head'].translation)
    rU0, rL0, rC = q(cs[U].rotation), q(cs[L].rotation), q(cs[C].rotation)
    keys_path = [(0.0, wrist0)] + [(t, (head[0] + out_sign * o, head[1] + f, head[2] + u)) for t, f, u, o in PATH] + [(LENGTH, wrist0)]

    def target(t):
        for (t0, p0), (t1, p1) in zip(keys_path, keys_path[1:]):
            if t <= t1:
                k = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
                return add(p0, mul(sub(p1, p0), k))
        return keys_path[-1][1]

    def fistness(t):
        a, b = PATH[0][0], PATH[-1][0]
        return ease(min(1.0, t / a)) if t < a else (1.0 if t <= b else ease(max(0.0, 1 - (t - b) / (LENGTH - b))))

    frames = int(round(LENGTH * FPS))
    tracks = {b: ([], [], []) for b in bones}
    reached = []
    for f in range(frames + 1):
        t = f / FPS
        goal = target(t)
        to_goal = sub(goal, shoulder)
        d = min(length(to_goal), REACH * (upper_len + lower_len))
        aim = norm(to_goal)
        goal = add(shoulder, mul(aim, d))
        # The elbow: on the circle the two bones allow, toward a pole below the arm and a little outward.
        pole = norm((out_sign * .6, -.2, -1.0))
        side_dir = norm(sub(pole, mul(aim, dot(pole, aim))))
        cos_a = max(-1.0, min(1.0, (upper_len ** 2 + d ** 2 - lower_len ** 2) / (2 * upper_len * d)))
        elbow = add(shoulder, add(mul(aim, upper_len * cos_a), mul(side_dir, upper_len * math.sqrt(max(0.0, 1 - cos_a ** 2)))))
        turn_u = between(sub(elbow0, shoulder), sub(elbow, shoulder))
        rU = qmul(turn_u, rU0)
        rL_carried = qmul(turn_u, rL0)
        turn_l = between(qrot(turn_u, sub(wrist0, elbow0)), sub(goal, elbow))
        rL = qmul(turn_l, rL_carried)
        reached.append(round(length(sub(goal, head)), 1))
        k = fistness(t)
        for b in bones:
            lp = Pose.get_bone_pose(stance, b, LOCAL)
            pos, rot, scl = lp.translation, q(lp.rotation), lp.scale3d
            if b == U:
                rot = qmul(qinv(rC), rU)                       # local to the clavicle, which holds still
            elif b == L:
                rot = qmul(qinv(rU), rL)
            elif b in hand_tree:
                rot = slerp(rot, q(Pose.get_bone_pose(fist, b, LOCAL).rotation), k)
            tracks[b][0].append(pos)
            tracks[b][1].append(uq(rot))
            tracks[b][2].append(scl)
    name = f'AS_PunchFP_{side.title()}_v1'
    path = f'{FOLDER}/{name}'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    anim = unreal.EditorAssetLibrary.duplicate_asset(HOOKS[side], path)
    assert anim, path
    c = anim.controller
    c.open_bracket(unreal.Text('First-person jab'))
    c.set_frame_rate(unreal.FrameRate(FPS, 1))
    c.set_number_of_frames(unreal.FrameNumber(frames))
    for b, (ps, rs, ss) in tracks.items():
        c.set_bone_track_keys(b, ps, rs, ss)
    c.close_bracket()
    unreal.AnimationLibrary.remove_all_animation_notify_tracks(anim)
    assert unreal.EditorAssetLibrary.save_loaded_asset(anim), path
    return anim, {'fist_from_s': round(fist_t, 3), 'arm_cm': [round(upper_len, 1), round(lower_len, 1)],
                  'fist_to_head_cm_min_max': [min(reached), max(reached)], 'frames': frames}


def main():
    report = {}
    hooks = {side: unreal.load_asset(p) for side, p in HOOKS.items()}
    assert all(hooks.values())
    jabs = {}
    for side in ('right', 'left'):
        jabs[side], report[side] = jab(side, hooks[side])
    bp = unreal.load_asset(CHARACTER)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('attack_animations', [hooks['right']])
    cdo.set_editor_property('left_punch_animations', [hooks['left']])
    cdo.set_editor_property('first_person_right_punch_animations', [jabs['right']])
    cdo.set_editor_property('first_person_left_punch_animations', [jabs['left']])
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp)
    report['character'] = {k: [x.get_name() for x in cdo.get_editor_property(k)] for k in
                           ('attack_animations', 'left_punch_animations', 'first_person_right_punch_animations', 'first_person_left_punch_animations')}
    Path(unreal.Paths.project_saved_dir(), 'PunchesResult.json').write_text(json.dumps({'success': True, **report}, indent=2))


main()
