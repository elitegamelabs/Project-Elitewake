"""Recipes the constellation skill tree unlocks (owner, October 22): Hatchet, Inn Torch and Metal Pickaxe. Costs are working values; each recipe is created once and
then left alone (the skill tree, Source/EW/EWSkillTree.cpp, names them). Run in the editor outside Play:
    UnrealEditor-Cmd.exe EW.uproject -ExecutePythonScript=<this file>"""
import unreal

ITEMS = '/Game/Elitewake/Items/Testing/DA_Test'
FOLDER = '/Game/Elitewake/Crafting/Testing'
RECIPES = {
    'Hatchet': ('Hatchet', [('Wood', 15), ('Stone', 10)]),
    'InnTorch': ('InnTorch', [('Sticks', 5), ('Thatch', 5)]),
    'MetalPickaxe': ('MetalPickaxe', [('Wood', 10), ('Ore', 15)]),
}
made = []
for name, (output_name, costs) in RECIPES.items():
    path = f'{FOLDER}/DA_Recipe{name}'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        continue
    output = unreal.load_asset(ITEMS + output_name)
    assert output, output_name
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', unreal.EWCraftingRecipe)
    recipe = unreal.AssetToolsHelpers.get_asset_tools().create_asset(f'DA_Recipe{name}', FOLDER, unreal.EWCraftingRecipe, factory)
    assert recipe, name
    ingredients = []
    for item_name, quantity in costs:
        item = unreal.load_asset(ITEMS + item_name)
        assert item, item_name
        ingredient = unreal.EWCraftingIngredient()
        ingredient.set_editor_property('item', item)
        ingredient.set_editor_property('quantity', quantity)
        ingredients.append(ingredient)
    recipe.set_editor_property('ingredients', ingredients)
    recipe.set_editor_property('output', output)
    recipe.set_editor_property('craft_seconds', 4.0)
    assert unreal.EditorAssetLibrary.save_loaded_asset(recipe)
    made.append(name)
unreal.log(f'Skill recipes created: {made}')
unreal.SystemLibrary.quit_editor()
