"""Imports Art/UI/Journal/JournalParchment.png as /Game/Elitewake/UI/Journal/T_JournalParchment for the Journal pages (owner, October 22). Run in the editor:
    UnrealEditor-Cmd.exe EW.uproject -ExecutePythonScript=<this file>"""
import unreal
from pathlib import Path

source = Path(unreal.Paths.project_dir()) / 'Art' / 'UI' / 'Journal' / 'JournalParchment.png'
assert source.exists(), source
task = unreal.AssetImportTask()
task.set_editor_property('filename', str(source))
task.set_editor_property('destination_path', '/Game/Elitewake/UI/Journal')
task.set_editor_property('destination_name', 'T_JournalParchment')
task.set_editor_property('replace_existing', True)
task.set_editor_property('automated', True)
task.set_editor_property('save', True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
texture = unreal.load_asset('/Game/Elitewake/UI/Journal/T_JournalParchment')
assert texture, 'the texture did not import'
texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
texture.set_editor_property('srgb', True)
texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
texture.set_editor_property('never_stream', True)
assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
unreal.log('Journal parchment imported')
unreal.SystemLibrary.quit_editor()
