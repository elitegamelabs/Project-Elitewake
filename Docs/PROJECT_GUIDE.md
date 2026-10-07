# Project guide

Updated October 7, 2026. Active checkout: `C:\UnrealProjects\EW`. Engine: **Unreal 5.8.3**. Repository: **elitegamelabs/Project-Elitewake**. The OneDrive copy is a backup, not the working project.

## Current state

This is a tested gameplay foundation for version 0.01, not a finished pirate sandbox. Normal Play starts with empty inventory. Test Wood/Hats/Fiber/Sticks and the pickup map are opt-in fixtures.

| System | Current foundation | Remaining work |
| --- | --- | --- |
| Locomotion/camera | Move, jump, sprint, first/third-person; locomotion states | Final perspective animation and hardware coverage |
| Crouch/prone | Distinct capsules, clearance-gated exits, prone-body collision; client prediction tested | Moving decks, dedicated server, final animation polish |
| Survival | Authoritative stats/HUD/weight; contextual fresh-water drinking | Needs drain/damage, food, other water qualities, five-second stamina tuning, jump/climb costs, regeneration/fall damage |
| Inventory | 24 slots, stacking, weight, saved item definitions; selection/details and live refresh | Durability/freshness/item instances, preview/tabs, discard and crafting |
| Pickups | Owned requests; server range/aim/visibility validation; partial transfer and competition | Production world content and target-specific actions; see interaction foundation |
| Interaction | M6 foundation: E/X prompts, server Press/Hold timing/cancellation, fresh-water action; opt-in Inspect fixtures | Actual station/storage/ship/vendor actions, remapping and final presentation |
| Equipment | Atomic owned-unit equip/unequip/swaps with capacity checks | Cosmetics, armor effects, durability and persistence |
| Gathering | Hand fiber/stick pools use E/X; equipped-hatchet trees use Left Mouse/RT and server validation | Production vegetation/balance, berries, mining/regrowth, bare-hand punching/injuries, swing presentation and durability |
| Hotbar | Eight owned-definition shortcuts; 1–8/LB/mouse assignment; safe equipment activation | Consumables, maps/taming/harpoon actions, remapping and persistence |
| Ship/world/prologue | Current Bible and owner decisions recorded | Production ship loop, Port/missions, navigation and save/load |

