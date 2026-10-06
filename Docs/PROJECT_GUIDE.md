# Project guide

Updated October 6, 2026. Active checkout: `C:\UnrealProjects\EW`. Engine: **Unreal 5.8.3**. Repository: **elitegamelabs/Project-Elitewake**. The OneDrive copy is a backup, not the working project.

## Current state

This is a tested gameplay foundation for version 0.01, not a finished pirate sandbox. Normal Play starts with empty inventory. Test Wood/Hats and the pickup map are opt-in fixtures.

| System | Current foundation | Remaining work |
| --- | --- | --- |
| Locomotion/camera | Move, jump, sprint, first/third-person; locomotion states | Final perspective animation and hardware coverage |
| Crouch/prone | Distinct capsules, clearance-gated exits, prone-body collision; client prediction tested | Moving decks, dedicated server, final animation polish |
| Survival | Authoritative stats; five HUD gauges and empty-stat warnings; carried weight includes gear | Needs drain/damage, drinking/food, five-second stamina tuning, jump/climb costs, regeneration/fall damage |
| Inventory | 24 slots, stacking, weight, saved item definitions; selection/details and live refresh | Durability/freshness/item instances, preview/tabs, discard and crafting |
| Pickups | Owned requests; server range/aim/visibility validation; partial transfer and competition | Full interaction prompts/framework and production world content |
| Equipment | Atomic owned-unit equip/unequip/swaps with capacity checks | Cosmetics, armor effects, durability and persistence |
| Hotbar | Eight owned-definition shortcuts; 1–8/LB/mouse assignment; safe equipment activation | Consumables, maps/taming/harpoon actions, remapping and persistence |
| Ship/world/prologue | Current Bible and owner decisions recorded | Production ship loop, Port/missions, navigation and save/load |

The latest gameplay acceptance includes nine native automation tests, 20 standalone/20 client survival HUD checkpoints and 42 network hotbar regressions. See [verification](VERIFICATION.md) for exact scope and historical evidence. Local listen-server packet emulation is not production multiplayer acceptance. Final artwork, physical controller, packaged and dedicated-server coverage remain open.

Survival still uses prototype 15/s sprint drain and 10/s recovery. The owner confirmed recovery while walking as well as stationary. Hunger is currently normalized 0–100%; 50 kg carry capacity is provisional, displayed rather than enforced as a hard cap. Do not claim full M4 completion or invent unspecified needs-damage/scaling rules.

<a id="next-work"></a>

## Next work

Milestone A interaction work is authorized on `milestone-a-interaction`. First generalize pickups and pass unchanged pickup checks; then add device-aware prompts and server-controlled holds with cancellation verification. Merge to main requires verified Play checks and owner approval. One-second fixture holds, walking while aimed/in range, and Campfire/Smithy fixtures are draft choices. Tree punching remains Attack, outside this interaction slice. `.mcp.json` stays local; editor preferences are preserved. Current authority is owner decisions, then Shared, then team guides; the supplied DOCX guides identify October 5 source revision and await the October 6 changes. Port rule carryover awaits confirmation.

Development guide chapter 41 (archived Master §24.3) specifies: baseline -> locomotion/input -> camera/animation state -> survival/HUD -> items/inventory/equipment -> interaction -> gathering -> crafting/skills -> sword/enemy -> shovel/map objective/treasure -> ship/helm/anchor/cargo/weight -> cannons/shared ammo -> day/night/cold/fire/clothing -> Port/vendors -> prologue logic -> map/compass -> additional encounters/polish. Use this dependency order as the reference; the later conversational M0-M5 labels are not a one-to-one numbering of that list.

