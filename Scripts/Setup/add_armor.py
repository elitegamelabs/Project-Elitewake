"""The three armor sets (owner, November 8: cloth, fur and metal; a helmet, a chest piece with gloves and pants with
footwear each). Safe to run again; no world rebuild, the map is not touched. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"
EW_QUIT_WHEN_DONE=1 closes the editor at the end.

Materials (Items/Resources):
  DA_Cloth    woven from fiber: 3 Fiber make 1 Cloth, 3 s, by hand.
  DA_Leather  tanned from hide: 2 Hide and 1 Fiber make 1 Leather, 6 s, at a lit fire (smoke-curing).
  DA_Fur      a fur pelt, from furred animals: wolf, bear, polar bear, fox, hare, caribou, seal, mountain goat, otter,
              jackal, lion and jaguar give Fur; boar, deer, wild horse, gazelle, oryx, tapir, elephant, walrus and the
              crocodilians give Hide; birds, snakes, frogs, spiders, scorpions, monkeys, tortoises and turtles give none.

The nine pieces (Items/Armor), each slot's share of the set: helmet 20%, chest 45%, pants 35%.
  Full set        damage stopped   overheating   cold (insulation)   weight helmet/chest/pants (kg)
  Cloth           10%              1.10x         none                0.5 / 1.5 / 1.2
  Fur              8%              1.30x         1.0 (Winter cold)   1.5 / 4.0 / 3.5
  Metal           40%              1.50x         none                3.0 / 9.0 / 7.0
Recipes (Crafting/Testing; scaled to what fiber, hide and ore actually yield; tuning):
  Cloth Head Wrap 4 Cloth + 2 Fiber     Cloth Chest Piece 10 Cloth + 4 Fiber     Cloth Pants 8 Cloth + 4 Fiber
  Fur Hood 3 Fur + 2 Leather + 2 Fiber  Fur Jacket 8 Fur + 4 Leather + 4 Fiber   Fur Pants 6 Fur + 3 Leather + 3 Fiber
  Metal Tricorn Helmet 6 Iron Ingot + 2 Leather + 2 Cloth (fire)
  Metal Cuirass 14 Iron Ingot + 4 Leather + 5 Cloth (fire)    Metal Pants 10 Iron Ingot + 4 Leather + 4 Cloth (fire)
New survivors know cloth, leather, cloth and fur armor (UEWArrivalComponent); Metalwork unlocks the metal pieces.
Icons: Art/UI/Icons/Armor (Scripts/Art/make_armor_icons.py, cut from the owner's concept sheets). Writes Saved/ArmorResult.json.
"""
import json
import os
import time
from pathlib import Path
import unreal

ITEMS = '/Game/Elitewake/Items'
RECIPES = '/Game/Elitewake/Crafting/Testing'
ICONS = '/Game/Elitewake/UI/Icons/Armor'
ANIMALS = '/Game/Elitewake/Wildlife/Animals'
ROOT = Path(unreal.Paths.project_dir())

FUR = {'Wolf': (1, 3), 'Bear': (3, 5), 'PolarBear': (3, 6), 'Fox': (1, 2), 'Hare': (1, 1), 'Caribou': (2, 4), 'Seal': (2, 3),
       'MountainGoat': (1, 3), 'Otter': (1, 2), 'Jackal': (1, 2), 'Lion': (2, 4), 'Jaguar': (2, 3)}
HIDE = {'Boar': (1, 3), 'Deer': (2, 3), 'WildHorse': (2, 4), 'Gazelle': (1, 2), 'Oryx': (2, 3), 'Tapir': (2, 3), 'Elephant': (4, 6),
        'Walrus': (3, 5), 'Alligator': (2, 4), 'Crocodile': (2, 4), 'GiantCrocodile': (4, 6)}

