# C7 — Owner's 12 game-improvement requests (partial)

Date: October 20, 2026
Status: partial implementation; map/options/helm changes are in `41a050b` and `e3161d7`; the reusable mining substrate is in `38b817b`.
Scope source: `Docs/Delegation/CODEX.md` C7 and the owner's pasted 12-item task list.

## Implemented in source

- The map now builds an overview center and fit width from the placed `AEWClimateRegion` actors, updates the title from the survivor's sampled region, overlays a player marker, supports mouse drag/wheel and right-stick/trigger navigation, and does not recenter when the survivor moves. The overview maximum was raised to fit the five-region layout. The unwanted map-only status phrases were removed while movement and world ticking remain allowed. The map lifecycle and pan/zoom controls passed a two-player Play check; clear water/land presentation, readability at both zoom bounds, and complete island visibility still need a visual review.
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
| Cave crystals and winter deposits | Mining support is now implemented in `AEWMineable`: pickaxe tiers gate mining, optional total stock randomizes from 4–8, depleted nodes can respawn on an authored timer, and depletion/respawn visibility and collision replicate. A two-player listen-server/client Play check passes against a test-only Metal Pick fixture. Production resource DataAssets/IDs, a production Metal Pick, resource-specific node meshes, and cave/winter placement are not integrated. `Scripts/Setup/build_caves.py` still builds cave rock only and explicitly leaves deposits pending. The owner-approved distribution rules remain in `Docs/OwnerDecisions/CRYSTAL_AND_COAL_SPAWN_RULES_2026-10-18.md`; do not substitute the test fixture for production content. |
| Empty ship decks/interiors and sealed windows | Not changed yet. File reservations were released on October 20; audit the current hull/build scripts and verify that the surgeon's table remains while windows stay watertight. |
| Helm prompt cleanup | Implemented in `AEWShip`; `Elitewake.Ships.SailingAuthority` passes assertions for the concise prompt and hold-to-leave interaction. A live on-screen Play review remains unverified. |
| General deck/captain's-quarter placement | Audit found `UEWPlacementPreviewComponent` only previews ship fittings at mounts. There is no general ship deck/interior placement path here to extend safely in this task. |
| Multiplayer island placement restrictions | Not changed. No island ownership/claim API was found in the inspected placement path, and claim timing is unresolved. Single-player unrestricted building, craft-anywhere, Port exclusion, and separation from ship customization must be enforced together when the ownership API exists. |

## Verification

- Unreal Engine 5.8.3 `EWEditor` build: **succeeded** after the mining tier, stock, respawn, and verification-helper changes.
- `verify_resource_mining_lifecycle_play.py` passed **5/5** checkpoints in two-player listen-server/client Play: randomized 4–8 stock and Metal gate; generic pick rejected; Metal test pick accepted; depletion hid the node and disabled collision on both machines while awarding the full stock; 2-second test respawn restored 4–8 stock and collision on both. Result: `Saved/ResourceMiningLifecyclePlayResult.json`. This proves reusable mining behavior only, not production assets, cave/winter placement, one-hour balance timing, or visual resource identity.
- Unreal native automation `Elitewake.Ships.SailingAuthority`: **passed 1/1** after the helm prompt change. It confirms the prompt includes leaving the helm, excludes the extra control legend, and keeps leaving as a hold interaction; the broader test also exercises helm sailing authority.
- Added `Elitewake.Input.HotbarKeyboardAndControllerBindings`; Unreal native automation **passed 1/1**. It covers number keys 1–8, D-pad slots 1–4, LB+face-button slots 5–8, and rejects face-button shortcuts without LB.
- Python syntax checks for `verify_map_play.py`, `verify_hotbar_play.py`, and `verify_options_menu_play.py`: **passed**.
- `git diff --check`: **passed**.
- `verify_map_play.py` passed 8/8 two-player listen-server/client checks; result: `Saved/MapPlayResult.json`. The mining lifecycle Play check also passed for its test fixture as described in `Docs/VERIFICATION.md`. Controller hotbar/Y assignment, compass presentation, options persistence, and visual map review still need dedicated Play review. The native hotbar test covers mapping logic only; it does not verify physical controller input or in-world behavior.
- Physical Xbox controller, visual map review at both zoom limits, and multiplayer placement/claim acceptance: **not verified**.

## Working-tree notes

- `Config/DefaultEditor.ini` was already modified by the owner and was not edited, staged, or reverted.
- Claude's protected files were not changed. The owner explicitly authorized publishing this C7 partial update on October 20. Mining code and test fixture: `38b817bf973ce33630489c42396d13039968c2b9`.
- An initial sandboxed Unreal build attempt repeatedly failed to access the shared UBA cache under `C:\ProgramData\Epic`; it was stopped. The approved build then succeeded and the focused native test passed. Unreal and build processes are closed and the editor lock was removed.
