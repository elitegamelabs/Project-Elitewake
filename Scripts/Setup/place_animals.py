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
from wildlife_distribution import HABITAT, LEGACY_ISLAND_KEYS, expansion_islands, missing_counts  # noqa: E402
from world_landmarks import near_landmark  # noqa: E402
from build_coastal_flora import Ground  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/Wildlife/Animals'
LEVEL_FOLDER = 'Coast/Wildlife/Animals'
SPAWN, DOCK = (150.0, 0.0), (4000.0, 900.0)
# Per island of each region: {animal: how many} (tuning). Habitats: shore (the beach band), trees (near trees),
# low (wet low ground of the swamp), inland.
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
    existing_animals = [actor for actor in actors.get_all_level_actors() if isinstance(actor, unreal.EWAnimal)]
    if W.FIVE_ISLAND_WORLD:
        # The old islands are gone: animals left standing where they were would float over open sea.
        for actor in existing_animals:
            actors.destroy_actor(actor)
        existing_animals = []
    added_keys = {island.key for island in W.ISLANDS if island.key not in LEGACY_ISLAND_KEYS}
    existing_by_island_kind = {}
    for actor in existing_animals:
        label = f' {actor.get_actor_label()} '
        island_key = next((key for key in added_keys if f' {key} ' in label), None)
        if island_key:
            definition = actor.get_editor_property('definition')
            kind = definition.get_name().removeprefix('DA_Animal_') if definition else ''
            existing_by_island_kind[(island_key, kind)] = existing_by_island_kind.get((island_key, kind), 0) + 1
    targets = expansion_islands()
    # Leave all existing actors in place. Fill only missing species counts on the fourteen appended islands.
    trees = [(t.get_actor_location().x, t.get_actor_location().y) for t in actors.get_all_level_actors()
             if isinstance(t, unreal.EWHarvestTree)]
    ground = Ground()
    placed, counts = [], {}
    for island in targets:
        existing_counts = {kind: count for (key, kind), count in existing_by_island_kind.items() if key == island.key}
        plan = missing_counts(island, existing_counts)
        rng = random.Random(sum(map(ord, island.key)) * 6151)
        reach = island.reach()
        near_trees = [(tx, ty) for tx, ty in trees if abs(tx - island.cx) < reach and abs(ty - island.cy) < reach]
        taken = [(a.get_actor_location().x, a.get_actor_location().y) for a in existing_animals
                 if f' {island.key} ' in f' {a.get_actor_label()} ']
        for name, count in plan.items():
            if count == 0:
                continue
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
                if not fits(HABITAT[name], island, x, y, z, near_trees) or W.near_port(x, y) or T.near_cave(x, y) or near_landmark(x, y):
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
                animal.set_actor_label(f'{display} {island.key} {existing_counts.get(name, 0) + made + 1}')
                animal.set_folder_path(LEVEL_FOLDER)
                animal.set_editor_property('definition', definition)
                animal.set_editor_property('surface_z', T.SEA)
                taken.append((x, y))
                placed.append((name, island.key, island.region, round(x), round(y), round(z)))
            if made < count:
                unreal.log_warning(f'{island.key} could add only {made}/{count} {name} with current habitat constraints')
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'AnimalsExpansionResult.json').write_text(json.dumps({
        'success': True, 'islands_targeted': [i.key for i in targets],
        'existing_animals_untouched': len(existing_animals), 'new_animals': len(placed),
        'by_kind': counts, 'placed': placed}, indent=2))
    unreal.log(f'Animals added to new islands: {len(placed)}')


if __name__ == '__main__':
    main()
