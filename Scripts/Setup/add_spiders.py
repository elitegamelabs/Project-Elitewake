"""Spiders in every cave and in the Southern Swamp (owner, October 16 milestone). Safe to run again; the other animals are left alone.
Run in the editor outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
Builds the Cave Spider (model, material instance, definition from build_animals.py), removes any spiders already in the map, then
places CAVE_SPIDERS in the chamber of each island's cave (T.CAVES, they stay in it: roam radius 450 cm) and SWAMP_SPIDERS on each
swamp island's wet low ground. Counts are tuning (DECIDED delegated, TBD owner)."""
import importlib
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_animals as BA  # noqa: E402
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from build_coastal_flora import Ground  # noqa: E402
from place_animals import fits  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

CAVE_SPIDERS = 2
SWAMP_SPIDERS = 5
LEVEL_FOLDER = 'Coast/Wildlife/Animals'


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    meat = unreal.load_asset(BA.RAW_MEAT)
    assert meat, 'Run build_fish.py first (it makes Raw Meat).'
    # A fresh copy of build_animals first: the rebuild runs every step in one editor, and another step may have narrowed
    # its ANIMALS to its own kind (add_spiders and build_plains_threat each do).
    importlib.reload(BA)
    BA.ANIMALS = {'Spider': BA.ANIMALS['Spider']}
    definition = BA.build_definitions(meat)['Spider']
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, BA.MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWAnimal) and actor.get_editor_property('definition') == definition:
            actors.destroy_actor(actor)
    ground = Ground()
    # An animal stands on its feet a body radius below its centre (AEWAnimal::ApplyDefinition): lift it by that, not a
    # fixed 25 cm (the spider's radius is larger, which left its feet 35 cm under the floor).
    size = definition.get_editor_property('size')
    lift = max(size.y * .5, size.x * .3, 15.0)
    rng = random.Random(8128)
    placed = []

    def spawn(x, y, z, where):
        animal = actors.spawn_actor_from_class(unreal.EWAnimal, unreal.Vector(x, y, z), unreal.Rotator(0, 0, rng.uniform(-180, 180)))
        animal.set_actor_label(f'Cave Spider {where} {len(placed) + 1}')
        animal.set_folder_path(LEVEL_FOLDER)
        animal.set_editor_property('definition', definition)
        animal.set_editor_property('surface_z', T.SEA)
        placed.append((where, round(x), round(y), round(z)))

    for key, cave in T.CAVES.items():
        if not cave or cave.kind == 'sea':
            continue
        for k in range(CAVE_SPIDERS):
            v = (-1 if k % 2 else 1) * rng.uniform(120, 260)
            x, y = cave.world(cave.chamber_u + rng.uniform(-200, 150), v)
            spawn(x, y, cave.floor + lift, f'{key} cave')
    for island in W.ISLANDS:
        if island.region != 'Swamp':
            continue
        reach, made, tries = island.reach(), 0, 0
        while made < SWAMP_SPIDERS and tries < 8000:
            tries += 1
            x, y = island.cx + rng.uniform(-reach, reach), island.cy + rng.uniform(-reach, reach)
            z = ground(x, y)
            if z is None or not fits('low', island, x, y, z, []) or T.near_cave(x, y, 900) or T.near_climb(x, y) or W.near_port(x, y):
                continue
            if any(math.hypot(x - p[1], y - p[2]) < 500 for p in placed):
                continue
            spawn(x, y, z + lift, f'{island.key} swamp')
            made += 1
    assert world_map.save_map()
    Path(unreal.Paths.project_saved_dir(), 'SpidersResult.json').write_text(json.dumps({'success': True, 'spiders': len(placed), 'placed': placed}, indent=2))
    unreal.log(f'Spiders: {len(placed)}')


if __name__ == '__main__':
    main()
