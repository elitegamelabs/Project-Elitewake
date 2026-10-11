# Project guide

Updated October 11, 2026. Active checkout: `C:\UnrealProjects\EW`. Engine: **Unreal 5.8.3**. Repository: **elitegamelabs/Project-Elitewake**. The OneDrive copy is a backup, not the working project.

## Current state

This is a tested gameplay foundation for version 0.01, not a finished pirate sandbox. Normal Play starts with empty inventory. Test Wood/Hats/Fiber/Sticks and the pickup map are opt-in fixtures.

| System | Current foundation | Remaining work |
| --- | --- | --- |
| Locomotion/camera | Move, jump, sprint, first/third-person; locomotion states | Final perspective animation and hardware coverage |
| Crouch/prone | Distinct capsules, clearance-gated exits, prone-body collision; client prediction tested | Moving decks, dedicated server, final animation polish |
| Survival | Authoritative stats/HUD/weight; fresh-water drinking, Azren eating/healing and non-finite input rejection | Needs drain/damage, other food/cooking and water qualities, five-second stamina tuning, jump/climb costs, regeneration/fall damage |
| Inventory | 24 slots, stacking, weight, selection/details; berry freshness batches and live bars | Other item use, durability/persistence, final preview/tabs and discard; crafting foundation verified below |
| Pickups | Owned requests; server range/aim/visibility validation; partial transfer and competition | Production world content and target-specific actions; see interaction foundation |
| Interaction | M6 foundation: E/X prompts, server Press/Hold timing/cancellation, fresh-water action; opt-in Inspect fixtures | Actual station/storage/ship/vendor actions, remapping and final presentation |
| Equipment | Atomic owned-unit equip/unequip/swaps with capacity checks | Cosmetics, armor effects, durability and persistence |
| Gathering | Hand fiber/stick/berry pools use E/X; equipped-hatchet trees and pickaxe nodes use Left Mouse/RT and server validation | Production vegetation/ore distribution/balance, other berry definitions, regrowth, bare-hand punching/injuries, deferred swing presentation and durability |
| Hotbar | Eight owned-definition shortcuts; 1–8/LB/mouse assignment; equipment and authored berry consumption | Other consumables, maps/taming/harpoon actions, remapping and persistence |
| Crafting | Owned atomic transaction and client menu; four starter fixtures and separate 20 Wood + 20 Stone Repair Kit fixture | Production unlock events, station/timed crafting, final metadata and item use |
| Map/menu | M-key surrounding preview; larger inventory/crafting tiles and shared imagery | Explored cartography, final menu organization and packaged physical-input acceptance |
| Private testing | Host/Join/Leave/recovery, separate-process gameplay/late join and local Development archive | Inventory privacy decision, packaged menus/controls, clean-PC/two-PC/LAN, Shipping and distribution |
| Objectives | Controller-owned ordered sequence, owner-only snapshot/display and trusted completion recipe rewards | Production events/endpoint, final layout and persistence |
| Ship/world/prologue | Ships remain central and highly customizable; one NPC trade **Port** per region (four currently) retains PvP safety, specialized vendors, Ferryman links and introduction rules; "THE SHIP IS HOME" is retired | Production ship loop, four weather-biome Port islands, missions, navigation and save/load |

Acceptance evidence and coverage limits live in [VERIFICATION.md](VERIFICATION.md). The latest native suite has **19 passing tests**; packaged startup/connection checks cover only their recorded scope. Physical-controller, full packaged gameplay and dedicated-server coverage remain open.

**Current editor status:** the editor connector now responds, reports Play stopped, and its log records a recent ThirdPerson Play session and teardown. The earlier startup stall has cleared; its cause is unconfirmed. No restart or scene mutation was performed for the consolidated review.

Survival still uses prototype 15/s sprint drain and 10/s recovery. The owner confirmed recovery while walking as well as stationary. Hunger is currently normalized 0–100%; 50 kg carry capacity is provisional, displayed rather than enforced as a hard cap. Do not claim full M4 completion or invent unspecified needs-damage/scaling rules.

<a id="next-work"></a>

## Next work

**October 11 maximum ocean depth:** the owner sets the deepest ocean to **500 meters below the mean surface**, replacing the earlier approximate half-mile maximum. The saved coastal swimming brush and flat prototype seabed match this depth. Basin shapes, underwater shelves and terrain transitions remain planned; preserve the existing shallows and visual wave surface.

