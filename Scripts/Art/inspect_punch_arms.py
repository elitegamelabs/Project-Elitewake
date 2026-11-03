"""Which arm each bare-hand punch throws: how far forward of the chest each hand reaches over the animation, sampled from
the animation itself (owner, November 3: left- and right-arm punches). Run in the editor:
    UnrealEditor-Cmd.exe EW.uproject -nullrhi -unattended -SCCProvider=None -run=pythonscript -script=<this file>
Writes Saved/PunchArms.json.
"""
import json
from pathlib import Path
import unreal

ANIMS = ['/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01',
         '/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_02',
         '/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_03']
Pose = unreal.AnimPoseExtensions
SPACE = unreal.AnimPoseSpaces.WORLD
out = {}
for path in ANIMS:
    anim = unreal.load_asset(path)
    assert anim, path
    length = unreal.AnimationLibrary.get_sequence_length(anim)
    options = unreal.AnimPoseEvaluationOptions()
    rows = []
    for k in range(31):
        t = length * k / 30
        pose = Pose.get_anim_pose_at_time(anim, t, options)
        chest = Pose.get_bone_pose(pose, 'spine_05', SPACE).translation
        row = {'t': round(t, 3)}
        for side in ('l', 'r'):
            hand = Pose.get_bone_pose(pose, f'hand_{side}', SPACE).translation
            # The mannequin faces +Y in its own space: forward reach is Y, height Z, side X.
            row[side] = [round(hand.x - chest.x), round(hand.y - chest.y), round(hand.z - chest.z)]
        rows.append(row)
    reach = {side: max(r[side][1] for r in rows) for side in ('l', 'r')}
    out[path.rsplit('/', 1)[1]] = {'length_s': round(length, 3), 'max_forward_cm': reach,
                                   'arm': 'left' if reach['l'] > reach['r'] else 'right', 'samples': rows}
    unreal.log(f'EWPUNCH {path}: {out[path.rsplit("/", 1)[1]]["arm"]} {reach}')
Path(unreal.Paths.project_saved_dir(), 'PunchArms.json').write_text(json.dumps(out, indent=2))
