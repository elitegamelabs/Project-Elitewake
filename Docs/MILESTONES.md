# Milestones

The order Elitewake is built in, from what stands today to a private release. Each milestone ends in something a tester can play, and each item in it is built, checked in Play and committed before the next ("compiling is not proof it works"). Design rules are in [DESIGN_REFERENCE.md](DESIGN_REFERENCE.md), test results in [VERIFICATION.md](VERIFICATION.md), day-to-day status in [PROJECT_GUIDE.md](PROJECT_GUIDE.md).

Drawn up October 13, 2026 at the owner's request, under the owner's delegation; the owner can reorder anything. **Blocked** items wait on an owner answer listed in the design reference's [open questions](DESIGN_REFERENCE.md#open-questions) or on owner art; they are skipped, not guessed.

Status: ✅ done · 🔨 in progress · ⏳ next · ⛔ blocked on the owner

Work reports: [Claude, October 15](REPORTS/2026-10-15_Claude.md). Tasks open for another agent: [DELEGATED_TASKS.md](DELEGATED_TASKS.md).

## Owner priority, October 14 — core survival on a clean island 🔨

The owner set this ahead of the milestone order: a clean island to play the core survival actions on, then the environment and the world. Boats are out of the island map (they, the cannons and their checks carry on in `/Game/Elitewake/Maps/Test/Lvl_ShipsTest`); the sea creatures stay. The title screen, HUD, compass and the working systems are kept.

