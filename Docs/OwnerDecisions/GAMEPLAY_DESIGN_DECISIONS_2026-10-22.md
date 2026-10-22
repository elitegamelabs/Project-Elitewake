# Owner decisions — gameplay design specifications (October 22, 2026)

Source: the owner's "Gameplay Design Decisions & Development Direction" message. These are **approved initial design targets for implementation and balancing, not
necessarily final production values.** Implement systems so values can be rebalanced without rebuilding them (configurable data). Prioritize world, survival,
progression and functional gameplay over advanced ship development. Report technical limitations and status accurately. They answer the open questions on food,
ship recipes, repair, tree regrowth and island claims, and supersede any older conflicting value.

## Decisions waiting on implementation

### 1. The five islands
One naturally generated island per region for initial testing: Plains, Winter, Swamp, Desert, Jungle. Each has its own environment, wildlife, resources, hazards and
exploration opportunities. **Plains is the universal start.** These five test environments, gathering, wildlife, survival and sailing between regions. More islands later.

### 2. Cooking, food and sickness
A 100-point hunger system. Cooked foods also give small health.

| Food | Hunger | Health |
|---|---:|---:|
| Raw fish | +8 | 0 |
| Cooked fish | +20 | +3 |
| Raw meat | +12 | -3 |
| Cooked meat | +30 | +5 |
| Fresh berries | +6 | 0 |
| Cooked berry dish | +15 | +2 |

Raw fish: 15% chance of food sickness; raw meat: 25%. Fresh berries are safe unless poisonous.
**Food sickness:** lasts 3 real minutes; stamina regeneration -30%; thirst depletion +50%; occasional nausea and minor visual distortion; cured early by medicinal
herbs or a crafted remedy; never kills by itself. Cooking takes 5 to 12 seconds by recipe. Advanced recipes unlocked by the skill tree give temporary stamina,
temperature resistance and health regeneration bonuses.

### 3. Ship crafting recipes (specifications for later; NOT authorization to resume advanced shipbuilding now)
| Item | Requirements |
|---|---|
| Small sail | 80 Fiber, 40 Cloth, 25 Wood, 10 Rope |
| Medium sail | 150 Fiber, 80 Cloth, 60 Wood, 25 Rope |
| Large sail | 300 Fiber, 160 Cloth, 120 Wood, 50 Rope, 20 Iron |
| Ship wheel | 100 Wood, 30 Iron, 20 Fiber, 10 Leather |
| Cannon | 120 Iron, 40 Wood, 30 Bronze, 20 Fiber |
| Tier 1 Shipyard | 500 Wood, 250 Fiber, 150 Stone, 80 Rope |
| Tier 2 Shipyard | 1,200 Wood, 600 Stone, 400 Fiber, 250 Iron, 100 Rope |
| Tier 3 Shipyard | 2,500 Wood, 1,200 Stone, 800 Iron, 500 Fiber, 300 Rope, 150 Bronze |
Each tier unlocks larger construction and better components. Recipes integrate with the skill tree and the resource economy.

### 4. Repairing ship damage
A craftable **Shipwright's Hammer**: 30 Wood, 15 Stone, 10 Fiber, 5 Iron. Repairing one damaged hull opening needs 20 Wood, 10 Fiber, 5 Resin, 5 Iron. Repairs take
5 seconds (minor) or 10 seconds (major); materials are consumed only on successful completion; major holes may need several repair actions. Temporary emergency
patches stop most water but do not restore structural integrity; permanent repairs restore hull durability. Repairs can be done aboard, including while sailing;
repairing under attack is harder.

### 5. Tree regrowth
Trees regrow **20 real minutes after being fully harvested**. Felled logs stay interactable for 5 minutes before despawning, unless fully harvested earlier.
Regrowth happens without players nearby, is blocked by player-built structures, and is consistent across multiplayer sessions.

### 6. Multiplayer island claims
A claim-and-upkeep system. Players need a Company to claim. **The Plains starting island is permanently neutral and cannot be claimed.** A claim needs a crafted Claim
Banner and 500 Gold, and 30 uninterrupted minutes to establish. Upkeep 100 Gold per 24 real hours; a Company can prepay up to seven days. A claim is abandoned and
contestable after 72 hours without upkeep. Active claims can be challenged in an announced daily 2-hour vulnerability window; contesting needs a rival Claim Banner and
30 minutes of capture progress; defenders interrupt by controlling the capture zone. 48-hour protection after a successful capture. Ownership limits scale with Company
size. PvE servers do not allow hostile takeover of maintained territory. **During the five-island test phase claims are optional or simulated so no region is ever blocked.**

## Gameplay vision by area

### 7. The first 30 minutes
Discovery, manageable danger and meaningful progression without heavy tutorials. 0-5: create a character, arrive on Plains, explore, collect basics, learn movement and
interaction. 5-10: wood, stone, fiber, berries, fresh water; first stone tool and basic survival gear. 10-15: catch or hunt small wildlife, make a campfire, learn cooking.
15-20: basic clothing, a weapon, a shelter; inventory, stats, needs. 20-25: gain experience, level up, allocate a stat point, unlock the first constellation node, discover a
recipe. 25-30: explore farther, find a point of interest or reward, a natural introduction to the journal, map exploration and future sailing. The player should end feeling
capable and curious, not punished by constant survival penalties.

