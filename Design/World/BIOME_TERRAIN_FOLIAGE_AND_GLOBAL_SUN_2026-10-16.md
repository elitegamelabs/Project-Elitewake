# ELITEWAKE biome terrain, foliage and global sun

Implementation requirements for Claude, Codex and other ELITEWAKE production agents. Preserve existing game systems and prior world design documentation.

## Desert
Use sand and sandstone as dominant surfaces. Include irregular natural sand dunes, occasional tall sandstone or sand pillars, rocky transitions, and varied heights. Dunes and pillars are permitted on **any island** where they fit local geography, not restricted to the Desert region; avoid making every island identical.

## Swamp
Dark brown to very dark brown saturated muddy terrain, peat, puddles, marsh sediment, uneven wet ground, moss, and appropriate muddy shoreline transitions. Wetness and ground roughness should read clearly.

## Jungle
Dense bushes, grass of varying heights, abundant trees, understory plants, flowers, and layered foliage across the landscape, with navigable paths and performance-aware density. **Tree species conflict to resolve:** earlier confirmed assignment was **ash** for Jungle; latest spoken request says **birch** in Jungle. Do not silently overwrite this choice: request confirmation before changing Jungle's primary tree species. Winter remains birch unless revised.

## Winter
Snow-covered ground, trees, rocks, hills, and landscape surfaces with natural variation and believable exposure; preserve navigability and distinguish ice from snow.

## Central Plains
Sunny, lush green terrain with healthy grasslands, oak trees, varied groundcover and rolling hills.

## World sun
Use one coherent world-space sun direction and position across the connected world rather than independently positioned suns per island. Keep sunlight orientation consistent across all regions; use biome-specific atmospheric, fog, weather and material treatments to communicate regional identity without conflicting sun directions. Whether time-of-day is fixed or globally synchronized must be decided before implementation; do not assume separate clocks per biome.

## Production
Build region-specific landscape material layers and blending, sensible foliage scattering and LODs, and avoid destructive changes to existing maps or gameplay. This file is a design specification; no terrain, materials, foliage, or lighting assets are claimed to be implemented.