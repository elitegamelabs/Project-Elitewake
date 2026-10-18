# ELITEWAKE AI Agent Instructions

These instructions apply to every AI coding, design, art, and implementation assistant working in this repository. Read `Docs/DESIGN_REFERENCE.md` and the latest owner decisions before changing project behavior. The owner's latest explicit direction takes precedence over older documentation. Do not claim a design requirement is implemented unless code/assets and verification confirm it.

## Confirmed island and regional foliage requirements (owner, October 15, 2026)

Canonical details: [Island Terrain and Regional Tree Assignments](Design/World/ISLAND_TERRAIN_AND_REGIONAL_TREE_ASSIGNMENTS_2026-10-15.md).

- Every island must be deliberately terrain-oriented and individually recognizable. Vary island size, footprint, silhouette, coastlines, coves, cliffs, beaches, elevations, mountains, hills, ridges, valleys, plateaus, cavern entrances and cave layouts, landmarks, traversal routes, and tree placement. Do not create a world of cloned/resized/rotated island templates.
- Make the terrain feel geographically plausible from sea and on foot. Integrate caves, slopes, mountains and routes into the terrain rather than placing features on a flat surface. Islands can have different combinations and amounts of features, but each needs a distinct identity.
- Regional primary tree types are fixed as follows: **Winter = Birch; Jungle = Ash; Desert = Palm; Swamp = Spruce; Central Plains islands = Oak.** The latest correction is authoritative: Birch replaces the earlier Winter/Spruce mention; Spruce belongs to Swamp.
- Put quite a few of the region's assigned trees on each island, forming substantial stands/forests where terrain allows—not just isolated token trees. Distribute trees in terrain-aware clusters with natural differences in density, spacing, clearings and forest edges.
- Terrain and biome must influence vegetation placement. Preserve visual differences between islands while making each region's assigned tree identity clearly readable. These are primary species, not a blanket ban on other appropriate vegetation.
- Apply these requirements to every existing and future island, including the starter island in Central Plains. Keep island layouts and foliage placement distinct. Prefer data-driven configurations where they fit existing architecture.
- Preserve unrelated gameplay, asset IDs, inventory/crafting icons, and established systems. Do not invent new species or gameplay rules without owner direction.
- When implementing, inspect the current world-generation scripts and asset catalog first; coordinate with the agent responsible for the world rebuild. Do not edit files another agent explicitly owns in `Docs/DELEGATED_TASKS.md`. Only one agent may run Unreal Editor/build/Play checks at a time; follow the repository's editor-lock instructions.
- Distinguish status honestly: design requirements documented, code changed, assets generated, assets integrated, and in-game verification are separate milestones. Do not say terrain or tree placement is implemented merely because these instructions or a design document are committed.

Claude-specific note: check `Docs/DELEGATED_TASKS.md` before choosing work and respect the files owned by other agents.

## Disk-space cleanup: mandatory safe procedure

The owner wants AI assistance identifying unnecessary local files to reclaim storage. Follow `Docs/SAFE_STORAGE_CLEANUP_POLICY.md` before recommending or performing cleanup. Audit first, list exact candidate paths and estimated savings, preserve user changes and unique assets, and never use broad recursive deletion. Do not permanently delete uncertain files, tracked content, saves/backups, or files outside the project root without explicit owner approval. Treat Unreal `Saved/` as mixed-use; never delete the whole directory. Distinguish local generated cache/build files from shared source content. If the owner has not approved specific deletions, provide a ranked proposal and wait rather than deleting anything.

## Confirmed Cavalier ship-class requirement (owner, October 15, 2026)

Canonical details: [Cavalier Legendary Capital Ship](Art/Ships/CAVALIER_LEGENDARY_CAPITAL_SHIP_2026-10-15.md).

- The Cavalier is a distinct ship class and must be the **largest ship in ELITEWAKE, larger than the Brigantine**. Keep the Brigantine as its own class; do not replace it or simply scale its mesh.
- Give the Cavalier a high-definition, class-specific design with a distinct silhouette, detailed hull and decks, convincing physically based materials, timber/metal/rope/rigging detail, and readability close up and at gameplay distance. This requires actual asset creation and integration, not concept art alone.
- Follow the modular sail rule: base hulls have no permanently integrated sails; removable sail assemblies include masts/poles, flags mounted on poles, sail cloth, rigging, and attachment details.
- Exact dimensions and gameplay stats (crew, cannons, cargo, speed, durability, draft, cost, unlock tier) remain TBD until approved. Do not invent balance values or assume the biggest ship must dominate every statistic.
- Inspect existing ship assets, class data, shipyard recipes, module architecture, and shared design rules before implementation. Preserve existing gameplay and user assets. Track concept art, 3D asset creation, integration, and in-game verification as separate milestones; never claim completion without evidence.

