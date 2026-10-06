# M5F equipment transfer verification

Reviewed 2026-10-05 in `C:\UnrealProjects\EW`, Unreal 5.8.3. Slice commit: `Implement M5F authoritative equipment transfers`.

## Behavior and design scope

The character now owns a replicated equipment component. Each occupied slot holds one unit of an item definition. Requests travel through the player's owned controller; the server resolves its possessed character, checks ownership and exact item-slot compatibility, and performs the transfer. None/invalid slots and non-equippable resources are rejected. The five Bible body slots remain Head, Chest, Hands, Legs and Feet; existing MainHand/OffHand metadata is supported without adding weapon behavior.

Equip removes one inventory unit. Replacing occupied gear first plans returning the previous unit to inventory, including the slot freed by consuming the incoming item. If the return cannot fit, the whole operation is rejected. Unequip similarly leaves gear equipped when inventory is full. Both containers commit before authority weight recalculation and events, and transfer guards reject reentrant mutations. Replayed requests cannot create extra units. Inventory plus equipment weight contributes to survival carried weight; equipping does not shed weight. Capacity is still 24 inventory slots, without a hard weight cap.

The scrolling inventory lists occupied equipment after stored stacks. Enter/A/click opens details; R/controller X or the visible Equip/Unequip button performs the selected action. These action bindings are draft UI choices. Equipped slot rows, total carried weight and server result messages update in the local panel. A full-inventory message explains why gear remains equipped. The mouse button preserves panel focus for subsequent keyboard/stick navigation. Cosmetics, meshes, armor protection, durability, item instances, persistence, item use and the eight-slot hotbar are separate gates.

`DA_TestHat` and `DA_TestHatAlternate` are opt-in Head-slot fixtures with stable IDs `Test.Hat` and `Test.HatAlternate`, stack one and temporary weights 2/3 kg. `Scripts/create_equipment_test_assets.py` preserves existing assets. No grant is added to normal Play, and no production item/map/story content changes in this slice.

## Verification

- EWEditor Win64 Development build succeeds. `Saved/Logs/M5FFinalRegression.log` records seven successful automation tests: StanceBlendSpaces, EquipmentTransfer, PersistedEquipmentFixtures, PersistedTestItem, PickupValidation, StackingAndWeight and StanceCollision.
- EquipmentTransfer covers authority/null/ownership/slot rejection, single-unit consumption, occupied-slot swaps, full-inventory rejection, a blocked swap whose source stack does not free space, restoration after freeing capacity, returning into a partial stack, repeated requests and carried-weight conservation.
- PersistedEquipmentFixtures discovers and loads both saved hats by their stable primary IDs in a fresh engine process. Initial asset creation emitted stale registration-ID diagnostics before the configured IDs were saved; fresh-process discovery succeeds.
- `Saved/M5FEquipmentPlayResult.json`: 12 standalone checkpoints pass through focused Slate keys, owned-controller intent and authority fixture grants.
- `Saved/M5FEquipmentNetworkResult.json`: 12 client checkpoints pass in an in-process listen-server/client session with 100 ms outgoing lag and 1% loss on both drivers. Server/client item counts, equipped definition, composite weight and survival carried weight agree. The other player's inventory/equipment remains unchanged; direct client mutation is rejected.
- Existing M5E selection and M5D pickup network scripts were rerun in fresh sessions after M5F: 19 selection and five pickup checkpoints pass.
- Actual mouse Equip/Unequip clicks, subsequent keyboard navigation/confirmation and the full-inventory feedback are inspected in Play. `Saved/M5FMouseEquip.png`, `Saved/M5FMouseUnequipFocus.png` and `Saved/M5FFullInventoryFeedback.png` record the layout. A console inspection steals UI focus, so its recorded focus flag is not mouse-focus acceptance evidence; navigation immediately after the button click verifies preserved input.

The initial scripted network runs were not acceptance evidence: Unreal's editor scripting guard forced actor RPCs to execute locally, where authority checks rejected them. Actual native Slate input successfully equipped on the server. The editor-only verifier now scopes that scripting bypass off during normal input/owned-controller requests and restores it immediately; gameplay authority remains unchanged. The successful network run uses this corrected helper. Test reports/scripts retain failure information and are isolated from other Python execution.

`Scripts/verify_equipment_play.py` runs only in fresh PIE, restores panel, throttle and packet settings, and removes its callback on completion/failure/Play exit. Grants are confined to PIE. Stop Play after testing. The helpers live in EWEditor and are excluded from game targets.

## Remaining gates

Physical controller/device switching, polished equipment presentation, protective stats, durability, per-instance identity/save/load, death/logout drops, packaging, dedicated servers and broader network/load coverage remain unverified. M5G hotbar is next; M4 survival/HUD work remains open. The rye/currency/prologue requirements and core ship-home design are unchanged.

## Owner-requested acceptance recheck

On 2026-10-05, after publication of `f2d32d4`, the owner requested confirmation before moving on. A fresh editor build succeeded and all seven automated tests passed in `Saved/Logs/M5FAcceptanceRegression.log`. A fresh editor process reran equipment, selection and pickup scripts in separate standalone and listen-server/client sessions: 12 + 19 + 5 checkpoints passed in each mode. Multiplayer used 100 ms outgoing lag and 1% loss on both drivers. `Saved/Logs/M5FAcceptancePlay.log` contains no Error, ensure or fatal entries from this pass.

The additional `Scripts/verify_equipment_network_stress.py` sent 60 alternating equip and 40 repeated unequip intents across the two owned controllers in fresh two-player PIE. Its two checkpoints verified both players in both worlds, covering authority, owning-client and observing-client copies. All eight recorded character states retained correct inventory/equipment quantities and 5.1 kg composite/survival weight per player. This is a bounded local regression probe, not a production load test. Packet/throttle settings and its callback were restored/removed on completion.

`Saved/M5FAcceptanceSummary.json` indexes the seven fresh Play reports, totaling 74 successful checkpoints. No gameplay fix was required. Play is stopped, single-player settings restored, and the editor observer removed. The existing `Config/DefaultEditor.ini` owner change remains untouched and excluded from publication. Remaining gates above still apply; this recheck does not begin M5G or certify the full game.
