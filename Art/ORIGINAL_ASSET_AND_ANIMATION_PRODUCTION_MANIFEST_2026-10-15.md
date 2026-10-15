# ELITEWAKE Original Art and Animation Production Manifest
**Date:** 2026-10-15  
**Purpose:** Track original visual production separately from actual model, animation, and Unreal implementation files.

## First generated concept board
A new original ELITEWAKE concept-board image was generated in this conversation. It depicts the five-region world layout, five regional stone ports, mountain caves and treasure, biome concepts, creature examples, port architecture, tools/resources, ships, character silhouettes, animation thumbnails, and 3D asset preview tiles.

**Status:** Concept/reference image generated; not yet committed as a binary file in this repository. The available GitHub repository actions in this session create/update UTF-8 text files; no working binary upload action was available. Do not treat this board as a set of finished individual assets, animation clips, or 3D models.

## Production rule
Create original assets specifically for ELITEWAKE. Track these deliverable types independently:
- **Concept image:** visual direction only.
- **Production image/texture/UI icon:** a usable source image with defined dimensions, format, transparency, and intended in-game use.
- **3D model:** actual mesh file(s), materials, UVs, collision, scale/origin, LODs, and import validation.
- **Animation:** actual animation data or a rigged source animation that can be imported into Unreal Engine; a static image or storyboard is not an animation.
- **Unreal implementation:** imported assets wired to the correct Blueprint/C++ systems, tested in context.

## Initial asset worklist
### World and environments
- Five regional biome environment sets: Winter (north), Swamp (south), Desert (east), Jungle (west), Plains (center).
- At least five distinct islands per region, with varied silhouettes and shorelines; coves on some islands, not all.
- Distinct regional ports with high-definition stone architecture, some vendor buildings, plain walls, docks, piers, stairs, gates, and site-specific set dressing.
- Mountain-side cave entrances, climbable ledges, cave interiors, region-specific gems, giant spiders, and the three-stage treasure-dig encounter.

### Characters, creatures, and animations
- Player and NPC base rigs, skeleton compatibility, and animation retargeting plan.
- Locomotion: idle/breathing, walk, jog/run, sprint, jump, fall, land, crouch, prone/crawl, swim/tread water.
- Tool actions: hatchet chopping, pickaxe mining, plant gathering, shovel digging, climbing-pick traversal, eating/drinking, placing objects, crafting, and harvesting feedback.
- Combat and survival: melee attacks, blocks/parries if approved, hit reactions, firearm equip/aim/fire/reload, medical treatment, and patient reactions.
- Ship actions: helm, sails, anchor, cannons, repairs, and other interactions already specified in the Systems Bible.
- Each action requires actual animation data, appropriate first-/third-person presentation, gameplay triggers, and synced audio/VFX where applicable.

### Tools, props, ships, and interface
- Hatchet, pickaxe, waterskin, torch, shovel, climbing pick, resource nodes, gems, storage chest, and placement/building props.
- Ships and boats, sails, ship modules, dock equipment, crates, barrels, vendor props, and regional set dressing.
- Original UI icons, inventory/crafting imagery, prompts, HUD and title/menu artwork.

## Next implementation sequence
1. Commit individual original concept/production images and 3D model source files through a binary-capable Git workflow.
2. Create/import one small tested vertical slice before scaling production: starter island, core tools, wood/stone/water gathering, and synchronized harvesting/use/place sounds.
3. Add asset catalog entries and status tracking for every source file.
4. Import rigged animation clips into Unreal, connect animation state machines and interaction notifies, then test in first and third person.
5. Verify builds and references after each small batch. Do not claim assets are integrated until tested.

## Current limitation
This manifest is documentation, not the binary asset payload. The generated concept-board image has not been pushed to GitHub from this session. The repository needs a binary-capable upload path (for example, a local Git checkout and push, Git LFS where appropriate, or an enabled binary-capable connector) to commit image/model/animation files.
