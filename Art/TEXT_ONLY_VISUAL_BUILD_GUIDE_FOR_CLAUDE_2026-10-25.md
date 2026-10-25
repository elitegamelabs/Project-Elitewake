# Text-only visual build guide for Claude

**Purpose.** This guide records what the existing Elitewake pictures actually show so an implementation pass can proceed when image viewing is unavailable. It describes the named source assets, not a replacement art bible. Use it together with the linked image, its adjacent prompt/provenance, and current owner decisions. If a source image disagrees with an owner decision, follow the owner decision and record the mismatch. Do not describe a concept as an integrated Unreal asset.

**Standing rule (owner, October 25, 2026): every future visual design added to the repo must include a detailed text-only description that Claude can use without opening the image.** Put it beside the image or in a clearly linked per-asset brief. Include the exact filename; observed silhouette and construction; proportions and distinctive landmarks; palette and material/surface cues; camera/view and pose; required details and prohibited additions; consistency rules across views/variants; intended use (icon, concept, modeling reference, texture, or production asset); actionable modeling/material notes; source prompt/provenance; and status (concept, approved reference, model, imported, verified). Separate owner-approved requirements from suggestions and TBD values. If the image cannot be inspected or is only an LFS pointer, say so and record only supported facts. Do not leave images as unlabelled files or rely on the image itself to communicate instructions.

## How to use this guide

For each asset, check the exact file path below, then read its adjacent `generation.json`, `PROMPTS.md`, selection record, or canonical design document when present. Use this text as a visual fallback. Reconstruct the visible silhouette, construction, material, markings, and palette; do not add invented gameplay, dimensions, variants, or decoration. Keep the asset name/ID from the live catalog. A concept image is a visual target, not a mesh, rig, UV map, collision setup, recipe, or final balance value. Record concept, model, Unreal import, and in-game verification as separate states.

When an image only provides one angle, do not pretend unseen geometry is specified. Use real-world anatomy or believable period construction to fill only ordinary hidden details, and flag any consequential design choice for owner review. Keep the original images and their provenance intact.

## Shared visual language

The item-icon contact sheet (`Art/Items/Icons/contact-sheet.png`) shows isolated, small survival objects with transparent cutouts, a neutral dark studio ground, soft upper-left light, warm brown wood, rough fibers, muted iron, and readable silhouettes. Favor the same grounded, hand-made material family for inventory objects. Keep enough edge contrast for a 256-pixel icon. Do not bake a colored square background into a transparent inventory icon.

The raw food samples (`Art/Items/Raw-Meat-v1.png`, `Raw-Fish-v1.png`) are flatter, graphic symbols on colored fields. Treat them as legacy/placeholder identity cues, not the final photorealistic look for the game. In the 3D world, use believable food shape, surface response, and lighting consistent with the realistic environment; do not put the colored icon background on the model.

The boat originals use a clean studio cutout, raised three-quarter view, bow generally to image-left and stern to image-right, weathered brown timber with visible plank courses, end grain, ribs, joints, restrained dark iron fasteners, and believable hand construction. Interior pictures are separate layout concepts. Preserve the selected original set; `selection.json` and its exact generation prompts identify the canonical sources. Do not use excluded second variants as replacements.

## Berry and everyday resource images

