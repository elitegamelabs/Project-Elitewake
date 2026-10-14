# Milestones

The order Elitewake is built in, from what stands today to a private release. Each milestone ends in something a tester can play, and each item in it is built, checked in Play and committed before the next ("compiling is not proof it works"). Design rules are in [DESIGN_REFERENCE.md](DESIGN_REFERENCE.md), test results in [VERIFICATION.md](VERIFICATION.md), day-to-day status in [PROJECT_GUIDE.md](PROJECT_GUIDE.md).

Drawn up October 13, 2026 at the owner's request, under the owner's delegation; the owner can reorder anything. **Blocked** items wait on an owner answer listed in the design reference's [open questions](DESIGN_REFERENCE.md#open-questions) or on owner art; they are skipped, not guessed.

Status: ✅ done · 🔨 in progress · ⏳ next · ⛔ blocked on the owner

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
| Cannon: fit it at a hardpoint, man it, aim within its arc, load round shot and fire | ⏳ |
| Hull health; round shot that strikes a hull and damages it | ⏳ |
| Holes below the waterline let water in (the ship settles and slows); bailing and repair | ⏳ |
| Sinking: a ship that fills or is destroyed goes down, leaving wreck crates with its hold | ⏳ |
| Integrated two-cannon fight Play check | ⏳ |
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

### October 14 owner handoff: world terrain for Claude

Terrain mesh construction is assigned to Claude. The five-region layout, substantial islands, long sailing distances, varied cliffs, one differently located cave system per island, regional terrain, solid island/seabed collision, selected 500-meter depths, and vegetation growth-stage mesh requirements are listed in [the world mesh milestone handoff](MILESTONE_WORLD_MESH_HANDOFF_2026-10-14.md). That checklist supplements M5 and supersedes its older four-region geography. It remains pending implementation and Play verification. Mode-specific rules are in [Single Player](SINGLE_PLAYER_RULES.md) and [Multiplayer](MULTIPLAYER_RULES.md).

Work takes the first ⏳ item of the earliest unfinished milestone that is not blocked. Each item: build, run its Play check and the regression checks it touches, update the docs, commit and push. Owner requests jump the queue. Before starting, check `git log` and `git status` for work committed by other sessions, and leave files someone else has uncommitted alone.
