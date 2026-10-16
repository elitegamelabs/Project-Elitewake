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