**October 11 owner-directed coast/water pass:** development resumed locally;
Fab acquisition is deferred and the old heartbeat remains paused. The existing
coastal map now has a brush-backed swimming ocean, generated sand/timber textures,
an original irregular sloped shore and small animated visual waves. Retain the
same gathering, inventory and introduction recipe gates. See
[coastal play instructions](COASTAL_PLAYGROUND.md) and current water verification.
Vessel buoyancy, production terrain/foliage, swimming animations, underwater
presentation and audio remain separate dependencies. The owner requested
GPT-Realtime-1.5 for sounds; it is documented as a voice model and no audio tool
or API credential is connected. No sound generation or import is claimed.

**Company foundation:** [Company design](COMPANY_DESIGN.md) records the owner's approved configurable ownership policies and personal tames counting toward both caps. Session-only membership, invitations, roster, leadership and permission checks plus policy selection are implemented locally: 21 native tests, 15 network checkpoints and four actual menu-click checkpoints pass. Open I → Company. Policies do not yet affect world assets. Actual tame-total accounting, persistence, logs, alliances, crew groups and mergers remain unbuilt. The coastal/sloop slice remains active. The owner also confirms the ten named skill constellations, with ten skills each.

**Skills presentation direction:** opening Skills pans into a night sky of selectable constellations, each with exactly ten unlockable skills. See [skill constellations](SKILL_CONSTELLATIONS.md). Constellation roster and actual skill definitions/costs need authoring; the existing progression awards and respec rules remain. This is recorded direction, not an implemented system, and does not replace the coastal/sloop milestone.

**Connected world slice saved:** [coastal playground](COASTAL_PLAYGROUND.md) is open in the editor. It links beach Wood/Stone, a six-tree grove, fiber/Azren gathering, mining nodes, a freshwater spring and an over-water dock in one map, with a nearby islet for the coming vessel loop. Listen/client acceptance checks actual placed resources and recipe locks. The October 11 pass adds textured sand/timber, a sloped shoreline and swimmable ocean with small visual waves; vegetation/interior remain blockout. Wildlife, sailing and production introduction completion are still unbuilt. Next connect the first controllable two-hardpoint sloop to this scene.

**Owner workflow reset:** the previous hourly continuation is paused. The owner requests a cohesive playable pirate world, detailed image-based survival HUD art, and resources/wildlife in the shared scene. All four newly supplied guides were read and reconciled in [consolidated build review](CONSOLIDATED_BUILD_REVIEW.md). Preserve the tested foundations; the next world deliverable is a separately saved connected coastal playthrough, with gathering/crafting leading into a small-vessel journey and Port onboarding. Owner answers: four regular recipes unlock after the innkeeper introduction; Journal is a permanent menu reference; first sloop has two cannon hardpoints. The owner supplies a translucent three-panel menu reference; inventory/crafting presentation is being revised first. Production completion/unlock integration remains unbuilt. The historical work order below remains context, not permission to continue the old automation unchanged.

Owner resumed development after the engineer review and adopted the [private multiplayer testing plan](PRIVATE_MULTIPLAYER_TESTING.md). Configured-class/spawn auditing, separate-process gameplay, Host/Join/Leave recovery, diagnostic packaging and three-process late-join acceptance are verified within the scopes recorded below. Handshake cancellation and abrupt host loss now pass, with two runtime recovery fixes. Next private-testing work is rendered packaged controls and owner-assisted two-PC acceptance. This supplements world creation without cancelling the remaining prologue/gameplay backlog. The networked foundations already exist; no rewrite from a single-player baseline is required. Two-PC/Internet/distribution remain unverified. Publishing and external network/account changes still require explicit authorization.

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

Item-image integration now reads each item definition's assigned texture for inventory/equipment rows and selected-recipe material rows, alongside the existing recipe-list/preview and hotbar image support. Icon-less items retain labels; final tool/flask/torch art is still pending; generated placeholders are recorded below. Diagnostic checkerboard fixtures and the newer generated icons remain testing content without normal grants/unlocks. Wood is now confirmed as one generic resource; production availability and balance remain pending.

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

## Map and inventory presentation

M toggles a surrounding overhead preview without a HUD minimap. It follows the player and facing, refreshes twice per second while open, and destroys its capture on close. Walking and world time continue; sprint, stance changes, interaction, inventory and hotbar actions are suppressed. Discovery, ghost markers, zoom/pan, compass, authored cartography and other map bindings remain pending.

