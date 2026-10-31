# Controls (keyboard/mouse and controller)

Owner, October 22: every action has a controller equivalent using standard MMORPG-style mappings. This table is read from the code (`EWPlayerController.cpp`, `EWInventoryWidget.cpp`,
`EWMapWidget.cpp`, `EWCharacter.cpp`) on October 22; anyone who changes a binding updates it. Status: `OK` works and is covered by a Play check, `PARTIAL`, `GAP` no controller input yet.

## In the world
| Action | Keyboard / mouse | Controller | Status |
|---|---|---|---|
| Move / look | WASD / mouse | Left stick / right stick | OK |
| Jump, swim up | Space | (project Enhanced Input default) | PARTIAL: verify |
| Sprint | Left Shift (hold) | click the left stick (L3) once to start; click again, stop moving or run out of stamina to end | PARTIAL |
| Stance (crouch/prone) | per `IA_Stance` | per `IA_Stance` | PARTIAL |
| Attack | Left mouse | Right trigger | OK |
| Interact / gather | E (hold) | X (west face button) | OK |
| Ride a spider (climb on) | E (press, within reach of a live spider) | X | OK, October 28. Steer with the move input (along the camera heading); Jump / A gets off. Sprint, crouch and attacks are off while riding. Seat height is tuning |
| Inventory | I | Y (north face button) | OK |
| Map | M | Back / View button (added Oct 22) | OK (this change; needs a Play check) |
| Pause menu: RESUME GAME, SAVE GAME (single player), OPTIONS, MAIN MENU; OPTIONS holds brightness (whole picture), mouse and controller horizontal/vertical look speed and master volume (with a dial), BACK or Escape returns | Escape, Up/Down, Enter, Left/Right adjust | Start, d-pad, A, B | OK (`verify_options_menu_play`) |
| Private-test session menu | F10 | (none) | GAP, test-only |
| Hotbar slots 1 to 8 | 1 to 8 | d-pad left/up/right/down = 1 to 4; hold LT + the d-pad = 5 to 8 (one thumb, added Oct 23, `verify_hotbar_trigger_play`); or hold LB + A/X/B/Y = 5 to 8 | OK (`verify_hotbar_play`, `verify_hotbar_trigger_play`) |
| Assign item to hotbar | Open inventory, press 1 to 8 | Select item, hold LB + slot button, or Y quick-assigns to the first empty slot; Y again (item already on bar, or bar full) opens a slot picker: d-pad moves, A assigns or removes, B cancels | OK (`verify_hotbar_picker_play`) |
| Region teleport (testing phase only) | Shift + 1 to 5 | not bound | 1 Plains starter island, 2 Jungle, 3 Desert, 4 Swamp, 5 Winter; carries the survivor to dry ground near the island centre. Compiled out of shipping builds (`verify_region_teleport_play`) |
| Port teleport (testing phase only) | Shift + 6 | not bound | carries the survivor to the nearest Port plaza, in front of its general merchant (use Shift + 1 to 5 first for another region's Port). Compiled out of shipping builds (`verify_port_teleport_play`) |
| Talk to a townsperson | E (press) | X | opens their dialogue window; choose with 1 to 9 or a click, Up/Down (or W/S) and Enter, D-pad and A; leave with Escape, E or Tab, or B (`verify_freeport_multiplayer_play`) |
| Mark a target for hired gunners (at a cannon) | Right mouse | LB | marks the ship your cannon is laid on; on open water it clears the mark (`verify_gunner_volley_multiplayer_play`) |
| Climb ladder | Up / Down arrows | d-pad up / down | OK |
| Sail trim left / right | Left / Right arrows | LB / RB | OK |
| Respawn after death | Enter / Space / click | A | OK (`verify_death_respawn_play`) |

## In the menu (inventory screen)
| Action | Keyboard / mouse | Controller | Status |
|---|---|---|---|
| Next / previous section (Inventory, Skills, Company, Tames, Journal; the menu always opens on Inventory) | Tab / Shift+Tab, PageDown / PageUp, click a tab | RB / LT, or tap LB | OK (`verify_menu_sections_play`, `verify_menu_layout_play`) |
| Move selection (a gold ring marks it; Down past the last item row enters the crafting list, Up returns) | Arrows | d-pad / left stick | OK (`verify_menu_layout_play`) |
| Tab bar: Up from the top of any tab (or the pause menu) highlights the tabs; Left/Right move, A opens | Up, Left/Right, Enter | d-pad or left stick, A | OK (`verify_menu_layout_play`) |
| Ship's hold: pick a stack, move it across | Arrows, Enter, or click | d-pad or left stick, A | OK (`verify_ship_cargo_play`) |
| Company (live, October 30): pick member / action, next lower panel; Enter on Invitations accepts an invitation | Up/Down, Left/Right, Enter, X or R | d-pad, A, X | OK (`verify_company_screen_multiplayer_play`, `verify_menu_layout_play`) |
| Tames: pick a creature | Up/Down | d-pad | OK (sample data only) |
| Confirm / craft / unlock star | Enter | A | OK |
| Equip / use | R | X | OK |
| Choose a stat for a point | C, then Up/Down, Enter | RT, then d-pad, A | OK (`verify_stats_play`) |
| Skill tree: move among stars | Arrows or hover | d-pad | OK (`verify_skills_play`) |
| Journal: next / previous page | Up / Down | d-pad up / down | OK |
| Close | I / Escape | B | OK |

## Build Mode (milestones 2 and 3; test access: no Builder's Plan item yet; costs TBD)
| Action | Keyboard / mouse | Controller | Status |
|---|---|---|---|
| Enter / leave Build Mode | B (Escape also leaves) | click right stick | OK (`verify_build_mode_play`) |
| Open / close the piece dial | Tab | Y | OK (`verify_build_mode_play`) |
| Open / close the doors and windows wheel (door frame, door, window frame, window; F again goes back to pieces) | F | X (left face button) | OK (`verify_build_mode_play`) |
| Point at a dial slot | mouse | right or left stick | Pointer maths OK (injected values); real stick and mouse deltas not injectable in Play checks |
| Pick the slot / place the piece / remove the piece you look at (demolish) | Left mouse | A or RT | OK (`verify_build_mode_play`) |
| Step through slots with the dial closed | mouse wheel | none | code only, not Play-checked |
| Turn a foundation a quarter | Q / E | d-pad left / right | OK (`verify_build_mode_play`) |
| Change material (placeholder: Thatch, Wood, Stone, Metal) | Z / C | LB / RB | OK (`verify_build_mode_play`) |
| Change wall design (solid / doorway, placeholder) | R | d-pad up / down | OK (`verify_build_mode_play`) |
| Switch place / demolish | X | B button | OK (`verify_build_mode_play`) |
Ghost is blue where it may go, red with a reason where it may not. Other pieces go at fixed places on a foundation (or ceiling): top wall on the top edge, corners where walls meet, ceiling and roof need a wall under them. A and the dial's keys replace jump while Build Mode is on. Hint text is an on-screen debug line.

## On the map
Pan: drag / right stick. Zoom: wheel / triggers. Close: M or Escape / Back or B.

## Known gaps for the team (task C8)
- Jump, sprint and stance controller bindings live in assets (`Content/Elitewake/Input`) and are not written down here; check each in a gamepad-only Play check.
- LB is both the hotbar modifier and sail-left; RB is sail-right and next menu section. Decide whether sailing needs its own contexts.
- A single place to rebind keys (an options screen) does not exist.