| Source | What the picture shows | Build/design cue and boundary |
|---|---|---|
| `Art/Items/Icons/AzrenBerry-v1.png` | A small cluster of vivid cobalt-blue berries with round, slightly mottled skins, dark blossom scars, short stems, and several veined green leaves. | Keep the berry recognizable as the same blue fruit and keep its bush static. Berries are wild-only; do not add seed or planted growth stages. Winter bushes/berries receive snow dressing per owner direction, while the fruit identity remains readable. The icon does not specify a bush mesh or harvest quantity. |
| `Art/Items/Icons/SpoiledBerries-v1.png` | A darker, shriveled purple-black berry cluster, visibly older and less glossy than the fresh blue fruit. | Spoiled berries are inedible and toxic crafting material. Keep the visual “spoiled” through dull, collapsed skins; never imply that the player can eat them. |
| `Art/Items/Icons/Wood-v1.png` | Several short split logs stacked diagonally; pale freshly split faces contrast with irregular dark bark around the outer surface. | Inventory Wood is one generic resource. Do not make separate tree species into separate Wood stacks. Biome-specific trees remain visually distinct in the world, and the species rules live in `Design/World/ISLAND_TERRAIN_AND_REGIONAL_TREE_ASSIGNMENTS_2026-10-15.md`. |
| `Art/Items/Icons/Fiber-v1.png` | A loose, dry tan bundle of long fine strands gathered into a compact knot. | Model individual strands with uneven ends and soft fiber roughness; keep it visually distinct from the thicker straw-like Thatch bundle. |
| `Art/Items/Icons/Thatch-v1.png` | A thicker, golden-brown sheaf of stiff straw/reed-like pieces bound into a rough bundle. | Use coarse stalks and uneven cut ends. Do not make it look like fine rope or cloth. |
| `Art/Items/Icons/Sticks-v1.png` | Short crooked branches tied together with coarse cord; bark remains on most surfaces. | Keep sticks smaller and more irregular than the split-log Wood icon. |
| `Art/Items/Icons/Stone-v1.png` | One rough, asymmetrical gray rock with chipped edges and granular mottling. | Preserve a natural, non-geometric silhouette and consistent common stone appearance. This icon is not a mineable ore design. |
| `Art/Items/Icons/CopperOre-v1.png` | A lumpy rock with exposed orange-copper patches and blue-green weathering against the darker host stone. | Read as copper-bearing ore, not a clean copper ingot. The icon does not establish a mining tool gate; use the canonical item/tool catalog. |
| `Art/Items/Icons/Hide-v1.png` | Rolled, irregular brown hide with a rough outer surface and visible layered edge. | Use flexible organic thickness and uneven perimeter; do not turn it into finished leather unless that is a separate catalog item. |
| `Art/Items/Icons/WaterSkin-v1.png` | A squat, pear-shaped brown leather waterskin with a narrow neck, tied stopper, stitched seam, and looped carrying cord. | Keep it like a worn water container, not a glass potion bottle. Preserve the swollen leather silhouette and visible seam. |
| `Art/Reference/Resources/Berries/PROMPTS.md` and `Art/Reference/Resources/*/PROMPTS.md` | Six-view prompt text exists for resources; most required six-view PNGs are still explicitly marked pending in `REFERENCE_COVERAGE_2026-10-18.md`. | Do not report the six-view resource library complete from prompts alone. For species-specific wood references, preserve the resource rule above: those references guide tree species/material art, not separate inventory Wood types. |

## Other inventory and food images

- **WoodenAxe / WoodenPickaxe / WoodenShovel** (`Art/Items/Icons/WoodenAxe-v1.png`, etc.): rough carved wooden handles and simple stone-like working heads bound with cord. Keep silhouettes distinct: broad cutting wedge for the axe, transverse pointed head for the pick, and a broad flat blade for the shovel. The icon family is a starting visual; exact tool geometry/material tiers come from the item catalog.
- **StoneAxe / StonePickaxe**: coarse stone heads lashed to wood handles with visible fiber/cord wraps. The stone surfaces are irregular rather than machined. Tool eligibility is gameplay data, not implied by the picture.
- **Torch**: a narrow wooden shaft with wrapped fiber and a burning, ember-orange head. In the world, flames and illumination are separate runtime effects; do not flatten the glow into the mesh texture.
- **RepairKit**: a compact bundle of rough timber/stone repair supplies and cord. Its icon is symbolic; contents and repair rules remain in the game system.
- **ShipWheel**: circular wooden spokes and rim around a darker central hub, with restrained metal details. The inventory icon does not specify mounting dimensions.
- **Cannon / CannonAmmo**: the cannon icon is a dark iron barrel on a small timber carriage; the ammunition icon is two dark iron cannonballs. Treat these as separate, attachable ship components. Keep weapon counts and hardpoint rules in the ship/gameplay documents.
- **SmallSail / MediumSail / LargeSail**: the icons show folded or tightly furled tan canvas bundles, wrapped with rope. They are inventory silhouettes, not sails permanently attached to a hull. The separate ship-sail design files define the sail assemblies and deployment states.
- **Raw meat**: `Raw-Meat-v1.png` is a simple red steak-shaped graphic with pale fat edge/striation. The owner specifically chose a steak visual rather than a chicken leg. Develop a realistic cut of raw steak if replacing the icon; cooking state and edible stats are separate decisions.
- **Raw fish**: `Raw-Fish-v1.png` is a minimal pale fish-bone/silhouette mark on a salmon-colored square, not a detailed fish model. Match a species-specific fish mesh to the approved fish roster; do not infer species from this placeholder icon.
- Currency and other icons: use `Art/CATALOG.json` for exact names, atlas slots, and classification. The coin atlas is in `Art/Items/Currency/2026-10-14/`; its text/catalog entry is the source for coin identity, not a new currency rule.

