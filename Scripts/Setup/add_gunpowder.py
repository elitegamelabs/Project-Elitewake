"""Gunpowder backs the cannon's powder step (CLAUDE.md 7.4; November 7). Safe to run again; no world rebuild. Run in the editor,
outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"
EW_QUIT_WHEN_DONE=1 closes the editor at the end.

  - DA_Gunpowder (Items/Ships): a charge of black powder, stacking to 50; a Port's resource trader pays 8 Copper.
  - DA_RecipeGunpowder (Crafting/Testing): 1 Sulfur Ore (Desert's Sulfur Flats) and 1 Coal (Winter) make 1 Gunpowder, 4 s,
    no fire. Every new survivor knows it (UEWArrivalComponent's first recipes).
  - The cannon fitting (DA_TestCannon) loads one Gunpowder with each round shot (UEWItemDefinition::CannonPowder).
  - Every merchant who sells round shot also sells powder: 5 charges for 40 Copper, 6 bundles held (added only if missing).
All numbers are tuning. Writes Saved/GunpowderResult.json.
"""
import json
import os
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_map  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
ITEMS = '/Game/Elitewake/Items'
RECIPES = '/Game/Elitewake/Crafting/Testing'


def data_asset(folder, name, cls):
    asset = unreal.load_asset(f'{folder}/{name}')
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', cls)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    return asset


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    shot = unreal.load_asset(f'{ITEMS}/Testing/DA_TestRoundShot')
    powder = data_asset(f'{ITEMS}/Ships', 'DA_Gunpowder', unreal.EWItemDefinition)
    for k, v in {'item_id': 'Gunpowder', 'display_name': 'Gunpowder',
                 'description': 'A charge of black powder: one for every round shot a cannon fires. Mixed from sulfur ore and coal.',
                 'category': unreal.EWItemCategory.RESOURCE, 'max_stack_size': 50, 'unit_weight': .3, 'sell_value_copper': 8,
                 'icon': shot.get_editor_property('icon')}.items():
        powder.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(powder)

    recipe = data_asset(RECIPES, 'DA_RecipeGunpowder', unreal.EWCraftingRecipe)
    parts = []
    for path, quantity in ((f'{ITEMS}/Resources/DA_SulfurOre', 1), (f'{ITEMS}/Resources/DA_Coal', 1)):
        part = unreal.EWCraftingIngredient()
        item = unreal.load_asset(path)
        assert item, path
        part.set_editor_property('item', item)
        part.set_editor_property('quantity', quantity)
        parts.append(part)
    recipe.set_editor_property('ingredients', parts)
    recipe.set_editor_property('output', powder)
    recipe.set_editor_property('craft_seconds', 4.0)
    assert unreal.EditorAssetLibrary.save_loaded_asset(recipe)

    cannon = unreal.load_asset(f'{ITEMS}/Testing/DA_TestCannon')
    cannon.set_editor_property('cannon_powder', powder)
    assert unreal.EditorAssetLibrary.save_loaded_asset(cannon)

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    stocked = []
    for merchant in actors.get_all_level_actors():
        if not isinstance(merchant, unreal.EWMerchant):
            continue
        goods = list(merchant.get_editor_property('goods'))
        items = [g.get_editor_property('item') for g in goods]
        if shot not in items or powder in items:
            continue
        line = unreal.EWMerchantGoods()
        line.set_editor_property('item', powder)
        line.set_editor_property('bundle', 5)
        line.set_editor_property('price_copper', 40)
        line.set_editor_property('max_stock', 6)
        goods.insert(items.index(shot) + 1, line)
        merchant.set_editor_property('goods', goods)
        stocked.append(merchant.get_actor_label())
    assert world_map.save_map()
    report = {'success': True, 'merchants_stocked': stocked, 'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    Path(unreal.Paths.project_saved_dir(), 'GunpowderResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWGUNPOWDER done: {len(stocked)} merchants now sell powder')


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
