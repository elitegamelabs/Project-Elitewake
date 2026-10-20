# Codex: your tasks

**Owner, October 20: no agent owns any file, API or system.** Claude helps the owner design the game; it holds no locks and reserves nothing. Codex, ChatGPT and Claude may all edit any file. To avoid collisions: pull first, check `git log` and the inbox for recent work on the same files, keep commits small, and say in the inbox when you start on a file another agent changed recently. The shared Unreal editor lock (one editor at a time on this PC) still applies to everyone.

Owner, October 16: Claude coordinates Codex, ChatGPT and Scenario and hands each the work that suits it. This file
is **Codex's list**: code, native tests, Python tests and Play-check scripts. ChatGPT's is
[CHATGPT.md](CHATGPT.md); Scenario's generation queue is [SCENARIO.md](SCENARIO.md).


**Report in the shared inbox (owner, October 17):** whenever you claim, finish, get stuck on or stop a task, add an entry to
[INBOX.md](INBOX.md) and push it with your work to `main`. Work left on a local branch or worktree is invisible to
Claude and the owner.

## Before you start

1. `git fetch && git pull --ff-only`. Claude, ChatGPT and the owner all commit to `main`.
2. Read the header of [../DELEGATED_TASKS.md](../DELEGATED_TASKS.md) first. It has the shared rules, the Unreal
   editor lock (one editor at a time on this PC) and the build and Play-check commands. No files are reserved for any
   agent (owner, October 20).
3. **Claim** a task by changing its status here to `CLAIMED (Codex, <date>)` and pushing that one-line change before
   you start. When finished, set it to `DONE <commit>` and write under it what you verified and what you could not.
   If you stop part-way, set it back to `OPEN` and say where you got to.
4. Compiling is not proof. Every gameplay change needs a Play check (`Scripts/Verification/run_play_check.py`) or a
   native test, with the result recorded in `Docs/VERIFICATION.md`.
5. Do not invent balance values: working numbers are *tuning*; anything the owner has not decided stays TBD.

## Owner-approved expansion: 40 islands and wildlife (October 18, 2026)

### C-WORLD40. Expand world from 26 to 40 islands — PARTIAL (Codex, 2026-10-20)
- **Owner directive:** exactly **8 islands in each of five regions**: Plains (Starter + Plains2–8), Winter1–8, Swamp1–8, Desert1–8, Jungle1–8. The 40-island wildlife specification is [WILDLIFE_DISTRIBUTION_26_ISLANDS.md](../WILDLIFE_DISTRIBUTION_26_ISLANDS.md) (legacy filename, **40-island content**). Owner approved this as the target and explicitly requests Claude/Codex implementation.
- **Preserve all 26 original islands and their existing locations, shapes, ports, placed structures, wildlife and saves**. Current `Scripts/Setup/world_layout.py` uses one seeded sequential RNG loop; **do not merely change counts** because it can reshuffle later regions. Snapshot baseline island records and append 14 deterministically generated new islands with stable keys. Maintain nearest-shore separation rules, regional orientation, starter safe beach/dock/pond/sloop and one port per region. Flag any impossible geometry/spacing constraints rather than silently changing the world scale.
- Audit every consumer of island count and island keys: terrain setup, water/ocean and nav, maps and discovery persistence, spawn generation, ports, save migration, multiplayer/world replication, milestones. Implement in small tested stages; the world and animal placement scripts are open to edit (owner, October 20); pull first and note in the inbox when you start on them.
- **Source checkpoint:** `world_layout.py` now appends fourteen deterministically seeded records and pins Port placement to the original island keys. New non-Swamp islands receive distinct terrain plans without changing the original islands' terrain assignments. Offline regressions pass for the original 26 complete records, all 40 keys/counts, all Port keys, deterministic additions, terrain-plan coverage, regional orientation, and spacing. The coastal map has **not** been rebuilt: the 40-island layout is not yet in-engine, and saves/discovery, multiplayer, and runtime performance have not been verified. Continue with the editor migration/rebuild and those acceptance checks before marking done.
- **Verify:** Python layout check: 40 unique islands, 8 per region, original 26 unchanged by key and coordinates/geometry, nearest-neighbor constraints; then Unreal Engine **5.8.3** native/Play checks and multiplayer/saved discovery regression; record in `Docs/VERIFICATION.md`. Mark CLAIMED/DONE and report in `Docs/Delegation/INBOX.md`.

