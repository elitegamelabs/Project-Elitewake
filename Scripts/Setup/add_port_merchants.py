"""Port general merchants (with goods to buy), crew masters and placeholder sell values (design reference, Economy; Milestones "Port general merchant",
"Sail control and crew dependency"). Sets SellValueCopper on the pack resources (every number is TUNING, TBD owner), makes the
Sailhand's Articles item, and places one AEWMerchant and one AEWCrewMaster on each Port's plaza.
Safe to run again. Run in the editor outside Play:
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -nullrhi -run=pythonscript -script=<this file>"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
ITEMS = '/Game/Elitewake/Items'
SELL = {  # placeholder prices in Copper per unit (500 Copper = 1 Silver)
    'Testing/DA_TestWood': 2, 'Testing/DA_TestStone': 2, 'Testing/DA_TestThatch': 1, 'Testing/DA_TestFiber': 1,
    'Testing/DA_TestSticks': 1, 'Testing/DA_TestHide': 8, 'Testing/DA_TestOre': 12, 'Testing/DA_TestAzulBerry': 2,
    'Resources/DA_Coal': 6, 'Resources/DA_Ruby': 60, 'Resources/DA_Sapphire': 60, 'Resources/DA_Emerald': 60, 'Resources/DA_Obsidian': 30,
    'Food/DA_RawMeat': 5, 'Food/DA_RawFish': 4, 'Food/DA_CookedMeat': 8, 'Food/DA_CookedFish': 7, 'Food/DA_MedicinalHerb': 10,
}
GOODS = [  # what every Port merchant stocks: (item, units per purchase, Copper per purchase, purchases held); all TUNING, TBD owner
    ('Testing/DA_TestRoundShot', 5, 50, 6),
    ('Testing/DA_TestRepairKit', 1, 60, 4),
    ('Food/DA_CookedFish', 1, 15, 8),
    ('Food/DA_MedicinalHerb', 1, 25, 5),
    ('Testing/DA_TestHideWaterFlask', 1, 40, 3),
]


def goods(path, bundle, price, stock):
    line = unreal.EWMerchantGoods()
    item = unreal.load_asset(f'{ITEMS}/{path}')
    assert item, path
    line.set_editor_property('item', item)
    line.set_editor_property('bundle', bundle)
    line.set_editor_property('price_copper', price)
    line.set_editor_property('max_stock', stock)
    return line


def make_articles(name, flag, text):
    path = f'/Game/Elitewake/Items/Crew/DA_{name}Articles'
    item = unreal.load_asset(path)
    if not item:
        item = unreal.AssetToolsHelpers.get_asset_tools().create_asset(f'DA_{name}Articles', '/Game/Elitewake/Items/Crew',
                                                                      unreal.EWItemDefinition, unreal.DataAssetFactory())
    kit = unreal.load_asset(f'{ITEMS}/Testing/DA_TestRepairKit')
    item.set_editor_property('item_id', f'{name}Articles')
    item.set_editor_property('display_name', unreal.Text(f'{name} Articles'))
    item.set_editor_property('description', unreal.Text(text))
    item.set_editor_property('max_stack_size', 10)
    item.set_editor_property('unit_weight', 0.05)
    item.set_editor_property(flag, True)
    item.set_editor_property('icon', kit.get_editor_property('icon'))
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    return item


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    articles = make_articles('Sailhand', 'signs_on_sailhand', 'Signed articles for one hired sailhand. Use them at a sail lines aboard (the pin rail by the mast) and the hand works that sail on the helm orders.')
    gunner_articles = make_articles('Gunner', 'signs_on_gunner', 'Signed articles for one hired gunner. Use them at an installed cannon aboard: the gunner loads it from the hold and fires with your shots when it bears.')
    for path, value in SELL.items():
        item = unreal.load_asset(f'{ITEMS}/{path}')
        assert item, path
        item.set_editor_property('sell_value_copper', value)
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWMerchant) and str(actor.get_folder_path()) == 'World/Ports':
            actors.destroy_actor(actor)
    placed = {}
    for region, port in W.PORTS.items():
        if region == 'Plains':
            continue   # Saltreach Freeport has its own named traders and recruiter (owner, October 30; build_freeport.py)
        x, y = port.world(400, 250)
        yaw = math.degrees(port.facing) + 180
        merchant = actors.spawn_actor_from_class(unreal.EWMerchant, unreal.Vector(x, y, T.PORT_LEVEL + 4), unreal.Rotator(0, 0, yaw))
        merchant.set_actor_label(f'Port Merchant {region}')
        merchant.set_folder_path('World/Ports')
        merchant.set_editor_property('goods', [goods(path, bundle, price, stock) for path, bundle, price, stock in GOODS])
        merchant.set_editor_property('restock_seconds', 300.0)   # tuning
        cx, cy = port.world(400, -250)
        crew = actors.spawn_actor_from_class(unreal.EWCrewMaster, unreal.Vector(cx, cy, T.PORT_LEVEL + 4), unreal.Rotator(0, 0, yaw))
        crew.set_actor_label(f'Port Crew Master {region}')
        crew.set_folder_path('World/Ports')
        crew.set_editor_property('articles', articles)
        gx, gy = port.world(400, -500)
        gunnery = actors.spawn_actor_from_class(unreal.EWCrewMaster, unreal.Vector(gx, gy, T.PORT_LEVEL + 4), unreal.Rotator(0, 0, yaw))
        gunnery.set_actor_label(f'Port Gunnery Master {region}')
        gunnery.set_folder_path('World/Ports')
        gunnery.set_editor_property('articles', gunner_articles)
        gunnery.set_editor_property('crew_role', 'gunner')
        gunnery.set_editor_property('hire_cost', 150)   # tuning
        placed[region] = [round(x), round(y), round(cx), round(cy)]
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'PortMerchantsResult.json').write_text(json.dumps({'success': True, 'merchants': placed}, indent=2))
    unreal.log(f'Port merchants: {placed}')


if __name__ == '__main__':
    main()
