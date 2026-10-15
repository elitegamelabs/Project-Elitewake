# ELITEWAKE Asset Production and Unreal Integration Backlog
**Date:** 2026-10-15  
**Status:** Production backlog based on the current Systems Bible and owner directions  
**Authority:** Owner decisions and the Shared Guide supersede older team-guide wording.

## Important scope distinction
This backlog is not a claim that all assets have already been made. Concept images, production textures/UI images, actual 3D meshes, rigged animation clips, and Unreal gameplay integration are different deliverables and must be tracked separately. Do not mark an item complete until its source file exists in the repository, its Unreal import is verified where applicable, and its implementation has passed the relevant test.

## Phase 0 — Establish the source-of-truth and delivery path
- Keep the current authoritative project terminology as **Port/Ports**, not Village/Villages. Safely update current docs and player-facing text; preserve historical source archives where needed, clearly marking them as historical.
- Audit the repository asset inventory and current Unreal project before replacing or renaming any assets.
- Use a binary-capable Git workflow for PNG/TGA/EXR, FBX/glTF, WAV, and animation/source files. Use Git LFS for appropriate large binary assets if the repository workflow supports it. The current GitHub text-file action can commit documentation only; it cannot push binary images, models, or animation files.
- Never claim a generated concept board is an actual mesh or animation clip.
- For each deliverable, record file path, source/provenance, license, intended use, dimensions/format or mesh/rig details, import status, test status, and known dependencies.

## Phase 1 — Small playable slice first
This follows the development guide's staged-build and test-first approach.
1. Preserve the existing title screen and starter island, trees, ocean/water, and dock unless the current project audit says otherwise.
2. Improve the starter island stone/resource-node appearance.
3. Confirm spawn, third-person baseline, first-person toggle, and equipment interactions.
4. Implement and validate the Stone Hatchet wood-gathering loop.
5. Implement and validate the Stone Pickaxe mining loop.
6. Implement and validate waterskin filling/drinking and torch equip/use.
7. Add shovel and climbing pick only after their relevant interaction foundations are confirmed.
8. Add synchronized, contextual sound and animation notifies for gathering, mining, drinking, equipping, and placing objects.
9. Compile, run the slice, verify resource and inventory state, and checkpoint before adding more asset families.

## Phase 2 — Original image and texture production
Create separate production-ready source images—not only mood boards—for:
- Title/menu art and UI states.
- Inventory/crafting icons for tools, resources, weapons, ammunition, clothing, consumables, gems, treasure, and ship parts.
- Five region-specific environment concept sets: North/Winter, South/Swamp, East/Desert, West/Jungle, Center/Plains.
- Five distinctive regional ports with stone architecture, some vendor buildings, plain walls, waterfront access, and unique regional layout.
- Island silhouettes, shorelines, coves on some islands, landmarks, caves, climbable mountain ledges, cave gems, giant spiders, and the three-stage treasure-dig encounter.
- Characters, NPC/crew roles, creatures, ships, ship modules, props, and environmental set dressing.
Every in-game image must specify intended dimensions, aspect ratio, alpha/transparency needs, color-space requirements, and target material/UI slot.

## Phase 3 — Actual 3D asset production
Produce and catalog source meshes in small, testable batches:
- Character base meshes, skeleton/rig and clothing variants.
- Tools: hatchet, pickaxe, waterskin, torch, shovel, climbing pick, hammer, repair kit.
- Resource nodes: trees, stone, biome-specific harvestable plants, ore/gem nodes, and water interactions.
- Weapons and combat equipment: swords, firearms, ammunition, melee props, cannon assets where required.
- Survival and world props: storage chest, three-stage treasure mound states, containers, crafting props, doors/gates, ladders/stairs, walls, masonry modules.
- Port architecture: high-definition stone buildings, vendor-building variants, plain walls, piers, docks, stairs, retaining walls, gates, props and lighting fixtures.
- Ships and ship modules: dinghy, schooner/brigantine classes as needed by the current build, sails, helm, anchor, cannons, cargo/storage, repair points.
- Biome/island assets: terrain kits, shoreline/rock kits, trees/plants, snow/ice, swamp water/mud, desert rock/sand, jungle foliage, plains grass/stone, cave kits, gems and giant spider.
For each mesh, include appropriate UVs/material slots, scale/origin conventions, collision, LODs, naming, and performance checks. Use modular kits where efficient, but do not make every island or port look identical.

