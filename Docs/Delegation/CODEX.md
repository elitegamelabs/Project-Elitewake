# Codex: your tasks

Owner, October 16: Claude coordinates Codex, ChatGPT and Scenario and hands each the work that suits it. This file
is **Codex's list**: code, native tests, Python tests and Play-check scripts. ChatGPT's is
[CHATGPT.md](CHATGPT.md); Scenario's generation queue is [SCENARIO.md](SCENARIO.md).


**Report to Claude (owner, October 17):** whenever you claim, finish, get stuck on or stop a task, add an entry to
[INBOX.md](INBOX.md) and push it with your work to `main`. Work left on a local branch or worktree is invisible to
Claude and the owner.

## Before you start

1. `git fetch && git pull --ff-only`. Claude, ChatGPT and the owner all commit to `main`.
2. Read the header of [../DELEGATED_TASKS.md](../DELEGATED_TASKS.md) first. It has the shared rules, the Unreal
   editor lock (one editor at a time on this PC), the build and Play-check commands, and the **Claude is working on**
   list. Never edit the files on that list; leave a note under your task instead.
3. **Claim** a task by changing its status here to `CLAIMED (Codex, <date>)` and pushing that one-line change before
   you start. When finished, set it to `DONE <commit>` and write under it what you verified and what you could not.
   If you stop part-way, set it back to `OPEN` and say where you got to.
4. Compiling is not proof. Every gameplay change needs a Play check (`Scripts/Verification/run_play_check.py`) or a
   native test, with the result recorded in `Docs/VERIFICATION.md`.
5. Do not invent balance values: working numbers are *tuning*; anything the owner has not decided stays TBD.

## Owner-approved expansion: 40 islands and wildlife (October 18, 2026)

### C-WORLD40. Expand world from 26 to 40 islands — OPEN (Codex/Claude coordination required)
- **Owner directive:** exactly **8 islands in each of five regions**: Plains (Starter + Plains2–8), Winter1–8, Swamp1–8, Desert1–8, Jungle1–8. The 40-island wildlife specification is [WILDLIFE_DISTRIBUTION_26_ISLANDS.md](../WILDLIFE_DISTRIBUTION_26_ISLANDS.md) (legacy filename, **40-island content**). Owner approved this as the target and explicitly requests Claude/Codex implementation.
- **Preserve all 26 original islands and their existing locations, shapes, ports, placed structures, wildlife and saves**. Current `Scripts/Setup/world_layout.py` uses one seeded sequential RNG loop; **do not merely change counts** because it can reshuffle later regions. Snapshot baseline island records and append 14 deterministically generated new islands with stable keys. Maintain nearest-shore separation rules, regional orientation, starter safe beach/dock/pond/sloop and one port per region. Flag any impossible geometry/spacing constraints rather than silently changing the world scale.
- Audit every consumer of island count and island keys: terrain setup, water/ocean and nav, maps and discovery persistence, spawn generation, ports, save migration, multiplayer/world replication, milestones. Implement in small tested stages; coordinate with Claude before touching Claude-owned world or animal placement scripts.
- **Verify:** Python layout check: 40 unique islands, 8 per region, original 26 unchanged by key and coordinates/geometry, nearest-neighbor constraints; then Unreal Engine **5.8.3** native/Play checks and multiplayer/saved discovery regression; record in `Docs/VERIFICATION.md`. Mark CLAIMED/DONE and report in `Docs/Delegation/INBOX.md`.

### C-WILDLIFE40. Implement approved per-island animal additions — OPEN (after C-WORLD40 baseline)
- **Owner directive:** follow every row in [40-island wildlife distribution](../WILDLIFE_DISTRIBUTION_26_ISLANDS.md), including the 14 new islands. **Additive only**: preserve every existing animal spawn, behavior, taming food, level, home-island assignment and safe area. The table's wildlife are additional habitat-based populations, not replacement/exhaustive lists.
- First enumerate actual creature registry, spawn data, animal levels and island placements; reconcile with design guide (~60 estimate, count unverified) and flag missing creature assets or ambiguities. Do not fabricate implemented species or use provisional Plains species as proof of existing assets.
- Use biome-specific spawn rules and density tuning for land/cave/freshwater/coast/reef/open ocean; keep wild spiders cave-only/no wild jumping and tamed jump/climb rules, approved water aggro and port safety. Coordinate with existing C2 animal-island roaming task and Claude's animal placement work. Ensure wildlife stays on its assigned island.
- **Verify:** baseline existing spawns unchanged, 40 island distribution checks, creature coverage audit, no dangerous spawns in safe areas, no aquatic creatures on land, native/Play and multiplayer checks in Unreal **5.8.3**; log in `Docs/VERIFICATION.md`, report to INBOX. If missing assets block a species, mark explicitly pending instead of claiming it spawned.

