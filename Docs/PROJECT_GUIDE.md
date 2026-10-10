# Project guide

Updated October 9, 2026. Active checkout: `C:\UnrealProjects\EW`. Engine: **Unreal 5.8.3**. Repository: **elitegamelabs/Project-Elitewake**. The OneDrive copy is a backup, not the working project.

## Current state

This is a tested gameplay foundation for version 0.01, not a finished pirate sandbox. Normal Play starts with empty inventory. Test Wood/Hats/Fiber/Sticks and the pickup map are opt-in fixtures.

| System | Current foundation | Remaining work |
| --- | --- | --- |
| Locomotion/camera | Move, jump, sprint, first/third-person; locomotion states | Final perspective animation and hardware coverage |
| Crouch/prone | Distinct capsules, clearance-gated exits, prone-body collision; client prediction tested | Moving decks, dedicated server, final animation polish |
| Survival | Authoritative stats/HUD/weight; fresh-water drinking and Azren eating/healing | Needs drain/damage, other food/cooking and water qualities, five-second stamina tuning, jump/climb costs, regeneration/fall damage |
| Inventory | 24 slots, stacking, weight, selection/details; berry freshness batches and live bars | Other item use, durability/persistence, final preview/tabs and discard; crafting foundation verified below |
| Pickups | Owned requests; server range/aim/visibility validation; partial transfer and competition | Production world content and target-specific actions; see interaction foundation |
| Interaction | M6 foundation: E/X prompts, server Press/Hold timing/cancellation, fresh-water action; opt-in Inspect fixtures | Actual station/storage/ship/vendor actions, remapping and final presentation |
| Equipment | Atomic owned-unit equip/unequip/swaps with capacity checks | Cosmetics, armor effects, durability and persistence |
| Gathering | Hand fiber/stick/berry pools use E/X; equipped-hatchet trees and pickaxe nodes use Left Mouse/RT and server validation | Production vegetation/ore distribution/balance, other berry definitions, regrowth, bare-hand punching/injuries, deferred swing presentation and durability |
| Hotbar | Eight owned-definition shortcuts; 1–8/LB/mouse assignment; equipment and authored berry consumption | Other consumables, maps/taming/harpoon actions, remapping and persistence |
| Objectives | Controller-owned, server-controlled ordered sequence and owner-only replicated snapshot; 17 native tests pass | Production events/rewards, final objective layout and persistence |
| Ship/world/prologue | Ships remain central and highly customizable; one NPC trade **Port** per region (four currently) retains PvP safety, specialized vendors, Ferryman links and introduction rules; "THE SHIP IS HOME" is retired | Production ship loop, four weather-biome Port islands, missions, navigation and save/load |

Acceptance evidence and coverage limits live in [VERIFICATION.md](VERIFICATION.md). Physical-controller, packaged and dedicated-server coverage remain open.

Survival still uses prototype 15/s sprint drain and 10/s recovery. The owner confirmed recovery while walking as well as stationary. Hunger is currently normalized 0–100%; 50 kg carry capacity is provisional, displayed rather than enforced as a hard cap. Do not claim full M4 completion or invent unspecified needs-damage/scaling rules.

<a id="next-work"></a>

## Next work

Owner resumed development after the engineer review and adopted the [private multiplayer testing plan](PRIVATE_MULTIPLAYER_TESTING.md). Advance the next small slice through configured-class/spawn auditing and separate-process host/client acceptance, then a minimal Host/Join/failure flow. This supplements world creation without cancelling the remaining prologue/gameplay backlog. The networked foundations already exist; no rewrite from a single-player baseline is required. Two-PC/Internet/distribution remain unverified. Publishing and external network/account changes still require explicit authorization.

Owner authorized automatic continuation on October 9 until account usage prevents further work or the owner pauses/cancels. An hourly chat heartbeat (`continue-elitewake-build`) resumes small verified slices and reports meaningful outcomes or required decisions. This does not change unresolved design gates or confer new publication permission. Build evidence and remaining work must be updated at each slice rather than treating scheduled continuation as feature completion.

The owner-designated [complete October 9 update](OCTOBER_9_COMPLETE_REVIEW.md) overrides conflicting older design. All 33 sections have been reconciled; creature/ocean/farming expansion remains planned rather than displacing the current crafting slice. Inventory-first placeables have been reaffirmed. The source DOCX is unchanged.

