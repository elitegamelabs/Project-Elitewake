"""Apply the animals' temperaments and attacks from build_animals.py to their existing definitions, without rebuilding the
models (owner, November 1: elephants are neutral and defend themselves). Safe to run again. Run in the editor outside Play:
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -run=pythonscript -script=<this file>
Writes Saved/AnimalTemperamentsResult.json.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_animals as B  # noqa: E402

FOLDER = '/Game/Elitewake/Wildlife/Animals'


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    report = {}
    for name, a in B.ANIMALS.items():
        definition = unreal.load_asset(f'{FOLDER}/DA_Animal_{name}')
        if not definition:
            continue
        aggressive, _, _, _, _, _, notice, damage, interval, reach, attack, _ = a['behave']
        for k, v in {'aggressive': aggressive, 'defends_itself': name in B.DEFENDERS, 'notice_range': float(notice),
                     'attack_damage': float(damage), 'attack_interval': float(interval), 'attack_reach': float(reach),
                     'attack_name': attack}.items():
            definition.set_editor_property(k, v)
        assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
        report[name] = {'aggressive': aggressive, 'defends_itself': name in B.DEFENDERS, 'damage': damage, 'reach': reach}
    report['success'] = 'Elephant' in report and report['Elephant']['defends_itself']
    Path(unreal.Paths.project_saved_dir(), 'AnimalTemperamentsResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Animal temperaments: {report}')


main()
