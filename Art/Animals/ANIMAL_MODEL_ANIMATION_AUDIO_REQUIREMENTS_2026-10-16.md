# Animal Models, Six-View References, Animations, and Audio
**Owner-confirmed direction — October 16, 2026**

## Scope
Apply this to **every animal already in the ELITEWAKE project and every animal explicitly approved for the game**. First inventory the current animal catalog and existing assets; do not invent or omit species. Reuse established species names, IDs, skeletons and asset paths where possible.

## Six-view image set for each animal
For each animal, create six reference images of the same individual/model and consistent proportions:
1. Front
2. Back
3. Left
4. Right
5. Top
6. Underside

Suggested paths (follow existing repository conventions if an equivalent location already exists):
- `Art/Reference/Animals/<AnimalName>/front.png`
- `Art/Reference/Animals/<AnimalName>/back.png`
- `Art/Reference/Animals/<AnimalName>/left.png`
- `Art/Reference/Animals/<AnimalName>/right.png`
- `Art/Reference/Animals/<AnimalName>/top.png`
- `Art/Reference/Animals/<AnimalName>/underside.png`

## Animal appearance guidance
Use the real-world species as the anatomical baseline unless the approved game design explicitly calls for a fantastical variant. The six views must agree on anatomy, markings, coloration, body proportions, limb count, tail, ears, muzzle/beak, claws/hooves/paws, feather/fur/scale pattern, and other distinctive features. The silhouette should read clearly at gameplay distance, while close-up views should support high-quality modeling and texturing. Make each species recognizable and biologically coherent; avoid generic interchangeable animal shapes. Use physically plausible fur, feathers, scales, skin, eyes and wetness appropriate to the species and biome. Keep the animal's visual identity consistent between reference images, production mesh, rig, animation and audio.

## Required 3D asset work
For each species, provide or update:
- Production-quality 3D model and textures/materials.
- Rig/skeleton and skin weights suitable for its body plan.
- Appropriate collision and navigation dimensions.
- LODs and performance-conscious settings as appropriate to the project.
- Consistent scale and orientation with the project's coordinate conventions.
- Integration into the existing asset catalog and runtime systems.

## Required animation coverage
Every animal needs, at minimum:
- **Idle / standing still:** natural breathing, blinking, subtle head/ear/tail movement, weight shifts as appropriate; avoid a frozen statue.
- **Walk:** species-appropriate gait and foot/paw/hoof placement.
- **Sprint / run:** distinct faster gait with appropriate stride, body movement and footfalls; not merely a sped-up walk unless that is genuinely correct for the species.
- **Attack/action animations appropriate to the animal:** pawing/swiping, biting, jumping/pouncing, charging, kicking, pecking, or other species-appropriate actions. Implement the relevant actions for each animal rather than forcing every action onto every species.
- Transitions between idle, walk, sprint, turn, attack/action, hit reaction and return-to-idle where supported by the game's combat/AI.
- Root motion or in-place animation according to the existing movement architecture; inspect and follow project conventions.

## Required animal audio
Create or source properly licensed, species-appropriate sounds and integrate them into the audio system for each animal:
- **Idle/standing:** breathing, snuffling, chirping, growling, calls, rustling, or other natural low-activity sounds as appropriate; do not force every animal to vocalize constantly.
- **Walking:** correct footfalls and body movement sounds for the surface/material and animal type.
- **Running/sprinting:** faster, heavier or otherwise gait-appropriate footfalls and movement sounds, with surface variation where supported.
- **Attacks/actions:** bite, claw/paw strike, pounce, charge, kick, peck, impact, and/or vocalization sounds appropriate to the species and action.
- Optional reactions such as alert, hurt, startled, and death only where consistent with existing game design.
- Use variation and sensible cooldowns to avoid repetitive sound loops. Mix sounds at gameplay-appropriate levels and test spatialization/distance attenuation.
- Do not copy copyrighted audio without permission. Record source/licensing and provenance for external sound assets.

## Suggested repository layout
- `Art/Reference/Animals/<AnimalName>/` — six-view reference images
- `Art/Animals/<AnimalName>/` — production models, textures, rigs and animations, following existing conventions
- `Audio/Animals/<AnimalName>/` — source audio, processed audio and metadata, following existing conventions

Inspect the repository first and use existing paths and Unreal naming conventions when present; do not create parallel duplicates unnecessarily.

