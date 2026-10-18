# ELITEWAKE — Crystal and Coal Mining Rules
Date: 2026-10-18
Status: Owner-approved design specification; implementation not yet verified
Engine: Unreal Engine 5.8.3

## Resource placement
- Ruby (red): crystal nodes protruding from cave walls, caves in every region.
- Sapphire (blue): crystal nodes protruding from cave walls, caves in every region.
- Emerald (green): crystal nodes in caves in every region; additionally exposed deposits at multiple locations across mountains in winter regions (mountainsides, rocky slopes, cliffs, rock outcrops), not only summits.
- Obsidian (black, visually distinct from coal): cave deposits in every region.
- Coal ore (black): exposed deposits at multiple locations across mountains in winter regions only; not in caves or non-winter regions.

Mountain placement refers to natural mountains, not freestanding geographic rock pillars. Do not restrict winter mountain deposits to mountaintops.

## Harvesting
- Minimum tool: metal pickaxe; higher-tier pickaxes permitted.
- Each fully harvested node yields 4–8 units of its corresponding resource.
- Each depleted node respawns after one hour (60 minutes).
- Apply these shared harvesting rules to all five resource types.

## Implementation handoff to Claude
Implement resource-specific spawn filters, harvesting requirements, variable drops, and per-node respawn timers in Unreal Engine 5.8.3. Ensure server-authoritative harvesting and respawns in multiplayer, avoid inaccessible placements, and validate cave and winter mountain distributions. Do not replace existing systems or modify scenery beyond what these mineable nodes require. This file documents requirements only; it does not claim gameplay or assets are implemented.
