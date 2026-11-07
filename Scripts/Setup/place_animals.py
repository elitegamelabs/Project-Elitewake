"""Place the land animals across the twenty-island world, each island its own planned mix (wildlife_distribution.py). Safe to run again. Run in the editor after build_animals.py
(which makes the animals' models and definitions) and the world scripts, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner habitat directions (October 14): the Swamp has the reptiles; Horses belong in Plains and Snow Leopards in Winter
(neither is modelled yet). DECIDED (delegated; counts are tuning): alligators and cottonmouths on the Swamp islands;
squirrel monkeys among the Jungle's trees; tortoises in the Desert and the Jungle; flamingos and pelicans along the
shores of the Plains and Desert islands. The starter island keeps a few docile animals only (pelicans, flamingos, a
tortoise and squirrel monkeys) so a new survivor is not met by an alligator. The Winter islands wait for their
Snow Leopards. Aggressive animals start well away from the beach spawn and the dock.

Run this after build_animals.py to lay the approved populations out across the canonical five-island world.
"""
import json
import math
import os
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from wildlife_distribution import HABITAT, CLEAR_AGGRESSIVE, CLEAR_PASSIVE, missing_counts, target_counts  # noqa: E402
from world_landmarks import near_landmark  # noqa: E402
from build_coastal_flora import Ground  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/Wildlife/Animals'
LEVEL_FOLDER = 'Coast/Wildlife/Animals'
SPAWN, DOCK = (150.0, 0.0), (4000.0, 900.0)
SQUARE, SHARE_PER_SQUARE = 20000.0, .15        # cm, CLAUDE.md 5.7
# Where people are (CLAUDE.md 5.6): the starter's spawn and dock, and every village's Port and its waterfront.
PEOPLE = [SPAWN, DOCK] + [xy for p in W.PORTS.values() for xy in ((p.cx, p.cy), p.shore)]
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
    assert world_map.open_map(level, MAP)
    existing_animals = [actor for actor in actors.get_all_level_actors() if isinstance(actor, unreal.EWAnimal)]
    # Owner, November 6: no full rebuilds, so this adds only what each island is missing and leaves every animal already
    # placed where it is (and the spiders and Plains boars other scripts place). EW_ANIMALS_FRESH=1 clears this script's
    # own animals first, for a world whose ground has been re-cut under them.
    if os.environ.get('EW_ANIMALS_FRESH') == '1':
        for actor in existing_animals:
            if any(f' {i.key} ' in f' {actor.get_actor_label()} ' for i in W.ISLANDS) and str(actor.get_folder_path()) == LEVEL_FOLDER \
                    and str(actor.get_editor_property('definition').get_name()) != 'DA_Animal_Spider':
                actors.destroy_actor(actor)
        existing_animals = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWAnimal)]
    targets = W.ISLANDS
    trees = [(t.get_actor_location().x, t.get_actor_location().y) for t in actors.get_all_level_actors()
             if isinstance(t, unreal.EWHarvestTree)]
    # The forests are stands of instanced trees (November 6): every 25th tree of each stand marks where trees are.
    for stand in actors.get_all_level_actors():
        if isinstance(stand, unreal.EWForest):
            for i in range(0, stand.get_tree_count(), 25):
                at = stand.get_tree_transform(i).translation
                trees.append((at.x, at.y))
    ground = Ground()
    placed, counts = [], {}
    for island in targets:
        here = [a for a in existing_animals if f' {island.key} ' in f' {a.get_actor_label()} ' and a.get_editor_property('definition')]
        have = {}
        for a in here:
            kind = a.get_editor_property('definition').get_name().replace('DA_Animal_', '')
            have[kind] = have.get(kind, 0) + 1
        plan = missing_counts(island, have)
        rng = random.Random(sum(map(ord, island.key)) * 6151)
        reach = island.reach()
        near_trees = [(tx, ty) for tx, ty in trees if abs(tx - island.cx) < reach and abs(ty - island.cy) < reach]
        taken = [(a.get_actor_location().x, a.get_actor_location().y) for a in existing_animals
                 if f' {island.key} ' in f' {a.get_actor_label()} ']
        # CLAUDE.md 5.7: no 200 m square holds more than 15 % of an island's animals. Refusing a spot whose 200 m box
        # (200 m either way on both axes) already holds that share guarantees it: in any crowded square, the last animal
        # placed would have seen all the others within its box.
        crowd = max(1, int(SHARE_PER_SQUARE * sum(target_counts(island).values())))
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
                if not fits(HABITAT[name], island, x, y, z, near_trees) or W.near_port(x, y) or T.near_cave(x, y) or T.near_climb(x, y) or near_landmark(x, y):
                    continue
                if min(math.hypot(x - px, y - py) for px, py in PEOPLE) < (CLEAR_AGGRESSIVE if aggressive else CLEAR_PASSIVE):
                    continue
                if any(math.hypot(x - px, y - py) < 400 for px, py in taken):
                    continue
                if sum(1 for px, py in taken if abs(x - px) <= SQUARE and abs(y - py) <= SQUARE) >= crowd:
                    continue
                animal = actors.spawn_actor_from_class(unreal.EWAnimal, unreal.Vector(x, y, z + radius),
                                                       unreal.Rotator(0, 0, rng.uniform(-180, 180)))
                made += 1
                counts[name] = counts.get(name, 0) + 1
                display = str(definition.get_editor_property('display_name'))
                animal.set_actor_label(f'{display} {island.key} {have.get(name, 0) + made}')
                animal.set_folder_path(LEVEL_FOLDER)
                animal.set_editor_property('definition', definition)
                animal.set_editor_property('surface_z', T.SEA)
                world_map.keep_loaded(animal)          # every client has it (the map streams only its ground cover)
                taken.append((x, y))
                placed.append((name, island.key, island.region, round(x), round(y), round(z)))
            if made < count:
                unreal.log_warning(f'{island.key} could add only {made}/{count} {name} with current habitat constraints')
    assert world_map.save_map()
    Path(unreal.Paths.project_saved_dir(), 'AnimalsExpansionResult.json').write_text(json.dumps({
        'success': True, 'islands_targeted': [i.key for i in targets],
        'existing_animals_untouched': len(existing_animals), 'new_animals': len(placed),
        'by_kind': counts, 'placed': placed}, indent=2))
    unreal.log(f'Animals added to new islands: {len(placed)}')


if __name__ == '__main__':
    main()
