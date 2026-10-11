# Project guide

What is built, what is broken, what comes next, and how to work in this repository. Design rules are in [DESIGN_REFERENCE.md](DESIGN_REFERENCE.md); test results are in [VERIFICATION.md](VERIFICATION.md).

Last updated: October 11, 2026.

## Where things stand

Elitewake is a tested set of gameplay foundations, with one connected test map. It is not yet a playable pirate game. Every system below runs server-authoritative and has been tested with a listen server and a client, unless noted otherwise.

- **Build:** both Editor and Game targets build.
- **Native tests:** 22 of 22 pass (October 11, `Saved/Logs/ShipFittingNative.log`).
- **GitHub:** all work is committed and pushed to `main`.

| System | What works | Not done yet |
| --- | --- | --- |
| Movement | Walk, sprint, jump, crouch and prone with clearance checks; first/third-person toggle; swimming, with diving and surfacing | Final animations, moving ship decks, physical gamepad testing |
| Survival | Replicated Health, Stamina, Hunger, Hydration, temperature, weight; HUD icons and warnings; drinking fresh water; rejects invalid numbers | Needs drain and damage, temperature effects, regeneration, fall damage. Sprint uses placeholder rates (15/s drain, 10/s recovery) |
| Inventory and equipment | 24 slots, stacking, weight, item details; equip, unequip and swap; eight-slot hotbar | Durability, save/load, character preview, discard. Inventory is visible to all players (privacy undecided) |
| Interaction | E / X prompts that follow the device; press and hold actions timed by the server; cancellation | Real station, storage, vendor and ship actions |
| Gathering | Fiber, sticks and berries by hand; hatchet trees (Wood, Thatch); pickaxe nodes (Stone, ore) | Bare-hand tree punching and injury, regrowth, real world placement, swing animations |
| Food | Eat Azren berries (Hunger and Health); 20-minute freshness, then toxic | Marad, cooking, other foods, freshness that survives save/load |
| Crafting | Server-checked crafting with no item loss; menu with icons; four starter recipes and a Repair Kit as test assets | The event that unlocks recipes after the innkeeper introduction; stations; craft timers; using the crafted items (dig, drink, repair) |
| Objectives | Ordered objective steps per player, current-step display, recipe rewards on completion | The real prologue steps; save/load |
| Menus and map | Inventory and crafting grids; seven menu sections (Company works, the others are placeholders); M shows the surrounding area | Building, Skills, Tames and Journal screens; real map with discovery and compass |
| Inn torch | One torch per player, with the owner's message and a highlight | Real inn placement, flame and light, carrying and using it |
| Company | Create, invite, accept, roster, rename, promote and demote, remove, leave, transfer leadership, ownership policy settings | Policies don't affect anything yet; alliances, logs, crew groups, save/load |
| Private multiplayer | F10 Host / Join / Leave panel (local and private IPv4); recovery from failed or dropped connections; separate-process tests; local Windows package | Two-PC LAN test, Internet, Shipping build, distribution |
| Coastal map | `Lvl_CoastalPlayground`: beach, dock, islet, resources, freshwater spring, textured sand and timber, sloped shore, swimmable ocean 500 m deep | Real terrain and foliage, wildlife, Port and inn, final art |
| Ships | `AEWShip` built from a ship definition: a bare hull with helm, sail and cannon mounts. Players install and remove fittings carried in their inventory (server-checked). One bare sloop floats in the coastal map | Sailing, walking on a moving deck, anchor, cargo, cannons, real hull and fitting art (boxes stand in) |

## Known problems

1. **The editor crashed while shutting down** on October 11, 01:52. It hit an engine assertion (`GIsPlayInEditorWorld`, `Editor.cpp` line 1225) after an MCP editor tool requested the close while a Play session was ending. The script stack names `SlateInspectorToolset`. It is not in Elitewake code. Stop Play before closing the editor, and close it normally rather than through a tool. Crash files: `Saved/Crashes/UECC-Windows-129F0C5A…_0001`.
2. **Startup opens the wrong map.** `Config/DefaultEngine.ini` still starts the editor and game in `/Game/ThirdPerson/Lvl_ThirdPerson`. Open `/Game/Elitewake/Maps/Lvl_CoastalPlayground` yourself to see current work.
3. **The latest Windows package is stale.** `Saved/PrivateBuilds/local-20261010-071931` predates the coastal map, Company and swimming.
4. **The Repair Kit icon is not imported.** The source PNG exists but has no Unreal texture yet; the kit shows fallback art.

