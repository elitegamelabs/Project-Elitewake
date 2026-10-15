# ELITEWAKE — Port Terminology and Regional Port Design
**Date:** 2026-10-15  
**Status:** CONFIRMED owner direction

## Project-wide terminology
Replace the current project term **Village/Villages** with **Port/Ports** in current authoritative documentation, player-facing text, UI, NPC/vendor descriptions, quest/onboarding text, asset labels, and future implementation work. This supersedes older current-design wording such as “Village” or “Free Port.” Do not blindly rename code symbols or Unreal assets: inspect dependencies and serialized references, migrate safely, preserve save compatibility, and test. Historical archives may retain original wording as historical evidence, but must not be treated as current terminology.

## Regional ports
Create **one port in each of the five regions**:
- North — Winter
- South — Swamp
- East — Desert
- West — Jungle
- Center — Plains

This means five regional ports, not a port on every island. The separate world direction calls for at least five islands per region, with varied silhouettes/coastlines and coves on some islands. The exact island assigned to each port, coordinates, routes, names, vendor roster, building counts, and safe-zone boundaries remain TBD unless separately approved.

## Port architecture and appearance
Each location must read as a functioning coastal port, not a generic inland village. Use high-definition, believable stone architecture with convincing geometry, masonry, material response, scale, weathering, and lighting consistent with ELITEWAKE’s grounded pirate-survival art direction.

Include a varied mix of:
- Stone buildings that contain vendors or other port services in some locations/structures.
- Plain stone structures, including walls and defensive/boundary elements, that do not contain vendors.
- Suitable waterfront infrastructure such as docks, piers, stairs, paths, retaining walls, and access points where the layout calls for them.

Not every structure should be a vendor building. Avoid identical rows of shops or copy-pasted port layouts. Vary silhouettes, layout, condition, height, detail, and regional character. Do not invent exact vendor services, names, or architectural restrictions as confirmed rules.

## Art and 3D assets are separate deliverables
Track concept/reference imagery separately from actual Unreal-ready models:
1. Original concept art for each regional port and its architecture.
2. Actual 3D models for stone buildings, plain walls, modular masonry, docks/piers, stairs, gates or other approved structures, vendor-building variants, and set dressing.
3. Materials/textures, appropriate collision, scale/origin conventions, LODs, and performance validation.
4. Asset catalog entries with intended use, provenance, and status (concept, model in progress, imported, tested, approved).

Use modular kits where useful while keeping each port recognizable. Concept images do not count as completed 3D models. Do not overwrite working Unreal assets or change runtime references without reviewing dependencies and testing.

## Acceptance checks
- Current authoritative text and player-facing content use Port/Ports rather than Village/Villages.
- One port exists in each of the five regions; ports are not required on every island.
- Each port reads as a port and uses high-quality stone architecture.
- Some stone structures contain vendors/services; others are plain structures such as walls.
- Each port has a distinct composition and regional identity.
- Concept art and actual 3D model files have separate tracked status.
