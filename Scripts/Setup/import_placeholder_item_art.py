"""Import generated v1 PNG icons and assign them to opt-in item fixtures only.
No recipe unlocks, inventory grants, gameplay tuning or production map changes.
"""
import unreal, json
from pathlib import Path

root = Path(unreal.Paths.project_dir()).resolve()
mapping = [('Axe','WoodenAxe'),('Shovel','WoodenShovel'),('Pickaxe','WoodenPickaxe'),
           ('Flask','HideWaterFlask'),('Torch','InnTorch'),('RepairKit','RepairKit')]
results = []
for source, item_name in mapping:
    filename = root / 'Art/Placeholders/ItemIcons' / (source+'-v1.png')
    assert filename.is_file(), filename
    texture_path = '/Game/Elitewake/UI/PlaceholderIcons/T_'+source+'_v1'
    if not unreal.EditorAssetLibrary.does_asset_exist(texture_path):
        task = unreal.AssetImportTask()
        task.set_editor_property('filename',str(filename))
        task.set_editor_property('destination_path','/Game/Elitewake/UI/PlaceholderIcons')
        task.set_editor_property('destination_name','T_'+source+'_v1')
        task.set_editor_property('automated',True)
        task.set_editor_property('replace_existing',False)
        task.set_editor_property('save',True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(texture_path)
    assert isinstance(texture,unreal.Texture2D), texture_path
    texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('srgb',True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
    item = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_Test'+item_name)
    assert item, item_name
    item.set_editor_property('icon',texture)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    results.append({'item':item.get_path_name(),'texture':texture.get_path_name()})
(root/'Saved/PlaceholderArtImportResult.json').write_text(json.dumps({'success':True,'assets':results},indent=2))
unreal.log('Imported '+str(len(results))+' generated placeholder icons; fixtures only.')
