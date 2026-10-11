# Verification

What has been tested, how, and what the tests do not cover. A passing test proves only its own scope. A test fixture is not a finished feature.

Last updated: October 11, 2026. The full dated log of every run, including earlier failures, is in [ARCHIVE/2026-10_VERIFICATION_LOG.md](ARCHIVE/2026-10_VERIFICATION_LOG.md).

## How things are tested

- **Native tests:** C++ automation tests under `Source/EW/Tests/`, run headless with the `Elitewake` filter (see [PROJECT_GUIDE.md](PROJECT_GUIDE.md#building-and-testing)). Latest run: **24 of 24 pass** (`Saved/Logs/DeckNative.log`, October 11).
- **Play checks:** Python scripts in `Scripts/Verification/` that run inside the editor. Most use a listen server and one client in the same process. Some launch separate game processes over loopback. Results go to `Saved/*Result.json`. `run_play_check.py` runs a check unattended: it starts Play, runs the script and closes the editor.
- **Package checks:** PowerShell scripts that verify a cooked Windows Development build.

`Saved/` is not in Git, so result files and logs exist only on the machine that produced them.

**Not covered anywhere yet:** a physical gamepad, a dedicated server, two separate PCs, Internet play, a Shipping build, performance, and any save/load (none exists).

## Results by system

| System | Commit | Native test | Play check (passing checkpoints) | Not covered |
| --- | --- | --- | --- | --- |
| Stance animation and collision | `19c573c`, `a8996d4` | `Animation.StanceBlendSpaces`, `Movement.StanceCollision` | `verify_stance_play`, `verify_stance_clearance_play`, `verify_stance_network_play` (client to host with 100 ms lag and 1% loss) | Moving decks, final transitions |
| Survival HUD | `ad0d82b`, redesign in `52678ec` | `Survival.ExhaustionNotification` | `verify_survival_hud_play` (20 standalone, 20 client) | Needs drain and damage, final icon art |
| Survival invalid-number guard | `3d054fd` | `Survival.InvalidNumericInput` | — | — |
| Inventory selection | `ecf9f61` | — | `verify_inventory_selection_play` | Physical controller |
| Pickups | `1e0e05d` | `Inventory.PickupValidation` | `verify_pickup_play` (competing pickups, packet loss) | — |
| Equipment | `f2d32d4` | `Inventory.EquipmentTransfer`, `Inventory.PersistedEquipmentFixtures` | `verify_equipment_play`, `verify_equipment_network_stress` | Armor effects, durability |
| Hotbar | `60ed961` | `Inventory.HotbarOwnershipAndActivation` | `verify_hotbar_play` (42 network regressions) | Remapping |
| Interaction (press, hold, prompts) | `adc9693` | `Interaction.AuthorityAndHolds` | `verify_interaction_play` (31 standalone, 31 client) | Real station and ship actions |
| Fresh water | `fdf774b` | — | `verify_water_play` | Salt water |
| Hand gathering | `3246f9e` | `Gathering.HandResources` | `verify_hand_gathering_play` | Regrowth |
| Hatchet trees | `30c2136` | `Gathering.HatchetTree` | `verify_hatchet_play` | Bare hands, animation |
| Pickaxe mining | `eb3d227` | `Gathering.PickaxeMining` | `verify_mining_play` | Ore distribution |
| Berries and eating | `a2bf748`, `be80b53`, `7eddba8` | `Gathering.Berries`, `Inventory.FoodConsumptionAndFreshness` | `verify_berry_play`, `verify_food_play` | Freshness across sessions |
| Integrated loop (pickup through gathering) | `9443259` | — | `verify_integrated_play` | — |
| Crafting | `52678ec` | `Crafting.AtomicTransaction` | `verify_crafting_play`, `verify_starting_recipes_play`, `verify_item_icons_play` (3) | Stations, timers, item use |
| Starter tool loop (craft, equip, harvest) | `bf5511e` | — | `verify_starter_tool_loop_play` (7) | Durability |
| Repair Kit recipe | `bf5511e` | — | `verify_prologue_repair_recipe_play` (7) | Repair use |
| Objectives | `52678ec` | `Objectives.OrderedAuthority` | `verify_objectives_play` (5), `verify_objective_ui_play` (9), `verify_objective_rewards_play` (8) | Real prologue steps |
| Map preview | `52678ec` | — | `verify_map_play` (6) | Discovery, compass |
| Inn torch | `52678ec` | — | `verify_inn_torch_play` (7) | Placement, flame, use |
| Multiplayer setup | `52678ec` | `Multiplayer.PrivateAddress` | `verify_multiplayer_configuration_play` (4); separate-process connection (4) and gameplay (13 observations); Host/Join/Leave lifecycle (10) | Two PCs, LAN, Internet |
| Late join and recovery | `3d054fd` | — | Three-process late join (17 checks); cancel and host-loss recovery (13) | Two PCs |
| Windows package | local archive `local-20261010-071931` | — | 16 required packages cooked; 5 loopback checks; HUD rendered at 1280×720, 1920×1080, 2560×1440 | Clean PC, LAN, Shipping. Archive predates the coastal map, Company and swimming |
| Company | `7b024cf` | `Company.NameValidation`, `Company.TameCapBoundaries` | `verify_company_play` (15 network, 4 menu clicks) | Persistence, world effects |
| Coastal map and swimming | `42636f3` | — | `verify_coastal_play` (4), `verify_coastal_swimming_play` (6), `verify_coastal_ocean_depth_play` (3) | Buoyancy, underwater effects |
| Ship hull, fittings and sailing | `b84ec94`, `26240ee`, `929fcc8` | `Ships.FittingAuthority`, `Ships.SailingAuthority` | `verify_ship_sailing_play` (9): client installs helm and two sails, takes the helm, sets full sail, sails 12.6 m and turns 52° in 4 s with its copy within 31 cm of the server, centres the rudder, leaves | Walking on a moving deck, anchor, cargo, cannons, ownership, separate processes |
| Crew on deck and boarding ladders | `75c038b` | `Ships.BoardingAndAnchor` | `verify_ship_deck_play` (13): while the host sails 25 m, the client crew stays put on deck (0 cm slide, client copy within 3 mm), walks 2.4 m along the deck at 6.3 m/s, walks overboard and swims, then climbs the ladder back aboard | Separate processes, rough seas, many crew |
| Anchor | `dcf33ad` | `Ships.SailingAuthority`, `Ships.BoardingAndAnchor` | `verify_ship_sailing_play` (11): the client raises the anchor, sails, then drops it and the ship stops; `verify_ship_deck_play` (14): the host raises it before sailing | Anchor HUD art, dragging and damage |

## Known failures

**Sloop sailing (October 11), prototype deleted.** The client boarded the sloop and held the helm, and an open inventory blocked steering. Then the steering phase failed: the hull stayed put at speed 0 (`Saved/CoastalSloopPlayResult.json`).

The cause was found afterwards. The editor ran in the background at about 3 frames per second, and the server discarded helm input older than 0.25 s. Every input therefore expired as it arrived. The owner deleted the prototype that day. The next ship must not expire held input on elapsed time alone, and its Play test must disable editor background throttling. The replacement ship system passes this same client test (see the table above).

**Editor crash on close (October 11).** This was an engine assertion during shutdown, not a test failure; see [PROJECT_GUIDE.md](PROJECT_GUIDE.md#known-problems).

## Adding a result

Add or update the system's row: commit, test names, checkpoint count, and the main thing not covered. Record failures as failures, with their evidence path. Put any long narrative in the commit message, not here.
