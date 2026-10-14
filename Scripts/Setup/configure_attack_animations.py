"""Give the survivor its swings, flinch and ladder climbing animations. Safe to run again.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Attack plays the three unarmed swings in turn; a survivor who is struck plays a light hit reaction. Both play
through the locomotion blueprint's default slot, over whatever the legs are doing. The swings' root motion is
turned off: a swing must never move the survivor, or it would shift their aim and their place on a deck.
With a tool in hand the survivor chops instead (AS_ToolChop_v1, from Scripts/Setup/build_tool_swing.py, run that
first). On a ladder it plays the animation library's ladder loops: climbing up, climbing down and holding on. At a
helm it holds the wheel, or strokes with a paddle on the raft, and at a capstan it leans into the bars
(build_crew_animations.py, run that first).
"""
import json
from pathlib import Path
import unreal

CHARACTER = '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
ANIMS = '/Game/Characters/Mannequins/Anims'
SWINGS = [f'{ANIMS}/Unarmed/Attack/MM_Attack_0{k}' for k in (1, 2, 3)]
FLINCH = f'{ANIMS}/Rifle/HitReact/MM_HitReact_Front_Lgt_01'
CHOP = '/Game/Elitewake/Animations/Tools/AS_ToolChop_v1'
LADDER = '/Game/FreeAnimationLibrary/Animations/Ladder'
CREW = '/Game/Elitewake/Animations/Crew'


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    swings = [unreal.load_asset(p) for p in SWINGS]
    flinch = unreal.load_asset(FLINCH)
    chop = unreal.load_asset(CHOP)
    ladder = {k: unreal.load_asset(f'{LADDER}/anim_Ladder_{k}') for k in ('Up', 'Down', 'Idle')}
    stroke, hold = unreal.load_asset(f'{CREW}/AS_Paddle_v1'), unreal.load_asset(f'{CREW}/AS_HelmHold_v1')
    push = unreal.load_asset(f'{CREW}/AS_CapstanPush_v1')
    assert all(swings) and flinch and chop and all(ladder.values()) and stroke and hold and push, \
        'animations missing (run build_tool_swing.py and build_crew_animations.py first)'
    for animation in swings + [flinch, chop] + list(ladder.values()):
        if animation.get_editor_property('enable_root_motion'):
            animation.set_editor_property('enable_root_motion', False)
            assert unreal.EditorAssetLibrary.save_loaded_asset(animation)
    blueprint = unreal.load_asset(CHARACTER)
    defaults = unreal.get_default_object(unreal.load_object(None, f'{CHARACTER}.BP_ThirdPersonCharacter_C'))
    defaults.set_editor_property('attack_animations', swings)
    defaults.set_editor_property('hit_react_animation', flinch)
    defaults.set_editor_property('tool_swing_animations', [chop])
    defaults.set_editor_property('ladder_up_animation', ladder['Up'])
    defaults.set_editor_property('ladder_down_animation', ladder['Down'])
    defaults.set_editor_property('ladder_idle_animation', ladder['Idle'])
    defaults.set_editor_property('paddle_animation', stroke)
    defaults.set_editor_property('helm_hold_animation', hold)
    defaults.set_editor_property('capstan_animation', push)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    assert unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    Path(unreal.Paths.project_saved_dir(), 'AttackAnimationsResult.json').write_text(json.dumps(
        {'success': True, 'swings': [s.get_name() for s in swings], 'flinch': flinch.get_name(), 'tool_swing': chop.get_name(),
         'ladder': [a.get_name() for a in ladder.values()]}, indent=2))
    unreal.log('Attack animations configured')


if __name__ == '__main__':
    main()
