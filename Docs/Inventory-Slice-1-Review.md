# Inventory Slice 1 review

Reviewed November 12, 2026 against the owner's latest approved changes.

The core layout and survivor-preview work passes its functional review. The remaining visual differences are recorded in Inventory-Post-Slice.md for later polish. This closes the Slice 1 presentation foundation with those explicit limitations.

| Area | Review result |
| --- | --- |
| Overall layout | Three columns and all five existing navigation tabs are present. Inventory and Crafting stay on the left. Identity, progression, Equipment, World, Character Stats, and reset stay in the center. The right column holds the live survivor. |
| Inventory | Six columns display the actual 24-slot capacity. Sorting, selection, details, live stack refresh, empty state, and reopening work. |
| Crafting | Existing search, readiness checks, ingredients tooltip, Craft button, and keyboard/controller crafting work. No separate center Recipe Details section remains. |
| Live data | Identity, progression, climate, body temperature, equipment, and applicable stat values read the existing gameplay components. |
| Presentation | Warm backgrounds use the approved 70% and 80% opacity. The current serif headings, rounded frames and buttons, centered grid, inset status text, and adjusted reset placement are present. |
| Survivor preview | Full-body source mesh and equipped meshes render over an alpha-composited background. Bright-shore, dim-deck, and 720p checks passed. The fixture's underlying character and equipment are placeholders. |
| Scrolling | Review found equipment selection attempting to reveal a widget through the inventory scroll box. The widget now routes inventory selections to ItemsScroll and equipment selections to SurvivorScroll, including confirmation and delayed reveal. The subsequent UI and networked equipment checks passed without that scroll warning. |
| Readability limits | Long inventory captions can clip at 720p. The lower stat controls have tight clearance above the reset footer at that size. These are recorded visual follow-ups. |

**Verification**

- Win64 Development Editor build succeeded after the scroll-routing correction.
- The fresh UI review passed all 27 checks at 1920 by 1080 and 1280 by 720. This includes portrait alpha, world ticking, mouse sorting, controller input, recipe search, missing-material rejection, and exactly-one-item crafting through Enter and controller A.
- The existing inventory selection verification passed 22 checkpoints on a network client. It exercised empty and populated inventories, keyboard, d-pad, analog dead zone, item removal, live refresh, and menu focus/lifecycle.
- The existing equipment verification passed 12 checkpoints on a network client. It exercised ownership/slot rejection, equip/unequip, swaps, replay protection, full-inventory rejection, and matching server/client quantities and weight.
- Menu navigation passed all three checks for the five tabs, Journal page navigation, and closing from Journal.
- The first legacy Journal test assumed page zero was always selected. Current discovery refresh preserves the shown page by title. The review rerun explicitly selected page zero before testing page navigation and passed. The original failure report is preserved.
- The test environment was Lvl_ShipsTest with temporary verification fixtures. Controller events were injected through Unreal's Slate input route.
- Diff whitespace validation passed.

Results are in Saved/InventorySlice1ReviewSummary.json, Saved/InventorySlice1FinalReview_1080p.json, and Saved/InventorySlice1MenuReview.json. Fresh captures are in Saved/Screenshots/InventorySlice1FinalReview.

**Later implementation**

- Slice 2 is the crafting interaction slice. Implement stable recipe tiles that toggle between icon and actual requirements on inspect, restore the previous tile when selection changes, and craft exactly one eligible item on double-click through the existing authority path. Keyboard/controller inspect and craft actions must remain distinct. Retain time, station, ingredients, capacity, and failure feedback.
- The five equipment positions are displayed. Accessory is explicitly unavailable in the current gameplay model. Equipment additions belong to their later slice.
- Minus controls are currently disabled. Existing eligible plus controls use the current immediate-spend behavior. Pending allocation, confirmation/cancellation, and the paid reset belong to the later stat slice.
- RESET STAT POINTS (5 GOLD) is currently a disabled presentation control. The later transaction must use existing currency, confirmation, authority validation, attribute refund/recalculation, and saving. It must preserve constellation skill points.
- Oxygen has its existing live survival readout. Intelligence has an unavailable state. New attribute effects require owner-approved definitions.

The current local build depends on untracked UI artwork, materials, fonts, and portrait source added during the approved work. They must accompany any future source handoff. This review covers the local editor build and Play checks; clean-checkout packaging was outside this review.
