"""Missing-only assets via Unreal APIs; generic ore and all weights are test tuning."""
import unreal

cls = unreal.load_class(None, '/Script/EW.EWItemDefinition')
factory = unreal.DataAssetFactory()
factory.set_editor_property('data_asset_class', cls)
items = [
    ('DA_TestStone', 'Test.Stone', 'Stone (Test)', .1, False, unreal.EWPickaxeTier.NONE),
    ('DA_TestOre', 'Test.Ore', 'Ore (Test)', .1, False, unreal.EWPickaxeTier.NONE),
    ('DA_TestPickaxe', 'Test.Pickaxe', 'Pickaxe (Test)', 1, True, unreal.EWPickaxeTier.NONE),
    # Verification-only capability fixture. This is not the missing production Metal Pick asset.
    ('DA_TestMetalPickaxe', 'DA_TestMetalPickaxe', 'Metal Pickaxe (Test)', 1, True, unreal.EWPickaxeTier.METAL),
]
for name, item_id, label, weight, tool, tier in items:
    path = '/Game/Elitewake/Items/Testing/' + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        if name == 'DA_TestMetalPickaxe':
            # This newly added test asset uses the asset name as its stable primary ID.
            existing = unreal.load_asset(path)
            if existing.get_editor_property('item_id') != name:
                existing.set_editor_property('item_id', name)
                assert unreal.EditorAssetLibrary.save_loaded_asset(existing)
        unreal.log('Preserving ' + path)
        continue
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Elitewake/Items/Testing', cls, factory)
    assert asset
    asset.set_editor_property('item_id', item_id)
    asset.set_editor_property('display_name', label)
    asset.set_editor_property('description', 'Opt-in mining fixture; generic ore, weights and yields are test tuning, not production balance.')
    asset.set_editor_property('category', unreal.EWItemCategory.TOOL if tool else unreal.EWItemCategory.RESOURCE)
    asset.set_editor_property('max_stack_size', 1 if tool else 250)
    asset.set_editor_property('unit_weight', weight)
    if tool:
        asset.set_editor_property('equipment_slot', unreal.EWEquipmentSlot.MAIN_HAND)
        asset.set_editor_property('gathering_tool', unreal.EWGatheringTool.PICKAXE)
        asset.set_editor_property('pickaxe_tier', tier)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
