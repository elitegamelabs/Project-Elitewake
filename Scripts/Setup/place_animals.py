"""Place the land animals across the five-region world. Safe to run again. Run in the editor after build_animals.py
(which makes the animals' models and definitions) and the world scripts, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner habitat directions (October 14): the Swamp has the reptiles; Horses belong in Plains and Snow Leopards in Winter
(neither is modelled yet). DECIDED (delegated; counts are tuning): alligators and cottonmouths on the Swamp islands;
squirrel monkeys among the Jungle's trees; tortoises in the Desert and the Jungle; flamingos and pelicans along the
shores of the Plains and Desert islands. The starter island keeps a few docile animals only (pelicans, flamingos, a
tortoise and squirrel monkeys) so a new survivor is not met by an alligator. The Winter islands wait for their
Snow Leopards. Aggressive animals start well away from the beach spawn and the dock.

build_animals.py also places animals on the old two-island layout when run; run this after it to lay them out over
the world instead.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from build_coastal_flora import Ground  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/Wildlife/Animals'
LEVEL_FOLDER = 'Coast/Wildlife/Animals'
SPAWN, DOCK = (150.0, 0.0), (4000.0, 900.0)
# Per island of each region: {animal: how many} (tuning). Habitats: shore (the beach band), trees (near trees),
# low (wet low ground of the swamp), inland.
PER_ISLAND = {'Swamp': {'Alligator': 2, 'Cottonmouth': 2},
              'Jungle': {'SquirrelMonkey': 3, 'Tortoise': 1},
              'Desert': {'Tortoise': 2, 'Flamingo': 2, 'Pelican': 1},
              'Plains': {'Pelican': 2, 'Flamingo': 1},
              'Winter': {}}
STARTER = {'Pelican': 2, 'Flamingo': 2, 'Tortoise': 1, 'SquirrelMonkey': 2}
HABITAT = {'Alligator': 'low', 'Cottonmouth': 'low', 'SquirrelMonkey': 'trees', 'Tortoise': 'inland',
           'Flamingo': 'shore', 'Pelican': 'shore'}


def fits(habitat, island, x, y, z, trees):
    inland = -island.distance(x, y)
    if habitat == 'shore':
        return 150 < inland < 1800 and z > T.SEA + 15
    if habitat == 'low':
        return inland > 500 and T.SEA + 15 < z < T.SEA + 250
    if habitat == 'trees':
        return inland > 500 and z > T.SEA + 30 and any(math.hypot(x - tx, y - ty) < 450 for tx, ty in trees)
    return inland > 600 and z > T.SEA + 30


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWAnimal):
            actors.destroy_actor(actor)
    trees = [(t.get_actor_location().x, t.get_actor_location().y) for t in actors.get_all_level_actors()
             if isinstance(t, unreal.EWHarvestTree)]
    ground = Ground()
    placed, counts = [], {}
    for island in W.ISLANDS:
        plan = STARTER if island.key == 'Starter' else PER_ISLAND[island.region]
        rng = random.Random(sum(map(ord, island.key)) * 6151)
        reach = island.reach()
        near_trees = [(tx, ty) for tx, ty in trees if abs(tx - island.cx) < reach and abs(ty - island.cy) < reach]
        taken = []
        for name, count in plan.items():
            definition = unreal.load_asset(f'{FOLDER}/DA_Animal_{name}')
            assert definition, f'run build_animals.py first ({name})'
            size = definition.get_editor_property('size')
            radius = max(size.y * .5, size.x * .3, 15.0)
            aggressive = definition.get_editor_property('aggressive')
            made, tries = 0, 0
            while made < count and tries < 6000:
                tries += 1
                x, y = island.cx + rng.uniform(-reach, reach), island.cy + rng.uniform(-reach, reach)
                z = ground(x, y)
                if not fits(HABITAT[name], island, x, y, z, near_trees):
                    continue
                if min(math.hypot(x - px, y - py) for px, py in (SPAWN, DOCK)) < (2600 if aggressive else 700):
                    continue
                if any(math.hypot(x - px, y - py) < 400 for px, py in taken):
                    continue
                animal = actors.spawn_actor_from_class(unreal.EWAnimal, unreal.Vector(x, y, z + radius),
                                                       unreal.Rotator(0, 0, rng.uniform(-180, 180)))
                made += 1
                counts[name] = counts.get(name, 0) + 1
                display = str(definition.get_editor_property('display_name'))
                animal.set_actor_label(f'{display} {island.key} {made}')
                animal.set_folder_path(LEVEL_FOLDER)
                animal.set_editor_property('definition', definition)
                animal.set_editor_property('surface_z', T.SEA)
                taken.append((x, y))
                placed.append((name, island.key, island.region, round(x), round(y), round(z)))
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'AnimalsPlacedResult.json').write_text(json.dumps({
        'success': True, 'animals': len(placed), 'by_kind': counts,
        'by_region': {r: sum(1 for p in placed if p[2] == r) for r in W.REGION_CENTRES}, 'placed': placed}, indent=2))
    unreal.log(f'Animals placed: {len(placed)}')


if __name__ == '__main__':
    main()
