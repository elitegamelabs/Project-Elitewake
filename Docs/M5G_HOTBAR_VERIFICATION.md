# M5G hotbar foundation verification

Reviewed 2026-10-06 in `C:\UnrealProjects\EW`, Unreal 5.8.3. Slice: `Implement M5G owned hotbar shortcuts`.

## Behavior and design scope

The owning player has a permanent eight-slot bottom-center draft HUD. Bindings reference owned item definitions; they are not extra storage and do not change quantities or carried weight. Each definition has one shortcut, so reassignment moves it. The server resolves the requesting controller's own possessed character and validates ownership and slot indices. Bindings and selected slot replicate only to that owner.

Inventory details expose eight assignment buttons. Keyboard 1–8 or LB combinations assign the selected item while details are open; selecting its existing binding clears it. Outside inventory these shortcuts select the slot and request its implemented action. Equipable definitions use the existing M5F atomic equipment transfer and full-inventory return rules. Repeated activation of already-worn gear does not consume another unit. Empty, unavailable and unsupported actions produce feedback without changing item quantities. Unavailable bindings remain and become usable again when the item is replenished.

Bible §5.9 confirms 1–8 and the LB modifier concept. Exact draft controller order is LB+A/B/X/Y for slots 1–4 and LB+D-pad Up/Right/Down/Left for 5–8. This order is implementation tuning, not a new authoritative design rule. The complete chord is consumed before ordinary gameplay input, including a face-button release after LB releases first. Engine key flushing also clears custom modifier state. Without LB, ordinary A jump, B stance/close, X pickup/equipment and Y inventory roles remain available.

The old permanent inventory control-hint panel is removed in accordance with §5.8; contextual assignment buttons replace it. HUD names are shortened for the draft layout. No normal-player grants, production assets or story/economy changes are introduced.

## Verification

- EWEditor Win64 Development builds successfully. `Saved/Logs/M5GFinalRegression.log` records eight successful automation tests, including new `Elitewake.Inventory.HotbarOwnershipAndActivation` and all seven previous stance/inventory/pickup/equipment regressions.
- The hotbar automation covers authority, invalid indices, unowned definitions, reference-only assignment, unique bindings, worn availability, safe replay, equipment swaps, blocked full-inventory returns, resources without consumption, retained unavailable bindings, replenishment and clearing.
- `Scripts/verify_hotbar_play.py` passes 42 standalone and 42 owning-client checkpoints. Client requests use ordinary Slate input/controller RPC routing, with 100 ms outgoing packet lag and 1% loss on the local listen-server/client drivers. Host and owner agree on bindings, selected slot, equipment, inventory quantities and weight; the other player's inventory and equipment remain unchanged.
- The Play runs cover all eight keyboard activation keys, all eight controller combinations in both inventory and world, assignment/move/clear, equipment activation/replay/swaps, empty/unsupported/unavailable/replenished shortcuts, release ordering, normal Y/B/X/A roles and engine input flushing while LB is held. The last check proves normal Y opens inventory after the flush.
- The existing network selection and equipment scripts pass all 19 and 12 checkpoints with the modified inventory widget.
- Mouse assignment moves the selected definition to slot four, a second click clears it, and immediate Down/Enter still selects and opens the next item's details. Inventory quantity and 6.1 kg fixture weight remain unchanged. `Saved/M5GMouseResult.json` records the probe. The final taller HUD was rebuilt and visually inspected to accommodate wrapped names and quantities in small Play windows.

Local reports are `Saved/M5GHotbarPlayResult.json`, `Saved/M5GHotbarNetworkResult.json`, `Saved/M5ESelectionNetworkResult.json` and `Saved/M5FEquipmentNetworkResult.json`. Generated reports, logs and screenshots are evidence retained locally, not tracked assets. The 84 hotbar and 31 existing regression checkpoints precede the final HUD-height-only adjustment; the rebuilt layout is checked visually afterward.

## Remaining gates

This verifies the hotbar foundation and equipment shortcut action. Consumables, weapon drawing, treasure maps, taming and underwater-only harpoon restrictions require their actual item-action systems; resources currently bind safely but do not consume or execute an invented action. Map-open input suppression must be integrated when the map exists. Save/load, death/respawn policy, per-instance durability/identity, remappable bindings, physical controller hardware, packaged/dedicated-server testing and final artwork remain open. M4 survival/HUD work remains independently incomplete.
