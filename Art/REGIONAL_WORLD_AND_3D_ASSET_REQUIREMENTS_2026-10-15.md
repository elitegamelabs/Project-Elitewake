# ELITEWAKE — Regional World Layout, Island Diversity & 3D Asset Requirements
**Date:** 2026-10-15  
**Status:** CONFIRMED owner direction; detailed island count above minimum remains flexible.

## Confirmed world layout
The owner has explicitly set the world regions to:
- **North:** Winter region
- **South:** Swamp region
- **East:** Desert region
- **West:** Jungle region
- **Center:** Plains region

Provide **at least five islands in each region**. More than five may be used when needed for meaningful exploration, navigation, resource geography, and gameplay variety. Five is the minimum per region, not the total island count. With five regions, the minimum implied count is 25 islands.

The consolidated guide previously listed the directional arrangement and island count/distribution as recommended or TBD. This newer explicit owner direction supersedes that uncertainty for the five-region layout and the minimum island count. Do not leave these decisions marked TBD.

## Island individuality and coves
Islands must not look like copies of one another. Each island should have a distinct overall silhouette and readable identity from offshore, supported by combinations of:
- Shoreline shape, elevation, cliffs, beaches, headlands, bays, and coves
- Inland terrain, ridges, valleys, plateaus, rock formations, and vegetation distribution
- Landmark placement and skyline
- Distinct combinations of resource nodes, harvestables, wildlife, points of interest, and approach hazards consistent with its biome
- Different sheltered and exposed landing approaches

**Some islands should contain coves; not every island needs one.** Coves should vary in width, depth, enclosure, shoreline material, and navigability. Where appropriate, they can create sheltered anchorages or concealed approaches, but don't assume every cove is safe or navigable by every vessel. Exact dimensions, island coordinates, route spacing, and the number of coves are not specified and remain open for world-design review.

## Region visual identities
- **Winter / North:** snow and ice, cold-exposed coastlines, rugged high ground, mountain silhouettes, and cave entrances partway up mountains where the current cave design calls for them.
- **Swamp / South:** wet lowlands, marshy shorelines, pools and channels, boggy ground, dense moisture-loving vegetation, and varied waterlogged terrain.
- **Desert / East:** arid shorelines, sand and exposed stone, dry ridges, dunes or rocky desert landforms, sparse drought-adapted vegetation, and water-scarcity cues.
- **Jungle / West:** humid dense vegetation, layered canopy, varied cliffs and beaches, vines and roots, and obscured interior landmarks.
- **Plains / Center:** open grassland, rolling terrain, scattered tree groups, rock outcrops, rivers or ponds where suitable, and broad sightlines; it should not be a flat empty green plane.

These are visual direction guidelines, not permission to invent unapproved resource drop rules or exact biome distributions. Keep exact resource placement data-driven and mark unapproved assignments RECOMMENDED/TBD.

## Original 3D model and image pipeline
The asset refresh covers both **original concept/reference images and original 3D models**. They are different deliverables:
- Concept images establish appearance, silhouette, materials, and variants.
- 3D assets require actual mesh/model files, materials/textures, collision where needed, scale/origin conventions, LODs where appropriate, and Unreal import/integration.
- A generated concept image is not a 3D model and must not be reported as one.

Plan original, consistent 3D assets for:
1. Island landforms and reusable shoreline/cove/cliff/rock kits, plus region-specific terrain and vegetation.
2. Mountain cave entrances, ledges, cave interiors, mineable gem deposits, treasure dig sites, loot chests, and giant spiders.
3. Starter-island trees, rocks, dock, water-adjacent props, hatchet, pickaxe, waterskin, torch, shovel, and gatherable resource nodes.
4. Region-specific plants, trees, rocks, resources, wildlife, and landmarks.
5. Ships, sails, world props, inventory/UI artwork, and title/menu key art as scoped by the art-production plan.

Reuse modular pieces where it improves performance and production speed, but compose and dress islands differently so repeated modules do not make islands visually identical. Use procedural placement only with authored constraints and per-island variation, not as a substitute for distinct island design.

## Repository and implementation rules
- Keep source concept images, prompts, metadata, and model files in clearly named repository folders when the file sizes and Git workflow support them. Use Git LFS or the project's established large-binary asset workflow for large model/texture files.
- Maintain the art catalog and record each asset's intended Unreal destination, license/provenance, and status (concept, model in progress, imported, tested, approved).
- Preserve current working assets. Add candidate replacements beside old files; do not silently overwrite art or change runtime references before review.
- Unreal binary assets must be imported or modified through Unreal/editor-supported workflows; text-only GitHub file edits cannot create a valid Unreal mesh, material, or working world.
- Keep implementation staged: create a small asset batch, import, compile/build, test visuals/performance, checkpoint, then proceed.

## Acceptance checks
- The map clearly communicates the five confirmed cardinal/central regions.
- Every region contains at least five distinct islands.
- Island silhouettes and compositions are visibly varied; coves occur on some, not all, islands.
- Region identity is legible without relying solely on color.
- Concept images and actual 3D model files are tracked as separate deliverables.
- No existing gameplay or art is removed merely to make room for the new assets.
