# ELITEWAKE — Starter Island: Central Plains
**Date:** 2026-10-15  
**Updated:** 2026-10-16  
**Status:** Confirmed owner direction

## Starter-island identity
The starter island belongs to the **Central Plains region** and must read visually as Plains. It is not a separate biome and should not primarily resemble the northern Winter, southern Swamp, eastern Desert, or western Jungle regions.

## Environment direction
- Preserve the current starter-island foundation—ocean/water, dock, terrain, and functioning gameplay—unless inspection and testing show a concrete reason to change it.
- **October 16 owner correction: Remove all palm trees from the starter island and replace them with realistic oak trees. Relocate palm-tree placement to Desert-region islands.** Do not leave palms on the starter island or reintroduce them via procedural spawning.
- Preserve tree harvesting, collision, resource yields, animations, and replication when changing species. Use oak-appropriate resources rather than palm-specific fronds/thatch where applicable.
- Desert-region islands should use palms in terrain-appropriate locations; retain their existing biome identity and other functional vegetation.
- Update all relevant level actors, foliage instances, procedural placement rules, setup scripts, and tests; do not merely change documentation. In particular, revise tests that currently expect palms on the starter island.
- Build a believable temperate plains environment with varied grass, open ground, natural stone outcrops, and a distinctive shoreline.
- Give the island its own silhouette, landmarks, and approach routes. Do not clone the same island layout across the world.
- Treat the starter island as the first playable test area for spawning, equipment, gathering, inventory, interaction, animation, and sound.
- Keep the title-screen specification distinct: moving ocean waves, centered silver ELITE WAKE lettering, and wave audio synchronized to visible water movement.

## Acceptance criteria
- The island clearly reads as Central Plains and has **zero palm trees**, including procedurally spawned palms.
- The starter island has realistic, terrain-aware **oak trees**, which can be harvested and collide correctly.
- Desert islands contain palm trees, appropriately distributed for their terrain.
- Its coastline and landmarks are recognizable and distinct.
- Existing working water, dock, and tree gameplay remain functional.
- Automated verification reflects the new regional tree assignment and passes in Unreal Play tests.
- The island supports the first playable core-survival test loop.