## Ship silhouettes and construction cues

Canonical source files are in `Art/Concepts/Boats/2026-10-11/`; each class has an original exterior and a separate interior concept. Read `selection.json` for the exact prompt and hashes. The original models show the same hand-built timber language but have distinct outlines:

- **Raft** (`Raft-Exterior-Original-v1.png`): a low rectangular platform of thick parallel buoyant logs, cross-timbers and heavy rope lashings, with a flat open deck and low perimeter rails. Its primitive log construction is deliberate; do not convert it into a planked ship. Current raft scale is retained.
- **Dinghy** (`Dinghy-Exterior-Original-v1.png`): a small open clinker-built rowboat, tapered at both ends, with narrow plank strakes, exposed ribs, a few transverse thwarts, and no enclosed deck. It is not a miniaturized ship hull.
- **Sloop** (`Sloop-Exterior-Original-v1.png`): a compact, low-profile, single-hull working vessel with curved oak planking, visible ribs/iron straps, modest bow rise and a raised stern. It has below-deck access but no captain's quarters. The owner-directed scale target is about three raft-heights overall; it is a visual relationship, not a meter value.
- **Schooner** (`Schooner-Exterior-Original-v1.png`): a longer, taller hull than the sloop at approximately the same width, with a long open working deck, raised aft deck, empty structural gunports, and substantial stern framing. The captain's quarters occupy about one eighth of ship length across the full width; stairs rise on both sides and the helm is on top of those quarters.
- **Brigantine** (`Brigantine-Exterior-Original-v1.png`): wider and taller than the schooner, with a heavier hull, a line of empty gunports and distinct raised fore/aft deck structure. The captain's quarters are longer than the schooner's; the helm is inside them.
- **Cavalier** (`Art/Reference/Ships/Hulls/Cavalier/LayoutSheet-v1.png`): the named layout reference has prompt/metadata alongside it. The current owner spec makes Cavalier about the same overall size as the Brigantine, with three traversable levels and its own class design; captain's quarters match the Brigantine in length and the helm is inside. Do not substitute the older exploratory `Large-Multi-Deck` hull concept for the Cavalier.

**Every base ship is a bare hull.** Keep sail hardpoints, but remove fitted masts/sails from base-hull art. Cannons, railings/modules, diving and dinghy attachments, and decorations are separate build/attachment items under the latest ship design. Gunports in the originals are empty openings. Do not add flags to sail assemblies. The ship reference images are concepts, not collision-ready meshes or proof the ship has been imported.

## Animal image references

The concept roster is deliberately larger than the approved runtime roster. First check `Art/Concepts/Animals/2026-10-12/roster.json`, `Art/Animals/ANIMAL_MODEL_ANIMATION_AUDIO_REQUIREMENTS_2026-10-16.md`, `Art/Animals/ATTACK_AND_VOICE_MATRIX_2026-10-16.md`, and `Docs/OPEN_QUESTIONS_2026-10-15.md`. A concept image never approves a new species, habitat, count, combat rule, drop, or taming system. Use the named same-species picture as identity reference; use the following descriptions when the picture itself is inaccessible:

