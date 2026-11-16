# Inventory Slice 2 — recipe cards

Implemented November 12, 2026. This slice changes crafting interaction within the existing Inventory design. It adds no center-column Recipe Details section and changes no gameplay recipes or transactions.

## Behavior

- A single left click switches the existing recipe tile to its requirements. A second single click restores the item face. Selecting a different recipe restores the previous face and inspects the new one.
- Double-click requests one eligible craft through the existing player-controller/server crafting path. The tile and its Slate click target remain stable during inspection, quantity refresh, craft start and completion.
- R on keyboard or X on controller toggles inspection. Enter or controller A crafts; key repeats cannot issue another craft. Existing arrow, d-pad and left-stick recipe selection remain available.
- Mouse wheel, Shift+Up/Down and controller right stick scroll the inspected tile. Scrolling stays inside its fixed bounds. It does not enlarge the tile, cover adjacent recipes, or scroll the outer recipe list through the bottom of the card.
- Cards use actual ingredient definitions and aggregate duplicate costs. Need/Have quantities update from the player's inventory. Craft time, hand/campfire requirement and readiness use the actual recipe and existing validation. Detailed station/material/capacity failure reasons also remain visible in the existing action area.
- A pending-request latch prevents additional requests before the server acknowledges a craft. Existing busy checks remain in force while its timer runs.
- Search filters the live unlocked recipe list. It rebuilds tiles only when that list actually changes, preserving the selected recipe by identity where possible.

## Preserved scope

The three-column layout, Inventory grid, fixed recipe-tile sizes, current wood/brass styling, warm 70%/80% panel backgrounds, center-column information and live survivor preview are unchanged. No character art, item artwork, world geometry, saves, crafting transactions, recipe assets, progression or economy settings were edited.

The disabled RESET STAT POINTS (5 GOLD) control remains for the later stat slice. Equipment additions, attribute changes, constellation changes, and clothing-icon transparency cleanup remain deferred.

## Verification

See the current JSON results in Saved/InventoryRecipeCardsPlayResult.json and Saved/InventoryRecipeCardsNetworkResult.json. The acceptance script exercises actual Slate clicks, a first click plus a real double-click event, keyboard keys, controller buttons, mouse wheel and controller analog input. The network run sends normal requests with the editor's local-RPC bypass disabled.

The test sessions use temporary real recipe fixtures, unlocks and materials. Recipe durations are shortened only in memory and restored; no fixture or survivor state is saved. The test map is Lvl_ShipsTest. Controller coverage uses injected Unreal input events rather than physical controller hardware.

Screenshots are direct captures of the Play viewport including its UI, at 1920×1080 and 1280×720, in Saved/Screenshots/InventorySlice2. The fixtures deliberately show three recipes and a simple inventory so inspection is easy to see.

- Win64 Development Editor build passed. The existing font-constructor deprecation warning remains.
- Standalone acceptance passed all 23 checks, including 1080p/720p interaction, actual mouse single/double clicks, stable tile identity, keyboard/controller inspect and craft, internal scrolling, live quantities, search, missing resources, station readiness and loss of materials during a running craft.
- Listen-server/client acceptance passed all 23 checks through the normal authority path.
- The existing networked timed-crafting regression passed all three checks: materials are retained until completion, exactly one shovel consumes exactly 20 wood after three seconds, and death during crafting gives no item and loses no ingredients.
- Elitewake.Crafting.AtomicTransaction passed, covering locked recipes, missing materials, full inventory, duplicate ingredient aggregation, invalid overflow costs and client-authority rejection. Its report is Saved/Automation/InventorySlice2/index.json.
- Python syntax and scoped diff-whitespace checks passed.

## Files changed for this slice

- Source/EW/EWInventoryWidget.h
- Source/EW/EWInventoryWidget.cpp
- Source/EWEditor/Public/EWEditorVerificationLibrary.h
- Source/EWEditor/Private/EWEditorVerificationLibrary.cpp
- Scripts/Verification/verify_inventory_recipe_cards_play.py
- Docs/Inventory-Slice-2-Review.md

The editor-only helpers add double-click, mouse-wheel, right-stick and explicit Play-viewport capture support. Existing unrelated working-tree changes and deleted planning documents are preserved. Nothing has been committed or packaged.

## Remaining limits

- Longer ingredients, long names, station conditions and detailed failure text require scrolling within the deliberately fixed-size tile. Even a simple card can require a short scroll to its final status line. The full recipe name, readiness/failure reason and time also remain visible in the existing action area.
- The previously recorded Slice 1 visual differences still apply, including placeholder survivor/equipment assets, clothing-image backgrounds and long Inventory captions clipping at 720p. This slice does not claim a pixel match to the approved illustration.
- The artwork and source dependencies already recorded in the Slice 1 review remain local/untracked; this is a local Editor verification, not a clean-checkout packaging certification.

Stop for owner review before Slice 3.
