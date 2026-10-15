# ELITEWAKE — New Original Image Production Plan
**Date:** 2026-10-15  
**Status:** Owner direction confirmed; asset-by-asset production and review required.

## Owner direction
The owner means the GitHub repository itself. Create new, original visual assets for the project broadly—not screenshots of the workspace. Keep generated source artwork, prompts, and catalog metadata in the repository so the project and coding agents can use them.

## Repository baseline
The current Art/README.md says the artwork catalog indexes 179 images and distinguishes references, pending-model inputs, generated Unreal drafts, current UI art sources, and legacy art. Existing files are not automatically approved final assets. Preserve provenance and do not silently overwrite source artwork.

## Production scope
Work through these categories in manageable batches:
1. **Title screen and menus:** ocean/wave background, single-player pirate battle key art, multiplayer-coming-soon key art, menu backgrounds and state variants.
2. **Environment and biomes:** island/coast, ocean/water, dock, rocks, mountain silhouettes, winter mountains, caves, ledges, cave walls, crystals/gem deposits, treasure sites and chests; biome-specific vegetation and ground materials.
3. **Items and tools:** hatchet, pickaxe, climbing pick, shovel, waterskin, torch, mined resources, gems, treasure maps and loot-container imagery.
4. **Creatures and wildlife:** giant spiders and regional fauna; preserve species identity and use consistent scale, lighting, camera angle, and background treatment for modeling references.
5. **Flora and harvestables:** trees, plants, berries, herbs, mushrooms, crops and growth-stage references, with species correctness reviewed before approval.
6. **Inventory/UI icons and materials:** item icons, resources, equipment, storage/loot, crafting and interaction UI; keep icon silhouettes legible at small sizes and maintain one consistent visual language.
7. **Ships, sails, weapons and world props:** source images and concept sheets aligned to current owner-selected ship originals and existing design rules.

## Art direction
- Target grounded, high-fidelity pirate survival realism: believable materials, physically plausible shapes, readable silhouettes, coherent scale, consistent lighting, and region-specific color/material identity.
- Keep title/menu artwork compositionally useful for UI overlays; do not bake UI text into background art unless specifically requested.
- Create clean, clearly named originals in appropriate Art/Concepts, Art/Environment, Art/Fauna, Art/Flora, Art/Items, and Art/UI locations. Keep prompts and metadata adjacent to the source assets and update Art/CATALOG.json through the existing catalog workflow.
- Concept images are references, not Unreal meshes or finished in-game assets. Track modeling, import, material setup, and runtime integration separately.
- Preserve existing working project content. Add new versions beside old versions, compare them, and replace runtime references only after review and explicit approval.
- Do not invent gameplay rules, species, recipes, resource distributions, item stats, or visual canon from artwork alone. Existing owner decisions and current design authority take precedence; unresolved details remain TBD.

## Batch workflow / definition of done
For each batch:
1. Inventory the current asset and where it is used.
2. Generate original artwork and save the image plus its prompt/metadata.
3. Check anatomy, material plausibility, readability, consistency, and match to current design decisions.
4. Update the art catalog and identify the intended Unreal destination/use.
5. Import or integrate only when the necessary binary asset and project access are available.
6. Report created files, unresolved choices, runtime references changed, and validation performed.

## Immediate first batch
Begin with high-visibility and currently relevant visuals: title/menu art, the starter island's environment references, and a winter mountain/cave/giant-spider/mineable-gem/three-stage-treasure concept set. This connects the art refresh to the current playable starting area and the newly recorded owner direction.
