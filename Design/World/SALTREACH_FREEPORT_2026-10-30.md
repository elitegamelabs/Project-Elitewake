# Saltreach Freeport — the starting hub (owner request, October 30, 2026)

Owner direction (October 30): build an explorable, working Freeport — a small pirate harbor town that players reach by ship and
explore on foot, with a harbor, marketplace, tavern, shipyard, crew recruitment and town square, named NPCs with real interactions,
and safe-harbor rules. ATLAS's freeports are the gameplay inspiration only; nothing (names, art, text, numbers) is copied.

Status: built into `Lvl_CoastalPlayground` and Play-checked (see "Evidence"). Everything visible is placeholder art built in the
editor from engine shapes, the project's timber texture, its palms and the engine mannequin. Names, prices, stock, rumours and jobs
are placeholders for the owner to edit.

## Decisions made for the owner (reversible)

| Decision | Why | To change |
|---|---|---|
| The Freeport replaces the **Plains starter Port** on the starter island's south-west shore. | The owner asked for a starting hub; the Plains Port is the starter Port (owner, October 22). Its site already sits in a bay with a low headland as a natural breakwater. | `build_freeport.py` takes the Port from `world_layout.PORTS['Plains']`; `build_ports.py` and `add_port_merchants.py` skip the Plains. |
| The other four regional Ports stay as they were. | Only the Freeport was asked for. | — |
| Name: **Saltreach Freeport**; tavern **The Salt Lantern**. | Original names. | `NAME` and the NPC table in `build_freeport.py`. |
| **Palms** stand through the town, though the starter island's trees are oaks (owner, October 16: palms belong to the Desert). | The October 30 request asks for a tropical harbor with palms; the latest direction wins. Oaks still stand round the town. | `build_palms` in `build_freeport.py` (swap the meshes for `SM_Oak_*` or remove the call). |
| The island's terrain is not reshaped. | The site is already levelled; rebuilding the whole world's terrain risks every placed thing on it. The town's streets, seawall, wharf and piers are built on and over the existing ground. | — |
| "Your ship" is the ship nearest you (for repair, berthing and departure). | Ships have no owner yet. | `AEWShipwright::FindShipToRepair`, `AEWHarborMaster::FindShipFor`. |
| The harbor master's berthing and departure **tow** the ship (pilots), anchored at the berth or the harbor mouth. | A working docking service without an autopilot. | `AEWShip::TowTo`. |
| The safe zone is a circle of 95 m over town and harbor. | Covers the terrace, the piers, the berths and the harbor mouth. | `build_safe_zone` (radius) in `build_freeport.py`. |

## Layout (in the Port's frame: "along" points out to sea through the waterfront)

- **Harbor:** a stone seawall round the terrace and a timber wharf along its front; the **long pier** (54 m) to deep water with
  three berths (east, outer east for larger hulls, west); the **fishing jetty** (41 m) off the right side with two small-boat berths;
  bollards, ladders, mooring posts in the water, cargo, rope coils, lobster pots and net racks; two rowboats off the jetty and two
  fishing boats at anchor; a **channel beacon** either side of the harbor mouth; a timber **lighthouse** on the headland. Lamps
  along the waterfront and piers.
- **High street** from the tavern to the wharf (plank boardwalk), crossed by the **market lane**.
- **Marketplace:** five stalls facing across the market lane — resources (Oskar Brann), provisions (Marta Vell), outfitter
  (Lucia Fane), a fish stall and a fruit stall — awnings, goods on show, cargo piles.
- **Town square** at the head of the high street: the well, the **notice board**, benches, palms, lamps and a flag.
- **The Salt Lantern** tavern facing down the high street: walked into through its front door; bar, shelves of bottles, casks,
  hearth, seven tables with stools, hanging lanterns, a veranda with tables, the hanging sign. Lit inside at night.
- **Shipyard** on the left by the headland: an open ship shed over a hull in frame on the building cradle with scaffolding, the
  **slipway** running into the harbor (new hulls are launched at its foot), the workshop, timber and stores.
