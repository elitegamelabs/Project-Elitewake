# Elitewake artwork catalog

Original source images for the team and Claude. The catalog distinguishes references, pending model inputs, generated Unreal drafts, current UI art sources and legacy art. Images are **2D sources**, not proof that an art reference has been approved as final.

[Machine-readable catalog](CATALOG.json) includes dimensions, alpha ranges, hashes, classifications, atlas names and row/column UV regions. It also lists selected generated Unreal folders with draft status and asset counts. Adjacent JSON files preserve generation prompts. Run `python Scripts/Art/build_art_catalog.py` from the repository to rebuild it.

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

Catalog classifications are intentionally cautious: reference art is not a mesh; pending-model art has model work tracked elsewhere; generated-in-editor drafts still need visual review; in-game art sources are not final-art approval; and legacy items remain for history. The catalog records generated wildlife, flora, rock, world-material and tool-animation folders separately from PNG sources. Forage sheet 3 version 2 replaces version 1. Insects sheet 1 needs Bloodwing anatomy review. Blueprint diagrams are illustrative and need a wooden-tool material correction. Atlas arrangements and cutout quality need visual approval before runtime binding. No game balance or distribution is inferred from art. Duplicate ZIP bundles are excluded from this publication; individual source images are supplied.

Indexed images: **269**. PNG sources are stored through Git LFS; use a normal Git LFS checkout to obtain full-resolution files.

## Generated Unreal folders

These entries point to draft assets in `Content/`; the asset filenames appear in `CATALOG.json` so the team can see what exists without treating prototypes as finished models.

| Project folder | Assets | Status |
| --- | ---: | --- |
| `Content/Elitewake/Wildlife/Animals` | 19 | generated-in-editor-draft — Six coastal land-animal prototypes; the owner roster contains additional species. |
| `Content/Elitewake/Wildlife/Fish` | 35 | generated-in-editor-draft — Procedural aquatic-creature prototypes sourced from Art/Fauna/Fish; visual review remains open. |
| `Content/Elitewake/World/Flora` | 26 | generated-in-editor-draft — Editor-built vegetation prototypes using Art/Flora leaf textures; not a complete regional flora set. |
| `Content/Elitewake/World/Rocks` | 16 | generated-in-editor-draft — Editor-built rock variants; art and placement remain prototype content. |
| `Content/Elitewake/World/Materials` | 8 | generated-in-editor-draft — World material and texture prototypes; not final art approval. |
| `Content/Elitewake/Animations/Tools` | 9 | generated-in-editor-draft — Imported or configured animation assets; motion and retargeting need in-game review. |

## Images

