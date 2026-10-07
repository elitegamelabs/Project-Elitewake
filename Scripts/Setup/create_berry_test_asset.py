"""Author approved Azren display/effects/20-real-minute policy on the existing fixture.
Retains DA_TestAzulBerry/Test.AzulBerry identity, weight and stack tuning.
Creates one inedible toxic resource; no recipes, grants or production bush content.
"""
import unreal
folder = '/Game/Elitewake/Items/Testing'
cls = unreal.load_class(None, '/Script/EW.EWItemDefinition')
factory = unreal.DataAssetFactory()
factory.set_editor_property('data_asset_class', cls)

def fixture(name):
    asset = unreal.load_asset(folder + '/' + name) if unreal.EditorAssetLibrary.does_asset_exist(folder + '/' + name) else None
    return asset or unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)

exists = unreal.EditorAssetLibrary.does_asset_exist(folder + '/DA_TestAzulBerry')
berry = fixture('DA_TestAzulBerry')
assert berry
if not exists:
    berry.set_editor_property('item_id', 'Test.AzulBerry')
    berry.set_editor_property('max_stack_size', 500)
    berry.set_editor_property('unit_weight', .01)
assert str(berry.get_editor_property('item_id')) == 'Test.AzulBerry', 'Unexpected identity: preserve and review'
toxic = fixture('DA_TestToxicBerry')
assert toxic
toxic.set_editor_property('item_id', 'Test.ToxicBerry')
toxic.set_editor_property('display_name', 'Toxic Berry Residue (Test)')
toxic.set_editor_property('description', 'Spoiled berry crafting resource. Inedible; toxic recipes are not implemented.')
toxic.set_editor_property('category', unreal.EWItemCategory.RESOURCE)
toxic.set_editor_property('food_kind', unreal.EWFoodKind.NONE)
toxic.set_editor_property('food_consumption_enabled', False)
toxic.set_editor_property('max_stack_size', berry.get_editor_property('max_stack_size'))
toxic.set_editor_property('unit_weight', berry.get_editor_property('unit_weight'))
berry.set_editor_property('display_name', 'Azren Berry (Test)')
berry.set_editor_property('description', 'Restores 1/16 hunger and 5% maximum health. Fresh for 20 real minutes, then becomes inedible toxic residue. Eating uses the oldest fresh batch first.')
berry.set_editor_property('category', unreal.EWItemCategory.CONSUMABLE)
berry.set_editor_property('food_kind', unreal.EWFoodKind.BERRY)
berry.set_editor_property('food_consumption_enabled', True)
berry.set_editor_property('hunger_restore_fraction', 1 / 16)
berry.set_editor_property('health_restore_fraction', .05)
berry.set_editor_property('fresh_lifetime_seconds', 1200)
berry.set_editor_property('spoiled_item_definition', toxic)
assert unreal.EditorAssetLibrary.save_loaded_asset(toxic)
assert unreal.EditorAssetLibrary.save_loaded_asset(berry)
unreal.log('Azren fixture configured; original package/ID retained, toxic resource saved, no normal-start inventory.')
