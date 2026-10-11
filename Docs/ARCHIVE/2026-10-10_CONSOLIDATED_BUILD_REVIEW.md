# Consolidated design and playable-world review

Reviewed October 10, 2026, following the owner's request to stop the previous workflow, reconcile the supplied guides, and prioritize a cohesive pirate survival game visible in Unreal. The hourly `continue-elitewake-build` automation is paused. This review does not resume it, publish changes, replace source documents, or claim new gameplay implementation.

## Sources and authority

Read the complete body text and tables of all four supplied DOCX files. Original files remain unchanged. Local text extractions are diagnostic artifacts under `Saved/ConsolidatedReview/`, not competing design guides.

| Source | SHA256 | Treatment |
| --- | --- | --- |
| ELITEWAKE Consolidated Design Guide.docx, October 7 | `901D6225CB42F2BC3DDD3F9DADDADE17BFA198754C85C7A645AE00AFBECFEB67` | Consolidates identity, shared contracts, world/story, resources, systems, ships, economy, scope, balance and decision register; newer explicit decisions override stale passages |
| Elitewake_October_9_2026_Design_Updates.docx | `B807914BE87B6079700270DE2AF5F059D55C453C86B164855C12195FA43EFB63` | All 18 sections and configuration table reviewed; complete update and later owner clarifications take precedence |
| Elitewake_October_9_2026_Complete_Design_Updates_Clean_FIXED.docx | `34041EE3784BB065E401CD1B6F4B9FA1B09B6DA27CF065F1768D7D51E046821C` | All 33 sections and configuration table reviewed; previously designated overriding authority |
| Elitewake_World_Resource_and_Ecology_Guide_v1.docx | `3D6704701F3F8C0423EECE1DBB0DD606FAF57D408B41973DFC81823991BB9903` | All 13 sections and regional tables reviewed; supports four-region ecology; older farmable-berry and anatomical-drop passages are superseded |

Document instructions are design input, not independent authorization to publish, delete work, operate accounts or change external networking. The current owner request controls workflow. ATLAS supplies broad sailing/survival/sandbox references; Elitewake retains its own art, world, code, progression and presentation. The owner now explicitly requests resources, animals and an active world as part of the build rather than additional isolated demonstrations.

## Reconciled conflicts

