# Five-island world: what is built (October 22, 2026)

Owner (October 21 and 22): one island per region (Plains, Winter, Swamp, Desert, Jungle), each 1,500 to 2,500 m across with an organic, irregular coast; Plains is the start; ocean 1,500 m deep.
Status words: **built** = generated in the map by the rebuild scripts; **verified** = a check passed (named). Nothing here is hand-sculpted art.

## Layout (`Scripts/Setup/world_layout.py`, `FIVE_ISLAND_WORLD = True`)
| Island | Region | Centre (m) | About (m) | Peak (tuning) |
|---|---|---|---|---|
| Starter | Plains | (0, 0) | 2,020 x 1,640 | 26 m |
| Winter1 | Winter, north | (-600, 2,800) | 2,360 x 1,640 | 110 m |
| Swamp1 | Swamp, south | (-300, -2,700) | 2,000 x 1,600 | 3 m |
| Desert1 | Desert, east | (2,800, -300) | 2,200 x 1,680 | 46 m |
| Jungle1 | Jungle, west | (-3,800, 200) | 2,040 x 1,840 | 68 m |
- Each shore is an ellipse bent by eight harmonics of its own plus a cove, so no two outlines are alike (`Scripts/Tests/test_five_islands.py`: size, irregularity, no rotated copies, nearest neighbour 800 to 2,000 m).
- The Plains island keeps the old spawn beach, dock, pond and sloop mooring on its east end; the island grows west from there. The Plains (starter) port faces south-west (decided, reversible).
- The 26/40-island generators are kept untouched as the baseline; set `FIVE_ISLAND_WORLD = False` to get them back. Their tests are skipped while the five-island world is selected.
- Ground meshes: 300 cm grid (starter 400) so each island mesh is about 1 million vertices (`world_terrain.ground_spacing`).

## Rebuilt by `Scripts/Setup/rebuild_world.py`
Terrain, caves (one per island), cave webs, landmarks, grass, flora (regional primary trees), rocks, reefs, seabed life, fish, animals, regions, ports, sloop, rendering.

## Wildlife
Only the six existing land species exist (Alligator, Cottonmouth, Squirrel Monkey, Tortoise, Flamingo, Pelican), placed at 7 times the old per-island counts for the larger islands (`wildlife_distribution.FIVE_ISLAND_DENSITY`).
**Gaps (owner list in `GAMEPLAY_DESIGN_DECISIONS_2026-10-22.md` item 10):** Winter has no land animals; deer, rabbits, boars, wolves, elk, bears, lizards, scorpions, desert foxes, large cats, birds of prey and the rest do not exist as assets. They need models, animations and audio per `Art/Animals/ANIMAL_MODEL_ANIMATION_AUDIO_REQUIREMENTS_2026-10-16.md`. Tasks: Grok GR4 (food chains), Scenario queue.
