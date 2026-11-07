"""Smelting the islands' ores at a fire (November 7). Safe to run again; no world rebuild; the map is not touched. Run in the
editor, outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"
EW_QUIT_WHEN_DONE=1 closes the editor at the end.

  - DA_IronIngot and DA_CopperIngot (Items/Resources): a Port's resource trader pays 30 and 28 Copper.
  - Recipes (Crafting/Testing), each at a lit fire, 8 s: 2 Iron Ore + 1 Wood make 1 Iron Ingot; 2 Copper Ore + 1 Wood make 1
    Copper Ingot; 3 Bog Iron + 1 Wood make 1 Iron Ingot (poorer ore). The Metalwork skill unlocks them (EWSkillTree.cpp).
  - The Metal Pickaxe is forged from what smelting makes: 10 Wood + 4 Iron Ingots (it was 10 Wood + 15 of the generic test
    ore, which could only be bought), so iron ore leads to the pick that opens sulfur, gems and crystals.
All numbers are tuning. Writes Saved/SmeltingResult.json.
"""
import json
import os
import time
from pathlib import Path
import unreal

ITEMS = '/Game/Elitewake/Items'
RECIPES = '/Game/Elitewake/Crafting/Testing'
INGOTS = {'IronIngot': ('Iron Ingot', 'A bar of smelted iron, for tools, fittings and ship ironwork.', 30),
          'CopperIngot': ('Copper Ingot', 'A bar of smelted copper, for sheathing, fittings and trade.', 28)}
SMELT = {'IronIngot': ('IronIngot', 'Resources/DA_IronOre', 2), 'CopperIngot': ('CopperIngot', 'Resources/DA_CopperOre', 2),
         'IronIngotFromBogIron': ('IronIngot', 'Resources/DA_BogIron', 3)}


def data_asset(folder, name, cls):
    asset = unreal.load_asset(f'{folder}/{name}')
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', cls)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    return asset


def main():
    ingots = {}
    for key, (name, description, price) in INGOTS.items():
        item = data_asset(f'{ITEMS}/Resources', f'DA_{key}', unreal.EWItemDefinition)
        for k, v in {'item_id': key, 'display_name': name, 'description': description, 'category': unreal.EWItemCategory.RESOURCE,
                     'max_stack_size': 50, 'unit_weight': 1.0, 'sell_value_copper': price}.items():
            item.set_editor_property(k, v)
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
        ingots[key] = item
    wood = unreal.load_asset(f'{ITEMS}/Testing/DA_TestWood')
    for key, (ingot, ore_path, count) in SMELT.items():
        recipe = data_asset(RECIPES, f'DA_Recipe{key}', unreal.EWCraftingRecipe)
        parts = []
        for item, quantity in ((unreal.load_asset(f'{ITEMS}/{ore_path}'), count), (wood, 1)):
            assert item, ore_path
            part = unreal.EWCraftingIngredient()
            part.set_editor_property('item', item)
            part.set_editor_property('quantity', quantity)
            parts.append(part)
        recipe.set_editor_property('ingredients', parts)
        recipe.set_editor_property('output', ingots[ingot])
        recipe.set_editor_property('craft_seconds', 8.0)
        recipe.set_editor_property('needs_fire', True)
        assert unreal.EditorAssetLibrary.save_loaded_asset(recipe)
    pick = unreal.load_asset(f'{RECIPES}/DA_RecipeMetalPickaxe')
    assert pick, 'DA_RecipeMetalPickaxe is missing (create_skill_recipes.py)'
    parts = []
    for item, quantity in ((wood, 10), (ingots['IronIngot'], 4)):
        part = unreal.EWCraftingIngredient()
        part.set_editor_property('item', item)
        part.set_editor_property('quantity', quantity)
        parts.append(part)
    pick.set_editor_property('ingredients', parts)
    assert unreal.EditorAssetLibrary.save_loaded_asset(pick)
    report = {'success': True, 'ingots': sorted(INGOTS), 'recipes': sorted(SMELT), 'metal_pickaxe': '10 Wood + 4 Iron Ingot',
              'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    Path(unreal.Paths.project_saved_dir(), 'SmeltingResult.json').write_text(json.dumps(report, indent=2))
    unreal.log('EWSMELTING done')


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
