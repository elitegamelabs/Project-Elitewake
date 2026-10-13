"""Import the approved title splash and main-menu concept into /Game/Elitewake/UI/Title.

Run in Unreal Editor from this project. Source PNGs are kept in Art/UI/Title/2026-10-13.
This script only imports textures; it does not modify maps or editor preferences.
"""
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / 'Art/UI/Title/2026-10-13'
DESTINATION = '/Game/Elitewake/UI/Title'
ASSETS = {
    'Title-Dock-Background-v1.png': 'T_TitleBackground_20261013',
    'Elitewake-Logo-v1.png': 'T_ElitewakeLogo_20261013',
    'Press-Any-Key-v1.png': 'T_PressAnyKey_20261013',
    'Main-Menu-Concept-Blurred-Multiplayer-v1.png': 'T_MainMenu_20261013',
    'Title-Waves-4Frame-v1.png': 'T_TitleWaves_4Frame_20261013',
}

tools = unreal.AssetToolsHelpers.get_asset_tools()
for filename, name in ASSETS.items():
    source = SOURCE / filename
    if not source.is_file():
        raise FileNotFoundError(source)
    task = unreal.AssetImportTask()
    for key, value in {
        'filename': str(source), 'destination_path': DESTINATION, 'destination_name': name,
        'automated': True, 'replace_existing': True, 'save': True,
    }.items():
        task.set_editor_property(key, value)
    tools.import_asset_tasks([task])
    texture = unreal.load_asset(f'{DESTINATION}/{name}')
    if not texture:
        raise RuntimeError(f'Failed to import {source}')
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('never_stream', True)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    unreal.log(f'EW_TITLE_ASSET imported {DESTINATION}/{name}')

unreal.log('EW_TITLE_ASSET import complete')
