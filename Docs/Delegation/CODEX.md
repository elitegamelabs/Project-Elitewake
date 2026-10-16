# Codex: your tasks

Owner, October 16: Claude coordinates Codex, ChatGPT and Scenario and hands each the work that suits it. This file
is **Codex's list**: code, native tests, Python tests and Play-check scripts. ChatGPT's is
[CHATGPT.md](CHATGPT.md); Scenario's generation queue is [SCENARIO.md](SCENARIO.md).

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
| T12 | Tests for the world layout rules | OPEN |
| T24 | Move the hull damage check to the ships test map | OPEN |
| T25 | A packaged game's frame rate on the bigger world | OPEN |
| T26 | What fills video memory with two players' views | OPEN |
| T22 | A modelled wreck crate, and a native fill-sinking test | OPEN |
| T21 | A modelled bailing bucket | OPEN |

Suggested order: C3 (quick), C1, T28, T29, T31, then the rest.
