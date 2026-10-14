# Elitewake artwork catalog

Original source images for the team and Claude. This folder is part of the project. Images are **2D references**, not newly imported 3D meshes or implemented gameplay.

[Machine-readable catalog](CATALOG.json) includes dimensions, alpha ranges, hashes, atlas names and row/column UV regions. Adjacent JSON files preserve generation prompts. Run `python Scripts/Art/build_art_catalog.py` from the repository to rebuild it.

## Start here

- [Latest owner decisions](../Docs/WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md)
- [Milestones](../Docs/MILESTONES.md) and [remaining-work checklist](../Docs/REMAINING_WORK_2026-10-14.md)
- [Claude terrain/model handoff](../Docs/MILESTONE_WORLD_MESH_HANDOFF_2026-10-14.md)
- [Single Player](../Docs/SINGLE_PLAYER_RULES.md) / [Multiplayer](../Docs/MULTIPLAYER_RULES.md)
- [Animal roster](Concepts/Animals/2026-10-12/roster.json): guide region labels are provenance, not final five-region spawn assignments.
- [Owner-selected ship originals](Concepts/Boats/2026-10-11/selection.json): later alternate hulls do not replace these.

## Coverage and review

The October 14 atlases cover currency, common resources, ore and ingots, tools, crops, orchard fruit, regional forage/herbs/fungi/insects/trees, animal materials, weapons, ammunition, medicine, placeables, ship fittings, decorative recipe references, clothing and climate motifs. Existing animal, ship, sail, workstation, fish, HUD and title images are indexed too. Generic animal materials may be reused for species-specific drops; art does not establish new recipes, values or unlocks.

Growth stages remain incomplete. The first growth board has incorrect species imagery and is explicitly a draft. Do not treat it as an approved mesh reference. Tree/crop growth boards, seed and sapling imagery, multi-view modeling references, claim flags and neon ghost-ship group art remain on the checklist. Berry bushes are wild-only and static; no berry seeds or planted growth stages.

Forage sheet 3 version 2 replaces version 1. Insects sheet 1 needs Bloodwing anatomy review. Blueprint diagrams are illustrative and need a wooden-tool material correction. Atlas arrangements and cutout quality need visual approval before runtime binding. No game balance or distribution is inferred from art. Duplicate ZIP bundles are excluded from this publication; individual source images are supplied.

Indexed images: **153**. PNG sources are stored through Git LFS; use a normal Git LFS checkout to obtain full-resolution files.

## Images

