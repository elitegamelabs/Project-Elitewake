"""Probe what MetaHuman Creator does unattended on this PC (November 7, the pirate survivor): create a character asset,
ask for the face rig (auto-rigging) and the skin textures (both go through Epic's MetaHuman cloud service), and record
what worked. Writes Saved/MetaHumanProbe.json. Leaves the probe asset at /Game/Elitewake/Characters/MetaHumans/MH_Probe.
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"   (EW_QUIT_WHEN_DONE=1 quits after)
"""
import json
import os
from pathlib import Path
import unreal

FOLDER = '/Game/Elitewake/Characters/MetaHumans'
report = {}


def step(name, fn):
    try:
        result = fn()
        report[name] = {'ok': True, 'result': str(result)}
    except Exception as e:      # noqa: BLE001
        report[name] = {'ok': False, 'error': repr(e)}
    unreal.log(f'MHPROBE {name}: {report[name]}')


character = unreal.load_asset(f'{FOLDER}/MH_Probe')
if not character:
    character = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name='MH_Probe', package_path=FOLDER, asset_class=unreal.MetaHumanCharacter,
        factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew))
report['created'] = character is not None
mh = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
report['edit'] = mh.try_add_object_to_edit(character)
report['subsystem_functions'] = sorted(n for n in dir(mh) if not n.startswith('_'))
try:
    def rig():
        p = unreal.MetaHumanCharacterAutoRiggingRequestParams()
        p.blocking = True
        p.report_progress = False
        p.rig_type = unreal.MetaHumanRigType.JOINTS_ONLY
        return mh.request_auto_rigging(character, p)
    step('auto_rig', rig)
    report['rig_state'] = str(mh.get_rigging_state(character)) if hasattr(mh, 'get_rigging_state') else 'n/a'

    def textures():
        p = unreal.MetaHumanCharacterTextureRequestParams()
        p.blocking = True
        p.report_progress = False
        return mh.request_texture_sources(character, p)
    step('textures', textures)
finally:
    if mh.is_object_added_for_editing(character):
        mh.remove_object_to_edit(character)
unreal.EditorAssetLibrary.save_loaded_asset(character)
Path(unreal.Paths.project_saved_dir(), 'MetaHumanProbe.json').write_text(json.dumps(report, indent=2))
if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
    unreal.SystemLibrary.quit_editor()
