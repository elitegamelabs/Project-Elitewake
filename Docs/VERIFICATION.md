# Verification record

Updated October 6, 2026. Each section records a dated implementation slice and its limits. Use the [project guide](PROJECT_GUIDE.md) for current status and the [design reference](DESIGN_REFERENCE.md) for authority. Historical failures remain here so they cannot be mistaken for successful acceptance.

## Contents

- [Foundation history](#foundation-history)
- [M2 stance animations](#m2-stance) and [collision/clearance](#m2-collision)
- [M4 survival HUD](#m4-hud)
- M5 [persisted inventory fixture](#m5c-inventory), [pickups](#m5d-pickups), [selection](#m5e-selection), [equipment](#m5f-equipment), [hotbar](#m5g-hotbar)
- [Repository cleanup](#repository-cleanup)

## Foundation history

The following baseline table and ledger were consolidated from the October 6 status record. Entries describe their original checks; later sections extend those results.

| Milestone/system | Gameplay implementation | Presentation/content | Multiplayer evidence | Files and commits |
| --- | --- | --- | --- | --- |
| M0 foundation | Verified: active repository/path and history inspected | Project structure documented; template content | No online infrastructure claimed | `EW.uproject`, `.gitignore`, `README.md`, `Docs/PROJECT_GUIDE.md#repository-conventions`; `919737f`, `50ecc95` |
| M1 locomotion | Implemented: move/jump, walk 500, sprint 750 | Template animations | Sprint state replicated in source; network session not repeated in this review | `Source/EW/EWCharacter.*`; `d8ca1dc` |
| M2 stance | Verified foundation: tap C/B, hold 0.35s prone; distinct stance sizes, clearance-gated exits and prone body movement query | Proper stance blends, aligned roots and camera; final polish/controller hardware coverage open | Client/host collision states verified with 100 ms outgoing packet lag and 1% loss; dedicated server/moving decks pending | `EWCharacter.*`, `EWCharacterMovementComponent.*`, `ABP_EWLocomotion`; [collision verification](VERIFICATION.md#m2-collision) |
| Temporary stance scaling | Replaced: reverted | Do not restore as animation substitute | Not applicable | `cf282a8` reverted by `e88acb1` |
| M3 cameras/states | Implemented: default third person, Z toggle; six locomotion states | Cyan diagnostics temporary; final perspective animations Planned | Perspective local; state source inspected, network presentation pending | `EWCharacter.*`; `fb214b3` |
| M4 survival | Implemented stats; current stamina drain 15/s and recovery 10/s, including walking; full needs gameplay remains open | Verified draft health/stamina/food/hydration/weight gauges and 1.5-second empty-stat warnings | Standalone/client HUD checks pass with packet emulation; retained owner-only exhaustion notification; dedicated server pending | `EWSurvivalComponent.*`, `EWSurvivalWidget.*`; [HUD return evidence](VERIFICATION.md#m4-hud) |
| Integrations | Implemented: Unreal MCP auto-start, Git editor, client configs | Scenario availability reported by handoff; no asset request made | Not gameplay | `EW.uproject`, `Config/DefaultEditorPerProjectUserSettings.ini`, `Config/DefaultSourceControlSettings.ini`; `0e18009`, `2f36734`, `edb52c3` |
| M5A items/inventory | Implemented: definitions, categories/slot metadata, 24 slots, stacking, add/remove/count/weight | No game item assets/pickup evidenced in this slice | Replicated entries; server-only mutation source inspected. Multi-client behavior pending | `EWItemDefinition.*`, `EWInventoryComponent.*`, `EWInventoryComponentTests.cpp`; `9b7f129` |
| M5B inventory panel | Verified: build, empty panel, I open/close/reopen and walking/camera recovery | Native functional draft; not final inventory design | Local-only Play test; remote populated inventory not verified | `EWInventoryWidget.*`, `EWPlayerController.*`; `286f8d0`, pushed after owner approval |
| M5C persisted test item/grant | Verified: saved asset registration/load, stacking/capacity/weight tests and populated Play panel | Wood (Test), resource stack 250, temporary fixture weight 0.1 kg | Authority check and no client grant RPC; multi-client behavior not verified | `DA_TestWood`, editor-only `EWGrantTestWood`; [verification](VERIFICATION.md#m5c-inventory) |
| M5D pickups | Verified: server range/aim/visibility/ownership checks, partial transfer and exhaustion | Saved Wood pickup Blueprint and isolated test map; E/controller X draft bindings | Competing host/client intent conserves quantities; inventory/remainder replication verified under 100 ms outgoing lag/1% loss | `EWPickup.*`, `EWPlayerController.*`; [verification](VERIFICATION.md#m5d-pickups) |
| M5E selection/details | Verified: first selection, highlight, keyboard/D-pad/stick/mouse navigation, read-only confirmation and safe live refresh | Native scrolling draft, I/Y open and UI focus; physical controller/final art pending | 19 client UI checkpoints pass with replicated authority changes under local packet emulation | `EWInventoryWidget.*`, `EWPlayerController.*`; [verification](VERIFICATION.md#m5e-selection) |
| M5F equipment | Verified: ownership/slot validation, atomic equip/unequip and occupied-slot swaps; worn weight retained | Equipped rows, action button/R/X and result feedback; opt-in hat fixtures | 12 client checkpoints pass under 100 ms outgoing lag/1% loss; foreign pawn unaffected | `EWEquipmentComponent.*`, inventory/controller/widget; [verification](VERIFICATION.md#m5f-equipment) |
| M5G hotbar | Verified foundation: eight owned-definition shortcuts, assignment/move/clear, safe equipment activation | Permanent native draft HUD; 1–8, contextual mouse buttons and LB combinations; final art/hardware pending | 42 standalone and 42 client checkpoints pass with packet emulation; owner-only bindings and quantity/weight conservation | `EWHotbarComponent.*`, `EWHotbarWidget.*`, inventory/controller; [verification](VERIFICATION.md#m5g-hotbar). Other item actions and persistence remain open |

### Verification ledger

| Date | Check | Result / boundary |
| --- | --- | --- |
| 2026-10-05 | Active path, Git status/history, GitHub repository | Verified `C:\UnrealProjects\EW`, private repository and main default branch; four original UI files uncommitted |
| Historical 2026-09-30 local time | `Elitewake.Inventory.StackingAndWeight` | Success recorded in `Saved/Logs/EW-backup-2026.10.01-02.55.24.log`; stacking/removal/survival-weight unit checks only |
| 2026-10-05 | EWEditor Win64 Development baseline | Succeeded; target up to date |
| 2026-10-05 | Initial Play inventory check | Failed: I showed cursor but invisible panel; native tree constructed too late. Fixed by building before `Super::RebuildWidget()`; subsequent successful retest below |
| 2026-10-05 | Repaired EWEditor build and inventory automation | Succeeded; `InventoryVerification.log` records `StackingAndWeight` Success and exit code 0 |
| 2026-10-05 | Repaired panel in local Play mode | Verified visible empty panel, Slots 0/24, Weight 0.0/50.0 kg, I close/reopen, walking input and mouse camera rotation after closing. Logs confirm cursor true/false and GameAndUI/GameOnly capture transitions |
| 2026-10-05 | Historical chat / integrated Bible / source / GitHub cross-reference | Reconciled prologue, progression, map/hotbar, rejuvenation, multiplayer and known gaps. Remote main read at `9b7f129`; `286f8d0` is local. No remote push |
| 2026-10-05 | Owner-approved publication after cross-reference | Rechecked clean tree, pending changes and remote main at `9b7f129`; ordinary push of `286f8d0` and reconciliation `41ee3fc` succeeded. Verification boundaries remain unchanged |
| 2026-10-05 | M2 collision/clearance acceptance on 5.8.3 | Build and four automation tests pass; eight animation/camera and sixteen single-player clearance checkpoints pass; sixteen client/host clearance checkpoints pass with 100 ms outgoing lag/1% loss; eleven stance/sprint/simulated-proxy checkpoints pass. [Scope and evidence](VERIFICATION.md#m2-collision) |
| 2026-10-05 | M5D pickup acceptance | Build and five automation tests pass; five single-player and five host/client pickup checkpoints pass, including packet emulation and competing intents; actual E collection and I populated panel inspected. [Scope and evidence](VERIFICATION.md#m5d-pickups) |
| 2026-10-05 | M5E selection/details acceptance | Build and existing five regression tests pass; 19 single-player and 19 replicated client UI checkpoints pass; mouse/details and full-list layout inspected; movement and pawn absence/rebinding probed. [Scope and evidence](VERIFICATION.md#m5e-selection) |
| 2026-10-05 | M5F equipment transfer acceptance | Build and seven regression tests pass; 12 standalone and 12 client equipment checkpoints pass, including full-capacity rejection, swaps, replay safety and carried-weight conservation. [Scope and evidence](VERIFICATION.md#m5f-equipment) |
| 2026-10-05 | Owner-requested M5 acceptance recheck before advancing | Fresh build and seven automation tests pass; equipment/selection/pickup rerun standalone and network plus 100-intent equipment probe: 74 Play checkpoints pass. No gameplay fix required; M5G remains Planned at that checkpoint. [Recheck record](VERIFICATION.md#m5f-acceptance) |
| 2026-10-06 | M5G hotbar foundation and snag review | Build and eight automation tests pass; 42 standalone and 42 client hotbar checks plus 19 selection/12 equipment regressions pass. Review fixes engine-flush modifier reset and narrow-window layout; mouse assignment/clear/focus and rebuilt client HUD inspected. [Evidence and limits](VERIFICATION.md#m5g-hotbar) |
| 2026-10-06 | M4 survival HUD return | Final build and nine automation tests pass; 20 standalone/20 client HUD checks plus 42 network hotbar regressions pass. Real sprint exhaustion/1.5-second notices, needs warnings, weight and possession changes verified; final HUD inspected. Walking recovery confirmed by owner; full survival rates/effects remain open. [Evidence](VERIFICATION.md#m4-hud) |

Generated logs are local evidence, not tracked artifacts. Historical handoff play claims are not fresh verification. M5B verification applies to the empty local draft; M5C adds the populated checks below. Full gameplay and multiplayer remain pending.

M5C adds populated local verification: 251 -> stacks 250/1, live increment to 252 -> 250/2, weight 25.1 -> 25.2 kg, zero/negative rejection, I close/reopen, and fresh Play empty. Both inventory automation tests succeeded. Full gameplay, packaging and multiplayer remain pending.

<a id="m2-stance"></a>

## M2 stance animation configuration — 2026-10-05

Active project: `C:\UnrealProjects\EW`. Unreal **5.8.3**, changelist 58210709. Owner directed a return to M2 after M5C; M5D remains pending.

This records the initial animation slice published in `19c573c`. Subsequent collision, camera callback and movement-replication changes are recorded in the [collision pass](VERIFICATION.md#m2-collision).

### Implementation

- Free Animation Library's 164 files were found in the older OneDrive backup and copied into active `Content/FreeAnimationLibrary`. The backup was neither launched nor modified.
- Library and character mannequin skeletons have matching bone names, parent hierarchy and reference transforms; compatibility is explicitly saved. No character scaling or skeleton substitution is used.
- `ABP_EWLocomotion` retains template standing/running/jumping and adds crouch/prone blend spaces driven by the actual character's crouch and replicated prone state. Each has twelve samples: three idle points and eight movement directions plus a backward seam duplicate. Crossfades are 0.2 seconds.
- Eighteen private animation copies under `Content/Elitewake/Animations/Stances` lock the root to the reference pose. Imported movement clips otherwise translate their root during loops; CharacterMovement must own displacement. Imported animation clips remain unchanged.
- Standing foot-placement IK is bypassed for prone; crouch retains foot placement.
- Fixed prone-to-crouch tap by preserving the existing crouch request when clearing prone. Sprint/jump still explicitly request standing.
- First-person prone eye height targets 40 cm above the capsule bottom. Its calculation uses the requested crouch size because stance callbacks can precede capsule resizing.
- `EWEditor` provides native blend-space compilation and Play verification access; it is an Editor module, excluded from game targets. `Scripts/Setup/configure_stance_animations.py` revalidates assets without duplicating an existing configured graph.

### Verification

- Final EWEditor Win64 Development build succeeds on 5.8.3; source uses the supported `GetCrouchedHalfHeight()` getter.
- `Elitewake.Animation.StanceBlendSpaces` passes after reloading saved assets: matching skeleton hierarchy/reference transforms, persisted compatibility, twelve samples per blend space, normalized runtime weights at nine directions and three speeds, and locked animation roots.
- Both existing inventory tests pass: `PersistedTestItem` and `StackingAndWeight`. Final regression log: `Saved/Logs/M2ReleaseRegression.log`.
- `Scripts/Verification/verify_stance_play.py` injects normal Enhanced Input actions and checks tap crouch, walking at 300 cm/s, hold prone, crawling at 150 cm/s, both return transitions, mesh scale, root alignment and first-person prone eye height. Results: `Saved/M2StancePlayResult.json`.
- Final Play result is **success** with eight checkpoints: crouch walking 300 cm/s, prone crawling 150 cm/s, root displacement 0 cm, unchanged unit mesh scale, and first-person prone eye height exactly 40 cm. Log: `Saved/Logs/M2AcceptedPlay.log`. Earlier eye-height/transition failures were corrected and retested.
- `Scripts/Verification/verify_stance_network_play.py` identifies the client by replicated PlayerId, not local actor names. In a listen-server/one-client session, client inputs and animation state matched on client and authoritative host for crouch, prone and both return transitions. `Saved/M2StanceNetworkResult.json` records success. Inputs are released afterward; the editor is returned to single-player Play for owner inspection.
- Logs/results/screenshots under Saved are local evidence. Earlier failed probes remain in logs; only final successful results establish verification.

### Remaining boundaries

- The initial animation slice used a shared 90/40 cm standing/crouched capsule. The subsequent [collision pass](VERIFICATION.md#m2-collision) replaces this with distinct stance sizes and a prone body movement query; its obstacle, slope and packet-emulation evidence supersedes those initial collision/latency gaps.
- Dedicated servers and production multiplayer remain unverified; local packet-emulation coverage is bounded by the collision-pass record.
- Imported stand-to-prone/prone-to-stand clips are available but are not connected as authored actions; this slice uses responsive crossfades. Final animation polish remains later work.
- Controller B retains its existing shared stance mapping; physical gamepad testing remains pending.
- Packaging and full game acceptance are not claimed. Animation and collision foundations are configured and tested within the linked records; final presentation/controller coverage remains open.

<a id="m2-collision"></a>

## M2 collision and clearance — 2026-10-05

Active project: `C:\UnrealProjects\EW`, Unreal 5.8.3. This continues the [stance animation pass](VERIFICATION.md#m2-stance) under the owner's request to finish M2 collision/clearance. M5D remains pending.

### Accepted behavior

`UEWCharacterMovementComponent` checks clearance before changing the accepted stance. Standing uses the active Blueprint's 90 cm capsule half height; crouch uses 60 cm. Prone uses a 28 cm radius/half-height root sphere and a horizontal capsule query with 28 cm radius and 105 cm half length. Its body query has a 2 cm floor skin and follows the supporting floor normal. These are implementation tuning values, not new Bible rules or character scaling.

- Low ceilings block crouch-to-stand, prone-to-crouch, and prone sprint/jump exits. Rejection preserves the existing collider, animation stance and speed. Removing an obstacle permits a new exit request.
- Prone entry checks the space around the body, including obstacles outside the standing root capsule. Swept movement checks the body; intermediate orientations check turn clearance. Prone stepping is disabled so crawling cannot use a standing step-up to bypass an obstacle.
- Capsule resizing preserves its bottom and updates the mesh's normal crouch offsets. Standing radius is restored when leaving prone. The first-person eye targets remain 40 cm above the capsule bottom in prone and 96 cm in crouch.
- Prone intent travels in CharacterMovement saved moves/compressed flags rather than a separate prone RPC. Sprint-held intent accompanies stance movement so the server accepts sprint after a successful exit. Jump clearance resolves before jump processing on the owner and server; a one-frame jump press no longer gets consumed by deferred uncrouching.
- Simulated proxies follow replicated accepted stance rather than applying absent local input intent. Their collision size updates when the host changes between prone, crouch and standing.
- Airborne prone entry is rejected. An already-prone character retains its collider while falling rather than expanding it midair.

### Verification

- EWEditor Win64 Development build succeeded on 5.8.3.
- All four automation tests passed: `Elitewake.Animation.StanceBlendSpaces`, `Elitewake.Inventory.PersistedTestItem`, `Elitewake.Inventory.StackingAndWeight`, and `Elitewake.Movement.StanceCollision`. The new test checks real blocking geometry, stance sizes, preserved capsule bottom, body movement/turn clearance, airborne entry, movement flags, and prone entry/sweep on a 10-degree inclined surface. Log: `Saved/Logs/M2CollisionRegression.log`.
- `Scripts/Verification/verify_stance_play.py` passes eight animation/camera checkpoints in a temporary clear area: crouch 300 cm/s, crawl 150 cm/s, unit mesh scale, aligned animation roots, both return transitions and prone eye target 40 cm. `Saved/M2StancePlayResult.json` records success.
- `Scripts/Verification/verify_stance_clearance_play.py` passes sixteen single-player checkpoints, including blocked rises, blocked prone entry, crawling under a 65 cm roof, body stopping at a wall, turn rejection, open crawl, sprint exit, prone jump and landing. `Saved/M2ClearancePlayResult.json` records success.
- The same obstacle course passes from a client with **100 ms outgoing packet lag and 1% packet loss on both PIE drivers**. Client and authoritative host agree on accepted stance/collider at all sixteen checkpoints. This is configured packet emulation, not a measured internet round-trip time. `Saved/M2ClearanceNetworkResult.json` records success.
- `Scripts/Verification/verify_stance_network_play.py` passes eleven client/host checkpoints, including client sprint exit and host stance changes observed by a simulated proxy. Stance/collider/animation flags agree; settled animation roots remain 1 cm above their capsule bottoms in both representations. `Saved/M2StanceNetworkResult.json` records success.

The fixtures exist only in Play worlds; scripts release injected input, remove fixtures, unregister callbacks and restore throttling/network settings. Generated logs/results stay under ignored `Saved`. Earlier failures remain as diagnostic history; only the final successful runs establish acceptance. The animation-only speed route was moved to clear space after the new body guard correctly encountered an obstacle in the template map.

### Scope and remaining work

The collision/clearance foundation is verified for the fixtures above. The horizontal body query is a movement-clearance approximation, not skeletal damage hitboxes. Other actors are tested against their existing blocking geometry. Teleports/network corrections use normal engine placement; the body guard applies to swept locomotion and turning.

Physical controller B testing, authored transition polish and terrain-aligned animation remain open. The slope check is one planar 10-degree fixture; complex terrain edges, moving ship decks, dedicated servers, broader latency/loss conditions, performance and packaging are not established by this pass. No full-game or finished-M2-presentation claim is made.

<a id="m4-hud"></a>

## M4 survival HUD return slice

Reviewed 2026-10-06, active `C:\UnrealProjects\EW`, Unreal 5.8.3.

### Scope

The local controller creates a read-only survival HUD above the existing hotbar. Five labeled gauges show health/current maximum, stamina/current maximum, normalized food and hydration percentages, and inventory-plus-equipment carried weight/current prototype capacity. The widget reads only its possessed character's survival component, clears stale information while unpossessed, and resumes with current values on possession. It does not intercept gameplay input or mutate stats. Inventory still overlays the HUD and the world stays live.

Bible §§5.6 and 30.15 supply the presentation requirements. Empty food blinks red, hydration yellow and stamina white. Their top-center messages are “You are hungry!”, “You are thirsty!” and “You are out of stamina!” for 1.5 seconds on a new empty transition. Independent warnings can coexist. Warning duration continues during replenishment/recovery; persistent empty values keep blinking without repeating the notice every frame. Blink period is draft presentation tuning.

This slice displays existing gameplay truth. It does not implement 15-minute needs drain, starvation/dehydration damage, food/drinking, jump/climb costs, five-second stamina tuning, natural health regeneration, fall damage or condition/ship HUD systems. Food is currently a normalized 0–100 percentage, not the Bible's upgradeable 75-point base capacity. The displayed 50 kg carry capacity remains a prototype value and does not imply an enforced hard cap or encumbrance penalty.

Direct owner clarification on October 6: stamina recovery should also occur while walking. This supersedes the stationary-only recovery description for the next gameplay pass; the existing walking recovery already behaves that way. Capacity scaling and needs-damage tuning remain separate decisions.

### Verification

- Final EWEditor Win64 Development build succeeds. `Saved/Logs/M4HUDFinalRegression.log` records nine successful automation tests: the eight existing animation/stance/inventory/pickup/equipment/hotbar checks and new `Elitewake.Survival.ExhaustionNotification`.
- ExhaustionNotification proves that partial drain emits no exhaustion, the first empty transition emits once, remaining empty does not replay it, the marker survives recovery before replication and a later exhaustion emits a new marker. The marker is authority-produced, owner-only replicated and does not alter survival rates. It prevents the owning HUD from missing an intermediate zero stamina value when replication arrives after recovery begins.
- `Scripts/Verification/verify_survival_hud_play.py` passes 20 standalone and 20 owning-client checkpoints on the final build. These read the rendered widget labels after authority changes, including damage/restore, food/hydration values, independent and simultaneous warnings, warning expiry/retrigger, inventory-plus-equipment weight, inventory overlay/input lock, above-capacity display and same-pawn unpossession/repossession. The other survivor stays unchanged.
- Real Shift input drains stamina through the existing gameplay loop and produces the exhaustion warning. Measured notice duration is approximately 1.50 seconds standalone and 1.51 seconds on the client, continuing through automatic recovery. This verifies presentation at the existing rates, not the future five-second rate tuning.
- Network Play uses a local listen server and client with 100 ms outgoing packet lag and 1% loss on both drivers. `Saved/M4HUDPlayResult.json` and `Saved/M4HUDNetworkResult.json` retain results. The possession probe can emit movement saved-move/timestamp warnings during the temporary detach under packet emulation; it is not full respawn or moving-deck validation.
- All 42 existing network hotbar checkpoints pass with the survival HUD visible, including keyboard/controller chords, ordinary gameplay roles, inventory assignment and focus reset. Final standalone and client screenshots confirm readable gauges above the hotbar; simultaneous red food/yellow hydration notices appear at top center without overlap.

The verification script restores packet/throttle/input/panel settings and removes its callback. Saved Wood/Hat fixtures remain opt-in and no production assets/default grants are changed. Logs, reports and screenshots are local evidence rather than tracked assets.

### Remaining gates

Final HUD art, controller hardware, packaged/dedicated-server checks, complete survival gameplay and condition/interaction/ship displays remain open. M4 is partially implemented; this presentation slice does not mark the whole milestone complete.

<a id="m5c-inventory"></a>

## M5C persisted inventory fixture

Verified October 5, 2026 in `C:\UnrealProjects\EW`, Unreal Engine 5.8.2. This slice adds real saved item content and an opt-in editor grant to verify the existing native inventory panel. It does not implement pickups, equipment, hotbar, save/load, production wood balance or multiplayer acceptance.

### Content and developer use

- Asset: `/Game/Elitewake/Items/Testing/DA_TestWood`, stable primary ID `EWItem:Test.Wood`.
- Display name: Wood (Test). Resource stack size 250 follows October Bible §30.17.
- Unit weight 0.1 kg is temporary fixture tuning. Ash/Oak/Birch gameplay definitions, icons and production weights remain pending.
- The asset is a native `UEWItemDefinition`, created and saved through Unreal-supported APIs. `Scripts/Setup/create_inventory_test_asset.py` preserves an existing asset rather than overwriting designer edits.
- `DefaultGame.ini` registers the EWItem scan under `/Game/Elitewake/Items`. It also supplies the required GameFeatureData scan/rule, resolving the existing startup configuration error.
- During Play, open the developer console and run `EWGrantTestWood 251`, then open inventory with I. Running `EWGrantTestWood 1` while the panel is open should refresh its counts/weight immediately.
- The command requires authority and positive quantity, has no client RPC, and its implementation is compiled only for editor builds. It never grants startup items. Inventory accepts only what fits its slots; displayed weight capacity is not yet enforced.
- To regenerate a missing fixture, run the editor PythonScript commandlet with `-EnablePlugins=PythonScriptPlugin -run=PythonScript -Script=<absolute path to Scripts/Setup/create_inventory_test_asset.py>`. Python is enabled for that invocation; no permanent project plugin addition is needed.

### Evidence

| Check | Result |
| --- | --- |
| EWEditor Win64 Development build | Succeeded after correcting a compiler-detected controller variable-name conflict |
| Supported asset creation | Saved .uasset; later idempotent commandlet run preserved it, exit 0, zero errors |
| `Elitewake.Inventory.StackingAndWeight` | Success |
| `Elitewake.Inventory.PersistedTestItem` | Success: asset-manager discovery and load, stable ID, 250 stack boundary, 251 split, weight synchronization, partial acceptance at full 24-slot capacity, excess rejection, removal and weight cleanup |
| Normal Play before granting | Empty inventory; Python assertions on used slots and screenshot inspection |
| Explicit controller grant 251 | Log: requested=251 added=251 total=251 slots=2 weight=25.1 kg; assertions match |
| Rendered panel through normal I input | Visible Wood (Test) x250 at 25.0 kg and x1 at 0.1 kg; Slots 2/24, total 25.1/50.0 kg |
| Grant 1 with panel already open | Visible second stack x2, total 25.2 kg; assertions confirm 252 items |
| Grant 0 and -1 | Rejected; quantity stays 252 |
| I close/reopen populated panel | Visually verified removal and correct returning 250/2 stacks |
| Stop/restart Play | Fresh session again Slots 0/24, Weight 0.0/50.0 kg, Inventory is empty |

Local evidence is ignored generated output: `Saved/Logs/M5CAssetCreation.log`, `M5CInventoryVerification.log`, `M5CPlayVerification.log`; screenshots `Saved/M5CPopulated.png`, `M5CLiveRefresh.png`, `M5CClosed.png`, `M5CReopened.png`, `M5CFreshEmpty.png`. Earlier Python verification-harness reflection errors remain in the Play log; the subsequent controller grant, assertions and actual I-driven visual checks succeeded. Do not mistake the early harness failures for a final gameplay failure.

### Remaining gates

Package/cook validation and multi-client item reference replication are pending. Controller Y/navigation, final UI layout/icons, long-list scrolling, item condition/rarity data, weight penalties, equipment and hotbar are not completed by this fixture. Next slice is server-validated pickup/interaction, preserving no-duplication and partial-capacity rules.

<a id="m5d-pickups"></a>

## M5D pickup verification

Verified 2026-10-05 in `C:\UnrealProjects\EW`, Unreal 5.8.3. Slice commit: `Implement M5D authoritative world pickups`.

### Behavior

`EWPickup.*` supplies a replicated world stack and Blueprint-configurable mesh/item/quantity. `EWPlayerController.*` binds the Enhanced Input interaction draft to E and controller X. An assigned designer action replaces the runtime fallback and needs a mapping in the controller's mapping contexts. Interaction is suppressed locally while inventory is open.

The owned player controller sends a target actor only. The server uses its possessed character's eye position/control rotation to trace 250 cm on Visibility, and verifies the same target, world, possession, authority, usable item/quantity and any assigned pickup owner. Walls and looking away block interaction. Public pickups have no owner; an assigned owner must be the collecting character or its controller. This is a pickup access check, not a general ownership/tribe system.

Inventory accepts only what fits its slots/stacks. The world quantity decreases by that accepted count, remains when capacity is insufficient, and destroys the actor only when exhausted. Server operations run serially; a transfer guard also rejects reentrant attempts during inventory change notifications. Clients cannot supply item definitions, quantities or receiving inventories through the interaction RPC.

E and 250 cm are draft tuning, not newly confirmed Bible rules. Controller X follows the authoritative Bible. Preserve zero starting currency and the later rye-sale mission; this slice adds no currency or prologue behavior.

### Evidence

- EWEditor Win64 Development build succeeded, including the editor-only fixture helper.
- `Saved/Logs/M5DRegression.log`: all five tests Success: StanceBlendSpaces, PersistedTestItem, PickupValidation, StackingAndWeight, StanceCollision.
- PickupValidation checks possession, distance, aim, occlusion, foreign ownership, partial/full capacity, exhaustion, repeated intent and count conservation using real collision queries.
- `Saved/M5DPickupPlayResult.json`: five checkpoints pass through the real Enhanced Input action binding in fresh single-player Play.
- `Saved/M5DPickupNetworkResult.json`: five checkpoints pass in listen-server/client Play with 100 ms outgoing lag and 1% loss on both drivers. Both local players send overlapping pickup intents; the original 10 units transfer exactly once. Each inventory with three free units receives three from a later stack, leaving four replicated units. Full inventories preserve that remainder; freeing capacity collects it once. Inventory quantities and world remainders agree in both worlds.
- `Saved/M5DPickupInventory.png`: actual Slate E key collects the placed Blueprint's 10 Wood (Test); I displays Slots 1/24, Wood x10, weight 1.0 kg. Normal Play begins empty before collection.
- `BP_TestWoodPickup` and `Lvl_M5PickupTest` are saved under `/Game/Elitewake/Blueprints` and `/Game/Elitewake/Maps`. The original startup map is unchanged. The map reloads and the placed actor enters Play with the saved item and quantity 10. Face forward from PlayerStart, press E, then I to inspect the inventory.

`Scripts/Setup/create_pickup_test_content.py` creates/reconciles only the named fixture content. `Scripts/Verification/verify_pickup_play.py` requires that test map in fresh single-player or in-process listen-server/client Play. It clears PIE test inventory, creates temporary stacks, restores packet/throttle settings, removes its callbacks and fixtures on success/failure/Play exit. Stop Play afterward; no inventory is saved. The spawn helper belongs to EWEditor and is not available in game targets. Earlier failed Python spawning/path/content probes are diagnostic only, superseded by the successful records above.

### Boundaries

This is the M5D pickup foundation, not a complete interaction framework for stations, gathering, vendors, loot permissions, ships or hold actions. The eye/control-rotation ray is the accepted aiming convention for this slice; third-person camera-parallax polish, reticle/prompts/feedback and inventory selection follow in presentation work. Controller X is mapped but physical controller testing remains open. Wood's cube and 0.1 kg weight are fixtures. Slot capacity, not a hard weight cap, limits transfer. Dedicated server, packaging, persistence, death drops, moving ships, broader latency/load tests and complete multiplayer inventory UI are not verified.

<a id="m5e-selection"></a>

## M5E inventory selection verification

Reviewed 2026-10-05 in `C:\UnrealProjects\EW`, Unreal 5.8.3. Slice commit: `Implement M5E inventory selection and navigation`.

### Behavior and scope

The native inventory draft now selects the first valid stack on opening, highlights the selection, and supports Up/Down, controller D-pad/left stick, and mouse hover/click. Enter/controller A/click confirms the selected stack and shows its description, quantity, unit weight and stack limit. Confirmation is read-only; equipping and item use belong to later slices.

I and controller Y open the panel through Enhanced Input. I/Y/B/Escape close it from the focused UI. Inventory owns keyboard/controller input while open; movement/look input is ignored and pressed gameplay keys are flushed. Closing restores the controller's matching input locks and normal game focus. The world continues running. Designer-assigned inventory input actions require their own mapping contexts; full user remapping is not implemented by these draft UI keys.

The list scrolls to keep selection visible. Opening details also requests scrolling because the details reduce the list height. Refresh preserves item definition plus stack occurrence where possible, otherwise clamps to a valid row. These are local display positions, not persistent stack IDs. Empty/unavailable inventory clears selection and details. The widget rebinds when its owning pawn's inventory changes. Summary reads current survival capacity while visible; changing capacity through an approved gameplay API remains unverified.

Left-stick dead zone 0.5, initial repeat delay 0.35 seconds and repeat interval 0.18 seconds are draft UI tuning, not additional Bible rules. List boundaries clamp without wrapping. Controller Y, automatic first focus, visible selection and controller navigation implement the relevant §§5.8/25.4 foundation; character preview, tabs, equipment and art remain separate gates.

### Verification

- EWEditor Win64 Development builds succeeded, including the final selected-row layout fix and explicit SlateCore dependency.
- `Saved/Logs/M5ERegression.log`: all five existing automation tests Success (StanceBlendSpaces, PersistedTestItem, PickupValidation, StackingAndWeight, StanceCollision). The later layout-only fix does not change their gameplay scope.
- `Saved/M5ESelectionPlayResult.json`: 19 checkpoints pass through real Slate keyboard/gamepad key/analog events, routed into the focused Play UI. Empty navigation, I/Y open/close, first selection, arrows/D-pad, Enter/A confirmation, stick dead zone/repeat, B/Escape cancellation, removed-stack clamp, live details refresh and empty-to-populated transitions are covered. Input locks and focus are checked at each stage.
- `Saved/M5ESelectionNetworkResult.json`: the same 19 checkpoints pass from the client of an in-process listen-server/client session, with 100 ms outgoing lag and 1% loss on both drivers. Authority inventory changes replicate into the selected client panel without invalid selection.
- Mouse hover/click on the second stack visibly changes highlight and confirms details; `Saved/M5EMouseDetails.png` records it.
- Follow-up Play checks cover actual movement recovery, movement blocking while open, unpossessed view clearing, repossession rebinding and full 24-slot selection. `Saved/M5EFollowupResult.json` and `Saved/M5EFullListDetails.png` record the final checks.

`Scripts/Verification/verify_inventory_selection_play.py` runs in fresh single-player or in-process listen-server/client Play. Its state is isolated in a function closure, it uses only the existing Wood fixture and authority test mutations, and it restores UI/input focus, packet/throttle settings and callback registration on success/failure/Play exit. Test inventory lives only in PIE; stop Play afterward. Editor-only Slate injection helpers are excluded from game targets. No production item content or default starting inventory was added.

Earlier probes encountered Python reflection restrictions and an editor crash whose stack was in PythonScriptPlugin/python311; they are retained as diagnostics and are not acceptance evidence. The project was reopened and the selection verifier rerun with isolated Python state. The additional probe was separated from attempted editor property changes. No root cause or long-duration stability claim is made from the crash stack alone.

### Remaining gates

Physical controller hardware and real device-switching, remapping/options, LB/RB tabs, character preview/final art, arbitrary long descriptions, world pickup prompts/reticle/feedback, general item operations, equipment/hotbar, new-pawn respawn flows, packaging, dedicated servers and broad performance/load tests remain unverified or planned. Pawn absence/rebinding was tested by unpossessing/repossessing the same actor, not a complete respawn system. Inventory slots still enforce capacity; a hard weight cap and encumbrance are not implemented.

<a id="m5f-equipment"></a>

## M5F equipment transfer verification

Reviewed 2026-10-05 in `C:\UnrealProjects\EW`, Unreal 5.8.3. Slice commit: `Implement M5F authoritative equipment transfers`.

### Behavior and design scope

The character now owns a replicated equipment component. Each occupied slot holds one unit of an item definition. Requests travel through the player's owned controller; the server resolves its possessed character, checks ownership and exact item-slot compatibility, and performs the transfer. None/invalid slots and non-equippable resources are rejected. The five Bible body slots remain Head, Chest, Hands, Legs and Feet; existing MainHand/OffHand metadata is supported without adding weapon behavior.

Equip removes one inventory unit. Replacing occupied gear first plans returning the previous unit to inventory, including the slot freed by consuming the incoming item. If the return cannot fit, the whole operation is rejected. Unequip similarly leaves gear equipped when inventory is full. Both containers commit before authority weight recalculation and events, and transfer guards reject reentrant mutations. Replayed requests cannot create extra units. Inventory plus equipment weight contributes to survival carried weight; equipping does not shed weight. Capacity is still 24 inventory slots, without a hard weight cap.

The scrolling inventory lists occupied equipment after stored stacks. Enter/A/click opens details; R/controller X or the visible Equip/Unequip button performs the selected action. These action bindings are draft UI choices. Equipped slot rows, total carried weight and server result messages update in the local panel. A full-inventory message explains why gear remains equipped. The mouse button preserves panel focus for subsequent keyboard/stick navigation. Cosmetics, meshes, armor protection, durability, item instances, persistence, item use and the eight-slot hotbar are separate gates.

`DA_TestHat` and `DA_TestHatAlternate` are opt-in Head-slot fixtures with stable IDs `Test.Hat` and `Test.HatAlternate`, stack one and temporary weights 2/3 kg. `Scripts/Setup/create_equipment_test_assets.py` preserves existing assets. No grant is added to normal Play, and no production item/map/story content changes in this slice.

### Verification

- EWEditor Win64 Development build succeeds. `Saved/Logs/M5FFinalRegression.log` records seven successful automation tests: StanceBlendSpaces, EquipmentTransfer, PersistedEquipmentFixtures, PersistedTestItem, PickupValidation, StackingAndWeight and StanceCollision.
- EquipmentTransfer covers authority/null/ownership/slot rejection, single-unit consumption, occupied-slot swaps, full-inventory rejection, a blocked swap whose source stack does not free space, restoration after freeing capacity, returning into a partial stack, repeated requests and carried-weight conservation.
- PersistedEquipmentFixtures discovers and loads both saved hats by their stable primary IDs in a fresh engine process. Initial asset creation emitted stale registration-ID diagnostics before the configured IDs were saved; fresh-process discovery succeeds.
- `Saved/M5FEquipmentPlayResult.json`: 12 standalone checkpoints pass through focused Slate keys, owned-controller intent and authority fixture grants.
- `Saved/M5FEquipmentNetworkResult.json`: 12 client checkpoints pass in an in-process listen-server/client session with 100 ms outgoing lag and 1% loss on both drivers. Server/client item counts, equipped definition, composite weight and survival carried weight agree. The other player's inventory/equipment remains unchanged; direct client mutation is rejected.
- Existing M5E selection and M5D pickup network scripts were rerun in fresh sessions after M5F: 19 selection and five pickup checkpoints pass.
- Actual mouse Equip/Unequip clicks, subsequent keyboard navigation/confirmation and the full-inventory feedback are inspected in Play. `Saved/M5FMouseEquip.png`, `Saved/M5FMouseUnequipFocus.png` and `Saved/M5FFullInventoryFeedback.png` record the layout. A console inspection steals UI focus, so its recorded focus flag is not mouse-focus acceptance evidence; navigation immediately after the button click verifies preserved input.

The initial scripted network runs were not acceptance evidence: Unreal's editor scripting guard forced actor RPCs to execute locally, where authority checks rejected them. Actual native Slate input successfully equipped on the server. The editor-only verifier now scopes that scripting bypass off during normal input/owned-controller requests and restores it immediately; gameplay authority remains unchanged. The successful network run uses this corrected helper. Test reports/scripts retain failure information and are isolated from other Python execution.

`Scripts/Verification/verify_equipment_play.py` runs only in fresh PIE, restores panel, throttle and packet settings, and removes its callback on completion/failure/Play exit. Grants are confined to PIE. Stop Play after testing. The helpers live in EWEditor and are excluded from game targets.

### Remaining gates

Physical controller/device switching, polished equipment presentation, protective stats, durability, per-instance identity/save/load, death/logout drops, packaging, dedicated servers and broader network/load coverage remain unverified. M5G hotbar is next; M4 survival/HUD work remains open. The rye/currency/prologue requirements and core ship-home design are unchanged.

<a id="m5f-acceptance"></a>

### Owner-requested acceptance recheck

On 2026-10-05, after publication of `f2d32d4`, the owner requested confirmation before moving on. A fresh editor build succeeded and all seven automated tests passed in `Saved/Logs/M5FAcceptanceRegression.log`. A fresh editor process reran equipment, selection and pickup scripts in separate standalone and listen-server/client sessions: 12 + 19 + 5 checkpoints passed in each mode. Multiplayer used 100 ms outgoing lag and 1% loss on both drivers. `Saved/Logs/M5FAcceptancePlay.log` contains no Error, ensure or fatal entries from this pass.

The additional `Scripts/Verification/verify_equipment_network_stress.py` sent 60 alternating equip and 40 repeated unequip intents across the two owned controllers in fresh two-player PIE. Its two checkpoints verified both players in both worlds, covering authority, owning-client and observing-client copies. All eight recorded character states retained correct inventory/equipment quantities and 5.1 kg composite/survival weight per player. This is a bounded local regression probe, not a production load test. Packet/throttle settings and its callback were restored/removed on completion.

`Saved/M5FAcceptanceSummary.json` indexes the seven fresh Play reports, totaling 74 successful checkpoints. No gameplay fix was required. Play is stopped, single-player settings restored, and the editor observer removed. The existing `Config/DefaultEditor.ini` owner change remains untouched and excluded from publication. Remaining gates above still apply; this recheck does not begin M5G or certify the full game.

<a id="m5g-hotbar"></a>

## M5G hotbar foundation verification

Reviewed 2026-10-06 in `C:\UnrealProjects\EW`, Unreal 5.8.3. Slice: `Implement M5G owned hotbar shortcuts`.

### Behavior and design scope

The owning player has a permanent eight-slot bottom-center draft HUD. Bindings reference owned item definitions; they are not extra storage and do not change quantities or carried weight. Each definition has one shortcut, so reassignment moves it. The server resolves the requesting controller's own possessed character and validates ownership and slot indices. Bindings and selected slot replicate only to that owner.

Inventory details expose eight assignment buttons. Keyboard 1–8 or LB combinations assign the selected item while details are open; selecting its existing binding clears it. Outside inventory these shortcuts select the slot and request its implemented action. Equipable definitions use the existing M5F atomic equipment transfer and full-inventory return rules. Repeated activation of already-worn gear does not consume another unit. Empty, unavailable and unsupported actions produce feedback without changing item quantities. Unavailable bindings remain and become usable again when the item is replenished.

Bible §5.9 confirms 1–8 and the LB modifier concept. Exact draft controller order is LB+A/B/X/Y for slots 1–4 and LB+D-pad Up/Right/Down/Left for 5–8. This order is implementation tuning, not a new authoritative design rule. The complete chord is consumed before ordinary gameplay input, including a face-button release after LB releases first. Engine key flushing also clears custom modifier state. Without LB, ordinary A jump, B stance/close, X pickup/equipment and Y inventory roles remain available.

The old permanent inventory control-hint panel is removed in accordance with §5.8; contextual assignment buttons replace it. HUD names are shortened for the draft layout. No normal-player grants, production assets or story/economy changes are introduced.

### Verification

- EWEditor Win64 Development builds successfully. `Saved/Logs/M5GFinalRegression.log` records eight successful automation tests, including new `Elitewake.Inventory.HotbarOwnershipAndActivation` and all seven previous stance/inventory/pickup/equipment regressions.
- The hotbar automation covers authority, invalid indices, unowned definitions, reference-only assignment, unique bindings, worn availability, safe replay, equipment swaps, blocked full-inventory returns, resources without consumption, retained unavailable bindings, replenishment and clearing.
- `Scripts/Verification/verify_hotbar_play.py` passes 42 standalone and 42 owning-client checkpoints. Client requests use ordinary Slate input/controller RPC routing, with 100 ms outgoing packet lag and 1% loss on the local listen-server/client drivers. Host and owner agree on bindings, selected slot, equipment, inventory quantities and weight; the other player's inventory and equipment remain unchanged.
- The Play runs cover all eight keyboard activation keys, all eight controller combinations in both inventory and world, assignment/move/clear, equipment activation/replay/swaps, empty/unsupported/unavailable/replenished shortcuts, release ordering, normal Y/B/X/A roles and engine input flushing while LB is held. The last check proves normal Y opens inventory after the flush.
- The existing network selection and equipment scripts pass all 19 and 12 checkpoints with the modified inventory widget.
- Mouse assignment moves the selected definition to slot four, a second click clears it, and immediate Down/Enter still selects and opens the next item's details. Inventory quantity and 6.1 kg fixture weight remain unchanged. `Saved/M5GMouseResult.json` records the probe. The final taller HUD was rebuilt and visually inspected to accommodate wrapped names and quantities in small Play windows.

Local reports are `Saved/M5GHotbarPlayResult.json`, `Saved/M5GHotbarNetworkResult.json`, `Saved/M5ESelectionNetworkResult.json` and `Saved/M5FEquipmentNetworkResult.json`. Generated reports, logs and screenshots are evidence retained locally, not tracked assets. The 84 hotbar and 31 existing regression checkpoints precede the final HUD-height-only adjustment; the rebuilt layout is checked visually afterward.

### Remaining gates

This verifies the hotbar foundation and equipment shortcut action. Consumables, weapon drawing, treasure maps, taming and underwater-only harpoon restrictions require their actual item-action systems; resources currently bind safely but do not consume or execute an invented action. Map-open input suppression must be integrated when the map exists. Save/load, death/respawn policy, per-instance durability/identity, remappable bindings, physical controller hardware, packaged/dedicated-server testing and final artwork remain open. M4 survival/HUD work remains independently incomplete.

<a id="repository-cleanup"></a>

## Repository cleanup — October 6, 2026

The asset-registry audit found 515 packages in the unused Combat, Platforming and SideScrolling template variants, with zero outside package referencers and zero outside Blueprint parents using those native variants. A separate scan of all 432 retained tracked asset files found no references to the 58 native type names declared by those templates. No non-variant source/config/script references remained except their build include paths.

The variants are deleted through Unreal asset APIs, including their world-partition external data; their 76 source files and obsolete include paths are removed. The active ThirdPerson foundation, mannequin/input/prototyping assets, Free Animation Library, Elitewake content and saved test fixtures remain. Documentation is consolidated into three current references and one historical archive; scripts are grouped into Setup and Verification, and native runtime tests into Tests. Duplicate identical renderer/RHI configuration lines are removed.

EWEditor Win64 Development builds successfully after removal and reorganization. `Saved/Logs/RepositoryCleanupRegression.log` records all nine automation tests passing. All 12 retained Blueprint/animation/UI Blueprint assets load and compile with UpToDate status in a fresh editor process. The normal ThirdPerson startup map passes eight stance/camera checkpoints; the retained isolated pickup map passes all 42 owning-client hotbar checkpoints with 100 ms outgoing packet lag and 1% loss, including inventory/equipment/pickup and ordinary input roles.

The structure check confirms all 432 retained tracked asset files still exist, all 61 Markdown links/anchors resolve and all 13 moved scripts parse. No retained content asset was edited. Results are retained locally as `RepositoryCleanupBlueprintResult.json`, `RepositoryCleanupStructureResult.json`, `M2StancePlayResult.json` and `M5GHotbarNetworkResult.json`. Play is stopped, single-player settings restored and observer/callback cleanup completed. The unrelated owner's `Config/DefaultEditor.ini` change is excluded from the cleanup commit.

Git history is retained; this is ordinary file cleanup rather than history rewriting or LFS-object pruning. Generated local reports remain under ignored Saved/.

<a id="interaction-pickup-refactor"></a>

## October 6, 2026 — Milestone A pickup interaction checkpoint

Authorized on `milestone-a-interaction`; no main merge or remote publication. Added Blueprint-native interactable queries/action and shared 250 cm Visibility eye targeting. Pickups retain the legacy targeting wrapper for unchanged acceptance scripts and their authoritative partial-transfer/reentrancy/ownership checks. Controller requests now accept a generic actor and revalidate interface, possession, trace, eligibility and Press mode before dispatch. Hold execution and prompt presentation are not implemented at this checkpoint.

EWEditor Win64 Development build passed. All nine existing `Elitewake` automation tests passed against the rebuilt modules (`Saved/Logs/InteractionPickupRegression.log`). The unchanged `Scripts/Verification/verify_pickup_play.py` passed five standalone and five listen/client checks: range rejection, competing transfer conservation, partial capacity, full-inventory remainder and final single collection. Network checks used 100 ms outgoing lag and 1% loss; owner inventories and world remainders agreed across worlds (`Saved/M5DPickupPlayResult.json`, `Saved/M5DPickupNetworkResult.json`, fresh October 6 evidence). This is local packet-emulated acceptance, not dedicated-server or packaged coverage.

Documentation reconciliation preserves the supplied README/DESIGN_REFERENCE edits, corrects the unincorporated October 6 Shared-guide revision claim, updates current Project Guide terminology and records Attack for tree punching. Port rule carryover remains pending. `.mcp.json` and the existing `Config/DefaultEditor.ini` change are excluded from checkpoints. Original editor preference SHA-256: `0E61E2200AEAB9EC14A2CD1C55F024F1CCAB668D1C43759D89B71DD9D7B0185A`.

<a id="interaction-foundation"></a>

## October 6, 2026 — Milestone A interaction foundation

Scope: Blueprint-native `IEWInteractable`, shared 250 cm Visibility eye targeting, owned-controller requests, local E/X prompts and authoritative Press/Hold timing. `UEWInteractionComponent` lives on the controller; one active hold retains its original pawn, target, duration and server start time. Reliable begin/cancel/menu intents on that controller preserve ordering; repeated starts do not reset holds. A 50 ms server timer revalidates life, possession, target identity, range/visibility, mode, duration and `CanInteract` before completion. Progress is owner-only replicated presentation, not permission to complete. Press admission is limited to one request per 100 ms. Completion clears hold state before calling the target, guarding reentrancy.

Release, looking away, range loss, new obstruction, inventory opening, input flush, pawn loss/change, death, unavailable/destroyed targets and losing a single-use competition cancel. Walking while aimed/in range is permitted. Native fixtures serialize single-use acknowledgement on the game thread; production targets must implement their own atomic mutation and ownership/permission checks. A client can lie about its physical button or UI state; the server validates gameplay outcomes, not hardware honesty. Inventory menu state is synchronized through the ordinary owned-controller path.

`AEWStation` (Campfire/Smithy) and `AEWResourceNode` (Tree/Rock) are opt-in Inspect fixtures only: no resources, crafting, injury or storage. No default-world actors or saved assets changed. `Scripts/Setup/spawn_interaction_play_fixtures.py` requires Play in `Lvl_M5PickupTest` and spawns transient fixtures. Draft default holds are one second; the verification script uses 1.2 seconds to sample progress/cancellation under latency. Remapping, final art, real controller hardware, shipping/package and dedicated-server coverage remain open. Trees are punched through Attack in the future gathering slice.

Final EWEditor Win64 Development build passed. All ten `Elitewake` automation tests passed (`Saved/Logs/InteractionHoldRegression.log`), including shared target types, range, through-wall/mismatched/ineligible targets, inventory blocking, retained timing, completion and cancellation. Fresh `Scripts/Verification/verify_interaction_play.py` passed **31 standalone and 31 listen/client checkpoints** (`Saved/InteractionPlayResult.json`, `Saved/InteractionNetworkResult.json`). Network drivers used 100 ms outgoing lag and 1% loss. Checkpoints include device switches through inventory, neutral controller samples, E and held X, walking, real Slate input, owner progress, rejected forged requests and exactly-one competing completion. All callbacks, fixtures, packet settings and throttling are cleaned up. Script RPC helpers explicitly disable Python's editor-local actor RPC bypass.

Initial verification-tool failures were corrected and rerun: synthetic world steps needed distinct engine frames to tick TimerManager; destroyed actors could lose their Python native wrappers before cleanup; the old input-flush helper did not disable Python's local RPC bypass. These failed runs are not acceptance. Under packet emulation the deliberate unpossess/repossess checkpoint emits saved-move/time-stamp warnings; it proves hold cancellation, not complete respawn/network-movement acceptance.

Final regression evidence: unchanged pickup script passed five standalone and five listen/client checkpoints against the final feature build. Hotbar passed all 42 listen/client checkpoints, including LB input suppression and ordinary X pickup/jump restoration (`Saved/M5GHotbarNetworkResult.json`, October 6 09:12 local). Its first rerun rejected X because the test pawn was facing away after menu mouse recapture; a state probe confirmed both server/client menu blocks were false and the pickup remained intact. The test now restores its known aim after closing UI, retaining all 42 assertions. No gameplay camera or pickup guard was weakened.

Direct viewport-input check: opt-in fixture setup, readable `E: Inspect Smithy (test)` prompt, Slate PressKey E, and exactly one Smithy acknowledgement with the other three fixture counts unchanged (`Saved/InteractionManualResult.json`, `Saved/InteractionManualBefore.png`). All fixtures were PIE-only and removed by stopping Play. The editor was left stopped in standalone test-map configuration. `Config/DefaultEditor.ini` retained its original checksum; `.mcp.json` remained untracked. At that checkpoint no main merge or remote push was performed. The owner subsequently approved continuation; main was fast-forwarded and pushed to `adc9693` on October 6.

<a id="fresh-water"></a>

## October 6, 2026 — Fresh-water interaction

`AEWWaterSource` provides a replicated, designer-sized query surface implementing the existing Press interaction. A valid fresh source instantly sets the server survivor's hydration to 100%, matching Development chapters 6/15; E/X uses the ordinary owned-controller interaction path. Standing is supported, with no prone requirement. Full hydration hides the prompt and rejects redundant use. The source remains reusable and shared: it does not consume inventory or a global water charge. Life, possession, source ownership/availability/quality, same-world identity, range and visibility are checked; direct target dispatch also rechecks authority and the eye trace. The existing interaction component rejects inventory-open requests. Salt quality is reserved and currently ineligible: it cannot grant fresh hydration; sickness and other qualities await their specified systems.

The EWEditor Win64 Development build passed. All ten `Elitewake` native tests passed in `Saved/Logs/FreshWaterRegression.log`, including new fresh-water refill/reuse, full-state, salt, unavailable/foreign-owned/distant source, menu, death and direct-dispatch aim assertions within `Elitewake.Interaction.AuthorityAndHolds`. Existing native stance, inventory, equipment, pickup, hotbar and exhaustion checks remain successful.

Final `Scripts/Verification/verify_water_play.py` passed **13 standalone and 14 listen/client checkpoints**, using 100 ms outgoing lag and 1% loss on both local network drivers. Evidence: `Saved/WaterPlayResult.json` (09:55–09:56 local) and `Saved/WaterNetworkResult.json` (09:54–09:55 local). Checks read the actual rendered hydration HUD and E/X prompt alongside server/owning-client stats; cover E refill, X refill from empty, harmless repeats, reusable source, client mutation rejection, salt/unavailable/range/wall/aim/menu/death rejection and independent shared-source use. Inventory count stays unchanged throughout. Scripts restore hydration, health, packet settings, throttling and input; remove temporary actors and callbacks.

Two initial network-fixture failures were corrected and rerun: the verification box helper is intentionally nonreplicated, so the test now places equivalent query geometry in both PIE worlds for the local hidden-prompt assertion; the shared-source test initially overlapped player capsules, so players are now separated and aim at a widened test surface. No gameplay targeting or hydration guards were relaxed. These failed runs are not acceptance.

`Scripts/Setup/spawn_water_play_fixture.py` is opt-in and PIE-only: it lowers test hydration to 25% and marks a source in blue without saving assets. The setup script was exercised successfully. Direct viewport PressKey E changed hydration **25% -> 100%**, cleared the interaction prompt, and visibly updated the HUD (`Saved/WaterManualBeforeResult.json`, `Saved/WaterManualResult.json`, `Saved/WaterManualBefore.png`, `Saved/WaterManualAfter.png`). The viewport was focused before this check; an earlier press while the console held focus did not reach gameplay. Play was stopped afterward; no test actors or callbacks remain active.

Production water geometry/content, animation/audio, salt/brackish/contaminated/carried-water effects, automatic needs drain/damage, physical controller hardware, shipping/package and dedicated-server checks remain open. This is verified fresh-water gameplay, not complete survival or a finished pond.

<a id="m6-interaction-closeout"></a>

## October 6, 2026 — M6 interaction foundation closeout

For the owner's instruction to continue the planned workflow through M6 under auto-approval, M6 uses the previously recorded interaction-framework sequence, implemented as Milestone A plus the fresh-water return slice. Gathering/crafting remains the following package. Completion applies to this foundation, not to all future actors that will use it.

| Acceptance target | Evidence |
| --- | --- |
| Shared target interface and unchanged pickup behavior | [Pickup refactor](#interaction-pickup-refactor); unchanged standalone/client pickup checks |
| Device-aware E/X prompts and owned Press/Hold authority | [Interaction foundation](#interaction-foundation); 31 standalone/31 client checkpoints |
| Server-timed holds; release, aim/range/obstruction, menu, pawn/death, availability/destroy and competing-use cancellation | Native interaction test plus both Play runs; direct E fixture check |
| Opt-in Tree/Rock/Campfire/Smithy acknowledgement fixtures | No yields/crafting/injury/storage; no saved/default world content |
| Fresh-water E/X action and replicated survival HUD | [Fresh-water slice](#fresh-water); 13 standalone/14 client checkpoints and direct viewport input |
| Existing subsystem conservation and input isolation | Milestone A pickup/hotbar regression evidence; final ten native tests including water assertions |

All foundation targets above are verified. Production anchor/ladder/crew/vendor/storage behaviors belong to their dependent ship/world systems; resource yields, Attack/tree punching and injuries belong to gathering/combat. Remapping, final presentation and packaged/dedicated/hardware acceptance are retained as explicit later gates. No unresolved design rule has been silently assigned a value. Local editor preference checksum remains `0E61E2200AEAB9EC14A2CD1C55F024F1CCAB668D1C43759D89B71DD9D7B0185A`; `.mcp.json` stays local.

<a id="hand-gathering"></a>

## October 7, 2026 — Hand-gathered resources

First gathering slice: `AEWHandGatherable` specializes the serialized pickup transfer for finite plant-fiber and loose-stick resource pools. Authored item definition/remaining quantity come from replicated actor data; E/X requests still go through the owned controller and shared 250 cm Visibility trace. The inherited interface dispatch calls virtual `TryPickup`, so specialized resource-category/stable-ID/life checks also apply to direct native transfers. Source ownership, possession, range, aim/visibility, authority and reentrancy guards remain inherited. Inventory-open requests remain blocked by the interaction component. Only accepted units leave the pool; full inventory preserves all remaining stock; depletion destroys the node. There is no regrowth timer or per-hit tool path in this slice.

Saved opt-in `DA_TestFiber` and `DA_TestSticks` use resource stack 250; their 0.01/0.05 kg weights and fixture pool quantities 10/6 are draft test tuning. `Scripts/Setup/create_hand_gathering_test_assets.py` uses Unreal-supported asset APIs and preserves existing assets. `Scripts/Setup/spawn_hand_gathering_play_fixtures.py` creates only PIE actors in `Lvl_M5PickupTest`, never saving a map or granting inventory at normal startup. Cube markers are temporary visuals. Original Tree/Rock Inspect fixtures stay acknowledgement-only; tree harvesting remains Attack.

EWEditor Win64 Development build passed. All **eleven** native `Elitewake` tests passed (`Saved/Logs/HandGatheringFinalRegression.log`). `Elitewake.Gathering.HandResources` covers resource category/life, interface dispatch, aim/wall/ownership/range, partial/full capacity, depletion, replay and total conservation; the previous ten interaction/water/stance/inventory/equipment/pickup/hotbar/exhaustion tests also pass. The initial new test used a world that had not entered Play, preventing authority-only interface event dispatch. Registering and beginning its temporary world corrected the test setup; the full suite was rebuilt and rerun. The failed initial run is not acceptance.

`Scripts/Verification/verify_hand_gathering_play.py` passes **13 standalone and 13 listen/client checkpoints** (`Saved/HandGatheringPlayResult.json`, `Saved/HandGatheringNetworkResult.json`). Both network drivers use 100 ms outgoing lag and 1% loss. Checks cover actual E and controller X input, device-aware Gather/Collect prompts, authoritative inventory and replicated remaining pools, survival weight, distant/obstructed/unaimed/menu/death rejection, partial capacity, full-inventory preservation, freed-capacity collection and competing requests conserving one shared pool. Temporary wall query geometry is created separately in each PIE world because the editor box helper does not replicate. Test cleanup removes fiber/sticks, fixtures/callbacks and restores input, packet settings and throttling.

The unchanged pickup verification script also passed five standalone and five listen/client checks on the final build (`Saved/M5DPickupPlayResult.json` and `Saved/M5DPickupNetworkResult.json`, October 7). Direct viewport E at the visible `E: Gather Fiber (Test)` prompt collected exactly 10 Fiber, left Sticks at zero, updated carried weight to 0.1 kg and cleared the depleted target prompt (`Saved/HandGatheringManualResult.json`, `Saved/HandGatheringManualBefore.png`, `Saved/HandGatheringManualAfter.png`). The fixture setup script was exercised; all actors were transient. Play ended in standalone test-map configuration with no active verification callbacks. The original editor preference checksum remained unchanged; `.mcp.json` stayed local.

Production vegetation/foliage instances, production item weights/yields, berries/food use, resource regrowth, tree Attack/tool harvesting, tools/durability, injuries/infection, crafting and final art remain open. The 25-hit hand injury rule and its unresolved counting/reset/treatment/time conversion are not approximated. Physical controller hardware, packaged and dedicated-server acceptance remain later gates. This is the verified hand-resource foundation, not completion of the entire gathering package.