Owner confirmed HUD/controls in the active checkout and approved the enlarged [HUD redesign](DESIGN_REFERENCE.md#hud-redesign) on October 9. **Current step:** owner-requested M-key surrounding-map preview and larger inventory/crafting grids are implemented locally; then connect approved post-prologue recipe availability to the objective foundation. Crafting transaction/menu/client requests and four saved opt-in fixtures are implemented and verified. Wooden Shovel, Wooden Axe and Wooden Pickaxe cost 20 Wood each; Hide Water Flask costs 1 Hide + 10 Thatch. Read-only recipe readiness now shares transaction validation and drives the Craft button. Owner now confirms generic Wood and unlocks for all four recipes after the prologue. Next connect normal-player availability to a trusted prologue-completion event; do not silently promote test weights/art to production. The inn torch's session-only per-player pickup/message/highlight foundation is verified; production inn placement/use/save and Rye/Journal ordering remain open. See [first crafting decisions](DESIGN_REFERENCE.md). Campfires, storage chests and crafting stations are crafted into inventory before placement; construction pieces use the separate Builder's Plan. Exact final menu nesting and controls remain TBD. The rolled-back campfire/torch/chest starter set remains withdrawn.

Use the [October 9 decisions](DESIGN_REFERENCE.md#october-9-decisions) for material variants, regional farming/mining, crafting visuals, skill families and server configuration principles, together with the [October 8 decisions](DESIGN_REFERENCE.md#october-8-decisions) for current design and the [resource/ecology review](DESIGN_REFERENCE.md#resource-ecology) for regional direction. The berry loop remains verified: Azren restores 1/16 Hunger and 5% maximum Health and expires after twenty real minutes into an inedible toxic resource. Marad authoring, production vegetation and persistence remain separate work.

The October 8 rollback withdrew later crafting/ecology INIs, starter-recipe costs/unlocks and the unfinished loader. Recovery files are local history, not current configuration. See [checkpoint restoration](VERIFICATION.md#checkpoint-restore-october-8). Root `.mcp.json` and editor preferences remain local; publishing new changes requires owner authorization.

Development guide chapter 41 (archived Master §24.3) specifies: baseline -> locomotion/input -> camera/animation state -> survival/HUD -> items/inventory/equipment -> interaction -> gathering -> crafting/skills -> sword/enemy -> shovel/map objective/treasure -> ship/helm/anchor/cargo/weight -> cannons/shared ammo -> day/night/cold/fire/clothing -> Port/vendors -> prologue logic -> map/compass -> additional encounters/polish. Use this dependency order as the reference; conversational milestone labels are not a one-to-one numbering of that list. For the owner's October 6 auto-approved run through M6, M6 means the recorded interaction-framework package: shared pickup/world targeting, E/X prompts, Press/Hold authority and cancellation, Inspect-only resource/station fixtures, plus the fresh-water return slice. It does not include gathering/crafting or production ship/vendor/storage actions. See [M6 closeout](VERIFICATION.md#m6-interaction-closeout).

M4 remains partially implemented. The [HUD return slice](VERIFICATION.md#m4-hud) now supplies health/stamina/food/hydration/weight gauges and empty-stat warnings. Activity-dependent needs drain, starvation/dehydration consequences, salt/other-water drinking, other food/cooking, five-second base stamina timing, jump/climb costs and regeneration remain open. October 6 owner clarification permits recovery while walking. Upgraded-stat/activity scaling and health-loss interpretation still require clarification. The owner move to M5 does not verify or cancel these requirements.

### Proposed 0.01 work packages after M5

1. Production gathering and crafting: extend the verified gathering/tool foundations with authored resources, recipes, resource costs and unlock prerequisites. C++ authority; Data Assets for recipes/resources; Blueprints for world content; UMG for crafting. Verify no resource duplication or unaffordable crafting.
2. Skills, simple combat and treasure: 7 skill-tree points and 1 character stat point per level, character cap 80, respec at levels 10/15/20 onward for 2 Gold, shovel/digging, map objective and small enemy encounter. Deterministic C++/Blueprint behavior; data-driven rewards. Verify progression and authoritative damage/rewards; node costs remain TBD where not assigned.
3. Small ocean and starter sloop: helm, hold-to-anchor, cargo, ship weight and two opposing cannons with shared limited ammunition. Depends on movement/interaction/inventory; test boarding, moving deck behavior, cargo transfer, anchoring and overload sinking in multiplayer. Implement current hardpoint and storage-only Ammo Bin rules.
4. Environment, Port/prologue and navigation: 90 real minutes each for day/night, contextual conditions, basic Port vendors, revised schooner battle/dinghy repair/journal opening, then map/compass. M opens the local surrounding-map preview; other map bindings remain TBD. Walking is allowed, sprint/stance/hotbar/inventory suppressed, and the world still runs. Command radial uses Middle Mouse / D-pad Right. Survival/HUD return work above must not be silently delayed until final polish.
5. Integrated 0.01 playthrough: Prepare/Sail/Discover/Loot/Upgrade on a small test world. Repeat dedicated-server and two-client checks, packaging, save/load where implemented, and performance checks. This does not imply the full prologue or finished content is ready.

### Crafting implementation slice — October 9

Native recipe data, an authority-only inventory transaction and inventory/crafting menu are built. Recipe availability is granted by trusted server code and replicated only to the owning player. Owned-controller requests validate possession and living status. Ingredients are aggregated and the complete post-craft inventory is validated before committing, including space freed by consumed ingredients. Each transaction yields one item. Exact-item ingredients support the owner-confirmed single generic Wood resource; no species-specific inventory/mixing system is required. Four saved opt-in recipe fixtures use the approved costs; generic Wood, 1 kg output/Hide weights and missing item art are prototype content. Authored icons are shared in recipe lists and large previews. I/Y opens inventory; Tab/RB switches crafting; arrows/d-pad or mouse select; Enter/A or the Craft button requests one item. Controls/layout remain a functional draft. Normal inventory still starts empty and normal gameplay does not grant these fixture unlocks. Post-prologue unlock timing is confirmed; its production trigger, final art/weights, tool/flask use and inn torch content remain open. Native regression and a client menu transaction pass; wider controller, latency, dedicated-server and packaging coverage remains pending.

### Prologue objective foundation — October 9

`UEWObjectiveComponent` is a default controller component, so progress is independent of the possessed pawn within the same controller session. Trusted server gameplay starts one authored sequence and reports validated current-step events. The component snapshots ordered IDs/descriptions/counts, rejects invalid or duplicate IDs, clamps progress without spillover, rejects stale-step reports and prevents restarting a completed sequence. Its state uses owner-only replication and a change delegate; no client completion RPC exists. Native tests and five listen-server/client replication/possession checkpoints pass. Read-only current-objective presentation now passes nine client Play checkpoints. Trusted recipe-reward integration now passes eight client Play checkpoints. Next define production objective events and the prologue endpoint. A compact current-step display shows authored description/count at the upper left, hides during inventory and clears on completion. A trusted `StartRecipeSequence` snapshots deduplicated recipe rewards; final completion unlocks them for the controlled survivor, and later server possession reapplies knowledge to the new inventory within the same controller session. The default sequence/reward list remains empty. No production prologue recipe grant, currency, save/reconnect or ship tutorial is claimed. The exact prologue endpoint (Port arrival versus introduction completion) remains pending owner clarification.

### Longer-term backlog

Starting-recipe integration: inventory components expose an editor-authored `StartingRecipes` list. Authority applies it during BeginPlay through the existing owner-replicated availability path; no finished items are granted. Native initialization and a real deferred-spawn/possession/client-menu lifecycle check pass. The production starting list remains empty: the owner confirms the four regular starter recipes unlock after the prologue, rather than at character creation. A trusted completion event still needs to grant them. This hook is not a progression/save system or a prologue-completion trigger. Existing fixture grants remain opt-in.

Item-image integration now reads each item definition's assigned texture for inventory/equipment rows and selected-recipe material rows, alongside the existing recipe-list/preview and hotbar image support. Icon-less items retain labels; finished tool/flask/torch art is still pending. Diagnostic checkerboard icon fixtures are isolated under Testing and never granted/unlocked in normal gameplay. This presentation work does not resolve species mixing, progression availability or production balance.

Inn torch return slice: `AEWInnTorchPickup` grants one unit per PlayerState in the current session, leaves the actor available to other players, and preserves entitlement on failed transfer. Looking at it displays the exact top-center owner message and retains a local silver bounding-frame highlight until collection. Its mesh becomes locally invisible after collection. This uses existing E/X interaction validation. A separate metadata fixture uses a placeholder cube and temporary 1 kg weight; flame/light, carried use, finished inn placement, cross-session identity/save and split-screen presentation remain pending. No prologue grants/currency or Journal ordering change is made. Seven in-process listen-server/client Play checkpoints passed through the ordinary interaction RPC route, including retained pickup entitlement after possession changes within the same session; physical E/X input is covered only by the existing interaction foundation, not newly certified by this torch script.

**Deferred harvesting presentation (owner confirmed October 7):** add hatchet chopping and pickaxe mining animations later, with first/third-person state, held-tool visuals and validated multiplayer presentation. The functional gathering slices do not claim these animations are complete. This backlog must remain visible until integrated and verified.

Ports, specialized vendors, Ferryman routes, currency, shipyard progression, larger customizable vessels and belongings transfer; sail damage/repair and deeper naval combat; storms/adventure encounters, ghost ships, floating salvage and dungeons; tribes and communication; crew roles and shared commands; Beast Mastery, taming/breeding; injuries/surgeon, aging/hair; world density and official regional hosting. Davy Jones quest is Removed, not a planned rejuvenation implementation.

Prologue and Rye-sale requirements are maintained in [DESIGN_REFERENCE.md](DESIGN_REFERENCE.md#resource-ecology), including zero starting currency and the 250 Copper introduction reward. Do not revive the old raft/shipyard opening.

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
| `Docs/PRIVATE_MULTIPLAYER_TESTING.md` | Adopted private listen-server testing/distribution plan and reconciled audit |
| `Docs/ARCHIVE/` | Historical source-review snapshots |
| `.codex/`, `.cursor/` | Shared Unreal/Scenario connector endpoints, without credentials |

Generated Binaries, Intermediate, Saved, DerivedDataCache and IDE state are ignored. Use Git LFS for Unreal binary assets; preserve commit history and focused commits. Local editor preferences belong in generated Saved/Config where possible.

## Development checks

Build `EWEditor Win64 Development` against this checkout before Play checks. Run automation filter `Elitewake` with `UnrealEditor-Cmd.exe`, `-unattended -nop4 -NullRHI`, `-ExecCmds="Automation RunTests Elitewake"` and `-TestExit="Automation Test Queue Empty"`. Do not append an early Quit command.

Run Play scripts from Unreal's Python console with an absolute path. Pickup/inventory/equipment/hotbar/HUD checks need fresh Play in `/Game/Elitewake/Maps/Lvl_M5PickupTest`; use standalone or in-process listen-server plus one client as their docstrings specify. Test scripts create PIE-only inventory, restore input/network/throttle state and remove callbacks. Stop Play afterward. Editor helpers never ship with the game.

| Scripts | Purpose |
| --- | --- |
| Setup `create_inventory_test_asset.py`, `create_equipment_test_assets.py`, `create_pickup_test_content.py` | Reconcile only named saved fixtures; preserve existing designer edits |
| Setup `create_hand_gathering_test_assets.py`, `create_hatchet_test_assets.py`, `create_mining_test_assets.py` | Create missing named gathering/tool fixtures; do not overwrite authored values |
| Setup `create_berry_test_asset.py` | Explicit approved display/effects/freshness migration of the existing berry fixture; authors its toxic resource while retaining identity/weight/stack size |
| Setup `configure_stance_animations.py` | Audited stance configuration; read prerequisites before using |
| Verification `verify_stance_play.py`, `verify_stance_clearance_play.py`, `verify_stance_network_play.py` | Animation/clearance/client stance checks |
| Verification `verify_interaction_play.py` | Device-aware Press/Hold, cancellation and server validation |
| Verification `verify_pickup_play.py` | Authority and competing pickup checks |
| Verification `verify_inventory_selection_play.py` | Inventory input, focus and live-refresh checks |
| Verification `verify_equipment_play.py`, `verify_equipment_network_stress.py` | Transfer/capacity and bounded request stress checks |
| Verification `verify_hotbar_play.py` | Assignment, activation, input isolation and conservation |
| Verification `verify_hatchet_play.py` | Mouse/RT, equipped-tool validation, E exclusion, strike admission and dual-resource conservation |
| Verification `verify_mining_play.py` | Pickaxe/hatchet separation, stone/ore identity, full/partial capacity, depletion and competing strikes |
| Verification `verify_food_play.py` | Inventory R/X, hotbar keyboard/controller, owned RPC rejection, replicated effects and separate-batch expiry |
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
| `spawn_berry_play_fixture.py` | E/X gathers Azren; confirm inventory details then Eat (R / X), or assign/use a hotbar slot; original Azul package/ID retained | [Berries](VERIFICATION.md#berry-gathering) |

Tool strikes require the owned MainHand capability and server admission; holding Attack does not auto-repeat. Bare-hand harvesting awaits injury/treatment decisions. Final held-tool visuals, swing animations, durability, stamina costs, regrowth and production vegetation are separate work. See the deferred animation backlog above.

## Surrounding map and menu presentation — October 9

M opens/closes a local overhead preview of the surrounding area; there is no HUD minimap. The capture follows the player, refreshes twice per second only while open, and is destroyed on close. A centered direction marker tracks facing. Walking and world time continue; sprint, stance changes, interaction, inventory and hotbar actions are suppressed. This is a prototype live preview, not explored-world cartography: discovery, ghost markers, zoom/pan, compass and authored map art remain planned. Other map bindings remain TBD.

Inventory and crafting use larger wrapping item/recipe tiles with a separate detail/action pane, following the owner-selected ARK: Survival Ascended direction. Assigned artwork is preferred; native placeholders remain for missing art. I opens inventory, Tab switches inventory/crafting, and M can switch from inventory to map. No character preview, search/categories or production starting unlocks are implied. The four opt-in recipe fixtures remain separate from normal post-prologue availability. See VERIFICATION.md for scoped checks.

Private multiplayer checkpoint: the reusable `Scripts/Verification/verify_separate_process_connection.ps1` passes four headless, loopback-only host/client connection checks. It leaves the regular editor untouched. The -Gameplay repeat now passes cross-process movement, owned crafting and pickup conservation. Inventory visibility and graceful disconnection remain open before private-testing acceptance; Host/Join/Leave and recovery now pass ten local lifecycle checkpoints; two-PC/LAN and physical-input acceptance are next; see PRIVATE_MULTIPLAYER_TESTING.md and VERIFICATION.md. No LAN or Internet acceptance is claimed. A local Development package now passes the bounded loopback smoke check below.

Separate-process gameplay uses explicit editor-build-only EWVerifyRole flags in two disposable loopback game processes, not the owner editor. Both role reports passed; 17 native regressions passed on the rebuilt module. Recipes remain owner-only, but inventory contents currently replicate to peers; that visibility gap is recorded without inventing inspection/loot permissions. See the private-testing guide for exact scope and deferred checks.

Private-test connection controls: F10 opens a separate Host/Join/Leave panel. Use Play > Standalone Game for travel; ordinary in-editor Play shows a disabled preview with instructions. Join uses local/private IPv4 (default port 7777). Host/Join/Leave reload the retained map and do not save session progress; the panel says so. EWGameInstance handles local travel and retained connection errors across arrival. Ten separate-process lifecycle checkpoints and 18 native tests pass; the existing gameplay repeat also passes. This is not a complete pause/main menu, Internet/authentication service or packaged release. Private inventory visibility and two-PC testing remain open. See PRIVATE_MULTIPLAYER_TESTING.md for steps and scope.

## Local Windows diagnostic package — October 9

`Scripts/Verification/build_private_windows.ps1` builds, cooks and archives the two retained test maps into a unique ignored `Saved/PrivateBuilds/` folder. Close the editor and EW games before running it. The current successful package is `Saved/PrivateBuilds/local-20261009-233201/Windows/EW.exe`; keep its entire Windows folder together. It is Development, built from dirty local source at c0084623ed4c1530c114c66a985458be81c405f8, and unpublished. PrivateBuildInfo.json records this scope, not a released version.

Five packaged headless loopback checks pass: archived build-label loading, exclusive local binding, distinct processes, admission/welcome and two replicated character instances with bounded connection stability. The editor connector is editor-only and absent from the runtime manifest. GameFeatureData scanning remains available to editor tools but is editor-only because EW has no runtime Game Feature assets. Next verify rendered packaged HUD/menus and physical controls, prerequisite portability, then two-PC LAN with the same build. Inventory visibility awaits the owner's decision; no replication rule is changed by this package. Production prologue completion and normal recipe unlocks remain unresolved.

The F10 connection panel now shows the package label, short source revision, Development configuration and local-change marker. Packaging writes PrivateBuildLabel.txt beside the packaged project and TEST_NOTES.md alongside the Windows folder. Unpackaged/missing-label launches explicitly say Unlabelled development build. The label is diagnostic information, not network compatibility enforcement or a complete source snapshot. Latest evidence is recorded in VERIFICATION.md.
