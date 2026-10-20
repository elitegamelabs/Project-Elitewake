# C7 — Owner's 12 game-improvement requests (partial)

Date: October 20, 2026
Status: partial implementation; code, report and focused test committed as `41a050b`.
Scope source: `Docs/Delegation/CODEX.md` C7 and the owner's pasted 12-item task list.

## Implemented in source

- The map now builds an overview center and fit width from the placed `AEWClimateRegion` actors, updates the title from the survivor's sampled region, overlays a player marker, supports mouse drag/wheel and right-stick/trigger navigation, and does not recenter when the survivor moves. The overview maximum was raised to fit the five-region layout. The unwanted map-only status phrases were removed while movement and world ticking remain allowed. This remains a live scene capture; clear water/land presentation and complete island visibility need in-game review.
- The hotbar maps D-pad Left/Up/Right/Down to slots 1–4, and LB+A/X/B/Y to slots 5–8. Controller glyphs and the LB label above slot 5 are shown when the controller is the active input device; number keys remain supported.
- D-pad Up/Down continues to reach the existing ladder-climb input while the survivor is on a ladder. In inventory, Y quick-assigns only when LB is not held, preserving LB+Y as slot 8.
- Pressing Y with an inventory item selected requests a binding in the nearest empty hotbar slot, starting at the currently selected slot. It leaves existing bindings untouched when full or already assigned.
- The compass/wind panel backing is darker and more opaque at its existing HUD location.
- The options screen now has live brightness, mouse-look and controller-look sliders. Values persist in the user-settings ini. Brightness is applied to both cameras; look input uses the sensitivity for the last-used input device.
- Play scripts were updated for the map overview/hint text, controller mapping and Y assignment to a hand-usable torch, and options persistence. The options test restores the user's original settings at cleanup.

## Not implemented / coordinated

| Request | Status and reason |
| --- | --- |
| Cave crystals | Not changed. Cave generation/assets are on Claude's protected-file list; crystal identity and placement need coordination. |
| Empty ship decks/interiors and sealed windows | Not changed. Ship builders are protected; needs a ship-side pass and Play verification. |
| Helm prompt cleanup | Not changed. `AEWShip` source is protected; current prompt still includes sail/rudder guidance. |
| General deck/captain's-quarter placement | Audit found `UEWPlacementPreviewComponent` only previews ship fittings at mounts. There is no general ship deck/interior placement path here to extend safely in this task. |
| Multiplayer island placement restrictions | Not changed. No island ownership/claim API was found in the inspected placement path, and claim timing is unresolved. Single-player unrestricted building, craft-anywhere, Port exclusion, and separation from ship customization must be enforced together when the ownership API exists. |

## Verification

- Unreal Engine 5.8.3 `EWEditor` build: **succeeded** after the last C++ change.
- Added `Elitewake.Input.HotbarKeyboardAndControllerBindings`; Unreal native automation **passed 1/1**. It covers number keys 1–8, D-pad slots 1–4, LB+face-button slots 5–8, and rejects face-button shortcuts without LB.
- Python syntax checks for `verify_map_play.py`, `verify_hotbar_play.py`, and `verify_options_menu_play.py`: **passed**.
- `git diff --check`: **passed**.
- Unreal Play checks: **not run**. The editor process exited immediately in the earlier available command session, no fresh Play result was written, and the desktop-control inventory exposed no native-app launcher. The existing `Saved/MapPlayResult.json` is dated October 10 and is stale; it is not evidence for this change. The requested Play checks still need to run in the editor.
- Physical Xbox controller, visual map review, map screenshots at both zoom limits, and multiplayer placement/claim acceptance: **not verified**.

## Working-tree notes

- `Config/DefaultEditor.ini` was already modified by the owner and was not edited, staged, or reverted.
- Claude's protected files were not changed. The owner explicitly authorized publishing this C7 partial update on October 20. Commit: `41a050b`.
- An initial sandboxed Unreal build attempt repeatedly failed to access the shared UBA cache under `C:\ProgramData\Epic`; it was stopped. The approved build then succeeded and the focused native test passed. Unreal and build processes are closed and the editor lock was removed.