# (asset, name, slot, kind, insulation, damage stopped, overheating added, weight, sell value, description, recipe, fire)
SLOT = {'Head': unreal.EWEquipmentSlot.HEAD, 'Chest': unreal.EWEquipmentSlot.CHEST, 'Legs': unreal.EWEquipmentSlot.LEGS}
KIND = {'Cloth': unreal.EWArmorKind.CLOTH, 'Fur': unreal.EWArmorKind.FUR, 'Metal': unreal.EWArmorKind.METAL}
SHARE = {'Head': .20, 'Chest': .45, 'Legs': .35}
SET = {'Cloth': (.10, .10, 0.0), 'Fur': (.08, .30, 1.0), 'Metal': (.40, .50, 0.0)}   # damage, overheating, insulation
PIECES = [
    ('ClothHeadWrap', 'Cloth Head Wrap', 'Head', 'Cloth', .5, 8,
     'Layered linen bandages wound over the head, face and neck, a slit left for the eyes. Light, cheap, and little use against a blade.',
     [('Resources/DA_Cloth', 4), ('Testing/DA_TestFiber', 2)], False),
    ('ClothChest', 'Cloth Chest Piece', 'Chest', 'Cloth', 1.5, 20,
     'A rough linen tunic with the arms and hands bound in cloth: shirt, sleeves and gloves in one.',
     [('Resources/DA_Cloth', 10), ('Testing/DA_TestFiber', 4)], False),
    ('ClothPants', 'Cloth Pants', 'Legs', 'Cloth', 1.2, 16,
     'Loose linen trousers wrapped from knee to ankle, with wrapped cloth shoes.',
     [('Resources/DA_Cloth', 8), ('Testing/DA_TestFiber', 4)], False),
    ('FurHood', 'Fur Hood', 'Head', 'Fur', 1.5, 20,
     'A whole pelt worn as a hood, its head and ears above the brow, fur falling over the face, neck and shoulders. Warm in the north, stifling in the south.',
     [('Resources/DA_Fur', 3), ('Resources/DA_Leather', 2), ('Testing/DA_TestFiber', 2)], False),
    ('FurJacket', 'Fur Jacket', 'Chest', 'Fur', 4.0, 60,
     'A heavy coat of pelts over hide, belted and strapped, with fur-lined leather gloves.',
     [('Resources/DA_Fur', 8), ('Resources/DA_Leather', 4), ('Testing/DA_TestFiber', 4)], False),
    ('FurPants', 'Fur Pants', 'Legs', 'Fur', 3.5, 50,
     'Hide trousers lined with fur, laced at the shins, and thick fur boots.',
     [('Resources/DA_Fur', 6), ('Resources/DA_Leather', 3), ('Testing/DA_TestFiber', 3)], False),
    ('MetalTricornHelmet', 'Metal Tricorn Helmet', 'Head', 'Metal', 3.0, 90,
     'A steel helmet under a tricorn brim edged in brass, its face closed by a pierced steel plate, the neck guarded, padded with leather.',
     [('Resources/DA_IronIngot', 6), ('Resources/DA_Leather', 2), ('Resources/DA_Cloth', 2)], True),
    ('MetalCuirass', 'Metal Cuirass', 'Chest', 'Metal', 9.0, 260,
     'A steel breast- and backplate strapped over a navy sea coat, with shoulder plates, forearm guards and gauntlets.',
     [('Resources/DA_IronIngot', 14), ('Resources/DA_Leather', 4), ('Resources/DA_Cloth', 5)], True),
    ('MetalPants', 'Metal Pants', 'Legs', 'Metal', 7.0, 190,
     'Navy breeches with steel at the knee and shin, a leather belt, and tall boots with steel-capped toes.',
     [('Resources/DA_IronIngot', 10), ('Resources/DA_Leather', 4), ('Resources/DA_Cloth', 4)], True),
]


def data_asset(folder, name, cls):
    asset = unreal.load_asset(f'{folder}/{name}')
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', cls)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    return asset


def import_icons():
    tasks = []
    for png in sorted((ROOT / 'Art' / 'UI' / 'Icons' / 'Armor').glob('T_Icon_*.png')):
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', str(png))
        task.set_editor_property('destination_path', ICONS)
        task.set_editor_property('replace_existing', True)
        task.set_editor_property('automated', True)
        task.set_editor_property('save', True)
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    return len(tasks)


def icon(piece):
    return unreal.load_asset(f'{ICONS}/T_Icon_{piece}')