Inventory/crafting use larger wrapping tiles and a separate detail/action pane in the owner-selected ARK: Survival Ascended direction. I/Y opens inventory; Tab/RB switches crafting; arrows/d-pad or mouse select; Enter/A crafts. Assigned item art is preferred, with native fallback icons. Character preview, search/categories, final menu nesting and production unlocks remain pending.

## Current art, tools and recipe fixtures

A sixth generated source icon, Art/Placeholders/ItemIcons/RepairKit-v1.png, is prepared for the Repair Kit fixture. Its original RGBA 1254x1254 PNG/alpha, unchanged source hash and visual review pass (Saved/RepairKitArtResult.json); prompt/provenance are in generation.json. The six-item importer mapping parses but has not been run while editor startup is unresolved. No T_RepairKit_v1 texture/assignment or packaged imagery is claimed; current 071931 uses fallback art for the kit. After editor recovery, run the importer, verify the client kit icon and add the imported texture to required cooked-content checks. The wood/stone bundle's cord is presentation only; recipe costs and repair behavior remain unchanged.

Five original ChatGPT-generated transparent icons (Wooden Axe, Pickaxe, Shovel, Hide Water Flask and Inn Torch) live in Art/Placeholders/ItemIcons with exact prompts/provenance in generation.json. Imported textures live under /Game/Elitewake/UI/PlaceholderIcons; `Scripts/Setup/import_placeholder_item_art.py` reproduces assignment without normal grants. These are 2D placeholders; held/world meshes, flame/light and final art remain open.

Wooden Axe/Pickaxe fixtures equip in MainHand and reuse existing Hatchet/Pickaxe capabilities. `Scripts/Verification/verify_starter_tool_loop_play.py` passes seven client checkpoints covering 20-Wood crafting, all five icons, hotbar equipment, finite tree/mining conservation, wrong-tool rejection and independent host state. No new yield, durability, animation or stamina balance is inferred. Shovel digging and flask fill/drink remain pending.

The separate Repair Kit fixture costs 20 generic Wood + 20 Stone. `Scripts/Setup/create_prologue_repair_recipe.py` creates missing item/recipe assets outside Play and validates existing costs without overwriting them; its repeat passed. `Scripts/Verification/verify_prologue_repair_recipe_play.py` passes seven client-menu checkpoints for empty starts, costs, shortage preservation, readiness, one replicated output, repeat rejection and independent host/regular recipes still locked. Output metadata is explicitly test-only (1 kg, single-unit stack, miscellaneous category and fallback imagery). Repair use and production tutorial unlock events remain unbuilt. The four regular starter recipes still unlock after the unresolved production prologue completion event.

## Private multiplayer checkpoint

F10 opens the diagnostic Host/Join/Leave panel and closes inventory/map. Use Standalone Game for travel; ordinary in-editor Play shows a disabled preview. Join accepts local/private IPv4 (default port 7777), rejecting arbitrary URLs, public addresses, hostnames and IPv6. Host/Join/Leave reload the retained map without saving session progress. GameInstance preserves arrival/errors; Leave/Cancel cancels pending connections/callbacks, and established-session timeout shows the lost-host message. This is a private-test flow, not a final main/pause menu, authentication service or Internet transport.

| Verification | Recorded scope | Evidence |
| --- | --- | --- |
| Separate-process gameplay | Movement, owned crafting, pickup conservation and request rejection; 13 observations include public inventory visibility | Saved/SeparateProcessGameplayResult.json |
| Third-player late join | 17 acceptance checks plus 3 public-inventory observations; current pickup state, empty start and rejected grants/craft | Saved/SeparateProcessLateJoinResult.json |
| Graceful lifecycle | 10 local Host/Join/Leave, menu/input-lock and recovery checkpoints | Saved/SessionLifecycleResult.json |
| Pending cancel/abrupt host shutdown | 13 checkpoints, including 25 seconds without stale cancellation error and subsequent join/recovery | Saved/SessionRecoveryResult.json; raw logs in Saved/SessionRecovery |

Gameplay/lifecycle harnesses are opt-in WITH_EDITOR code and absent from packaged targets. The late-join fixture clears pawns away from fallback spawn; it does not certify production spawn capacity. Inventory Entries currently replicate publicly while recipe knowledge/objectives are owner-only; owner privacy policy is pending. No inspection/loot/raid permission is inferred. See [private testing](PRIVATE_MULTIPLAYER_TESTING.md) and [verification](VERIFICATION.md) for limits and historical runs.

