"""Imports the controller button icons, Art/UI/ControllerIcons/<Xbox|PlayStation>/T_Icon_*.png (Scripts/Art/publish_controller_icons.py),
as /Game/Elitewake/UI/Icons/Controller/<Family>/T_Icon_* UI textures for FEWControllerIcons (owner, November 1). Safe to run again.
Run in the editor with source control off, so the editor's git plugin cannot put the old assets back:
    UnrealEditor-Cmd.exe EW.uproject -SCCProvider=None -ExecutePythonScript=<this file>"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()) / 'Art' / 'UI' / 'ControllerIcons'
DEST = '/Game/Elitewake/UI/Icons/Controller'

tasks = []
for family in ('Xbox', 'PlayStation'):
    for source in sorted((ROOT / family).glob('T_Icon_*.png')):
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', str(source))
        task.set_editor_property('destination_path', f'{DEST}/{family}')
        task.set_editor_property('destination_name', source.stem)
        task.set_editor_property('replace_existing', True)
        task.set_editor_property('automated', True)
        task.set_editor_property('save', True)
        tasks.append(task)
assert len(tasks) == 36, f'expected 36 icons, found {len(tasks)}: run Scripts/Art/publish_controller_icons.py first'
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for task in tasks:
    path = f"{task.get_editor_property('destination_path')}/{task.get_editor_property('destination_name')}"
    texture = unreal.load_asset(path)
    assert texture, f'{path} did not import'
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)   # UserInterface2D: no block artefacts on glossy edges
    texture.set_editor_property('srgb', True)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('never_stream', True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture), path
unreal.log(f'Controller icons imported: {len(tasks)}')
unreal.SystemLibrary.quit_editor()