## Next work

Proposed order, pending owner confirmation:

1. **Ship foundation,** following the [ship model](DESIGN_REFERENCE.md#ship-model). Each step is built, tested and committed before the next:
   1. **Hull and fittings** (done): `AEWShip`, `DA_Ship_Sloop`, helm and sail test items.
   2. **Sailing:** take the helm, sail states and rudder, the wind model, and movement in fixed steps.
   3. **On deck:** walk on a moving ship, board and disembark as a client.
   4. **Anchor, cargo and weight,** in that order.
2. **Builder's Plan, Loom and Tanner,** once fitting and recipe questions are answered (see [open questions](DESIGN_REFERENCE.md#open-questions)).
3. **Prologue and Port connection.** Innkeeper introduction completion gives 250 Copper and unlocks the four starter recipes. Place the per-player inn torch for real.
4. **World content.** Regional resources, real wildlife with AI, terrain and foliage, survival HUD art.
5. **Then,** in dependency order:
   1. simple combat
   2. digging and treasure
   3. cannons and ammo
   4. weather, time of day and clothing
   5. vendors
   6. map and compass
   7. skills
   8. save/load

## Playing the coastal map

Open `Content/Elitewake/Maps/Lvl_CoastalPlayground` and press Play. The map grants no items or recipes.

- **Beach:** loose Wood and Stone stacks. Look at one and press E.
- **Grove:** fiber plants and Azren bushes (E). Trees need an equipped axe and stone needs an equipped pickaxe; use Left Mouse.
- **Freshwater spring:** inland at about X −17 m, Y 15 m. Press E while thirsty.
- **Dock and sea:** the dock reaches over swimmable water.
  - Look down and move forward to dive; hold Space to rise.
  - The water surface is at Z −65 cm. The visible waves are cosmetic.
- **Sloop:** a bare hull floats off the dock at about X 62 m, Y 14 m. Look at a mount and hold E to install a carried helm or sail; hold E on a fitting to remove it. Fittings have no recipe yet, so use test items.
- **Menus:** I opens inventory and crafting; M shows the map. Starter recipes stay locked because the innkeeper introduction isn't built yet.

## Building and testing

Close the editor before building code that adds or changes classes.

```bash
"C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" EWEditor Win64 Development -Project="C:/UnrealProjects/EW/EW.uproject" -WaitMutex
```

Build the `EW` target the same way when runtime code changes. Then run all native tests:

```bash
"C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "C:/UnrealProjects/EW/EW.uproject" -unattended -nop4 -NullRHI -ExecCmds="Automation RunTests Elitewake" -TestExit="Automation Test Queue Empty" -log
```

Do not add an early quit command. The run ends when the test queue is empty.

**Play scripts** (`Scripts/Verification/*.py`) run from the editor's Python console using the full path. Each script's docstring names its map and Play mode.

- Most use `/Game/Elitewake/Maps/Lvl_M5PickupTest`; the `verify_coastal_*` scripts use the coastal map.
- Results are written to `Saved/*Result.json`.
- Scripts may move pawns or create test items during Play only. They never change saved maps or normal starting inventory.

**Setup scripts** (`Scripts/Setup/*.py`) create test assets and fixtures:

- `create_*` scripts make missing saved test assets and do not overwrite existing ones.
- `spawn_*` scripts place temporary fixtures in a running Play session.
- The coastal scripts (`create_coastal_playground.py`, `shape_coastal_shore.py`, `upgrade_coastal_water.py`, `set_coastal_ocean_depth.py`, `create_sloop_test_assets.py`) built the saved coastal map. Do not rerun them over an edited map.

**Evidence lives in `Saved/`,** which Git ignores. Test results and logs exist only on the machine that ran them.

## Private multiplayer testing

The goal is for the owner to host and play while one approved tester joins from another Windows PC. Test locally first, then on LAN, then over the Internet.

- **F10** opens the test session panel. Join accepts local or private IPv4 addresses only (default port 7777). Use Standalone Game, because ordinary in-editor Play shows the panel disabled. Host, Join and Leave reload the ThirdPerson map and reset session progress.
- **`Scripts/Verification/build_private_windows.ps1`** builds, cooks and archives a Development package into `Saved/PrivateBuilds/`, with Microsoft VC++ redistributables and a `TEST_NOTES.md`. The editor must be closed.
- **Done:** separate-process connection, gameplay, late join, host loss and cancellation recovery, packaged loopback startup.
- **Next:** test the packaged menus and controls, a clean PC install, and two PCs on LAN.
- **Later, with owner approval:** Internet transport, a restricted itch.io page, Butler uploads, and tester invites.

Never change firewall or router settings, create accounts, upload builds or invite testers without the owner's explicit go-ahead. Never commit credentials or download keys.

## Art and placeholder assets

The owner has deferred Fab purchases; only free assets have been approved so far. Until final art exists, placeholder art is generated and clearly labeled.

- **Sources** live in `Art/`, with the exact prompt, tool and SHA-256 hash recorded in `generation.json` next to each set:
  - `Art/Placeholders/ItemIcons/`: transparent item icons.
  - `Art/Environment/`: base-color textures.
- **Unreal copies** are imported under `Content/Elitewake/UI/PlaceholderIcons/` and `Content/Elitewake/World/Materials/`, with a `_v1` suffix.
- **Importing:** `Scripts/Setup/import_placeholder_item_art.py` imports the icons and assigns them to their items.
- **Replacing:** final art gets a new version or path. Never overwrite a placeholder in place.
- **Imported library:** `Content/FreeAnimationLibrary/` (Free Animation Library by Voxel Vision) is installed. Only the stance animations are wired up so far.

## Repository map

| Path | Contents |
| --- | --- |
| `EW.uproject`, `Config/` | Project file and shared engine/game settings |
| `Source/EW/` | Gameplay module; native tests in `Source/EW/Tests/` |
| `Source/EWEditor/` | Editor-only helpers used by verification scripts; never shipped |
| `Content/Elitewake/` | All Elitewake assets: items, recipes, maps, materials, meshes, UI, animation setup. Test assets sit in `Testing/` subfolders |
| `Content/ThirdPerson/`, `Characters/`, `Input/`, `LevelPrototyping/` | Unreal template content the project still depends on; keep the paths |
| `Content/FreeAnimationLibrary/` | Imported animation library |
| `Content/__ExternalActors__/`, `__ExternalObjects__/` | Unreal-managed map data; never edit by hand |
| `Art/` | Source images for placeholder art, with provenance |
| `Scripts/Setup/`, `Scripts/Verification/` | Fixture creation and acceptance scripts |
| `Docs/` | This guide, the design reference, the verification summary, and the [archive](ARCHIVE/README.md) |

## Conventions

**Code and content**

- **Where things go:** gameplay state, replication and transactions in C++; scenes assembled in Blueprint; tunable content in Data Assets; screens in UMG.
- **Clients request, the server decides.** Every consequential action goes through an owned request that the server validates.
- **Production starts stay empty.** Normal play begins with no items and no recipes. Test content stays opt-in.
- **Editing assets:** change `.uasset` and `.umap` files only through Unreal. Delete an asset only after checking package and native-type references, then rebuild and load the retained maps.
- **Paths:** keep template paths and class names unless every reference has been checked.

**Naming**

- C++ classes use the Unreal prefix plus `EW` (`AEWCharacter`).
- Asset prefixes: `BP_` Blueprint, `WBP_` widget, `DA_` data asset, `DT_` data table, `IA_` input action, `IMC_` input mapping context, `M_` material, `T_` texture, `SM_` static mesh, `AC_` actor component, `E_` enum, `ST_` struct.

**Git**

- Binary files go through Git LFS (`.gitattributes`).
- Keep `main` to tested, focused commits. Do not force-push or rewrite history.
- Ask the owner before pushing.
- Never commit `Config/DefaultEditor.ini` local changes, the root `.mcp.json`, or anything in `Saved/`.

**Docs**

- Update the three current docs; do not add a new document per session.
- New design decisions go into the matching topic in `DESIGN_REFERENCE.md`. Answered questions come off its open-questions list.
- New test results go into `VERIFICATION.md`.
- Superseded material goes to `Docs/ARCHIVE/` with a date prefix.
