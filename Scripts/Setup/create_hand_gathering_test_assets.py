"""Create missing opt-in Fiber/Sticks fixtures through Unreal asset APIs.
Existing assets are preserved. Resource stack 250 follows the Bible; weights and
node yields are test tuning, not approved production resource balance.
"""
import unreal

cls = unreal.load_class(None, '/Script/EW.EWItemDefinition')
assert cls
factory = unreal.DataAssetFactory()
factory.set_editor_property('data_asset_class', cls)
for name, item_id, label, weight in [('DA_TestFiber', 'Test.Fiber', 'Fiber (Test)', .01),
                                      ('DA_TestSticks', 'Test.Sticks', 'Sticks (Test)', .05)]:
    path = '/Game/Elitewake/Items/Testing/' + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log('Preserving existing fixture: ' + path)
        continue
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Elitewake/Items/Testing', cls, factory)
    assert asset
    asset.set_editor_property('item_id', item_id)
    asset.set_editor_property('display_name', label)
    asset.set_editor_property('description', 'Opt-in gathering fixture. Resource stack 250; weight and node yields are temporary test tuning.')
    asset.set_editor_property('category', unreal.EWItemCategory.RESOURCE)
    asset.set_editor_property('max_stack_size', 250)
    asset.set_editor_property('unit_weight', weight)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
