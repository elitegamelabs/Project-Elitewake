"""Give the survivor its swing and flinch animations, from the Unreal mannequin's unarmed set. Safe to run again.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Attack plays the three unarmed swings in turn; a survivor who is struck plays a light hit reaction. Both play
through the locomotion blueprint's default slot, over whatever the legs are doing. The swings' root motion is
turned off: a swing must never move the survivor, or it would shift their aim and their place on a deck.
"""
import json
from pathlib import Path
import unreal

CHARACTER = '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
ANIMS = '/Game/Characters/Mannequins/Anims'
SWINGS = [f'{ANIMS}/Unarmed/Attack/MM_Attack_0{k}' for k in (1, 2, 3)]
FLINCH = f'{ANIMS}/Rifle/HitReact/MM_HitReact_Front_Lgt_01'


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    swings = [unreal.load_asset(p) for p in SWINGS]
    flinch = unreal.load_asset(FLINCH)
    assert all(swings) and flinch, 'mannequin animations missing'
    for animation in swings + [flinch]:
        if animation.get_editor_property('enable_root_motion'):
            animation.set_editor_property('enable_root_motion', False)
            assert unreal.EditorAssetLibrary.save_loaded_asset(animation)
    blueprint = unreal.load_asset(CHARACTER)
    defaults = unreal.get_default_object(unreal.load_object(None, f'{CHARACTER}.BP_ThirdPersonCharacter_C'))
    defaults.set_editor_property('attack_animations', swings)
    defaults.set_editor_property('hit_react_animation', flinch)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    assert unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    Path(unreal.Paths.project_saved_dir(), 'AttackAnimationsResult.json').write_text(json.dumps(
        {'success': True, 'swings': [s.get_name() for s in swings], 'flinch': flinch.get_name()}, indent=2))
    unreal.log('Attack animations configured')


if __name__ == '__main__':
    main()