| Item | Status |
|---|---|
| Island cleaned: boats removed from the island map (kept in the ships test map); the starter supplies are the four core tools | ✅ `04771cf` |
| Hatchet chops trees for Wood; Pickaxe mines rock for Stone; Waterskin fills at fresh water and is drunk; Torch is lit and put out with light and flame; each with its animation | ✅ `04771cf` |
| Fish harvesting: strike with anything; carry the body ashore; harvest it on land for 2 to 5 fish meat (6 to 10 for sharks, the manatee and bigger creatures) | ✅ `a1143cf` |
| Escape OPTIONS menu: SAVE GAME (single player) and MAIN MENU back to the ELITEWAKE title; Single Player resumes the saved survivor | ✅ `dfbdc22` |
| The sloop back off the island beach (owner, October 15), helm, sails, cannon and shot in its hold | ✅ `b148160` |
| A second, smaller island about 125 m south-west across open water (owner, October 15) | ✅ `e0443c4` |
| More trees and rock in different sizes and colours; rock no longer low-poly: 68 palms (0.7 to 1.35 scale), 31 Maravai broadleaf hardwoods with per-tree leaf shades, 67 rocks in eight shapes and four stones (granite, sandstone, basalt, limestone) with shader-detailed surfaces, across all three islands | ✅ `e0443c4` |
| Sea creatures made 3D: a round trunk lofted inside each creature's fins (owner: they were "hilariously 2D") | ✅ `e0443c4` |
| Land animals on both islands from the owner's photos (October 15): American alligator, flamingo, brown pelican, cottonmouth (water moccasin), tortoise, squirrel monkey, as 3D models that move | ✅ `01fa50a` |
| Gathering and harvesting motions (ground squat, bush pick, hatchet chop, pickaxe blow) and the hit feedback (chips, shake, hit marker, what it gave) | ✅ `c214316` |
| Regions and climate: Desert islands (humidity 100 m offshore) and a first Winter island (snow, birches, snowy rocks); body temperature, Cold and Freezing, HUD and Character screen readouts | ✅ `811a3e8` |
| First sounds, drafts from the owner's Scenario account (October 15): chop, pickaxe strike and glancing clink at the blow; gather rustle and pickup; footsteps on sand and snow; surf everywhere, wind on the Winter island, seabirds; alligator hiss, flamingo and pelican calls. Listening and final audio remain | ✅ `9a54ac7` |
| Second sound batch (owner-approved, October 15 night): cannon fire, hull hits, splashes, bailing, sinking, ship creak and rigging loops, deck steps, swimming, night insects, cave drips; all loops seamless | ✅ `b98c572` |
| Bigger islands to explore (owner, October 15 night): every island 500–900 m across, the starter about 620 m with its beach, dock, pond and sloop unchanged; the world rebuilt and rechecked; wildlife far from survivors rests so it stays fast | ✅ `7dfab58` |
| Cobwebs in every cave that tear as you walk through (owner, October 15 night) | ✅ `7dfab58` |
| Each region's own trees (owner, October 15): Plains oak groves, Winter birch, Jungle ash forest, Desert palms, Swamp spruce stands; new oak and ash models | ✅ `468ce0d` |
| Every island its own terrain (owner, October 15): peaks, ridges, plateaus and valleys in a different plan on each island | ✅ `0d0a685` |
| Third sound batch: grass and stone footsteps, forest wind, the jungle by day, swamp frogs | ✅ `0d0a685` |
| Swimming moves only forward and back, no sideways drift (owner, October 16) | ✅ `745f72f` |
| Helm-only sail keys (arrows, LB/RB) and the 180-degree sail range (owner, October 16) | ✅ `ffebdd7` |
| A foam wake trail about 20 m long that follows the ship's turns (owner, October 16) | ✅ `27afdaa` |
| Sails fill and billow with the wind, and go slack but keep flapping when it runs along them (owner, October 16) | ✅ `037df4f` |
| Anchor chain: slack paid out, then taut with a clank and a smooth stop; the chain drawn paying out, sagging, taut and coming in (owner, October 16) | ✅ `030df8c` |
| Faster crossings between islands (owner, October 16) | ✅ `030df8c` |
| Fewer trees on the Plains (owner, October 17) | ✅ `dae6240` |
| Each region's own soils on the ground (owner, October 16) | ✅ `7765e57` |
| Desert dunes, sandstone pillars and the Jungle's understory (owner, October 16) | ✅ `b6ab72e` |
| Water pushed aside at the bow and along the sides, heavier outside a turn (owner, October 16; reverse waits for ships that can go astern) | ✅ `f1a1e08` |
| Surf fades out 20 m inland; anchor chain sounds on drop, catch and raise (owner, October 16) | ✅ `8ae15b7` |
| Island rock formations rebuilt to look natural | ✅ `e0443c4` (with the rock rework above) |
| The five-region world (owner, October 15): Plains centre with the starter island and five more, Winter north, Swamp south, Desert east, Jungle west, 5+ islands each, 800–2,000 m sea gaps, regional terrain, dressing, animals, sea life and climate on all 26 islands | ✅ `90978cc` |
| **C-WORLD40 (owner, October 18):** expand to exactly eight islands in each region while preserving the original 26 islands and Port sites | 🟡 Source layout and offline checks pass; Unreal map rebuild, save/discovery migration, multiplayer and performance checks remain open |
| **C-WILDLIFE40 (owner, October 18):** add approved wildlife to the 14 new islands without changing existing placements | 🟡 Additive source for six existing land species; new species assets, fish preservation/distribution, and Unreal verification remain open |
| Ports: one per region (owner), stone quay, pier, plaza, nine masonry buildings with shops marked, town wall and gate, landmark lighthouse, regional character | ✅ `618acbb` (vendors, names, safe zones open) |
| Caves: one per island, inland, cliff-face and coastal entrances, walkable passage and chamber | ✅ `fb35edc` (contents wait for design values) |
| Grass you can see as plants on the Plains and Jungle islands | ✅ `fb35edc` |
| Island landmarks: one per island (sea stacks, shore arch, standing stones, spire, giant dead tree) | ✅ `fb35edc` |
| Larger islands (open question for the owner) | ⏳ |
| Day and night: 90 real minutes each (owner), server-owned clock, moving sun, moon, darker nights | ✅ `2ac71d9` (stars, saving the hour, night climate open) |
| Winter snow: falling snow round the survivor in the Winter region, stopping under roofs; snow on Winter's plants and berry bushes | ✅ `d59f225` |
| Six glowing reefs (design reference; places decided provisionally): one per region and a second in the Plains | ✅ `d86efa3` |
| Environment and world (M5 terrain and vegetation) | ⏳ |

## Owner-requested follow-up milestones — October 16, 2026 ⏳

These are **pending implementation and Unreal Play verification**, not completed by recording them here. Existing completed milestones remain historical records; the owner requests below supersede conflicting earlier tree-placement expectations.

