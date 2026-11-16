# Inventory Slice 4 — pending attributes and paid reset

November 12, 2026. The owner authorized this slice while explicitly deferring the unresolved equipment report. Equipment is not owner-approved as working; see the owner-review notation at the top of Inventory-Slice-3-Review.md. No equipment diagnosis or item-art changes were made in Slice 4.

## Functionality

- Plus creates a local pending allocation. The invested count shows committed plus pending points, with pending emphasis and a committed/pending tooltip. Real attributes and the server's point pool remain unchanged until Confirm.
- Minus removes only pending additions. It cannot refund committed points.
- Confirm commits the whole validated batch and saves it; Cancel discards the draft. Closing the menu or changing tabs discards unconfirmed points.
- Keyboard/controller: C / RT enters attribute selection; Up/Down follows the displayed supported rows; Left/Right adjusts pending points; Enter/A confirms; Esc/B cancels. Within attribute selection, R/X opens reset confirmation. Mouse plus, minus, Confirm, Cancel and Reset use actual interactive widgets.
- The reset asks for confirmation, charges exactly 5 gold through the existing wallet, refunds invested character attribute points, recalculates existing effects, and saves the result. It changes no constellation skill points, unlocked skills, level or experience.
- Existing Health, Stamina, Weight and Fortitude rules are reused. Oxygen and Intelligence remain unallocatable until the owner defines their effects. The six-row presentation remains.
- Server-side checks cover ownership/living survivor, exact batch shape, nonnegative additions, unspent budget, overflow, current revision, money, and successful persistence. A revision rejects duplicate/stale allocation and reset requests. A pending-request latch prevents repeat UI requests while awaiting a response.
- If persistence fails, the transaction restores invested/unspent points, money, current health and current stamina. It does not leave a paid reset or allocation half applied.

## Economy and persistence

The existing conversion is 500 copper per silver and 30 silver per gold. The reset therefore costs **75,000 copper**, exactly **5 gold**. A compile-time check ties that amount to the current conversion. No rewards, starting funds, merchant prices or other economy values changed. A fresh survivor's zero purse cannot afford the reset.

Standalone uses the existing survivor save. Hosted play uses the existing per-player server save. The normal save restrictions still apply; a survivor aboard/attached, on a ladder or mounted may need to return to land before the save can succeed. A failed save rolls back this transaction rather than charging anyway.

Attribute revision is a runtime replay guard. Existing save fields store the committed point arrays, unspent balance and purse; no save-schema replacement or equipment migration was introduced. The older internal single-point progression API remains available; the Inventory uses the new confirmed batch path.

## Editor verification

- Win64 Development Editor build passed; existing deprecation warnings remain.
- Standalone Play acceptance passed all **20** checks at 1920×1080 and 1280×720.
- Listen-server/client Play acceptance passed all **20** checks through normal owned-controller requests.
- Coverage includes pending-only mouse edits, pending-only minus, keyboard editing, controller cancellation/confirmation/reset, authoritative effects, actual saved allocation/reset values, exact currency charge, replay rejection, insufficient money, stale drafts, preserved constellation progression, unsupported rows and 720p cancellation.
- Play tests use uniquely named EW_AttributeVerification_ saves, configured only in PIE. They delete only their own generated test save. They do not write the owner's Survivor or hosted profile slots.
- The native AttributeTransactions test separately covers invalid/over-budget allocations, save-failure rollback, exact purse restoration, injured health/stamina restoration, insufficient gold, refunds, replay rejection, empty reset, unchanged skills/level/XP and client-authority rejection.

The native AttributeTransactions test passed without warnings, including failed-save rollback of points, money and injured health/stamina. Reports: Saved/InventoryAttributesPlayResult.json, Saved/InventoryAttributesNetworkResult.json and Saved/Automation/InventorySlice4/index.json. Screenshots: Saved/Screenshots/InventorySlice4.

These are Development Editor/PIE tests using temporary progression and currency fixtures. Controller events are injected through Unreal's input route. They do not establish owner acceptance in the normal game launch; no packaged EXE has been updated.

## Presentation limits

The three columns, current wood/brass styling, 70%/80% backgrounds and live survivor presentation were preserved. The center footer adds contextual confirmation/status controls. While these are visible, lower center content requires scrolling; controller attribute selection reveals its selected row. This is functional layout, not a claim of a finished visual match at both resolutions.

Known earlier UI/art differences and the owner's equipment issue remain deferred. No Oxygen/Intelligence effects, full UI redesign, world edits, clothing-icon cleanup or new equipment work were included.

## Affected files

- Source/EW/EWProgressionComponent.h and .cpp — authoritative batch/reset transactions and replay revision.
- Source/EW/EWSurvivalComponent.h — progression-only access to restore exact vitals after failed persistence.
- Source/EW/EWPlayerController.h and .cpp — owned requests/results and existing persistence routing.
- Source/EW/EWInventoryWidget.h and .cpp — pending controls, confirmation/cancellation, reset, feedback and input.
- Source/EWEditor/Public/EWEditorVerificationLibrary.h and Private/EWEditorVerificationLibrary.cpp — isolated-save configuration, normal request injection and widget-state inspection for tests.
- Source/EW/Tests/EWAttributeTransactionTests.cpp — transaction regression test.
- Scripts/Verification/verify_inventory_attributes_play.py — Play acceptance and screenshot capture.
- Docs/Inventory-Slice-3-Review.md — owner's unresolved-equipment notation and launch/build verification follow-up.
- This review.

Existing work, intentionally deleted planning documents, world actors, backups and real survivor saves were preserved. Nothing was committed, packaged or published. Stop for owner review.
