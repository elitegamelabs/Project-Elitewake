"""Controller bindings missing from IMC_Default (November 7, controller-complete play). Safe to run again:
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>
- First / third person (IA_TogglePerspective) on the right-stick click (R3). R3 also demolishes in Build Mode, where
  UEWBuildComponent takes the key first, so the two never meet.
Writes Saved/ControllerBindings.json.
"""
import json
from pathlib import Path
import unreal

IMC = '/Game/Input/IMC_Default'
ADD = [('/Game/Input/Actions/IA_TogglePerspective', 'Gamepad_RightThumbstick')]
imc = unreal.load_asset(IMC)
report = {'added': [], 'present': []}
existing = [(m.get_editor_property('action').get_path_name() if m.get_editor_property('action') else '', str(m.get_editor_property('key').get_editor_property('key_name')))
            for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
for action_path, key_name in ADD:
    action = unreal.load_asset(action_path)
    if not action:
        # The action may live elsewhere: find it by name.
        name = action_path.rsplit('/', 1)[1]
        found = [d for d in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(unreal.TopLevelAssetPath('/Script/EnhancedInput', 'InputAction'), True)
                 if str(d.asset_name) == name]
        action = unreal.load_asset(str(found[0].package_name)) if found else None
    assert action, action_path
    if any(a.endswith(action.get_name()) and k == key_name for a, k in existing):
        report['present'].append([action.get_name(), key_name])
        continue
    key = unreal.Key()
    key.set_editor_property('key_name', key_name)
    imc.map_key(action, key)
    report['added'].append([action.get_name(), key_name])
imc.modify()
assert unreal.EditorAssetLibrary.save_loaded_asset(imc, False)      # map_key does not mark the asset changed
Path(unreal.Paths.project_saved_dir(), 'ControllerBindings.json').write_text(json.dumps(report, indent=2))