| Milestone | Status | Completion evidence |
|---|---|---|
| **M5: Starter island oak replacement** — remove all palms from the Central Plains starter island; replace with realistic oak trees, preserving terrain, dock, water, harvesting, collisions and gameplay. | ✅ `2e7404d` | No palm actors, foliage instances or procedural spawns on the starter island; oak trees visibly present and harvestable in Unreal Play. |
| **M5: Desert palm relocation** — ensure palms are placed on Desert-region islands in natural, terrain-aware distributions, rather than on the starter island. | ✅ `2e7404d` | Inspect Desert islands in Play; update procedural placements and tests, including any existing test that expects starter-island palms. |
| **M5: Dense non-palm foliage** — full, natural-looking, species-appropriate leaves or needles on oak, birch, ash, spruce and all other non-palm trees throughout the world; preserve wind response and performance. | ✅ `97c3cf4` | Inspect each regional tree type close-up and at gameplay distance; verify LOD and frame-rate impact. |
| **M5: Winter tree partial snow coverage** — snow accumulates on portions of winter-tree branches and foliage while some leaves/needles remain exposed; vary coverage naturally by tree and exposure. | ✅ `97c3cf4` | Unreal Play visual checks confirm both snow-covered and exposed foliage; no uniformly white canopies. |
| **M1 / Ships: Centered stern boarding ladders** — on every applicable boat/ship, place the boarding ladder **directly at the horizontal center of the rear (stern)**, aligned with the vessel's longitudinal centerline; preserve boarding interaction and climb animations. | ✅ `01dfca1` | Check stern ladder alignment from behind on each ship type and board/disembark in Unreal Play, including multiplayer where supported. |

Related specifications: [starter island](STARTER_ISLAND_CENTRAL_PLAINS_DIRECTION_2026-10-15.md) and [foliage/winter snow](TREE_FOLIAGE_AND_WINTER_SNOW_DIRECTION_2026-10-16.md).


## Owner-approved wildlife and interaction follow-ups — October 16, 2026 ⏳

All entries below are **pending implementation and Unreal Play verification**; documentation does not mean finished. Preserve existing approved wildlife, animations, audio and ecology.

| Milestone | Status | Completion evidence |
|---|---|---|
| **M5: Regional animal roster** — retain prior animals; add bears (Winter), lions (Central Plains), giant crocodiles (Swamp), and elephants (**tropical Western Jungle**, not Desert or Central Plains). Review earlier proposed foxes, deer, boars, birds, snakes and other species before treating proposals as canon. | 🔶 | First pass placed (Oct 26): code-built meshes, definitions, regional counts, one call each; `verify_animals_play` passes. Still to do: species attack animations, remaining calls, a look in game. |
| **M5: Species-appropriate attacks and vocalizations** — bite/head/jaw and growl/threat animations with synchronized bite/contact and vocal audio for applicable animals; alternate behaviors for species that do not bite/growl. | ⏳ | Per-species coverage matrix, synced audio/animation notifies, authoritative combat and multiplayer checks. |
| **M5: Natural wildlife roaming** — all animals wander and behave naturally on their assigned islands, with species-specific locomotion, idle, foraging, threat, rest, avoidance and audio; retain distance-based performance optimizations. | ⏳ | Roaming and navigation Play checks, island boundaries, replication and performance. |
| **M5: Spiders in every cave and Southern Swamp** — place spiders in each cave across all regions and in suitable swamp habitats, with full crawling, leg, turning, bite, hit, death and web animations and synchronized sound effects. | ⏳ | Every cave populated, swamp placement, animation/audio, multiplayer and performance Play checks. |
| **M5: Tropical elephant obstacle destruction** — elephants physically push down destructible trees and appropriate obstacles with credible animations, impact/cracking sounds and collision; protect critical structures. | ⏳ | Obstacle/tree falling, navigation and authoritative physics verified in Unreal Play. |
| **M5: Elephant-felled trees persist and yield wood** — fallen trees stay on the ground for players to chop with hatchets and harvest wood; prevent duplicate yields, maintain collision and multiplayer state. | ⏳ | Tree remains, chop animation/audio and inventory yield validated; persistence and cleanup tests. |
| **Owner decision deferred: fallen-tree cleanup after harvesting** — duration and disappearance/regrowth rules to be chosen later; do not invent a timer. | ⛔ | Owner specifies policy before finalizing cleanup logic. |

