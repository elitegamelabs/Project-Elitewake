"""Persist opt-in M5F metadata fixtures. No gear appearance, protection or starting-item grant."""
import unreal
for name,item_id,label,weight in [('DA_TestHat','Test.Hat','Hat (Test)',2.0),
                                  ('DA_TestHatAlternate','Test.HatAlternate','Alternate Hat (Test)',3.0)]:
    folder='/Game/Elitewake/Items/Testing'
    path=folder+'/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log('Preserving existing '+path)
        continue
    factory=unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class',unreal.EWItemDefinition)
    item=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.EWItemDefinition,factory)
    assert item
    item.set_editor_property('item_id',item_id)
    item.set_editor_property('display_name',label)
    item.set_editor_property('description','Equipment transfer fixture. Head slot only; no protection or appearance. Weight is temporary test tuning.')
    item.set_editor_property('category',unreal.EWItemCategory.CLOTHING)
    item.set_editor_property('equipment_slot',unreal.EWEquipmentSlot.HEAD)
    item.set_editor_property('max_stack_size',1)
    item.set_editor_property('unit_weight',weight)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)
