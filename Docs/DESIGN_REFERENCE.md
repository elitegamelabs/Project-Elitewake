# Design reference

What Elitewake is meant to be, organized by topic. This file states the current rules only. How each rule was reached, and older rules it replaced, are in [ARCHIVE](ARCHIVE/README.md). What is actually built is in [PROJECT_GUIDE.md](PROJECT_GUIDE.md).

Last reconciled: October 11, 2026.

**October 14 owner revision:** [World structure decisions](WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md) override older geography and the specified resource/traversal rules below. The current layout has five regions; unfinished mechanics and conflicting barrier behavior remain explicitly open. Mode separation is in [Single Player](SINGLE_PLAYER_RULES.md) and [Multiplayer](MULTIPLAYER_RULES.md), with [terrain mesh work assigned to Claude](MILESTONE_WORLD_MESH_HANDOFF_2026-10-14.md).

<a id="authority"></a>

## Authority

When sources disagree, the higher one wins:

1. **The owner's explicit decisions.** The latest decision wins. The *October 9 2026 Complete Design Updates* document was designated by the owner as overriding earlier discussion; later direct decisions override it where they say so.
2. **Elitewake Shared Design Authority & Cross-Team Guide.**
3. **Team guides:** *Game Development & Systems Bible*, *Creative & World Bible*, and the *World Resource & Ecology Guide v1* (resource and species catalog).
4. **This repository's docs.** Code and tests show what is implemented. They do not create design rules.

The October 5 *Master Game Design Bible* is an archive. Its section numbers (§0–§30) are still used as references; it is never edited. The guide documents live outside this repository, in the owner's `OneDrive\Desktop\Elitewake\` folder. Original documents are never modified.

Since October 11, 2026 the owner has delegated gap-filling design decisions to the development team. These are marked **DECIDED (delegated)** and carry the owner's authority until the owner overrides them. They never replace an explicit owner decision.

Status words keep their meaning: **CONFIRMED** (build toward it), **FUTURE** (intended, not in the first playable), **TBD** (concept exists, values or rules undecided), **RECOMMENDED** (a suggestion, not a rule). A value that has not been decided stays TBD. Do not fill it in. Ask.

## The game

Elitewake is an original open-world PvP and PvE pirate survival sandbox with realistic graphics, built in Unreal Engine 5.8. Players survive, gather, craft, sail, explore islands and ocean, hunt treasure, fight creatures and other players, tame animals, trade, and grow into more capable ships and equipment.

- **Core loop:** Prepare → Sail → Discover → Fight/Explore → Loot → Escape → Upgrade → Sail Farther.
- **Adventure interrupts routine.** Weather, treasure, hostile players, ghost ships, salvage, wildlife, caves and scarcity turn ordinary voyages into stories.
- **Ships are the center of play** and highly customizable. Land bases are allowed but temporary.
- **Player fantasy:** castaway → sailor → captain → pirate lord → legend. These are not fixed classes.
- **Small remains viable.** Solo players and small vessels keep useful roles.
- **Setting:** mid-1700s technology, roughly 1740–1760. No electricity or industrial machinery unless the owner approves a specific exception.
- **Originality:** ATLAS, ARK, Sea of Thieves and similar games are references for broad mechanics only. Elitewake uses its own code, models, textures, UI, names, dialogue and presentation.
- **NPCs are deterministic.** No generative AI for ordinary runtime NPC behavior.

**Retired, do not revive:** the "THE SHIP IS HOME" slogan, "Village" (now Port), the Davy Jones quest, the raft-and-shipyard prologue, the four-hour day and night, old currency ratios, +25 Health per point, the Magnum and its damage numbers, 15 skill points per level, farmable berries, species-specific Wood stacks, and Small Sail construction in the prologue.

## World

- **Regions:** five multi-island regions: Desert, Winter, Jungle, Plains and Swamp. Islands vary in shape and size, with substantial exploration space and longer voyages. Single player keeps neighboring regions accessible; multiplayer uses regional grids. Generation stays fixed for the saved/server world. The [October 14 decisions](WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md) define current geography, trees, caves, collision and climate; older ecology-guide region labels are provenance only.
- **Ports:** exactly one NPC trade Port per region, so five. Ports are PvP-safe, unclaimable and uncontestable, have specialized vendors, and connect to selected docks through Ferrymen. Functional shops are NPC-run only; players may build decorative shops. Each Port's island, identity and stock: TBD.
- **Time:** 90 real minutes of day, 90 real minutes of night.
- **Weather:** moving rain and snow clouds, darker ocean, foliage sway, rain fills crops and barrels. Other weather timings: TBD.
- **Ocean:** maximum depth 500 m below the mean surface. Several basins, with slopes and shelves rising toward islands. Six major reefs glow day and night (locations TBD). Light fades gradually with depth to a muted blue or navy; wrecks and navigation stay readable. No pitch-black water, flashlights or night vision.
- **Coastal test map (DECIDED, delegated, October 11):** until real art arrives the test coast is generated by script: a sand island and islet, an Unreal Water ocean with a swell under a metre that runs with the game wind (*tuning*), animated surf on the beaches, and no primitive-shape props. Survivors float head-out at the surface (buoyancy 1.3, *tuning*). Test maps may place a starter kit; normal starts still grant nothing.
- **Coastal plant life (DECIDED, delegated, October 12):** the test coast is a Western Tropical island, so it grows that region's plants from the ecology guide, built in the editor like the ships.
  - **Veyran Palms** first: about thirty behind the beaches of the island and islet, singly and in pairs. Each is a tree that gives Wood and Thatch to a hatchet at the existing test yields (12 Wood and 4 Thatch, 3 and 1 a strike, *tuning*); its fruit is visual until a Veyran fruit item exists.
  - **Hand-gathered plants:** low fern-like fiber plants and berry bushes in the open sand behind the beach, and piles of fallen sticks near the palms, gathered with Interact at the existing test amounts (10 Fiber, 6 Sticks, 10 berries, *tuning*). The bushes carry the existing test berry (Azren) until the region's Korri Berry item exists.
  - **Boulders:** about twenty on the higher ground and beach heads, shaped in the editor with a weathered dark stone and lichen. Each gives Stone to a pickaxe at the existing test yield (12, 3 a strike, *tuning*).
  - Trees and rocks are solid: survivors walk around trunks, not through them, and can climb onto low rocks.
