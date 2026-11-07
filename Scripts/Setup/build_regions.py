"""Lay the climate regions over the world (owner's five regions, October 14-15). Safe to run again.
Run in the editor after build_coastal_terrain.py, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

One AEWClimateRegion per island of world_layout.py, of that island's region: Plains in the centre (the starter
island and the five round it), Winter north, Swamp south, Desert east, Jungle west. Each covers its island and 15 m
of shallows (working value) past its farthest shore; past that is the open sea, except round the Desert's islands,
whose humidity reaches 100 m offshore (owner). Region temperatures and humidity are working values (see
AEWClimateRegion::DefaultClimate and the design reference). The map's world overview reads these actors too.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = 'World/Regions'
SHALLOWS = 1500.0          # cm of shallows each region keeps past its shore (tuning)
DESERT_OFFSHORE = 10000.0  # cm: the desert's humidity reaches 100 m offshore (owner)
KINDS = {'Plains': unreal.EWRegion.PLAINS, 'Winter': unreal.EWRegion.WINTER, 'Swamp': unreal.EWRegion.SWAMP,
         'Desert': unreal.EWRegion.DESERT, 'Jungle': unreal.EWRegion.JUNGLE}


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWClimateRegion):
            actors.destroy_actor(actor)
    placed = []
    for island in W.ISLANDS:
        kind = KINDS[island.region]
        reach = DESERT_OFFSHORE if island.region == 'Desert' else 0.0
        region = actors.spawn_actor_from_class(unreal.EWClimateRegion, unreal.Vector(island.cx, island.cy, 0))
        region.set_actor_label(f'{island.region}: {island.key}')
        region.set_folder_path(FOLDER)
        region.set_editor_property('region', kind)
        # A circle round the island's farthest shore, plus the shallows.
        r = island.reach() + SHALLOWS
        region.set_editor_property('radii', unreal.Vector2D(r, r))
        region.set_editor_property('offshore_reach', reach)
        region.set_editor_property('climate', unreal.EWClimateRegion.default_climate(kind))
        placed.append({'label': f'{island.region}: {island.key}', 'centre_m': [round(island.cx / 100), round(island.cy / 100)], 'reach': reach})
    assert world_map.save_map()
    Path(unreal.Paths.project_saved_dir(), 'RegionsResult.json').write_text(json.dumps({'success': True, 'regions': placed}, indent=2))
    unreal.log(f'Regions: {len(placed)}')


if __name__ == '__main__':
    main()
