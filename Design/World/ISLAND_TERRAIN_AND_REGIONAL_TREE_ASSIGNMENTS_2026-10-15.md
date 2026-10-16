# ELITEWAKE Island Terrain Diversity and Regional Tree Assignments
Date: 2026-10-15
Status: CONFIRMED owner direction

## World-generation rule: every island must be individually designed
Every island in ELITEWAKE must have its own terrain identity. Do not generate a set of islands that are merely resized or rotated copies of one template. Across the world, vary:
- Overall island size and footprint.
- Silhouette, coastline, bays, coves, beaches, cliffs, and shoreline approaches.
- Elevation profiles, including different combinations of mountains, hills, ridges, valleys, plateaus, and flatter ground.
- Mountain shapes, heights, slopes, and placement.
- Cavern and cave entrances, placement, scale, layout, and relationship to surrounding terrain.
- Tree placement, density, clearings, forest edges, and the way vegetation follows the terrain.
- Distinctive landmarks and traversal routes.

Each island should feel geographically plausible and recognizable from the sea. Terrain should shape exploration and routes on foot; caves and elevation changes should feel integrated into the land rather than pasted onto a flat surface. Not every island must contain the same exact mix or amount of features, but every island must be deliberately varied and identifiable.

## Regional tree assignments
Use these owner-approved primary tree types for the regions:

| Region | Primary tree type |
| --- | --- |
| Winter | Birch |
| Jungle | Ash |
| Desert | Palm |
| Swamp | Spruce |
| Central Plains islands | Oak |

The Winter assignment is **Birch**, correcting the earlier mention of spruce for Winter. Spruce belongs to the Swamp region in the current decision. Oak is the primary tree type for the central Plains islands.

## Forest density and distribution
- Include quite a few of the region's assigned trees on islands; forests and substantial stands should be visible, not just occasional isolated trees.
- Distribute trees in terrain-aware groups, with natural variation in density, spacing, clearings, and forest boundaries.
- Let slopes, cliffs, wetlands, dunes, valleys, and other terrain features influence where trees can grow.
- Preserve visual variety between individual islands while keeping the assigned regional tree identity readable.
- These assignments identify the primary regional tree type; they do not silently prohibit other vegetation where the design calls for it. Any additional species should support the region's identity rather than obscure it.

## Implementation guidance
- Apply the rule to every island, including the starter island and future islands.
- Use data-driven island and foliage definitions where practical so terrain and vegetation can be configured without duplicating logic.
- Keep island-specific terrain layouts and foliage placement distinct; do not assume a shared terrain stamp or identical cave layout across a region.
- Preserve existing gameplay systems and project assets unrelated to world generation.
- Treat this document as a world-design requirement, not proof that the island terrain or tree assets have already been implemented in Unreal Engine 5.8.

## Acceptance criteria
1. Every island has a distinct combination of size, shape, coastline, elevation, and terrain features.
2. Islands use varied mountains, hills, valleys, and cave/cavern layouts where appropriate; these features are integrated into traversal and exploration.
3. Winter islands use Birch as the primary tree type.
4. Jungle islands use Ash as the primary tree type.
5. Desert islands use Palm as the primary tree type.
6. Swamp islands use Spruce as the primary tree type.
7. Central Plains islands use Oak as the primary tree type.
8. Each island has substantial, terrain-aware tree distribution rather than sparse token trees.
9. The world remains recognizable by region while individual islands remain visually distinct.
