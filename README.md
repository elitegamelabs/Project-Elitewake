# Project Elitewake

A ship-centered pirate survival sandbox by **Elite Game Labs**, built in **Unreal Engine 5.8.3**.

Ships are the center of play: transportation, shelter, storage, workshop, combat platform, crew headquarters and progression, and they are highly customizable. Land bases are allowed but temporary, and players can raid them; wild animals do not aggro player items. The loop is Prepare → Sail → Discover → Fight/Explore → Loot → Escape → Upgrade → Sail Farther. (The former "THE SHIP IS HOME" slogan was retired by owner decision on October 6, 2026.)

The current target is a small playable **0.01** foundation with server-authoritative gameplay and private multiplayer testing. Movement/stance, survival HUD, inventory/equipment/hotbar, interaction, gathering and berry food have verified foundations. New local work adds crafting transactions and larger inventory/crafting grids, an M-key surrounding-map preview, per-player inn torch pickup, ordered objectives and completion recipe rewards, and an F10 Host/Join/Leave test panel. Normal play still starts empty; starter recipes remain opt-in fixtures until the production prologue completion trigger is agreed.

The latest verification passes 18 native tests, ten separate-process connection lifecycle checkpoints and five cooked Windows loopback checks. These are scoped foundation checks, not a finished sandbox or LAN/Internet certification. Production ships, complete survival, combat, world/Port content, prologue, persistence, final artwork/animations and balance remain open. Private packages stay outside Git; see the [private testing guide](Docs/PRIVATE_MULTIPLAYER_TESTING.md) for build steps and remaining acceptance.

## Start here

- [Project guide](Docs/PROJECT_GUIDE.md): current status, next work, repository map and developer checks.
- [Design reference](Docs/DESIGN_REFERENCE.md): current authority, requirement tracking and owner decisions.
- [Verification record](Docs/VERIFICATION.md): dated acceptance results and their limits.
- [Historical reviews](Docs/ARCHIVE/CONTEXT_AND_DESIGN_REVIEWS.md): preserved source cross-references.

## Design authority

Design is governed by three guides maintained outside this repository. When sources conflict, the higher one wins:

1. Explicit owner decisions, including the overriding [complete October 9 design update](Docs/OCTOBER_9_COMPLETE_REVIEW.md) and subsequent clarifications.
2. **Elitewake Shared Design Authority & Cross-Team Guide**: common authority, terminology, cross-team contracts, open decisions and retired rules.
3. Team guides: **Elitewake Game Development & Systems Bible** and **Elitewake Creative & World Bible**.
4. Repository docs and work notes, including this README and `Docs/`.

The October 5, 2026 **Master Game Design Bible** is an archive. Its section numbers are still used as source labels, but it is not edited or used as current authority. Status labels CONFIRMED, FUTURE, TBD and RECOMMENDED are preserved as assigned; missing values stay TBD until the owner decides them. See [Design reference](Docs/DESIGN_REFERENCE.md#authority) for the current decisions.

## Open the project

1. Install Unreal Engine **5.8.3**, Visual Studio's Unreal/C++ build components and **Git LFS**.
2. Clone this repository and run `git lfs pull`.
3. Open `EW.uproject` and allow the native modules to build.

Use a checkout outside OneDrive or other cloud synchronization folders. The active development checkout is `C:\UnrealProjects\EW`; its OneDrive copy is a backup. Required editor integrations are declared in `EW.uproject`; shared Unreal/Scenario connector endpoints are in `.codex/config.toml` and `.cursor/mcp.json`. Root `.mcp.json` is local and ignored. Open the active `C:\UnrealProjects\EW\EW.uproject` directly or use Browse in Unreal's Project Browser; both copies display EW, so verify the path. A clearly named shortcut to the active file avoids opening the old backup.

## Repository

`Source/` contains gameplay and editor helpers, `Content/` contains Unreal assets, `Config/` contains shared settings, and `Scripts/Setup` / `Scripts/Verification` contain opt-in tooling. New game-specific assets belong in `Content/Elitewake/`.

Generated Unreal/IDE files are ignored. `main` holds verified, focused changes; use Git LFS for binary assets. Keep gameplay foundations in C++, assemble content in Blueprints, and preserve original code/art/story and the current design authority.