| Species/reference | Text-only identity cues for a modeler | Status boundary |
|---|---|---|
| American alligator (`american_alligator.png`) | Low, broad crocodilian body; long tapered muscular tail; short splayed legs; broad blunt snout; armored dorsal scutes. | Existing coastal prototype. Use the matrix for passive/aggressive behavior. |
| Flamingo | Tall wading bird; very long thin legs and neck; compact body; downward-curved bill; pink feather mass with darker flight-feather accents. | Existing prototype, but no flamingo turnaround PNG is present in the checked-in Art paths. `Art/Wildlife/Turnarounds/README.md` says the generated overview was not committed. Use real species anatomy until a reference sheet is added; do not add predator teeth or mammal-like growls. |
| Brown pelican | Large stocky seabird; long straight bill with hanging throat pouch; folded broad wings; webbed feet; brown/cream feather blocks. | Existing prototype, but no pelican turnaround PNG is present in the checked-in Art paths. `Art/Wildlife/Turnarounds/README.md` says the generated overview was not committed. Use the real species anatomy until a reference sheet is added. |
| Cottonmouth (`cottonmouth.png`) | Heavy-bodied, ground-hugging venomous snake; broad triangular head, keeled scales and dark crossbands; a pale open mouth can signal warning. | Existing prototype; no rattlesnake rattle or legs. |
| Tortoise (`desert_tortoise.png`) | Low domed shell with polygonal scutes, thick scaled limbs, blunt claws, short tail and beaked mouth. | Existing prototype; use dedicated Tortoise references and geometry notes; no new combat behavior by implication. |
| Squirrel monkey (`monkey.png`) | Small agile primate; golden-olive coat, pale face framing a dark muzzle/eyes, slender limbs and long curved dark-tipped tail. | Existing prototype; keep passive behavior unless gameplay authority changes. |
| Horse (`horse.png`) | Chestnut coat, black mane and tail, narrow white blaze, dark lower legs and sturdy natural equine proportions; neutral standing pose. | Approved Plains habitat; concept only, not a production model. |
| Snow Leopard (`snow_leopard.png`) | Stocky mountain cat with pale smoky-gray coat, dark rosette spots, broad paws, small rounded ears and very thick long ringed tail. | Approved Winter habitat; concept only, not a production model. |
| Bear (`black_bear.png`/`grizzly_bear.png`) | Heavy quadruped with deep chest, strong shoulders, dense brown-to-black fur, rounded ears, broad muzzle, large paws and short tail. Keep the selected bear subtype consistent per image. | Approved wildlife work; subtype/habitat source must be checked before use. |
| Lion (`lion.png`) | Powerful tawny big cat, deep chest, muscular shoulders and hindquarters, rounded ears, long tail with dark tuft, broad muzzle and feline paws. | Approved Plains region; do not invent mane/sex variants beyond the selected reference. |
| Giant crocodile (`crocodile.png`) | Olive-gray armored dorsal scutes with subtle dark bands, pale cream underside, broad crocodilian head, visible closed-jaw tooth pattern, four planted legs and long tapered tail. | Approved Southern Swamp reference; no final scale or balance value inferred. |
| Elephant (`elephant.png`) | Massive four-legged body; thick columnar legs; long flexible trunk; broad fan-shaped ears; wrinkled gray hide; tusks only as depicted in the selected source. | Latest correction places it in Western Jungle; exact behavior/size values remain governed by docs. |
| Cave/swamp spider (`giant_spider.png`, `SpiderCave`, `SpiderSwamp`) | Eight articulated legs around a compact abdomen/cephalothorax, low grounded stance, visible eye cluster and organic bristles; keep cave and swamp presentations related unless an approved brief says otherwise. | Use the spider brief and queued art jobs; no size, venom, density or aggression values invented. |

For the remaining named animal concepts, use the real-world species named by each filename as the anatomical baseline and preserve the exact individual/color pattern visible in that file. The 54 concept images are not 54 approved spawn entries. The six-view requirement is front, back, left, right, top, underside; existing concepts are not a substitute for those views. Keep model, rig/animation, audio, Unreal integration and spawn verification separately tracked.



## Trees, bushes, and environmental art

Regional primary trees are fixed: Winter Birch, Jungle Ash, Desert Palm, Swamp Spruce, Central Plains Oak. Make trees substantial, thick-trunked silhouettes with naturally varied branch taper; palms need thick trunks with layered old frond bases resembling overlapping pineapple scales. This is the owner's requested direction. Use the regional leaf images under `Art/Flora/` as leaf-color/shape cues. Bushes and berries remain static wild forage references; winter berries/bushes are snow-covered. Do not infer crop growth stages from the draft growth board: `Art/README.md` marks the first board as incorrect/draft and separate growth-stage coverage is incomplete.

The workstations (`Art/Concepts/Workstations/2026-10-12/`) and survival indicators (`Art/UI/Survival/2026-10-11/`) have their own `generation.json` prompts. Treat each as concept/source art. Reuse their documented materials and shapes, but keep the final HUD aligned with the realistic environment and preserve readable silhouette/value contrast at gameplay scale.

## Survival HUD and menu images