Supporting requirements: [animal attacks and regional suggestions](ANIMAL_ATTACK_AUDIO_AND_REGIONAL_WILDLIFE_PROPOSAL_2026-10-16.md), [four approved additions](APPROVED_BEAR_ELEPHANT_GIANT_CROCODILE_LION_WILDLIFE_2026-10-16.md), [tropical elephant correction](ELEPHANT_TROPICAL_ISLAND_HABITAT_CORRECTION_2026-10-16.md), [roaming and spiders](ELEPHANT_DESTRUCTION_WILDLIFE_ROAMING_AND_SPIDER_MILESTONES_2026-10-16.md), [harvestable fallen trees](ELEPHANT_FELLED_TREES_HARVESTABLE_2026-10-16.md).

## M0 — Foundations ✅

Server-authoritative survivor (movement, stances, swimming, survival needs), inventory, equipment, hotbar, crafting, objectives, Company, private multiplayer with recovery; the coastal map with terrain, ocean, palms, boulders and plants; ships (sloop, raft, dinghy) with fittings, sailing, crew on deck, ladders, anchor, cargo and weight; melee; the Journal guides. See the VERIFICATION table for every check.

## M1 — First Voyage (a complete coastal session) 🔨

Goal: from the title, a tester lands on the coast, gathers, boards and sails a ship, fights and harvests sea life, and can tell what to do without being told. Ends with one integrated Play check that walks the whole session.

| Item | Status |
|---|---|
| Ladders with E and the arrows; ship place labels | ✅ `d5f7b22` |
| ATLAS-style sail trim, wind, compass, helm camera | ✅ `e6b4ac3` |
| Sea creatures, harvest for Raw Fish / Raw Meat | ✅ `7fca84c` |
| Tools held in the hand, tool chop, ladder animations | ✅ `5ae3fbc` |
| Title splash and main menu (Single Player) | ✅ `6f9ac2c`, `1f7d505`, `3673627` |
| Small craft pass: wake behind moving boats; sloop moored with its bow to open water | ✅ `6b5829f` |
| Small craft pass: ships rock on the swell and heel under sail | ✅ `6aaf8cb` |
| Small craft pass: the rudder swings over instead of snapping | ✅ `ff74ff9` |
| Small craft pass: the wheel and tiller visibly turn with the rudder | ✅ `15414cd` |
| Small craft pass: a finish pass on the raft, dinghy and sloop | ✅ `63e671e` |
| Paddling animation for the raft; holding the helm | ✅ `50e1c5f` |
| First-person body: see your arms, hands and feet (owner, October 13) | ✅ `6fd9133` |
| Capstan animation | ✅ `a764bc3` |
| Freshwater pond on the island for bass, catfish and piranha | ✅ `24f1418` |
| Campfire: cook Raw Fish and Raw Meat; eat raw (10% health, sickness) or cooked (20% / 25%) | ⛔ hunger restored by fish and meat, what sickness does and how long, campfire recipe and cooking time (open question 11) |
| Inventory and crafting screen redesign: a full slot grid with item pictures, counts and freshness, an equipped row, needs with their icons, item details and crafting | ✅ `3b3e942` |
| Item art: the reviewed atlases cut into clean inventory icons and bound to every current item | ✅ `3b3e942` |
| Integrated First Voyage Play check | ✅ `60e813f` |

## M2 — Cannon fight

Goal: the design's "simple two-cannon fight before the deeper systems". Cannons fitted on the sloop's hardpoints, aimed and fired by a survivor, round shot that hits hulls, hull health, holes that let water in, bailing and repair, and a ship that sinks into floating wreck crates. Cannon art is a stand-in until the owner's. Ammo crafting, recipes and costs: ⛔ (open question 1); placeholders are test items only.