- **Hiring office** by the fishing jetty (thatched, porch) and the **harbor office** at the long pier's root (two storeys, flag).
- Houses and a warehouse round the edge; palms through the town.

## People (all `AEWTownsfolk`; press E to open the dialogue window)

| Name | Role | Where | What they do |
|---|---|---|---|
| Marta Vell | Provisioner (merchant) | Provisions stall | Sells round shot x5, repair kits, cooked fish, medicinal herbs, water flasks; buys the pack. |
| Oskar Brann | Resource Trader | Resources stall | Sells wood, stone, fibre, thatch (x10), hide, ore (x2); buys the pack. |
| Lucia Fane | Outfitter (cosmetics) | Outfitter stall | Sells two hats and white colours. |
| Gideon Rusk | Crew Recruiter | Hiring office porch | A roster of six named sailors and gunners (fee, a word about each); signing one gives their articles. One more arrives every 4 minutes. |
| Bess Harrow | Keeper of the Salt Lantern | Behind the bar | Rumours (one after another), a drink (5 Copper, slakes thirst), five repeatable delivery jobs paid on hand-in. |
| Elias Thorne | Master Shipwright | Head of the slipway | Sells a raft (120), dinghy (400) and sloop (2,500), launched fitted out at the slipway; repairs the nearest damaged ship in the harbor (hull, holes, water) priced by damage. |
| Captain Ines Calder | Harbor Master | Harbor office porch | Brings your ship to a free berth that takes her length; clears her for departure to the harbor mouth with you aboard; tells the harbor rules. |
| notice board | — | Town square | The posted jobs and directions to every service. |
| (everyone named) | | | Turns to face whoever talks to them; walkers stop while talked to. |
| Pell, Hask, Ondine, Wat, Rosa, Abe, Corrie | dock workers, fisher, townsfolk, shipwright's hand, watchwoman | Walking rounds (piers, wharf, jetty, square, market, yard) | A word when spoken to. |
| Silas, Nan, Ibbie, Mack | patrons, sailor | Tavern, veranda, wharf | A word when spoken to. |

Prices (Copper) and stock are tuning. Hats and the flag are the existing test items.

## Safe harbor (`AEWSafeZone`)

The HUD announces it under the region banner on the way in ("Saltreach Freeport · a free port: no fighting, no building, no beasts") and on the way out.

Inside the zone: no survivor can hurt another (fists; round shot strikes and splashes but holes no ship); Build Mode refuses every
spot ("A free port: nobody may build here."); no hostile creature lives there (one placed inside is removed when play starts) and a
hunting creature drops the chase at the edge. The boundary is invisible to players and exact in the game logic.

## Evidence

- `verify_freeport_multiplayer_play` (listen server plus client): every named person's window opens on the client from a real
  interaction request; buying, selling, the number-key choice, Escape to leave, hiring from the roster, rumour, drink, delivery job,
  notice board, buying a raft, repairing her after a hole, berthing her and clearing her for departure with the client aboard; a punch
  does nothing inside the town and lands outside it; Build Mode refuses a town spot; no hostile creature inside. PASS.
- `verify_freeport_look_play`: twelve screenshots (`Saved/Screenshots/FreeportLook/`), day and night, judged by eye.

## Not done

- All art is placeholder: buildings, props and boats are editor-built shapes on the project's timber texture; townsfolk are the
  engine mannequin painted with plain clothes (no faces, hair or real clothing); no NPC sounds, no ambient town audio.
- Townsfolk walk fixed loops; they stop for a survivor in the way (and walk on when the way is clear) but do not step round them; nobody sits.
- Quests are delivery jobs only; no quest log, chains or story quests. Rumours are fixed text.
- Ships have no owner, so services act on the nearest ship; towing is instant (no pilot boats).
- No buying in quantity, no regional prices, merchant stock is not saved.
- Hired sailors' names do not go aboard with them; crew are not saved (ships are not saved).
- The terrain was not reshaped; the slipway's top crosses the terrace's seawall.