## New tasks (October 16)

### C1. Trees that fall and stay to be chopped — OPEN
- **Why:** owner, October 16 ([ELEPHANT_FELLED_TREES_HARVESTABLE](../ELEPHANT_FELLED_TREES_HARVESTABLE_2026-10-16.md)):
  a tree an elephant knocks down stays on the ground and is chopped with a hatchet for its wood. Elephants don't
  exist yet; this task builds the tree's half so they can use it later.
- **Do:** in `Source/EW/Gathering/EWHarvestTree.*`, add a server-authoritative `Fell(FVector Direction)` that turns a
  standing tree into a fallen log. The tree tips over that way across a couple of seconds (*tuning*) and lies on the
  ground. Its collision follows it. It keeps the Wood and Thatch it had left, and the state is replicated, so a client
  joining late sees it lying. The hatchet keeps working on the fallen log with the same yields, chips and sounds, until
  it is empty. Yields must not be duplicated: a log gives only what the tree had left. Leave what happens to an
  emptied log, and when (cleanup, regrowth), as the tree does today. Add an open question in
  `Docs/OPEN_QUESTIONS_2026-10-15.md` rather than picking a duration.
- **Test:** a native test (fell a spawned tree: it is felled, its remaining resources are unchanged, and a second
  `Fell` does nothing). Also a Play check `verify_felled_tree_play.py` on `Lvl_CoastalPlayground`: the server fells
  the oak nearest the spawn; the client sees it lying within a few seconds, walks into it and is stopped, then chops
  it and gets 3 Wood and 1 Thatch a blow until it is empty.
- **Done when:** both pass, and VERIFICATION and DESIGN_REFERENCE (Gathering) describe it.

### C2. Animals stay on their own island — OPEN
- **Why:** owner, October 16 ([ELEPHANT_DESTRUCTION_WILDLIFE_ROAMING_AND_SPIDER_MILESTONES](../ELEPHANT_DESTRUCTION_WILDLIFE_ROAMING_AND_SPIDER_MILESTONES_2026-10-16.md)):
  animals wander naturally on their assigned islands. Since the islands grew, nothing checks that a land animal never
  wanders into the sea or off its island.