### C-WILDLIFE40. Implement approved per-island animal additions — OPEN (after C-WORLD40 baseline)
- **Owner directive:** follow every row in [40-island wildlife distribution](../WILDLIFE_DISTRIBUTION_26_ISLANDS.md), including the 14 new islands. **Additive only**: preserve every existing animal spawn, behavior, taming food, level, home-island assignment and safe area. The table's wildlife are additional habitat-based populations, not replacement/exhaustive lists.
- First enumerate actual creature registry, spawn data, animal levels and island placements; reconcile with design guide (~60 estimate, count unverified) and flag missing creature assets or ambiguities. Do not fabricate implemented species or use provisional Plains species as proof of existing assets.
- Use biome-specific spawn rules and density tuning for land/cave/freshwater/coast/reef/open ocean; keep wild spiders cave-only/no wild jumping and tamed jump/climb rules, approved water aggro and port safety. Coordinate with existing C2 animal-island roaming task and Claude's animal placement work. Ensure wildlife stays on its assigned island.
- **Verify:** baseline existing spawns unchanged, 40 island distribution checks, creature coverage audit, no dangerous spawns in safe areas, no aquatic creatures on land, native/Play and multiplayer checks in Unreal **5.8.3**; log in `Docs/VERIFICATION.md`, report to INBOX. If missing assets block a species, mark explicitly pending instead of claiming it spawned.

## New tasks (October 16)

### C7. Owner's 12 game-improvement requests — PARTIAL (Codex, 2026-10-20; commit `41a050b`)
- **Source:** owner-pasted task list received October 20, 2026. Full request is in the conversation attachment; implementation status will be recorded in the dated report and `Docs/VERIFICATION.md`.
- **Independent code scope:** map label and map-only messages; Xbox hotbar mappings/prompts; inventory Y quick-assign; compass contrast; persistent pause-menu brightness and mouse/controller look sensitivity.
- **Map:** also T9 below. Preserve the player marker, support free pan/zoom, and use current world region actors rather than hard-coded island positions.
- **Mode rules:** island placement restrictions apply in multiplayer only; single-player remains unrestricted; crafting is never gated by claims; ship customization is outside island claims; Ports are excluded.
- **Open to Codex (owner, October 20):** cave crystals touch the cave setup scripts and ship furnishing/windows touch the ship builders; edit them directly. Helm prompt cleanup is in the ongoing C7 work. Ship-deck placement needs an audit of the current ship placement interface; claim restrictions need an island ownership API and unresolved timer rules.
- **Verification:** add appropriate native/Play acceptance for implemented work and update `Docs/VERIFICATION.md`. Keep incomplete pieces explicit. Do not invent crystal identity, claim durations or ship dimensions.

- **C7 cave-resource implementation subtask:** PARTIAL (Codex, 2026-10-20; code commit `38b817b`). Added reusable pickaxe-tier requirements, server-randomized 4–8 total stock, timed respawn, and replicated node visibility/collision. A two-player Play fixture verifies the Metal-tier gate, depletion, and respawn. Production cave/winter resource definitions, node meshes/placements, and the canonical Metal Pick item are still absent; do not mark the resource feature integrated until those exist.
- **C7 ship interior/window subtask:** PARTIAL (Codex, 2026-10-20; `46d37eb`, source checkpoint `dd7a907`, geometry test `75dc63d`). Schooner/Brigantine source generates closed glass panes while retaining complex hull collision; the glass material and one versioned Schooner mesh are saved, but the mesh predates the added surgeon-table source. A focused helper now generates versioned Sloop/Schooner/Brigantine hulls and updates only their definition references. The aft-port lower-deck surgeon-table prop is visual only; no Cavalier builder exists in the current source. New offline geometry test `Scripts.Tests.test_ship_window_geometry` passes, proving the source emits six glass pane boxes in slot 3 with expected front locations and restores the caller slot; this does not verify actual ship-specific meshes or runtime collision. Two Unreal Editor processes were active on the latest check, so the helper and two-player Play verification remain unrun; no asset integration or water sealing is claimed. See the latest C7 entry in `Docs/Delegation/INBOX.md` and `Docs/VERIFICATION.md`. No scenery art is included.
- **Progress:** map overview/region label/map-only hint, Xbox hotbar prompts and mappings, inventory Y quick-assign, darker compass backing, persistent brightness/look controls, and simplified sailing-ship helm prompt are implemented in source (`41a050b`, `e3161d7`). UE 5.8.3 build and focused native hotbar/sailing-authority tests pass; Python syntax and whitespace checks pass. `verify_resource_mining_lifecycle_play.py` passes five two-player listen-server/client checkpoints for its test fixture only. `verify_map_play.py` passes eight two-player listen-server/client checkpoints for local map lifecycle and controls (`cf6eca0`). Physical Xbox controller input, map readability at zoom bounds, and options presentation remain unverified in Play. Production cave-resource content, ship interiors/windows, general deck placement, and island-claim restrictions remain incomplete; see `Docs/REPORTS/2026-10-20_C7_GAME_IMPROVEMENTS_PARTIAL.md`.

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

