"""Import the owner title splash, water mask, prompt, and main-menu concept.

Run in Unreal Editor from this project. Source PNGs are kept in Art/UI/Title/2026-10-13.
It creates a UI material that UV-animates pixels inside the white water mask only. It does not
modify maps or editor preferences.
"""
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / 'Art/UI/Title/2026-10-13'
DESTINATION = '/Game/Elitewake/UI/Title'
ASSETS = {
    'Elitewake-Starter-Screen-Owner-v1.png': 'T_ElitewakeStarterScreen_20261013',
    'Elitewake-Starter-WaterMask-v1.png': 'T_TitleWaterMask_20261013',
    'Press-Any-Key-To-Start-v2.png': 'T_PressAnyKeyToStart_20261013_v2',
}

tools = unreal.AssetToolsHelpers.get_asset_tools()
for filename, name in ASSETS.items():
    source = SOURCE / filename
    if not source.is_file():
        raise FileNotFoundError(source)
    if unreal.EditorAssetLibrary.does_asset_exist(f'{DESTINATION}/{name}'):
        unreal.log(f'EW_TITLE_ASSET kept existing {DESTINATION}/{name}')
        continue
    task = unreal.AssetImportTask()
    for key, value in {
        'filename': str(source), 'destination_path': DESTINATION, 'destination_name': name,
        'automated': True, 'replace_existing': False, 'save': True,
    }.items():
        task.set_editor_property(key, value)
    tools.import_asset_tasks([task])
    texture = unreal.load_asset(f'{DESTINATION}/{name}')
    if not texture:
        raise RuntimeError(f'Failed to import {source}')
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('never_stream', True)
    if name == 'T_TitleWaterMask_20261013':
        texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
        texture.set_editor_property('srgb', False)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    unreal.log(f'EW_TITLE_ASSET imported {DESTINATION}/{name}')

unreal.log('EW_TITLE_ASSET import complete')

import runpy
runpy.run_path(str(ROOT / 'Scripts/Setup/create_title_water_material.py'))
