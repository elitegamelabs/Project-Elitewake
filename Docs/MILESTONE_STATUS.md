# Milestone status

Reviewed: 2026-10-05. Status describes individual layers, not finished-game readiness.

Current reference is the October 5 Authoritative Revision and later direct owner clarification of the rye sale. See [current revision review](DESIGN_REVISION_2026_10_05.md); the [September reconciliation](CONTEXT_RECONCILIATION.md) remains historical evidence. Owner paused M5 after M5C and returned to M2 stance animations on Unreal 5.8.3; M5D remains pending. M4 HUD, hunger/hydration gameplay and complete stamina exhaustion testing remain open; moving to M5 was an owner direction, not full M4 acceptance. New survival rates are requirements, not implemented behavior.

**Planned**: no implementation evidenced. **In Progress**: slice underway. **Implemented**: code/content exists. **Verified**: specified test passed. **Postponed**: deliberately deferred. **Blocked**: named dependency prevents progress. **Replaced**: superseded implementation.

## Verified baseline and history

| Milestone/system | Gameplay implementation | Presentation/content | Multiplayer evidence | Files and commits |
| --- | --- | --- | --- | --- |
| M0 foundation | Verified: active repository/path and history inspected | Project structure documented; template content | No online infrastructure claimed | `EW.uproject`, `.gitignore`, `README.md`, `Docs/PROJECT_STRUCTURE.md`; `919737f`, `50ecc95` |
| M1 locomotion | Implemented: move/jump, walk 500, sprint 750 | Template animations | Sprint state replicated in source; network session not repeated in this review | `Source/EW/EWCharacter.*`; `d8ca1dc` |
| M2 stance | Verified foundation: tap C/B, hold 0.35s prone; distinct stance sizes, clearance-gated exits and prone body movement query | Proper stance blends, aligned roots and camera; final polish/controller hardware coverage open | Client/host collision states verified with 100 ms outgoing packet lag and 1% loss; dedicated server/moving decks pending | `EWCharacter.*`, `EWCharacterMovementComponent.*`, `ABP_EWLocomotion`; [collision verification](M2_COLLISION_VERIFICATION.md) |
| Temporary stance scaling | Replaced: reverted | Do not restore as animation substitute | Not applicable | `cf282a8` reverted by `e88acb1` |
| M3 cameras/states | Implemented: default third person, Z toggle; six locomotion states | Cyan diagnostics temporary; final perspective animations Planned | Perspective local; state source inspected, network presentation pending | `EWCharacter.*`; `fb214b3` |
| M4 survival | Implemented: health/stamina/hunger/hydration/temperature/weight; stamina drain 15/s and recovery 10/s | Stamina diagnostic only; final HUD Planned | Replicated component and authority checks; dedicated-server validation pending | `EWSurvivalComponent.*`, `EWCharacter.*`; `55ed2c1` |
| Integrations | Implemented: Unreal MCP auto-start, Git editor, client configs | Scenario availability reported by handoff; no asset request made | Not gameplay | `EW.uproject`, `Config/DefaultEditorPerProjectUserSettings.ini`, `Config/DefaultSourceControlSettings.ini`; `0e18009`, `2f36734`, `edb52c3` |
| M5A items/inventory | Implemented: definitions, categories/slot metadata, 24 slots, stacking, add/remove/count/weight | No game item assets/pickup evidenced in this slice | Replicated entries; server-only mutation source inspected. Multi-client behavior pending | `EWItemDefinition.*`, `EWInventoryComponent.*`, `EWInventoryComponentTests.cpp`; `9b7f129` |
| M5B inventory panel | Verified: build, empty panel, I open/close/reopen and walking/camera recovery | Native functional draft; not final inventory design | Local-only Play test; remote populated inventory not verified | `EWInventoryWidget.*`, `EWPlayerController.*`; `286f8d0`, pushed after owner approval |
| M5C persisted test item/grant | Verified: saved asset registration/load, stacking/capacity/weight tests and populated Play panel | Wood (Test), resource stack 250, temporary fixture weight 0.1 kg | Authority check and no client grant RPC; multi-client behavior not verified | `DA_TestWood`, editor-only `EWGrantTestWood`; [verification](M5C_INVENTORY_VERIFICATION.md) |
| M5D-G pickup/interactions/equipment/hotbar | Planned | Planned | Planned | Slot enum is metadata only; no equip behavior claimed |

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

Generated logs are local evidence, not tracked artifacts. Historical handoff play claims are not fresh verification. M5B verification applies to the empty local draft; M5C adds the populated checks below. Full gameplay and multiplayer remain pending.

M5C adds populated local verification: 251 -> stacks 250/1, live increment to 252 -> 250/2, weight 25.1 -> 25.2 kg, zero/negative rejection, I close/reopen, and fresh Play empty. Both inventory automation tests succeeded. Full gameplay, packaging and multiplayer remain pending.

## Known limitations and next gates

- Inventory controller Y, automatic selection, navigation/highlight, character preview, tabs and crafting are Planned.
- Normal Play starts empty. The persisted Wood fixture can now be explicitly granted in editor Play; gameplay pickups remain Planned.
- Cyan movement diagnostics remain visible over the draft panel; final HUD/panel layout and long-list scrolling are pending presentation work.
- Inventory UI currently follows inventory-change events; survival-only capacity updates and pawn replacement need a later lifecycle pass.
- Max carried weight is a displayed survival value; current inventory capacity is enforced by slots, not a weight limit. Encumbrance gameplay remains Planned.
- Primary item scan and native fixture load are Verified; packaging remains pending. Required GameFeatureData scan/rule now resolves the previous startup configuration error.
- Save/load, dedicated-server tests, final assets and polished HUD are not verified.
- Proper stance animations and collision/clearance foundations are configured and tested. Physical controller coverage, authored transitions and final perspective/terrain animation polish remain open; see [M2 collision verification](M2_COLLISION_VERIFICATION.md).
- Free Animation Library was imported into the older backup; its content is now present in the active project. No status is claimed for other previously mentioned packs.
- Bible §25.4 includes item durability and structured tags; current item definition has neither. These are Planned extensions, not completed item behavior.
- Current maps, death/logout drops, persistence and ownership transfer are not implemented; they are requirements for future inventory/equipment integration.
- Controller command radial is now Middle Mouse / D-pad Right, resolving the old View/Select conflict. Current dinghy opening replaces raft construction; persistent sloop progression placement remains to be designed.