| Item | Status |
|---|---|
| Cannon: fit it at a hardpoint, man it, aim within its arc, load round shot and fire | ✅ `b919471` |
| Hull health; round shot that strikes a hull and damages it | ✅ `1fdbe41` |
| Holes below the waterline let water in (the ship settles and slows); bailing | ✅ `a0374fa` |
| Repairing holes | ⛔ repair cost and tools (open question) |
| Sinking: a ship that fills or is destroyed goes down, leaving wreck crates with its hold | ✅ `77a0452` |
| Integrated two-cannon fight Play check | ✅ `581186a` (`verify_cannon_fight_play`) |
| Cannon and shot recipes, costs and variant names | ⛔ open question 1 |

## M3 — Builder's Plan, Loom and Tanner ⛔

Build Mode for building on every island outside Ports and obstruction zones: design drafted October 27 in [Design/Gameplay/BUILD_MODE_ISLAND_BUILDING_DESIGN_2026-10-27.md](../Design/Gameplay/BUILD_MODE_ISLAND_BUILDING_DESIGN_2026-10-27.md); not implemented; open owner questions listed there.

The ship section of the Builder's Plan as the fitting screen; sails at the Loom, helm and cannons at the Smithy; Tanner. Blocked on fitting recipes and costs (open question 1).

## M4 — Prologue and the Port ⛔ partly

Waking on the island with the Quartermaster's Journal, the Repair Kit and the dinghy, the Port, the innkeeper introduction (250 Copper and the four starter recipes), the inn torch placed for real. Blocked on the dinghy route, first carried item and room price (open question 2) and the Port's island (open question 7). Unblocked parts — the Journal as the Quartermaster's, the Repair Kit loop — can go ahead.

## M5 — Living world

Regional resources and vegetation beyond the coast across five regions: Desert, Winter, Jungle, Plains and Swamp. Substantial varied islands, long voyages, one cave per island, solid terrain/seabed, and selected 500-meter ocean depths. Terrain mesh construction is assigned to Claude in [the world mesh handoff](MILESTONE_WORLD_MESH_HANDOFF_2026-10-14.md). Also pending: regional wildlife/AI and taming, hand gathering and ore tool gates, three-stage tree/crop planting, snow-covered static wild berries, and three-ship ghost encounters. See the [remaining-work checklist](REMAINING_WORK_2026-10-14.md) for evidence requirements and blockers.

## M6 — Survival depth

Cooking (campfire, then grill), spoilage, raw-food sickness, weather and storms, day and night (90 + 90 minutes), clothing and temperature. Add Character humidity, desert/jungle/swamp heat, winter freezing and snow, the desert's 100-meter offshore humidity zone, stamina-limited climbing and solid-ground fall damage. Thresholds, clothing effects and damage curves remain TBD.

## M7 — Persistence

Save and load for survivors, inventories, ships and the world; server restarts keep the game. Generated islands/caves remain fixed for that world. Single player has saving; multiplayer has server persistence without a player manual-save button. Include planted stages and Company claim state once implemented.

## M8 — Multiplayer menu and private release

Multiplayer from the main menu (now Coming Soon), the private release pipeline (`Docs/PRIVATE_RELEASE_AUTOMATION.md`, being set up separately), clean-PC, LAN and Internet tests. Any upload, account, runner or tester invitation needs the owner's go-ahead.

## M9 — Characters

Real survivor bodies: the owner's characters or MetaHumans on the mannequin skeleton, faces, hair and clothing; the character creator (in source, not in the menu path since October 13) returns where the owner wants it.

## M10 — Constellations and Company islands

Ten selectable night-sky constellations with ten skills each, including the upward Skills camera transition, progression and the confirmed respec cadence. Extend Company ranks, permissions and asset sharing, then multiplayer-only claim flags and the contest-to-new-claim sequence. Port islands are excluded; single player builds without claim gates. Skill effects/costs/connections and claim durations/proximity/defense remain TBD. This is pending work, not a change to the implemented Company foundation.

## How work proceeds

### Complete remaining-work map

The [October 14 checklist](REMAINING_WORK_2026-10-14.md) supplements every milestone with outstanding art integration, menus, prologue, ship fittings/combat, world/resources/animals, planting/climate/traversal, persistence, multiplayer, characters, progression and Company work. M10 adds the night-sky ten-by-ten constellation system and multiplayer-only Company claim/contest flags; NPC Port islands remain unclaimable. Earlier verified foundations are retained. No new feature is marked done by publishing source art or this list. The [art catalog](../Art/README.md) distinguishes reviewed references, drafts and pending models.

