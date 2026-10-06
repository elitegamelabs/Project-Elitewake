# M5E inventory selection verification

Reviewed 2026-10-05 in `C:\UnrealProjects\EW`, Unreal 5.8.3. Slice commit: `Implement M5E inventory selection and navigation`.

## Behavior and scope

The native inventory draft now selects the first valid stack on opening, highlights the selection, and supports Up/Down, controller D-pad/left stick, and mouse hover/click. Enter/controller A/click confirms the selected stack and shows its description, quantity, unit weight and stack limit. Confirmation is read-only; equipping and item use belong to later slices.

I and controller Y open the panel through Enhanced Input. I/Y/B/Escape close it from the focused UI. Inventory owns keyboard/controller input while open; movement/look input is ignored and pressed gameplay keys are flushed. Closing restores the controller's matching input locks and normal game focus. The world continues running. Designer-assigned inventory input actions require their own mapping contexts; full user remapping is not implemented by these draft UI keys.

The list scrolls to keep selection visible. Opening details also requests scrolling because the details reduce the list height. Refresh preserves item definition plus stack occurrence where possible, otherwise clamps to a valid row. These are local display positions, not persistent stack IDs. Empty/unavailable inventory clears selection and details. The widget rebinds when its owning pawn's inventory changes. Summary reads current survival capacity while visible; changing capacity through an approved gameplay API remains unverified.

Left-stick dead zone 0.5, initial repeat delay 0.35 seconds and repeat interval 0.18 seconds are draft UI tuning, not additional Bible rules. List boundaries clamp without wrapping. Controller Y, automatic first focus, visible selection and controller navigation implement the relevant §§5.8/25.4 foundation; character preview, tabs, equipment and art remain separate gates.

## Verification

- EWEditor Win64 Development builds succeeded, including the final selected-row layout fix and explicit SlateCore dependency.
- `Saved/Logs/M5ERegression.log`: all five existing automation tests Success (StanceBlendSpaces, PersistedTestItem, PickupValidation, StackingAndWeight, StanceCollision). The later layout-only fix does not change their gameplay scope.
- `Saved/M5ESelectionPlayResult.json`: 19 checkpoints pass through real Slate keyboard/gamepad key/analog events, routed into the focused Play UI. Empty navigation, I/Y open/close, first selection, arrows/D-pad, Enter/A confirmation, stick dead zone/repeat, B/Escape cancellation, removed-stack clamp, live details refresh and empty-to-populated transitions are covered. Input locks and focus are checked at each stage.
- `Saved/M5ESelectionNetworkResult.json`: the same 19 checkpoints pass from the client of an in-process listen-server/client session, with 100 ms outgoing lag and 1% loss on both drivers. Authority inventory changes replicate into the selected client panel without invalid selection.
- Mouse hover/click on the second stack visibly changes highlight and confirms details; `Saved/M5EMouseDetails.png` records it.
- Follow-up Play checks cover actual movement recovery, movement blocking while open, unpossessed view clearing, repossession rebinding and full 24-slot selection. `Saved/M5EFollowupResult.json` and `Saved/M5EFullListDetails.png` record the final checks.

`Scripts/verify_inventory_selection_play.py` runs in fresh single-player or in-process listen-server/client Play. Its state is isolated in a function closure, it uses only the existing Wood fixture and authority test mutations, and it restores UI/input focus, packet/throttle settings and callback registration on success/failure/Play exit. Test inventory lives only in PIE; stop Play afterward. Editor-only Slate injection helpers are excluded from game targets. No production item content or default starting inventory was added.

Earlier probes encountered Python reflection restrictions and an editor crash whose stack was in PythonScriptPlugin/python311; they are retained as diagnostics and are not acceptance evidence. The project was reopened and the selection verifier rerun with isolated Python state. The additional probe was separated from attempted editor property changes. No root cause or long-duration stability claim is made from the crash stack alone.

## Remaining gates

Physical controller hardware and real device-switching, remapping/options, LB/RB tabs, character preview/final art, arbitrary long descriptions, world pickup prompts/reticle/feedback, general item operations, equipment/hotbar, new-pawn respawn flows, packaging, dedicated servers and broad performance/load tests remain unverified or planned. Pawn absence/rebinding was tested by unpossessing/repossessing the same actor, not a complete respawn system. Inventory slots still enforce capacity; a hard weight cap and encumbrance are not implemented.
