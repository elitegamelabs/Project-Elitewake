# ELITEWAKE — Metric Units, Island Count, and Sea Spacing
**Date:** 2026-10-15  
**Status:** Confirmed owner direction

## Metric system
Use the metric system for in-game world measurements and player-facing distance readouts. Use **meters (m)** for island spacing and travel distances. Avoid presenting imperial units as the normal gameplay unit system.

## Starter island and nearby islands
- The starter island is in the **Central Plains** region.
- Place **at least five other islands around the starter island** so the player has destinations to sail to.
- Keep these destinations separated by open sea; they should not read as one continuous landmass or as islands immediately touching the starter shoreline.

## Island-to-island sea gap
- The required gap is **at least 800 m and at most 2,000 m between every pair of islands**.
- Measure this as the shortest open-water gap between the islands' shorelines, not center-to-center distance. This makes the requirement reflect the actual sea crossing the player must sail.
- Check the gap between each island and every other island, not only each island's nearest neighbor. Adjust placement or shoreline shape if any pair falls outside the 800–2,000 m range.
- Use these values as world-layout constraints during procedural placement, hand-authored map layout, and validation tooling.
- Travel time can vary with vessel, speed, weather, and route; the spacing rule defines distance, not a guaranteed travel duration.

## World-region consistency
The wider world plan calls for five regions: **North — Winter; South — Swamp; East — Desert; West — Jungle; Center — Plains**. Preserve each region's identity and ensure the starter island is part of the central Plains region. The five-island minimum around the starter island is an explicit local requirement; do not treat it as a replacement for any broader region-wide island-count requirement.

## Validation checklist
- [ ] Gameplay distance units and distance UI use meters.
- [ ] Starter island is assigned to Central Plains.
- [ ] At least five other islands are placed around the starter island.
- [ ] Every island pair's shortest shoreline-to-shoreline open-water gap is 800–2,000 m.
- [ ] Island layout still provides distinct silhouettes, shorelines, landmarks, and approach routes.
- [ ] Playtest sailing between islands and confirm the gaps create meaningful travel.

## Implementation note
These requirements document the intended design. They do not claim that the current Unreal map has already been measured, adjusted, or tested. Implement the layout in Unreal and validate actual shoreline distances before marking it complete.
