"""Import the single-player front end's pictures (owner, November 7). Safe to run again. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py Scripts/Setup/build_front_end.py"
- Art/UI/FrontEnd/WorldMap_PortSelect.png (Scripts/Art/draw_port_select_map.py): the whole world on the Freeport choice.
- Art/UI/FrontEnd/LoadingVoyage.png: the loading screen's picture, made by ChatGPT for the owner with its page design
  (LoadingScreen_Design.html, which UEWLoadingWidget paints in the game).
Both as UI textures under /Game/Elitewake/UI/FrontEnd. No map is touched.
"""
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DEST = '/Game/Elitewake/UI/FrontEnd'
PICTURES = {'T_WorldMap_PortSelect': 'Art/UI/FrontEnd/WorldMap_PortSelect.png', 'T_LoadingVoyage': 'Art/UI/FrontEnd/LoadingVoyage.png'}


def import_picture(name, source):
    task = unreal.AssetImportTask()
    for k, v in {'filename': str(ROOT / source), 'destination_path': DEST, 'destination_name': name, 'automated': True,
                 'replace_existing': True, 'save': True}.items():
        task.set_editor_property(k, v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(f'{DEST}/{name}')
    assert texture, name
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('never_stream', True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return [texture.blueprint_get_size_x(), texture.blueprint_get_size_y()]


def main():
    result = {name: import_picture(name, source) for name, source in PICTURES.items()}
    Path(unreal.Paths.project_saved_dir(), 'FrontEndResult.json').write_text(json.dumps({'success': True, 'textures': result}, indent=2))
    unreal.log(f'Front end pictures imported: {result}')
    if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
        unreal.SystemLibrary.quit_editor()


if __name__ == '__main__':
    main()
