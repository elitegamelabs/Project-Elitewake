"""Import the crystal, obsidian and coal icons (Scripts/Art/make_crystal_icons.py) and give them to those five items.
Safe to run again. Run in the editor outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
Only the inventory picture changes."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / 'Art/Items/Icons'
FOLDER = '/Game/Elitewake/UI/ItemIcons'
ITEMS = '/Game/Elitewake/Items/Resources'
NAMES = ('Ruby', 'Sapphire', 'Emerald', 'Obsidian', 'Coal')


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    bound = []
    for name in NAMES:
        task = unreal.AssetImportTask()
        for k, v in {'filename': str(SOURCE / f'{name}-v1.png'), 'destination_path': FOLDER, 'destination_name': f'T_Icon_{name}_v1',
                     'automated': True, 'replace_existing': True, 'save': True}.items():
            task.set_editor_property(k, v)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = unreal.load_asset(f'{FOLDER}/T_Icon_{name}_v1')
        assert isinstance(texture, unreal.Texture2D), name
        texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        texture.set_editor_property('srgb', True)
        assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
        item = unreal.load_asset(f'{ITEMS}/DA_{name}')
        assert item, name
        item.set_editor_property('icon', texture)
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
        bound.append(name)
    (ROOT / 'Saved/CrystalIconsResult.json').write_text(json.dumps({'success': True, 'bound': bound}, indent=2))
    unreal.log(f'Crystal icons bound: {bound}')


if __name__ == '__main__':
    main()