### 8. Survival and character mechanics
Health, hunger, thirst, stamina, temperature and environment. 100-point hunger and thirst: hunger empties in about **45 minutes** of ordinary activity without food; thirst
in about **25 minutes**; heat, exertion and cold change the rates. At zero hunger or thirst, health falls gradually (not instant death). Extreme temperatures reduce stamina
regeneration and eventually damage health. Injuries can cause bleeding, slower movement or weaker combat; bandages treat bleeding, medical supplies treat serious conditions.
Death: the black fade, icy edges and respawn choice; respawn at a safe randomized place in the same region, a meaningful distance from the death site; a recoverable inventory
bag stays at the death location for **30 real minutes**; essential quest items are protected.

### 9. Gathering and crafting
Early resources are plentiful. Starter progression: stone axe and pickaxe, a basic weapon, campfire, water container, simple clothing, basic shelter, storage chest, crafting
station. Advanced resources (quality metals, rare timber, special fibers, medicinal ingredients, unusual minerals) need exploring more dangerous regions. Gathering uses
believable animations and rewards tool upgrades and skills. Every unlockable item connects to its skill node and shows a materials panel.

### 10. Regional island identity
- **Plains (start):** rolling grassland, scattered forest, rivers, freshwater lakes, gentle coast. Deer, rabbits, boars, birds. Plentiful wood, stone, fiber, berries, basic minerals. Moderate weather, low-to-medium danger.
- **Winter:** snow forests, frozen lakes, ice cliffs, mountains. Wolves, elk, bears. Fur, ice-region minerals, rare timber, cold-water resources. Hazards: freezing, blizzards, poor visibility.
- **Swamp:** marshes, murky water, mangroves. Crocodiles, snakes, amphibians, insects, wetland birds. Medicinal plants, mushrooms, reeds, resin, alchemical ingredients. Hazards: poison, contaminated water, hard terrain.
- **Desert:** dunes, plateaus, canyons, oases, coastal cliffs. Lizards, scorpions, snakes, desert foxes, birds of prey. Ores, salt, sulfur, sandstone, rare plants. Hazards: dehydration, heat exhaustion, sandstorms.
- **Jungle:** dense forest, waterfalls, rivers, hidden ruins. Monkeys, tropical birds, large cats, snakes, insects. Exotic hardwoods, rare fruit, medicinal plants, fine fibers. Hazards: predators, poisonous plants, restricted visibility.
Each island needs a believable food chain, a distinct resource economy and natural wildlife distribution.

### 11. Ships and sailing
For now repair existing sailing mechanics; no new vessels. Wind, trim, steering, position, weight and weather should reward skill. Players board from the water, use ship
components and recover nearby floating items. Currents must not make swimming or recovering a drifting ship frustrating. Advanced sails, fitting and construction stay deferred.

### 12. Combat
Wildlife: recognizable attack animations and warning behavior; blocking, dodging, positioning, stamina and reach matter; small creatures manageable alone; large predators need
preparation or teamwork; wildlife reacts to injury, danger and obstacles. Ships: cannon position, range, ammunition, hull damage and movement matter; hits show damage,
splinters and water effects; damaged sections may leak; crews balance steering, attacking and repairs; ships do not sink instantly from minor damage. Land combat and wildlife
behavior come before advanced naval combat.

### 13. Wildlife
Living creatures, not decorations: roaming, feeding, drinking, resting, fleeing, hunting, territorial behavior. Predators hunt prey rather than always the player; passive animals
flee unless cornered. Natural variation in size, behavior and density. Marine life by depth and habitat (schools, shoreline creatures, predators, large animals). Avoid excessive
spawning; keep performance. **The manatee and its artwork remain quarantined and out of gameplay.**

### 14. Ports, trading and the Company
Ports are safe settlements and economic centers; eventually merchants, markets, storage and cargo, ship repair, crafting stations, Company management, notice boards and contracts,
missions, NPC services. The Company lets players group, manage permissions, share resources, assign roles and own territory. **Begin with one functional starter port on Plains.**

### 15. Visuals, sound and atmosphere
Immersive, natural, mysterious, historical maritime fantasy. Priorities: natural island silhouettes and believable coastlines; biome ambience; responsive footsteps, swimming,
gathering and combat audio; wildlife calls; dynamic weather and water; aged parchment journal; constellation-themed skill tree; an atmospheric square map with drifting grey
clouds and exploration fog; consistent character appearance across gameplay and interfaces; readable on controller and keyboard/mouse.

### 16. Confirmed problems to correct first
Incomplete controller support and hard hotbar assignment; no death/respawn; inaccessible menu sections; no skill tree; incomplete character creation and Survivor display; no
stat allocation; wrong island geography and starting biome; too little wildlife and too few resources; wrong map and no fog; too-strong currents and unnatural swimming;
incomplete boarding and ocean harvesting; journal presentation; no damage feedback; ocean depth (should be 1,500 m).

### 17. Development direction
Interconnected, testable systems, not disconnected demos. Use configurable values for hunger, food, resource costs, damage, respawn distance, crafting time, animal density,
claim rules and progression. Preserve working systems; validate in the editor; test keyboard/mouse **and** controller. Do not build everything at once: the smallest functional
version of each loop, tested, then expand. **Priorities:** (1) broken interactions, menus, controls, swimming, death/respawn; (2) stats, skill-tree nodes, crafting progression;
(3) geography and populating the five regions; (4) make exploration, gathering, wildlife, combat and survival playable; (5) then multiplayer, trading, claims, advanced sailing.
