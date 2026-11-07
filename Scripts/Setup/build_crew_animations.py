"""Make the animations of a survivor at a helm or a capstan, and the paddle a raft's paddler holds. Safe to run again.
Run in the editor, outside Play, then configure_attack_animations.py:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Both are keyed on the mannequin's standing idle (anim_keying.py), as the project has neither:
- AS_Paddle_v1: a paddle stroke, 1.6 s, looping. The body twists to one side and leans in as both arms reach
  forward, then pull back past the hip; then the same on the other side.
- AS_HelmHold_v1: hands up on the wheel or tiller, arms forward and bent, swaying a little, 2 s, looping.
- AS_CapstanPush_v1: leaning into a capstan bar at waist height with both hands, driving forward and easing, 1.6 s,
  looping, while the anchor is worked.
- SM_HeldPaddle_v1: one paddle, gripped near its T-handle with the blade below, held in the right hand while the
  raft's paddles are taken up (it is the raft paddles fitting's held mesh).
Angles, timing and sizes are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anim_keying  # noqa: E402
from build_held_tools import GRIP  # noqa: E402
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/Animations/Crew'
PADDLE_ITEM = '/Game/Elitewake/Items/Ships/DA_RaftPaddles'
PADDLE_MESH = '/Game/Elitewake/World/Tools/SM_HeldPaddle_v1'

# Keys (time 0-1, degrees): about X, arms swing forward and up and the spine leans back; about Z the body twists.
STROKE_ARM = [(0, 70), (.25, 20), (.5, 70), (.75, 20), (1, 70)]       # reach forward, pull back, on each side
STROKE_ELBOW = [(0, 15), (.25, 50), (.5, 15), (.75, 50), (1, 15)]
STROKE_TWIST = [(0, 18), (.25, 0), (.5, -18), (.75, 0), (1, 18)]
STROKE_LEAN = [(0, -10), (.25, -4), (.5, -10), (.75, -4), (1, -10)]
HOLD_ARM = [(0, 52), (.5, 56), (1, 52)]
HOLD_ELBOW = [(0, 42), (.5, 38), (1, 42)]
HOLD_WRIST = [(0, -10), (1, -10)]
PUSH_LEAN = [(0, -14), (.5, -24), (1, -14)]
PUSH_ARM = [(0, 48), (.5, 58), (1, 48)]
PUSH_ELBOW = [(0, 34), (.5, 16), (1, 34)]


def paddle():
    """Gripped at the origin near the top; T-handle above, the shaft and blade below (along -Z)."""
    b = Builder()
    b.box((0, 0, 14), (4, 16, 4))
    b.tube([(0, 0, 14), (0, 0, -120)], 1.8, sides=10)
    b.box((0, 0, -148), (2.2, 16, 56))
    return b


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    stroke = anim_keying.build(f'{FOLDER}/AS_Paddle_v1', 48, {
        'spine_03': [('z', STROKE_TWIST), ('x', STROKE_LEAN)],
        'upperarm_r': [('x', STROKE_ARM)], 'upperarm_l': [('x', STROKE_ARM)],
        'lowerarm_r': [('x', STROKE_ELBOW)], 'lowerarm_l': [('x', STROKE_ELBOW)]}, 'Build paddle stroke')
    hold = anim_keying.build(f'{FOLDER}/AS_HelmHold_v1', 60, {
        'upperarm_r': [('x', HOLD_ARM)], 'upperarm_l': [('x', HOLD_ARM)],
        'lowerarm_r': [('x', HOLD_ELBOW)], 'lowerarm_l': [('x', HOLD_ELBOW)],
        'hand_r': [('x', HOLD_WRIST)], 'hand_l': [('x', HOLD_WRIST)]}, 'Build helm hold')
    push = anim_keying.build(f'{FOLDER}/AS_CapstanPush_v1', 48, {
        'spine_03': [('x', PUSH_LEAN)],
        'upperarm_r': [('x', PUSH_ARM)], 'upperarm_l': [('x', PUSH_ARM)],
        'lowerarm_r': [('x', PUSH_ELBOW)], 'lowerarm_l': [('x', PUSH_ELBOW)]}, 'Build capstan push')
    mesh = write_static_mesh(paddle(), PADDLE_MESH, [make_timber_material()], 40.0, collision=False)
    item = unreal.load_asset(PADDLE_ITEM)
    assert item, PADDLE_ITEM
    item.set_editor_property('held_mesh', mesh)
    item.set_editor_property('held_mesh_transform', GRIP)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    Path(unreal.Paths.project_saved_dir(), 'CrewAnimationsResult.json').write_text(json.dumps(
        {'success': True, 'stroke': stroke.get_play_length(), 'hold': hold.get_play_length(), 'push': push.get_play_length()}, indent=2))
    unreal.log('Crew animations built')


if __name__ == '__main__':
    main()
