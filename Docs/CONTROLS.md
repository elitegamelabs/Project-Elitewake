# Controls (keyboard/mouse and controller)

Owner, October 22: every action has a controller equivalent using standard MMORPG-style mappings. This table is read from the code (`EWPlayerController.cpp`, `EWInventoryWidget.cpp`,
`EWMapWidget.cpp`, `EWCharacter.cpp`) on October 22; anyone who changes a binding updates it. Status: `OK` works and is covered by a Play check, `PARTIAL`, `GAP` no controller input yet.

## In the world
| Action | Keyboard / mouse | Controller | Status |
|---|---|---|---|
| Move / look | WASD / mouse | Left stick / right stick | OK |
| Jump, swim up | Space | (project Enhanced Input default) | PARTIAL: verify |
| Sprint | Left Shift | Left stick click is used for stats in menus; sprint per `IA_Sprint` | PARTIAL |
| Stance (crouch/prone) | per `IA_Stance` | per `IA_Stance` | PARTIAL |
| Attack | Left mouse | Right trigger | OK |
| Interact / gather | E (hold) | X (west face button) | OK |
| Inventory | I | Y (north face button) | OK |
| Map | M | Back / View button (added Oct 22) | OK (this change; needs a Play check) |
| Options menu | Escape | Start | OK |
| Private-test session menu | F10 | (none) | GAP, test-only |
| Hotbar slots 1 to 8 | 1 to 8 | d-pad left/up/right/down = 1 to 4; hold LT + the d-pad = 5 to 8 (one thumb, added Oct 23, `verify_hotbar_trigger_play`); or hold LB + A/X/B/Y = 5 to 8 | OK (`verify_hotbar_play`, `verify_hotbar_trigger_play`) |
| Assign item to hotbar | Open inventory, press 1 to 8 | Select item, hold LB + slot button, or Y quick-assigns | OK |
| Climb ladder | Up / Down arrows | d-pad up / down | OK |
| Sail trim left / right | Left / Right arrows | LB / RB | OK |
| Respawn after death | Enter / Space / click | A | OK (`verify_death_respawn_play`) |

## In the menu (inventory screen)
| Action | Keyboard / mouse | Controller | Status |
|---|---|---|---|
| Next / previous section | Tab / Shift+Tab, PageDown / PageUp, click a tab | RB / LT | OK (`verify_menu_sections_play`) |
| Move selection | Arrows | d-pad | OK |
| Confirm / craft / unlock star | Enter | A | OK |
| Equip / use | R | X | OK |
| Choose a stat for a point | C, then Up/Down, Enter | Left stick click, then d-pad, A | OK (`verify_stats_play`) |
| Skill tree: move among stars | Arrows or hover | d-pad | OK (`verify_skills_play`) |
| Journal: next / previous page | Up / Down | d-pad up / down | OK |
| Close | I / Escape | B | OK |

## On the map
Pan: drag / right stick. Zoom: wheel / triggers. Close: M or Escape / Back or B.

## Known gaps for the team (task C8)
- Jump, sprint and stance controller bindings live in assets (`Content/Elitewake/Input`) and are not written down here; check each in a gamepad-only Play check.
- LB is both the hotbar modifier and sail-left; RB is sail-right and next menu section. Decide whether sailing needs its own contexts.
- A single place to rebind keys (an options screen) does not exist.
