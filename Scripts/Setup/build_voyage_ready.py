"""Make the first voyage ready (CLAUDE.md Phase 1, slice 6, minutes 25-30). Safe to run again.
Run in the editor outside Play, after build_saltreach_welcome.py:
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -run=pythonscript -script=<this file>

Owner, November 1: the first boat is bought, the raft, at a price the first session reaches; the sloop moored at the east dock
stays where she is but is the shipyard's, for sale, and no longer claims herself for whoever takes her helm.
  - Prices (tuning; build_freeport.py writes the same): the raft 60 Copper (was 180) and an empty waterskin from Marta Vell 15 (was 40).
    A first session's haul (about 10 wood and 3 raw meat, 35 Copper) and one tavern job (20 wood, 70) buy both.
  - Patching (UEWItemDefinition::PatchValue, what a voyage's hold counts as repair materials): Wood 1, a Repair Kit 20.
  - The placed sloop: AEWShip::bHeldByYard.
  - Saltreach's well gives fresh water (an AEWWaterSource over its mouth), to drink and to fill a waterskin, so a voyage can be
    watered in port.
The steps a survivor is shown (buy a boat, load her hold, sail to the Swamp island) are code (UEWArrivalComponent).
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from build_coastal_flora import MAP  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

ITEMS = '/Game/Elitewake/Items'
FOLDER = 'World/Freeport'
WELL = (-600.0, -900.0)          # Saltreach's well in the town's own frame (build_freeport.py), its rim 80 cm above the street
WELL_MOUTH = 75.0                # cm, the inner radius of its stones
TOWN = T.PORT_LEVEL + 5
RAFT_PRICE, WATERSKIN_PRICE = 60, 15
PATCH = {'Testing/DA_TestWood': 1, 'Testing/DA_TestRepairKit': 20}
LABEL = 'Saltreach Freeport: well water'


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    report = {'patch': {}, 'removed': []}
    for path, value in PATCH.items():
        item = unreal.load_asset(f'{ITEMS}/{path}')
        item.set_editor_property('patch_value', value)
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
        report['patch'][path] = value

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    raft = unreal.load_asset('/Game/Elitewake/Ships/DA_Ship_Raft')
    waterskin = unreal.load_asset(f'{ITEMS}/Testing/DA_TestHideWaterFlask')
    held = []
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label() == LABEL:
            report['removed'].append(LABEL)
            actors.destroy_actor(actor)
        elif isinstance(actor, unreal.EWShip):
            actor.set_editor_property('held_by_yard', True)
            held.append(actor.get_actor_label())
        elif isinstance(actor, unreal.EWShipwright):
            sales = list(actor.get_editor_property('ships_for_sale'))
            for sale in sales:
                if sale.get_editor_property('definition') == raft:
                    sale.set_editor_property('price_copper', RAFT_PRICE)
            actor.set_editor_property('ships_for_sale', sales)
            report['raft_price'] = RAFT_PRICE
        elif isinstance(actor, unreal.EWMerchant) and str(actor.get_editor_property('npc_name')) == 'Marta Vell':
            goods = list(actor.get_editor_property('goods'))
            for line in goods:
                if line.get_editor_property('item') == waterskin:
                    line.set_editor_property('price_copper', WATERSKIN_PRICE)
            actor.set_editor_property('goods', goods)
            report['waterskin_price'] = WATERSKIN_PRICE
    report['held_by_yard'] = held
    assert held, 'no placed ship found'
    assert 'raft_price' in report and 'waterskin_price' in report, report

    port = W.PORTS['Plains']
    x, y = port.world(*WELL)
    water = actors.spawn_actor_from_class(unreal.EWWaterSource, unreal.Vector(x, y, TOWN + 78))
    water.set_actor_scale3d(unreal.Vector(WELL_MOUTH / 50, WELL_MOUTH / 50, 1))   # the box is 100 cm square at scale 1
    water.set_actor_label(LABEL)
    water.set_folder_path(FOLDER)
    report['well'] = [round(x), round(y), round(TOWN + 78)]

    assert world_map.save_map()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'VoyageReadyResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Voyage readiness built: {report}')


if __name__ == '__main__':
    main()
