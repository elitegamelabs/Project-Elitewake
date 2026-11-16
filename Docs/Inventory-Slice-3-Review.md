# Inventory Slice 3 — equipment

November 12, 2026. The owner approved Slice 3 and explicitly chose to add playable boots and accessories now.

**Owner review — unresolved, deferred:** After the implementation report, the owner said the equipment does not appear to work in their play experience. Equipment is not accepted as complete. The automated results below describe only the tested fixtures and do not resolve the owner's report. Diagnose the actual normal-game equip/unequip flow later, including item ownership/availability, selection and mouse/controller actions, slot assignment, appearance and persistence. Preserve the current work until that follow-up; do not treat the placeholder models or passing fixture tests as proof of owner acceptance. The owner requested functional behavior as the priority and authorized moving to Slice 4 now.

First identify the exact executable/build used in the owner's test. The verification below ran in the Development Unreal Editor; no updated packaged EXE was produced. Compare that launch path and build to the current local source before diagnosing the deferred equipment issue.

## Delivered

- Hat, Chest, Legs, Boots and Accessory are real selectable equipment positions, including empty slots. Empty selections explain how to equip an appropriate inventory item and cannot create items.
- Accessory was appended to the equipment enum. The existing serialized values, including Main Hand 6 and Off Hand 7, are unchanged. Both hands and legacy glove equipment remain available through their existing equipment/hotbar paths.
- Transfers use the existing authoritative component and player-controller requests, including ownership, slot matching, capacity, replay and atomic replacement checks. Worn weight remains part of carried weight.
- New Leather Sea Boots and Leather Wrist Cuff have actual item definitions, timed crafting recipes, starting-recipe entries and transparent item icons. No currency transaction or merchant price was added.
- The live survivor and portrait use the same equipment. Boots hide the pants' included shoe shapes while worn; removing boots restores that older appearance. Existing pants' costs and attributes were preserved.
- Optional bone-attached wearable mesh parts now let item definitions supply actual meshes/materials to the existing appearance renderer. The cuff uses this path. Production meshes can replace the current placeholder presentation without another equipment-system rewrite.
- The existing Equip/Unequip button stays visible below scrolling item descriptions. This corrects the inaccessible mouse action found during Play testing without adding another panel or changing the three-column arrangement.
- Inventory stack removal now clamps its cursor within remaining inventory rows instead of falling into a new empty equipment position.

## New item tuning

These are the initial authored values, using existing gameplay fields. No new attribute effects were introduced.

| Item | Recipe | Time / station | Weight | Effects |
| --- | --- | --- | --- | --- |
| Leather Sea Boots | 4 Leather + 4 Fiber | 8 seconds, by hand | 1.4 kg | +1 percentage point physical protection, +5 percentage points insulation, +1 percentage point overheating penalty, subject to existing caps/rules |
| Leather Wrist Cuff | 2 Leather + 2 Fiber | 6 seconds, by hand | 0.1 kg | Cosmetic; no attribute bonus |

Both sell values are zero (merchants do not buy them). Existing item prices, currencies, recipes and old armor-set values are unchanged. Boots reuse the existing light/cloth rendering classification and appear as Footwear in their equipment details.

## Verification

- Win64 Development Editor build passed.
- New equipment Play acceptance passed all 22 checks in standalone and all 22 on a listen-server/client session. It exercises actual Slate mouse selection and the Equip/Unequip button, keyboard and controller actions, real recipe costs/times, empty slots, both new items, replicated ownership, appearance components, worn weight, protection/insulation, five simultaneous worn positions, and restoration after removal.
- Fresh Play captures at 1920×1080 and 1280×720 are in Saved/Screenshots/InventorySlice3.
- The existing network equipment verification passed 12 checkpoints, including ownership/slot rejection, replay protection, atomic replacement, full-inventory rejection and matching carried weight.
- The older Inventory navigation check exposed a stack-removal cursor regression, which was corrected. Its fixture now accounts for the intentionally navigable empty equipment slots.
- New native coverage checks serialized slot values and simultaneous five-slot/two-hand equipment. The isolated survivor-save test now includes boots and the accessory, checking restoration and absence of duplicates. It writes only its own uniquely named test save and cleans that test save up.

