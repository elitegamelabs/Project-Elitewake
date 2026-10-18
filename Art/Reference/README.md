# Six-View Reference Asset Index

**Owner direction recorded October 16, 2026.** This index tracks intended six-view image sets. A listed target folder or filename is a destination specification, not proof that image files exist. Never mark a set complete until all six image files have been committed and visually checked.

## Resource references

Canonical design and coverage: [Regional Resource Distribution and Six-View Asset Plan](../../Design/World/RESOURCE_DISTRIBUTION_AND_SIX_VIEW_ASSET_PLAN_2026-10-16.md).

For every resource, material, plant/harvestable and animal-derived material listed in that plan, create one folder:
`Art/Reference/Resources/<ResourceAssetName>/`

Required filenames:
- `front.png`
- `back.png`
- `left.png`
- `right.png`
- `top.png`
- `underside.png`

At minimum, the resource inventory covers:
- **Wood/tree materials:** Oak Wood, Oak Branches, Oak Bark; Birch Wood, Birch Branches, Birch Bark; Ash Wood, Ash Branches, Ash Bark; Palm Wood, Palm Fronds, Palm Fibers; Spruce Wood, Spruce Branches, Spruce Resin.
- **Rock/mineral resources:** Stone, Flint, Gravel, Iron Ore, Coal, Copper Ore, Bog Iron, Sandstone, Sulfur Ore, Salt, blue-white crystals, green gemstones, amber-colored gemstones, dark gemstones, other approved cave gemstones/minerals.
- **Ground/water/materials:** Sand, Clay, Soil, Peat, Fresh Water, Ice, Snow.
- **Plant resources:** Fibers, Vines, Large Leaves, Reeds, Rushes, Moss, Mushrooms, Medicinal Herbs, Exotic Plants, Resin, Berries, Edible Plants, Wild Fruits, Coconuts, other approved palm products.
- **Animal materials:** Hides, Fur, Bones, and other existing approved animal harvest products. Inspect the current item catalog for canonical item names and IDs before finalizing names or adding duplicate references.

## Sulfur Ore special rule

The asset is **Sulfur Ore**. It is a mineable ore node, not a generic sulfur deposit. The player must be able to mine it with the existing **Metal Pick or a higher-tier pick**. Do not make an Iron Pick a specific prerequisite. Confirm the canonical Metal Pick item ID and tool-tier logic in the current catalog. If missing, report the gap; do not silently substitute.

## Animal references

Canonical requirements: [Animal Models, Six-View References, Animations, and Audio](../Animals/ANIMAL_MODEL_ANIMATION_AUDIO_REQUIREMENTS_2026-10-16.md).

Target location:
`Art/Reference/Animals/<AnimalName>/`

Use the exact existing species name and folder/file naming conventions. Required filenames for each animal are the same six views listed above.

Current six implemented land-animal prototypes have an existing starting reference roster in `Art/Wildlife/Turnarounds/README.md`:
- American alligator
- Flamingo
- Brown pelican
- Cottonmouth snake
- Tortoise
- Squirrel monkey

Existing named concept references are under `Art/Concepts/Animals/2026-10-12/`; the roster is `Art/Concepts/Animals/2026-10-12/roster.json`. These are source references, not proof that dedicated high-resolution six-view sets have been committed.

Additional habitat-directed animals include Horse (Plains), Snow Leopard (Winter), and Giant Spider (dangerous caves). Check the current approved roster and runtime catalog before deciding which further candidate concept species are in scope.

## Status checklist

- [ ] Resource list cross-checked against the canonical item catalog.
- [ ] Six separate images committed for each resource.
- [ ] Six separate images committed for each in-scope animal.
- [ ] Every set visually checked for consistent identity, scale, surface details and matching anatomy across views.
- [ ] Images cataloged in `Art/CATALOG.json` using the existing catalog workflow.
- [ ] Existing inventory/crafting menu icons preserved unchanged.

Do not create fake placeholder PNGs, empty files, or misleading status markers to make the checklist look complete. If image generation or binary upload is unavailable, keep the set marked pending and report the blocker.