def item(name, values):
    folder, asset = name.rsplit('/', 1)
    it = data_asset(f'{ITEMS}/{folder}', asset, unreal.EWItemDefinition)
    for k, v in values.items():
        it.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(it), name
    return it


def recipe(name, output, parts, seconds, fire):
    r = data_asset(RECIPES, f'DA_Recipe{name}', unreal.EWCraftingRecipe)
    ingredients = []
    for path, quantity in parts:
        part = unreal.EWCraftingIngredient()
        thing = unreal.load_asset(f'{ITEMS}/{path}')
        assert thing, path
        part.set_editor_property('item', thing)
        part.set_editor_property('quantity', quantity)
        ingredients.append(part)
    r.set_editor_property('ingredients', ingredients)
    r.set_editor_property('output', output)
    r.set_editor_property('craft_seconds', seconds)
    r.set_editor_property('needs_fire', fire)
    assert unreal.EditorAssetLibrary.save_loaded_asset(r), name
    return r


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    icons = import_icons()
    fiber = unreal.load_asset(f'{ITEMS}/Testing/DA_TestFiber')
    hide = unreal.load_asset(f'{ITEMS}/Testing/DA_TestHide')
    resource = unreal.EWItemCategory.RESOURCE
    cloth = item('Resources/DA_Cloth', {'item_id': 'Cloth', 'display_name': 'Cloth', 'category': resource, 'max_stack_size': 50,
                                        'unit_weight': .1, 'sell_value_copper': 2, 'icon': fiber.get_editor_property('icon'),
                                        'description': 'Coarse linen woven from plant fiber, for wraps, tunics and padding under armor.'})
    leather = item('Resources/DA_Leather', {'item_id': 'Leather', 'display_name': 'Leather', 'category': resource, 'max_stack_size': 50,
                                            'unit_weight': .4, 'sell_value_copper': 6, 'icon': hide.get_editor_property('icon'),
                                            'description': 'Hide cured over a fire: straps, gloves, belts and boots.'})
    fur = item('Resources/DA_Fur', {'item_id': 'Fur', 'display_name': 'Fur', 'category': resource, 'max_stack_size': 30,
                                    'unit_weight': .5, 'sell_value_copper': 8, 'icon': icon('FurHood') or hide.get_editor_property('icon'),
                                    'description': 'A furred pelt from a hunted animal. The warmest thing a survivor can wear.'})
    recipe('Cloth', cloth, [('Testing/DA_TestFiber', 3)], 3.0, False)
    recipe('Leather', leather, [('Testing/DA_TestHide', 2), ('Testing/DA_TestFiber', 1)], 6.0, True)
    made = []
    for asset, name, slot, kind, weight, value, text, parts, fire in PIECES:
        damage, heat, warmth = SET[kind]
        share = SHARE[slot]
        piece = item(f'Armor/DA_{asset}', {
            'item_id': asset, 'display_name': name, 'description': text, 'category': unreal.EWItemCategory.CLOTHING,
            'max_stack_size': 1, 'unit_weight': weight, 'sell_value_copper': value, 'equipment_slot': SLOT[slot],
            'armor_kind': KIND[kind], 'armor_reduction': round(damage * share, 4), 'overheat_penalty': round((heat) * share, 4),
            'insulation': round(warmth * share, 4), 'icon': icon(asset)})
        recipe(asset, piece, parts, 12.0 if kind == 'Metal' else 8.0, fire)
        made.append(asset)
    # Pelts from the animals that have them.
    pelts = {}
    for species, (low, high) in list(FUR.items()) + list(HIDE.items()):
        animal = unreal.load_asset(f'{ANIMALS}/DA_Animal_{species}')
        if not animal:
            continue
        animal.set_editor_property('pelt', fur if species in FUR else hide)
        animal.set_editor_property('pelt_min', low)
        animal.set_editor_property('pelt_max', high)
        assert unreal.EditorAssetLibrary.save_loaded_asset(animal), species
        pelts[species] = 'Fur' if species in FUR else 'Hide'
    report = {'success': True, 'icons': icons, 'pieces': made, 'pelts': pelts, 'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    Path(unreal.Paths.project_saved_dir(), 'ArmorResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWARMOR done: {len(made)} pieces, {len(pelts)} animals with pelts')


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