| Image | Size | Named atlas slots | Status |
| --- | --- | --- | --- |
| [Concepts/Animals/2026-10-12/american_alligator.png](Concepts/Animals/2026-10-12/american_alligator.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/arctic_fox.png](Concepts/Animals/2026-10-12/arctic_fox.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/arctic_hare.png](Concepts/Animals/2026-10-12/arctic_hare.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/bass.png](Concepts/Animals/2026-10-12/bass.png) | 1774 × 887 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/beaver.png](Concepts/Animals/2026-10-12/beaver.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/black_bear.png](Concepts/Animals/2026-10-12/black_bear.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/bullfrog.png](Concepts/Animals/2026-10-12/bullfrog.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/camel.png](Concepts/Animals/2026-10-12/camel.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/capybara.png](Concepts/Animals/2026-10-12/capybara.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/catfish.png](Concepts/Animals/2026-10-12/catfish.png) | 1983 × 793 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/cottonmouth.png](Concepts/Animals/2026-10-12/cottonmouth.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/crocodile.png](Concepts/Animals/2026-10-12/crocodile.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/desert_tortoise.png](Concepts/Animals/2026-10-12/desert_tortoise.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/eagle.png](Concepts/Animals/2026-10-12/eagle.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/elephant.png](Concepts/Animals/2026-10-12/elephant.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/elk.png](Concepts/Animals/2026-10-12/elk.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/gazelle.png](Concepts/Animals/2026-10-12/gazelle.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/giant_spider.png](Concepts/Animals/2026-10-12/giant_spider.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/giant_tortoise.png](Concepts/Animals/2026-10-12/giant_tortoise.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/gorilla.png](Concepts/Animals/2026-10-12/gorilla.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/great_white_shark.png](Concepts/Animals/2026-10-12/great_white_shark.png) | 1774 × 887 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/grizzly_bear.png](Concepts/Animals/2026-10-12/grizzly_bear.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/hammerhead_shark.png](Concepts/Animals/2026-10-12/hammerhead_shark.png) | 2172 × 724 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/heron.png](Concepts/Animals/2026-10-12/heron.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/horse.png](Concepts/Animals/2026-10-12/horse.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/house_cat.png](Concepts/Animals/2026-10-12/house_cat.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/hyena.png](Concepts/Animals/2026-10-12/hyena.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/iguana.png](Concepts/Animals/2026-10-12/iguana.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/jackal.png](Concepts/Animals/2026-10-12/jackal.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/jaguar.png](Concepts/Animals/2026-10-12/jaguar.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/lion.png](Concepts/Animals/2026-10-12/lion.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/manatee.png](Concepts/Animals/2026-10-12/manatee.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/manta_ray.png](Concepts/Animals/2026-10-12/manta_ray.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/monkey.png](Concepts/Animals/2026-10-12/monkey.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/moose.png](Concepts/Animals/2026-10-12/moose.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/mountain_goat.png](Concepts/Animals/2026-10-12/mountain_goat.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/ostrich.png](Concepts/Animals/2026-10-12/ostrich.png) | 1312 × 1199 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/otter.png](Concepts/Animals/2026-10-12/otter.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/parrot.png](Concepts/Animals/2026-10-12/parrot.png) | 1145 × 1374 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/piranha.png](Concepts/Animals/2026-10-12/piranha.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/python.png](Concepts/Animals/2026-10-12/python.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/raccoon.png](Concepts/Animals/2026-10-12/raccoon.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/reindeer.png](Concepts/Animals/2026-10-12/reindeer.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/rhino.png](Concepts/Animals/2026-10-12/rhino.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/siren.png](Concepts/Animals/2026-10-12/siren.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/snow_leopard.png](Concepts/Animals/2026-10-12/snow_leopard.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/squid.png](Concepts/Animals/2026-10-12/squid.png) | 1672 × 941 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/tapir.png](Concepts/Animals/2026-10-12/tapir.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/tiger.png](Concepts/Animals/2026-10-12/tiger.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/toucan.png](Concepts/Animals/2026-10-12/toucan.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/warthog.png](Concepts/Animals/2026-10-12/warthog.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/water_buffalo.png](Concepts/Animals/2026-10-12/water_buffalo.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/wild_boar.png](Concepts/Animals/2026-10-12/wild_boar.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Animals/2026-10-12/wolf.png](Concepts/Animals/2026-10-12/wolf.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Brigantine-Exterior-Mast-Sockets-v2.png](Concepts/Boats/2026-10-11/Brigantine-Exterior-Mast-Sockets-v2.png) | 1536 × 1024 | — | Alternate reference only; owner-selected original hulls remain canonical |
| [Concepts/Boats/2026-10-11/Brigantine-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Brigantine-Exterior-Original-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Brigantine-Interior-v1.png](Concepts/Boats/2026-10-11/Brigantine-Interior-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Dinghy-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Dinghy-Exterior-Original-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Dinghy-Interior-v1.png](Concepts/Boats/2026-10-11/Dinghy-Interior-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Large-Multi-Deck-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Large-Multi-Deck-Exterior-Original-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Large-Multi-Deck-Interior-v1.png](Concepts/Boats/2026-10-11/Large-Multi-Deck-Interior-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Raft-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Raft-Exterior-Original-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Raft-Interior-v1.png](Concepts/Boats/2026-10-11/Raft-Interior-v1.png) | 1672 × 941 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Schooner-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Schooner-Exterior-Original-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Schooner-Interior-v1.png](Concepts/Boats/2026-10-11/Schooner-Interior-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Sloop-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Sloop-Exterior-Original-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Sloop-Interior-v1.png](Concepts/Boats/2026-10-11/Sloop-Interior-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/angryfish.png](Concepts/Fish/2026-10-12/angryfish.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/bass.png](Concepts/Fish/2026-10-12/bass.png) | 1774 × 887 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/catfish.png](Concepts/Fish/2026-10-12/catfish.png) | 1983 × 793 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/mantaray.png](Concepts/Fish/2026-10-12/mantaray.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/mantee.png](Concepts/Fish/2026-10-12/mantee.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/shark.png](Concepts/Fish/2026-10-12/shark.png) | 1774 × 887 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/shark2.png](Concepts/Fish/2026-10-12/shark2.png) | 2172 × 724 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/squid.png](Concepts/Fish/2026-10-12/squid.png) | 1672 × 941 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Sails/2026-10-11/Large-Dark-Red-Sail-v1.png](Concepts/Sails/2026-10-11/Large-Dark-Red-Sail-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Sails/2026-10-11/Large-Sail-v1.png](Concepts/Sails/2026-10-11/Large-Sail-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Sails/2026-10-11/Medium-Sail-v1.png](Concepts/Sails/2026-10-11/Medium-Sail-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Sails/2026-10-11/Small-Sail-v1.png](Concepts/Sails/2026-10-11/Small-Sail-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Brick-Oven-Concept-v1.png](Concepts/Workstations/2026-10-12/Brick-Oven-Concept-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Cooking-Hearth-Concept-v1.png](Concepts/Workstations/2026-10-12/Cooking-Hearth-Concept-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Forge-Concept-v1.png](Concepts/Workstations/2026-10-12/Forge-Concept-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Loom-Concept-v1.png](Concepts/Workstations/2026-10-12/Loom-Concept-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Smithy-Concept-v1.png](Concepts/Workstations/2026-10-12/Smithy-Concept-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Tanner-Concept-v1.png](Concepts/Workstations/2026-10-12/Tanner-Concept-v1.png) | 1536 × 1024 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Environment/TropicalSand-v1.png](Environment/TropicalSand-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Environment/WeatheredTimber-v1.png](Environment/WeatheredTimber-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/Bass-v1.png](Fauna/Fish/Bass-v1.png) | 1024 × 421 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/Catfish-v1.png](Fauna/Fish/Catfish-v1.png) | 1024 × 313 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/GreatWhiteShark-v1.png](Fauna/Fish/GreatWhiteShark-v1.png) | 1024 × 440 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/HammerheadShark-v1.png](Fauna/Fish/HammerheadShark-v1.png) | 1024 × 330 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/Manatee-v1.png](Fauna/Fish/Manatee-v1.png) | 1024 × 521 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/MantaRay-v1.png](Fauna/Fish/MantaRay-v1.png) | 1024 × 621 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/Piranha-v1.png](Fauna/Fish/Piranha-v1.png) | 1024 × 609 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/Squid-v1.png](Fauna/Fish/Squid-v1.png) | 1024 × 564 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Flora/Growth/2026-10-14/Trees-Growth-1-v1.png](Flora/Growth/2026-10-14/Trees-Growth-1-v1.png) | 1153 × 1364 | 12 | DRAFT: species identity needs correction before modeling or runtime use |
| [Flora/Veyran-Palm-Frond-v1.png](Flora/Veyran-Palm-Frond-v1.png) | 2048 × 512 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Items/Atlases/2026-10-14/ammo-Atlas-v1.png](Items/Atlases/2026-10-14/ammo-Atlas-v1.png) | 1536 × 1024 | 6 | Family references only; specific ammunition variants not defined |
| [Items/Atlases/2026-10-14/Animal-Marine-Materials-Atlas-v1.png](Items/Atlases/2026-10-14/Animal-Marine-Materials-Atlas-v1.png) | 1448 × 1086 | 12 | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/blueprints-Atlas-v1.png](Items/Atlases/2026-10-14/blueprints-Atlas-v1.png) | 1536 × 1024 | 4 | Visual presentation references, not new physical blueprint items, recipe unlocks or functional engineering plans |
| [Items/Atlases/2026-10-14/climate-Atlas-v1.png](Items/Atlases/2026-10-14/climate-Atlas-v1.png) | 1774 × 887 | 8 | Clothing and indicator concepts; not approved equipment recipes or final HUD assets |
| [Items/Atlases/2026-10-14/Confirmed-Crops-Atlas-v1.png](Items/Atlases/2026-10-14/Confirmed-Crops-Atlas-v1.png) | 1774 × 887 | 8 | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/Core-Resources-Atlas-v1.png](Items/Atlases/2026-10-14/Core-Resources-Atlas-v1.png) | 1261 × 1247 | 16 | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/fittings-Atlas-v1.png](Items/Atlases/2026-10-14/fittings-Atlas-v1.png) | 1774 × 887 | 8 | Fitting concepts, original ship/sail references remain authoritative; anchor currently built-in, no crafted-anchor recipe implied |
| [Items/Atlases/2026-10-14/forage1-Atlas-v1.png](Items/Atlases/2026-10-14/forage1-Atlas-v1.png) | 1448 × 1086 | 16 | Generated 2D reference atlas; no gameplay balance or biome distribution implied |
| [Items/Atlases/2026-10-14/forage2-Atlas-v1.png](Items/Atlases/2026-10-14/forage2-Atlas-v1.png) | 1447 × 1087 | 16 | Generated 2D reference atlas; no gameplay balance or biome distribution implied |
| [Items/Atlases/2026-10-14/forage3-Atlas-v1.png](Items/Atlases/2026-10-14/forage3-Atlas-v1.png) | 1536 × 1024 | 7 | Legacy art; newer version preferred |
| [Items/Atlases/2026-10-14/forage3-Atlas-v2.png](Items/Atlases/2026-10-14/forage3-Atlas-v2.png) | 1774 × 887 | 7 | Illustrative 2D botanical reference atlas; replaces bokeh-background v1 for inventory use |
| [Items/Atlases/2026-10-14/fungi1-Atlas-v1.png](Items/Atlases/2026-10-14/fungi1-Atlas-v1.png) | 1374 × 1145 | 16 | Illustrative 2D resource atlas; visual references do not set recipes or effects |
| [Items/Atlases/2026-10-14/fungi2-Atlas-v1.png](Items/Atlases/2026-10-14/fungi2-Atlas-v1.png) | 1774 × 887 | 6 | Illustrative 2D resource atlas; visual references do not set recipes or effects |
| [Items/Atlases/2026-10-14/herbs1-Atlas-v1.png](Items/Atlases/2026-10-14/herbs1-Atlas-v1.png) | 1402 × 1122 | 16 | Illustrative 2D botanical reference atlas; gameplay values and distribution not defined |
| [Items/Atlases/2026-10-14/herbs2-Atlas-v1.png](Items/Atlases/2026-10-14/herbs2-Atlas-v1.png) | 1287 × 1222 | 16 | Illustrative 2D botanical reference atlas; gameplay values and distribution not defined |
| [Items/Atlases/2026-10-14/herbs3-Atlas-v1.png](Items/Atlases/2026-10-14/herbs3-Atlas-v1.png) | 1774 × 887 | 5 | Illustrative 2D botanical reference atlas; gameplay values and distribution not defined |
| [Items/Atlases/2026-10-14/insects1-Atlas-v1.png](Items/Atlases/2026-10-14/insects1-Atlas-v1.png) | 1263 × 1246 | 16 | Illustrative 2D resource atlas; visual references do not set recipes or effects |
| [Items/Atlases/2026-10-14/insects2-Atlas-v1.png](Items/Atlases/2026-10-14/insects2-Atlas-v1.png) | 1448 × 1086 | 11 | Illustrative 2D resource atlas; visual references do not set recipes or effects |
| [Items/Atlases/2026-10-14/materials-Atlas-v1.png](Items/Atlases/2026-10-14/materials-Atlas-v1.png) | 1536 × 1024 | 16 | Material-family concept references; does not approve new recipes |
| [Items/Atlases/2026-10-14/medicine-Atlas-v1.png](Items/Atlases/2026-10-14/medicine-Atlas-v1.png) | 1774 × 887 | 8 | Existing medical families and toxic spoiled berries; balance not assigned |
| [Items/Atlases/2026-10-14/Metal-Ingots-Atlas-v1.png](Items/Atlases/2026-10-14/Metal-Ingots-Atlas-v1.png) | 1448 × 1086 | 12 | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/Metal-Ores-Atlas-v1.png](Items/Atlases/2026-10-14/Metal-Ores-Atlas-v1.png) | 1278 × 1230 | 9 | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/Orchard-Fruits-Atlas-v1.png](Items/Atlases/2026-10-14/Orchard-Fruits-Atlas-v1.png) | 1286 × 1223 | 14 | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/placeables-Atlas-v1.png](Items/Atlases/2026-10-14/placeables-Atlas-v1.png) | 1774 × 887 | 8 | Placeable reference art only; inventory-first rules retained; no material cost or unlock invented |
| [Items/Atlases/2026-10-14/Portable-Tools-Atlas-v1.png](Items/Atlases/2026-10-14/Portable-Tools-Atlas-v1.png) | 1448 × 1086 | 12 | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/trees1-Atlas-v1.png](Items/Atlases/2026-10-14/trees1-Atlas-v1.png) | 1312 × 1199 | 16 | Illustrative 2D plant model reference; no species-specific Wood inventory types |
| [Items/Atlases/2026-10-14/trees2-Atlas-v1.png](Items/Atlases/2026-10-14/trees2-Atlas-v1.png) | 1448 × 1086 | 10 | Illustrative 2D plant model reference; no species-specific Wood inventory types |
| [Items/Atlases/2026-10-14/weapons-Atlas-v1.png](Items/Atlases/2026-10-14/weapons-Atlas-v1.png) | 1774 × 887 | 8 | Confirmed families; period pistol name, weapon stats and glider engineering remain TBD |
| [Items/Currency/2026-10-14/Currency-Coin-Atlas-v1.png](Items/Currency/2026-10-14/Currency-Coin-Atlas-v1.png) | 2172 × 724 | 3 | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Raw-Fish-v1.png](Items/Raw-Fish-v1.png) | 512 × 512 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Items/Raw-Meat-v1.png](Items/Raw-Meat-v1.png) | 512 × 512 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Axe-v1.png](Placeholders/ItemIcons/Axe-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Flask-v1.png](Placeholders/ItemIcons/Flask-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Pickaxe-v1.png](Placeholders/ItemIcons/Pickaxe-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/RepairKit-v1.png](Placeholders/ItemIcons/RepairKit-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Shovel-v1.png](Placeholders/ItemIcons/Shovel-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Torch-v1.png](Placeholders/ItemIcons/Torch-v1.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Survival/2026-10-11/Health-Full-v1.png](UI/Survival/2026-10-11/Health-Full-v1.png) | 1254 × 1254 | — | Legacy art; newer version preferred |
| [UI/Survival/2026-10-11/Hunger-Full-v1.png](UI/Survival/2026-10-11/Hunger-Full-v1.png) | 1254 × 1254 | — | Legacy art; newer version preferred |
| [UI/Survival/2026-10-11/Hydration-Full-v1.png](UI/Survival/2026-10-11/Hydration-Full-v1.png) | 1254 × 1254 | — | Legacy art; newer version preferred |
| [UI/Survival/2026-10-11/Matte-v2/Health-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Health-Matte-Full-v2.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Survival/2026-10-11/Matte-v2/Hunger-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Hunger-Matte-Full-v2.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Survival/2026-10-11/Matte-v2/Hydration-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Hydration-Matte-Full-v2.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Survival/2026-10-11/Matte-v2/Stamina-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Stamina-Matte-Full-v2.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Survival/2026-10-11/Matte-v2/Weight-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Weight-Matte-Full-v2.png) | 1254 × 1254 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Survival/2026-10-11/Stamina-Full-v1.png](UI/Survival/2026-10-11/Stamina-Full-v1.png) | 1254 × 1254 | — | Legacy art; newer version preferred |
| [UI/Title/2026-10-13/Elitewake-Logo-v1.png](UI/Title/2026-10-13/Elitewake-Logo-v1.png) | 2172 × 724 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Elitewake-Starter-Screen-Owner-v1.png](UI/Title/2026-10-13/Elitewake-Starter-Screen-Owner-v1.png) | 1672 × 941 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Elitewake-Starter-WaterMask-v1.png](UI/Title/2026-10-13/Elitewake-Starter-WaterMask-v1.png) | 1672 × 941 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Main-Menu-Concept-Blurred-Multiplayer-v1.png](UI/Title/2026-10-13/Main-Menu-Concept-Blurred-Multiplayer-v1.png) | 1672 × 941 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Press-Any-Key-To-Start-v1.png](UI/Title/2026-10-13/Press-Any-Key-To-Start-v1.png) | 2200 × 715 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Press-Any-Key-To-Start-v2.png](UI/Title/2026-10-13/Press-Any-Key-To-Start-v2.png) | 2200 × 360 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Press-Any-Key-v1.png](UI/Title/2026-10-13/Press-Any-Key-v1.png) | 2172 × 724 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Title-Dock-Background-v1.png](UI/Title/2026-10-13/Title-Dock-Background-v1.png) | 1672 × 941 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Title-Waves-4Frame-v1.png](UI/Title/2026-10-13/Title-Waves-4Frame-v1.png) | 2172 × 724 | — | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/Elitewake-Title-v1.png](UI/Title/Elitewake-Title-v1.png) | 1672 × 941 | — | Existing source reference; consult adjacent README/selection/roster metadata |