### C3. Clear the deprecated `GetMovementBase` warning — PARTIAL (Codex paused 2026-10-19)
- **Why:** `Source/EW/EWCharacter.cpp` line 311 calls `ACharacter::GetMovementBase`, deprecated in UE 5.8. It still
  compiles, but will break at the next engine upgrade.
- **Do:** switch it to `GetMovementBaseObject` or `GetMovementBaseInterfaceData`, keeping the same behaviour. It is
  used for footstep surfaces (deck when the base is a ship).
- **Done when:** the build has no C4996 warning there and `verify_ship_deck_play.py` and `verify_audio_play.py` pass.
- **Pause state:** code and build-warning acceptance pass. Deck and audio Play checks still need rerunning; see the October 19 handoff report.

### C4. Sails set in five positions, raised and lowered from the helm — PARTIAL (Codex paused 2026-10-19)
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
- **Done when:** checks pass, VERIFICATION records it, and you report in INBOX.md. Say in INBOX.md when you
  start on `EWShip.cpp`, so concurrent edits do not collide.
- **Pause state:** implementation, native coverage, build and the 11-step network sailing check pass. Sail-trim and the other affected ship regressions were not all rerun after the final change; see the October 19 handoff report.

### C5. Craftable plain white flags on flag mounts — DONE by Claude (2026-10-18; it was unclaimed and the owner asked Claude to do what the others are not doing). Nothing for Codex here.
- **Why:** owner, October 17: sloop 2 flag positions, brigantine 3, Cavalier 4, all empty at first; a crafted flag is
  plain clean white; flags install, remove and swap, flutter in the wind, and weather only from combat damage.
- **Do:** a Flag item (recipe values TBD: ask in OPEN_QUESTIONS, use a placeholder recipe marked *tuning*), a
  `Flag` mount type, flag mounts on the sloop and brigantine definitions (positions: masthead and stern ensign staff;
  the ship build scripts are open to every agent), install/remove through the existing
  fitting flow, and a cloth flag mesh that flutters with the world wind (UEWWindSubsystem). Combat damage and tearing
  come later.
- **Done when:** a Play check installs, swaps and removes a flag on the sloop on server and client; reported in INBOX.md.

### C6. Bring `verify_hull_damage_play` up to date — DONE `acbb898` (Codex, 2026-10-20)
- **Why:** since the sloop lost her hull gunports (`4870f1f`, owner, October 17) her cannons stand behind a two-cannon
  railing; the check still looks for the old `StarboardCannon` mount and times out at its first step.
- **Do:** fit `DA_TestRailingTwoCannon` at `StarboardRailing` first and use `StarboardCannon1`, as
  `verify_cannon_fight_play.py` does (including its hold-again loop). Keep its three checks (planking struck, health
  falls by one shot on both machines, a hole drawn on the client).
- **Verified:** the two-player `verify_hull_damage_play.py` run passes on the coastal map. Because the saved map contains only the sloop, the check spawns a temporary Schooner from its existing definition on the listen server; it is not saved to the map. The client fits the two-cannon railing, installs and mans the first starboard cannon, strikes the Schooner's planking, and sees replicated health and a shot hole placed within 1.5 cm of impact. Result: `Saved/HullDamagePlayResultC6.json`; implementation commit `acbb898`.

## Earlier tasks that suit you (full text in [../DELEGATED_TASKS.md](../DELEGATED_TASKS.md); claim them there)

| Task | What | Status |
|---|---|---|
| T28 | Python unit tests for `world_layout.py` / `world_terrain.py` | OPEN |
| T29 | Native tests for the cobweb and wildlife rest | OPEN |
| T31 | Why the sinking check sometimes cannot open a crate | OPEN |
| T32 | Directional swimming animations | OPEN |
| T23 | Native tests for the sound library | OPEN |
| T20 | Native tests for leaks and bailing | PARTIAL — native test passes; fresh Play rerun open |
| T14 | Native tests for swing kinds and gather gains | OPEN |
| T24 | Move the hull damage check to the ships test map | OPEN |
| T25 | A packaged game's frame rate on the bigger world | OPEN |
| T26 | What fills video memory with two players' views | OPEN |
| T22 | A modelled wreck crate, and a native fill-sinking test | OPEN |
| T21 | A modelled bailing bucket | PARTIAL — asset integrated; visual acceptance open |

Suggested order: C3 (quick), C1, T28, T29, T31, then the rest.