- **Health** (`Art/UI/Survival/2026-10-11/Matte-v2/Health-Matte-Full-v2.png`): a large, worn deep-red heart, like painted or stained leather/metal with scuffs and a subtle warm rim. Runtime fill should follow health; at zero retain only a thin heart outline. Do not replace the heart with a cartoon emoji.
- **Stamina** (`.../Stamina-Matte-Full-v2.png`): a chunky ochre-yellow lightning bolt with worn matte surface and dark edge wear. Fill recedes with stamina; zero leaves the outline.
- **Hydration** (`.../Hydration-Matte-Full-v2.png`): a blue-gray leather waterskin, bulging pear body, stitched side seam, cork/wood stopper and rough cord wrap. It should read as a waterskin, never a potion vial. Fill tracks hydration; zero leaves its outline.
- **Hunger** (`.../Hunger-Matte-Full-v2.png`): a thick cooked steak, browned and seared with visible marbling and fat, viewed close enough to recognize as meat. This is the HUD hunger symbol; the separate raw-meat inventory picture is a different state. Fill tracks hunger; zero leaves the outline.
- **Weight** (`.../Weight-Matte-Full-v2.png`): a squat, heavy, dark iron kettlebell/weight with a broad loop handle, pitted oxidation and worn highlights. Fill tracks weight; zero leaves the outline.

All five source icons are isolated transparent images with a realistic, scuffed material finish. Keep them modest in scale, legible against gameplay, and arranged as approved in the HUD layout; do not add cartoon facial features. Fill should be driven by the stat percentage, not a second invented gameplay value.

The title-screen source art is under `Art/UI/Title/` and its dated folder. The intended still plate has the ship, dock, survivor, and sunlight fixed in place; only ocean water, shoreline surge, and matching foam animate. `ELITEWAKE` sits near top center and the matching-font `PRESS ANY KEY TO START` prompt is centered near the bottom and flashes. Then the separate main-menu art shows a large active Single Player panel and a softened/blurred two-pirate Multiplayer preview marked Coming Soon; the intended hover treatment is cyan. These are separate screens and image layers, not a finished menu flow. Preserve the user's chosen source image and its written layout; don't ask an image model to redraw the logo or prompt into the water plate.

## Workstation references

The station concept sheets under `Art/Concepts/Workstations/2026-10-12/` use warm weathered timber, hand-forged dark iron, rope and realistic studio lighting. Their visible construction cues are:

- **Smithy** (`Smithy-Concept-v1.png`): a thick timber bench and heavy anvil mounted on a cut-log stump, dark iron straps and pegs, tools held upright at the rear, and a lower tool shelf. Read as a rugged metalworking station; retain open knee/work space and separate forge heat effects from the static mesh.
- **Loom** (`Loom-Concept-v1.png`): a tall rectangular wooden frame with upper beam, vertical warp threads, crossbars, a visible roller and a broad strip of pale woven cloth extending forward; a shuttle rests on the cloth. Expose the working face so the woven result reads clearly from the player approach.
- **Tannery** (`Tanner-Concept-v1.png`): a rough timber stretching frame with an irregular pale hide laced around the rim, a scraping board and hand tool, cut hide scraps, small buckets, and a large iron-hooped vat of liquid. The picture is a station concept, not a chemically exact process or a recipe list.
- **Forge, Cooking Hearth, Brick Oven**: see their named sheets in the same folder. Use those exact images and adjacent generation prompts for their detailed silhouettes; keep them separate stations and do not infer recipes from props alone.

## Asset-specific limits

The first pass gives detailed text cues for key assets named by the owner and records missing or inaccessible sources. It does not replace the authoritative per-animal roster or turn every one of the 269 catalog images into an independently approved build. For any catalog entry not described above, Claude should add the detailed description fields in the standing rule above beside its exact path before modeling it; do not guess at unseen markings or claim that a file has been visually inspected when it has not.
## Completion checklist for Claude

Before saying an image is ready for the game, report:
1. Exact source filename and whether the binary is present in the checkout (Git LFS must be hydrated to inspect it).
2. The source prompt/provenance and this text description used.
3. Whether the result is a concept, 3D mesh, texture/material set, icon, or imported Unreal asset.
4. Any unanswered owner decision kept TBD.
5. The actual build/import/play check and result. A picture plus a written brief is not an implementation.
