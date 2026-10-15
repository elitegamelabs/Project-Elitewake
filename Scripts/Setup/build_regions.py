"""Lay the climate regions over the coastal map (owner's five regions, October 14). Safe to run again.
Run in the editor after build_coastal_terrain.py, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

DECIDED (delegated): the three sandy palm islands (the island, the islet and the second island) are the Desert
group, whose humid climate the owner set and whose humidity reaches 100 m offshore (owner); the new snowy island to
the north begins the Winter group. Each region covers its island and a 15 m margin of shallows (working value)
beyond the shore; past that is the open sea, except the Desert's 100 m of offshore humidity. Region temperatures
and humidity are working values (see AEWClimateRegion::DefaultClimate and the design reference).
"""
import json
import sys
from pathlib import Path
import unreal

# The shores, as in build_coastal_terrain.py (not imported: that script builds the terrain when loaded).
MAIN_SHORE = (-800, -100, 5100, 4100, 0.03)
ISLET_SHORE = (9500, 2600, 1800, 1450, 0.05)
SECOND_SHORE = (-15000, -13000, 2800, 2200, 0.06)
WINTER_SHORE = (2000, 17500, 3000, 2400, 0.07)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = 'World/Regions'
SHALLOWS = 1500.0          # cm of shallows each region keeps past its shore (tuning)
DESERT_OFFSHORE = 10000.0  # cm: the desert's humidity reaches 100 m offshore (owner)
REGIONS = [('Desert: the island', unreal.EWRegion.DESERT, MAIN_SHORE, DESERT_OFFSHORE),
           ('Desert: the islet', unreal.EWRegion.DESERT, ISLET_SHORE, DESERT_OFFSHORE),
           ('Desert: the second island', unreal.EWRegion.DESERT, SECOND_SHORE, DESERT_OFFSHORE),
           ('Winter: the north island', unreal.EWRegion.WINTER, WINTER_SHORE, 0.0)]


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWClimateRegion):
            actors.destroy_actor(actor)
    placed = []
    for label, kind, shore, reach in REGIONS:
        cx, cy, rx, ry, wobble = shore
        region = actors.spawn_actor_from_class(unreal.EWClimateRegion, unreal.Vector(cx, cy, 0))
        region.set_actor_label(label)
        region.set_folder_path(FOLDER)
        region.set_editor_property('region', kind)
        # The wavy shore reaches out to about (1 + wobble) of the oval; the margin is past that.
        region.set_editor_property('radii', unreal.Vector2D(rx * (1 + wobble) + SHALLOWS, ry * (1 + wobble) + SHALLOWS))
        region.set_editor_property('offshore_reach', reach)
        region.set_editor_property('climate', unreal.EWClimateRegion.default_climate(kind))
        placed.append({'label': label, 'centre': [cx, cy], 'reach': reach})
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'RegionsResult.json').write_text(json.dumps({'success': True, 'regions': placed}, indent=2))
    unreal.log(f'Regions: {len(placed)}')


if __name__ == '__main__':
    main()
