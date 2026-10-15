"""Make the survivor's gathering and harvesting motions (owner, October 15: "you don't move to collect anything
yet"; the hatchet and pickaxe should strike like the work they do). Safe to run again. Run in the editor, outside
Play, after build_core_tools.py:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Keyed on the standing idle (anim_keying.py), without root motion:
  - AS_GatherGround_v1: squat (knees bend, feet planted), lean in, the right hand reaches to the ground, takes hold
    and brings what it took up to the chest, then stands. For sticks, fiber plants and anything picked up.
  - AS_GatherBush_v1: lean to the bush and pick with both hands in turn, at waist height. For berries.
  - AS_Chop_v1: the hatchet's chop at a trunk: the body winds up turned to the right with the hatchet raised behind
    the shoulder, then turns through a diagonal stroke across the body at chest height. Contact at CHOP_CONTACT.
  - AS_Mine_v1: the pickaxe's blow at a rock: raised overhead, then driven down with a lean and a bend of the knees
    to the rock at the feet. Contact at MINE_CONTACT.
The contact moments are where the game shows the blow landing (EWCharacter: ChopContactSeconds, MineContactSeconds).
Angles and timing are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anim_keying  # noqa: E402

ANIMS = '/Game/Elitewake/Animations/Tools'
CHARACTER = '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
CHOP_FRAMES, CHOP_CONTACT = 30, .45     # 1.0 s, contact at 0.45 s
MINE_FRAMES, MINE_CONTACT = 30, .5      # 1.0 s, contact at 0.5 s
ROLL = 70.0                             # the chop's forearm roll at contact


def squat(depth, thigh, keys):
    """Pelvis dropped by `depth` cm with thighs at `thigh` degrees, following key times `keys` (0..1 weights)."""
    scaled = lambda value: [(t, value * w) for t, w in keys]   # noqa: E731
    legs = {}
    for side in ('l', 'r'):
        legs[f'thigh_{side}'] = [('x', scaled(thigh))]
        legs[f'calf_{side}'] = [('x', scaled(-2 * thigh))]
        legs[f'foot_{side}'] = [('x', scaled(thigh))]
    legs['pelvis'] = [('drop', scaled(depth))]
    return legs


def animations():
    a = {}
    down = [(0, 0), (.3, 1), (.68, 1), (1, 0)]
    a['gather_ground'] = anim_keying.build(f'{ANIMS}/AS_GatherGround_v1', 42, {
        **squat(44, 62, down),
        # Fold well forward over the knees so the hand reaches the ground in front of the feet.
        'spine_01': [('x', [(0, 0), (.3, -18), (.5, -18), (.66, -8), (1, 0)])],
        'spine_03': [('x', [(0, 0), (.3, -30), (.5, -30), (.66, -14), (1, 0)])],
        'spine_04': [('x', [(0, 0), (.3, -14), (.5, -14), (.66, -6), (1, 0)])],
        # Reach down, close the hand on it, bring it up to the chest.
        'upperarm_r': [('x', [(0, 0), (.3, 12), (.45, 16), (.66, 55), (.82, 40), (1, 0)])],
        'lowerarm_r': [('x', [(0, 0), (.3, 4), (.45, 6), (.66, 95), (.82, 70), (1, 0)])],
        'hand_r': [('x', [(0, 0), (.3, -15), (.45, -30), (.66, 10), (1, 0)])],
        'upperarm_l': [('x', [(0, 0), (.3, 8), (.7, 8), (1, 0)])],
        'lowerarm_l': [('x', [(0, 0), (.3, 35), (.7, 35), (1, 0)])]}, 'Gather from the ground')
    a['gather_bush'] = anim_keying.build(f'{ANIMS}/AS_GatherBush_v1', 36, {
        **squat(16, 28, [(0, 0), (.25, 1), (.75, 1), (1, 0)]),
        'spine_03': [('x', [(0, 0), (.25, -24), (.75, -24), (1, 0)])],
        'upperarm_r': [('x', [(0, 0), (.25, 40), (.4, 34), (.55, 44), (.7, 32), (1, 0)])],
        'lowerarm_r': [('x', [(0, 0), (.25, 22), (.4, 55), (.55, 18), (.7, 60), (1, 0)])],
        'upperarm_l': [('x', [(0, 0), (.32, 32), (.48, 42), (.62, 30), (.8, 38), (1, 0)])],
        'lowerarm_l': [('x', [(0, 0), (.32, 50), (.48, 20), (.62, 58), (.8, 25), (1, 0)])]}, 'Pick from a bush')
    c = CHOP_CONTACT
    a['chop'] = anim_keying.build(f'{ANIMS}/AS_Chop_v1', CHOP_FRAMES, {
        # Turn right to wind up, through to the left in the stroke (about Z, positive turns to the right).
        'spine_03': [('z', [(0, 0), (c - .17, 26), (c, -8), (c + .15, -20), (1, 0)]), ('x', [(0, 0), (c, -8), (1, 0)])],
        'spine_04': [('z', [(0, 0), (c - .17, 12), (c, -4), (c + .15, -10), (1, 0)])],
        'upperarm_r': [('x', [(0, 0), (c - .17, 125), (c, 78), (c + .15, 60), (1, 0)]),
                       ('z', [(0, 0), (c - .17, 30), (c, -5), (c + .15, -25), (1, 0)])],
        # The forearm rolls into the stroke so the blade lies flat into the trunk, not edge-up.
        'lowerarm_r': [('x', [(0, 0), (c - .17, 75), (c, 12), (c + .15, 8), (1, 0)]),
                       ('y', [(0, 0), (c - .17, 0), (c, ROLL), (c + .15, ROLL), (1, 0)])],
        'hand_r': [('x', [(0, 0), (c - .17, 25), (c, -95), (c + .15, -90), (1, 0)])],
        'upperarm_l': [('x', [(0, 0), (c - .17, 30), (c, 15), (1, 0)])]}, 'Chop a tree')
    m = MINE_CONTACT
    a['mine'] = anim_keying.build(f'{ANIMS}/AS_Mine_v1', MINE_FRAMES, {
        **squat(14, 28, [(0, 0), (m - .2, .2), (m, 1), (m + .2, .9), (1, 0)]),
        'spine_03': [('x', [(0, 0), (m - .2, 10), (m, -30), (m + .2, -26), (1, 0)])],
        'spine_04': [('x', [(0, 0), (m - .2, 5), (m, -12), (1, 0)])],
        'upperarm_r': [('x', [(0, 0), (m - .2, 165), (m, 30), (m + .2, 26), (1, 0)])],
        'lowerarm_r': [('x', [(0, 0), (m - .2, 85), (m, 6), (m + .2, 6), (1, 0)])],
        'hand_r': [('x', [(0, 0), (m - .2, 25), (m, -55), (m + .2, -50), (1, 0)])],
        'upperarm_l': [('x', [(0, 0), (m - .2, 40), (m, 25), (1, 0)])]}, 'Strike a rock')
    return a


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    anims = animations()
    blueprint = unreal.load_asset(CHARACTER)
    defaults = unreal.get_default_object(unreal.load_object(None, f'{CHARACTER}.BP_ThirdPersonCharacter_C'))
    for prop, key in (('gather_ground_animation', 'gather_ground'), ('gather_bush_animation', 'gather_bush'),
                      ('chop_animation', 'chop'), ('mine_animation', 'mine')):
        defaults.set_editor_property(prop, anims[key])
    defaults.set_editor_property('chop_contact_seconds', CHOP_CONTACT * CHOP_FRAMES / anim_keying.RATE)
    defaults.set_editor_property('mine_contact_seconds', MINE_CONTACT * MINE_FRAMES / anim_keying.RATE)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    assert unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    Path(unreal.Paths.project_saved_dir(), 'WorkAnimationsResult.json').write_text(json.dumps({
        'success': True, 'animations': {k: round(v.get_play_length(), 2) for k, v in anims.items()}}, indent=2))
    unreal.log('Work animations built')


if __name__ == '__main__':
    main()
