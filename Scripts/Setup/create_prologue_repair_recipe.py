"""Save an opt-in Repair Kit recipe fixture: confirmed 20 Wood + 20 Stone.
Run outside PIE through Unreal Python. No production unlock/event or repair use.
The output has a clearly labelled temporary 1 kg test weight and no assigned art.
Existing assets are validated rather than overwritten.
"""
import json
from pathlib import Path
import unreal

assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play before saving fixtures.'
item_folder = '/Game/Elitewake/Items/Testing'
recipe_folder = '/Game/Elitewake/Crafting/Testing'
wood = unreal.load_asset(item_folder + '/DA_TestWood')
stone = unreal.load_asset(item_folder + '/DA_TestStone')
assert wood and stone
output = unreal.load_asset(item_folder + '/DA_TestRepairKit')
if not output:
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
    output = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'DA_TestRepairKit', item_folder, unreal.EWItemDefinition, factory)
    assert output
    output.set_editor_property('item_id', 'Test.RepairKit')
    output.set_editor_property('display_name', 'Repair Kit')
    output.set_editor_property('category', unreal.EWItemCategory.MISCELLANEOUS)
    output.set_editor_property('max_stack_size', 1)
    output.set_editor_property('unit_weight', 1.0)
    output.set_editor_property('description', 'Prologue crafting fixture only. Temporary 1 kg weight; repair use, final category, stack size, art and balance pending.')
    assert unreal.EditorAssetLibrary.save_loaded_asset(output)
recipe = unreal.load_asset(recipe_folder + '/DA_RecipePrologueRepairKit')
if not recipe:
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', unreal.EWCraftingRecipe)
    recipe = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'DA_RecipePrologueRepairKit', recipe_folder, unreal.EWCraftingRecipe, factory)
    assert recipe
    ingredients = []
    for resource in (wood, stone):
        ingredient = unreal.EWCraftingIngredient()
        ingredient.set_editor_property('item', resource)
        ingredient.set_editor_property('quantity', 20)
        ingredients.append(ingredient)
    recipe.set_editor_property('ingredients', ingredients)
    recipe.set_editor_property('output', output)
    assert unreal.EditorAssetLibrary.save_loaded_asset(recipe)
costs = recipe.get_editor_property('ingredients')
assert recipe.get_editor_property('output') == output
assert [(c.get_editor_property('item'), c.get_editor_property('quantity')) for c in costs] == [(wood, 20), (stone, 20)]
Path(unreal.Paths.project_saved_dir(), 'PrologueRepairRecipeAssets.json').write_text(json.dumps({
    'success': True, 'recipe': recipe.get_path_name(), 'output': output.get_path_name(),
    'costs': {'Wood': 20, 'Stone': 20}, 'scope': 'Saved testing assets only; no normal grants, prologue events or repair behavior'
}, indent=2), encoding='utf-8')
unreal.log('Repair Kit test recipe saved and validated; no normal unlock or item grant.')