M4 remains partially implemented. The [HUD return slice](VERIFICATION.md#m4-hud) now supplies health/stamina/food/hydration/weight gauges and empty-stat warnings. Activity-dependent needs drain, starvation/dehydration consequences, fresh/salt drinking, five-second base stamina timing, jump/climb costs and regeneration remain open. October 6 owner clarification permits recovery while walking. Upgraded-stat/activity scaling and health-loss interpretation still require clarification. The owner move to M5 does not verify or cancel these requirements.

### Proposed 0.01 work packages after M5

1. Gathering and crafting: harvestable tree, tool interaction, recipes, resource costs and unlock prerequisites. C++ authority; Data Assets for recipes/resources; Blueprints for world content; UMG for crafting. Verify no resource duplication or unaffordable crafting.
2. Skills, simple combat and treasure: 15 cumulative points per level, character cap 80, respec from level 10 for 2 Gold, shovel/digging, map objective and small enemy encounter. Deterministic C++/Blueprint behavior; data-driven rewards. Verify progression and authoritative damage/rewards; node costs remain TBD where not assigned.
3. Small ocean and starter sloop: helm, hold-to-anchor, cargo, ship weight and two opposing cannons with shared limited ammunition. Depends on movement/interaction/inventory; test boarding, moving deck behavior, cargo transfer, anchoring and overload sinking in multiplayer. Implement current hardpoint and storage-only Ammo Bin rules.
4. Environment, Port/prologue and navigation: 90 real minutes each for day/night, contextual conditions, basic Port vendors, revised schooner battle/dinghy repair/journal opening, then map/compass. M/View opens map; walking allowed, sprint/stance/hotbar/inventory suppressed, world still runs. Command radial uses Middle Mouse / D-pad Right. Survival/HUD return work above must not be silently delayed until final polish.
5. Integrated 0.01 playthrough: Prepare/Sail/Discover/Loot/Upgrade on a small test world. Repeat dedicated-server and two-client checks, packaging, save/load where implemented, and performance checks. This does not imply the full prologue or finished content is ready.

### Longer-term backlog

Ports, specialized vendors, Ferryman routes, currency, shipyard progression, larger customizable vessels and belongings transfer; sail damage/repair and deeper naval combat; storms/adventure encounters, ghost ships, floating salvage and dungeons; tribes and communication; crew roles and shared commands; Beast Mastery, taming/breeding; injuries/surgeon, aging/hair; world density and official regional hosting. Davy Jones quest is Removed, not a planned rejuvenation implementation.

Preserve October §§21,30: far-offshore schooner vs brigantine -> flooding/bailing -> boarding and sword fight -> head injury and lost sword -> unconscious Quartermaster rescue with rare rye -> island amnesia/journal -> gathering/tools -> Repair Kit/hammer and Small Sail on surviving dinghy -> sail/title/Port. Tutorial tools/supplies are discarded, but rare rye stays in player inventory. Survivor starts with zero currency. Innkeeper responds to request for free lodging with work/trade, introduces town-square merchants (quests later), and general merchant offers rye sale. Credit 250 Copper when the introduction mission completes; room charge remains unspecified. Raft/shipyard construction is no longer the opening. Persistent sloop progression placement remains to be designed.

## Repository map

| Location | Purpose |
| --- | --- |
| `EW.uproject`, `Config/` | Project descriptor and shared engine/game settings |
| `Source/EW/` | Active gameplay module; native tests in `Tests/` |
| `Source/EWEditor/` | Editor-only animation/content/verification helpers |
| `Content/Elitewake/` | Project-specific animations, items, Blueprint assembly and isolated fixture map |
| `Content/ThirdPerson/`, `Characters/`, `Input/`, `LevelPrototyping/` | Active foundation and shared dependencies; names retained to preserve asset references |
| `Content/FreeAnimationLibrary/` | Imported animation library retained for stance/current and future content |
| `Content/__ExternalActors__/`, `__ExternalObjects__/` | Unreal-managed external data for retained maps; do not edit manually |
| `Scripts/Setup/` | Opt-in fixture creation and stance-animation configuration |
| `Scripts/Verification/` | Repeatable Play acceptance checks |
| `Docs/PROJECT_GUIDE.md` | Current status, work order and repository conventions |
| `Docs/DESIGN_REFERENCE.md` | Authority, requirements and decisions |
| `Docs/VERIFICATION.md` | Acceptance evidence and limitations |
| `Docs/ARCHIVE/` | Historical source-review snapshots |
| `.codex/`, `.cursor/` | Shared Unreal/Scenario connector endpoints, without credentials |

Generated Binaries, Intermediate, Saved, DerivedDataCache and IDE state are ignored. Use Git LFS for Unreal binary assets; preserve commit history and focused commits. Local editor preferences belong in generated Saved/Config where possible.

## Development checks

Build `EWEditor Win64 Development` against this checkout before Play checks. Run automation filter `Elitewake` with `UnrealEditor-Cmd.exe`, `-unattended -nop4 -NullRHI`, `-ExecCmds="Automation RunTests Elitewake"` and `-TestExit="Automation Test Queue Empty"`. Do not append an early Quit command.

Run Play scripts from Unreal's Python console with an absolute path. Pickup/inventory/equipment/hotbar/HUD checks need fresh Play in `/Game/Elitewake/Maps/Lvl_M5PickupTest`; use standalone or in-process listen-server plus one client as their docstrings specify. Test scripts create PIE-only inventory, restore input/network/throttle state and remove callbacks. Stop Play afterward. Editor helpers never ship with the game.

| Scripts | Purpose |
| --- | --- |
| Setup `create_inventory_test_asset.py`, `create_equipment_test_assets.py`, `create_pickup_test_content.py` | Reconcile only named saved fixtures; preserve existing designer edits |
| Setup `configure_stance_animations.py` | Audited stance configuration; read prerequisites before using |
| Verification `verify_stance_play.py`, `verify_stance_clearance_play.py`, `verify_stance_network_play.py` | Animation/clearance/client stance checks |
| Verification `verify_pickup_play.py` | Authority and competing pickup checks |
| Verification `verify_inventory_selection_play.py` | Inventory input, focus and live-refresh checks |
| Verification `verify_equipment_play.py`, `verify_equipment_network_stress.py` | Transfer/capacity and bounded request stress checks |
| Verification `verify_hotbar_play.py` | Assignment, activation, input isolation and conservation |
| Verification `verify_survival_hud_play.py` | Rendered stats/warnings, carried weight and possession lifecycle |

<a id="repository-conventions"></a>

## Repository conventions

### Content Convention

All new Elitewake-specific assets should be created under `Content/Elitewake/` and grouped by gameplay domain rather than by individual developer.

Planned top-level domains include:

- `Characters`
- `Core`
- `Input`
- `Interaction`
- `Inventory`
- `Items`
- `Missions`
- `Ships`
- `Survival`
- `UI`
- `World`

Do not create every planned directory before it is needed. Add each domain with the first real asset that belongs there.

### C++ Convention

The runtime module remains `EW`. New classes should be grouped beneath `Source/EW/` by gameplay domain. Public headers and implementation files should remain close together until module growth justifies a separate public and private layout.

Recommended initial domains are:

- `Character`
- `Core`
- `Input`
- `Interaction`
- `Inventory`
- `Ships`
- `Survival`
- `UI`

Keep native class/module identities and Unreal asset paths stable unless their Blueprint dependencies have been audited. Unused template variants were removed after that audit; the active ThirdPerson foundation remains.

### Naming

- C++ classes use Unreal prefixes and `EW` in the class name where it improves project identity.
- Blueprints use `BP_`.
- Actor Components use `AC_` for asset names.
- Input Actions use `IA_`.
- Input Mapping Contexts use `IMC_`.
- Widgets use `WBP_`.
- Data Assets use `DA_`.
- Data Tables use `DT_`.
- Enums use `E_` for assets and `E` for C++ types.
- Structures use `ST_` for assets and `F` for C++ types.

Prefer descriptive names. Avoid names tied to the temporary product title when a neutral system name will remain valid after rebranding.

## Keeping this tidy

Update these three current documents rather than adding a new top-level document for every session. Put new dated acceptance sections into VERIFICATION.md and new decisions into DESIGN_REFERENCE.md. Archive superseded source reviews with an explicit historical label. Delete unused Unreal assets only after package and native-type dependency checks, then rebuild and load the retained maps/Blueprints.
