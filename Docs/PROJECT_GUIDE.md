# Project guide

What is built, what is broken, what comes next, and how to work in this repository. Design rules are in [DESIGN_REFERENCE.md](DESIGN_REFERENCE.md); test results are in [VERIFICATION.md](VERIFICATION.md).

Last updated: October 11, 2026.

## Where things stand

Elitewake is a tested set of gameplay foundations, with one connected test map. It is not yet a playable pirate game. Every system below runs server-authoritative and has been tested with a listen server and a client, unless noted otherwise.

- **Build:** both Editor and Game targets build.
- **Native tests:** 26 of 26 pass (October 11, `Saved/Logs/WeightNative.log`).
- **Client Play checks:**
  - A client fits out the sloop, raises the anchor, sails, steers, and anchors again (`verify_ship_sailing_play`, 11 of 11).
  - A client crew rides, walks, goes overboard and climbs back aboard while the host sails (`verify_ship_deck_play`, 14 of 14).
  - A client stores cargo in the ship's hold and the host takes some out; both see the same ship load (`verify_ship_cargo_play`, 5 of 5).
- **GitHub:** all work is committed and pushed to `main`.

| System | What works | Not done yet |
| --- | --- | --- |
| Movement | Walk, sprint, jump, crouch and prone with clearance checks; first/third-person toggle; swimming with its own animations, floating head-out at the surface, diving only when the camera clearly looks down | Final animations, moving ship decks, physical gamepad testing |
| Survival | Replicated Health, Stamina, Hunger, Hydration, temperature, weight; painted HUD icons (owner's matte set) that fill from the bottom, and warnings; drinking fresh water; rejects invalid numbers | Needs drain and damage, temperature effects, regeneration, fall damage. Sprint uses placeholder rates (15/s drain, 10/s recovery) |
| Inventory and equipment | 24 slots, stacking, weight, item details; equip, unequip and swap; eight-slot hotbar | Durability, save/load, character preview, discard. Inventory is visible to all players (privacy undecided) |
| Interaction | E / X prompts that follow the device; press and hold actions timed by the server; cancellation | Real station, storage, vendor and ship actions |
| Gathering | Fiber, sticks and berries by hand; hatchet trees (Wood, Thatch); pickaxe nodes (Stone, ore); all of them placed on the coast with real-looking palms, boulders and plants | Bare-hand tree punching and injury, regrowth, ore nodes and other regions' plants, tool-specific swing animations |
| Combat | Attack (Left Mouse / RT) swings, seen by everyone, once a second. With a hatchet or pickaxe aimed at a tree or rock it gathers; otherwise it strikes the survivor in front for 10 (fists), who flinches | Weapons and their damage, blocking, wildlife and enemies to fight, death and loot drops in play, tool and weapon swing animations |
| Food | Eat Azren berries (Hunger and Health); 20-minute freshness, then toxic | Marad, cooking, other foods, freshness that survives save/load |
| Crafting | Server-checked crafting with no item loss; menu with icons; four starter recipes and a Repair Kit as test assets | The event that unlocks recipes after the innkeeper introduction; stations; craft timers; using the crafted items (dig, drink, repair) |
| Objectives | Ordered objective steps per player, current-step display, recipe rewards on completion | The real prologue steps; save/load |
| Menus and map | Inventory and crafting grids; seven menu sections (Company works, the others are placeholders); M shows the surrounding area | Building, Skills, Tames and Journal screens; real map with discovery and compass |
| Inn torch | One torch per player, with the owner's message and a highlight | Real inn placement, flame and light, carrying and using it |
| Company | Create, invite, accept, roster, rename, promote and demote, remove, leave, transfer leadership, ownership policy settings | Policies don't affect anything yet; alliances, logs, crew groups, save/load |
| Private multiplayer | F10 Host / Join / Leave panel (local and private IPv4); recovery from failed or dropped connections; separate-process tests; local Windows package | Two-PC LAN test, Internet, Shipping build, distribution |
| Coastal map | `Lvl_CoastalPlayground`: a generated sand island and islet with wet shoreline and dunes, animated surf washing up both beaches, Unreal Water ocean with a gentle swell and underwater view (clear turquoise over the sand, deep navy past the shelf), volumetric clouds, a weathered timber dock, about thirty harvestable Veyran Palms behind the beaches, twenty minable boulders, and fiber plants, stick piles and berry bushes to gather by hand, freshwater spring, a test starter kit, swimming down to 500 m | Vegetation, rocks and gatherable resources (removed with the blockout; real meshes next), wildlife, Port and inn |
| Ships | `AEWShip` built from a ship definition: a bare hull with helm, sail and cannon mounts, a boarding ladder on each side, an anchor capstan and a shared cargo hold. Load slows the ship, and an overloaded ship is swamped after 60 s until lightened. Players install fittings from their inventory, take the helm, set sail (W/S) and steer (A/D). Crew stand and walk on deck while it sails, and climb aboard from the water by looking anywhere on a side ladder. The server moves ships in fixed steps, driven by a world wind, and every screen shows them gliding smoothly between steps and network updates. The sloop has a real hull modelled in-engine from the owner's art: planked and tarred, with bulwarks, a gunport each side, side ladders, a capstan, a hatch with stairs down to a walkable hold, and a mast, bowsprit and standing rigging. Its helm is a spoked wheel and its sails are the owner's gaff mainsail and jib art, shown rolled up, half set or full to match the helmsman's setting. A raft and a dinghy, also from the owner's art, have built-in steering (a steering oar, a tiller) and a Small sail on their own mast. The schooner, from the owner's art, is about 22 m long with three masts (a Large square topsail, two Medium gaff sails and three Small jibs), a raised aft deck carrying the helm with the captain's cabin beneath it, and a lower deck with twelve gunports reached by stairs from the main hatch. Both modelled hulls carry a real ship's working detail: deadeyes on channels, chainplates and ratlines, pin rails, a rudder and catted anchors | Sinking and wrecks, cannon art and firing, docking, ship ownership, ship motion under heavy packet loss, the brigantine and multi-deck ship |

## Known problems

1. **The editor crashed while shutting down** on October 11, 01:52. It hit an engine assertion (`GIsPlayInEditorWorld`, `Editor.cpp` line 1225) after an MCP editor tool requested the close while a Play session was ending. The script stack names `SlateInspectorToolset`. It is not in Elitewake code. Stop Play before closing the editor, and close it normally rather than through a tool. Crash files: `Saved/Crashes/UECC-Windows-129F0C5A…_0001`.
2. **Startup opens the wrong map.** `Config/DefaultEngine.ini` still starts the editor and game in `/Game/ThirdPerson/Lvl_ThirdPerson`. Open `/Game/Elitewake/Maps/Lvl_CoastalPlayground` yourself to see current work.
3. **The latest Windows package is stale.** `Saved/PrivateBuilds/local-20261010-071931` predates the coastal map, Company and swimming.
4. **Ship edge cases.**
   - A ship placed so its hull already overlaps something (a dock, a shore) cannot move until it is moved clear.
   - Client ships move in small steps 30 times a second rather than smoothly.
   - Overload never sinks a ship yet: a swamped ship simply cannot sail until lightened. Real sinking comes with hull damage.
   - The hold screen is functional only: mouse-driven, not yet controller-navigable, and not yet visually reviewed.
5. **The Repair Kit icon is not imported.** The source PNG exists but has no Unreal texture yet; the kit shows fallback art.
6. **The coast's gatherables never grow back.** Palms, boulders, fiber plants, stick piles and berry bushes are gone once emptied until the map reloads; regrowth is not built.
7. **The ocean must be rebuilt in a rendering editor.** After changing the coastal ground or water headless, run `build_coastal_terrain.py` in the editor (it rebuilds the ocean), or the ocean does not draw.

## Next work

Proposed order, pending owner confirmation:

1. **Ship foundation,** following the [ship model](DESIGN_REFERENCE.md#ship-model). Each step is built, tested and committed before the next:
   1. **Done (client-verified):** `AEWShip` and `DA_Ship_Sloop`; helm and sail fittings; sailing with wind; crew on a moving deck; boarding ladders; anchor; shared cargo hold; weight and overload.
   2. **Later, with combat:** hull damage, flooding, actual sinking and wreck crates; cannons on the hardpoints.
2. **Builder's Plan, Loom and Tanner,** once fitting and recipe questions are answered (see [open questions](DESIGN_REFERENCE.md#open-questions)).
3. **Prologue and Port connection.** Innkeeper introduction completion gives 250 Copper and unlocks the four starter recipes. Place the per-player inn torch for real.
4. **World content.** Regional resources, real wildlife with AI, vegetation and rocks.
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

Open `Content/Elitewake/Maps/Lvl_CoastalPlayground` and press Play. This test map's starter kit gives each survivor the wooden axe, pickaxe and shovel, the water flask, the inn torch, 20 Wood, 10 Stone, 10 Fiber and 10 Azul berries, and stocks each ship's hold with what its mounts take: a helm, and one sail for every sail mount (the sloop gets a Medium and a Small; the schooner a Large, two Medium and three Small). Other maps and normal starts grant nothing.

- **Playing alone:** set the editor's Play options to one player (Standalone). With a listen server and two players, Play runs two games in one editor, which is slower; the second window is the network client.
- **Attack:** Left Mouse (RT) swings once a second. Aim at another survivor within reach to strike for 10; with the wooden axe equipped (from your starter kit), aim at a palm's trunk to gather Wood and Thatch; with the wooden pickaxe, strike a boulder for Stone.
- **Plants:** look at a fiber plant, a pile of fallen sticks or a berry bush and press E to gather it all.
- **Freshwater spring:** inland at about X −17 m, Y 15 m. Press E while thirsty.
- **Dock and sea:** the dock reaches over swimmable water.
  - You float with your head out and swim level. Look well down and move forward to dive; hold Space to rise; let go and you drift back up.
  - The water surface is at Z −65 cm. The visible waves are cosmetic.
- **Sloop:** a bare hull floats off the dock at about X 62 m, Y 17.5 m. Climb a side ladder, walk the deck, and take the stairs through the hatch into the hold. Look at a mount and hold E to install a carried helm or sail; hold E on a sail to remove it. Hold E at the installed helm to take it: W/S set more or less sail, A/D steer, and hold E again to leave. The sloop starts anchored: hold E at the capstan near the bow to raise or drop the anchor. Hold E at the hatch amidships to open the ship's hold; click a stack to move it. From the water, look at the ladder on either side and hold E to climb aboard. The sloop is moored facing the islet about 15 m east, so steer north for open water. Fittings have no recipe yet; take the helm and sails from the hold and fit them.
- **Schooner:** anchored south of the dock at about X 64 m, Y −15 m, bow out to sea. Swim out and climb the ladder on either side. Its helm and sails are in its hold (open the hatch amidships). The wheel goes on the raised aft deck, the Large sail on the foremast as a square topsail, the Medium sails on the main and mizzen masts, and the Small sails on the three jib mounts near the bow. Take the stairs through the hatch to the lower deck and its twelve gunports. The doorway under the raised aft deck opens into the captain's cabin.
- **Raft and dinghy:** moored on the beach side of the dock (raft at about X 50 m, Y 3 m; dinghy at X 56.5 m, Y 3.5 m). Each has a Small sail in its hold (open the crate or chest), steers by its built-in oar or tiller (hold E there to take it), and is anchored at the bow.
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

**Unattended Play checks.** `Scripts/Verification/run_play_check.py`:

1. opens the editor on a map
2. starts a listen-server Play session
3. runs one check script
4. stops Play and closes the editor

Launch it from PowerShell, because Git Bash rewrites paths that start with `/`:

```powershell
$env:EW_PLAY_MAP='/Game/Elitewake/Maps/Lvl_CoastalPlayground'; $env:EW_PLAY_CHECK='C:/UnrealProjects/EW/Scripts/Verification/verify_ship_sailing_play.py'; $env:EW_PLAY_RESULT='ShipSailingPlayResult.json'
& 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' C:/UnrealProjects/EW/EW.uproject /Game/Elitewake/Maps/Lvl_CoastalPlayground -unattended -ExecCmds="py C:/UnrealProjects/EW/Scripts/Verification/run_play_check.py"
```

The outcome is written to `Saved/PlayCheckRun.json`. An editor window opens and closes on its own; leave it alone while it runs.

**Setup scripts** (`Scripts/Setup/*.py`) create test assets and fixtures:

- `create_*` scripts make missing saved test assets and do not overwrite existing ones.
- `spawn_*` scripts place temporary fixtures in a running Play session.
- The older coastal scripts (`create_coastal_playground.py`, `shape_coastal_shore.py`, `upgrade_coastal_water.py`, `set_coastal_ocean_depth.py`, `create_sloop_test_assets.py`) built the original map. Do not rerun them over the current map.
- The raft and dinghy come from `build_small_craft.py` (run after the two sloop scripts).
- The sloop comes from `build_sloop_hull.py` (hull, mast, rigging, definition) then `build_ship_fittings.py` (wheel and sails, given to the test items). The schooner comes from `build_schooner.py` (run after those two). The hull scripts draw from `ship_hull.py`, and all of them use `ship_geometry.py`. They run in the editor and are safe to rerun; each moves and relabels only its own ship. `Scripts/Verification/capture_ship_views.py` takes review screenshots.
- The current coastal look comes from `refresh_coastal_visuals.py`, then `build_coastal_terrain.py`, then `refresh_coastal_materials.py` (weathered dock, ocean colour), all run in the editor (not headless) and safe to rerun.
- `build_coastal_flora.py` grows the coast's plants (Veyran Palms, fiber plants, stick piles, berry bushes) and `build_coastal_rocks.py` then sets its boulders clear of them, from meshes they build in the editor; the frond texture is drawn by `Scripts/Art/make_palm_frond.py` (ordinary Python with Pillow).
- `configure_attack_animations.py` gives the survivor its swing and flinch animations; `configure_stance_animations.py` sets up stances and swimming. `Scripts/Verification/capture_coastal_views.py` takes review screenshots in Play.

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
