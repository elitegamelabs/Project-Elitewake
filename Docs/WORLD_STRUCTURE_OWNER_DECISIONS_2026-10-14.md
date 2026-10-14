# World structure — owner decisions, October 14

These direct owner decisions take precedence over older geography statements. They describe intended systems; this note does not claim implementation or approve unspecified balance values. Original Word documents are preserved.

## Regions and islands

- Five regions: Desert, Winter, Jungle, Plains and Swamp. This supersedes the older four-region count.
- Each region contains multiple islands belonging to its biome, with varied shapes, sizes and substantial explorable interiors.
- Single player keeps all neighboring regions accessible. Multiplayer organizes them into regional grids; one sufficiently capable server may host all five. Exact inter-grid travel remains unresolved; do not equate grids with mandatory separate machines.
- Single player should have stable, optimized performance. Full-world server requirements follow measured simulation/player load, not artificial overhead.
- Terrain and feature placement are generated when a world is created and remain fixed for that world. Multiplayer has no player-controlled manual Save button; the server persists characters, ships and structures.
- Islands are spaced for longer sailing voyages, not close hops or a fixed sixty-second crossing. Exact spacing must be tuned against ship speeds.
- Approximately ten feet of beach sand around islands; cliff faces can interrupt the beach where steep land meets water.
- Cliffs are distributed across different selected islands in every region, not concentrated on one island or required on every island.
- One cave system per island, with varied entrance placement in inland hills, cliff faces and coastal rock formations.

## Biome presentation and climate

| Region | Owner direction |
| --- | --- |
| Desert | Sandy terrain, bushes, palms; humid climate. Humidity extends 100 meters offshore around its islands. |
| Winter | Birch trees; rugged mountains and cliffs mixed with smooth slopes; snowy ground, bushes and berries; snowfall. Cold-region materials, ingredients and wildlife. |
| Jungle | Tall spruce trees per the owner's latest correction; dense, maze-like vegetation, navigable by the map; humid. |
| Plains | Grassy flatland with many hills; comfortable baseline climate; horses mentioned as characteristic wildlife. |
| Swamp | Humid wetland region; detailed terrain and vegetation choices remain open. |

Stone uses a consistent underlying visual style throughout the world; winter adds snow on top. Different shapes and formations remain possible. Older botanical naming remains reference material; its four-region distribution and specialty Wood outputs cannot silently override these decisions or the existing single generic Wood inventory resource.

All trees should have thick, mature-looking trunks. Main branches are sturdy, with varied branch thickness and natural taper to smaller branches and twigs. Palms have thick trunks with rough overlapping retained leaf bases resembling pineapple scales. This is bark/leaf-base structure, not shells attached to a tree. The owner also wants usable 3D project assets and multiple useful model reference views, not only front pictures; reference images alone do not satisfy that mesh requirement.

Humidity belongs in the Character interface, with appropriate humidity/overheating indicators for Desert, Jungle and Swamp. Overheating slowly reduces Health and is relieved by removing clothing; Winter requires suitable warm clothing and a freezing indicator. Exact thresholds, clothing values, damage rates and humidity-bar measurement remain open. Do not assign desert offshore radius to other regions without a decision.

## Gathering and resources

- Common resources are widespread; rare/specialty resources encourage travel between islands and biomes.
- Winter's signature resources include Coal and Emeralds. Emeralds are winter-only; Coal's exclusivity is not decided.
- Berry types can overlap biomes. Bush appearance depends on berry type, winter adds snow, and bushes yield Fiber as well as berries. Berries remain wild-only and keep existing spoilage rules.
- Trees and seed-grown farm plants need three distinct visible growth-stage designs. Every tree type has a plantable sapling, restricted to its own biome. An incompatible planting consumes one sapling and shows "This tree cannot be planted here". Exact stage times and species-to-region lists remain open. Berry bushes have a static design and are excluded from planted growth-stage progression.
- Trees, bushes and small stones on every island's beaches can be harvested bare-handed, enabling initial tool crafting. Bare-hand tree yields and existing hand-injury behavior require reconciliation; the owner has not explicitly removed injuries or defined new amounts.
- Metal ore requires a pickaxe. Stone picks handle Copper and softer ores; Iron and harder ores require Metal or Tungsten picks. The full hardness list and progression remain open.
- Tungsten Axe and Tungsten Pickaxe are explicitly confirmed; recipes, durability and efficiency are not set by artwork.

## Traversal and world collision

- Selected steep mountain/cliff sections require a Climbing Axe; gentler slopes remain walkable. All intended exploration areas should be reachable with appropriate traversal.
- Climbing consumes Stamina; reaching zero causes a loss of grip and a fall.
- Solid-ground falls exceeding 25 meters are fatal. Falls of 25 meters or less have damage scaled to fall distance; minimum safe fall height and the damage curve remain open. Deep-water landings are exempt from these impact rules.
- The ocean reaches a maximum of 500 meters only in selected deep areas, with shallower shelves and slopes elsewhere.
- The seabed and terrain must be solid: players cannot swim through the bottom, below 500 meters, or into the underside of an island. This includes distant-water coverage and gaps at terrain edges.
- The owner requested invisible barrier coverage throughout the world, including mountains, cliffs, hills and overlooks. **Unresolved:** whether these barriers hug solid terrain to prevent penetration or also prevent legitimate falls from edges. The latter conflicts with the confirmed stamina/fall rules. No behavior is selected by this note.

## Art handoff

The owner authorized original resource/item/currency/crafting/blueprint artwork generation and publication of existing art, including animal references, to GitHub for Claude. The art catalog is separate from gameplay implementation: images do not grant items, unlock recipes, introduce balance values, or constitute imported 3D models.

## Company claims and game modes

- Island claims are multiplayer-only. Single player has no claim flags, contests or ownership gates for building; the owner wants to build anywhere. Physical placement and terrain collision are separate from claim permission.
- NPC Port islands are excluded from claiming and contesting.
- A Company's Claim Flag rises during its initial claim timer. Duration remains TBD.
- A rival placing its flag next to the current flag starts a separate contest period. When that period expires, the original flag disappears and the challenger's own claim timer starts. The challenger does not finish claiming during the contest period.
- Claim/contest durations, allowed distance, multiple challengers, original-timer behavior during contest, defender cancellation and offline behavior remain open. No timer values are chosen by this note.

## Ghost ships

- Hostile ghost ships roam the ocean in groups of three, spread across the map.
- Their vessel types correspond to ships unlocked by the player. How that selection works for multiple players with different unlocks remains unresolved.
- The entire ship body is neon-colored; sails remain normal rather than neon. Exact palette, rewards, health, spawn density and encounter timing remain open.

## Authorized work order

The owner requested completion of the image collection and GitHub art handoff first, followed by implementation of the features described in this note. New 3D meshes and gameplay require their own verification; the image handoff is not evidence that the world, planting, climate or claim systems already work.
