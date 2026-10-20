# C7 — Owner's 12 game-improvement requests (partial)

Date: October 20, 2026
Status: partial implementation; code, report and tests committed as `41a050b` and `e3161d7`.
Scope source: `Docs/Delegation/CODEX.md` C7 and the owner's pasted 12-item task list.

## Implemented in source

- The map now builds an overview center and fit width from the placed `AEWClimateRegion` actors, updates the title from the survivor's sampled region, overlays a player marker, supports mouse drag/wheel and right-stick/trigger navigation, and does not recenter when the survivor moves. The overview maximum was raised to fit the five-region layout. The unwanted map-only status phrases were removed while movement and world ticking remain allowed. This remains a live scene capture; clear water/land presentation and complete island visibility need in-game review.
- The hotbar maps D-pad Left/Up/Right/Down to slots 1–4, and LB+A/X/B/Y to slots 5–8. Controller glyphs and the LB label above slot 5 are shown when the controller is the active input device; number keys remain supported.
- D-pad Up/Down continues to reach the existing ladder-climb input while the survivor is on a ladder. In inventory, Y quick-assigns only when LB is not held, preserving LB+Y as slot 8.
- Pressing Y with an inventory item selected requests a binding in the nearest empty hotbar slot, starting at the currently selected slot. It leaves existing bindings untouched when full or already assigned.
- The compass/wind panel backing is darker and more opaque at its existing HUD location.
- The options screen now has live brightness, mouse-look and controller-look sliders. Values persist in the user-settings ini. Brightness is applied to both cameras; look input uses the sensitivity for the last-used input device.
- The sailing-ship helm prompt keeps the existing hold-to-leave interaction but removes the extra W/S sails, A/D rudder and Shift+A/D trim instructions. Sailing inputs and behavior are unchanged.
- Play scripts were updated for the map overview/hint text, controller mapping and Y assignment to a hand-usable torch, and options persistence. The options test restores the user's original settings at cleanup.

## Not implemented / coordinated

| Request | Status and reason |
| --- | --- |
| Cave crystals | Not changed yet. File reservations were released on October 20; inspect the existing cave meshes and asset catalog before selecting an existing approved crystal asset or proposing a new one. |
| Empty ship decks/interiors and sealed windows | Not changed yet. File reservations were released on October 20; audit the current hull/build scripts and verify that the surgeon's table remains while windows stay watertight. |
| Helm prompt cleanup | Implemented in `AEWShip`; `Elitewake.Ships.SailingAuthority` passes assertions for the concise prompt and hold-to-leave interaction. A live on-screen Play review remains unverified. |
| General deck/captain's-quarter placement | Audit found `UEWPlacementPreviewComponent` only previews ship fittings at mounts. There is no general ship deck/interior placement path here to extend safely in this task. |
| Multiplayer island placement restrictions | Not changed. No island ownership/claim API was found in the inspected placement path, and claim timing is unresolved. Single-player unrestricted building, craft-anywhere, Port exclusion, and separation from ship customization must be enforced together when the ownership API exists. |

## Verification

- Unreal Engine 5.8.3 `EWEditor` build: **succeeded** after the last C++ change.
- Unreal native automation `Elitewake.Ships.SailingAuthority`: **passed 1/1** after the helm prompt change. It confirms the prompt includes leaving the helm, excludes the extra control legend, and keeps leaving as a hold interaction; the broader test also exercises helm sailing authority.
- Added `Elitewake.Input.HotbarKeyboardAndControllerBindings`; Unreal native automation **passed 1/1**. It covers number keys 1–8, D-pad slots 1–4, LB+face-button slots 5–8, and rejects face-button shortcuts without LB.
- Python syntax checks for `verify_map_play.py`, `verify_hotbar_play.py`, and `verify_options_menu_play.py`: **passed**.
- `git diff --check`: **passed**.
- Unreal Play checks: **not run**. The editor process exited immediately in the earlier available command session, no fresh Play result was written, and the desktop-control inventory exposed no native-app launcher. The existing `Saved/MapPlayResult.json` is dated October 10 and is stale; it is not evidence for this change. The requested Play checks still need to run in the editor.
- Physical Xbox controller, visual map review, map screenshots at both zoom limits, and multiplayer placement/claim acceptance: **not verified**.

## Working-tree notes

- `Config/DefaultEditor.ini` was already modified by the owner and was not edited, staged, or reverted.
- Claude's protected files were not changed. The owner explicitly authorized publishing this C7 partial update on October 20. Commit: `41a050b`.
- An initial sandboxed Unreal build attempt repeatedly failed to access the shared UBA cache under `C:\ProgramData\Epic`; it was stopped. The approved build then succeeded and the focused native test passed. Unreal and build processes are closed and the editor lock was removed.
