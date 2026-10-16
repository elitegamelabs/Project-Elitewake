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