The interaction foundation has ten native automation tests and 31 standalone/31 client checkpoints; see [interaction verification](VERIFICATION.md#interaction-foundation). Earlier gameplay acceptance includes 20 standalone/20 client survival HUD checkpoints and 42 network hotbar regressions. See [verification](VERIFICATION.md) for exact scope and historical evidence. Local listen-server packet emulation is not production multiplayer acceptance. Final artwork, physical controller, packaged and dedicated-server coverage remain open.

Survival still uses prototype 15/s sprint drain and 10/s recovery. The owner confirmed recovery while walking as well as stationary. Hunger is currently normalized 0–100%; 50 kg carry capacity is provisional, displayed rather than enforced as a hard cap. Do not claim full M4 completion or invent unspecified needs-damage/scaling rules.

<a id="next-work"></a>

## Next work

**M6 interaction foundation is verified complete for the October 6 run.** The first hand-resource gathering slice is verified on `codex/hand-gathering`; [evidence](VERIFICATION.md#hand-gathering). Equipped-hatchet Attack harvesting is verified on `codex/hatchet-harvesting`; [evidence](VERIFICATION.md#hatchet-harvesting). Bare hands remain temporarily disabled until injury/treatment rules are resolved. Berries/mining and resource content remain before crafting/skills. Tree harvesting remains Attack; detailed resource/tool/injury decisions stay explicit before their dependent implementation. [M6 acceptance and remaining gates](VERIFICATION.md#m6-interaction-closeout).

Milestone A is approved and published on main at `adc9693` after the owner said "Let's continue. I approve." Device-aware prompts and server-controlled holds passed 31 standalone/31 client checkpoints, with all ten pickup and 42 network hotbar regressions passing. The additional survival return slice is fresh-water drinking on `codex/fresh-water-interaction`: E/X refills hydration instantly at an eligible visible source, without requiring prone. Salt-water consequences remain TBD. One-second Inspect fixture holds, walking while aimed/in range, and Campfire/Smithy fixtures remain draft choices. Tree punching remains Attack, outside this interaction slice. `.mcp.json` stays local; editor preferences are preserved. Current authority is owner decisions, then Shared, then team guides; the supplied DOCX guides identify October 5 source revision and await the October 6 changes. Port rule carryover awaits confirmation.

Development guide chapter 41 (archived Master §24.3) specifies: baseline -> locomotion/input -> camera/animation state -> survival/HUD -> items/inventory/equipment -> interaction -> gathering -> crafting/skills -> sword/enemy -> shovel/map objective/treasure -> ship/helm/anchor/cargo/weight -> cannons/shared ammo -> day/night/cold/fire/clothing -> Port/vendors -> prologue logic -> map/compass -> additional encounters/polish. Use this dependency order as the reference; conversational milestone labels are not a one-to-one numbering of that list. For the owner's October 6 auto-approved run through M6, M6 means the recorded interaction-framework package: shared pickup/world targeting, E/X prompts, Press/Hold authority and cancellation, Inspect-only resource/station fixtures, plus the fresh-water return slice. It does not include gathering/crafting or production ship/vendor/storage actions. See [M6 closeout](VERIFICATION.md#m6-interaction-closeout).

M4 remains partially implemented. The [HUD return slice](VERIFICATION.md#m4-hud) now supplies health/stamina/food/hydration/weight gauges and empty-stat warnings. Activity-dependent needs drain, starvation/dehydration consequences, salt/other-water drinking, food, five-second base stamina timing, jump/climb costs and regeneration remain open. October 6 owner clarification permits recovery while walking. Upgraded-stat/activity scaling and health-loss interpretation still require clarification. The owner move to M5 does not verify or cancel these requirements.

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
| Verification `verify_hatchet_play.py` | Mouse/RT, equipped-tool validation, E exclusion, strike admission and dual-resource conservation |
| Verification `verify_hand_gathering_play.py` | Hand-resource prompts, authoritative/replicated conservation, full/partial inventory and competition |
| Verification `verify_water_play.py` | Fresh-water E/X, hydration HUD, invalid requests and shared-source use |
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

### Trying the interaction fixtures

Start Play in `/Game/Elitewake/Maps/Lvl_M5PickupTest`, then run `py C:/UnrealProjects/EW/Scripts/Setup/spawn_interaction_play_fixtures.py` from the editor Python console. Look at a fixture within 250 cm and follow E/X or Hold E/X. Campfire uses a one-second draft hold; Smithy, Tree and Rock acknowledge a press. Inspect does not harvest or craft. Stop Play to remove the fixtures; the script never saves a map.

### Trying fresh-water drinking

Start Play in `Lvl_M5PickupTest`, then run `py C:/UnrealProjects/EW/Scripts/Setup/spawn_water_play_fixture.py`. The opt-in script lowers hydration to 25% and marks a temporary source with blue bounds at (120, 100, 160). Look within 250 cm and press E/X; hydration immediately becomes 100% and the prompt hides until hydration falls. Stop Play removes the fixture and test state. Production ponds should place/size an `EWWaterSource` query surface over their authored water geometry; this slice adds no saved world content.

### Trying hand gathering

Start Play in `Lvl_M5PickupTest` and run `py C:/UnrealProjects/EW/Scripts/Setup/spawn_hand_gathering_play_fixtures.py`. The opt-in cubes at (120, 100, 160) and (120, -100, 160) hold Fiber and Sticks test pools. Look within 250 cm and press E/X. Only accepted inventory units leave a pool; depletion removes the actor. Stop Play removes test inventory/actors. Test yields 10/6 and weights 0.01/0.05 kg are temporary tuning. The script adds no default-world spawns. Existing Tree/Rock Inspect fixtures remain acknowledgement-only.

### Trying the hatchet tree

In `Lvl_M5PickupTest` Play, run `py C:/UnrealProjects/EW/Scripts/Setup/spawn_hatchet_play_fixtures.py`. E/X picks up the hatchet cube at (120, -100, 160); equip it in MainHand through inventory or hotbar. Aim at the tree cube at (120, 100, 160) and press Left Mouse/RT. E/X does not harvest trees. One press attempts a strike; holding does not auto-repeat. A one-second server admission interval, pools 12 Wood/4 Thatch and yields 3/1 are draft test tuning. Full/partial inventory preserves unaccepted resources. Bare-hand harvesting remains gated for this slice, not a permanent hatchet-only design rule. No saved/default world spawns, swing animation, tool mesh, sound, durability, stamina cost or injury gameplay is implied.