Unresolved owner decisions across those systems are consolidated in [Open Questions — October 15](OPEN_QUESTIONS_2026-10-15.md). The register includes source locations, current code values where verified, and dependent work; it does not choose answers.

### October 14 owner handoff: world terrain for Claude

Terrain mesh construction is assigned to Claude. The five-region layout, substantial islands, long sailing distances, varied cliffs, one differently located cave system per island, regional terrain, solid island/seabed collision, selected 500-meter depths, and vegetation growth-stage mesh requirements are listed in [the world mesh milestone handoff](MILESTONE_WORLD_MESH_HANDOFF_2026-10-14.md). That checklist supplements M5 and supersedes its older four-region geography. It remains pending implementation and Play verification. Mode-specific rules are in [Single Player](SINGLE_PLAYER_RULES.md) and [Multiplayer](MULTIPLAYER_RULES.md).

Work takes the first ⏳ item of the earliest unfinished milestone that is not blocked. Each item: build, run its Play check and the regression checks it touches, update the docs, commit and push. Owner requests jump the queue. Before starting, check `git log` and `git status` for work committed by other sessions, and leave files someone else has uncommitted alone.


## Ships rebuilt to the new design sheet — October 18, 2026 🔨

Owner, October 18: "THE NEW SHIP DESIGN" (`Art/Concepts/Boats/2026-10-18/Ship-Design-Sheet-v1.webp`) is the base for every
ship. Columns left to right: raft, sloop, schooner, brigantine, Cavalier; mast counts as drawn (raft 1, sloop 2, schooner 2,
brigantine 3). One ship at a time, each verified in Play; the flags, railings, gunports and ladders carry over.

