"""Opt-in crafting metadata fixtures; costs confirmed, weights are temporary testing values.
No normal-player unlocks/grants, wood substitution or flask use.
Wooden axe/pickaxe fixtures use existing gathering capabilities; no new yield balance.
Run through Unreal Python. Existing recipes and tuning are preserved.
"""
import unreal

folder = '/Game/Elitewake/Items/Testing'
def item(name, label, category, stack=1):
    path = folder + '/DA_Test' + name
    existing = unreal.load_asset(path)
    if existing:
        return existing
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
    value = unreal.AssetToolsHelpers.get_asset_tools().create_asset('DA_Test'+name, folder, unreal.EWItemDefinition, factory)
    assert value
    value.set_editor_property('item_id', 'Test.'+name)
    value.set_editor_property('display_name', label)
    value.set_editor_property('category', category)
    value.set_editor_property('max_stack_size', stack)
    value.set_editor_property('unit_weight', 1.0)
    value.set_editor_property('description', 'Crafting fixture. Temporary 1 kg weight; final balance, item art and use behavior pending.')
    assert unreal.EditorAssetLibrary.save_loaded_asset(value)
    return value

wood = unreal.load_asset(folder+'/DA_TestWood')
thatch = unreal.load_asset(folder+'/DA_TestThatch')
assert wood and thatch
hide = item('Hide', 'Hide (Test)', unreal.EWItemCategory.RESOURCE, 250)
for name, label, costs in [
    ('WoodenShovel', 'Wooden Shovel', [(wood,20)]),
    ('WoodenAxe', 'Wooden Axe', [(wood,20)]),
    ('WoodenPickaxe', 'Wooden Pickaxe', [(wood,20)]),
    ('HideWaterFlask', 'Hide Water Flask', [(hide,1),(thatch,10)])]:
    output = item(name,label,unreal.EWItemCategory.TOOL)
    capability = {'WoodenAxe':unreal.EWGatheringTool.HATCHET,
                  'WoodenPickaxe':unreal.EWGatheringTool.PICKAXE}.get(name)
    if capability is not None:
        output.set_editor_property('equipment_slot',unreal.EWEquipmentSlot.MAIN_HAND)
        output.set_editor_property('gathering_tool',capability)
        assert unreal.EditorAssetLibrary.save_loaded_asset(output)
    recipe_folder = '/Game/Elitewake/Crafting/Testing'
    recipe_name = 'DA_Recipe'+name
    if unreal.EditorAssetLibrary.does_asset_exist(recipe_folder+'/'+recipe_name):
        continue
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class',unreal.EWCraftingRecipe)
    recipe = unreal.AssetToolsHelpers.get_asset_tools().create_asset(recipe_name,recipe_folder,unreal.EWCraftingRecipe,factory)
    assert recipe
    ingredients = []
    for resource, quantity in costs:
        ingredient = unreal.EWCraftingIngredient()
        ingredient.set_editor_property('item',resource)
        ingredient.set_editor_property('quantity',quantity)
        ingredients.append(ingredient)
    recipe.set_editor_property('ingredients',ingredients)
    recipe.set_editor_property('output',output)
    assert unreal.EditorAssetLibrary.save_loaded_asset(recipe)
unreal.log('Crafting fixtures saved; no default unlock or inventory grant.')
