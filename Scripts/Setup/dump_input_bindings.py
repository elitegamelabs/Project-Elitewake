"""Read-only: every key mapped in the project's input mapping contexts (for the Options' Controls page). Writes
Saved/InputBindings.json.
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>
"""
import json
from pathlib import Path
import unreal

out = {}
registry = unreal.AssetRegistryHelpers.get_asset_registry()
for data in registry.get_assets_by_class(unreal.TopLevelAssetPath('/Script/EnhancedInput', 'InputMappingContext'), True):
    imc = unreal.load_asset(str(data.package_name))
    rows = []
    for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings') if hasattr(imc, 'default_key_mappings') else imc.get_editor_property('mappings'):
        action = m.get_editor_property('action')
        key = m.get_editor_property('key')
        rows.append([action.get_name() if action else None, str(key.get_editor_property('key_name'))])
    out[str(data.package_name)] = rows
Path(unreal.Paths.project_saved_dir(), 'InputBindings.json').write_text(json.dumps(out, indent=1))
