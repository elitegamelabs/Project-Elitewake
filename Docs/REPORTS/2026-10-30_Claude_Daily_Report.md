# Claude daily report — October 29–30, 2026

Owner direction: keep building the game's structure with placeholder art and free sounds until paid art is possible; pick defaults and keep going (the owner edits later).

## Done and Play-checked

| Work | Evidence | Status |
|---|---|---|
| **Port general merchant** (`AEWMerchant`): one per Port plaza; E sells every pack item that has a `SellValueCopper` value; placeholder prices on 18 items | `verify_port_merchant_multiplayer_play` PASS (2 players) | 🟡 no buying/stock yet |
| **Zero starting purse**: new survivors start with 0 Copper (the inn's 250 is not built); the surgeon check now funds its own purse | `verify_ship_surgeon_multiplayer_play` PASS (aim needed retries, as before) | ✅ |
| **Sail control and crew dependency**: each sail keeps its own setting; Port crew master hires a sailhand for 100 Copper (Sailhand Articles); signing on happens at the sail's lines (pin rail by the mast); the helm sets only crewed sails; survivors can work any sail by hand with Up/Down; placeholder sailhands haul when their sail changes | `verify_sail_crew_multiplayer_play` PASS (2 players); Elitewake.Ships.* and Elitewake.Save PASS | 🟡 see Milestones row |
| **Buying from the Port merchant**: a counter of goods crates beside each merchant; aim at a crate and press E to buy one bundle; five goods lines per Port with placeholder prices and stock, one bundle restocked every 300 s | `verify_port_merchant_multiplayer_play` PASS (2 players, extended); `verify_sail_crew_multiplayer_play` PASS | 🟡 stock not saved, same goods everywhere |
| **Saltreach Freeport** (owner request): the Plains Port rebuilt as an explorable harbor town and starting hub — harbor, piers and berths, market, walk-in tavern, shipyard and slipway, hiring and harbor offices, square, lighthouse; 15 named people with dialogue windows and working services (trade, crew roster, rumours/drinks/jobs, buy and repair ships, berth and depart); safe zone (no PvP, building or hostile creatures). Details: Design/World/SALTREACH_FREEPORT_2026-10-30.md | `verify_freeport_multiplayer_play` PASS (2 players, every service and rule); `verify_freeport_look_play` screenshots, day and night | 🟡 placeholder art; see the design doc's Not done |
| **Freeport polish**: HUD banner entering/leaving the safe zone; walkers stop for a survivor in their way and while talked to; the person talked to turns to face you | `verify_freeport_multiplayer_play` PASS (extended) | ✅ |
| **Freeport sounds**: synthesized (free, original) tavern and market voices, shipyard mallets and saws, water at the piles, and a harbor bell, placed with the existing hull and rigging loops; day-only sounds fade out at night (`AEWTownSound`) | `verify_freeport_sounds_play` PASS; Freeport two-player check PASS | 🟡 placeholders, not judged by ear |
| **Ships are saved (M7)**: the single-player Save Game and the server's world save keep every ship afloat (place, fittings, hold, hull and holes, anchor, sail settings and hired crew, cannons, ports); ships bought in play come back, lost ones stay lost | `verify_ship_save_play` PASS (both saves); build multiplayer, Freeport, cannon fight, Ships and Save automation PASS | 🟡 no ship owners yet; wrecks not kept |
| **World resources are saved (M7)**: cut trees, picked plants and taken items stay gone after loading; partly used trees and deposits (and a deposit's respawn wait) and knocked-over trees lying come back as left; both the Save Game and the server's world save | `verify_world_save_a/b_play` PASS (save in one Play session, load in a fresh one); trees, crystals, ship save, build multiplayer and all 40 automation tests PASS | 🟡 animals and fish not kept |
| **Death bags and wreck crates are saved**: their place, goods (food keeps its age) and the time they had left | `verify_world_save_a/b_play` PASS (extended); death and respawn check, all 40 automation tests PASS | ✅ |
| **Cannon operation**: loading in four steps (sponge, powder, shot, ram), recoil on every shot, and target lock (Right Mouse / LB marks a ship; hired gunners lay on her); aim lines no longer stop at the sea's invisible swimming volume | `verify_gunner_volley_multiplayer_play` PASS (extended: steps and recoil on both screens, a marked ship fired on while the survivor's own cannon is laid 15 degrees off); cannon fight, brigantine, ship save, Freeport and 40 automation tests PASS | 🟡 no powder item, no lead on moving targets |
| **Port teleport (testing only)**: Shift + 6 carries you to the nearest Port, in front of its merchant (owner request); compiled out of shipping builds | `verify_port_teleport_play` PASS (all five Ports) | ✅ |
| **Hired gunners and volleys**: Port gunnery master hires a gunner (150 Copper, Gunner Articles; tuning); signed on at a cannon, they load from the hold and fire with the survivor's shot when their cannon bears and the line is clear | `verify_gunner_volley_multiplayer_play` PASS (2 players, ships test map) | 🟡 see Milestones row |

## Fixed along the way

- Calling a server request from an editor Python check runs it on the client (the editor's script guard); the Freeport check sends dialogue choices through a C++ wrapper (`SendVerificationDialogueChoice`) and closes windows with real key events, like the other checks.
- The dialogue window could not take keys (not focusable); a real player's Escape and number keys would have done nothing. Fixed and checked.

- Ships near a Port stopped moving: the new merchant and crew master figures, and the ship's own surgeon, blocked everything, so a hull's swept move caught on them. They now block only people and aim traces, and the hull ignores its own surgeon. Schooner check moved 33 m again.
- `EWWalletComponent.cpp` stopped compiling in a new unity grouping (`Gold` hid a global); renamed the locals.

## Decisions I made (owner may change)

- Sailhand fee 100 Copper; sell prices per item; crew master and merchant stand on each Port plaza. All tuning.
- With no sailhand aboard, the helm does nothing to the sails (owner rule: unassigned sails cannot be operated from the helm). A lone sailor works the sails by hand at the mast or hires crew.
- The volley's mark is where the survivor's own cannon points (no target lock yet); a hired gunner holds fire when their cannon cannot bear or something solid is in the way.
- The merchant sells round shot, repair kits, cooked fish, medicinal herbs and water flasks: what a sailor needs between islands. Buying aims at a crate rather than opening a menu, so it works with the existing E prompt; a menu can come with the UI pass.
- Signing on uses an item (Sailhand Articles) so the hire happens at the Port and the assignment happens aboard, sail by sail.

## Not done

- There are no wages or crew limits. Gunners use no powder item (only round shot), and do not lead a moving target.
- The Freeport stands on the Plains Port's site; palms stand in it although the starter island's trees are oaks (the owner's October 30 request asks for palms). Ships have no owner, so the shipwright and harbor master act on the ship nearest you.
- Merchant stock is not saved, and every Port sells the same goods at the same prices.
- All figures are placeholder shapes.
