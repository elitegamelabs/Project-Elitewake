# ELITEWAKE Wildlife Turnaround, 3D Model and Animation Upgrade
Date: 2026-10-15
Status: CONFIRMED owner request; implementation not yet complete.

## Goal
Replace the current placeholder/simple land-animal meshes and basic material-driven gait with production-quality, original, riggable 3D animal assets and proper animation sets. Keep the existing wildlife gameplay contracts and data definitions unless a change is explicitly approved.

## Current six-animal roster
Source of truth: `Scripts/Setup/build_animals.py`.
1. American alligator
2. Flamingo
3. Brown pelican
4. Cottonmouth (water moccasin)
5. Tortoise
6. Squirrel monkey

This is the current implemented roster, not the full future-game creature roster in the Creative & World Bible. Expand to other confirmed creatures in a separate, tracked pass rather than silently treating these six as the entire game roster.

## Required reference images for EACH animal
Create one clean, consistent turnaround sheet per species with:
- Front view
- Back view
- Left-side profile
- Right-side profile
- Neutral natural standing/resting pose, full body visible, orthographic camera, consistent scale and neutral studio background.
- Clear species-specific anatomy, proportions, markings, colours, feet, tail, beak/muzzle, shell/scutes/scales/feathers/fur.
- No perspective distortion, props, labels covering anatomy, dramatic lighting, or cropped appendages.
- Add a three-quarter view only as an additional reference; it does not replace any of the four required views.
- Preserve distinctive species traits and use original ELITEWAKE art, not copied game assets.

Suggested paths:
`Art/Wildlife/Turnarounds/american_alligator_turnaround.png`
`Art/Wildlife/Turnarounds/flamingo_turnaround.png`
`Art/Wildlife/Turnarounds/brown_pelican_turnaround.png`
`Art/Wildlife/Turnarounds/cottonmouth_turnaround.png`
`Art/Wildlife/Turnarounds/tortoise_turnaround.png`
`Art/Wildlife/Turnarounds/squirrel_monkey_turnaround.png`

## 3D asset requirements
- Build clean, properly proportioned 3D meshes based on the approved turnarounds; avoid treating a concept image as a model.
- Use appropriate topology, smooth deformation loops, UVs/materials, collision, scale, pivots, and naming consistent with existing Unreal assets.
- Keep gameplay data assets and stable references intact where possible. Do not delete or casually rename existing assets.
- Import/build Unreal assets using Unreal Editor APIs and the existing project workflow; do not attempt to edit Unreal binary assets as plain text.
- Track model completion separately from concept-art completion and Unreal integration.

## Animation requirements
Replace the current single material World Position Offset gait as the final animation solution with rigged skeletal meshes and animation assets where practical. Maintain network-correct gameplay movement and replicated pose behavior.
Minimum per-species animation coverage, where anatomically applicable:
- Idle, breathing, head/neck movement, blinking, and species-specific secondary motion
- Walk and run / flee; turn and stop
- Resting or sleeping and getting up
- Hit reaction, death/fall, and harvestable dead pose
- Attack/bite/strike for aggressive species (American alligator and cottonmouth)
- Swim/wade for aquatic or shoreline species (alligator, flamingo, pelican, cottonmouth where applicable)
- Bird-specific head bob, steps, wing fold/adjustment, takeoff and landing where appropriate; flight is a separate decision if not yet supported by gameplay
- Tortoise leg cycle, head/neck extension and retraction; shell plates should read as individual scutes rather than painted stripes
- Squirrel monkey climb, perch, leap, and tail balance where the environment and AI support them

## Integration and validation
1. Inspect the current six meshes, material gait, definitions, animation/movement code, and verification scripts before changing anything.
2. Produce and review turnarounds before finalizing mesh proportions.
3. Implement one species end-to-end as a vertical slice (mesh + skeleton/rig + materials + animations + Unreal import + gameplay hookup).
4. Validate idle and locomotion from front, back, left, and right; check feet contact ground, no obvious sliding, clipping, or mesh deformation.
5. Verify aggressive/docile behavior, wading/ground movement, death and harvesting, replicated movement, and performance.
6. Extend to remaining species in small batches; run relevant animal Play checks and preserve unrelated systems.
7. Commit in focused checkpoints and report exactly which source images, model assets, animations, imports, and tests are complete.

## Current known baseline and limitations
The current six models are procedural lofted meshes and use a shared material World Position Offset gait, not full skeletal rigs. The tortoise shell needs better individual scute definition, and animals can walk through rocks and trees (tracked separately). Do not claim a production model, skeletal rig, or animation set exists until the corresponding assets are built and validated.

## Deliverable checklist
- [ ] Six approved four-view turnaround sheets
- [ ] Six production 3D meshes
- [ ] Rig/skeleton for each applicable species
- [ ] Species-specific animation assets
- [ ] Unreal imports and gameplay hookup
- [ ] Front/back/left/right visual review
- [ ] Wildlife gameplay and replication tests pass
- [ ] Asset manifest updated with source paths and status
