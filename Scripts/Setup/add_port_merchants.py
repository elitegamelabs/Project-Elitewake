"""Port general merchants and placeholder sell values (design reference, Economy; Milestones "Port general merchant").
Sets SellValueCopper on the pack resources (every number is TUNING, TBD owner) and places one AEWMerchant on each Port's plaza.
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


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    for path, value in SELL.items():
        item = unreal.load_asset(f'{ITEMS}/{path}')
        assert item, path
        item.set_editor_property('sell_value_copper', value)
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWMerchant):
            actors.destroy_actor(actor)
    placed = {}
    for region, port in W.PORTS.items():
        x, y = port.world(400, 250)
        yaw = math.degrees(port.facing) + 180
        merchant = actors.spawn_actor_from_class(unreal.EWMerchant, unreal.Vector(x, y, T.PORT_LEVEL + 4), unreal.Rotator(0, 0, yaw))
        merchant.set_actor_label(f'Port Merchant {region}')
        merchant.set_folder_path('World/Ports')
        placed[region] = [round(x), round(y)]
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'PortMerchantsResult.json').write_text(json.dumps({'success': True, 'merchants': placed}, indent=2))
    unreal.log(f'Port merchants: {placed}')


if __name__ == '__main__':
    main()