- The corrected network Inventory navigation check passed all 22 checkpoints. The fixture changes are limited to navigating the new empty equipment positions and explicitly selecting the last inventory stack before testing its removal.
- The Slice 2 recipe-card regression passed all 23 checks after adding the equipment slots.
- All nine native Elitewake.Inventory tests passed, including the new slot-value/transfer test, existing equipment transfers, hotbar ownership, inventory capacity/weight, food, pickups, containers and stable item fixtures.
- The native pickup-validation test passed with two warnings; the other eight Inventory tests passed without warnings.
- The isolated SurvivorRoundTrip test passed, restoring boots/accessory to their correct slots without duplicate inventory items while retaining the existing progression and saved-state checks.
- Scoped whitespace and Python syntax checks passed. The existing font-constructor deprecation warning remains in the build.

Native reports are Saved/Automation/InventorySlice3-equipment/index.json and Saved/Automation/InventorySlice3-save/index.json. Play and native results are summarized in Saved/InventorySlice3ReviewSummary.json.

Controller coverage uses Unreal input injection rather than physical hardware. Play fixtures change only temporary inventories and unlocks, not survivor saves or maps.

## Source and assets changed

- Source/EW/EWItemDefinition.h — appended slot and optional worn mesh parts.
- Source/EW/EWEquipmentComponent.cpp — accepts the appended slot.
- Source/EW/EWInventoryWidget.cpp and .h — five functional slots, selection, empty-state feedback, equipment action access and footwear details.
- Source/EW/Characters/EWArmorLook.cpp and .h — separate boots, included-shoe suppression and authored mesh attachments.
- Source/EW/EWArrivalComponent.cpp — two new starting recipes.
- Source/EW/Tests/EWEquipmentComponentTests.cpp — new-slot transfer/compatibility checks.
- Source/EW/Tests/EWSurvivorSaveTests.cpp — boots/accessory save round trip.
- Scripts/Setup/add_inventory_equipment.py — repeatable setup restricted to the new assets.
- Scripts/Verification/verify_inventory_equipment_slots_play.py — new Play acceptance.
- Scripts/Verification/verify_inventory_selection_play.py — navigation fixture accounts for empty slots.
- Art/UI/Icons/Equipment/T_Icon_LeatherSeaBoots.png and T_Icon_LeatherWristCuff.png — new generated icon sources.
- Content/Elitewake/Items/Armor/DA_LeatherSeaBoots.uasset and DA_LeatherWristCuff.uasset.
- Content/Elitewake/Crafting/Testing/DA_RecipeLeatherSeaBoots.uasset and DA_RecipeLeatherWristCuff.uasset.
- Content/Elitewake/UI/Icons/Equipment/ — two icon textures and MI_LeatherWristCuff material.
- This review and Inventory-Slice-3-Art.md.

Existing working-tree changes, intentionally deleted planning documents, world actors, saves, backups, HUD work, Slice 1 styling and Slice 2 recipe cards were preserved. No EXE was packaged and nothing was committed or published.

## Remaining limits / next slice

The icons are finished item artwork with real alpha; the survivor's garments and footwear still use the game's existing placeholder model approach. The cuff is a simple attached placeholder mesh. These do not constitute finished skinned clothing models.

Previously recorded Slice 1 visual differences remain, including the older clothing-icon backgrounds, long inventory captions clipping at 720p, and tight lower-stat clearance when the armor summary wraps. Clothing-icon cleanup remains deferred until after the final slice.

The disabled RESET STAT POINTS (5 GOLD) button remains unchanged. Pending stat allocation and the paid reset belong to Slice 4; Oxygen and Intelligence effects still require owner definitions. Stop for review before Slice 4.