## Phase 4 — Rigged animations and gameplay hookups
The Systems Bible requires an animation library that supports both survival and shipboard life. Build an animation matrix with distinct source clip and Unreal integration statuses.

### Locomotion and traversal
- Idle/breathing; walk; jog/run; sprint.
- Jump; falling; landing.
- Crouch idle/movement.
- Prone entry, crawl, prone idle, exit.
- Swim and tread water.
- Climbing-pick traversal.

### Tools and survival interactions
- Equip/unequip and hand/weapon transitions.
- Hatchet chopping; pickaxe mining; plant harvesting.
- Shovel digging with three visibly distinct dig stages.
- Eating/drinking and waterskin use.
- Torch lighting/equipping.
- Object placement and crafting-station use.
- Medical treatment and patient reactions.
- Looting and chest opening/withdraw-only chest interaction.

### Combat
- Sword/melee attacks and hit reactions; block/parry only if approved by the current combat design.
- Firearm equip, aim, fire, recoil, reload.
- Appropriate weapon handling in first person and full-body third person.
- Death/knockdown/return-to-control states consistent with the existing character system.

### Shipboard
- Helm use; sail interaction; anchor interaction; cannon loading/aim/fire; ship repairs; bailing water; climbing aboard and disembarking; crew work loops.
- Use dedicated first-person layers where needed while keeping correct third-person actions visible to other players.

Animation deliverables must be actual rigged clips/source files, retargeted to the project's skeleton, connected to Animation Blueprints/state machines, and triggered by gameplay events or animation notifies. Static storyboards do not satisfy animation requirements.

## Phase 5 — Audio and feedback synchronization
- Title screen: wave/ocean sound must align with visible water motion.
- Tools: separate contextual chopping, mining, harvesting, digging, equip, use, placement and impact sounds.
- Materials should change the sound appropriately; avoid one generic impact sound for every material.
- Ship: water, wind, sails, rope, helm, anchor, cannon, impacts, flooding, fire and repairs.
- Creature/character actions: footsteps by surface, breathing/effort, weapon handling, hits, water entry/swimming, climbing, eating/drinking.
- Connect audio cues to animation notifies/gameplay state so sound does not fire early, late, or when an action is interrupted. Test timing in play.

## Phase 6 — Regions, ports, caves, and treasure
- At least five distinct islands per region (at least 25 total); coves on some islands, not all.
- One port in each region, not one on every island.
- Each port must read as a coastal port and use high-definition stone architecture, with some vendor/service buildings and some plain walls/structures.
- North/Winter, South/Swamp, East/Desert, West/Jungle, Center/Plains.
- Cave access: mountain-side entrance partway up, climbing-pick route to a standable ledge, then cave entry.
- Cave encounters include giant spiders and regional gems, with exact gem tables and encounter tuning kept TBD until approved.
- Treasure dig has exactly three shovel stages: stage one exposes the encounter and guarding enemies; defeat them before stage two; stage two exposes more; stage three fully uncovers the chest. Chest interaction is withdraw-only, never deposit.
- Preserve existing world, inventory, safe-zone, multiplayer authority and reward validation rules.

## Phase 7 — Import, integration, validation
For each batch:
1. Confirm original source files and commit them.
2. Import to Unreal with correct settings.
3. Check scale, materials, UVs, collision, LODs, rig, and skeleton compatibility.
4. Wire the asset to the intended Blueprint/C++ system without duplicate systems.
5. Test keyboard/mouse and controller; test first/third person as relevant.
6. Test gameplay triggers, animation notifies, audio sync, replication implications, and save/load behavior as relevant.
7. Compile and run; fix regressions before proceeding.
8. Update the asset catalog and commit a checkpoint.

## Immediate next actions
1. Review Claude's last specific instructions before claiming to continue them; no Claude instruction text is present in this request itself.
2. Audit the current repository/project files and existing assets.
3. Establish a binary-capable Git upload path for actual images/models/animations.
4. Start with one original starter-island asset batch and the core tool animations/sounds; validate in Unreal before scaling to the full asset roster.
