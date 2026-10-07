"""Missing-only Azul Berry fixture. Food stack 500 is specified; weight is test tuning.
Food identity does not implement eating, healing, freshness or spoilage.
"""
import unreal
path='/Game/Elitewake/Items/Testing/DA_TestAzulBerry'
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.log('Preserving '+path)
else:
    cls=unreal.load_class(None,'/Script/EW.EWItemDefinition')
    factory=unreal.DataAssetFactory(); factory.set_editor_property('data_asset_class',cls)
    asset=unreal.AssetToolsHelpers.get_asset_tools().create_asset('DA_TestAzulBerry','/Game/Elitewake/Items/Testing',cls,factory)
    assert asset
    asset.set_editor_property('item_id','Test.AzulBerry')
    asset.set_editor_property('display_name','Azul Berry (Test)')
    asset.set_editor_property('description','Opt-in berry gathering fixture. Food stack 500; weight/yield are draft tuning. Eating, healing and freshness are not implemented.')
    asset.set_editor_property('category',unreal.EWItemCategory.CONSUMABLE)
    asset.set_editor_property('food_kind',unreal.EWFoodKind.BERRY)
    asset.set_editor_property('max_stack_size',500)
    asset.set_editor_property('unit_weight',.01)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
