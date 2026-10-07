# Project guide

Updated October 7, 2026. Active checkout: `C:\UnrealProjects\EW`. Engine: **Unreal 5.8.3**. Repository: **elitegamelabs/Project-Elitewake**. The OneDrive copy is a backup, not the working project.

## Current state

This is a tested gameplay foundation for version 0.01, not a finished pirate sandbox. Normal Play starts with empty inventory. Test Wood/Hats/Fiber/Sticks and the pickup map are opt-in fixtures.

| System | Current foundation | Remaining work |
| --- | --- | --- |
| Locomotion/camera | Move, jump, sprint, first/third-person; locomotion states | Final perspective animation and hardware coverage |
| Crouch/prone | Distinct capsules, clearance-gated exits, prone-body collision; client prediction tested | Moving decks, dedicated server, final animation polish |
| Survival | Authoritative stats/HUD/weight; contextual fresh-water drinking | Needs drain/damage, food, other water qualities, five-second stamina tuning, jump/climb costs, regeneration/fall damage |
| Inventory | 24 slots, stacking, weight, saved item definitions; selection/details and live refresh | Player-facing freshness and consumption, durability/persistence, preview/tabs, discard and crafting |
| Pickups | Owned requests; server range/aim/visibility validation; partial transfer and competition | Production world content and target-specific actions; see interaction foundation |
| Interaction | M6 foundation: E/X prompts, server Press/Hold timing/cancellation, fresh-water action; opt-in Inspect fixtures | Actual station/storage/ship/vendor actions, remapping and final presentation |
| Equipment | Atomic owned-unit equip/unequip/swaps with capacity checks | Cosmetics, armor effects, durability and persistence |
| Gathering | Hand fiber/stick/berry pools use E/X; equipped-hatchet trees and pickaxe nodes use Left Mouse/RT and server validation | Production vegetation/ore distribution/balance, berry eating/freshness, regrowth, bare-hand punching/injuries, deferred swing presentation and durability |
| Hotbar | Eight owned-definition shortcuts; 1–8/LB/mouse assignment; safe equipment activation | Consumables, maps/taming/harpoon actions, remapping and persistence |
| Ship/world/prologue | Ships remain central and highly customizable; four **Ports** retain PvP safety, specialized vendors, Ferryman links and introduction rules; "THE SHIP IS HOME" is retired | Production ship loop, four weather-biome Port islands, missions, navigation and save/load |