- **Land bases:** temporary, and raidable by players only. Wild animals never attack player items or structures, except a tamed animal under a player's direct control. Base lifetime and raid mechanics: TBD.
- **Servers:** players never see a server grid. Official servers wipe, with progression rewards (schedule and rewards TBD). Unofficial servers set their own rules. Server settings are multipliers on the official value of 1.0 (2.0 doubles a duration). Up to 100 players and Linux dedicated servers are future targets.

## Survival

- **Stats:** Health (base 100, +50 per Health point), Stamina, Hunger, Hydration, body temperature and carried weight.
- **Stamina:** sprinting drains it; it recovers while standing or walking. A jump costs about 1/8 of the bar and is blocked if Stamina is too low. The "five-second" sprint and recovery baseline and how it scales with upgrades: TBD.
- **Hunger and Hydration:** empty from full in about 15 minutes. How activity and upgrades change that, and starvation damage: TBD.
- **Water:** drink directly from fresh sources with Interact. No need to lie prone. Salt water is harmful (effects TBD).
- **Injuries are separate from Health,** and the Surgeon treats them (gauze, bandages, stitches, splints, surgery).
  - Punching trees with bare hands injures them after 25 hits, and a bandage is needed. Without one, the injury becomes an infection after 10 in-game minutes, fatal without a Surgeon.
  - Counting, reset, treatment and the game-clock conversion: TBD.
- **Death:** carried items and equipment drop. Currency is kept. Sleeping bodies and ships are vulnerable offline; the Armored Shipyard is the only offline-protection exception. Wreck loot floats in crates for about 15 real minutes. Effect of death on level and skills: TBD.

## Resources and gathering

- **Universal gatherables:** Wood, Thatch, Fiber, Stone and Berries. Everything else is regional.
- **Wood is one inventory resource.** Regional trees and building styles look different but produce the same Wood.
- **By hand:** berries, plants (Fiber) and loose sticks, using Interact (E / X). Punching trees gives a little Wood, no Thatch, and causes hand injury.
- **With tools:** a hatchet gives more Wood plus Thatch; a pickaxe mines Stone and ore. Both use Attack (Left Mouse / RT).
- **Tool tiers:** Wooden starters, then Stone, then Metal, then Tungsten.
- **Ores and metals:** Copper, Tin, Iron, Silver, Gold, Lead, Zinc, Nickel and Tungsten. Alloys are Bronze, Brass and Steel; Nickel Steel is a later candidate. Tungsten appears only in deliberate dangerous late-game areas. Copper ore and Copper currency are different items. Placement follows regional geology. Distributions and yields: TBD.
- **Other material families:** fuels, minerals, cloth and rope, resins, oils and fats, dyes, soil and fertilizer, ceramics, marine and animal materials, medicine, paper and trade goods, ship components.
- **Names:** the Ecology Guide's resource and species names are approved (owner, October 7). Real animals keep real names, and their drops are named after them ("Black Bear Hide").
- **Animal drops follow anatomy.**
  - Mammals: Hide, plus fur, fat or bone where it makes sense.
  - Birds: Feathers.
  - Reptiles: Scales.
  - Frogs: Frog Meat and Frog Skin, plus a Toxin Gland if poisonous.
  - Tortoise shell and scales: TBD.
- **Stack sizes:**

  | Item type | Stack |
  | --- | --- |
  | Food | 500 |
  | Raw resources | 250 |
  | Fish Oil | 150 |
  | Handheld ammo | 100 |
  | Cannon ammo | 50 |
  | Fishing bait, Repair Kits, Bandages, Antidote, Sickness Serum | 30 |
  | Seeds | 20 |
  | Medkits | 10 |
  | Weapons, tools, armor, placeables, treasure maps, saddles | 1 |

- **Rarity:**
  - Items: Common gray, Uncommon green, Rare blue, Epic gold, Legendary dark purple. Names display as "Rare: Sailor Sword".
  - Treasure maps use their own colors: Epic purple, Legendary gold.
  - Ammunition never has rarity.

## Food and farming

- **Berries grow wild only.** No seeds and no farming.
  - Azren (formerly Azul): one restores 1/16 Hunger and 5% of maximum Health. Monkey taming food.
  - Marad (formerly Mary-Dash): Warthog and Manatee taming food.
  - Berries stay fresh for 20 real minutes, then become an inedible toxic crafting resource.
- **Crops:** Corn, Tomato, Beans, Sugarcane (the source of sugar), Potato, Carrot, Pumpkin. Rye stays Rye.
- **Orchards:** Apple, Pear, Peach, Plum, Cherry, Orange, Lemon, Lime, Coconut, Banana, Mango, Pomegranate, Date and Fig. Mature trees regrow fruit until they are chopped down.
- **Planting:** a crop must match its region. Planting in the wrong region uses up one seed, fails and explains why. Seed descriptions list compatible regions once discovered.
- **Water:** comes from rain, manual watering or rain barrels. Dry crops slow, then stop, then wither. Planters and fertilizer help.
- **Cooking:** progresses from basic foods to meals to preserved provisions, mainly for Hunger with modest extra benefits. Raw meat can cause sickness. Cooking uses period methods: open hearths, brick ovens and ship firehearths. Use the name "Food Cabinet", not "Food Larder".
- All food values, growth times and yields: TBD.

## Crafting and building

- **Five separate systems:** portable crafting, Build Mode, specialist stations, cooking, and NPC trade.
- **Inventory first:** campfires, storage chests and crafting stations are crafted into inventory, then placed.
- **Builder's Plan:** a reusable crafted item that opens Build Mode. It covers:
  - construction pieces and material variants
  - ship parts and platforms
  - cannon variants (the player cycles the type)
  - one diving attachment and one dinghy attachment
  - platform railings and decorations
  
  Placement shows a blue ghost when valid and red when invalid, and checks collision, ground and boundaries. Tolerances and the final name: TBD.
