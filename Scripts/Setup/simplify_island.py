"""Simplify the playable island to its core (owner, October 14). Safe to run again.
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

The owner asked for a clean island to make the core survival actions work on: the island, its trees, the water
around it and the dock stay; the boats go (the owner then kept the fish). Nothing is deleted:
  - the map as it was is kept, once, as /Game/Elitewake/Maps/Test/Lvl_ShipsTest, where the ships, cannons and
    sea creatures (and their checks) carry on;
  - the island map loses its ships (its sea creatures stay, owner's correction; the owner brought the sloop back on
    October 15: run restore_sloop.py after this);
  - the starter supplies become the four core tools: Hatchet, Pickaxe, Waterskin and Torch;
  - the core items lose their "(Test)" labels and take the names the owner uses.
"""
import json
from pathlib import Path
import unreal

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
TEST_MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'
ITEMS = '/Game/Elitewake/Items/Testing'
TOOLS = ['WoodenAxe', 'WoodenPickaxe', 'HideWaterFlask', 'InnTorch']
NAMES = {'WoodenAxe': 'Hatchet', 'WoodenPickaxe': 'Pickaxe', 'HideWaterFlask': 'Waterskin', 'InnTorch': 'Torch',
         'Wood': 'Wood', 'Stone': 'Stone', 'Thatch': 'Thatch', 'Fiber': 'Fiber', 'Sticks': 'Sticks', 'AzulBerry': 'Azren Berry'}


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    library = unreal.EditorAssetLibrary
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    report = {}
    # Keep the full map for the ship and sea work before anything leaves the island.
    if not library.does_asset_exist(TEST_MAP):
        assert library.duplicate_asset(MAP, TEST_MAP), 'could not keep the ships test map'
        report['kept_test_map'] = TEST_MAP
    assert level.load_level(MAP)
    removed = []
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWShip):
            removed.append(actor.get_actor_label())
            actors.destroy_actor(actor)
    report['removed'] = removed
    kit = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWStarterKit)), None)
    assert kit, 'no starter kit on the island'
    entries = []
    for name in TOOLS:
        entry = unreal.EWStarterKitItem()
        entry.set_editor_property('item', unreal.load_asset(f'{ITEMS}/DA_Test{name}'))
        entry.set_editor_property('quantity', 1)
        entries.append(entry)
    kit.set_editor_property('items', entries)
    kit.set_editor_property('ship_cargo', [])
    kit.set_actor_label('Starter supplies')
    report['starter_supplies'] = [NAMES[n] for n in TOOLS]
    assert level.save_current_level()
    for name, display in NAMES.items():
        item = unreal.load_asset(f'{ITEMS}/DA_Test{name}')
        assert item, name
        item.set_editor_property('display_name', display)
        assert library.save_loaded_asset(item, False)
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'SimplifyIslandResult.json').write_text(json.dumps(report, indent=2))
    unreal.log('Island simplified')


if __name__ == '__main__':
    main()
