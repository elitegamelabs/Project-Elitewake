# Regional Resource Distribution and Six-View Asset Plan
**Owner-confirmed direction — October 16, 2026**

This document records the proposed resource ecosystem accepted by the owner. These are design requirements/proposals, not proof that gameplay, meshes, or images already exist.

## World regions and primary trees
- **North / Winter:** Birch is the primary tree.
- **West / Jungle:** Ash is the primary tree.
- **East / Desert:** Palm is the primary tree.
- **South / Swamp:** Spruce is the primary tree.
- **Center / Plains and starter islands:** Oak is the primary tree.

Every island must have its own terrain silhouette, coastline, coves, cliffs, beaches, elevations, hills, ridges, valleys, plateaus, landmarks, traversal routes, caves and resource distribution. Do not clone a single island template. Each island should contain plenty of its region's primary tree, placed in natural, terrain-aware clusters with varied density and clearings.

## Resource tiers
### Common resources
- Wood, branches, bark
- Stone, flint, gravel
- Sand, clay, soil
- Fresh water
- Fibers and common plant materials
- Berries, edible plants, medicinal herbs
- Common animal materials where appropriate (hides, fur, bones)

### Regional resources
- **Winter:** Birch wood, branches and bark; snow and ice; fresh water; iron ore; coal; exposed stone; animal hides, fur and bones.
- **Jungle:** Ash wood, branches and bark; vines, fibers and large leaves; medicinal herbs and wild fruits; clay and river stones; copper ore; green gemstones; resin and exotic plants.
- **Desert:** Palm wood, fronds and fibers; coconuts and other palm products; sand, sandstone and clay; copper ore; iron ore; salt; sulfur ore; amber-colored gemstones.
- **Swamp:** Spruce wood, branches and resin; peat and rich organic soil; reeds and rushes; clay and bog iron; mushrooms, moss and medicinal plants; dark gemstones in submerged caves.
- **Central Plains:** Oak wood, branches and bark; common stone, flint and gravel; clay, sand and soil; berries, edible plants and medicinal herbs; basic iron and copper ore; fresh water and common animal materials.

### Rare / exploration resources
- Gemstones and unusual cave minerals with regional visual identities.
- Rare crafting ingredients and treasure-related materials in dangerous locations.
- Cave resources should be tied to actual geology and biome rather than scattered as identical deposits everywhere. Mountain and cavern islands can provide advanced materials, with giant spiders guarding some cave systems as already specified elsewhere.

## Important sulfur correction
**Use mineable SULFUR ORE, not a generic “sulfur deposit.”** The player must be able to mine the sulfur ore using the **Metal Pick or a higher-tier pick**. Do not require an Iron Pick specifically. Before implementation, inspect the existing tool/item catalog to use the exact canonical Metal Pick item ID and existing tool-tier logic; do not create a duplicate tool or invent a new tier if one already exists. If the game has no canonical Metal Pick yet, document that gap for owner review instead of silently substituting Iron Pick.

## Six-view reference sets
Create a six-image reference set for every resource/material/harvestable item named in this document and for every additional resource item explicitly discussed in the current project conversation. Six views must depict the **same exact asset**:
1. Front
2. Back
3. Left
4. Right
5. Top
6. Underside

Use consistent scale, neutral studio/background treatment, realistic material response, clear silhouette, and useful detail. For ore and rock assets, show believable mineral inclusions, fracture, roughness and scale. For wood, bark, branches, leaves, fibers, plants and harvested items, show the correct surface, grain, leaf structure and shape. The views must not be six different variants.

Suggested repository layout:
- `Art/Reference/Resources/<ResourceAssetName>/front.png`
- `Art/Reference/Resources/<ResourceAssetName>/back.png`
- `Art/Reference/Resources/<ResourceAssetName>/left.png`
- `Art/Reference/Resources/<ResourceAssetName>/right.png`
- `Art/Reference/Resources/<ResourceAssetName>/top.png`
- `Art/Reference/Resources/<ResourceAssetName>/underside.png`

Use repository naming conventions if an established asset/reference folder already exists; inspect before creating duplicate directory structures. Keep current inventory/crafting menu icons unchanged. Reference images do not replace production 3D meshes, textures/materials, collision, resource nodes, harvesting logic, or in-game validation.

## Progression and distribution rules
- Common materials should be obtainable early, especially around the central Plains starter island.
- Regional resources should motivate travel and trade between islands.
- Rare resources should reward exploration and carry appropriate traversal/combat risk.
- Avoid making every island within a region identical. Vary the quantities, terrain accessibility, cave layouts, and resource combinations island by island.
- Preserve existing resource/item IDs and recipes where possible; inspect the current catalog before adding new IDs or duplicates.
- Treat this document as accepted design direction, not implementation proof. Track documentation, reference generation, 3D asset creation, gameplay integration, and verification as separate statuses.