## Cavalier three-level deck requirement (owner-confirmed, October 15, 2026)
The Cavalier must have **three traversable levels**, not two: (1) upper deck, (2) a separate deck directly below it, and (3) a lower interior deck/floor reached by ladder from the level above. The levels must be distinct in the reference design and actual 3D layout, with usable ladder openings, headroom, collision, structural supports, lighting, and character navigation. Exact room uses and weapon placements remain TBD unless approved. Canonical spec: `Art/Ships/CAVALIER_LEGENDARY_CAPITAL_SHIP_2026-10-15.md`.

## Regional resources, six-view reference sets, and sulfur ore (owner-confirmed, October 16, 2026)

**Reference index and target paths:** `Art/Reference/README.md`. The index distinguishes required destinations from files that have actually been committed.

Canonical resource plan: `Design/World/RESOURCE_DISTRIBUTION_AND_SIX_VIEW_ASSET_PLAN_2026-10-16.md`.

- Apply the approved regional resource distributions and tiers in that document. Regional primary trees remain Winter = Birch, Jungle = Ash, Desert = Palm, Swamp = Spruce, Central Plains = Oak.
- Critical correction: the desert resource is **sulfur ore**, not a generic sulfur deposit. It must be mineable with the existing **Metal Pick or a higher-tier pick**, not gated specifically behind an Iron Pick. Inspect the canonical tool/item catalog and reuse its exact item ID/tier logic; if no Metal Pick exists, report the gap rather than silently substituting another tool or inventing a duplicate.
- Produce six reference views of the same exact resource asset (front, back, left, right, top, underside) for all resources/materials/harvestables in the approved plan and other resources explicitly discussed in the project conversation. Follow existing repository conventions; intended reference location is `Art/Reference/Resources/<ResourceAssetName>/`.
- Preserve current inventory/crafting menu icons. Reference images do not by themselves implement meshes, textures, harvesting, recipes, or runtime behavior.

## Animal asset, animation, and audio requirements (owner-confirmed, October 16, 2026)

Canonical requirements: `Art/Animals/ANIMAL_MODEL_ANIMATION_AUDIO_REQUIREMENTS_2026-10-16.md`.

- Claude must inspect the current animal catalog and follow the canonical animal document before changing or creating animal assets. Use the actual existing/approved species; do not invent an animal list or omit current species.
- Create six consistent views per animal (front, back, left, right, top, underside). Intended reference location: `Art/Reference/Animals/<AnimalName>/`. Keep species anatomy, coloration, markings, proportions and silhouette consistent across all views and the production model.
- Every animal needs a species-appropriate idle/standing animation, walk animation, sprint/run animation, and relevant attack/action animations such as pawing/swiping, biting, jumping/pouncing, charging, kicking or pecking as appropriate to that species. Include usable transitions and follow existing movement/rig conventions.
- Every animal needs species-appropriate audio for idle/standing, walking, running/sprinting, and attacks/actions, with variation, sensible cooldowns, appropriate spatialization/attenuation, and licensing provenance for sourced sounds. Intended audio location: `Audio/Animals/<AnimalName>/`, unless the repository already has a canonical location.
- Audit first and report existing versus missing references, models, animations, and audio. Do not claim files or integration exist until verified. Keep image references, production assets, Unreal import/integration, and in-game verification as separate milestones.

## Latest ship/art authority — October 18, 2026
The owner's newer [ship proportions and hardpoints](Docs/OwnerDecisions/SHIP_PROPORTIONS_AND_MODULAR_SAIL_HARDPOINTS_2026-10-18.md) and [queued sailing rules](Docs/OwnerDecisions/SAIL_SPEED_WIND_AND_CODEX_PRIORITY_2026-10-18.md) supersede older conflicting text above. Cavalier is comparable in overall size to Brigantine with three traversable levels; preserve a distinct design. Sloop has lower-deck access but no captain's quarters. Base hulls have empty sail hardpoints; removable sail assemblies include their masts/poles and carry no flags. Stern boarding ladders are centered. Preserve approved shipyard tiers, captain's-quarter and helm placements. No scenery art in this pass.
The owner's current delegation authorizes ChatGPT to resolve remaining decisions, recorded as DECIDED (delegated) in [the decision record](Docs/REPORTS/2026-10-18_ChatGPT_Delegated_Decisions.md). These are reversible design choices, not in-engine implementation evidence. Preserve code ownership and the no-merge constraint.
