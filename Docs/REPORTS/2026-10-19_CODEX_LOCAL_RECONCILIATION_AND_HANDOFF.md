# Codex local reconciliation and pause handoff

**Date:** October 19, 2026  
**State:** Codex paused at the owner's request. Unreal Editor, Unreal commandlets and Play checks are closed. No editor lock remains.

This report exists so Claude can see the local work that was not visible from `main`. It distinguishes verified implementation, partially verified work, excluded drafts, and previously published project systems. Documentation, implementation, asset integration and in-game verification are separate states.

## Repository reconciliation

- Reconciled the old local checkout against GitHub `main` at `307a897` without overwriting Claude's newer versions of the coastal map, ship timber material, milestones, Claude report, verification ledger, world-layout tests or core-tools Play check.
- Preserved the complete pre-reconciliation checkout in local commit `e6b0ca9` on `codex/local-reconciliation-snapshot-20261019`.
- Preserved every later local file, including unfinished drafts, on the published recovery branch `codex/local-work-handoff-20261019` at commit `6aee038`.
- Kept `Config/DefaultEditor.ini` out of every commit. Its SHA-256 remained `0E61E2200AEAB9EC14A2CD1C55F024F1CCAB668D1C43759D89B71DD9D7B0185A`.
- Added ignores for local ZIP source bundles and the locally installed `Blacksmith_Setup` and `Burlap_Sacks` Marketplace folders. Those files remain on the workstation and are not represented as redistributable project source.

## Verified implementation selected for `main`

### Five-position sails — C4 partial acceptance

- Expanded the replicated sail setting to **Furled, Quarter, Half, ThreeQuarter and Full**, corresponding to 0%, 25%, 50%, 75% and 100% sail.
- Sail draw height, propulsion, heel and rigging audio now follow the fraction instead of a three-state approximation.
- At a sailing ship's helm, keyboard Up/Down and Xbox D-pad Up/Down step through the five positions. The first step is immediate, then holding repeats every 0.6 seconds.
- Rafts and other paddled craft retain their simple easy/hard stroke behavior by moving two 25% steps per command.
- W/S helm behavior remains available. Ladder movement and gunport controls keep their existing priority outside the helm.
- Leaving the helm clears held sail-step input so a stale command cannot keep changing sail after dismount.
- Added `Elitewake.Ships.SailPositions` native coverage and updated the affected ship Play scripts to use four steps to reach full sail.
- **Verified:** Unreal EWEditor compiled successfully on UE 5.8.3; the focused native ship suite passed 8/8; `verify_ship_sailing_play.py` passed 11/11 on a listen server plus client. It observed 25/50/75/100% replicated sail settings, 21.6 m travel, 54.45 degrees of turning, 75.4 cm client gap, wake/roll/pitch/heel/wheel feedback, and an anchored final speed of zero.
- **Still required:** the owner paused work before the sail-trim rerun completed. The updated trim, schooner, brigantine, first-voyage, deck, look, anchor-chain and small-craft checks were syntax-checked but not all rerun in Unreal after this change. Human/controller feel remains unverified.

### UE 5.8 movement-base warning — C3 partial acceptance

- Replaced the deprecated `ACharacter::GetMovementBase()` call with `GetMovementBaseObject()` plus a safe primitive-component cast, retaining ship-deck and stone footstep selection.
- **Verified:** the next UE 5.8.3 build completed without the old C4996 warning.
- **Still required:** rerun `verify_ship_deck_play.py` and `verify_audio_play.py` before marking C3 done.

### Hull-damage regression coverage — C6 partial acceptance

- Added native `Elitewake.Ships.HullDamage` coverage for initial hull health, repeated round-shot damage, local hole position and hole normal.
- Updated stale native ship expectations to Claude's newer anchor-chain, sailing-pace, upwind-factor and alternate ladder-landing behavior. Gameplay values were retained; only obsolete test expectations changed.
- **Verified:** the hull-damage native test passed as part of the 8/8 focused ship suite.
- **Still required:** the specific listen-server/client `verify_hull_damage_play.py` acceptance described by C6 was not rerun in this pause cycle.

### Leaks, bailing and bucket — T20/T21 partial acceptance