## Ship references — October 18, 2026

Eleven concept sheets generated with built-in image generation and visually reviewed. Prompt sheets include six camera lines and attachment detail. Separate validated orthographic files, deployment states, meshes, animation and integration remain pending. No scenery generated.

- [DinghyRailing](Ships/DinghyRailing/ConceptSheet-v1.png) — [prompts](Ships/DinghyRailing/PROMPTS.md), [provenance](Ships/DinghyRailing/generation.json).
- [LargeRectangularSail](Ships/LargeRectangularSail/ConceptSheet-v1.png) — [prompts](Ships/LargeRectangularSail/PROMPTS.md), [provenance](Ships/LargeRectangularSail/generation.json).
- [LargeWeightedSail](Ships/LargeWeightedSail/ConceptSheet-v1.png) — [prompts](Ships/LargeWeightedSail/PROMPTS.md), [provenance](Ships/LargeWeightedSail/generation.json).
- [MediumRectangularSail](Ships/MediumRectangularSail/ConceptSheet-v1.png) — [prompts](Ships/MediumRectangularSail/PROMPTS.md), [provenance](Ships/MediumRectangularSail/generation.json).
- [MediumWeightedSail](Ships/MediumWeightedSail/ConceptSheet-v1.png) — [prompts](Ships/MediumWeightedSail/PROMPTS.md), [provenance](Ships/MediumWeightedSail/generation.json).
- [PlainRailing](Ships/PlainRailing/ConceptSheet-v1.png) — [prompts](Ships/PlainRailing/PROMPTS.md), [provenance](Ships/PlainRailing/generation.json).
- [SmallRectangularSail](Ships/SmallRectangularSail/ConceptSheet-v1.png) — [prompts](Ships/SmallRectangularSail/PROMPTS.md), [provenance](Ships/SmallRectangularSail/generation.json).
- [SmallWeightedSail](Ships/SmallWeightedSail/ConceptSheet-v1.png) — [prompts](Ships/SmallWeightedSail/PROMPTS.md), [provenance](Ships/SmallWeightedSail/generation.json).
- [SurgeonTable](Ships/SurgeonTable/ConceptSheet-v1.png) — [prompts](Ships/SurgeonTable/PROMPTS.md), [provenance](Ships/SurgeonTable/generation.json).
- [SurgeonTools](Ships/SurgeonTools/ConceptSheet-v1.png) — [prompts](Ships/SurgeonTools/PROMPTS.md), [provenance](Ships/SurgeonTools/generation.json).
- [TwoCannonRailing](Ships/TwoCannonRailing/ConceptSheet-v1.png) — [prompts](Ships/TwoCannonRailing/PROMPTS.md), [provenance](Ships/TwoCannonRailing/generation.json).

## G4 animal prompts — October 18
[Bear](Animals/Bear/PROMPTS.md), [Lion](Animals/Lion/PROMPTS.md), [Giant Crocodile](Animals/GiantCrocodile/PROMPTS.md), [Elephant](Animals/Elephant/PROMPTS.md): prompts written; generated concept-sheet status is recorded beside each asset. Six separate validated view files, models and integration remain pending until individually checked. Latest habitat correction and existing reference identity preserved.

## Resource/material prompt coverage — October 18
[53 reference sample prompt sets](Resources/REFERENCE_COVERAGE_2026-10-18.md) prepared. Each has a shared identity and six camera suffixes. Actual PNG completion is recorded only in local generation.json; a prompt folder is not an image set. Sulfur remains ore requiring Metal Pick or higher; canonical tool-ID gap documented. No scenery or inventory/crafting icons replaced.


## Expanded delivery status — October 18
77 additional retained reference PNGs, with per-image metadata and limitations. See [delivery and outstanding work](../../Docs/REPORTS/2026-10-18_ChatGPT_Expanded_Delivery.md). Animal six-view files exist; exact projection and cross-view geometry remain pending. Deployment sheets are illustrative. Prompt coverage is not PNG completion.