| Image | Size | Named atlas slots | Classification | Status |
| --- | --- | --- | --- | --- |
| [Concepts/Animals/2026-10-12/american_alligator.png](Concepts/Animals/2026-10-12/american_alligator.png) | 1536 × 1024 | — | reference | Reference for an existing coastal prototype; compare the in-game model against this image |
| [Concepts/Animals/2026-10-12/arctic_fox.png](Concepts/Animals/2026-10-12/arctic_fox.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/arctic_hare.png](Concepts/Animals/2026-10-12/arctic_hare.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/bass.png](Concepts/Animals/2026-10-12/bass.png) | 1774 × 887 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/beaver.png](Concepts/Animals/2026-10-12/beaver.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/black_bear.png](Concepts/Animals/2026-10-12/black_bear.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/bullfrog.png](Concepts/Animals/2026-10-12/bullfrog.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/camel.png](Concepts/Animals/2026-10-12/camel.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/capybara.png](Concepts/Animals/2026-10-12/capybara.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/catfish.png](Concepts/Animals/2026-10-12/catfish.png) | 1983 × 793 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/cottonmouth.png](Concepts/Animals/2026-10-12/cottonmouth.png) | 1536 × 1024 | — | reference | Reference for an existing coastal prototype; compare the in-game model against this image |
| [Concepts/Animals/2026-10-12/crocodile.png](Concepts/Animals/2026-10-12/crocodile.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/desert_tortoise.png](Concepts/Animals/2026-10-12/desert_tortoise.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/eagle.png](Concepts/Animals/2026-10-12/eagle.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/elephant.png](Concepts/Animals/2026-10-12/elephant.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/elk.png](Concepts/Animals/2026-10-12/elk.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/gazelle.png](Concepts/Animals/2026-10-12/gazelle.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/giant_spider.png](Concepts/Animals/2026-10-12/giant_spider.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/giant_tortoise.png](Concepts/Animals/2026-10-12/giant_tortoise.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/gorilla.png](Concepts/Animals/2026-10-12/gorilla.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/great_white_shark.png](Concepts/Animals/2026-10-12/great_white_shark.png) | 1774 × 887 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/grizzly_bear.png](Concepts/Animals/2026-10-12/grizzly_bear.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/hammerhead_shark.png](Concepts/Animals/2026-10-12/hammerhead_shark.png) | 2172 × 724 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/heron.png](Concepts/Animals/2026-10-12/heron.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/horse.png](Concepts/Animals/2026-10-12/horse.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/house_cat.png](Concepts/Animals/2026-10-12/house_cat.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/hyena.png](Concepts/Animals/2026-10-12/hyena.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/iguana.png](Concepts/Animals/2026-10-12/iguana.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/jackal.png](Concepts/Animals/2026-10-12/jackal.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/jaguar.png](Concepts/Animals/2026-10-12/jaguar.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/lion.png](Concepts/Animals/2026-10-12/lion.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/manatee.png](Concepts/Animals/2026-10-12/manatee.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/manta_ray.png](Concepts/Animals/2026-10-12/manta_ray.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/monkey.png](Concepts/Animals/2026-10-12/monkey.png) | 1536 × 1024 | — | reference | Reference for an existing coastal prototype; compare the in-game model against this image |
| [Concepts/Animals/2026-10-12/moose.png](Concepts/Animals/2026-10-12/moose.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/mountain_goat.png](Concepts/Animals/2026-10-12/mountain_goat.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/ostrich.png](Concepts/Animals/2026-10-12/ostrich.png) | 1312 × 1199 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/otter.png](Concepts/Animals/2026-10-12/otter.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/parrot.png](Concepts/Animals/2026-10-12/parrot.png) | 1145 × 1374 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/piranha.png](Concepts/Animals/2026-10-12/piranha.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/python.png](Concepts/Animals/2026-10-12/python.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/raccoon.png](Concepts/Animals/2026-10-12/raccoon.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/reindeer.png](Concepts/Animals/2026-10-12/reindeer.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/rhino.png](Concepts/Animals/2026-10-12/rhino.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/siren.png](Concepts/Animals/2026-10-12/siren.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/snow_leopard.png](Concepts/Animals/2026-10-12/snow_leopard.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/squid.png](Concepts/Animals/2026-10-12/squid.png) | 1672 × 941 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/tapir.png](Concepts/Animals/2026-10-12/tapir.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/tiger.png](Concepts/Animals/2026-10-12/tiger.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/toucan.png](Concepts/Animals/2026-10-12/toucan.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/warthog.png](Concepts/Animals/2026-10-12/warthog.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/water_buffalo.png](Concepts/Animals/2026-10-12/water_buffalo.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/wild_boar.png](Concepts/Animals/2026-10-12/wild_boar.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Animals/2026-10-12/wolf.png](Concepts/Animals/2026-10-12/wolf.png) | 1536 × 1024 | — | pending-model | 2D animal modeling reference; follow the roster and milestones for per-species model status |
| [Concepts/Boats/2026-10-11/Brigantine-Exterior-Mast-Sockets-v2.png](Concepts/Boats/2026-10-11/Brigantine-Exterior-Mast-Sockets-v2.png) | 1536 × 1024 | — | reference | Alternate reference only; owner-selected original hulls remain canonical |
| [Concepts/Boats/2026-10-11/Brigantine-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Brigantine-Exterior-Original-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Brigantine-Interior-v1.png](Concepts/Boats/2026-10-11/Brigantine-Interior-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Dinghy-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Dinghy-Exterior-Original-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Dinghy-Interior-v1.png](Concepts/Boats/2026-10-11/Dinghy-Interior-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Large-Multi-Deck-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Large-Multi-Deck-Exterior-Original-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Large-Multi-Deck-Interior-v1.png](Concepts/Boats/2026-10-11/Large-Multi-Deck-Interior-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Raft-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Raft-Exterior-Original-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Raft-Interior-v1.png](Concepts/Boats/2026-10-11/Raft-Interior-v1.png) | 1672 × 941 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Schooner-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Schooner-Exterior-Original-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Schooner-Interior-v1.png](Concepts/Boats/2026-10-11/Schooner-Interior-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Sloop-Exterior-Original-v1.png](Concepts/Boats/2026-10-11/Sloop-Exterior-Original-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Boats/2026-10-11/Sloop-Interior-v1.png](Concepts/Boats/2026-10-11/Sloop-Interior-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/angryfish.png](Concepts/Fish/2026-10-12/angryfish.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/bass.png](Concepts/Fish/2026-10-12/bass.png) | 1774 × 887 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/catfish.png](Concepts/Fish/2026-10-12/catfish.png) | 1983 × 793 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/mantaray.png](Concepts/Fish/2026-10-12/mantaray.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/mantee.png](Concepts/Fish/2026-10-12/mantee.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/shark.png](Concepts/Fish/2026-10-12/shark.png) | 1774 × 887 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/shark2.png](Concepts/Fish/2026-10-12/shark2.png) | 2172 × 724 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Fish/2026-10-12/squid.png](Concepts/Fish/2026-10-12/squid.png) | 1672 × 941 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Sails/2026-10-11/Large-Dark-Red-Sail-v1.png](Concepts/Sails/2026-10-11/Large-Dark-Red-Sail-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Sails/2026-10-11/Large-Sail-v1.png](Concepts/Sails/2026-10-11/Large-Sail-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Sails/2026-10-11/Medium-Sail-v1.png](Concepts/Sails/2026-10-11/Medium-Sail-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Sails/2026-10-11/Small-Sail-v1.png](Concepts/Sails/2026-10-11/Small-Sail-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Brick-Oven-Concept-v1.png](Concepts/Workstations/2026-10-12/Brick-Oven-Concept-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Cooking-Hearth-Concept-v1.png](Concepts/Workstations/2026-10-12/Cooking-Hearth-Concept-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Forge-Concept-v1.png](Concepts/Workstations/2026-10-12/Forge-Concept-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Loom-Concept-v1.png](Concepts/Workstations/2026-10-12/Loom-Concept-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Smithy-Concept-v1.png](Concepts/Workstations/2026-10-12/Smithy-Concept-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Concepts/Workstations/2026-10-12/Tanner-Concept-v1.png](Concepts/Workstations/2026-10-12/Tanner-Concept-v1.png) | 1536 × 1024 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Environment/TropicalSand-v1.png](Environment/TropicalSand-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Environment/WeatheredTimber-v1.png](Environment/WeatheredTimber-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Fauna/Fish/Bass-v1.png](Fauna/Fish/Bass-v1.png) | 1024 × 421 | — | generated-in-editor-draft | Generated cutout and procedural mesh input; editor-built creature assets still need visual review |
| [Fauna/Fish/Catfish-v1.png](Fauna/Fish/Catfish-v1.png) | 1024 × 313 | — | generated-in-editor-draft | Generated cutout and procedural mesh input; editor-built creature assets still need visual review |
| [Fauna/Fish/GreatWhiteShark-v1.png](Fauna/Fish/GreatWhiteShark-v1.png) | 1024 × 440 | — | generated-in-editor-draft | Generated cutout and procedural mesh input; editor-built creature assets still need visual review |
| [Fauna/Fish/HammerheadShark-v1.png](Fauna/Fish/HammerheadShark-v1.png) | 1024 × 330 | — | generated-in-editor-draft | Generated cutout and procedural mesh input; editor-built creature assets still need visual review |
| [Fauna/Fish/Manatee-v1.png](Fauna/Fish/Manatee-v1.png) | 1024 × 521 | — | generated-in-editor-draft | Generated cutout and procedural mesh input; editor-built creature assets still need visual review |
| [Fauna/Fish/MantaRay-v1.png](Fauna/Fish/MantaRay-v1.png) | 1024 × 621 | — | generated-in-editor-draft | Generated cutout and procedural mesh input; editor-built creature assets still need visual review |
| [Fauna/Fish/Piranha-v1.png](Fauna/Fish/Piranha-v1.png) | 1024 × 609 | — | generated-in-editor-draft | Generated cutout and procedural mesh input; editor-built creature assets still need visual review |
| [Fauna/Fish/Squid-v1.png](Fauna/Fish/Squid-v1.png) | 1024 × 564 | — | generated-in-editor-draft | Generated cutout and procedural mesh input; editor-built creature assets still need visual review |
| [Flora/Birch-Leaves-v1.png](Flora/Birch-Leaves-v1.png) | 1024 × 1024 | — | generated-in-editor-draft | Generated leaf-card texture used by editor-built vegetation drafts; this is not a tree mesh |
| [Flora/Growth/2026-10-14/Trees-Growth-1-v1.png](Flora/Growth/2026-10-14/Trees-Growth-1-v1.png) | 1153 × 1364 | 12 | pending-model | DRAFT reference: species identity needs correction before modeling or runtime use |
| [Flora/Maravai-Leaves-v1.png](Flora/Maravai-Leaves-v1.png) | 1024 × 1024 | — | generated-in-editor-draft | Generated leaf-card texture used by editor-built vegetation drafts; this is not a tree mesh |
| [Flora/Veyran-Palm-Frond-v1.png](Flora/Veyran-Palm-Frond-v1.png) | 2048 × 512 | — | generated-in-editor-draft | Generated leaf-card texture used by editor-built vegetation drafts; this is not a tree mesh |
| [Items/Atlases/2026-10-14/ammo-Atlas-v1.png](Items/Atlases/2026-10-14/ammo-Atlas-v1.png) | 1536 × 1024 | 6 | reference | Family references only; specific ammunition variants not defined |
| [Items/Atlases/2026-10-14/Animal-Marine-Materials-Atlas-v1.png](Items/Atlases/2026-10-14/Animal-Marine-Materials-Atlas-v1.png) | 1448 × 1086 | 12 | reference | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/blueprints-Atlas-v1.png](Items/Atlases/2026-10-14/blueprints-Atlas-v1.png) | 1536 × 1024 | 4 | reference | Visual presentation references, not new physical blueprint items, recipe unlocks or functional engineering plans |
| [Items/Atlases/2026-10-14/climate-Atlas-v1.png](Items/Atlases/2026-10-14/climate-Atlas-v1.png) | 1774 × 887 | 8 | reference | Clothing and indicator concepts; not approved equipment recipes or final HUD assets |
| [Items/Atlases/2026-10-14/Confirmed-Crops-Atlas-v1.png](Items/Atlases/2026-10-14/Confirmed-Crops-Atlas-v1.png) | 1774 × 887 | 8 | reference | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/Core-Resources-Atlas-v1.png](Items/Atlases/2026-10-14/Core-Resources-Atlas-v1.png) | 1261 × 1247 | 16 | reference | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/fittings-Atlas-v1.png](Items/Atlases/2026-10-14/fittings-Atlas-v1.png) | 1774 × 887 | 8 | reference | Fitting concepts, original ship/sail references remain authoritative; anchor currently built-in, no crafted-anchor recipe implied |
| [Items/Atlases/2026-10-14/forage1-Atlas-v1.png](Items/Atlases/2026-10-14/forage1-Atlas-v1.png) | 1448 × 1086 | 16 | reference | Generated 2D reference atlas; no gameplay balance or biome distribution implied |
| [Items/Atlases/2026-10-14/forage2-Atlas-v1.png](Items/Atlases/2026-10-14/forage2-Atlas-v1.png) | 1447 × 1087 | 16 | reference | Generated 2D reference atlas; no gameplay balance or biome distribution implied |
| [Items/Atlases/2026-10-14/forage3-Atlas-v1.png](Items/Atlases/2026-10-14/forage3-Atlas-v1.png) | 1536 × 1024 | 7 | legacy | Legacy art; version 2 is preferred |
| [Items/Atlases/2026-10-14/forage3-Atlas-v2.png](Items/Atlases/2026-10-14/forage3-Atlas-v2.png) | 1774 × 887 | 7 | reference | Illustrative 2D botanical reference atlas; replaces bokeh-background v1 for inventory use |
| [Items/Atlases/2026-10-14/fungi1-Atlas-v1.png](Items/Atlases/2026-10-14/fungi1-Atlas-v1.png) | 1374 × 1145 | 16 | reference | Illustrative 2D resource atlas; visual references do not set recipes or effects |
| [Items/Atlases/2026-10-14/fungi2-Atlas-v1.png](Items/Atlases/2026-10-14/fungi2-Atlas-v1.png) | 1774 × 887 | 6 | reference | Illustrative 2D resource atlas; visual references do not set recipes or effects |
| [Items/Atlases/2026-10-14/herbs1-Atlas-v1.png](Items/Atlases/2026-10-14/herbs1-Atlas-v1.png) | 1402 × 1122 | 16 | reference | Illustrative 2D botanical reference atlas; gameplay values and distribution not defined |
| [Items/Atlases/2026-10-14/herbs2-Atlas-v1.png](Items/Atlases/2026-10-14/herbs2-Atlas-v1.png) | 1287 × 1222 | 16 | reference | Illustrative 2D botanical reference atlas; gameplay values and distribution not defined |
| [Items/Atlases/2026-10-14/herbs3-Atlas-v1.png](Items/Atlases/2026-10-14/herbs3-Atlas-v1.png) | 1774 × 887 | 5 | reference | Illustrative 2D botanical reference atlas; gameplay values and distribution not defined |
| [Items/Atlases/2026-10-14/insects1-Atlas-v1.png](Items/Atlases/2026-10-14/insects1-Atlas-v1.png) | 1263 × 1246 | 16 | reference | Illustrative 2D resource atlas; visual references do not set recipes or effects |
| [Items/Atlases/2026-10-14/insects2-Atlas-v1.png](Items/Atlases/2026-10-14/insects2-Atlas-v1.png) | 1448 × 1086 | 11 | reference | Illustrative 2D resource atlas; visual references do not set recipes or effects |
| [Items/Atlases/2026-10-14/materials-Atlas-v1.png](Items/Atlases/2026-10-14/materials-Atlas-v1.png) | 1536 × 1024 | 16 | reference | Material-family concept references; does not approve new recipes |
| [Items/Atlases/2026-10-14/medicine-Atlas-v1.png](Items/Atlases/2026-10-14/medicine-Atlas-v1.png) | 1774 × 887 | 8 | reference | Existing medical families and toxic spoiled berries; balance not assigned |
| [Items/Atlases/2026-10-14/Metal-Ingots-Atlas-v1.png](Items/Atlases/2026-10-14/Metal-Ingots-Atlas-v1.png) | 1448 × 1086 | 12 | reference | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/Metal-Ores-Atlas-v1.png](Items/Atlases/2026-10-14/Metal-Ores-Atlas-v1.png) | 1278 × 1230 | 9 | reference | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/Orchard-Fruits-Atlas-v1.png](Items/Atlases/2026-10-14/Orchard-Fruits-Atlas-v1.png) | 1286 × 1223 | 14 | reference | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/placeables-Atlas-v1.png](Items/Atlases/2026-10-14/placeables-Atlas-v1.png) | 1774 × 887 | 8 | reference | Placeable reference art only; inventory-first rules retained; no material cost or unlock invented |
| [Items/Atlases/2026-10-14/Portable-Tools-Atlas-v1.png](Items/Atlases/2026-10-14/Portable-Tools-Atlas-v1.png) | 1448 × 1086 | 12 | reference | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Atlases/2026-10-14/trees1-Atlas-v1.png](Items/Atlases/2026-10-14/trees1-Atlas-v1.png) | 1312 × 1199 | 16 | reference | Illustrative 2D plant model reference; no species-specific Wood inventory types |
| [Items/Atlases/2026-10-14/trees2-Atlas-v1.png](Items/Atlases/2026-10-14/trees2-Atlas-v1.png) | 1448 × 1086 | 10 | reference | Illustrative 2D plant model reference; no species-specific Wood inventory types |
| [Items/Atlases/2026-10-14/weapons-Atlas-v1.png](Items/Atlases/2026-10-14/weapons-Atlas-v1.png) | 1774 × 887 | 8 | reference | Confirmed families; period pistol name, weapon stats and glider engineering remain TBD |
| [Items/Currency/2026-10-14/Currency-Coin-Atlas-v1.png](Items/Currency/2026-10-14/Currency-Coin-Atlas-v1.png) | 2172 × 724 | 3 | reference | Original 2D reference/inventory atlas; not a 3D model or imported gameplay asset |
| [Items/Icons/AzrenBerry-v1.png](Items/Icons/AzrenBerry-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/Cannon-v1.png](Items/Icons/Cannon-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/CannonAmmo-v1.png](Items/Icons/CannonAmmo-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/contact-sheet.png](Items/Icons/contact-sheet.png) | 1536 × 1024 | — | in-game-art-source | Review sheet of the cut inventory icons |
| [Items/Icons/CopperOre-v1.png](Items/Icons/CopperOre-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/Fiber-v1.png](Items/Icons/Fiber-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/Hide-v1.png](Items/Icons/Hide-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/LargeSail-v1.png](Items/Icons/LargeSail-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/MediumSail-v1.png](Items/Icons/MediumSail-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/RepairKit-v1.png](Items/Icons/RepairKit-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/ShipWheel-v1.png](Items/Icons/ShipWheel-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/SmallSail-v1.png](Items/Icons/SmallSail-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/SpoiledBerries-v1.png](Items/Icons/SpoiledBerries-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/Sticks-v1.png](Items/Icons/Sticks-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/Stone-v1.png](Items/Icons/Stone-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/StoneAxe-v1.png](Items/Icons/StoneAxe-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/StonePickaxe-v1.png](Items/Icons/StonePickaxe-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/Thatch-v1.png](Items/Icons/Thatch-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/Torch-v1.png](Items/Icons/Torch-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/WaterSkin-v1.png](Items/Icons/WaterSkin-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/Wood-v1.png](Items/Icons/Wood-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/WoodenAxe-v1.png](Items/Icons/WoodenAxe-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/WoodenPickaxe-v1.png](Items/Icons/WoodenPickaxe-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Icons/WoodenShovel-v1.png](Items/Icons/WoodenShovel-v1.png) | 256 × 256 | — | in-game-art-source | In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable |
| [Items/Raw-Fish-v1.png](Items/Raw-Fish-v1.png) | 512 × 512 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Items/Raw-Meat-v1.png](Items/Raw-Meat-v1.png) | 512 × 512 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Axe-v1.png](Placeholders/ItemIcons/Axe-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Flask-v1.png](Placeholders/ItemIcons/Flask-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Pickaxe-v1.png](Placeholders/ItemIcons/Pickaxe-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/RepairKit-v1.png](Placeholders/ItemIcons/RepairKit-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Shovel-v1.png](Placeholders/ItemIcons/Shovel-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Placeholders/ItemIcons/Torch-v1.png](Placeholders/ItemIcons/Torch-v1.png) | 1254 × 1254 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Survival/2026-10-11/Health-Full-v1.png](UI/Survival/2026-10-11/Health-Full-v1.png) | 1254 × 1254 | — | legacy | Legacy art; newer version preferred |
| [UI/Survival/2026-10-11/Hunger-Full-v1.png](UI/Survival/2026-10-11/Hunger-Full-v1.png) | 1254 × 1254 | — | legacy | Legacy art; newer version preferred |
| [UI/Survival/2026-10-11/Hydration-Full-v1.png](UI/Survival/2026-10-11/Hydration-Full-v1.png) | 1254 × 1254 | — | legacy | Legacy art; newer version preferred |
| [UI/Survival/2026-10-11/Matte-v2/Health-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Health-Matte-Full-v2.png) | 1254 × 1254 | — | in-game-art-source | Updated survival indicator art source; rendered appearance still needs visual review |
| [UI/Survival/2026-10-11/Matte-v2/Hunger-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Hunger-Matte-Full-v2.png) | 1254 × 1254 | — | in-game-art-source | Updated survival indicator art source; rendered appearance still needs visual review |
| [UI/Survival/2026-10-11/Matte-v2/Hydration-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Hydration-Matte-Full-v2.png) | 1254 × 1254 | — | in-game-art-source | Updated survival indicator art source; rendered appearance still needs visual review |
| [UI/Survival/2026-10-11/Matte-v2/Stamina-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Stamina-Matte-Full-v2.png) | 1254 × 1254 | — | in-game-art-source | Updated survival indicator art source; rendered appearance still needs visual review |
| [UI/Survival/2026-10-11/Matte-v2/Weight-Matte-Full-v2.png](UI/Survival/2026-10-11/Matte-v2/Weight-Matte-Full-v2.png) | 1254 × 1254 | — | in-game-art-source | Updated survival indicator art source; rendered appearance still needs visual review |
| [UI/Survival/2026-10-11/Stamina-Full-v1.png](UI/Survival/2026-10-11/Stamina-Full-v1.png) | 1254 × 1254 | — | legacy | Legacy art; newer version preferred |
| [UI/Title/2026-10-13/Elitewake-Logo-v1.png](UI/Title/2026-10-13/Elitewake-Logo-v1.png) | 2172 × 724 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Elitewake-Starter-Screen-Owner-v1.png](UI/Title/2026-10-13/Elitewake-Starter-Screen-Owner-v1.png) | 1672 × 941 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Elitewake-Starter-WaterMask-v1.png](UI/Title/2026-10-13/Elitewake-Starter-WaterMask-v1.png) | 1672 × 941 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Main-Menu-Concept-Blurred-Multiplayer-v1.png](UI/Title/2026-10-13/Main-Menu-Concept-Blurred-Multiplayer-v1.png) | 1672 × 941 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Press-Any-Key-To-Start-v1.png](UI/Title/2026-10-13/Press-Any-Key-To-Start-v1.png) | 2200 × 715 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Press-Any-Key-To-Start-v2.png](UI/Title/2026-10-13/Press-Any-Key-To-Start-v2.png) | 2200 × 360 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Press-Any-Key-v1.png](UI/Title/2026-10-13/Press-Any-Key-v1.png) | 2172 × 724 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Title-Dock-Background-v1.png](UI/Title/2026-10-13/Title-Dock-Background-v1.png) | 1672 × 941 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/2026-10-13/Title-Waves-4Frame-v1.png](UI/Title/2026-10-13/Title-Waves-4Frame-v1.png) | 2172 × 724 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [UI/Title/Elitewake-Title-v1.png](UI/Title/Elitewake-Title-v1.png) | 1672 × 941 | — | reference | Existing source reference; consult adjacent README/selection/roster metadata |
| [Reference/Ships/DinghyRailing/ConceptSheet-v1.png](Reference/Ships/DinghyRailing/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/LargeRectangularSail/ConceptSheet-v1.png](Reference/Ships/LargeRectangularSail/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/LargeWeightedSail/ConceptSheet-v1.png](Reference/Ships/LargeWeightedSail/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/MediumRectangularSail/ConceptSheet-v1.png](Reference/Ships/MediumRectangularSail/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/MediumWeightedSail/ConceptSheet-v1.png](Reference/Ships/MediumWeightedSail/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/PlainRailing/ConceptSheet-v1.png](Reference/Ships/PlainRailing/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/SmallRectangularSail/ConceptSheet-v1.png](Reference/Ships/SmallRectangularSail/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/SmallWeightedSail/ConceptSheet-v1.png](Reference/Ships/SmallWeightedSail/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/SurgeonTable/ConceptSheet-v1.png](Reference/Ships/SurgeonTable/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/SurgeonTools/ConceptSheet-v1.png](Reference/Ships/SurgeonTools/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |
| [Reference/Ships/TwoCannonRailing/ConceptSheet-v1.png](Reference/Ships/TwoCannonRailing/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Generated concept reference; separate validated six-view files, models and integration pending |

| [Flora/Oak-Leaves-v1.png](Flora/Oak-Leaves-v1.png) | 1024 × 1024 | — | generated-in-editor-draft | Script-generated leaf card used by current regional tree builder; runtime look remains subject to Play review |

| [Flora/Ash-Leaves-v1.png](Flora/Ash-Leaves-v1.png) | 1024 × 1024 | — | generated-in-editor-draft | Script-generated leaf card used by current regional tree builder; runtime look remains subject to Play review |

| [Reference/Ships/DinghyRailing/front.png](Reference/Ships/DinghyRailing/front.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/PlainRailing/front.png](Reference/Ships/PlainRailing/front.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/SmallRectangularSail/deployment-0.png](Reference/Ships/SmallRectangularSail/deployment-0.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/SmallRectangularSail/deployment-25.png](Reference/Ships/SmallRectangularSail/deployment-25.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/SmallRectangularSail/deployment-50.png](Reference/Ships/SmallRectangularSail/deployment-50.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/SmallRectangularSail/deployment-75.png](Reference/Ships/SmallRectangularSail/deployment-75.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/SmallRectangularSail/front.png](Reference/Ships/SmallRectangularSail/front.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/SmallWeightedSail/front.png](Reference/Ships/SmallWeightedSail/front.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/TwoCannonRailing/front.png](Reference/Ships/TwoCannonRailing/front.png) | 1983 × 793 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Bear/ConceptSheet-v1.png](Reference/Animals/Bear/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/SpiderCave/ConceptSheet-v1.png](Reference/Animals/SpiderCave/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Elephant/ConceptSheet-v1.png](Reference/Animals/Elephant/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/GiantCrocodile/ConceptSheet-v1.png](Reference/Animals/GiantCrocodile/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/LargeRectangularSail/DeploymentSheet-v1.png](Reference/Ships/LargeRectangularSail/DeploymentSheet-v1.png) | 1983 × 793 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/LargeWeightedSail/DeploymentSheet-v1.png](Reference/Ships/LargeWeightedSail/DeploymentSheet-v1.png) | 2172 × 724 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Lion/ConceptSheet-v1.png](Reference/Animals/Lion/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/MediumRectangularSail/DeploymentSheet-v1.png](Reference/Ships/MediumRectangularSail/DeploymentSheet-v1.png) | 2172 × 724 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/MediumWeightedSail/DeploymentSheet-v1.png](Reference/Ships/MediumWeightedSail/DeploymentSheet-v1.png) | 2172 × 724 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/SmallRectangularSail/DeploymentSheet-v1.png](Reference/Ships/SmallRectangularSail/DeploymentSheet-v1.png) | 2172 × 724 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/SmallWeightedSail/DeploymentSheet-v1.png](Reference/Ships/SmallWeightedSail/DeploymentSheet-v1.png) | 1983 × 793 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/SpiderSwamp/ConceptSheet-v1.png](Reference/Animals/SpiderSwamp/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Tortoise/ConceptSheet-v1.png](Reference/Animals/Tortoise/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Bear/back.png](Reference/Animals/Bear/back.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Bear/front.png](Reference/Animals/Bear/front.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Bear/left.png](Reference/Animals/Bear/left.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Bear/right.png](Reference/Animals/Bear/right.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Bear/top.png](Reference/Animals/Bear/top.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Bear/underside.png](Reference/Animals/Bear/underside.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Elephant/back.png](Reference/Animals/Elephant/back.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Elephant/front.png](Reference/Animals/Elephant/front.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Elephant/left.png](Reference/Animals/Elephant/left.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Elephant/right.png](Reference/Animals/Elephant/right.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Elephant/top.png](Reference/Animals/Elephant/top.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Elephant/underside.png](Reference/Animals/Elephant/underside.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/GiantCrocodile/back.png](Reference/Animals/GiantCrocodile/back.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/GiantCrocodile/front.png](Reference/Animals/GiantCrocodile/front.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/GiantCrocodile/left.png](Reference/Animals/GiantCrocodile/left.png) | 1774 × 887 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/GiantCrocodile/right.png](Reference/Animals/GiantCrocodile/right.png) | 2172 × 724 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/GiantCrocodile/top.png](Reference/Animals/GiantCrocodile/top.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/GiantCrocodile/underside.png](Reference/Animals/GiantCrocodile/underside.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Lion/back.png](Reference/Animals/Lion/back.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Lion/front.png](Reference/Animals/Lion/front.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Lion/left.png](Reference/Animals/Lion/left.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Lion/right.png](Reference/Animals/Lion/right.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Lion/top.png](Reference/Animals/Lion/top.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Animals/Lion/underside.png](Reference/Animals/Lion/underside.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/DinghyRailing/attachment-v2.png](Reference/Ships/DinghyRailing/attachment-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/DinghyRailing/back-v2.png](Reference/Ships/DinghyRailing/back-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/DinghyRailing/left-v2.png](Reference/Ships/DinghyRailing/left-v2.png) | 1024 × 1536 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/DinghyRailing/right-v2.png](Reference/Ships/DinghyRailing/right-v2.png) | 1024 × 1536 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/DinghyRailing/top-v2.png](Reference/Ships/DinghyRailing/top-v2.png) | 1774 × 887 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/DinghyRailing/underside-v2.png](Reference/Ships/DinghyRailing/underside-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/PlainRailing/attachment-v2.png](Reference/Ships/PlainRailing/attachment-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/PlainRailing/back-v2.png](Reference/Ships/PlainRailing/back-v2.png) | 1774 × 887 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/PlainRailing/left-v2.png](Reference/Ships/PlainRailing/left-v2.png) | 1024 × 1536 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/PlainRailing/right-v2.png](Reference/Ships/PlainRailing/right-v2.png) | 1024 × 1536 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/PlainRailing/top-v2.png](Reference/Ships/PlainRailing/top-v2.png) | 2172 × 724 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/PlainRailing/underside-v2.png](Reference/Ships/PlainRailing/underside-v2.png) | 1774 × 887 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/TwoCannonRailing/attachment-v2.png](Reference/Ships/TwoCannonRailing/attachment-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/TwoCannonRailing/back-v2.png](Reference/Ships/TwoCannonRailing/back-v2.png) | 1774 × 887 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/TwoCannonRailing/left-v2.png](Reference/Ships/TwoCannonRailing/left-v2.png) | 1024 × 1536 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/TwoCannonRailing/right-v2.png](Reference/Ships/TwoCannonRailing/right-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/TwoCannonRailing/top-v2.png](Reference/Ships/TwoCannonRailing/top-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/TwoCannonRailing/underside-v2.png](Reference/Ships/TwoCannonRailing/underside-v2.png) | 2172 × 724 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/BailBucket/ConceptSheet-v1.png](Reference/Ships/BailBucket/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/Cannon/ConceptSheet-v1.png](Reference/Ships/Cannon/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/FlagWhite/CombatWearSheet-v1.png](Reference/Ships/FlagWhite/CombatWearSheet-v1.png) | 1774 × 887 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/GunportRound/MechanismSheet-v1.png](Reference/Ships/GunportRound/MechanismSheet-v1.png) | 1920 × 819 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/GunportSquare/MechanismSheet-v1.png](Reference/Ships/GunportSquare/MechanismSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Resources/OakWood/ConceptSheet-v1.png](Reference/Resources/OakWood/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Resources/SulfurOre/ConceptSheet-v1.png](Reference/Resources/SulfurOre/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/WreckCrate/ConceptSheet-v1.png](Reference/Ships/WreckCrate/ConceptSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/Hulls/Cavalier/LayoutSheet-v1.png](Reference/Ships/Hulls/Cavalier/LayoutSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/Hulls/Sloop/LayoutSheet-v1.png](Reference/Ships/Hulls/Sloop/LayoutSheet-v1.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/Hulls/Brigantine/LayoutSheet-v2.png](Reference/Ships/Hulls/Brigantine/LayoutSheet-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/Hulls/Raft/LayoutSheet-v2.png](Reference/Ships/Hulls/Raft/LayoutSheet-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
| [Reference/Ships/Hulls/Schooner/LayoutSheet-v2.png](Reference/Ships/Hulls/Schooner/LayoutSheet-v2.png) | 1536 × 1024 | — | reference | Concept; geometry validation pending |