- **Stations:**
  - Smithy, with folders: Structures (Ammo Bin, shipyards), Storage, Weapons → Melee (Shovel, Sword, Torch, Glider), Ammo, Cannons, Tools.
  - Loom: sails, armor and sail repair. Sails require a Loom.
  - Tanner: required station. Recipes TBD.
  - Smelter or forge.
  - How stations overlap: TBD.
- **First regular recipes,** unlocked when the innkeeper introduction completes:

  | Item | Cost |
  | --- | --- |
  | Wooden Shovel | 20 Wood |
  | Wooden Axe | 20 Wood |
  | Wooden Pickaxe | 20 Wood |
  | Hide Water Flask | 1 Hide + 10 Thatch |

  The prologue separately teaches the **Repair Kit** (20 Wood + 20 Stone). One craft makes one item. Craft time, weight, durability and flask capacity: TBD.
- **Crafting screen:** each item has one icon used everywhere. The selected recipe shows a large preview, ingredient icons with owned and required counts, the station needed, and lock state. Locked families stay hidden or unobtrusive.
- **Catalog:** comparable in breadth to ATLAS, but every item is Elitewake's own. Boss summons, TEK-style technology and quest relics are excluded. Avoid duplicate items unless they serve distinct roles.
- **Trade:** prices and stock are data-driven and regional. Local abundance lowers buyback prices; scarcity raises resale prices. Values: TBD.

## Ships

- **Ships start as bare hulls** with no cannons or fittings. Players build fittings separately and attach them by hand. The first sloop has **two cannon hardpoints**: places a cannon can go, not two free cannons.
- **Hardpoints:** cannons go on fixed hardpoints only.
  - Side and lower gunports take cannons only.
  - Selected upper-deck hardpoints take a cannon or a utility attachment: the Diving Platform, or the Docking Platform that carries and hoists a dinghy.
  - Proposed cannon variant names (Light, Standard, Heavy) are not approved.
- **Sails:** Small, Medium and Large, made at the Loom. A schooner mounts 2 Medium, 1 Large and 3 Small.
- **Vessels:**
  - Raft: emergency craft; paddled, with no mast or sail (owner, October 12, replacing its earlier Small Sail); no cannons, no leveling.
  - Dinghy: no leveling; ordinary damage cannot sink it.
  - Sloop: crew up to 6 (player, Surgeon and 4 crew).
  - Schooner: crew is its configured cannons plus the player and Surgeon.
  - Brigantine: crew up to 25.
  - A larger multi-deck ship: TBD.