## Claude and other agent instructions
Claude must read this file before modifying animal assets or AI. It must also inspect the current animal catalog and relevant Unreal project files, then report:
1. The complete animal inventory it found.
2. Existing assets/animations/audio for each animal.
3. Missing references, models, animations and audio.
4. Proposed exact file paths for missing assets.
5. Any dependencies or blockers.

Do not claim that six-view images, 3D models, animations or sounds exist until the files are present and checked. Reference images, generated assets, imported Unreal assets, runtime behavior and in-game verification are separate milestones. Do not change inventory/crafting menu icons as part of this task.

## Existing reference sources and appearance targets

Before generating anything, inspect:
- `Art/Concepts/Animals/2026-10-12/roster.json` — named species roster and reference filenames.
- `Art/Concepts/Animals/2026-10-12/README.md` — scope and limits of the 54 existing full-body concept references.
- `Art/Wildlife/Turnarounds/README.md` — six currently implemented prototype species and the intended six-view deliverables.
- `Scripts/Setup/place_animals.py`, `Scripts/Setup/build_animals.py`, and the current Unreal animal definitions/catalog — runtime species and approved habitats.

The 54 concept images are **not** substitutes for six clean views of each exact model. Existing six-species overview art is only a draft concept. Produce dedicated, high-resolution six-view sheets per animal and then separate front/back/left/right/top/underside image files in the agreed folder. Do not claim those individual files exist until committed and checked.

### Current six implemented land-animal prototypes: appearance guidance

Use each species' existing image in `Art/Concepts/Animals/2026-10-12/` as a starting reference, then correct it against real species anatomy. Keep the same individual, proportions, markings and materials across all six views.

- **American alligator:** broad, low-slung armored reptile; long muscular tail, short powerful legs, wide elongated snout, raised eyes/nostrils, rugged dark olive/brown scales and pale underside. Avoid crocodile-like narrow snout unless the selected species/reference specifically requires it.
- **Cottonmouth snake:** thick-bodied venomous pit viper; broad triangular head distinct from neck, keeled scales, dark mottled body, pale mouth interior only when the mouth is open. Keep a believable limbless body and continuous tapering tail; animation should slither rather than walk.
- **Tortoise:** low, sturdy body, domed patterned shell, scaly legs with claws, short tail and head/neck that retract or extend plausibly. Use the approved species reference for shell shape and coloration; do not make it look like a soft-bodied turtle.
- **Flamingo:** tall wading bird with long thin legs and neck, hooked/down-curved bill with dark tip, pink-to-coral plumage and webbed feet. Preserve the characteristic folded-leg/neck posture at idle and the correct leg/wing silhouette while running or taking off if flight is supported.
- **Brown pelican:** large coastal bird with long bill and expandable throat pouch, long folded wings, webbed feet, brown/gray plumage and pale head/neck variation appropriate to the selected adult plumage. Avoid flamingo-like legs/neck proportions.
- **Squirrel monkey:** small agile primate, compact body, long non-prehensile tail, golden/olive limbs, gray-olive coat, pale facial mask and dark muzzle/cap; use the existing concept as the exact color reference. Movement should use primate-appropriate quadrupedal gait, climbing/leaping if supported, not a human walk cycle.

### Additional approved habitat directions and cave creature

- **Horse:** use a realistic horse anatomy and proportions, with coherent mane, tail, hooves, muzzle and musculature; the owner placed horses in Plains. It needs walk, sprint/gallop, idle and relevant kick/bite reactions as supported by AI/combat.
- **Snow leopard:** thick pale gray/cream coat with dark rosettes, long thick balancing tail, compact powerful limbs, broad paws and feline face; the owner placed Snow Leopards in Winter. Provide feline walk/run/sprint, stalk, leap/pounce, bite/swipe and associated sounds.
- **Giant spider:** clearly arachnid anatomy with eight legs, segmented body, multiple eyes as appropriate, fangs/pedipalps and a distinct silhouette. Use the established cave-threat design; animate idle leg movement, skitter/walk, fast run, pounce/leap and bite/strike. Audio should be designed as stylized creature Foley (leg taps, body movement, hiss/click/strike), not falsely presented as literal natural spider vocalization.

For all other animals in `roster.json`, match the named real-world species anatomy and use its same-named concept image as the starting visual guide. Do not infer that every roster concept is currently approved for spawning. The current habitat and implementation authority remains the latest owner decisions and live animal catalog; keep candidate species clearly marked as pending. Aquatic creatures need swim/glide animations and appropriate underwater movement audio rather than land-only gait requirements, plus the required idle, faster movement and attack/action coverage when their design supports it.
