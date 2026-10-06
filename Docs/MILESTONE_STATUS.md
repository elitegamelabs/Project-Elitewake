# Milestone status

Reviewed: 2026-10-06. Status describes individual layers, not finished-game readiness.

Current reference is the October 5 Authoritative Revision and later direct owner clarification of the rye sale. See [current revision review](DESIGN_REVISION_2026_10_05.md); the [September reconciliation](CONTEXT_RECONCILIATION.md) remains historical evidence. Owner returned from M2 stance/collision work to M5D on Unreal 5.8.3; the pickup foundation is now verified. M4 survival gauges and empty-stat warnings are now verified in a dedicated return slice. Hunger/hydration gameplay, current-rate reconciliation and full survival acceptance remain open. October 6 owner clarification permits stamina recovery while walking; new survival rates remain requirements, not implemented behavior.

**Planned**: no implementation evidenced. **In Progress**: slice underway. **Implemented**: code/content exists. **Verified**: specified test passed. **Postponed**: deliberately deferred. **Blocked**: named dependency prevents progress. **Replaced**: superseded implementation.

## Verified baseline and history

| Milestone/system | Gameplay implementation | Presentation/content | Multiplayer evidence | Files and commits |
| --- | --- | --- | --- | --- |
| M0 foundation | Verified: active repository/path and history inspected | Project structure documented; template content | No online infrastructure claimed | `EW.uproject`, `.gitignore`, `README.md`, `Docs/PROJECT_STRUCTURE.md`; `919737f`, `50ecc95` |
| M1 locomotion | Implemented: move/jump, walk 500, sprint 750 | Template animations | Sprint state replicated in source; network session not repeated in this review | `Source/EW/EWCharacter.*`; `d8ca1dc` |
| M2 stance | Verified foundation: tap C/B, hold 0.35s prone; distinct stance sizes, clearance-gated exits and prone body movement query | Proper stance blends, aligned roots and camera; final polish/controller hardware coverage open | Client/host collision states verified with 100 ms outgoing packet lag and 1% loss; dedicated server/moving decks pending | `EWCharacter.*`, `EWCharacterMovementComponent.*`, `ABP_EWLocomotion`; [collision verification](M2_COLLISION_VERIFICATION.md) |
| Temporary stance scaling | Replaced: reverted | Do not restore as animation substitute | Not applicable | `cf282a8` reverted by `e88acb1` |
| M3 cameras/states | Implemented: default third person, Z toggle; six locomotion states | Cyan diagnostics temporary; final perspective animations Planned | Perspective local; state source inspected, network presentation pending | `EWCharacter.*`; `fb214b3` |
| M4 survival | Implemented stats; current stamina drain 15/s and recovery 10/s, including walking; full needs gameplay remains open | Verified draft health/stamina/food/hydration/weight gauges and 1.5-second empty-stat warnings | Standalone/client HUD checks pass with packet emulation; retained owner-only exhaustion notification; dedicated server pending | `EWSurvivalComponent.*`, `EWSurvivalWidget.*`; [HUD return evidence](M4_HUD_VERIFICATION.md) |
| Integrations | Implemented: Unreal MCP auto-start, Git editor, client configs | Scenario availability reported by handoff; no asset request made | Not gameplay | `EW.uproject`, `Config/DefaultEditorPerProjectUserSettings.ini`, `Config/DefaultSourceControlSettings.ini`; `0e18009`, `2f36734`, `edb52c3` |
| M5A items/inventory | Implemented: definitions, categories/slot metadata, 24 slots, stacking, add/remove/count/weight | No game item assets/pickup evidenced in this slice | Replicated entries; server-only mutation source inspected. Multi-client behavior pending | `EWItemDefinition.*`, `EWInventoryComponent.*`, `EWInventoryComponentTests.cpp`; `9b7f129` |
| M5B inventory panel | Verified: build, empty panel, I open/close/reopen and walking/camera recovery | Native functional draft; not final inventory design | Local-only Play test; remote populated inventory not verified | `EWInventoryWidget.*`, `EWPlayerController.*`; `286f8d0`, pushed after owner approval |
| M5C persisted test item/grant | Verified: saved asset registration/load, stacking/capacity/weight tests and populated Play panel | Wood (Test), resource stack 250, temporary fixture weight 0.1 kg | Authority check and no client grant RPC; multi-client behavior not verified | `DA_TestWood`, editor-only `EWGrantTestWood`; [verification](M5C_INVENTORY_VERIFICATION.md) |
| M5D pickups | Verified: server range/aim/visibility/ownership checks, partial transfer and exhaustion | Saved Wood pickup Blueprint and isolated test map; E/controller X draft bindings | Competing host/client intent conserves quantities; inventory/remainder replication verified under 100 ms outgoing lag/1% loss | `EWPickup.*`, `EWPlayerController.*`; [verification](M5D_PICKUP_VERIFICATION.md) |
| M5E selection/details | Verified: first selection, highlight, keyboard/D-pad/stick/mouse navigation, read-only confirmation and safe live refresh | Native scrolling draft, I/Y open and UI focus; physical controller/final art pending | 19 client UI checkpoints pass with replicated authority changes under local packet emulation | `EWInventoryWidget.*`, `EWPlayerController.*`; [verification](M5E_SELECTION_VERIFICATION.md) |
| M5F equipment | Verified: ownership/slot validation, atomic equip/unequip and occupied-slot swaps; worn weight retained | Equipped rows, action button/R/X and result feedback; opt-in hat fixtures | 12 client checkpoints pass under 100 ms outgoing lag/1% loss; foreign pawn unaffected | `EWEquipmentComponent.*`, inventory/controller/widget; [verification](M5F_EQUIPMENT_VERIFICATION.md) |
| M5G hotbar | Verified foundation: eight owned-definition shortcuts, assignment/move/clear, safe equipment activation | Permanent native draft HUD; 1–8, contextual mouse buttons and LB combinations; final art/hardware pending | 42 standalone and 42 client checkpoints pass with packet emulation; owner-only bindings and quantity/weight conservation | `EWHotbarComponent.*`, `EWHotbarWidget.*`, inventory/controller; [verification](M5G_HOTBAR_VERIFICATION.md). Other item actions and persistence remain open |