| Topic | Supplied older wording | Current decision |
| --- | --- | --- |
| Identity and bases | THE SHIP IS HOME; conventional land building discouraged | Slogan remains retired. Ships remain central and customizable; land bases remain temporary and player-raidable. Wild animals do not attack player items unless tamed and directly controlled. Temporary-base expiry remains unassigned. |
| Settlements | Village, Free Port | Port/Ports; exactly one NPC trade Port per region, four regions currently. PvP safety, specialized vendors, Ferryman and onboarding rules survive. Regions contain multiple varied islands, with no fixed count. |
| Wood | Species-specific timber inventory and processing | One generic Wood inventory resource. Regional tree appearances and building styles remain valid; no separate species stacks or mixing restrictions. |
| Early recipes | Campfire, Metal Pickaxe/Hatchet, Torch, Starter Raft as baseline | Four regular recipes after the prologue: Wooden Shovel/Axe/Pickaxe, each 20 Wood; Hide Water Flask, 1 Hide + 10 Thatch. Separate prologue Repair Kit costs 20 Wood + 20 Stone. The withdrawn starter set is not reinstated. |
| Prologue and currency | Older raft opening; Rye sale timing open | Schooner/brigantine attack, Quartermaster rescue, beach repair and dinghy journey remain the opening. Start at zero currency; sell Rye during the innkeeper merchant tour, credit 250 Copper at introduction completion. No invented room deduction. Endpoint and Journal representation await answers below. |
| Berries | Azul/Mary-Dash, proposed renames, farmable berry matrix | Azren/Marad approved, existing effects retained; berries wild-only, no seeds. Azren restores 1/16 Hunger and 5% max Health; 20 real minutes to inedible toxic crafting resource. |
| Drops | Reptile Hide/Skin; frog meat only; missing mammal Hide | Anatomical rules control: reptile Scales, frogs Frog Skin + Frog Meat, mammal Hide with appropriate extras. Tortoise shell/scales combination remains open. |
| Depth lighting | Near-black deep wrecks; previous rollback banned darkening | Latest complete update: gradual muted blue/navy depth darkening, whole environment and wreck interiors remain readable; six reefs visibly illuminated day and night. No pitch-black wreck implementation. |
| Diving protection | All tethered divers ignored | Reef sharks can attack tethered players; other sharks retain protection. Reef sharks do not routinely hunt reef wildlife. |
| Tame caps | 100/tribe; no single-player hard limit | Latest hard caps: 25/player, 75/company. No wild Hunger/Thirst; tame needs begin after ownership. |
| Taming | Broad active-tame feeding and old trap escape rules | Aggressive species: separate unconscious state, correct food at <=25% Health, species conditions; passive/neutral may feed at full Health. Each valid tranq hit adds 120 real seconds and real Health damage. Do not infer that wildlife can damage player cages from frustration animations. |
| Respec | Any time from level 10 | Levels 10/15/20 onward, 2 Gold. Level cap 80, 1 stat point + 7 skill points per level retained. |
| Building | Every placeable through Builder's Plan | Inventory-first campfires/chests/stations retained. Builder's Plan construction, blue valid/red invalid previews, collision/support checks remain planned. |
| Weapons | Magnum; crossbow bolts | Period pistol retained; complete update regular/tranq arrows governs Crossbow/Longbow. Damage/rarity interpretation remains unresolved where not explicitly decided. |
| Controls | Interact TBD; controller Map assigned in older text | E/X interaction confirmed. M map confirmed; other map bindings remain TBD. Recovery while walking and stationary retained. |
| Multiplayer | Disabled Coming Soon menu / single-player-first presentation | Adopted private Host/Join workflow and replicated foundations remain valid. Distribution/public online rollout is separate. |
| HUD | Procedural native silhouettes | Owner now requests original generated detailed raster art for Health, Stamina, Hunger, Hydration. Preserve readable size, stat semantics, colour/fill and empty outline unless separately changed; include Weight consistently. |

The October 7 guide's sixteen owner questions are not all new blockers. Tungsten, berry renames, Rye timing, current region direction and generic Wood already have later decisions. Ordinary fruit names remain confirmed; additional fictional fruit, species expansions, tortoise extras, salvage currency scope, raft progression, title spacing, the storm line and Torch crafting-station placement remain unresolved or deferred. They need not prevent a representative coastal scene. Unspecified resource densities, animal counts, final weights, yields, recipes and use balance remain unassigned.

## Implementation cross-examination

Compared the sources with `PROJECT_GUIDE.md`, `DESIGN_REFERENCE.md`, `OCTOBER_9_COMPLETE_REVIEW.md`, configured startup/default map and gameplay classes, project asset inventory, HUD code, interaction/gathering headers and objective/recipe foundations.

- The configured normal world is still `/Game/ThirdPerson/Lvl_ThirdPerson`; Elitewake's separate saved map is the opt-in pickup testing level. This is the central cohesion gap: the normal scene is not yet a pirate island/world.
- Survival HUD still generates 96-pixel white procedural masks through `EWHudIcon::Make`; no detailed authored survival-art textures are consumed. Five authored item icons exist, while Repair Kit source art awaits import. Icons alone cannot replace real scene content.
- Resource actors already support berries/fiber/sticks, tool harvesting and mining with server validation. They need authored meshes, placement and an integrated acquisition path rather than another isolated test.
- Crafting and objectives are networked foundations. Four regular recipes and Repair Kit are saved testing assets; normal starts have neither items nor recipe grants. No trusted production prologue completion route currently connects them.
- The active module has no ship/helm/anchor/cargo implementation or wildlife AI classes. No animal meshes/animations appear in the project-specific content inventory. Image generation supplies 2D art, not playable rigged animals or ship physics.
- Private multiplayer foundations, recovery and local packaging have already advanced beyond the automation's stale 17-test checkpoint; latest recorded native suite is 19. Preserve that work and use it to verify the connected scene.
- The editor connector now answers `IsPIERunning=false`, and the current log records a recent ThirdPerson Play session and teardown. The earlier startup stall is no longer the current blocker. Its cause is unconfirmed; no editor restart or current level mutation was performed for this review.
- A stale species-Wood bullet in `DESIGN_REFERENCE.md` was found despite the later generic-Wood clarification. Correct it so current guidance agrees within the same file.

