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
| Small craft pass: ships rock on the swell and heel under sail | ✅ pending commit |
| Small craft pass: rudder feel and a finish pass on the raft, dinghy and sloop | ⏳ |
| Paddling animation for the raft; helm and capstan animations | ⏳ |
| Freshwater pond on the island for bass, catfish and piranha (a basin carved in the terrain and a lake water body; the spring is a 4.5 m puddle) | ⏳ |
| Campfire: cook Raw Fish and Raw Meat; eat raw (10% health, sickness) or cooked (20% / 25%) | ⛔ hunger restored by fish and meat, what sickness does and how long, campfire recipe and cooking time (open question 11) |
| Inventory and crafting screen redesign | ⛔ owner's layout images did not arrive |
| Integrated First Voyage Play check | ⏳ |

## M2 — Cannon fight

Goal: the design's "simple two-cannon fight before the deeper systems". Cannons fitted on the sloop's hardpoints, aimed and fired by a survivor, round shot that hits hulls, hull health, holes that let water in, bailing and repair, and a ship that sinks into floating wreck crates. Cannon art is a stand-in until the owner's. Ammo crafting, recipes and costs: ⛔ (open question 1); placeholders are test items only.

## M3 — Builder's Plan, Loom and Tanner ⛔

The ship section of the Builder's Plan as the fitting screen; sails at the Loom, helm and cannons at the Smithy; Tanner. Blocked on fitting recipes and costs (open question 1).

## M4 — Prologue and the Port ⛔ partly

Waking on the island with the Quartermaster's Journal, the Repair Kit and the dinghy, the Port, the innkeeper introduction (250 Copper and the four starter recipes), the inn torch placed for real. Blocked on the dinghy route, first carried item and room price (open question 2) and the Port's island (open question 7). Unblocked parts — the Journal as the Quartermaster's, the Repair Kit loop — can go ahead.

## M5 — Living world

Regional resources and vegetation beyond the coast (the four regions of the ecology guide), land wildlife with AI (wild animals, predators, the known roster), rivers and ponds, and taming's first steps (manatee passive taming).

## M6 — Survival depth

Cooking (campfire, then grill), spoilage, raw-food sickness, weather and storms, day and night (90 + 90 minutes), clothing and temperature.

## M7 — Persistence

Save and load for survivors, inventories, ships and the world; server restarts keep the game.

## M8 — Multiplayer menu and private release

Multiplayer from the main menu (now Coming Soon), the private release pipeline (`Docs/PRIVATE_RELEASE_AUTOMATION.md`, being set up separately), clean-PC, LAN and Internet tests. Any upload, account, runner or tester invitation needs the owner's go-ahead.

## M9 — Characters

Real survivor bodies: the owner's characters or MetaHumans on the mannequin skeleton, faces, hair and clothing; the character creator (in source, not in the menu path since October 13) returns where the owner wants it.

## How work proceeds

Work takes the first ⏳ item of the earliest unfinished milestone that is not blocked. Each item: build, run its Play check and the regression checks it touches, update the docs, commit and push. Owner requests jump the queue. Before starting, check `git log` and `git status` for work committed by other sessions, and leave files someone else has uncommitted alone.
