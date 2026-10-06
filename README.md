# Project Elitewake

A ship-centered pirate survival sandbox by **Elite Game Labs**, built in **Unreal Engine 5.8.3**.

**THE SHIP IS HOME:** transportation, shelter, storage, workshop, combat platform, crew headquarters and progression. The loop is Prepare → Sail → Discover → Fight/Explore → Loot → Escape → Upgrade → Sail Farther.

The current target is a small playable **0.01** foundation, with a single-player first private beta and server-authoritative gameplay architecture. Movement/stance, inventory/pickups/equipment/hotbar and the survival HUD have verified foundations. The production ship loop, complete survival gameplay, persistence and final presentation remain open.

## Start here

- [Project guide](Docs/PROJECT_GUIDE.md): current status, next work, repository map and developer checks.
- [Design reference](Docs/DESIGN_REFERENCE.md): current authority, requirement tracking and owner decisions.
- [Verification record](Docs/VERIFICATION.md): dated acceptance results and their limits.
- [Historical reviews](Docs/ARCHIVE/CONTEXT_AND_DESIGN_REVIEWS.md): preserved source cross-references.

## Open the project

1. Install Unreal Engine **5.8.3**, Visual Studio's Unreal/C++ build components and **Git LFS**.
2. Clone this repository and run `git lfs pull`.
3. Open `EW.uproject` and allow the native modules to build.

Use a checkout outside OneDrive or other cloud synchronization folders. The active development checkout is `C:\UnrealProjects\EW`; its OneDrive copy is a backup. Required editor integrations and shared connector endpoints are declared in the project/configuration files.

## Repository

`Source/` contains gameplay and editor helpers, `Content/` contains Unreal assets, `Config/` contains shared settings, and `Scripts/Setup` / `Scripts/Verification` contain opt-in tooling. New game-specific assets belong in `Content/Elitewake/`.

Generated Unreal/IDE files are ignored. `main` holds verified, focused changes; use Git LFS for binary assets. Keep gameplay foundations in C++, assemble content in Blueprints, and preserve original code/art/story and the current design authority.
