"""Food items and cooking recipes from the owner's October 22 decisions (Docs/OwnerDecisions/GAMEPLAY_DESIGN_DECISIONS_2026-10-22.md, section 2):
hunger and health per food, the sickness chance of raw fish (15%) and raw meat (25%), cooking at 6 and 8 seconds (the owner's range is 5 to 12), and a medicinal
herb that cures food sickness. Safe to run again. Run in the editor outside Play:
    UnrealEditor-Cmd.exe EW.uproject -ExecutePythonScript=<this file>"""
import unreal

FOLDER = '/Game/Elitewake/Items/Food'
RECIPES = '/Game/Elitewake/Crafting/Testing'
cls = unreal.load_class(None, '/Script/EW.EWItemDefinition')
tools = unreal.AssetToolsHelpers.get_asset_tools()


def data_asset(folder, name, asset_class, factory_class=unreal.DataAssetFactory):
    path = f'{folder}/{name}'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    factory = factory_class()
    factory.set_editor_property('data_asset_class', asset_class)
    return tools.create_asset(name, folder, asset_class, factory)


def food(name, item_id, label, text, kind, hunger_points, health_points, sickness=0.0, cures=False, weight=.4, stack=50):
    item = data_asset(FOLDER, name, cls)
    assert item, name
    item.set_editor_property('item_id', item_id)
    item.set_editor_property('display_name', label)
    item.set_editor_property('description', text)
    item.set_editor_property('category', unreal.EWItemCategory.CONSUMABLE)
    item.set_editor_property('food_kind', kind)
    item.set_editor_property('food_consumption_enabled', True)
    item.set_editor_property('hunger_restore_fraction', hunger_points / 100.0)
    item.set_editor_property('health_restore_fraction', health_points / 100.0)
    item.set_editor_property('sickness_chance', sickness)
    item.set_editor_property('cures_food_sickness', cures)
    item.set_editor_property('fresh_lifetime_seconds', 0.0)
    if item.get_editor_property('max_stack_size') < 2:
        item.set_editor_property('max_stack_size', stack)
    if item.get_editor_property('unit_weight') <= 0:
        item.set_editor_property('unit_weight', weight)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item), name
    return item


K = unreal.EWFoodKind
raw_fish = food('DA_RawFish', 'Food.RawFish', 'Raw Fish', 'Eaten raw it restores 8 hunger, but one fish in seven makes you sick for three minutes. Cook it at a fire.', K.RAW_FISH, 8, 0, .15)
raw_meat = food('DA_RawMeat', 'Food.RawMeat', 'Raw Meat', 'Restores 12 hunger and costs 3 health; one piece in four brings food sickness. Cook it at a fire.', K.RAW_MEAT, 12, -3, .25)
cooked_fish = food('DA_CookedFish', 'Food.CookedFish', 'Cooked Fish', 'Restores 20 hunger and 3 health.', K.COOKED_FISH, 20, 3)
cooked_meat = food('DA_CookedMeat', 'Food.CookedMeat', 'Cooked Meat', 'Restores 30 hunger and 5 health.', K.COOKED_MEAT, 30, 5)
berry_dish = food('DA_CookedBerryDish', 'Food.CookedBerryDish', 'Cooked Berry Dish', 'Restores 15 hunger and 2 health.', K.BERRY_DISH, 15, 2)
herb = food('DA_MedicinalHerb', 'Food.MedicinalHerb', 'Medicinal Herb', 'Chewed, it ends food sickness at once.', K.REMEDY, 0, 0, 0.0, True, .05, 100)


def recipe(name, raw, cooked, seconds):
    asset = data_asset(RECIPES, name, unreal.EWCraftingRecipe)
    ingredient = unreal.EWCraftingIngredient()
    ingredient.set_editor_property('item', raw)
    ingredient.set_editor_property('quantity', 1)
    asset.set_editor_property('ingredients', [ingredient])
    asset.set_editor_property('output', cooked)
    asset.set_editor_property('craft_seconds', seconds)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset), name


recipe('DA_RecipeCookedFish', raw_fish, cooked_fish, 6.0)
recipe('DA_RecipeCookedMeat', raw_meat, cooked_meat, 8.0)
unreal.log('Food items and cooking recipes written')
unreal.SystemLibrary.quit_editor()
