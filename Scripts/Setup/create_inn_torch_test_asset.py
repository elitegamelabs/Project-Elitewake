"""Opt-in torch metadata; placeholder mesh/art, 1 kg test weight, no light/use or prologue grants."""
import unreal
folder='/Game/Elitewake/Items/Testing'
path=folder+'/DA_TestInnTorch'
if not unreal.EditorAssetLibrary.does_asset_exist(path):
    factory=unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class',unreal.EWItemDefinition)
    item=unreal.AssetToolsHelpers.get_asset_tools().create_asset('DA_TestInnTorch',folder,unreal.EWItemDefinition,factory)
    assert item
    item.set_editor_property('item_id','Test.InnTorch')
    item.set_editor_property('display_name','Torch (Test)')
    item.set_editor_property('description','Introductory pickup fixture. Art, light/use, durability and final weight remain pending.')
    item.set_editor_property('category',unreal.EWItemCategory.TOOL)
    item.set_editor_property('max_stack_size',1)
    item.set_editor_property('unit_weight',1.0)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)
