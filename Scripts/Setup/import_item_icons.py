"""Import the cleaned item icons (Scripts/Art/cut_item_icons.py) and give them to the items that show them.
Safe to run again: icons are re-imported over themselves, so a recut replaces them.
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Only the inventory picture changes; no recipe, unlock, value or starting inventory. Items without matching art
(the test hats) keep their fallback. Raw Fish and Raw Meat keep their own steak-motif icons.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / 'Art/Items/Icons'
FOLDER = '/Game/Elitewake/UI/ItemIcons'
TEST = '/Game/Elitewake/Items/Testing'
# Item asset -> icon name.
ITEMS = {
    f'{TEST}/DA_TestWood': 'Wood', f'{TEST}/DA_TestThatch': 'Thatch', f'{TEST}/DA_TestFiber': 'Fiber',
    f'{TEST}/DA_TestStone': 'Stone', f'{TEST}/DA_TestSticks': 'Sticks', f'{TEST}/DA_TestAzulBerry': 'AzrenBerry',
    f'{TEST}/DA_TestToxicBerry': 'SpoiledBerries', f'{TEST}/DA_TestHide': 'Hide', f'{TEST}/DA_TestOre': 'CopperOre',
    f'{TEST}/DA_TestWoodenAxe': 'WoodenAxe', f'{TEST}/DA_TestWoodenPickaxe': 'WoodenPickaxe',
    f'{TEST}/DA_TestWoodenShovel': 'WoodenShovel', f'{TEST}/DA_TestHideWaterFlask': 'WaterSkin',
    f'{TEST}/DA_TestHatchet': 'StoneAxe', f'{TEST}/DA_TestPickaxe': 'StonePickaxe', f'{TEST}/DA_TestInnTorch': 'Torch',
    f'{TEST}/DA_TestRepairKit': 'RepairKit', f'{TEST}/DA_TestShipHelm': 'ShipWheel',
    f'{TEST}/DA_TestSailSmall': 'SmallSail', f'{TEST}/DA_TestSailMedium': 'MediumSail', f'{TEST}/DA_TestSailLarge': 'LargeSail',
}


def import_icon(name):
    filename = SOURCE / f'{name}-v1.png'
    assert filename.is_file(), filename
    asset = f'T_Icon_{name}_v1'
    task = unreal.AssetImportTask()
    for k, v in {'filename': str(filename), 'destination_path': FOLDER, 'destination_name': asset,
                 'automated': True, 'replace_existing': True, 'save': True}.items():
        task.set_editor_property(k, v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(f'{FOLDER}/{asset}')
    assert isinstance(texture, unreal.Texture2D), asset
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('srgb', True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return texture


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    icons = {name: import_icon(name) for name in sorted(set(ITEMS.values()) | {'Cannon', 'CannonAmmo'})}
    bound = {}
    for path, name in ITEMS.items():
        item = unreal.load_asset(path)
        assert item, path
        item.set_editor_property('icon', icons[name])
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
        bound[path.rsplit('/', 1)[1]] = name
    (ROOT / 'Saved/ItemIconsResult.json').write_text(json.dumps({'success': True, 'icons': len(icons), 'bound': bound}, indent=2))
    unreal.log(f'Imported {len(icons)} item icons and bound {len(bound)} items')


if __name__ == '__main__':
    main()