| Ship | Status | Acceptance |
|---|---|---|
| Sloop: two masts (main and a mizzen on a raised stern deck), long bowsprit, baluster railings with brass caps, brass trim, dark tarred lower hull, furnished lantern-lit cabin under the stern deck and a furnished hold | ✅ reworked to the written rules (this commit): bare hull, two sockets, no captain's quarters, 3.6 m high, flags on deck staffs | Play checks for her sailing, fittings, flags, ladder and cannons pass; screenshots `Saved/Screenshots/ShipLook/Sloop` and `Sloop_rigged`. Interiors and colour to refine with the next ships |
| Schooner (two sail hardpoints) | ✅ reworked to the written rules (this commit): bare hull, 22 m, full-width aft quarters with the wheel on their roof, stairs both sides with fixed rails, 12 square gunports, jackstaff and ensign | Play checks for her fitting out, sailing, decks, quarters, ladder, gunports, flags and the cannon fight pass; screenshots `Saved/Screenshots/ShipLook/Schooner` and `Schooner_rigged` |
| Brigantine (three masts) | ⏳ | as above |
| Raft | ⏳ | as above |
| Cavalier (largest; three walkable decks, per the owner's specification) | ⏳ | as above |

## Owner ship systems expansion — October 17, 2026 ⏳

**Status: design approved, implementation and Play verification pending.** Latest owner decisions override older conflicting ship rules. These are planning milestones, not proof of implemented features. Concept imagery is reference-only; models, assets, code, and multiplayer verification remain separate.

| Milestone | Status | Acceptance criteria |
|---|---|---|
| **Ship hulls, decks and stairways** | ⏳ | Realistic class-specific raft, sloop, schooner, brigantine and Cavalier. Cavalier has three walkable decks connected by one central U-shaped switchback staircase with square landings, 180° turns, headroom, navigation and safety railings; realistic indirect interior lighting. Preserve functional anchor and centered stern ladders. |
| **Modular railing hardpoints** | ✅ sloop, schooner, brigantine `eace37e` (recipes, dinghy function, Cavalier pending); sloop first `4870f1f` | Sloop 2 (one per side), schooner 4 (two per side), brigantine 6 (three per side); interchangeable plain wooden, functional dinghy attachment, or two-cannon railing modules. Materials, curve, grain and weathering match host hull. Cavalier has permanent ordinary top-deck railing, not interchangeable. |
| **Hull gunports and cannon mounts** | 🔨 sloop none, brigantine six round ports `eace37e`; sliding glass covers, run-out and no firing shut on the brigantine and schooner ✅ (this commit); Cavalier pending | Sloop has NO hull gunports. Brigantine has 6 individually crafted permanent circular hull gunports (3/side), each with separately mounted cannon; Cavalier has 10 top-deck cannon mounts (5/side), 8 middle-deck gunports (4/side), 4 bottom-deck gunports (2/side amidships), 22 total potential cannons. Lower gunports above waterline. Each hull port has sliding dark opaque glass cover, cannon carriage extension/retraction, individually controlled open/close, cannot fire shut. |
| **Cannon operation and NPC volleys** | ⏳ | Physical powder/ball loading, ramming, aiming, firing, recoil and reload times; purchased Port NPCs can be assigned to any deck's cannons. NPCs aim at player's targeted enemy but fire only on player's cannon shot and only when ready and with line of sight; replicated authoritative combat and sound. |
| **Six modular sail assemblies and raft sail** | ⏳ | Small/medium/large standard rectangular draped cloth and small/medium/large triangular weighted sails; raft has one functional small-sail hardpoint. Sail positions 0/25/50/75/100%; physical gradual rope/cloth animation and wind-driven propulsion, no wind propulsion at 0%. |
| **Sail control and crew dependency** | ⏳ | Hold keyboard Up/Down or Xbox D-pad Up/Down to raise/lower progressively. Helm commands all sails that have assigned NPC sail operators; unassigned sails cannot be operated from helm. Human players can interact at each sail to operate it individually without NPCs. NPCs visibly work ropes; replicated state. |
| **Craftable flags and combat damage** | 🔨 sloop, schooner, brigantine ✅ (this commit; Cavalier with her hull; recipe TBD) | Sloop 2 flag positions, brigantine 3, Cavalier 4, all initially empty. Default crafted flag plain clean white, no emblem/skin options yet; future skins supported without changing durability. Flags install/remove/swap, flutter in wind, weather/fray/tear progressively ONLY when combat-damaged, never from storms. No repair; destroyed fabric disappears while pole remains, replacement must be crafted. |
| **Permanent ship surgeon** | ⏳ | Every ship with below-top walkable deck has an always-present interactive surgeon in rear-left corner of FIRST deck below top. Authentic operating table, scissors and tools, shelving and navigable room. Each treatment costs 15 copper, gradually restores 25% of maximum health (capped at 100%), with treatment animation and multiplayer-safe payment/healing. |
| **Art reference coverage** | ⏳ | Generate coherent orthographic views (front/back/left/right/top/underside and attachment/corner details) for each railing module and applicable ship assets; distinct deck-layout, sail, cannon, gunport, flag-damage and surgeon-station references. Confirm each image against specifications before use; reference images are not integrated game assets. |

**Implementation sequence:** audit current ships and their assets first; reconcile with latest owner decisions, then implement one independently testable system at a time, preserving current gameplay. Record Unreal Play and multiplayer verification in `Docs/VERIFICATION.md`; do not mark complete without evidence.

## Owner requests — October 17, 2026 (later)

| Milestone | Status | Evidence / acceptance |
|---|---|---|
| **Placement highlight** — every placeable item shows a blue highlight where it can be placed, red where it cannot, normal once placed. | 🔨 ship fittings ✅ `8a3df15`; Build Mode placeables when Build Mode exists | `verify_placement_preview_play` (5): blue at a fitting mount, red at a wrong-size mount and at a closed cannon place, normal once installed; screenshots `Saved/Screenshots/Placement` |
| **The ocean floor** — dynamic seabed scenery: deeper sand, varied geography, corals and aquatic plants; the ocean at most 2,000 m deep (owner, October 17; was 500 m). | ✅ built and verified (provisional looks until ChatGPT's G8 designs) | `verify_seabed_play` (10), `verify_coastal_ocean_depth_play` (4, 2 km); screenshots `Saved/Screenshots/Seabed`. Next: match the shapes, colours and textures to ChatGPT's designs when G8 lands |