## Verification ledger

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
| 2026-10-05 | M2 collision/clearance acceptance on 5.8.3 | Build and four automation tests pass; eight animation/camera and sixteen single-player clearance checkpoints pass; sixteen client/host clearance checkpoints pass with 100 ms outgoing lag/1% loss; eleven stance/sprint/simulated-proxy checkpoints pass. [Scope and evidence](M2_COLLISION_VERIFICATION.md) |
| 2026-10-05 | M5D pickup acceptance | Build and five automation tests pass; five single-player and five host/client pickup checkpoints pass, including packet emulation and competing intents; actual E collection and I populated panel inspected. [Scope and evidence](M5D_PICKUP_VERIFICATION.md) |
| 2026-10-05 | M5E selection/details acceptance | Build and existing five regression tests pass; 19 single-player and 19 replicated client UI checkpoints pass; mouse/details and full-list layout inspected; movement and pawn absence/rebinding probed. [Scope and evidence](M5E_SELECTION_VERIFICATION.md) |
| 2026-10-05 | M5F equipment transfer acceptance | Build and seven regression tests pass; 12 standalone and 12 client equipment checkpoints pass, including full-capacity rejection, swaps, replay safety and carried-weight conservation. [Scope and evidence](M5F_EQUIPMENT_VERIFICATION.md) |
| 2026-10-05 | Owner-requested M5 acceptance recheck before advancing | Fresh build and seven automation tests pass; equipment/selection/pickup rerun standalone and network plus 100-intent equipment probe: 74 Play checkpoints pass. No gameplay fix required; M5G remains Planned at that checkpoint. [Recheck record](M5F_EQUIPMENT_VERIFICATION.md#owner-requested-acceptance-recheck) |
| 2026-10-06 | M5G hotbar foundation and snag review | Build and eight automation tests pass; 42 standalone and 42 client hotbar checks plus 19 selection/12 equipment regressions pass. Review fixes engine-flush modifier reset and narrow-window layout; mouse assignment/clear/focus and rebuilt client HUD inspected. [Evidence and limits](M5G_HOTBAR_VERIFICATION.md) |
| 2026-10-06 | M4 survival HUD return | Final build and nine automation tests pass; 20 standalone/20 client HUD checks plus 42 network hotbar regressions pass. Real sprint exhaustion/1.5-second notices, needs warnings, weight and possession changes verified; final HUD inspected. Walking recovery confirmed by owner; full survival rates/effects remain open. [Evidence](M4_HUD_VERIFICATION.md) |

Generated logs are local evidence, not tracked artifacts. Historical handoff play claims are not fresh verification. M5B verification applies to the empty local draft; M5C adds the populated checks below. Full gameplay and multiplayer remain pending.

M5C adds populated local verification: 251 -> stacks 250/1, live increment to 252 -> 250/2, weight 25.1 -> 25.2 kg, zero/negative rejection, I close/reopen, and fresh Play empty. Both inventory automation tests succeeded. Full gameplay, packaging and multiplayer remain pending.

## Known limitations and next gates

- Inventory Y, first selection, highlight/navigation and read-only confirmation are implemented and scripted-input verified. Physical hardware, character preview, tabs and crafting remain open.
- Normal Play starts empty. Wood can be collected in the isolated M5D fixture map or explicitly granted in editor Play. Production gathering/content remain Planned.
- Cyan movement diagnostics remain part of the draft HUD; final HUD/panel art and arbitrary long-description layout are pending. The 24-slot list now scrolls with selection.
- Inventory UI follows inventory-change events and rebinds to its owning pawn; same-pawn absence/rebinding is tested. Complete respawn flows and survival-only capacity changes through gameplay remain unverified.
- Max carried weight is a displayed survival value; current inventory capacity is enforced by slots, not a weight limit. Encumbrance gameplay remains Planned.
- Primary item scan and native fixture load are Verified; packaging remains pending. Required GameFeatureData scan/rule now resolves the previous startup configuration error.
- Save/load, dedicated-server tests, final assets and polished HUD are not verified.
- Proper stance animations and collision/clearance foundations are configured and tested. Physical controller coverage, authored transitions and final perspective/terrain animation polish remain open; see [M2 collision verification](M2_COLLISION_VERIFICATION.md).
- Free Animation Library was imported into the older backup; its content is now present in the active project. No status is claimed for other previously mentioned packs.
- Bible §25.4 includes item durability and structured tags; current item definition has neither. These are Planned extensions, not completed item behavior.
- Current maps, death/logout drops, persistence and ownership transfer are not implemented; they are requirements for future inventory/equipment integration.
- Controller command radial is now Middle Mouse / D-pad Right, resolving the old View/Select conflict. Current dinghy opening replaces raft construction; persistent sloop progression placement remains to be designed.
