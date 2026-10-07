# Project Elitewake

A ship-centered pirate survival sandbox by **Elite Game Labs**, built in **Unreal Engine 5.8.3**.

Ships are the center of play: transportation, shelter, storage, workshop, combat platform, crew headquarters and progression, and they are highly customizable. Land bases are allowed but temporary, and players and wildlife can raid them. The loop is Prepare → Sail → Discover → Fight/Explore → Loot → Escape → Upgrade → Sail Farther. (The former "THE SHIP IS HOME" slogan was retired by owner decision on October 6, 2026.)

The current target is a small playable **0.01** foundation, with a single-player first private beta and server-authoritative gameplay architecture. Movement/stance, inventory/pickups/equipment/hotbar, contextual interaction, fresh-water drinking, hand-gathered resources and berry food, equipped-hatchet trees, pickaxe mining and the survival HUD have verified foundations. Native eating/freshness has opt-in automated coverage, but saved berries and player-facing consumption are not connected yet. The production ship loop, complete survival gameplay, remaining gathering/tools, crafting, persistence and final presentation remain open. Harvesting animations are recorded for later integration.

## Start here

- [Project guide](Docs/PROJECT_GUIDE.md): current status, next work, repository map and developer checks.
- [Design reference](Docs/DESIGN_REFERENCE.md): current authority, requirement tracking and owner decisions.
- [Verification record](Docs/VERIFICATION.md): dated acceptance results and their limits.
- [Historical reviews](Docs/ARCHIVE/CONTEXT_AND_DESIGN_REVIEWS.md): preserved source cross-references.

## Design authority

Design is governed by three guides maintained outside this repository. When sources conflict, the higher one wins:

1. Explicit owner decisions.
2. **Elitewake Shared Design Authority & Cross-Team Guide**: common authority, terminology, cross-team contracts, open decisions and retired rules.
3. Team guides: **Elitewake Game Development & Systems Bible** and **Elitewake Creative & World Bible**.
4. Repository docs and work notes, including this README and `Docs/`.

The October 5, 2026 **Master Game Design Bible** is an archive. Its section numbers are still used as source labels, but it is not edited or used as current authority. Status labels CONFIRMED, FUTURE, TBD and RECOMMENDED are preserved as assigned; missing values stay TBD until the owner decides them. See [Design reference](Docs/DESIGN_REFERENCE.md#authority) for the current decisions.

## Open the project

1. Install Unreal Engine **5.8.3**, Visual Studio's Unreal/C++ build components and **Git LFS**.
2. Clone this repository and run `git lfs pull`.
3. Open `EW.uproject` and allow the native modules to build.

Use a checkout outside OneDrive or other cloud synchronization folders. The active development checkout is `C:\UnrealProjects\EW`; its OneDrive copy is a backup. Required editor integrations are declared in `EW.uproject`; shared Unreal/Scenario connector endpoints are in `.codex/config.toml` and `.cursor/mcp.json`. Root `.mcp.json` is local and ignored.

## Repository

`Source/` contains gameplay and editor helpers, `Content/` contains Unreal assets, `Config/` contains shared settings, and `Scripts/Setup` / `Scripts/Verification` contain opt-in tooling. New game-specific assets belong in `Content/Elitewake/`.

Generated Unreal/IDE files are ignored. `main` holds verified, focused changes; use Git LFS for binary assets. Keep gameplay foundations in C++, assemble content in Blueprints, and preserve original code/art/story and the current design authority.