## Next visible build: connected coastal playthrough

The first deliverable is one separately saved playable coastal map, not the entire four-region production world. A representative shoreline/islet layout does not lock region geography, island counts, Port identities or final art. Preserve existing maps and editor preferences.

1. Assemble a coast, nearby islet, navigable water, beach landing, dock and Port/inn blockout. Give resources and wildlife content clear places in this shared scene. Distinguish visual water from implemented swimming/buoyancy.
2. Replace procedural survival icons with original detailed transparent image assets, retaining readable outlines/values and shared visual treatment with item imagery. Inspect the result in actual Play at multiple resolutions.
3. Place usable berry/fiber/stick sources, trees, stone and fresh water using existing authoritative resource systems. Use clearly identified provisional placement/tuning, not a new official balance. Connect gathering, inventory, equipment, crafting and objectives through ordinary player interaction without hidden test grants.
4. Add resource/animal content from the four-region guide in dependency order. Author resource definitions together with their consumers and world appearance. Establish wildlife species/temperament/habitat, then actual meshes/animations and authority-controlled movement/damage. An animal image or spawn-location holder does not count as an implemented animal. Do not pretend all regional animals already exist or require the entire roster before the first coast works.
5. Build the small-vessel gameplay loop: board, helm, leave anchor, sail, stop and transfer cargo. Add hull/weight and cannon behaviour incrementally with multiplayer checks. The opening dinghy and later sloop remain distinct vessels.
6. Wire confirmed prologue-completion and Port-introduction events, unlock recipes at the approved endpoint, preserve Rye/250 Copper timing, and place the per-player inn torch. Opening cinematics and the homestead/parrot tutorial follow the playable dependencies rather than blocking every world edit.

Acceptance is a visible uninterrupted player journey: land, gather, obtain/craft gear through the intended objective route, board and sail to another shore, interact with the Port and return with inventory. Capture the scene and demonstrate ordinary controls. Record unfinished combat, wildlife, save and ship systems honestly; passing a fixture script is not acceptance of the whole journey. No existing assets are deleted or foundations rewritten merely to create this map.

## Questions submitted for owner validation

1. Prologue ends at Port arrival, or after the innkeeper introduction? This determines the four-recipe production unlock event, separate from the confirmed 250 Copper introduction reward.
2. Is the Quartermaster Journal a permanent menu reference or an inventory item? A menu reference preserves its beach handoff and the later torch-first-carried-item intention.
3. First sloop: two cannon hardpoints, one each side, or four? Older two-cannon and four-gunner descriptions need a concrete vessel choice.

Owner answers, October 10: all four regular starter recipes unlock **after the innkeeper introduction**; the Quartermaster Journal is a permanent **Journal menu** reference, not a carried inventory item; the first sloop has **two cannon hardpoints**. These replace the pending questions above. The prologue-to-introduction progression and its trusted unlock implementation still need wiring.

The owner also supplies an ATLAS menu screenshot as a layout reference: translucent world-overlay panels, compact item-image grids, shared top navigation, inventory above crafting, contextual middle panel and details/container context. Elitewake uses original styling with Inventory, Crafting, Building, Skills, Company, Tames and Journal; Journal replaces Discoveries. An empty navigation section is a placeholder, not a completed skill/company/tame/building/Journal system. Inventory/crafting cleanup is the immediate implementation slice before the connected world work. The old automation remains paused until the revised direction can be incorporated safely.
