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
| Island rock formations rebuilt to look natural | ✅ `e0443c4` (with the rock rework above) |
| The five-region world (owner, October 15): Plains centre with the starter island and five more, Winter north, Swamp south, Desert east, Jungle west, 5+ islands each, 800–2,000 m sea gaps, regional terrain, dressing, animals, sea life and climate on all 26 islands | ✅ `90978cc` |
| Ports: one per region (owner), stone quay, pier, plaza, nine masonry buildings with shops marked, town wall and gate, landmark lighthouse, regional character | ✅ `618acbb` (vendors, names, safe zones open) |
| Caves: one per island, inland, cliff-face and coastal entrances, walkable passage and chamber | ✅ `fb35edc` (contents wait for design values) |
| Grass you can see as plants on the Plains and Jungle islands | ✅ `fb35edc` |
| Island landmarks: one per island (sea stacks, shore arch, standing stones, spire, giant dead tree) | ✅ `fb35edc` |
| Larger islands (open question for the owner) | ⏳ |
| Day and night: 90 real minutes each (owner), server-owned clock, moving sun, moon, darker nights | ✅ `2ac71d9` (stars, saving the hour, night climate open) |
| Winter snow: falling snow round the survivor in the Winter region, stopping under roofs; snow on Winter's plants and berry bushes | ✅ `d59f225` |
| Six glowing reefs (design reference; places decided provisionally): one per region and a second in the Plains | ✅ `d86efa3` |
| Environment and world (M5 terrain and vegetation) | ⏳ |

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