- Added native `Elitewake.Ships.Leaks` coverage: above-water holes do not leak, submerged holes do, admitted water adds ship load and settling, water caps at the existing limit, and one bucket stroke removes the existing `BailPerStroke` amount.
- Added a repeatable bucket builder and integrated `SM_BailBucket_v1`: open top, fitted bottom, tapered oak staves, two iron hoops and rope bail.
- Corrected the leak Play check's remote-client survivor lookup so it does not depend on an empty editor JSON PlayerId query during Play.
- **Verified:** the native leaks test passed as part of the 8/8 focused ship suite. Earlier local evidence recorded the five-step leak/bailing Play check passing.
- **Still required:** the dedicated bucket screenshot/capture timed out, so human visual review and a fresh post-reconciliation Play rerun remain open. This is not a final art claim.

## Local work preserved only on the recovery branch

The following files are intentionally **not selected for `main`**. They remain recoverable at `codex/local-work-handoff-20261019` / `6aee038` for Claude to inspect.

### Tortoise shell draft

- A procedural shell revision added raised vertebral, costal and marginal scutes with nested growth rings.
- The generated tortoise mesh/material assets were changed locally.
- It was not rerun and visually accepted in Unreal after reconciliation, and `build_animals.py` is listed as Claude-owned. It therefore remains a draft and was not used to overwrite Claude's copy.

### Starting fleet and Cavalier placeholder

- A draft setup attempted to place Sloop, Schooner, Brig and Cavalier at increasing sizes on the starter island.
- The Cavalier used a scaled Brigantine blockout. That conflicts with the requirement for a distinct Cavalier design and cannot serve as implementation evidence.
- The draft also predates the latest October 18 ship authority in several details. It was not rerun after reconciliation. The Cavalier asset, setup script and report remain recovery-branch material only.

### Private release automation draft

- Drafted Windows Shipping packaging, temporary crypto configuration and a GitHub Action intended to update a private rolling prerelease after pushes to `main`.
- It requires the private self-hosted UE 5.8 runner and `EW_PAK_AES_KEY` secret and has not completed a clean packaging/release acceptance.
- It was excluded from `main` so this handoff push cannot unexpectedly start an unconfigured release job. Encryption deters casual extraction but cannot make client assets impossible to recover.

### Conflicting ore work excluded during reconciliation

- An older local ore pass used obsolete region and tool-tier rules. It was excluded in favor of newer owner authority: Ruby, Sapphire, Emerald and Obsidian cave resources across regions; Emerald also in Winter mountains; Coal only in Winter mountains; Metal Pick or higher; 4–8 per node; 60-minute respawn.
- The obsolete version remains reachable in the recovery history only and must not be treated as current design.

## Verification record for this pause

- Unreal Editor/build processes: closed.
- Editor lock: absent.
- Updated Python verification scripts: compile/syntax check passed.
- UE 5.8.3 EWEditor build: passed; deprecated movement-base warning removed.
- Focused native ship suite: **8/8 passed** — BoardingAndAnchor, BuiltInFittings, FittingAuthority, HullDamage, Leaks, SailingAuthority, SailPositions, WeightAndOverload.
- Network sailing Play check: **11/11 passed**; result was written locally to `Saved/ShipSailingPlayResult.json`.
- Full native run still has the previously documented headless `Title.RoutedKeyboardMouseAndWheel` NullRHI geometry failure. This was not introduced by the ship work.
- Sail-trim rerun: interrupted by the owner's pause and not claimed as passed.

## Existing project work already on GitHub

The project-wide record remains [VERIFICATION.md](../VERIFICATION.md). It documents the previously published HUD, inventory/hotbar, gathering, crafting, objectives and prologue fixtures, map, title/menu flow, save/restore, multiplayer foundations, ports, world/island generation, caves, resources, wildlife, swimming/ocean, ships, fittings, cargo, cannons, damage, sailing, UI and related checks. This report does not reclassify those systems; it records the local changes Claude could not see.

## Resume guidance

1. Read this report and inspect `codex/local-work-handoff-20261019` before deleting any recovery branch.
2. Treat the five-position sails as partially accepted until the remaining affected Play checks run.
3. Do not restore the Cavalier placeholder as production art; build the distinct three-level class under the latest owner authority.
4. Do not enable the private release workflow until its runner, secret, clean Shipping package and release behavior are verified.
5. Reconcile any new owner redesign decisions before resuming implementation. Codex has stopped work and will not run Unreal or change gameplay until the owner resumes it.