The original interaction acceptance run had ten native automation tests and 31 standalone/31 client checkpoints; see [interaction verification](VERIFICATION.md#interaction-foundation). Earlier gameplay acceptance includes 20 standalone/20 client survival HUD checkpoints and 42 network hotbar regressions. See [verification](VERIFICATION.md) for exact scope and historical evidence. Local listen-server packet emulation is not production multiplayer acceptance. Final artwork, physical controller, packaged and dedicated-server coverage remain open.

Survival still uses prototype 15/s sprint drain and 10/s recovery. The owner confirmed recovery while walking as well as stationary. Hunger is currently normalized 0–100%; 50 kg carry capacity is provisional, displayed rather than enforced as a hard cap. Do not claim full M4 completion or invent unspecified needs-damage/scaling rules.

<a id="next-work"></a>

## Next work

The October 7 [resource/ecology draft review](DESIGN_REFERENCE.md#resource-ecology) records four updated resource regions: Northern Snow, Southern Desert, Central Swamp and Western Tropical. The owner approved **Azren** (formerly Azul) and **Marad** (formerly Mary-Dash) as names only, retaining existing effects and tame-food roles, including Marad for Manatee. Next food authoring should update display names through Unreal while preserving stable identities. The broader catalog, new fauna, farming candidates, balance/recipes and the proposed Manatee aquatic-plant diet remain draft/TBD. These regions do not assign the four Ports' biomes or stock; all existing Port rules remain unchanged, and "THE SHIP IS HOME" stays retired.

The October 7 [food transaction/freshness foundation](VERIFICATION.md#food-foundation) adds native, opt-in owned-unit eating and real-time inventory aging. Owner D056 specifies twenty real minutes, then conversion to an inedible toxic crafting resource. Later pickups use separate freshness batches so each retains its full lifetime. Existing saved berries are still disabled for eating and have no configured lifetime; this checkpoint does not change their Play behavior. **Next:** author the toxic/berry fixture data, connect inventory/hotbar eating and freshness presentation, then verify standalone and client requests before publishing the complete food flow. Toxic recipes and persistence remain separate work.

**Verified baseline:** M6 interaction/fresh-water foundations and hand resources, equipped-hatchet trees, pickaxe mining and berry gathering. The [integrated acceptance pass](VERIFICATION.md#integrated-acceptance) covered one continuous flow with 29 standalone/29 client checkpoints and the then-current 14 native tests. The later [food foundation](VERIFICATION.md#food-foundation) brought the native suite to 15 tests; it has no player-facing acceptance yet. Dated evidence and limitations belong in [VERIFICATION.md](VERIFICATION.md), rather than repeated release summaries here.

**Publication review:** `main` is at `9443259`; food, Port terminology and ecology/technology documentation are already published on `origin/codex/food-consumption-foundation` through `6bc2eee`, not merged into `main`. The repository cleanup is prepared locally on `codex/repository-audit-cleanup`. The owner requires approval before its push; older standing publication approvals do not override this request. Root `.mcp.json` is ignored and local editor changes remain excluded.

Development guide chapter 41 (archived Master §24.3) specifies: baseline -> locomotion/input -> camera/animation state -> survival/HUD -> items/inventory/equipment -> interaction -> gathering -> crafting/skills -> sword/enemy -> shovel/map objective/treasure -> ship/helm/anchor/cargo/weight -> cannons/shared ammo -> day/night/cold/fire/clothing -> Port/vendors -> prologue logic -> map/compass -> additional encounters/polish. Use this dependency order as the reference; conversational milestone labels are not a one-to-one numbering of that list. For the owner's October 6 auto-approved run through M6, M6 means the recorded interaction-framework package: shared pickup/world targeting, E/X prompts, Press/Hold authority and cancellation, Inspect-only resource/station fixtures, plus the fresh-water return slice. It does not include gathering/crafting or production ship/vendor/storage actions. See [M6 closeout](VERIFICATION.md#m6-interaction-closeout).

M4 remains partially implemented. The [HUD return slice](VERIFICATION.md#m4-hud) now supplies health/stamina/food/hydration/weight gauges and empty-stat warnings. Activity-dependent needs drain, starvation/dehydration consequences, salt/other-water drinking, food, five-second base stamina timing, jump/climb costs and regeneration remain open. October 6 owner clarification permits recovery while walking. Upgraded-stat/activity scaling and health-loss interpretation still require clarification. The owner move to M5 does not verify or cancel these requirements.

### Proposed 0.01 work packages after M5

1. Production gathering and crafting: extend the verified gathering/tool foundations with authored resources, recipes, resource costs and unlock prerequisites. C++ authority; Data Assets for recipes/resources; Blueprints for world content; UMG for crafting. Verify no resource duplication or unaffordable crafting.
2. Skills, simple combat and treasure: 15 cumulative points per level, character cap 80, respec from level 10 for 2 Gold, shovel/digging, map objective and small enemy encounter. Deterministic C++/Blueprint behavior; data-driven rewards. Verify progression and authoritative damage/rewards; node costs remain TBD where not assigned.
3. Small ocean and starter sloop: helm, hold-to-anchor, cargo, ship weight and two opposing cannons with shared limited ammunition. Depends on movement/interaction/inventory; test boarding, moving deck behavior, cargo transfer, anchoring and overload sinking in multiplayer. Implement current hardpoint and storage-only Ammo Bin rules.
4. Environment, Port/prologue and navigation: 90 real minutes each for day/night, contextual conditions, basic Port vendors, revised schooner battle/dinghy repair/journal opening, then map/compass. M/View opens map; walking allowed, sprint/stance/hotbar/inventory suppressed, world still runs. Command radial uses Middle Mouse / D-pad Right. Survival/HUD return work above must not be silently delayed until final polish.
5. Integrated 0.01 playthrough: Prepare/Sail/Discover/Loot/Upgrade on a small test world. Repeat dedicated-server and two-client checks, packaging, save/load where implemented, and performance checks. This does not imply the full prologue or finished content is ready.

### Longer-term backlog

**Deferred harvesting presentation (owner confirmed October 7):** add hatchet chopping and pickaxe mining animations later, with first/third-person state, held-tool visuals and validated multiplayer presentation. The functional gathering slices do not claim these animations are complete. This backlog must remain visible until integrated and verified.

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
| Setup `create_hand_gathering_test_assets.py`, `create_hatchet_test_assets.py`, `create_mining_test_assets.py`, `create_berry_test_asset.py` | Create missing named gathering/tool fixtures; do not overwrite authored values |
| Setup `spawn_interaction_play_fixtures.py`, `spawn_water_play_fixture.py`, `spawn_hand_gathering_play_fixtures.py`, `spawn_hatchet_play_fixtures.py`, `spawn_mining_play_fixtures.py`, `spawn_berry_play_fixture.py` | Temporary Play fixtures; see the compact usage table below |
| Setup `configure_stance_animations.py` | Audited stance configuration; read prerequisites before using |
| Verification `verify_stance_play.py`, `verify_stance_clearance_play.py`, `verify_stance_network_play.py` | Animation/clearance/client stance checks |
| Verification `verify_interaction_play.py` | Device-aware Press/Hold, cancellation and server validation |
| Verification `verify_pickup_play.py` | Authority and competing pickup checks |
| Verification `verify_inventory_selection_play.py` | Inventory input, focus and live-refresh checks |
| Verification `verify_equipment_play.py`, `verify_equipment_network_stress.py` | Transfer/capacity and bounded request stress checks |
| Verification `verify_hotbar_play.py` | Assignment, activation, input isolation and conservation |
| Verification `verify_hatchet_play.py` | Mouse/RT, equipped-tool validation, E exclusion, strike admission and dual-resource conservation |
| Verification `verify_mining_play.py` | Pickaxe/hatchet separation, stone/ore identity, full/partial capacity, depletion and competing strikes |
| Verification `verify_berry_play.py` | E/X berry gathering, food-stack capacity, depletion, rejection and replicated conservation |
| Verification `verify_integrated_play.py` | Continuous collected-inventory flow through selection, hotbar assignment/equipment, gathering, water and held interaction |
| Verification `verify_hand_gathering_play.py` | Hand-resource prompts, authoritative/replicated conservation, full/partial inventory and competition |
| Verification `verify_water_play.py` | Fresh-water E/X, hydration HUD, invalid requests and shared-source use |
| Verification `verify_survival_hud_play.py` | Rendered stats/warnings, carried weight and possession lifecycle |

<a id="repository-conventions"></a>

## Repository conventions

### Content and C++ organization

Create new game-specific assets under `Content/Elitewake/`, grouped by gameplay domain. Add a domain only when it has real content. Keep the runtime module `EW`; new classes belong beneath `Source/EW/` in the relevant domain, with headers and implementations together. Editor-only tooling stays in `Source/EWEditor/`.

Preserve native class/module identities and Unreal asset paths until package and Blueprint dependencies have been audited. Active ThirdPerson/Mannequin dependencies and the imported Free Animation Library are retained; being unused by today's test scene does not establish redundancy.

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

### Trying opt-in fixtures

Start Play in `/Game/Elitewake/Maps/Lvl_M5PickupTest`, then run the desired `Scripts/Setup/` script from Unreal's Python console using its absolute path. These fixtures are temporary: they do not save a map or grant normal-start inventory. Stop Play afterward. Read each script's prerequisites/docstring for coordinates and fixture tuning; production balance is not established by test yields or weights.

| Setup script | Action and behavior | Acceptance evidence |
| --- | --- | --- |
| `spawn_interaction_play_fixtures.py` | E/X Press or Hold; Campfire/Smithy/Tree/Rock Inspect only, no crafting or yield | [Interaction](VERIFICATION.md#interaction-foundation) |
| `spawn_water_play_fixture.py` | Starts hydration at 25%; E/X at the visible source restores 100%; no prone required | [Fresh water](VERIFICATION.md#fresh-water) |
| `spawn_hand_gathering_play_fixtures.py` | E/X transfers finite Fiber/Sticks; unaccepted units stay in the pool | [Hand gathering](VERIFICATION.md#hand-gathering) |
| `spawn_hatchet_play_fixtures.py` | Pick up/equip Hatchet, aim and press Left Mouse/RT; E/X does not chop | [Hatchet](VERIFICATION.md#hatchet-harvesting) |
| `spawn_mining_play_fixtures.py` | Pick up/equip Pickaxe, aim and press Left Mouse/RT; Hatchet cannot mine | [Mining](VERIFICATION.md#pickaxe-mining) |
| `spawn_berry_play_fixture.py` | E/X gathers Azren; saved display/package still says Azul pending supported authoring; eating/freshness disabled on the fixture | [Berries](VERIFICATION.md#berry-gathering) |

Tool strikes require the owned MainHand capability and server admission; holding Attack does not auto-repeat. Bare-hand harvesting awaits injury/treatment decisions. Final held-tool visuals, swing animations, durability, stamina costs, regrowth and production vegetation are separate work. See the deferred animation backlog above.