- **Do:** read how `AEWAnimal` picks wander targets (`Source/EW/Wildlife/EWAnimal.*`). Keep land animals' targets on
  their home island's land; the island is in `Scripts/Setup/world_layout.py`, and the animal's spawn point is a good
  home. Keep the resting optimisation (`FEWWildlifeRest`: wildlife more than 200 m from every survivor rests). Do not
  change `build_animals.py` placement (Claude's).
- **Test:** a Play check: stand a survivor among each region's animals for a few minutes of game time, and record that
  every awake land animal stayed above the sea and within its island.
- **Done when:** it passes and VERIFICATION has it.

### C3. Clear the deprecated `GetMovementBase` warning — OPEN
- **Why:** `Source/EW/EWCharacter.cpp` line 311 calls `ACharacter::GetMovementBase`, deprecated in UE 5.8. It still
  compiles, but will break at the next engine upgrade.
- **Do:** switch it to `GetMovementBaseObject` or `GetMovementBaseInterfaceData`, keeping the same behaviour. It is
  used for footstep surfaces (deck when the base is a ship).
- **Done when:** the build has no C4996 warning there and `verify_ship_deck_play.py` and `verify_audio_play.py` pass.

### C4. Sails set in five positions, raised and lowered from the helm — OPEN
- **Why:** owner, October 17 (`Docs/MILESTONES.md`, "Owner ship systems expansion"): sail positions 0/25/50/75/100%,
  raised and lowered progressively by holding keyboard Up/Down or the Xbox D-pad Up/Down at the helm; no wind
  propulsion at 0%. Today `EEWSailState` has Furled, Half and Full, stepped by forward/back input
  (`Source/EW/Ships/EWShip.*`, `AEWCharacter` helm input).
- **Do:** replace the three states with a replicated sail setting (0, 25, 50, 75, 100%) that holding Up/Down moves one
  step at a time (tuning: a step every 0.6 s), feeding `ComputeTargetSpeed` (speed share = setting) and the sails'
  drawn height (as Half scales them now; Claude's `ShowSailFill` reads the sail state, keep it working). Keep W/S
  helm forward/back working the same way if they are used for this today; check `Docs/DESIGN_REFERENCE.md` (Helm).
  The crew-dependency rule (only sails with assigned NPC operators answer the helm) needs NPCs that do not exist yet:
  leave it out and note it.
- **Test:** update `verify_ship_sailing_play.py`, `verify_sail_trim_play.py` and any check that sets full sail;
  add native tests for the setting's steps.
- **Done when:** checks pass, VERIFICATION records it, and you report in INBOX.md. Claude owns `EWShip.cpp` too:
  say in INBOX.md when you start so edits do not collide.

### C5. Craftable plain white flags on flag mounts — DONE by Claude (2026-10-18; it was unclaimed and the owner asked Claude to do what the others are not doing). Nothing for Codex here.
- **Why:** owner, October 17: sloop 2 flag positions, brigantine 3, Cavalier 4, all empty at first; a crafted flag is
  plain clean white; flags install, remove and swap, flutter in the wind, and weather only from combat damage.
- **Do:** a Flag item (recipe values TBD: ask in OPEN_QUESTIONS, use a placeholder recipe marked *tuning*), a
  `Flag` mount type, flag mounts on the sloop and brigantine definitions (positions: masthead and stern ensign staff;
  ask Claude in INBOX.md for exact points, Claude owns the ship build scripts), install/remove through the existing
  fitting flow, and a cloth flag mesh that flutters with the world wind (UEWWindSubsystem). Combat damage and tearing
  come later.
- **Done when:** a Play check installs, swaps and removes a flag on the sloop on server and client; reported in INBOX.md.

### C6. Bring `verify_hull_damage_play` up to date — OPEN
- **Why:** since the sloop lost her hull gunports (`4870f1f`, owner, October 17) her cannons stand behind a two-cannon
  railing; the check still looks for the old `StarboardCannon` mount and times out at its first step.
- **Do:** fit `DA_TestRailingTwoCannon` at `StarboardRailing` first and use `StarboardCannon1`, as
  `verify_cannon_fight_play.py` does (including its hold-again loop). Keep its three checks (planking struck, health
  falls by one shot on both machines, a hole drawn on the client).
- **Done when:** it passes on the coastal map with a listen server plus client; reported in INBOX.md.

## Earlier tasks that suit you (full text in [../DELEGATED_TASKS.md](../DELEGATED_TASKS.md); claim them there)

| Task | What | Status |
|---|---|---|
| T28 | Python unit tests for `world_layout.py` / `world_terrain.py` | OPEN |
| T29 | Native tests for the cobweb and wildlife rest | OPEN |
| T31 | Why the sinking check sometimes cannot open a crate | OPEN |
| T32 | Directional swimming animations | OPEN |
| T23 | Native tests for the sound library | OPEN |
| T20 | Native tests for leaks and bailing | OPEN |
| T14 | Native tests for swing kinds and gather gains | OPEN |
| T24 | Move the hull damage check to the ships test map | OPEN |
| T25 | A packaged game's frame rate on the bigger world | OPEN |
| T26 | What fills video memory with two players' views | OPEN |
| T22 | A modelled wreck crate, and a native fill-sinking test | OPEN |
| T21 | A modelled bailing bucket | OPEN |

Suggested order: C3 (quick), C1, T28, T29, T31, then the rest.