- **Upgrades:** ships earn sailing XP and upgrade only Crew Capacity, Weight/Storage, and Hull Health. Amounts: TBD.
- **Overload:** too much weight can sink a ship (timing TBD). Crew overload has a separate five-minute grace period.
- **Anchor and ladder:** hold Interact at the anchor. An anchored ship cannot sail, and the HUD shows anchor state. Ladders: see [Ship model v1](#ship-model), Crew and boarding.
- **Shipyards:** Small (Raft, Dinghy, Sloop), Medium (Schooner), Large (Brigantine), each crafted at Smithy → Structures. The late-game Armored Shipyard gives specific offline protection.
- **Ammo Bin:** storage only, cannon ammo only, 20 stacks of 50.
- **Ownership cap:** 8 ships per player, 20 per Company.
- **Naval combat:** should be readable: ammo types, mast, sail and rudder damage, flooding, fire, boarding, grappling and repair. A simple two-cannon fight comes before the deeper systems.
- **Cannons in play (DECIDED, delegated, October 14; the two-cannon fight's first step):**
  - A cannon is a fitting for a cannon hardpoint, installed like a sail. Once installed it is manned, not removed (removing it is a Builder's Plan action), as the helm is taken.
  - Hold Interact at an installed cannon to man it: the gunner stands behind the carriage and rides the ship. The view aims it, Left Mouse fires it, and Interact leaves it.
  - A manned cannon loads itself from the round shot its gunner carries, one shot at a time, in 5 s (*tuning*). It must be loaded to fire.
  - Its port limits its aim: 15 degrees either side, 5 down and 8 up on the sloop (*tuning*).
  - Round shot leaves the muzzle at 60 m/s (*tuning*) plus the ship's own way, and falls under gravity into the sea or against whatever solid it meets first, never its own ship. It does not strike people yet.
  - Cannon and round shot are test fixtures until their recipes, costs and variant names are decided (open question 1); round shot stacks to 50 (confirmed for cannon ammo).
- **Ghost ships** are hostile NPC vessels haunting several areas. They fire on players and stay visible on the map through fog. Ordinary enemy pirates are other players.
- **Technical rule:** each ship is its own authoritative actor. A player at the helm stays their own character; they do not become the ship.

<a id="ship-model"></a>

### Ship model v1 (decided under owner delegation, October 11, 2026)

The owner delegated these gap-filling decisions. Each is marked **DECIDED (delegated)**; the owner can override any of them. Numbers marked *tuning* are starting values for playtesting, not balance. The model follows ATLAS's "frame plus placed parts" idea while cutting its grind.

- **What a bare hull includes (DECIDED, delegated):**
  - the complete hull and decks; no plank-by-plank building
  - built-in masts with fixed sail mounts
  - a fixed helm mount
  - the cannon hardpoints and utility mounts
  - a built-in anchor and boarding ladder
- **What players fit (DECIDED, delegated):** the **helm** (ship's wheel), **sails**, **cannons**, **utility attachments** (Diving Platform, Docking Platform), storage, railings and decorations.
  - A ship needs a helm to steer and at least one sail to move. A bare hull floats and can be anchored, nothing more.
- **How fittings are obtained and placed (DECIDED, delegated):** this reconciles the inventory-first rule with the Builder's Plan.
  - Fittings are crafted into inventory at their station: sails at the Loom, helm and cannons at the Smithy.
  - The player installs a carried fitting at a matching empty mount. The fitting leaves the inventory only when the server accepts the install.
  - The Builder's Plan's ship section is the selection screen for this: choose a carried fitting, a compatible mount, and the cannon variant. The first build uses a simple Interact-at-the-mount step; the Builder's Plan screen uses the same server request later.
  - Removing a fitting returns it to the inventory if there is room; nothing is destroyed.
- **Mount sizes (DECIDED, delegated):**
  - Sail mounts accept their own size only.
  - The **first sloop** has one mast with a Medium mainsail mount and a Small headsail mount. It also has the two confirmed cannon hardpoints (port and starboard) and one helm mount.
- **Sail roles (DECIDED, delegated):** none in the first version; sails differ by size only. Handling, speed and cargo roles stay a RECOMMENDED later layer for when sailing is balanced.
- **Sailing (DECIDED, delegated):**
  - The helmsman uses forward and back to step the sails between three states (furled, half, full) and left and right for the rudder, which returns to centre when released.
  - **Sail trim (owner, October 12: sails should work on wind and movement like ATLAS):** the helmsman swings the sails with Sprint held and left or right (Shift+A/D on a keyboard, as in ATLAS). All of a ship's sails swing together, up to 85 degrees either side of the centreline at 45 degrees a second (*tuning*); they turn on their mast or stay and every screen shows them swung. The angle stays where it is left. A paddled boat has nothing to trim.
  - Wind has a world direction, the same on every machine. Speed depends on the ship's angle to the wind and on the trim (DECIDED, delegated): the best angle has the sails out on the side the wind blows toward, square across running before it, half way out with it on the beam and in along the centreline heading into it. Well trimmed, a ship makes full speed running downwind; badly trimmed, or heading into the wind, never less than about 30%, so it can always make headway. Trim quality falls off sharply: about 70% a quarter of the way off, nothing from 60 degrees off (*tuning*).
  - At the helm the camera stands back over the ship so the helmsman sees the sails and the water ahead, and a trim bar under the compass shows the sails' angle, the best angle and how well they draw (DECIDED, delegated).
  - More and larger sails raise top speed; carried weight lowers it (*tuning*).
  - The rudder turns best with way on, but keeps 20% of its effect when stopped, so a ship pinned against a shore can always turn away (*tuning*).
  - The helm shows it: the sloop's wheel turns on its axle (270 degrees hard over) and the dinghy's rudder and tiller swing on their post (35 degrees), on every screen (DECIDED, delegated, October 13; *tuning*).
  - The rudder blade swings over rather than snapping: centre to hard over in 0.8 s, so a ship eases into and out of a turn (DECIDED, delegated, October 13; *tuning*).
  - Holding Interact at an installed helm takes it. The helm itself is removed through the Builder's Plan, not by Interact.
- **Crew and boarding (DECIDED, delegated):**
  - Survivors stand and walk on deck while the ship sails, and ride with it.
  - A built-in boarding ladder on each side lets a swimmer, or someone on a dock, climb aboard.
  - **Climbing (owner, October 12):** press Interact once to take hold of the ladder, then Up and Down (arrow keys, W and S, or the D-pad) climb it. At the top the survivor steps onto the deck by themselves; at the foot, or with Jump, they let go into the water (DECIDED, delegated). Climbing speed 1.3 m/s (*tuning*).
  - **Ship markers (DECIDED, delegated, October 12; the owner asked for indicators because mounts were hard to find):** within 14 m of a ship (*tuning*) the screen labels its places to act. Aboard: each mount with the size of sail it takes, or "Wheel mount" (amber while empty, green with "Fit ... here" while the survivor carries a fitting that fits, white once fitted), the anchor with what Interact will do, the hold, and nearby empty cannon ports. From outside: the anchor and the ladders on the near side only, so nothing shows through the hull. The place under the survivor's aim is drawn larger, and labels that would overlap are stacked.
  - Leaving is just walking or jumping off the side.
  - People never block a moving ship.
- **Swell and heel (DECIDED, delegated, October 13; the owner asked to fix the boats' movement):** every ship rocks gently on the swell, at anchor too: a sloop rolls about 1.4 degrees, pitches 0.8 and rises 6 cm, and smaller hulls rock more (up to twice). Under sail it also leans to leeward, up to 6 degrees for a sloop at full sail with the wind well used, easing in and out. Each ship rides its own swell, and movement follows the heading only (*tuning*).
- **Wake (DECIDED, delegated, October 13):** a moving ship trails foam on the water: churned water close behind the stern and two broken foam lines spreading from it, growing with speed (full at top speed) and fading when it stops, the same on every screen.
- **Ship sizes (owner, October 12):** the dinghy is the smallest boat and the raft a little bigger; the sloop, schooner and larger ships are considerably larger again. Working lengths (*tuning*): dinghy about 3.5 m, raft about 5 m, sloop about 14 m, schooner about 22 m, brigantine about 30 m; the larger multi-deck ship steps up from there.
- **Raft and dinghy (DECIDED, delegated, October 12, from the owner's art):**
  - Both steer by fittings built into the hull, fitted when the boat enters play and never removed: the raft's paddles, and a rudder and tiller on the dinghy. Neither takes a ship's wheel.
  - **The raft is paddled (owner, October 12):** no mast, sail or steering oar. Its two paddles rest on the side rails; taking them up is taking its helm. Forward and back set the stroke (resting, easy, hard) and left and right steer. Paddling ignores the wind. Top speed 2.5 m/s at a hard stroke (*tuning*). A paddling animation is still to come.
  - The dinghy has one Small sail mount on its own short mast and boom. A mount can set how a fitting looks on that hull, so the same Small sail is the sloop's jib but sets on the raft's or dinghy's own mast.
  - Their holds are a lashed crate on the raft (8 slots, 400 kg) and a sea chest under the dinghy's aft thwart (6 slots, 250 kg); both have an anchor at the bow and boarding points on each side (*tuning*).
  - Raft top speed 2.5 m/s paddled, dinghy 4.5 m/s, sloop 7 m/s (*tuning*).
- **The sloop's hull (DECIDED, delegated, October 12, from the owner's sloop art):**
  - About 14 m long and 5 m in beam, double-ended: the stern mirrors the deep curved bow, each rising to a post, with no square transom (owner, October 12). Low bulwarks with a rail and posts, one gunport each side, side ladders clear of the gunports, and a planked, tarred hull (*tuning*).
  - The deck stands 2.5 m above the waterline. Beneath it a cramped hold has 2 m of headroom, reached by stairs through the cargo hatch. The hold floor sits above the swell, so the sea neither shows nor counts as swimmable inside a ship; every ship with a hold follows this rule.
  - Hulls are built by script in the editor (`Scripts/Setup/build_sloop_hull.py`), not bought or generated, so they can be reshaped and re-run.
  - The mast, bowsprit and standing rigging come with the hull. The mainsail fitting brings its boom and gaff; the jib hangs on the forestay. Sails show the helmsman's setting: rolled on their spars when furled, shortened at half, fully set at full. The owner's sail art is the cloth itself. Crew walk on the hull itself; the bulwarks keep them aboard, and a jump clears the rail.
- **Larger ships on hold (owner, October 12):** the schooner and brigantine below are taken out of the game while the owner supplies better designs; work focuses on the raft, the dinghy and the sloop first.
- **The schooner (DECIDED, delegated, October 12, from the owner's schooner art):**
  - About 22 m long and 6.6 m in beam. It is double-ended like the sloop, following the owner's dislike of a square stern (*tuning*).
  - It keeps the art's raised aft deck, raised to 2.2 m above the main deck so a full-height captain's cabin fits under it (owner request, October 12), with stairs up each side and a breast rail (*tuning*).
  - **Captain's cabin:** under the raised aft deck, entered by a doorway from the main deck. It is lit by three windows in each hull side, two in its front wall and a skylight grating in the deck above; the mizzen mast passes through it. It is a bare room: furniture and storage are later fittings.
  - **Rig:** three masts stand in the art's three mast sockets. The six sail mounts follow the confirmed schooner rig of 2 Medium, 1 Large and 3 Small:
    - a Large square topsail on the foremast,
    - Medium gaff sails on the main and mizzen masts,
    - three Small jibs on stays out to the bowsprit.
  - **Guns:** twelve cannon hardpoints, six a side, at gunports on a lower deck under the main deck. This matches the prologue schooner's 12 cannons.
  - **Lower deck:** reached by stairs through the main hatch. It has about 2.4 m of headroom (*tuning*), pillars, a mast step at each mast, and an aft bulkhead with a doorway into a small aft hold. Its floor sits above the swell.
  - **Helm:** on the raised aft deck. A helmsman always stands on whichever deck is under the wheel.
  - **Crew capacity:** 14, the twelve cannons' crews plus the player and the Surgeon, reading "its configured cannons" as the full fit. Whether capacity drops when fewer cannons are fitted stays an open question (see item 9 below).
  - **Handling:** top speed 8 m/s, turn rate 22° per second, hold 40 slots and 4,000 kg (*tuning*).
  - **Sail looks:** each sail mount sets how a sail of its size looks on that rig, so the same Small, Medium and Large sail items fit any ship.
  - **Built by script:** `Scripts/Setup/build_schooner.py`, from the shared hull builder `ship_hull.py` that also draws the sloop.
- **The brigantine (DECIDED, delegated, October 12, from the owner's brigantine art and its mast-socket revision):**
  - About 30 m long and 8.4 m in beam: stout and ocean-going, clearly larger than the schooner, and double-ended like the other hulls (*tuning*).
  - **Decks:** as in the art, a raised forecastle at the bow (2 m) and a raised quarterdeck at the stern (2.2 m), each reached by stairs up both sides. Under the quarterdeck is the captain's cabin; under the forecastle, the crew's quarters, each through a doorway from the main deck with windows in the hull sides.
  - **Guns:** a single gun deck under the main deck carries the prologue brigantine's 24 cannons, twelve a side, reached by stairs through the main hatch, with small holds through doorways at each end.
  - **Rig:** two masts in the art's two sockets. The foremast is square-rigged with a course and a topsail; the mainmast carries a gaff mainsail with a square topsail above it. That makes four Large sail mounts, matching the prologue brigantine's four large sails. Two Small headsails set on stays to the bowsprit, because a square-rigged ship without them is unseaworthy.
  - **Crew** up to 25 (confirmed). **Handling:** top speed 7.5 m/s, turn rate 16° per second, hold 60 slots and 8,000 kg (*tuning*).
  - **Built by script:** `Scripts/Setup/build_brigantine.py`, from the shared hull builder.
- **Working detail on every hull (DECIDED, delegated, October 12, owner asked for more realistic ships):** shrouds end in deadeyes on channels outboard of the rail, carried by iron chainplates, with ratlines between them; pin rails at each mast; a rudder hung on the stern by iron pintles; and an anchor catted at each bow. These are part of the hull and do nothing yet: the rudder's movement, anchors that drop and climbable ratlines are later work.
- **Anchor (DECIDED, delegated, within the owner's hold-to-anchor rule):**
  - Each ship has a built-in anchor capstan on deck. Anyone aboard holds Interact there to raise or drop the anchor.
  - Working the capstan takes a 3 s hold (*tuning*; fittings take 0.75 s). Meanwhile the survivor leans into its bars and its head turns, faster when the anchor is let go, and every player sees both. The raft's stone and the dinghy's grapnel have no capstan and keep the short hold.
  - Ships start anchored, so a moored ship never drifts.
  - An anchored ship cannot sail, whatever its sails are set to. Dropping anchor under way drags the ship to a stop within about 2 seconds (*tuning*), with no damage for now.
  - The helmsman's prompt shows "Anchored" while it is down. The trim bar shows the sails; a full ship HUD (speed, anchor, hull) comes with the HUD art pass.
- **Cargo hold (DECIDED, delegated):**
  - Every ship has a built-in hold, separate from what survivors carry. Its slot count comes from the ship definition (the sloop has 20, *tuning*); Weight/Storage upgrades will raise it.
  - Hold Interact at the cargo hatch on deck to open the hold beside your inventory, then move whole stacks across.
  - Anyone aboard, or standing at the hatch, can use it. Who may use a ship's hold once ownership and Company permissions exist: TBD.
  - Moves are all-or-nothing on the server: only what fits leaves your inventory. Ageing food keeps its age, so storing it never refreshes it.
  - Placeable storage containers on deck are a separate, later fitting.
- **Weight and overload (DECIDED, delegated, within the owner's rule that overload can sink a ship):**
  - Ship load is everything in the hold plus installed fittings. A survivor's carried weight is not ship weight.
  - Each ship definition sets a weight capacity (the sloop carries 1,500 kg, *tuning*); Weight/Storage upgrades will raise it.
  - Speed: full up to half capacity, easing to 60% when full, and 40% when overloaded (*tuning*).
  - Overloaded ships get a warning and 60 seconds to lighten (*tuning*). After that they are swamped and cannot sail until lightened below capacity.
  - Actual sinking (losing the ship, floating wreck crates) comes with the hull damage and flooding system, which shares the same wreck rules. Until then overload is never destructive.
  - The server owns all ship movement and steps it in fixed small increments, so speed never depends on frame rate. Helm controls are held as the player's last chosen state, never as input that expires after a fixed time (the lesson from the deleted prototype).
- **Hull health (DECIDED, delegated):** one hull-health pool, upgraded through Hull Health. Holes, flooding and part damage layer on later.
- **Starter ship (DECIDED, delegated):** no cheap pre-built sloop for now. The prologue dinghy and the craftable raft are the starter boats, and the sloop needs a Small Shipyard. Revisit if playtests show the jump to a sloop is too steep.

## Ocean life and diving

- **Diving Platform:** burns Fish Oil, one unit per 90 seconds, from a 100-unit slot. Divers are on a tether: unlimited vertically, horizontal limit TBD.
- **Tether safety:** sea creatures ignore tethered divers unless attacked, except reef sharks, which can attack them.
- **Where things live:**
  - Bass and Catfish: freshwater ponds and lakes.
  - Piranha: freshwater, aggressive.
  - Manta: aggressive, with a tail strike.
  - Manatee: peaceful, warm water, tamed passively with Marad.
  - Great White, Hammerhead and Squid: aggressive.
  - Sirens: always hostile, never tameable, around level 45–50.
- **Sea creatures in play (owner, October 12: implement fish and make them harvestable, from the owner's art):**
  - Bass, catfish, piranha, manta ray, manatee, great white, hammerhead and squid, each built from the owner's painting of it (`Art/Concepts/Fish/2026-10-12`): the art cut from its background and its outline rounded into a body, swimming by a tail sway or, for the manta, a wing beat.
  - Habits follow the list above. Aggressive kinds go for a swimmer who comes near and bite, sting or grab; they give up when the swimmer leaves the water (DECIDED, delegated). Peaceful kinds dart away when struck. Survivors may now swing while swimming, to fight back (DECIDED, delegated).
  - A killed creature floats up belly-first; Interact harvests it for Raw Fish, or Raw Meat from a manatee (DECIDED, delegated: manatees are mammals). Whatever does not fit stays on the body. It returns to its home 5 minutes after dying (*tuning*). Raw Fish and Raw Meat are items now; eating them (10% health and sickness, confirmed) waits for the cooking and raw-food pass, and the Fillet Knife's Fish Pieces (yield TBD) for fishing.
  - Working numbers (*tuning*): health from 15 (bass, piranha) to 400 (great white); a great white bites for 25 every 1.5 s, a hammerhead for 20, a manta stings for 15 every 2 s, a squid grabs for 12, a piranha bites for 4. Sharks notice a swimmer from 13–15 m, mantas from 6 m. Yields: bass 2, catfish 3, piranha 1, manta 6, squid 6, hammerhead 10, great white 12 Raw Fish; manatee 12 Raw Meat.
  - The coastal map is salt water: three mantas, three manatees, two of each shark and three squid live around the island and islet, the aggressive ones at least 35–60 m from the spawn, the dock and the moorings.
  - The island's spring is a freshwater pond 14 m across and 2.6 m deep in the middle (DECIDED, delegated; *tuning*), where three bass, two catfish and two piranhas live. Survivors swim in it, drink from its bank on the side facing the beach, and the piranhas go for a swimmer there.
  - Taming manatees, sirens, fishing with a pole and diving gear are later work.
- **Treasure:**
  - Floating crates and sunken treasure can hold currency, scaling with treasure level, risk and difficulty (amounts TBD).
  - Treasure maps come in bottles. Dig with a shovel; on cave maps, X marks the treasure, not the cave entrance.
  - The harpoon gun works only underwater. The glider (crafted at the Smithy) gives a controlled descent, not flight.

## Creatures and taming

- **Wild animals** have no hunger or thirst. Predators start fights with other wildlife; passive and neutral animals defend themselves. Damage and death are real. Health bars show only nearby.
- **Taming:**
  - Health and unconsciousness are separate.
  - Each valid tranquilizer hit adds 2 real minutes of knockout (it stacks) and deals real damage.
  - Aggressive species can only be fed at 25% Health or less, once incapacitated or contained. Passive and neutral species can be fed at full Health.
  - Waking restores hostility. Cages block movement; frustration animations do not damage anything.
- **Caps:** 25 tames per player and 75 per Company. Personal tames count toward both.
- **Ownership:** every tame can be named and released. A released animal turns wild, wanders off and disappears, and can be recaptured before then.
- **Roles:** predators fight; rideable predators need their own species saddle. Passive and neutral animals do utility, transport and breeding.
- **Breeding:** compatible species pass on stats, looks, temperament, abilities and size, with possible mutations. The lineage view starts at the selected animal, scrolls sideways through ancestors, and opens a details pop-up for any ancestor. Genetics values: TBD.
- **Known roster:**
  - Monkey: desert; tamed with Azren.
  - Warthog: tamed with Marad.
  - House Cat: Port wildlife; tamed with Bass; rides on your shoulder.
  - Horse: jungle; food TBD.
  - Black Bear: winter islands.
  - Grizzly Bear, Rhino and Elephant: neutral.
  - Snow Leopard: cold regions.
  - Tiger and Lion: jungle.
  - Giant Spider: caves in every region, levels 1–70; climbs walls and ceilings.
  
  The full roster is in the Ecology Guide.
- **Commands:** Follow All, Follow One, Stop All and Stop One, plus job assignments. Hold Middle Mouse or D-pad Right.

## Progression

- **Levels:** cap 80. Each level gives 1 character stat point and 7 skill points. Level 80 cannot unlock everything.
- **Respec:** available at levels 10, 15 and 20, then every 5 levels, for 2 Gold. Baseline recipes survive a respec.
- **Skills:** ten constellations of ten skills each (100 total): Survival, Building, Cooking, Farming, Smithing, Weapons, Seamanship, Medicine, Trade and Beast Mastery.
  - Opening Skills pans the view up into a night sky; the player picks a constellation, then its connected skill stars. Honkai: Star Rail's skill screens are a presentation reference only.
  - Effects, costs and connections: TBD.

## Combat

- Fists deal 10, a Common Sailor Sword 20. Damage values are fixed and data-driven, not percentages.
- The period pistol stays (the old Magnum is reworked; name and stats TBD).
- Rifles use bullets and tranquilizer darts. Longbows and crossbows use regular and tranquilizer arrows. Harpoon ammo is separate.
- Simple melee and a small enemy encounter come before deeper combat.
- **Simple melee (DECIDED, delegated, October 12):**
  - Attack swings once a second (*tuning*), with a swing everyone sees.
  - What it does depends on the target:
    - A tree or rock with the right tool equipped is gathered, as before.
    - Anything else takes a strike at the first survivor within 1.7 m in the direction the attacker looks (*tuning*). Walls and hulls in the way block the strike.
  - A strike deals the confirmed fist damage of 10 and makes the target flinch. Tools strike as fists until tool and weapon damage values are set.
  - No swinging while prone, on a ladder or at a helm. Swimmers may swing, to fight sea creatures (October 12).
  - Whether Company members can hurt each other: TBD.

## Economy

- **Currency:** 500 Copper = 1 Silver, and 30 Silver = 1 Gold, converted automatically. It weighs nothing and is kept on death.
- **Crew wages:** NPC crew are paid in physical Copper. How NPC loot converts to currency: TBD.
- **Vendors:** regional stock, prices and restocking are data-driven (values TBD). Ferryman fees and limits: TBD.

## Prologue and onboarding

1. Far out at sea, the player's schooner (12 cannons, 2 Medium Sails) is attacked by a brigantine (24 cannons, 4 large dark-red sails).
2. The player bails water, fails to stop the boarding, fights, takes a head wound, loses their sword and falls unconscious.
3. The Quartermaster escapes with them in a dinghy, carrying a case of rare Rye.
4. The player wakes on an island by day with amnesia. The Quartermaster gives them his Journal, which lives permanently in the Journal menu, not in inventory.
5. The player gathers resources and crafts a Repair Kit (20 Wood + 20 Stone) to repair the dinghy.
6. The dinghy sails to the Port. The ELITEWAKE title is revealed letter by letter during an afternoon sky shot with a seagull.
   - Sail construction is no longer part of the prologue. How the dinghy becomes seaworthy without it: TBD.
7. Tutorial tools and supplies are discarded. The player starts normal play with zero currency but keeps the Rye.
8. At the Port, the Quartermaster leaves. The player asks the innkeeper for a free night. She says it must be earned through work or trade, then tours the town square and introduces the shopkeepers (their quests come later).
9. The general merchant offers to buy the Rye. When the introduction completes, the player receives 250 Copper and the four regular recipes.
10. After the first night at the inn, each player can take one wall torch. Looking at it shows "ye, this looks like it will be useful", and it stays highlighted until taken.
11. Homestead chores follow: wood to the shed, a seed bag to the garden, a hoe or plow, seeds and a watering can. They earn soil, seeds and a Small Farming Plot.
12. A parrot-bonding tutorial follows.

Room price, dialogue, the storm line, and whether the torch or the Rye counts as the first carried item: TBD.

- **Title screen (owner, October 13; updated later October 13):** the game opens on the exact supplied dock-at-dawn image (`Art/UI/Title/2026-10-13/Elitewake-Starter-Screen-Owner-v1.png`), retaining its ELITEWAKE and START YOUR JOURNEY lettering. Add “PRESS ANY KEY TO START” at bottom center in a matching serif; it pulses and any key or click advances to the separate main menu. Animate only the water, including shore foam, using a mask; keep the sky, sunlight, ship, survivor, dock, coastline, and all text still. Single Player then loads directly into the normal game. This changes only the front-end title treatment; the prologue's letter-by-letter title reveal over the afternoon sky stays as written.
- **Character creation (owner, October 13: characters and their customization right after Start Your Journey):** the survivor is made on the end of a dock at dusk. Choices (DECIDED, delegated): body (a man or a woman for now), colouring (six skin tones, fair to deep) and height (92-108%, *tuning*); drag to turn the survivor. Set Sail opens the coast. The look is remembered for the next launch, sent to the server when the survivor arrives, kept within what the roster offers, and seen by every player.
  - The bodies are the Unreal mannequins as stand-ins. The owner's own characters were not on disk on October 13; MetaHumans made in MetaHuman Creator share the mannequin skeleton and are the recommended route if they cannot be used. New bodies are added to the roster asset without code. Faces, hair and clothing choices come with real bodies (TBD).

## Company and multiplayer

- **Company** is the player group. ATLAS's Company page is a mechanics reference only.
  - Ranks; promote, demote, remove and leave.
  - Leadership transfer, crew groups, alliances, activity logs and governance. Mergers come later.
  - Only the Company owner can rename it; server admins cannot.
- **Asset policies:** leaders choose personal, personal with shared access, or Company-owned, separately for ships, structures and tames. Sharing access never transfers ownership.
- **Nameplates:** friends green, allies light blue, enemies red; your own is hidden.
- **Owner revision, October 14:** Company island claim/contest flags are multiplayer-only; single player has no claim ownership gates. NPC Port islands are excluded. Claim flags rise during the claim timer; a nearby rival starts a contest, whose successful expiry removes the original flag before the challenger's claim timer starts. Durations, proximity and interruption/defense rules remain TBD. See [Multiplayer rules](MULTIPLAYER_RULES.md). Taxation and top-company bonuses remain unadopted; no additional permanent-ownership policy is inferred.
- **Communication:** text and proximity voice. Mute, block and report must exist before any public launch.
- **Private testing first:** the owner hosts a listen server and one approved tester joins. Test locally, then on LAN, then over the Internet. Distribution later goes through a restricted itch.io page with Butler. There is no Epic Games Store release.
- **Undecided:** can other players see a survivor's inventory (it currently replicates to everyone)?

## Controls and menus

All inputs use Enhanced Input and must be remappable. Prompts follow the last device used.

| Action | Keyboard / mouse | Controller |
| --- | --- | --- |
| Move / Look | WASD / Mouse | Left / Right stick |
| Sprint | Left Shift | L3 |
| Jump | Space | A |
| Crouch / Prone | Tap C / Hold C | Tap B / Hold B |
| Interact (tap or hold) | E | X |
| Attack / Fire | Left Mouse | RT |
| Aim | Right Mouse | LT |
| Reload | R | RB |
| Inventory | I | Y |
| Map | M | TBD |
| First / third person | Z | — |
| Hotbar | 1–8 | Hold LB + face buttons / D-pad |
| Command radial | Hold Middle Mouse | Hold D-pad Right |
| Back / Close | Tab | B |
| Pause | Escape | Start / Menu |

- **Menu:** translucent panels over the live world. Sections are Inventory, Crafting, Building, Skills, Company, Tames and Journal. Inventory sits above crafting on the left, survivor status in the middle, item details on the right. Large item grids, in the direction of ARK: Survival Ascended.
- **HUD:**
  - A centered eight-slot hotbar with transparent cells and silver outlines; the selected slot is brighter and thicker, and every assigned slot shows its item image.
  - Left side, five stat icons that fill from the bottom and keep an outline when empty: red heart (Health), yellow lightning (Stamina), blue flask (Hydration), gray weight (carried weight), orange meat (Hunger). The owner wants detailed painted icons here.
  - Right side: condition notices with timers.
  - No minimap.
  - **Compass (owner, October 12):** a straight strip across the top of the screen. The bearings (N, NE, E and so on, with degree marks between) scroll past a fixed centre mark as the view turns, and the bearing faced shows under it. The wind is marked where it blows from. North is the map's up.
- **Map:** M shows the surrounding area. You can walk but not sprint, change stance, use the hotbar or open inventory, and the world keeps running. Fog-of-war discovery and ghost-ship markers are planned. The HUD compass is in (see HUD); a physical compass item is not.
- **Pause:** in single player it freezes the world and hides the HUD. In multiplayer it does not.
- **Camera:** third person by default; Z toggles first person.
  - **First-person body (owner, October 13: see your arms and hands, look down at your feet when crouched, realistic movement):** in first person you see your own body, with only your head hidden. The eyes ride on the body: down with a crouch, low when prone, along with a climb. They lean out over the chest when you look down, so your legs and feet come into view. Your arms and hands show as they swing and work. The body turns with the view, so walking sideways or backward steps that way. On a ladder or at a helm the body keeps to the ladder or the helm. Everyone else sees you whole.
  - DECIDED (delegated, *tuning*): the eyes keep up with the body up and down but follow it across slowly, so a stride or a swing reads as a sway, not a lurch; motion blur is light in first person; the swings' root is locked, so a swing no longer carries the body a metre out of place.

## Audio and animation

- **Audio** must be original or properly licensed, and match what is on screen:
  - waves, rain, thunder with distance, wind, rigging and hull creaks
  - footsteps by surface; animals with real-world calls
  - harvesting, cannons and fishing
  - short contextual crew shouts, with no random chatter
  
  NPC voices must differ from player voices. Licensed AI voices are allowed; cloning real people is not.
- **Held tools (owner, October 12: hotbar items must show in the hand and work):** whatever is in the main hand is held in the right hand on every screen, built in-engine: the wooden axe, wooden pickaxe and wooden shovel of the starter kit, the iron hatchet and pickaxe, and the inn torch. The shovel and the torch are now main-hand items too, and the torch casts a warm light while held (DECIDED, delegated). With a tool in hand, Attack plays an overhead chop instead of a punch; the chop is made for Elitewake from the mannequin's idle (`Scripts/Setup/build_tool_swing.py`), as the project had none.
- **Helm animations (DECIDED, delegated, October 13):** a helmsman holds the wheel or tiller with both hands; on the raft they take up a paddle and stroke with it, side to side, faster at a hard stroke than an easy one, and hold it still at rest. Both are made for Elitewake on the mannequin skeleton (`Scripts/Setup/build_crew_animations.py`).
- **Ladder animations (DECIDED, delegated):** a survivor on a ladder plays the animation library's ladder loops, climbing up, climbing down or holding on, judged from how they move, so every screen shows the same climb.
- **Animations needed:** swimming, digging, eating and drinking, aiming, firing and reloading, helm, anchor and cannons, station use, medical treatment, and first-person versions; the tool chop, ladder climbing, holding the helm, paddling and pushing a capstan are in.

<a id="open-questions"></a>

## Open questions

Decisions that block or shape upcoming work. Ask the owner; do not assume.

1. **Ship fittings:** recipes and costs, cannon variant names, and Loom and Tanner recipes and how they overlap. How fittings are obtained and placed is settled by the [ship model](#ship-model).
2. **Prologue:** how the dinghy reaches the Port now that sail-building is removed; torch versus Rye as the first carried item; room price.
3. **Inventory privacy:** should other players see your inventory?
4. **Survival scaling:** the five-second stamina baseline at higher capacity; needs drain under activity; starvation and dehydration damage.
5. **Hand injury:** hit counting and reset, treatment steps, and the length of an in-game minute.
6. **Land bases:** lifetime, decay and raid mechanics.
7. **Ports:** which island, identity and stock each Port has.
8. **Servers:** wipe schedule and rewards; which rules unofficial hosts can change.
9. **Ships:** crew caps as starting values or absolute limits; schooner crew when fewer cannons are fitted or a utility attachment replaces one; starter raft recipe versus Small Shipyard.
10. **Combat and death:** pistol name and stats; level and skill effects of death; bed cooldown.
11. **Content values:** flask capacity, tortoise drops, horse and bear taming foods, and all yields, weights and prices not listed above.