## Current local Windows diagnostic archive

Latest archive: **Saved/PrivateBuilds/local-20261010-071931**. Launch Windows/EW.exe and keep the entire Windows folder. Development Win64, dirty source at 52678ecb34333205fc095d9a9bb38b3db286de02, unpublished; the label is diagnostic, not compatibility enforcement or a complete source snapshot. F10 displays the package/source/configuration label; unpackaged launches say Unlabelled development build.

`Scripts/Verification/build_private_windows.ps1` requires editor/EW games closed, builds/cooks the two retained maps, explicitly cooks Content/Elitewake and creates a unique archive. All **16 starter/prologue packages** pass cooked-registry and actual IoStore-container checks, including the Repair Kit. Its runtime SHA256 matches the current compiled Game target. This archive includes the survival numeric guard and kit fixture without granting normal inventory/knowledge or adding repair behavior. The editor connector/runtime dependencies and unused GameFeatureData scan remain editor-only.

| Archive check | Result/evidence | Scope limit |
| --- | --- | --- |
| Editor/Game build, cook/stage/archive | Pass; PrivateBuildInfo.json | Local Development, no release certification |
| 16 required packages | CookedStarterContentResult.json + StarterContainerListing.csv | Presence only, not packaged crafting/use |
| Runtime executable identity | RuntimeBinaryResult.json | Matches compiled executable, not gameplay acceptance |
| VC x64/ARM64 installers | PrerequisitesResult.json | Valid Microsoft signatures + engine hashes; not executed/clean-PC certified |
| Packaged loopback | 5 checks; PackagedConnectionResult.json and host/client logs in archive | Startup/admission/two characters and bounded stability; not LAN |
| Rendered startup HUD | 1280x720, 1920x1080, 2560x1440; Saved/RenderedStartup/20261010-072151 | Default stats, empty hotbar/arena; no physical menus/controls or performance |

UAT -prereqs stages vc_redist.x64.exe and vc_redist.arm64.exe under Windows/Engine/Extras/Redist/en-us; `verify_private_windows_prerequisites.ps1` checks them without installation. Use the x64 installer interactively on an x64 tester PC if needed. ARM64 redistribution supports the engine's emulation setup, not verified native ARM64. GameInput redist remains unconfigured. TEST_NOTES.md explains setup/limitations.

`verify_packaged_rendered_startup.ps1` captures normal-renderer offscreen HUD frames, checks build label/real PNG sizes, leaves visual review pending, and terminates only its helpers. Standard captures three 16:9 sizes; AspectRatios captures 4:3/ultrawide. The 022851 archive has historical 4:3/ultrawide evidence at Saved/RenderedStartup/20261010-032123; that was not repeated on the current archive. Previous archives and detailed chronological evidence are preserved in [VERIFICATION.md](VERIFICATION.md).

Editor restoration is unresolved: first startup PID 22080 stalled before level/connector and was stopped only after identification; no unsaved project edits were loaded. Normal-access startup PID 10860 completed SDK detection with exit 0 but still has no verified level/connector. No new project crash directory was found. Logs/status: Saved/EditorStartup/20261010-071931-package-restart. Owner DefaultEditor.ini retains SHA256 0E61E2200AEAB9EC14A2CD1C55F024F1CCAB668D1C43759D89B71DD9D7B0185A. Await the owner's startup-dialog observation; leave the current process alone. No startup cause or restored editor is claimed.

## Outstanding decisions and acceptance

| Decision/check | Work it gates |
| --- | --- |
| Production prologue endpoint and Journal/torch order | Trusted normal-player objective events, currency/recipe completion integration |
| Flask capacity, hydration per drink and refill-water scope | Flask fill/drink use |
| Inventory visibility policy | Owner-only inventory versus explicit future inspection/loot behavior |
| Repair targets/use/amounts, final item weights/art/stacking and other unspecified balance | Production item/tool/combat content; test metadata stays provisional |
| Owner observation of stalled editor startup | Editor-assisted content/Play acceptance |
| Packaged menus/keyboard/controller, alternate stats/debuffs, clean-PC setup, two PCs/LAN, Shipping/distribution | Wider private-testing acceptance; source/native checks do not substitute |

Continue independent foundations in the dependency order above. Do not rerun unchanged acceptance merely because a heartbeat fires, replace normal starts with fixtures, or infer new publication/network/setup permission. Original DOCX/preferences and prior evidence remain preserved. Remote publication is still unapproved for these local changes.
