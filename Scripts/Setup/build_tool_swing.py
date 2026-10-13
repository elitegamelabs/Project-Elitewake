"""Make the survivor's one-handed tool swing: an overhead chop. Safe to run again.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

There is no chop among the project's animations (the spear sets are long acrobatic combos), so this builds one on
the mannequin skeleton from the standing idle (anim_keying.py): the right arm draws up and back over the head with
the elbow bent and the body leaning back, then whips down and forward to arm's length as the body leans into it,
and recovers. Only the spine, right arm and right hand are keyed; the legs keep the idle. The result is
/Game/Elitewake/Animations/Tools/AS_ToolChop_v1, 0.9 s, without root motion. Angles and timing are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anim_keying  # noqa: E402

PATH = '/Game/Elitewake/Animations/Tools/AS_ToolChop_v1'
FRAMES = 27                     # 0.9 s
# Keys (time 0-1, degrees) about the mesh's X: forward and up for an arm, backward for the spine.
UPPER_ARM = [(0, 0), (.42, 160), (.56, 58), (.7, 52), (1, 0)]       # the shoulder: up overhead, then down to the front
FOREARM = [(0, 0), (.42, 80), (.52, 18), (.58, 4), (1, 0)]          # the elbow bends back behind the head, then straightens
WRIST = [(0, 0), (.42, 20), (.56, -85), (.72, -65), (1, 0)]        # the wrist cocks back, then turns the head over into the blow
LEAN = [(0, 0), (.42, 7), (.58, -14), (.75, -10), (1, 0)]           # the upper body leans back, then into the blow


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    anim = anim_keying.build(PATH, FRAMES, {'spine_03': [('x', LEAN)], 'upperarm_r': [('x', UPPER_ARM)],
                                            'lowerarm_r': [('x', FOREARM)], 'hand_r': [('x', WRIST)]}, 'Build tool chop')
    Path(unreal.Paths.project_saved_dir(), 'ToolSwingResult.json').write_text(json.dumps(
        {'success': True, 'length': anim.get_play_length(), 'frames': FRAMES + 1}, indent=2))
    unreal.log('Tool chop built')


if __name__ == '__main__':
    main()
