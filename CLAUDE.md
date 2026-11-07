# ELITEWAKE — Claude Production Guide and Canonical World Bible

Last consolidated: 2026-11-01
Engine: Unreal Engine 5.8 (installed build verified 2026-11-01: 5.8.3, changelist 58210709, promoted release)
Project: EW.uproject
Canonical playable map: /Game/Elitewake/Maps/Lvl_CoastalPlayground
Title map: /Game/Elitewake/Maps/Lvl_Title

This is the only human-readable production authority in the repository. It replaces the previous READMEs, game bibles, agent charters, delegation files, owner-decision fragments, reports, prompt collections, and phase packets. Historical material remains recoverable in Git history and the verified offline repository bundle; it must not be reintroduced as a competing instruction set.

The document tells Claude what Elitewake is, what is already real, which older statements lost conflicts, how to work safely, how to judge evidence, and how to execute each production phase. A requirement in this file is not proof that it is implemented. Source, assets, automated tests, Play checks, screenshots, packaged builds, and human review are separate evidence.

## 1. Authority, scope, and operating contract

### 1.1 Authority order

When instructions conflict, use this order:

1. The owner's newest explicit instruction in the current conversation.
2. This file, after checking its last-consolidated date.
3. The current island implementation and its tests (five islands are placed today; the approved world is twenty, section 5).
4. Current source code, Data Assets, maps, and verified runtime behavior.
5. Git history only as recovery evidence, never as current design authority.

Do not revive a deleted document because it appears more detailed. Do not silently invent a compromise. If the first four sources cannot resolve a new conflict, record both statements, dates, affected files, and your proposed winner, then ask the owner.

### 1.2 Solo workload

Claude works this project as one coherent workload. Do not create agent ownership tables, file locks, inboxes, delegated task files, handoff chains, model-specific workflows, or parallel branches for ChatGPT, Grok, Gemini, Codex, or Copilot. One coherent outcome belongs in one commit. Keep work small enough to verify and leave the branch clean.

Do not start a broad rewrite because several systems touch the same class. Extract one tested boundary at a time. Preserve working gameplay while replacing placeholders.

### 1.3 Canonical local state

The normal owner-facing project location is C:\UnrealProjects\EW_CLEAN and the normal branch is main after cleanup promotion. The old C:\UnrealProjects\EW checkout encountered a Windows file lock during retirement; do not use it for testing. On October 31 only its locked .claude worktree remnant (about 1 MB) remained; the owner deleted C:\UnrealProjects\EW_RETIRED_20261031. The desktop test shortcut opens C:\UnrealProjects\EW_CLEAN\EW.uproject with /Game/Elitewake/Maps/Lvl_CoastalPlayground. Keep the retired fragments only until they can be safely removed; a future rename to C:\UnrealProjects\EW must update this guide and every project shortcut in the same change.

Local folders outside the repository (each has a plain-English README.txt that is the detailed record):

| Path | Purpose | Rule |
|---|---|---|
| C:\UnrealProjects\EW_CLEAN | The one game project, matching GitHub main | Work, build and test only here |
| C:\ELITEWAKE | Storage beside the project: backup, quarantine, shortcuts | Not a project; never build or test here |
| C:\ELITEWAKE\BACKUP_CURRENT | Verified recovery set: CleanedProjectSnapshot (f6a474e7), ProjectSnapshot (pre-cleanup dfc390f1, with BACKUP_MANIFEST.csv hashes), Cleaned_Main_20261031.bundle, Repository_All_Refs.bundle (every old ref), Old_Codex_Snapshots_20261030.bundle, six historical player saves, unused Marketplace packs | Never delete or overwrite; add beside. Bundles hold Git history only, not LFS contents. Restore beside EW_CLEAN, never over it |
| C:\ELITEWAKE\QUARANTINE | Only copies moved from the owner's Desktop, Documents and Downloads remain | Delete only with explicit owner confirmation covering those personal copies |

Shortcuts: the Desktop "Elitewake" and "ELITEWAKE - Open Game in Unreal" open the EW_CLEAN project on Coastal Playground; "ELITEWAKE - Project Folder" opens EW_CLEAN; copies of the game and folder shortcuts plus "ELITEWAKE - Recovery Backup" are in C:\ELITEWAKE. Update all of them and the READMEs whenever a path here changes.

The following directories are generated and must never be edited or committed: Binaries, DerivedDataCache, Intermediate, and Saved. Saved contains mixed-use local data; never erase it wholesale without a specific, verified target and owner authorization.

The Game Default Map is the title map. The Editor Startup Map is Coastal Playground. UEWGameInstance still uses the ThirdPerson map as a temporary hosted-session recovery harness. Do not remove or redirect that harness until host, join, reconnect, survivor identity, save/load, and packaged multiplayer tests pass against the replacement.

### 1.4 Mandatory start procedure

Before changing anything:

1. Report the exact repository path, branch, HEAD commit, upstream, Unreal version, and requested outcome.
2. Inspect status and all worktrees without modifying them. If unrelated changes exist, preserve them and work around them.
3. Confirm Git LFS is installed. Report missing objects; do not replace pointer files with placeholders.
4. Read this entire file, then inspect the code, assets, tests, and current runtime path related to the request.
5. List the smallest useful slice, its dependencies, its tests, and what is deliberately out of scope.
6. Do not run two Unreal Editor instances against the same project.

Never solve a branch mismatch with reset --hard, destructive checkout, force push, or removal of an unverified worktree. Never delete a source asset because a text search finds no reference; inspect Unreal hard references, soft references, Asset Registry use, Python generation, packaging, and runtime loads.

### 1.5 Change and evidence rules

- One coherent outcome per commit.
- Prefer Data Assets, data tables, profiles, material instances, and source-controlled generators over one-off level edits.
- Keep balance values out of widgets and scattered literals.
- The server awards inventory, currency, ownership, damage, progression, company state, and saved state. Clients request; the server validates.
- Do not introduce a plugin, dependency, Fab pack, or generated asset without its version, purpose, license, source, and maintenance risk in ASSET_LEDGER.csv.
- Do not move a large Unreal content tree without fixing redirectors and validating references.
- Do not commit API keys, EOS credentials, Scenario credentials, signing keys, private server addresses, local connector files, or personal paths.
- Never call a screenshot, generated image, test map, or design paragraph an implementation.

Use only these status words:

- Implemented: source or content exists, but every gate has not passed.
- Verified: specified automated and manual functional checks passed.
- Owner visual review pending: objective visual checks passed; artistic approval has not.
- Owner audio audition pending: technical audio checks passed; the owner has not listened and approved.
- Accepted: the owner approved the required human gate for the named version.
- Deferred: intentionally outside the active phase, with a reason.
- Blocked: progress cannot safely continue without a decision, access, or external dependency.

### 1.6 Mandatory end report

Every session ends with: outcome; branch and commit; exact changed files; tests with pass/fail/not-run; maps and builds exercised; screenshot paths and visual-review status; audio paths and audition status; asset-ledger rows; performance measurements when relevant; remaining risks; and one recommended next action inside the active phase.

## 2. Product concept

Elitewake is a cooperative age-of-sail survival, expedition, and maritime-combat game. The ship is not a disposable vehicle; it is the player's persistent home, cargo hold, workshop, social space, and largest source of risk. The intended period language is approximately 1740–1760, expressed as high-definition naturalistic realism (section 9.1; owner, 2026-11-01) rather than a cartoon or stylized look, strict simulation, or high fantasy.

The core loop is:

Prepare at port → sail → discover → fight or explore → collect cargo → survive the return → trade and upgrade → sail farther.

The project succeeds when a player can tell a story about a voyage: what they prepared, what weather or threat changed the plan, what they risked, what the ship suffered, what they brought home, and how that changed the next voyage.

### 2.1 Design pillars

1. The ship is home. Ownership, crew, cargo, fittings, damage, repairs, and persistence matter.
2. Five regions create five survival and economic problems. A biome is not a ground-color swap.
3. Preparation has consequences. Food, water, tools, powder, shot, repair materials, crew, and cargo capacity shape a voyage.
4. Systems connect. Weather changes sailing; islands supply ship repairs; ship damage changes exploration; ports turn risk into progression.
5. Cooperation is useful without making solo play helpless. A lone player can manually operate the ship; a crew makes it faster and safer.
6. Readability precedes spectacle. Navigation, interaction, danger, damage, and ownership must be understandable without debug labels.
7. Complete loops precede content volume. One accepted voyage is worth more than many unfinished islands, ships, recipes, or animals.

### 2.2 Explicit non-goals for the current world

- No return to the old 26- or 40-island layouts. The approved world is twenty islands, four per region (owner, 2026-11-01).
- No mass import of free asset packs.
- No new ship class until the current class loop is complete.
- No claim warfare before persistence and authority are trustworthy.
- No large quest chain before the first 30 minutes work end to end.
- No public-Internet promise until a real external test is authorized and recorded.
- No claim that generated visuals or sounds are final without human review.

## 3. Current implementation truth

The advanced five-island branch is the source from which the cleaned project was selected. The following are known to exist and have prior functional or Play-check evidence, but they must be rechecked after changes that affect them:

| Area | Current truth | Important gap or caution |
|---|---|---|
| World | Five-island Coastal Playground, regional terrain/resources, caves, landmarks, wildlife, day/night, weather, and procedural setup scripts exist; reef-building scripts exist | Three open-ocean reefs are built and verified (November 6; see "Open-ocean reefs" below). Much of the presentation is placeholder or procedural; owner visual acceptance is not complete. Measured 2026-11-01 (terrain function): islands 2.0–2.4 km long, 2.4–3.0 km² of land, one dominant peak each (Winter 360 m, Jungle 261 m, Desert 118 m, Plains 65 m); the Swamp is a flat sheet (top 1.6 m) cut by a wave-pattern maze of channels. Walking routes measured 2026-11-01 (`measure_walking_routes_play.py`, walking speed 5 m/s): Starter 6.65 / 6.2 min, Swamp1 long axis 9.8 min, Desert1 across 5.6 min, Jungle1 across 6.4 min; Winter1 both routes, Desert1 and Jungle1 long axes never arrive within 30 min (their central mountains block them; Swamp1 across stuck at its start, to re-measure). Passable ground runs about 4–5 m/s in a straight line, so the sizes already suit 6–17 minutes; the impassable central relief is what fails. The map places exactly five islands; 35 more island meshes (Desert2–8, Jungle2–8, Plains2–8, Swamp2–8, Winter2–8, October 22) sit unused in `Content/Elitewake/World/Meshes/Islands` from the old 40-island layout; do not reuse or delete them without owner approval |
| Wildlife | Six land animals, bears, a lion, a giant crocodile and elephants are placed by `wildlife_distribution.py` / `place_animals.py` (a 146-animal placement plan: Plains 50, Desert 35, Jungle 30, Swamp 29, Winter 2) | Every animal is a rigid model built from lofted shapes, with no skeleton or animation. Behavior has two temperaments only: aggressive, or flee for 6 s when struck; the elephant flees. The 146 is a placement plan, not a population cap (section 5.6) |
| Port | Saltreach Freeport has merchants, buying/selling, service spaces, a safe zone, HUD feedback, and placeholder sound | Other ports are blockouts; merchant stock does not yet have complete persistence |
| Economy | Starting purse is zero; merchants and shipyard paths exist | Balance needs journey testing and duplicate-transaction protection |
| Ships | Raft, dinghy, sloop, schooner, and brigantine exist; per-sail controls and crew-dependent helm control work | The Cavalier is not built: no definition, hull, or build script exists, only its class speed in a code comment. The owner will supply the design reference `cavalier.png`. Visual quality, modularization, recipes, complete permissions, and persistence vary by system |
| Cannon | Sponge, powder-step, shot, ram, recoil, targeting, and fight checks exist; since November 7 a load takes a real Gunpowder charge with each round shot (sulfur ore + coal, or bought where round shot is sold) | Moving-target lead is still required; obstruction rules need acceptance testing. The cannon-fight, gunports and gunner-volley checks need the schooner or brigantine, which are parked off the map (October 12), so they cannot run until those ships return |
| Sailing | Individual sails, five deployment positions, crewed helm control, class speeds, sail multipliers, anchor and sinking checks exist | Weighted-sail presentation is placeholder; recipes and complete handling balance are not accepted |
| Survival | Needs, food, sickness, death/respawn, death bags, gathering, tools, cooking, skills, and building paths exist | Full first-30-minute pacing and owner-facing presentation are not accepted |
| Persistence | Survivors, ships, resources, death bags, and wreck crates have save behavior | Companies, merchant stock, schema migration, atomic recovery, and full dedicated-server coverage are incomplete |
| Multiplayer | Hosted/listen and separate-process checks exist; survivor reconnect and Company/ship-sharing paths exist | Public Internet is untested; direct-IP/session identity is transitional; in-game ship give/abandon is missing |
| Companies | Company screen and sharing policy exist | Company state is not fully persisted; roles and edge cases require authority tests |
| Crew | Sailhands, hired gunners, and service NPC paths exist | Wages, limits, target lead, lifecycle, and full persistence are incomplete |
| UI | Title, HUD, inventory, hotbar, crafting, skills, objectives, journal, map (all open, no fog, owner 2026-11-03; deep blue ocean, owner 2026-11-01), options, Company, and port feedback have checks | Visual hierarchy, accessibility, controller consistency, and 1080p readability need one accepted standard. Options has brightness, look sensitivity, and volume only: no graphics quality settings exist (section 9.6). The controller hotbar and Build Mode bindings differ from the owner layout in section 6.5 |
| Audio | Generated/imported placeholder ambience, wildlife, work, town, ship, and UI sounds exist | Technical presence is not human audition; provenance and final mix remain incomplete |

Treat this table as a starting audit, not permission to skip verification.

## 4. Resolved conflicts

These decisions replace every older conflicting statement:

| Conflict | Canonical resolution |
|---|---|
| Island count | Owner, 2026-11-01: twenty islands, four per region, each with its own shape and land area. This supersedes "exactly five". The old 26- and 40-island generators, tests, maps, and images stay obsolete; the twenty-island world is built fresh from section 5.7. The earlier "four sceneries per region" request is met by the four islands. |
| Villages | Owner, 2026-11-01: exactly one village per region, on one island (section 5.7); every other island has landings, not a village or port. Saltreach is the Plains village. |
| Four vs. five regions | Five: Plains, Winter, Swamp, Desert, Jungle. Plains is a full central region. |
| Island directions | Plains center/start; Winter north; Swamp south; Desert east; Jungle west. |
| Reefs | Owner, 2026-10-31: about three reefs out in the open ocean between islands, clear of every port. This replaces the five-regional-reef plan and the older six-reef text. |
| Regional primary trees | Plains Oak; Winter Birch; Swamp Spruce; Desert Palm; Jungle Ash. Birch never belongs to Swamp in the canonical plan. |
| Cavalier size | Cavalier is a distinct capital class approximately comparable in overall footprint to Brigantine, not an automatically larger scaled copy. It has three traversable levels. |
| Cavalier rooms | Upper deck, a separate deck below, and a lower interior reached by ladder; exact room and weapon layout remains approval work. |
| Sloop interior | Sloop has a lower deck but no captain's quarters. |
| Schooner | Same general width family as sloop but longer/taller; aft full-width quarters about one-eighth length; helm above. |
| Brigantine | Wider/taller; longer quarters; helm inside. |
| Sail assemblies | Base hulls have empty hardpoints. Removable sail assemblies include mast/pole, cloth, rigging, and attachment details. No flags are built into sail assemblies. |
| Boarding ladders | Centered at the stern. |
| Shipyard tiers | Small yard: Raft/Sloop. Medium: Schooner/Brigantine. Large: Cavalier. Higher yards do not automatically craft lower tiers. |
| Sulfur | Desert only (owner, 2026-11-01, superseding the same day's Swamp-sulfur request). Desert sulfur is sulfur ore, mined with Metal Pick or any approved higher-tier pick. Do not invent an Iron Pick gate. No sulfur item or deposit exists yet. |
| Visual target | Owner, 2026-11-01: high-definition naturalistic realism (section 9.1) replaces "high-definition naturalistic realism" everywhere, including prompts. |
| Island size | Owner, 2026-11-01 (corrected the same day from 30–45, then 15–20): a walk across each island takes 6–17 minutes on foot, preferably in every direction, measured in-game. This replaces the fixed 1.5–2.5 km diameter; there is no fixed diameter or mountain-height cap. All four islands of a region meet it and differ in shape and land area. |
| Inland water depth | Owner, 2026-11-01 (in feet): ponds 15 ft deep (457 cm), lakes 50 ft deep (1524 cm) at their deepest. The starter spring pond is 15 ft with a flat floor over its middle. |
| Swamp water | Owner, 2026-11-01: one winding coast-to-coast main river with connected tributaries; ponds stay separate closed water (section 5.5). Replaces the maze of channels. |
| Wild animals and tames | Owner, 2026-11-01: no design cap on wild animals, only technical spawning and performance controls (section 5.6). The tame limits (25 per player, 75 per Company, `UEWCompanyComponent::FitsTameCaps`) are separate and unchanged. |
| Elephant temperament | Owner, 2026-11-01: neutral. It never attacks unprovoked; struck, it defends itself instead of fleeing. |
| Controller hotbar and Build Mode | Owner, 2026-11-01: section 6.5 is the layout. It replaces the left-trigger hotbar chords, LB+A/X/B/Y order, right-stick Build Mode entry, and LB/RB material cycling. |
| Graphics tiers | Owner, 2026-11-01: higher quality settings improve visuals only; gameplay is identical on every tier (section 9.6). |
| Launch maps | Title launches the game; Coastal Playground is the canonical owner test world. ThirdPerson is only a temporary session harness until migrated. |
| Work model | One Claude production guide and one workload. Old agent locks, handoffs, team charters, and model workflows are void. |

## 5. Canonical world bible

### 5.1 World constants

- Twenty islands, four per region (owner, 2026-11-01), each of its own shape and land area. Each is sized so a walk across it takes 6–17 minutes on foot, preferably in every direction (owner, 2026-11-01). This is a gameplay-time target, not a diameter or height limit. Measure representative routes in-game (landing to forest, coast to coast, landing to the main resource areas) at real walking speed over real terrain before deciding dimensions, and keep the measurements with the island's evidence.
- Travel is full, not empty: accessible landings and routes into the main forest; space for wildlife, resources, exploration, hills, valleys, ravines, scattered mountains, and cliffs; no long stretches of empty travel.
- Relief is several smaller, plausibly shaped hills, peaks, or ridges distributed around each island, never one dominant central mountain to trek over.
- Each island offers practical base sites on hills and cliff shelves as well as flat ground (section 6.4).
- Plains is central and is the universal start. Winter is north, Swamp south, Desert east, Jungle west; each region's four islands lie together in its direction, open sea between them.
- Ocean depth may reach approximately 1.5 km where the world design requires deep water.
- Terrain is deterministic and explainable. A seed or source-data change must produce a reviewable diff.
- Coastlines are irregular: coves, headlands, beaches, shelves, cliffs, and eroded transitions. Never use five scaled/rotated copies of one island.
- Authored ports, caves, safe landings, primary landmarks, and gameplay resources do not move when decorative generation changes.
- World Partition, One File Per Actor, Data Layers, HLOD, and PCG are used where the canonical map supports them. Decorative PCG is separate from persistent resources and player structures.

### 5.2 Regional identity and resource matrix

| Region | Landform and palette | Primary ecology and hazards | Canonical resources | Navigation and sound identity |
|---|---|---|---|---|
| Plains | Rolling grassland, broad beaches, lake/river, gentle limestone cliffs; deep brown loam, restrained green, gray limestone, pale sand | Oak groves, common prey, boar/predator pockets, storms, exposure away from shelter | Oak; stone, flint, gravel; clay, sand, soil; berries, plants, herbs; basic iron/copper; water; common hides, meat, bones | Saltreach lighthouse, oak ridge, standing stones or sea arch; open birds, oak wind, moderate surf |
| Winter | Mountain spine, ice cliffs, frozen basin, sheltered dark shore; blue-gray rock, dirty white snow, dark soil, muted ice | Birch and cold scrub; freezing, blizzard, poor visibility, wolves and bears | Birch; snow/ice; water; iron, coal, stone; hides, fur, bones; emerald and coal also appear on mountainsides | Split ice face or black-rock peak; low wind, snow movement, distant ice, sparse wildlife |
| Swamp | Low marsh crossed by one winding coast-to-coast river with tributaries (section 5.5), separate closed ponds, peat ground, sandy banks, wet coast; black peat, olive, brown water, gray-green bark | Spruce, reeds, rushes, mushrooms, moss; poison, contaminated water, crocodiles, snakes, slowed travel | Spruce/resin; peat/soil; reeds/rushes; clay/bog iron; mushrooms/moss/herbs; dark gemstones in submerged caves | Giant dead tree, half-sunken ruin, or dry ridge; frogs, insects, close rustle, water movement |
| Desert | Dunes, plateau, canyon, oasis, sandstone coast; warm ochre, pale gold, red-brown stone, salt white | Palm at water, thorn scrub; heat, dehydration, sandstorm, scorpions, snakes | Palm/fronds/fibers/coconuts; sand, sandstone, clay; copper, iron; salt; sulfur ore; amber gems | Needles, arch, or mesa; dry wind, moving sand, sparse birds, canyon reflection |
| Jungle | Steep forest, rivers, waterfalls, hidden basins/ruins; dark loam, deep green, wet gray stone, small saturated accents | Ash canopy, vines, ferns, flowering understory; predators, poison, tight sightlines | Ash; vines/fibers/leaves; herbs/fruits; clay/river stone; copper; green gemstones; resin/exotic plants | Waterfall cliff, overgrown ruin, or giant tree; insects, water, day chorus, canopy movement |

Primary tree assignments create instant regional readability, not a ban on secondary species. Use substantial terrain-aware stands with clearings and forest edges, never token trees or grids.

### 5.3 Required island composition

Every island has:

1. One primary silhouette landmark readable from sea at 1–2 km.
2. Two secondary inland navigation landmarks.
3. At least three shoreline characters, such as beach, rock shelf, cliff, mangrove, ice, or dune.
4. One safe landing legible from a moving ship in day, night, rain, and regional weather.
5. One difficult landing.
6. One deliberate freshwater source where appropriate; Desert uses its oasis or equivalent.
7. One cave or sheltered exploration space.
8. One high-value inland resource area.
9. One predator/prey/habitat ecology loop.
10. Landings and, on the one village island of its region only, the village (section 5.7). Saltreach is the only port required to be fully functional during island production.
11. Its own reason to visit: a specialty resource or combination not found elsewhere in its region (section 5.7), with the basics (water, wood, stone, fiber, food, hide or meat) within about 3 minutes' walk of a safe landing.

PCG masks use slope, height, moisture, shore distance, exposure, soil, and region profile. Some areas have dense forest; vary species, spacing, undergrowth, bushes, and clearings with terrain and moisture. Avoid even rings, circular resource clusters, repeated tree grids, identical vegetation patterns, flat biome-wide color filters, and identical port plans. Preserve player buildings when generation reruns.

### 5.4 Caves, crystals, and harvesting

Ruby, sapphire, emerald, and obsidian may appear in every regional cave. Emerald and coal also appear on Winter mountainsides. Crystal nodes require a Metal Pick or approved higher-tier pick, yield 4–8 units, and use a 60-minute respawn unless later tuning is explicitly approved. Sulfur ore follows the same tool-tier interpretation.

Trees regrow after 20 minutes unless a building blocks regrowth. A felled log remains for 5 minutes unless harvested and must survive the intended save/reload boundary. Gameplay resource nodes use stable IDs; decorative instances do not require individual persistence.

### 5.5 Swamp river

Owner, 2026-11-01. The Swamp island has one navigable main tidal river or channel crossing it from coast to coast. Its winding, meandering course connects every flowing tributary and has distinct stretches: open marsh, wooded banks, bends, shallow-looking edges, and broader pools. It is not an arbitrary maze. Ponds remain separate closed bodies of water, never connected to the river network. Grassy ground, wet swamp, and sandy banks blend naturally; varied rocks are scattered across sandy areas without blocking land or ship routes. Wildlife is abundant but ecologically appropriate, with varied behavior, and does not fill every area uniformly. There is no Swamp sulfur (section 4).

The river is sized for the Cavalier, the largest intended ship: several metres of clear water on each side of the ship on the narrowest straight, wider in bends and turning areas. Before the channel is accepted, measure the Cavalier's beam, fully loaded draft, overall length, slow-speed turning circle, and mast top above the waterline in-game, plus any water-level variation (the game has no tides today: the sea level is fixed). Then verify safe depth at the lowest navigable water level, bank collision, overhead clearance, and a complete coast-to-coast voyage in-game. Never size the channel from a concept image. Until the Cavalier exists, build a large river that ships can enter and label every channel dimension provisional.

### 5.6 Wildlife populations

Owner, 2026-11-01. There is no design cap on wild animals. Keep species appropriate to each island and make the world feel alive, using sensible technical spawning and performance controls (distance-based spawning and simulation, a measured server budget), never a fixed design count. Placement counts in `wildlife_distribution.py` are a plan, not a cap. Wild-animal populations are separate from the tame limits (25 per player, 75 per Company), which stay as they are.

Distribution (owner, 2026-11-01): animals spread through suitable habitat across every island, placed by water, food, cover, and terrain, never as a uniform grid or one cluster, and never identically on every island. Species stay in their region (winter wildlife in Winter, desert in Desert, jungle in Jungle, plains in Plains, swamp in Swamp); islands within a region carry different mixes. Passive animals keep about 150 m and aggressive ones about 250 m from safe landings and villages. Species not yet in the game arrive as realistic, rigged assets (Phase 5); until then only existing species are placed, and only where they belong (today's squirrel monkeys on the Plains island are out of region).

People, elephants, and other wildlife have credible anatomy, proportions, skin or fur, movement, and behavior (section 9.1). Elephants look realistic and are neutral: they never attack unprovoked and defend themselves when attacked instead of fleeing.

### 5.7 Island plan and villages

Owner-approved 2026-11-01. Every island is worth visiting: the basics stay accessible everywhere, and each island has its own specialty. 🏘 marks the region's one village. Many listed resources and species do not exist yet as items or assets; adding them is part of island production.

| Region | Island | Specialty | Wildlife mix |
|---|---|---|---|
| Plains | P1 Starter 🏘 | Saltreach; oak, flint, berries, the spring pond | Boar, hares; coastal pelicans and flamingos |
| Plains | P2 Copper Downs | Copper and iron outcrops on limestone hills | Boar, deer, a lion pride on the high grass |
| Plains | P3 Clay Shore | Clay, sand, herbs along a river and lake | Deer, wild horses, wading birds |
| Plains | P4 Oak Heights | The great hardwood forest: ship timber, herbs, hides | Deer, boar, wolves in the deep wood |
| Winter | W1 Coal Spine | Coal seams along the mountainsides | Mountain goats, bears |
| Winter | W2 Birch Haven 🏘 | Sheltered birch valleys, fresh water, fur trade | Caribou, hares, foxes |
| Winter | W3 Iron Cliffs | Iron ore, building stone, emerald faces | Wolves, eagles |
| Winter | W4 Ice Reach | Ice and snow, best furs, emerald caves | Seals and walrus on the shore, polar bears |
| Swamp | S1 River Isle 🏘 | The coast-to-coast river (5.5), spruce, reeds | Herons, turtles, otters, cottonmouths |
| Swamp | S2 Bog Fen | Bog iron and peat fuel | Alligators, boar |
| Swamp | S3 Resin Woods | Spruce resin and pitch for ship repair | Giant crocodile in the backwater, snakes |
| Swamp | S4 Mushroom Hollows | Mushrooms, medicinal herbs, dark gems in submerged caves | Spiders, frogs, crocodiles at the edges |
| Desert | D1 Oasis Isle 🏘 | The oasis spring, date palms, coconuts | Gazelles, tortoises; flamingos at the lagoon |
| Desert | D2 Sulfur Flats | Sulfur ore at vents and evaporite flats (sulfur is Desert-only) | Scorpions, snakes, vultures |
| Desert | D3 Salt Pans | Salt for preserving food, sandstone | Flamingos, pelicans, jackals |
| Desert | D4 Copper Canyon | Copper, iron, amber in canyon sandstone | Snakes, tortoises, oryx |
| Jungle | J1 Waterfall Basin 🏘 | Rivers and falls, fruit, fresh water | Squirrel monkeys, parrots, tapirs |
| Jungle | J2 Gem Ridge | Green gemstones in ravines, copper | Jaguars, snakes |
| Jungle | J3 Spice Isle | Exotic plants, herbs, and fruit as trade goods | Monkeys, tortoises, parrots |
| Jungle | J4 Vine Woods | Ash timber, vines, and fiber for rope | Elephant herds (neutral, they defend themselves), boar |

Village islands have a sheltered harbor, their own fresh water, buildable ground, and a central sailing position in their region: P1 keeps Saltreach and the start; W2 is the sheltered, forested, watered option in the cold; S1's river gives ships a route inland; D1's oasis is the desert's water; J1 sits at the waterfall basin's river mouth.

Acceptance checks for the island world: exactly 20 islands, 4 per region, and 5 villages, one per region (layout test and map scan); a measured coast-to-coast walk of 6–17 minutes on every island in every direction tried (at least the long axis and across it), landing to forest in 3 minutes or less, and no empty stretch over 2 minutes; the basics within 3 minutes of each safe landing; each island's specialty present on it and absent from the rest of its region; every species placed only in its allowed region; no 200 m square holding more than 15% of an island's animals; the island mixes within a region all different; the landing and village distances above; server and client frame time measured at full populations.

The map screen shows a deep blue ocean around the islands (owner, 2026-11-01; done 2026-11-03) and the whole world with no fog of war (owner, 2026-11-03).

## 6. Player, survival, progression, and land systems

### 6.1 First-session arc

The first 30 minutes prove the land game and prepare the first voyage:

- Minutes 0–5: arrive on a safe Plains beach, read ocean/fresh-water/landmark directions, learn movement and interaction through contextual prompts.
- Minutes 5–10: gather wood, stone, fiber, berries, and water; craft one real stone tool.
- Minutes 10–15: build or repair fire/shelter, cook a safer meal, see hunger/thirst consequences.
- Minutes 15–20: face a modest wildlife or environmental threat; recover from injury or sickness.
- Minutes 20–25: reach Saltreach, sell or turn in something, understand merchants, storage, shipyard, and Company access without a wall of text.
- Minutes 25–30: acquire or prepare the first eligible craft, load essentials, and receive a clear regional-voyage goal.

No unexplained full-screen tutorial. The player should identify a safe route, water direction, and one memorable cue within ten seconds of spawn.

### 6.2 Needs and food

- Hunger and thirst each use a 0–100 scale.
- Ordinary hunger drains over roughly 45 minutes; thirst over roughly 25 minutes. Activity, climate, sickness, and equipment may modify data-driven rates.
- Raw fish: +8 hunger, 15% sickness chance.
- Cooked fish: +20 hunger, +3 health.
- Raw meat: +12 hunger, -3 health, 25% sickness chance.
- Cooked meat: +30 hunger, +5 health.
- Berries: +6 hunger.
- Cooked berry dish: +15 hunger, +2 health.
- Sickness lasts 3 minutes, reduces stamina regeneration by 30%, increases thirst depletion by 50%, is cured by herbs/remedy, and is not fatal by itself.

Death uses a readable fade/icy-edge presentation. Respawn chooses a safe randomized point in the same region. The death bag lasts 30 minutes. Save/load must preserve the intended bag lifetime and contents without duplication.

### 6.3 Progression

The current maximum level is 50. Each level grants one unspent stat point and one skill point. The implemented Wayfarer constellation contains First Light plus Gatherer, Torchbearer, Hardy, Field Repair, Strong Back, Second Wind, Metalwork, and Deep Reserves. Hunter, Cook, Builder, or other constellation proposals are not approved merely because they exist in history; introduce them only through an explicit balance/design slice with UI, save migration, and tests.

### 6.4 Building and claims

Building is a real gameplay system but still needs production art, cost, multiplayer, claim, and persistence hardening. New pieces require placement preview, collision, support rules, server authority, resource cost, cancellation/refund rules, save/load, demolition, and controller use.

Bases must be practical on hills and cliff shelves, not only flat ground (owner, 2026-11-01). Today a foundation is refused when the ground under its 4 × 4 m footprint varies by more than 2.5 m (`max_slope_rise`, `world_buildzones.py` / `BuildZones.json`); revise it with supported foundations and terrain-marked shelves rather than by removing the check.

Claims are deferred until the core voyage and persistence phases, but their canonical rules are:

- Claims apply to multiplayer only. In single-player, all five regions are accessible, world shapes remain fixed for the save, and the player may build without a Company, claim, contest, or artificial resource gate. Placement still obeys collision and NPC-site rules.
- A Company is required. Plains remains permanently neutral.
- Claim Banner plus 500 Gold starts a 30-minute establishment.
- Upkeep is 100 Gold per 24 hours; at most 7 days may be prepaid.
- A claim becomes abandoned after 72 hours without upkeep.
- A daily 2-hour vulnerability window controls hostile interaction.
- Rival banner capture takes 30 minutes and successful capture grants 48 hours of protection.
- PvE mode has no hostile takeover.
- During island production claims may be optional or simulated; do not let them block the voyage loop.

### 6.5 Input and control baseline

The current bindings are a baseline to verify in the actual Enhanced Input assets and Play checks, not a promise that all controller paths are accepted. Every shipping action needs keyboard/mouse and controller access. On foot: WASD/mouse or two sticks move/look; Space jumps/swims up; Shift sprints; with something in hand, left mouse/right trigger swing or use it; bare-handed (owner, 2026-11-03), the left arm punches with left mouse or LT and the right arm with right mouse or RT, each with a third-person punch others see and a first-person punch, the fist thrown out in front of the eyes, on the puncher's own screen; E/X interacts; I/Y opens inventory; M/View opens the map; Escape/Start opens pause. Hotbar 1–8 uses number keys. On a controller (owner, 2026-11-01): slot 1 D-pad Left, 2 D-pad Up, 3 D-pad Right, 4 D-pad Down; slot 5 LB+X, 6 LB+Y, 7 LB+B, 8 LB+A. The left trigger plus D-pad selects nothing. Inventory tabs use Tab/Shift+Tab or shoulder controls; arrows/D-pad move focus; Enter/A confirms; Escape/B closes. Map drag/right stick pans; wheel/triggers zoom. Sail trim uses left/right arrows or LB/RB; ladder uses up/down arrows or D-pad. Build Mode (owner, 2026-11-01): enter with B on the keyboard or hold LB and press D-pad Right on a controller, only on foot. Entering opens the radial menu of build options at once, on its paper/parchment backdrop, with no second press. Choose with the mouse or right stick and confirm with left mouse or A, which closes the radial and shows the placement preview; Tab/Y reopens it. On a controller, B closes the radial and B again (or LB + D-pad Right) leaves Build Mode; on the keyboard, Escape closes the radial and Escape or B leaves. Q/E or D-pad Left/Right alone rotate. Material: C or RB next, Z or LB+RB previous; LB alone does nothing in Build Mode. Demolish: X on the keyboard, R3 (right-stick click) on a controller, in Build Mode only; the right-stick click no longer enters Build Mode. Left mouse/A or right trigger places. LB keeps its sail-trim and cannon-target roles at those stations. Test-only F9 item spawn, F10 private session, and Shift+number teleports must remain out of shipping builds.

Known controller debt: jump, sprint, and stance bindings require gamepad-only Play verification; LB/RB overlap hotbar and sail/menu contexts; real-stick build-dial movement needs a physical controller check; a unified rebinding screen is missing. Resolve conflicts with explicit input contexts and on-screen focus, not hidden priority rules.

## 7. Maritime, ship, combat, and economy authority

### 7.1 Ship classes and yards

| Class | Base speed | Canonical role/shape | Yard |
|---|---:|---|---|
| Raft | 3 knots | Smallest improvised craft; current footprint is the reference | Small |
| Dinghy | 5 knots, tuning | Small utility/recovery craft | Existing acquisition path; do not invent a tier |
| Sloop | 8 knots | Primary vertical-slice vessel; lower deck, no captain's quarters | Small |
| Schooner | 10 knots | Similar width family to sloop, longer/taller; full-width aft quarters about one-eighth length; helm above | Medium |
| Brigantine | 12 knots | Wider/taller; longer aft quarters; helm inside | Medium |
| Cavalier | 14 knots | Distinct capital class, roughly comparable footprint to Brigantine; three traversable levels; helm inside. Not built yet: the owner will supply `cavalier.png` as its design reference | Large |

Ship recipes and prices remain data-driven. Do not infer that a larger yard can craft lower-tier vessels. All ships use centered stern ladders and base-hull sail hardpoints.

### 7.2 Sail behavior

- Deployment positions are 0%, 25%, 50%, 75%, and 100%.
- A standard small/medium/large sail gives a whole-ship multiplier of 1.30/1.50/1.80.
- A weighted small/medium/large sail gives 1.25/1.40/1.70 and steadies current influence by 10%.
- Only the best drawing sail multiplier applies; multipliers do not stack.
- All sails at zero create the approved horizontal hold.
- A lone player can operate individual sails at their stations. Helm control changes only sails assigned to crew.
- Wind fill, trim, class speed, weight, current, damage, and weather must remain inspectable data rather than hidden exceptions.

### 7.3 Repair

Shipwright's Hammer recipe: 30 Wood, 15 Stone, 10 Fiber, 5 Iron. A hole repair requires 20 Wood, 10 Fiber, 5 Resin, and 5 Iron. Minor repair takes 5 seconds; major repair takes 10 seconds. Consume materials only after a successful server-authoritative action. An emergency patch stops most water but does not restore full structure; permanent repair restores durability and has a distinct visible state.

### 7.4 Cannon and damage

Cannons use an explicit sponge → powder → shot → ram sequence, then aim/fire/recoil. A real powder item backs the powder step (November 7): a load takes one Gunpowder (DA_Gunpowder, the fitting's CannonPowder) and one round shot, both checked before either is taken; Gunpowder is mixed from 1 sulfur ore and 1 coal (a first recipe) or bought, 5 for 40 Copper, wherever round shot is sold (`add_gunpowder.py`). Gunners must not fire through obstructions and must lead moving targets before acceptance. Hull damage needs location-readable fresh splintering, a hole, incoming water, temporary patch, and permanent repair. Minor damage must not instantly sink a ship.

### 7.5 Port and economy

Saltreach is a working frontier Freeport: safe harbor, market, tavern, shipyard, services, storage, and voyage preparation. It is not a pristine resort, a ruined ghost town, or a generic fantasy village. Starting currency is zero. Purchases, sales, ship acquisition, crew hire, and repair are server-authoritative and idempotent under retries. Merchant stock, restock time, pricing profile, and transaction state must become persistent in Phase 4.

## 8. Multiplayer and persistence contract

Every persisted object needs a stable-ID rule, serialization owner, payload version, migration path, missing-reference behavior, duplicate-ID detection, and at least one older fixture. The save envelope contains schema version, build/commit ID, world seed/map ID, timestamp/server ID, object type/stable ID/owner scope, subsystem payload version, integrity result, and safe-write state.

Use atomic replacement: write a new generation, validate it, preserve the prior valid generation, then promote the new file. Never overwrite the only valid save. A corrupt newest generation must recover from the prior valid one without silently zeroing inventory or deleting a ship.

Required eventual persistence scope: survivor identity/appearance/position rules/inventory/stats/progression; Companies and roles; ships, fittings, cargo, damage, anchor, sails, crew and ownership; resource state and regrowth; death bags and wreck crates; merchant stock and transaction state; structures and enabled claims; scalable required wildlife state. Do not serialize every decorative animal every frame.

Tests must cover listen server, dedicated server with two clients, two physical PCs on LAN, 100–200 ms simulated latency, loss/duplicate requests, disconnect before acknowledgement, and shutdown immediately before/after save. Public Internet testing is separate and requires owner authorization. Direct-IP identity is transitional; preserve a migration path to stable platform/EOS identity.

## 9. Visual production standard

Claude may check geometry, scale, collision, pivots, UV/material assignment, LOD/Nanite state, broken textures, intersections, exposure ranges, framing consistency, and whether required screenshots exist. Claude must not declare a composition beautiful, cohesive, historically convincing, or final. Those judgments remain Owner visual review pending.

### 9.1 Visual thesis and palette

Use high-definition naturalistic realism (owner, 2026-11-01), not a cartoon or stylized look. People and animals have credible anatomy, proportions, skin or fur, movement, and behavior; crouching, walking, working, and interacting look physically believable. Vendor booths, villages, ships, terrain, foliage, and materials look like functional places and objects of the 1740–1760 setting, never exaggerated props. Use natural lighting, restrained color grading, believable wear and texture scale, varied silhouettes, natural materials, and weathering caused by salt, sun, water, use, and shelter. The grounded maritime appeal of Atlas is a mood reference only, with a more modern visual finish; never copy its assets or designs. Avoid modern plastic, electric fixtures, machine-perfect timber, contemporary typography, industrial fasteners, generic neon fantasy glow, and uniform dirt overlays.

| Use | Anchor color |
|---|---|
| Sun-bleached plaster | #D6C7A8 |
| Limestone | #B8AA8E |
| Warm weathered timber | #5B402D |
| Dark wet timber | #2D241E |
| Tar/deep shadow | #181815 |
| Rope/canvas | #A88961 |
| Oxidized copper accent | #52726A |
| Plains grass | #71834D |
| Winter blue-gray | #697987 |
| Swamp olive | #59603A |
| Desert ochre | #B77A3D |
| Jungle deep green | #244B36 |

These are anchors, not flat albedo values. Materials need controlled value, roughness, hue, edge wear, moisture, sun bleaching, and contact variation. Saturated color is reserved for navigation, banners, hazards, important props, flora accents, UI, and approved rare materials.

### 9.2 Scale, meshes, materials, and UI

- 1 Unreal unit = 1 cm. Human reference is about 180 cm. Typical doors are 210–230 cm high.
- Test stairs, ladders, hatches, rail gaps, deck headroom, and paths against the real player capsule and third-person camera.
- Use logical pivots and intentional gameplay collision.
- Target about 512 pixels/meter for ordinary environment surfaces and up to 1024 pixels/meter for close hero assets. Large surfaces use tiles, trims, and detail normals rather than huge unique maps.
- Keep material slots low; use instances. Provide intentional LODs or measured Nanite use.
- At 1920×1080, primary body text is at least a 24 px equivalent and secondary labels at least 18 px unless measured otherwise. Aim for 4.5:1 normal-text contrast.
- Controller focus uses shape/value as well as color. Generated Scenario images contain no text; typography is built in UMG.

### 9.3 Lighting and navigation readability

Start daylight direction near physically plausible 50,000–100,000 lux and then tune measured exposure. Night remains dark but navigable through sky fill, moon, fire, windows, lighthouse, and route hierarchy—not a bright blue sun. Avoid adaptation pumping when opening UI or entering buildings. Keep the sea horizon readable in navigable weather. In final 8-bit evidence, do not crush gameplay-critical surfaces; night interaction areas generally remain distinguishable around RGB 20–80.

### 9.4 Mandatory visual evidence

Capture before and after using the same camera, 70-degree horizontal FOV unless the gameplay camera differs, 1920×1080, same preset, time, weather, exposure, and color settings. Beauty views contain no gizmos, selection, or debug text. Diagnostic views are separate.

For a location capture: 1 km establishing; 200–300 m navigation; 20–30 m human-scale; 2–5 m interaction; reverse angle; day; night; signature weather. Add collision, navmesh, lighting complexity, overdraw, PCG mask, LOD/HLOD, and performance diagnostics where relevant.

Check objectively: no floating/buried/intersecting critical props; capsule fit; no foliage through structures; water/shore gaps; plausible variation without visible repetition; landmark visibility; collision alignment; intentional shadows/reflections; no gameplay-route LOD pop; weather/night retain interaction cues. Then mark Owner visual review pending.

### 9.5 Scenario visual workflow

Use Scenario for original reference boards, material studies, decals, icons without text, sky/weather studies, vegetation studies, prop turnarounds, and approved production textures. Never upload Fab, Marketplace, Megascans, Epic sample, other-game, film, scraped portfolio, or copyrighted character material as a reference/training input without explicit generative-use rights.

Base prompt:

Production reference for Elitewake. High-definition naturalistic realism; historical maritime frontier approximately 1740–1760; believable hand-built construction; natural materials; restrained saturation; weathered by salt, sun, water, and use; strong readable silhouette. SUBJECT: [one precise subject]. GAMEPLAY FUNCTION: [how the player uses or reads it]. REGION: [Plains/Winter/Swamp/Desert/Jungle]. DIMENSIONS: [centimeters and human comparison]. MATERIALS: [specific species, stone, metal, cloth]. CONSTRUCTION: [joints, fasteners, load-bearing logic]. CAMERA: [orthographic or 70-degree gameplay view, exact distance and height]. LIGHT: [time, direction, weather, neutral exposure]. BACKGROUND: neutral, uncluttered. Preserve identical proportions across views.

Negative prompt:

No modern hardware, plastic, neon, science fiction, cartoon proportions, excessive fantasy ornament, readable generated text, logo, watermark, extra parts, impossible joints, glossy uniform material, extreme depth of field, black crush, cinematic fog hiding construction, or inconsistent view-to-view proportions.

For any modeled prop, request front, back, left, right, top, underside, and three-quarter views of the same design. Specify exact dimensions and a 180 cm human silhouette. Reject a set if doors, joints, handles, anatomy, count of parts, or material boundaries change between views. Scenario output is a reference until modeled/imported, integrated, tested, and reviewed.

### 9.6 Graphics quality tiers

Owner, 2026-11-01. Provide scalable visual-quality settings so stronger graphics cards show higher-resolution textures, foliage, shadows, water, and effects. Core gameplay, resource availability, navigation, and fairness stay the same on every tier: anything that blocks movement, conceals a player, or can be gathered or interacted with never scales with quality. A better GPU must never grant a gameplay advantage. Verify with an automated comparison of gameplay objects, collision, and resources across tiers, and measure frame time per tier.

Minimum machine (owner, 2026-11-02): the game must at least run and be testable on the owner's GeForce GTX 1660 Super (6 GB video memory, no ray-tracing hardware) at 1920×1080 on the Low tier, within about 4.5 GB of video memory. Nothing may assume the whole world is resident: islands stream (World Partition, HLOD for distant islands) and dense foliage exists only near the player. Measure a packaged build on that card before a phase is accepted.

## 10. Audio production standard

Audio communicates material, distance, weather, danger, and ship condition. Preserve quiet and dynamic space; do not fill every moment with music or animal calls. Claude may validate files and implementation but must mark selections Owner audio audition pending until the owner listens.

- Master at 48 kHz, 24-bit WAV where possible.
- Mono for positional one-shots; stereo stems for ambience/music unless a spatial design requires otherwise.
- Peak at or below approximately -1 dBTP before Unreal mix processing.
- Remove DC offset, clipping, accidental silence, bad generation tails, and loop seams. Preserve lossless masters.
- Common events have at least three variations and appropriate concurrency/cooldown.
- Ordinary world sound: full about 4 m, faded by about 40 m.
- Surf: full at water edge, fade from roughly 2 m inland, silent near 20 m; inland ponds are not surf emitters.
- Region-bed crossfade: at least 2.5 seconds.
- Cannon and anchor-scale work: full within 20 m, audible around 400 m when conditions allow.
- Use attenuation assets, Sound Classes, Submixes, Audio Modulation, MetaSounds, Quartz, and concurrency instead of baking behavior into a stereo file.

Mix priority: immediate danger/damage; dialogue/critical confirmation; player action; ship state; nearby wildlife/settlement; weather/ambience; music.

Scenario starting models, subject to checking the current model card at generation time:

- ElevenLabs Sound Effects 2 — model_elevenlabs-sound-effects-v2 — commercially licensed, loop option, up to 30 seconds.
- Beatoven SFX — model_beatoven-sound-effect — royalty-free, up to 35 seconds.
- MM Audio 2 text-to-audio — model_mm-audio-2-t2a — MIT model card, up to 30 seconds.
- MM Audio 2 video-to-audio — model_mm-audio-2 — use only owner-captured silent gameplay video.

Scenario consumes compute units. A free plan or low audio cost does not make every generation free forever. Record the displayed cost before generation and download selected outputs; platform retention may be limited.

SFX prompt:

Isolated game sound effect. SOURCE: [object/creature]. ACTION: [one action]. MATERIAL: [wood/rope/canvas/iron/water/soil]. FORCE/SPEED: [specific]. ENVIRONMENT: [close dry/open harbor/stone cave/ship deck]. LISTENER DISTANCE: [meters]. DURATION: [seconds]. TRANSIENT: [soft/sharp]. TAIL: [none/short natural decay]. Produce a clean source, no music, melody, speech, unrelated ambience, cinematic boom, modern machinery, clipping, or reverb unless specified.

Ambience prompt:

Seamless environmental ambience stem for a grounded historical maritime survival game. REGION: [region]. LAYER ONLY: [wind/water/fauna/settlement]. TIME: [day/night]. WEATHER: [condition]. DENSITY: sparse and natural. DURATION: [maximum supported]. No music, dialogue, foreground action, modern source, siren, or rhythmic repetition. Stable loop bed with no dominant event at the seam.

Generate wind, water, fauna, weather, and settlement separately so Unreal can mix state. For synchronized Foley, owner-captured video is reference; interactive events still require separate triggers.

## 11. Free asset and license policy

Free means zero price at acquisition, commercial game use allowed, studio account acquisition completed where required, compatible engine/use restrictions, satisfiable attribution, and a complete ASSET_LEDGER.csv entry. A downloadable or royalty-free file is not automatically free or shippable.

Allowed evaluation sources include Unreal built-in tools/content under current terms; compatible Epic samples; Fab zero-price products under the Fab Standard License; Fab CC-BY with exact attribution; currently free or previously validly claimed Megascans; CC0/public-domain material with provenance; original studio work; and Scenario output whose model and inputs permit commercial generative use.

The Fab Standard License generally permits commercial/private use, modification, and distribution inside a project, but not resale or standalone redistribution. Personal and Professional tiers have the same use scope; Reference-Only does not supply source format. CC-BY requires attribution. UE-Only and any additional listing restrictions must be recorded. Claim assets through the studio account and preserve a listing/license snapshot.

Megascans is not categorically free. Use only assets validly claimed under earlier terms or currently shown as zero price and acquired under current terms. Record which license applies.

Prefer built-in Unreal 5.8 capabilities before a plugin: World Partition/Data Layers/OFPA/HLOD; PCG; Landscape/Water; Nanite/Lumen after profiling; Niagara; MetaSounds/Sound Cues/Audio Modulation/Quartz; Control Rig/IK Rig/IK Retargeter; Modeling Mode/Geometry Script; Chaos where measured; UMG/Slate/CommonUI; Automation Framework; Insights and Network Insights. Procedural Vegetation Editor is experimental and must not become a production dependency without an exit plan.

New third-party packs enter an isolated intake map, not /Game/Elitewake. Check license, version, dependency, scale, collision, topology, UVs, material slots, texture memory, skeleton/root motion, LOD/Nanite, naming pollution, warnings, style, package inclusion, and size. Mark accept, modify, reference-only, or reject. Migrate only used pieces.

Never use ripped assets, search-result images, Pinterest/ArtStation/DeviantArt material without direct rights, YouTube audio, other-game content, non-commercial/editorial-only assets, expiring trial output, unidentified authors, or GPL code/plugins without deliberate legal and architecture review.

Official references to recheck at acquisition time:

- https://www.unrealengine.com/fabfreecontent
- https://www.fab.com/eula
- https://www.unrealengine.com/license
- https://www.unrealengine.com/eula/unreal
- https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- https://dev.epicgames.com/documentation/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine
- https://help.scenario.com/articles/1129045411-frequently-asked-questions-faq
- https://help.scenario.com/articles/2852272401-introduction-to-audio-generation-on-scenario
- https://help.scenario.com/articles/8811829644-model-costs-for-asset-generation

Before public release, export the ledger, map every non-studio packaged asset to a record, generate notices, confirm raw source is not redistributed, exclude intake/rejected packs, audit Scenario inputs, and preserve evidence with the release.

## 12. Production phases and copy-ready Claude guides

Run phases in order. A later phase may be audited early, but do not expand it while an earlier exit criterion blocks the core loop. Within a phase, complete the smallest vertical slice, verify it, and commit before the next slice. A visually impressive change does not excuse a broken save, controller path, authority rule, or packaged build.

### Phase 0 — Stabilize one real project

#### Objective

Make the owner shortcut, normal checkout, GitHub main, verified backup, tests, and this guide refer to the same recoverable game state. No gameplay or art expansion belongs in this phase.

#### Required sequence

1. Inventory all project folders/worktrees, branches, HEADs, upstreams, dirty files, LFS state, shortcuts, backups, packages, and Unreal versions.
2. Select the newest complete five-island implementation by commit ancestry and functional evidence, not folder name or timestamp alone.
3. Create a byte-verified project snapshot excluding only generated directories and a complete Git bundle containing every ref. Record file count, total bytes, hashes, source commit, and bundle verification.
4. Build a clean candidate checkout from the bundle/remote. Prove that apparent LFS or timestamp modifications have zero content diff before clearing false flags.
5. Resolve known text/config conflicts: exactly five islands, five reefs, five regions, canonical tree assignments, Coastal editor startup, solo workload, and one authority file.
6. Remove obsolete high-island code paths, tests, images, model-agent instructions, redundant READMEs, exact duplicate source art, stale reports, and obsolete local generated builds only after the new backup is verified.
7. Run Python tests, source/config searches, LFS checks, Unreal Editor build, game build, native automation, focused Play checks, package, and launch smoke test.
8. Point both owner shortcuts at the tested C:\UnrealProjects\EW_CLEAN checkout and test through the same game shortcut the owner will use. Retire the locked old EW folder only when Windows releases it; do not treat that stale folder as a second project authority.
9. Push the tested commit to GitHub main by fast-forward; never rewrite public history. Verify remote main, then remove obsolete agent branches. The bundle remains the recovery path.
10. Delete the retired local project, old backup, quarantine, old packets/reports, and temporary cleanup checkout only after the owner shortcut launches and the remote is verified. If Windows locks a retired folder, leave its exact path recorded and retry after the handle is closed; never delete the active EW_CLEAN checkout.

#### Baseline visual evidence

These are truth captures, not an art pass: title screen; Plains spawn in daylight; Saltreach sea approach daylight; Saltreach market at night; each island offshore at roughly 1 km; two distinct connected players; packaged-build title screen. Use 1920×1080, the same preset, 70-degree horizontal FOV, and no editor overlay.

#### Verification and exit

- Exactly one normal project path and one retained verified backup.
- Main and local normal checkout resolve to the same commit.
- Status is clean; LFS objects required by that commit are available.
- Python/unit gates pass; editor and game targets compile.
- Packaged development build launches and reaches Coastal Playground.
- The owner shortcut launches that tested project.
- Current tree contains this Markdown file only; the asset ledger is present.
- No 26/40-island path, stale model workflow, or conflicting world authority remains.

#### Copy-ready prompt for Claude

Work only on Phase 0 in section 12 of CLAUDE.md. Begin read-only: report exact project path, branch, HEAD, upstream, worktrees, status, Git LFS state, Unreal version, shortcut target, and backup targets. Treat /Game/Elitewake/Maps/Lvl_CoastalPlayground as the canonical owner test map and exactly five islands as absolute. Preserve all working gameplay. Create and verify recovery artifacts before any deletion. Do not use reset --hard, force push, or broad deletion. Remove only verified obsolete duplicates, old model workflows, high-island paths, generated builds, and superseded documents. Run the complete Phase 0 build/test/package/shortcut gates. Stop before any unverified destructive action. Report exact evidence and leave one clean workload.

### Phase 1 — Accept the first 30 minutes

#### Objective and boundary

Deliver a new-player Plains experience that teaches through play and ends with the player supplied, capable, and curious about a voyage. Do not add another ship class, claim warfare, advanced farming/breeding, late-game metals, a large quest chain, or a second fully functional port.

#### Implementation slices

1. Arrival: spawn orientation, movement/camera/jump/crouch/interact prompts, safe beach, fresh-water cue, oak silhouette, and distant Saltreach cue.
2. First resources: wood, stone, fiber, berries, water, correct feedback, inventory-full response, and a stone tool through the real crafting path.
3. Shelter and sustenance: fire or minimal shelter loop, cooking, needs explanation through consequences, save/reload.
4. Risk and recovery: modest threat, injury/sickness treatment, death, same-region respawn, and 30-minute death bag.
5. Saltreach arrival: merchant interaction, zero-purse economy explanation, storage/services/shipyard orientation.
6. Voyage readiness: acquire or prepare the eligible starting craft, load food/water/repair materials, and present one destination goal.

Each slice includes keyboard/mouse, controller, save/reload, failure-path, UI, audio trigger, and screenshot evidence before continuing.

#### Exact Plains visual target

Spawn at late morning. Put the ocean behind or 30–90 degrees to one side rather than directly filling the forward view. The forward 10-second read contains: a 3–6 m wide traversable sand/grass route; one oak group creating a vertical silhouette; a low fresh-water or terrain cue; one distant human-made Saltreach/lighthouse cue; and no more than one prominent tutorial prompt. Use pale warm sand, restrained #71834D grass, deep-brown soil, gray limestone, and weathered timber. Avoid a symmetrical corridor, evenly scattered rocks, identical trees, oversaturated green, fog that hides the destination, or a cluttered survival-game prop dump.

At 20–30 m, every first resource has a different silhouette and material response. At 2–5 m, the interaction point is unobstructed, the pickup/tool animation contacts the source, and the prompt never covers the crosshair or item. Fire/shelter establishes a warm value focal point without turning daylight orange. The Saltreach reveal frames lighthouse/roof/mast layers rather than exposing the whole town at once.

#### Scenario references to make only when needed

Plains spawn board prompt:

Elitewake gameplay-environment reference, high-definition naturalistic realism, 1740–1760 maritime frontier. A safe central-Plains island arrival beach viewed from third-person player eye height 170 cm, 70-degree horizontal FOV. Ocean 45 degrees behind-left; forward route 4 m wide crossing pale sand into restrained green grass; irregular gray limestone; a natural oak group forming one readable silhouette; subtle freshwater direction cue; distant Saltreach lighthouse and masts at least 500 m away. Late-morning warm sun from camera-right, neutral exposure, clear navigation, no UI. Natural asymmetry, believable erosion and scale. No tropical resort, no modern objects, no giant fantasy tree, no excessive props, no symmetrical path, no cinematic depth of field, no text.

First-resource sheet prompt:

Consistent production reference sheet for five separate Elitewake Plains harvestables: fallen oak branch bundle, loose flint/stone cluster, fibrous grass/reed bundle, berry bush, and clear freshwater edge. High-definition naturalistic realism, neutral overcast studio light, exact scale beside a 180 cm human and 30 cm ruler, front/side/top/three-quarter views, clear silhouette at 5 m, believable hand-harvest points, no labels or generated text, no decorative fantasy glow, no duplicate silhouettes.

#### Audio target

Use separate gentle surf, light oak wind, sparse birds, sand/grass/soil/stone/wood footsteps, gather impacts, pickup, craft completion, drinking/eating, fire ignition/loop, and restrained discovery cue. Common footsteps/impacts need at least three variations. Needs warnings are brief, non-musical, and never repetitive beeps. The campfire loop has close attenuation and no audible seam. No constant dramatic music.

#### Failure tests

Craft without materials; invalid/contaminated water; deterministic raw-food sickness; inventory-full pickup; death before/after shelter; death-bag expiration/recovery; save after cooking, level-up, and storage placement; disconnect/reconnect where hosted multiplayer is active. Test UI at 1920×1080 and controller navigation from the title screen through voyage readiness.

#### Required captures and exit

Capture the same spawn camera day/night/weather; 10-second route read; each resource at 20 m and 3 m; tool contact; fire/shelter day/night; threat/readable damage; death/respawn/bag; Saltreach reveal and service route; loaded starting craft. Record an uninterrupted playthrough.

Exit when a new player finishes without developer commands in a median 25–40 minutes, no keyboard/controller blocker exists, the sequence survives save/load, death recovery works, tuning is data-driven, objective visual checks pass, and the owner has reviewed visuals and auditioned the full recording.

#### Copy-ready prompt for Claude

Execute only Phase 1 in section 12 of CLAUDE.md. Audit the existing game against every five-minute block before editing. Choose the first incomplete vertical slice and state what later slices will remain untouched. Implement the real gameplay path—never a verification-only shortcut—with keyboard/mouse, controller, server authority where relevant, save/load, failure tests, objective visual captures, and audio triggers. Follow the exact Plains composition, scale, palette, screenshot, and sound rules in CLAUDE.md. Do not expand another region, ship class, claims, or quests. End with the uninterrupted playthrough evidence and label artistic/audio judgments pending until the owner accepts them.

### Phase 2 — Build five memorable islands, not five color swaps

#### Objective and boundary

Turn the test world into the approved twenty-island world (section 5.7): five distinct, navigable, performant regional identities, four islands each. Work one island at a time: Plains and Saltreach interfaces, then Winter, Swamp, Desert, Jungle. Do not reactivate the old 26/40-island layouts or make all villages fully functional.

#### Per-island production order

1. Lock scale, coastline, elevation, silhouette, safe/difficult landings, cave, freshwater logic, authored port site, and three navigation landmarks.
2. Validate player/ship approach, traversal, collision, navmesh, world streaming, and return to sea in graybox.
3. Add soil/shore/material profile and primary tree stands.
4. Add persistent resources with stable IDs and ecology/hazard loop.
5. Add region weather, post-process limits, audio stems, and landmark sounds.
6. Add decorative PCG using slope/height/moisture/shore/exposure masks; generate HLOD and profile.
7. Capture the full evidence set, fix objective defects, obtain owner review, then proceed.

Built November 6: three open-ocean reefs on seamount tops (see "Open-ocean reefs" in the November 4 section); `verify_reefs_play.py` passes with one listen server and one client.

#### Exact visual cards

Plains: broad, navigable beaches; rolling grass/loam; gray limestone; oak stands with irregular clearings; one freshwater corridor; Saltreach/lighthouse dominance near the home coast. The silhouette is low-to-medium relief with one ridge/arch/standing-stone break. It feels hospitable but not manicured.

Winter: a dark-rock mountain spine breaks the horizon; dirty snow occupies planes based on exposure and wind, not every surface uniformly; blue-gray ice is localized; birch stands collect in sheltered lower areas. Safe landing is a dark sheltered shore. Blizzard reduces range but retains the landing cue. Avoid pure white, bright cyan ice, Christmas-pine shorthand, and terrain hidden by fog.

Swamp: one winding coast-to-coast river (section 5.5) with tributaries, broad pools, bends, wooded banks, and open marsh creates close choices without becoming a maze; ponds stay separate; brown water remains visually distinct from walkable black/olive ground; spruce rises on firmer pockets, while reeds/rushes/mushrooms mark moisture. A giant dead tree, raised ridge, or half-sunken ruin provides a long cue. Avoid a uniform green filter, identical mangrove tunnel, or water/ground ambiguity.

Desert: large-form dune direction leads toward plateau/canyon/oasis; warm ochre and red-brown sandstone are broken by salt-white and sparse palm at water only. Landmark is an arch, mesa, or needle visible above dust. Keep sand microdetail quiet enough to read slope. Avoid endless flat sand, random palms, orange global tint, and a lush oasis larger than its water logic supports.

Jungle: steep wet-gray stone, rivers/waterfalls, dark loam, dense ash canopy, ferns/vines, and small saturated flora accents. Local sightlines tighten but authored corridors and waterfall/ruin/giant-tree cues prevent maze failure. Canopy density varies with slope, gaps, river, and exposure. Avoid an impenetrable wall, uniformly bright green, foliage through routes, or every surface shining wet.

#### Scenario island prompts

For each region substitute its card into this template:

Elitewake regional island production reference, high-definition naturalistic realism and believable geography. REGION: [name and exact card]. Island sized for a 6–17 minute walk across in any direction, with several distributed hills, ridges, valleys, and cliffs, no single dominant mountain. CAMERA: offshore at sea level, 1 km from safe landing, third-person ship-eye height 4 m, 70-degree horizontal FOV. Show one primary landmark readable against sky, at least three shoreline materials, one obvious safe landing, and a different hazardous landing. Lighting: neutral late morning; no cinematic haze hiding the silhouette. Natural eroded coastline, terrain-driven vegetation, plausible drainage and human-scale construction. No circular island, no cloned mountain, no evenly spaced trees, no fantasy megastructure, no modern object, no labels, no tiny diorama perspective.

Generate four compass approaches per island and compare silhouette consistency. Generate separate 200–300 m landing and 20–30 m route references; do not use a distant concept painting to decide interaction-scale dressing.

#### Required evidence per island

High aerial with scale and named routes; four offshore compass views at about 1 km; safe and difficult landing from ship-eye height; primary landmark at 1 km, 250 m, and 30 m; inland route in day/night/signature weather; fresh water, cave, resource area, ecology loop, port site; collision/navmesh; PCG masks; World Partition/Data Layer/HLOD view; streaming and densest-scene profile.

#### Audio and performance

Each region owns separate day/night base bed, wind/weather, shore/water, sparse fauna scheduler, and landmark emitter. Crossfade at least 2.5 seconds; never play every animal call continuously. Export Scenario stems separately. Profile an approach, landing, inland traversal, dense vista, cave transition, storm, and departure on the agreed minimum machine and two-player server.

#### Exit

All twenty load in approved directions and crossing-time range; each has a distinct silhouette, survival problem, economy, palette, and sound identity; a player can sail to, land, traverse, and leave; authored items do not move after decorative regeneration; persistence survives streaming/reload; target performance holds; the owner reviews the image set and full regional traversal audio.

#### Copy-ready prompt for Claude

Execute only Phase 2 in section 12 of CLAUDE.md, one island at a time in the stated order. First compare the current island against its exact visual card, ten composition requirements, resource matrix, and evidence list. Fix authored geography, safe/difficult landings, landmarks, port/cave/freshwater, routes, collision, and streaming before decorative PCG. Use terrain-driven masks; never a circular scatter or cloned island. Do not reactivate high-count layouts or complete another port. Produce exact-distance day/night/weather and diagnostic captures, measured performance, persistence checks, and separated regional audio stems. Mark visuals and audio pending until owner review.

### Phase 3 — Complete one maritime voyage

#### Objective and boundary

Deliver one complete Saltreach-to-region-and-back voyage using the sloop: prepare, load, crew or manually operate, depart, navigate wind/weather, face one threat, take damage, repair/recover, obtain cargo, return, trade/store, save, quit, and reload. Do not add a ship class. Refactor AEWShip only one tested responsibility at a time.

#### Required voyage and architecture slices

1. Acquisition/ownership: eligible ship, owner, Company sharing policy, unauthorized denial.
2. Provisioning: real food, water, repair materials, shot, and real powder; hold transfer and capacity.
3. Stations: manual sail use, crew assignment, helm behavior, anchor, boarding, centered stern ladder.
4. Navigation: wind, trim, compass/map, landmark route, weather/current, world streaming.
5. Threat/combat: one wildlife/weather/hostile-ship event; cannon four-step load; obstruction and target lead.
6. Damage/recovery: hull location, flooding, bail, emergency patch, permanent repair, sinking/wreck recovery.
7. Return/persistence: berth, trade/store, ship/cargo/crew/fittings/sails/anchor/position/hull/hole state after reload.

Incrementally separate sailing/propulsion, helm/sails, fittings/stations, hull/flooding/repair, cargo, ownership/permissions, crew/orders, and serialization components. Each extraction preserves the current tests before the next.

#### Exact ship visual language

The sloop is a believable working vessel, not a theme-park pirate prop. From profile, hull sheer, bow/stern, waterline, one dominant mast/sail group, centered stern ladder, and functional deck circulation read at 50–100 m. At helm, horizon occupies enough frame to navigate across full camera movement; mast and cloth never block the forward route continuously. Stations use silhouette, rope/wood/iron material contrast, hand-height placement, and deck circulation rather than floating labels.

Show sails at 0/50/100% through cloth area, tension, line position, and rigging—not UI alone. Cannon stages visibly differ: sponge tool in bore; powder container/charge; shot; rammer. Damage stages differ by material/state: bright fresh wood/splinters; dark opening; moving water; rough temporary patch; fitted permanent repair. Hold uses organized zones and load-state cues rather than literal display of every item. Night preserves horizon, compass, station edges, and lighthouse without flattening sea into daylight.

#### Scenario ship references

Damage-state prompt:

Consistent five-panel production reference of the same 1740–1760 oak ship-hull section at human scale: intact weathered planking; fresh cannon splinter damage with localized bright fibers; open hull hole with dark interior; emergency patch made from rough timber/canvas/resin; permanent fitted repair matching plank structure. Orthographic three-quarter close view from 3 m, neutral daylight, identical camera and plank layout in every panel. High-definition naturalistic realism, believable fasteners and thickness. No gore, fire, fantasy glow, huge explosion, modern bolts, labels, text, or changed hull geometry between panels.

Station sheet prompt:

Elitewake sloop station reference sheet: helm, sail line/cleat, anchor capstan control, cannon work area, repair point, hold access. 1740–1760 working maritime construction, oak/iron/hemp/canvas, exact dimensions beside 180 cm sailor, 1 m clear circulation where practical, hand interaction heights 80–120 cm, readable silhouettes and distinct material groupings, front/top/three-quarter views, neutral light. No floating UI, no fantasy ornament, no modern hardware, no impossible rope routing, no unsafe blocked ladder.

#### Audio target

Ship creak scales rest-to-speed; rigging scales with deployed sail and speed; close line/canvas/block-pulley events are separate; anchor release, bottom catch, and recovery differ; flooding intensity tracks active holes; bailing plays per stroke; sinking changes or stops normal ship sound. Cannon has tool stages, powder/shot handling, report/recoil, and sea/hull/land impacts. Use at least three variations for wood, rigging, and water impacts.

#### Failure, network, and evidence gates

Test owner, shared Company member, unauthorized player at every station; disconnect at helm/repair/fire/trade/cargo; owner leaves Company; streaming boundary with crew/cargo/holes; restart at sea/berth; sink online/offline owner; simultaneous ammo request; simultaneous repair; merchant/shipyard retry under latency.

Capture ship profile at no/half/full sail; helm into/across wind; every cannon-load step; intact/hole/flooding/temporary/permanent repair; empty/partial/full hold; Saltreach departure day/night; destination signature weather; sinking and wreck recovery; two-client synchronized damage.

Exit only when a packaged two-player dedicated-server voyage completes, permissions and transactions are authoritative, required state persists, damage/repair is owner-reviewed, and departure/underway/combat/damage/repair/return/night audio is auditioned.

#### Copy-ready prompt for Claude

Execute only Phase 3 in section 12 of CLAUDE.md. Map current AEWShip responsibilities and existing checks to the required sloop voyage before editing. Choose one missing vertical slice and one incremental component boundary; do not rewrite the ship monolith wholesale and do not add a vessel class. Use real inventory items, server validation, permissions, failure/retry handling, save/reload, packaged two-player testing, and the exact visual/audio evidence. Preserve manual solo station use and crew-only helm sail control. End with a full Saltreach-to-region-and-back voyage report; visual and audio acceptance remains human.

### Phase 4 — Make multiplayer and persistence trustworthy

#### Objective and boundary

Make hosted and dedicated play survive reconnects and server restarts without loss, duplication, or unauthorized control. Do not add account-service or public-Internet scope without authorization. Do not delete incompatible player data to make a migration test pass.

#### Implementation order

1. Inventory each persisted type, stable ID, authority owner, current payload, save trigger, load order, dependencies, and known failure behavior.
2. Implement the versioned save envelope and atomic generation replacement with integrity validation and prior-good fallback.
3. Add fixtures: empty/new; oldest recoverable; previous schema; current; corrupt newest/valid previous; missing asset; removed recipe/item; missing Company owner; missing ship owner; duplicate IDs.
4. Migrate one subsystem at a time: survivor; Company; ship; resources; recoverable containers; merchants/economy; structures/claims; scalable wildlife.
5. Make retry-prone transactions idempotent: buy/sell, transfer, craft, repair, cannon load/fire, ship transfer, Company operations, harvest, death/loot.
6. Add configurable autosave, save-duration/file-size telemetry, manual administrator save, clean shutdown, rotating backups, structured logs, and performed crash recovery.
7. Run the complete server matrix and keep public-Internet status separate.

#### UI and visual communication

Reconnect/loading never implies that data vanished. Use a restrained full-screen state with plain language, current step, and recoverable failure option; do not show a fake percent. Ownership denial names the owning scope and reason without exposing private identifiers. Company roles and ship sharing use a visible controller focus, explicit confirmation, and before/after state. Save feedback is small and nonblocking; repeated autosaves do not flash or chime.

Required captures: two clients viewing the same cargo and hull damage; Company policy before/after; unauthorized station denial; reconnect restoration; merchant stock before/after restart; migration success and fallback log/summary; controller focus at 1080p.

#### Audio communication

Use restrained, distinct events for invite, accepted transaction, denied action, failed save, and recovered connection. A successful background autosave normally does not play a prominent sound. The failure sound cannot resemble damage, low health, or combat danger.

#### Test matrix

Run critical transactions on listen server plus client; dedicated server plus two clients; real two-PC LAN; 100–200 ms latency; packet loss/duplicate simulation; disconnect before acknowledgement; server shutdown immediately before and after save. Measure populated-world save duration, file growth, load time, fallback time, and log volume. Test the temporary ThirdPerson session harness before replacing it; then rerun the same matrix on Coastal.

#### Exit

All required state survives restart/reconnect; current and previous versions migrate; corrupt newest restores prior valid; retries never duplicate currency/items; unauthorized clients cannot mutate protected state; two-PC LAN passes; save cost is measured; the written recovery procedure has been performed successfully; public Internet remains accurately labeled tested or untested.

#### Copy-ready prompt for Claude

Execute only Phase 4 in section 12 of CLAUDE.md. Begin with a table of every persisted type, stable ID rule, server owner, payload version, dependencies, save/load trigger, and existing test. Design fixtures and the atomic versioned save envelope before modifying payloads. Migrate one subsystem at a time and retain original data on failure. Exercise listen, dedicated, LAN, latency, duplicate, disconnect, and shutdown boundaries. Never silently zero inventory, currency, Company, or ship state. Produce the exact synchronized-state, denial, reconnect, stock, and migration evidence. Do not start public-Internet/account-service work without owner authorization.

### Phase 5 — Replace placeholders with one coherent production language

#### Objective and boundary

Replace the hero-path placeholders with performant art and audio using Unreal's included tools, properly acquired zero-cost public assets, and original Scenario-assisted material. The goal is one controlled language, not the largest library. Do not delete a placeholder until its replacement is integrated, referenced, packaged, performance-checked, and owner-approved.

#### Production order

1. Create a small reference gallery map containing a 180 cm mannequin, 1 m/5 m/20 m scales, neutral daylight, neutral overcast, night, water edge, material spheres, and performance markers.
2. Approve one Plains material/prop/foliage/lighting/audio family.
3. Finish Plains spawn and the full first-30-minute route.
4. Finish Saltreach sea silhouette, harbor mouth, market, tavern, shipyard, and night-light hierarchy.
5. Finish the sloop exterior/interior, stations, sails, damage, cargo states, and sound layers.
6. Finish one hero vista and one complete gameplay route for Winter, Swamp, Desert, and Jungle.
7. Extend only the accepted kits to secondary areas.
8. Optimize textures/materials/meshes/audio/streaming, validate package inclusion, then remove superseded placeholders.

#### Free-resource acquisition ladder

Use this order and record every external/generative asset in ASSET_LEDGER.csv:

1. Reuse or modify current project assets when quality and rights are adequate.
2. Use Unreal 5.8 built-in systems and editor tools: Modeling Mode, Geometry Script, Landscape, Water, PCG, Niagara, Control Rig, IK Retargeter, MetaSounds, Material Editor, UMG/CommonUI, World Partition, HLOD, Insights.
3. Evaluate official Epic samples or zero-cost Epic/Fab content in an isolated intake map. Copy only the necessary pieces; do not drag in an architecture to obtain one feature.
4. Evaluate zero-price Fab Standard or CC0/CC-BY content with a direct listing/license record. Treat Reference-Only, UE-Only, attribution, and additional terms explicitly.
5. Use Scenario to make original references, texture/decal/icon candidates, ambience, Foley, and music drafts under the rules in sections 9–11.
6. Model, texture, retarget, or synthesize the gap in-house when imported kits would fracture the style.

Do not assume Paragon, Infinity Blade, Lyra, Game Animation Sample, Starter Content, or a free Fab pack fits the historical visual language. They are candidates or learning references, not automatic production content.

#### Intake checklist

Before import: listing URL; publisher; acquisition date; zero price proof; license and attribution; engine restriction; plugin/version; source size; expected cooked size; topology/UV/material count; texture resolution/memory; collision; skeleton/root motion; LOD/Nanite; naming/folder impact; warnings; visual comparison; generative-use restriction. Test in the intake gallery, decide accept/modify/reference-only/reject, and migrate only selected files into /Game/Elitewake.

#### Saltreach visual specification

Saltreach is a busy frontier Freeport. From 1 km, lighthouse/signal tower, clustered pale masonry and dark weathered roofs, ship masts, cranes, and the harbor mouth make the silhouette. At 200–300 m, piers, shipyard slip, market awnings, route lighting, and berths establish functions. At 20–30 m, props form believable work groups: timber and saw area; rope/spar store; repair scaffolds; fish/food/cargo stalls; tavern seating/service. At 2–5 m, wood grain scale, iron fasteners, rope diameter, wear, interaction height, and collision hold up.

Architecture uses pale plaster/limestone lower levels, weathered timber upper structures, restrained canvas, dark roof forms, and oxidized copper accents. Market lanes remain clear and asymmetrical; people work, walk, or converse for a reason. Night hierarchy is lighthouse first, harbor route second, market/tavern third, minor windows last. Do not repeat identical lamps down every street, overfill the scene with barrels, use pristine white resort plaster, or turn the port into ruins.

Saltreach Scenario prompt:

Elitewake Saltreach Freeport production reference, high-definition naturalistic realism, 1740–1760 frontier harbor. CAMERA: gameplay ship approach at sea level, 1 km distance, eye height 4 m, 70-degree horizontal FOV. Show a readable harbor mouth; one lighthouse/signal tower as primary vertical; layered masts, cranes, clustered dark roofs, pale weathered masonry, timber upper structures, restrained canvas, working piers and shipyard slip. Late-afternoon side light with neutral exposure; water and horizon readable. The town is active, repaired, practical, and imperfect—not pristine and not ruined. Natural asymmetry and plausible construction. No modern marina, palm-resort cliché, giant castle, fantasy skyline, identical lamps, barrel clutter, generated signs/text, crowds posing at camera, or cinematic depth of field.

Create matching sea-approach, 250 m harbor, 25 m market lane, 3 m merchant stall, reverse, night, and storm references with the same geography. Do not accept a set if lighthouse, harbor mouth, roof arrangement, or main route moves between views.

#### Sloop and character/animal content

Hero ships require consistent orthographic profile/top/front/rear and human-scale deck/interior views before production geometry. Base hull excludes permanent sails; hardpoints and centered stern ladder remain readable. Verify deck/headroom/ladder/cannon contact with the real capsule and animation.

Each production animal needs a consistent front/back/left/right/top/underside reference, real species anatomy, scale, rig, idle, walk, run/sprint, relevant attack/action, transitions, collision, navigation, and audio variations. Treat reference art, mesh, texture, rig, animation, audio, integration, behavior, performance, and owner acceptance as separate milestones. Do not invent species to fill an asset-pack gap.

#### Texture and Scenario rules

Generate material studies as tile candidates with specified real-world scale, albedo/roughness/normal/height intent, neutral lighting, and no baked directional shadows. Never ship an AI image as a physical material without checking tiling, perspective, seams, color-space, PBR ranges, compression, mip behavior, and distance readability. Icons use a consistent camera, stroke/silhouette, light direction, palette, transparent background, and no generated text.

Material prompt:

Seamless square material source study for Elitewake: [specific material and exposure story], real-world tile covers [meters], high-definition naturalistic realism, orthographic flat capture, even neutral light, no directional shadow, no object silhouette, no text, no border. Show medium and large variation caused by [salt/sun/water/hand wear], physically believable joints and grain, restrained color. Intended for separate albedo, roughness, normal, and height authoring—not a finished PBR set. No perspective, vignette, dramatic lighting, random stains, modern treatment, or repeated obvious motif.

#### Audio production batch

Produce in this order: core footsteps/gather/survival feedback; Plains beds; Saltreach market/tavern/shipyard/pier; sloop hull/deck/rigging/canvas/line/helm/anchor/flood/repair; cannon stages/impacts; other regional stems; wildlife actions; restrained music layers. Generate 3–6 variations for repeated one-shots, keep stems separate, record model/output/prompt/settings/cost/input rights, import lossless masters, and implement attenuation/concurrency before owner audition.

#### Evidence and exit

For each asset family provide the gallery turntable/scale, source/license row, memory/material/LOD report, collision, in-context required cameras, day/night/weather where relevant, package inclusion, before/after performance, and owner review status. Exit when the first-30-minute route, Saltreach, sloop, and one hero route per remaining region use an accepted coherent language; no unlicensed source is packaged; hero placeholders are removed only after replacement; target performance and memory hold; owner accepts visual sets and audio families.

#### Copy-ready prompt for Claude

Execute only Phase 5 in section 12 of CLAUDE.md and name one hero-path asset family. Audit existing assets before acquiring or generating anything. Follow the free-resource acquisition ladder and isolated intake gate; add complete ASSET_LEDGER.csv rows before migration. Use the exact Elitewake palette, scale, texel density, construction, camera, screenshot, Saltreach/sloop/animal, Scenario, and audio rules. Import only used pieces. Preserve the current placeholder until its replacement is integrated, packaged, profiled, reference-validated, and owner-reviewed. Never claim visual or audio quality from metadata or a test alone.

### Phase 6 — Controlled alpha hardening

#### Objective and boundary

Turn the accepted core loop into a reproducible private alpha: install, host/join, play the first session and voyage, save/reconnect/restart, report a problem, and recover. This is hardening, not a content-expansion phase. Freeze new islands, classes, large mechanics, and broad art kits.

#### Release slices

1. Define supported Windows version, CPU/GPU/RAM/storage, graphics presets, input devices, server topology, save compatibility, and known limitations.
2. Create a clean versioned development package with correct maps/assets, icon, configuration, crash/log paths, no secrets, no internal reports, and no intake/rejected content.
3. Test clean-machine install/launch, title/settings/input, host/join, first 30 minutes, complete voyage, save/quit/reload, disconnect/reconnect, server restart, and uninstall/reinstall with preserved save policy.
4. Run performance/streaming/network/save soak tests and fix blockers, crashes, loss, duplication, authority exploits, and severe readability failures before cosmetic issues.
5. Produce a concise tester guide inside the distribution channel, structured feedback form, build/commit identification, privacy statement, log collection, save backup/recovery, and rollback plan.
6. Test the release and rollback procedure with a small internal ring before adding testers.

#### Visual and audio alpha gate

At Low/Medium/High or the approved presets, verify title/UI text, Plains spawn, Saltreach day/night, all five offshore silhouettes, sloop stations/damage, storms, caves, and critical prompts. Capture frame time/VRAM/streaming behavior rather than screenshots alone. Confirm graphics presets do not remove navigation cues or turn night into black.

Listen through the entire first session and voyage on ordinary stereo speakers and headphones. Check repetition, missing surface types, ambience transitions, UI spam, danger masking, ship-state mismatch, and excessive peaks. Alpha can contain labeled placeholders, but it cannot contain broken, misleading, unlicensed, or painfully repetitive audio.

#### Priority order

P0: crash, corrupt/lost save, inability to launch/join/progress, remote authority exploit.
P1: duplication, ownership bypass, severe performance/streaming blocker, broken reconnect, unreadable required UI.
P2: balance/pacing/animation/visual/audio problem that does not block the loop.
P3: polish or content suggestion.

#### Exit

A clean machine installs and launches; two physical machines complete first session and voyage; save/reconnect/restart and fallback recovery pass; agreed performance and network budget holds; package contains no secrets/unlicensed/rejected assets; build/commit and logs are identifiable; rollback has been performed; owner approves the private-alpha release and known-issues list.

#### Copy-ready prompt for Claude

Execute only Phase 6 in section 12 of CLAUDE.md. Freeze feature/content expansion. Define the target machine and measurable release budgets, produce a clean versioned private-alpha candidate, and run clean-install, title/input, first-session, voyage, multiplayer, persistence, restart, soak, package-audit, and rollback gates. Rank every finding P0–P3 using the guide and fix P0/P1 before polish. Verify visuals across presets and audition the full route on speakers/headphones. Do not publish publicly, invite testers, expose credentials, or declare alpha accepted without owner authorization.

## 13. Human review forms

### 13.1 Visual location review

Record commit, map/location, asset/gallery version, reviewer/date, resolution/preset/hardware, time/weather set, and before/after camera path.

Claude checks: same camera/FOV/conditions; required distances/reverse/day/night/weather; beauty images free of overlays; diagnostics present; no missing material; no obvious critical intersection; capsule fits; landmark visible; performance captured. Owner scores 1–5: immediate identity; focal hierarchy; natural navigation; believable scale; material cohesion; exposure/weathering story; inhabited feeling; day readability; night readability; weather readability; historical tone; desire to explore. Decision: accept; accept with minor fixes; revise same cameras; reject direction. Record exact revisions.

### 13.2 Visual asset review

Record asset, source/license, project path, dimensions/pivot, intended role, memory and material count. Claude checks ledger, collision, UVs, texture sizes, LOD/Nanite, shadows/reflections, interaction/animation contact, and consistent turnaround. Owner answers: silhouette at gameplay distance; Elitewake proportion/material fit; generated geometry/anatomy/text/construction errors; generic/regional/hero status; changes required before repetition.

### 13.3 Audio review

Record commit/path, Scenario model/output or third-party source, prompt/settings/license, trigger/attenuation, format/channels/sample rate/duration/peak, and listening devices. Claude checks decode, clipping/silence, loop, variations, attenuation/concurrency, trigger/replication, and ledger. Owner scores 1–5: source/material identity; period/region fit; synthetic artifact absence; transient/tail; meaning without looking; variation; close/medium/far behavior; mix priority; repetition comfort; speakers/headphones. Decision: production source; placeholder; edit; regenerate; reject.

### 13.4 Full-sequence review

Record build, commit, server, players, inputs, route, time/weather, and capture. During uninterrupted playback timestamp navigation failures, unclear interactions, exposure jumps, wrong/missing surface sound, repetitive ambience/fauna, masked danger/dialogue, ship-state mismatch, hero placeholders, frame/streaming/LOD hitches, and successful place/danger/reward moments. End with three strongest moments, three highest-priority problems, and accept/revise decision for the phase.

## 14. Verification commands and evidence discipline

Adjust only the project path when the canonical checkout moves; do not change maps or targets to make a failure disappear.

Fast source/world gate from the repository root:

    python -m unittest discover -s Scripts/Tests -p "test_*.py" -v

Editor compile on the canonical Windows installation:

    "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" EWEditor Win64 Development "C:\UnrealProjects\EW_CLEAN\EW.uproject" -WaitMutex -NoHotReloadFromIDE

Game compile:

    "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" EW Win64 Development "C:\UnrealProjects\EW_CLEAN\EW.uproject" -WaitMutex -NoHotReloadFromIDE

Use the focused scripts in Scripts/Verification only after reading what each changes, launches, captures, and leaves behind. Prefer the narrowest relevant Play check, then run integrated/title-to-coast/first-voyage/session lifecycle and package checks for phase gates. A script filename is not evidence that it passed; retain timestamped output tied to commit and map.

Before every commit:

1. Inspect the full diff, staged file types, large files, LFS pointers, generated directories, secrets, external paths, and unexpected deletes.
2. Run tests affected by the change plus the fast world suite.
3. If Unreal content changed, validate references, redirectors, map load, package inclusion, and the relevant Play check.
4. If visuals changed, create fixed-camera before/after and diagnostics; if audio changed, record technical analysis and audition state.
5. If a third-party or Scenario asset changed, update ASSET_LEDGER.csv in the same commit.

## 15. ASSET_LEDGER.csv rules

Use one row per product or generated family, with child rows when files have different licenses/restrictions. Required columns already exist in the repository ledger. Boolean fields use TRUE/FALSE/UNKNOWN, not prose. PricePaid is 0.00 only when acquisition was actually zero cost. SourceURL points to the listing or model card, not a search result. LicenseURL and acquisition evidence must remain retrievable. Scenario rows include exact model ID, output ID, input-rights verification, and owner approver. Unknown rights means the asset stays out of production/package.

## November 4 recovery and island layout decision

The owner has returned development to Codex after the saved WIP checkpoint `4b01a28c`. This section supersedes earlier handoff restrictions and island crossing targets. Keep the existing 20 islands: four in each of Plains, Winter, Swamp, Desert, and Jungle. Preserve their distinct proportions and resource/wildlife assignments, exactly one village per region, the existing compact footprints, and broad open-water lanes. The intended walking experience is the current roughly 5–14 minutes across an island; do not enlarge islands to meet the older 15–20, 30–45, or 6–17 minute targets. Walking routes are no longer tested (owner, November 6; see below).

Keep the three crescent coves on Plains3, Desert3, and Jungle3, with different silhouettes. Each sea cavern must accept a ship from open water, conceal a parked ship from direct sea sight, and permit a player to leave the berth on foot. Make Plains3 and Jungle3 walk-through caverns with safe inland exits onto explorable island ground. Make Desert3 a covered shore berth with a safe bridge or walkway onto the island. These assignments are provisional if terrain proves unsuitable; preserve the two-through/one-bridge mix. Verify ship clearance, water depth, walkable collision, entry and exit in Play. A boat remains visible on the game map even under a roof. Built November 5 (delegated; `world_terrain` SEA_* constants, `Cave.berth`, `Cave.exit_path`):
- Each cavern has a 110 m passage that is widest at the waterline (22 m wide, 29 m roof) and swings 23 m aside and back, so no straight sightline from the sea reaches the 44 × 58 m pool.
- The formation footprint is unchanged.
- Plains3 has a walkway along the pool and up through the back (56 m, rising 15 m).
- Desert3 has a level walkway out the back onto the sand.
- Jungle3 has a rock ledge looping the pool one and a sixth times up to the plateau (181 m, rising 57 m, about 19°).
- Verified in Play for the brigantine: entry, a half turn at the berth, and hidden from every sea viewpoint (`verify_cavern_ship_fit_play.py`). A survivor walks out of each berth and back (`verify_cavern_walks_play.py`). The Cavalier's fit stays pending until it is built.

Climb-outs (owner, November 5: a swimmer must never be stuck against a steep coast). Every stretch of coast lies within a minute's swim (150 m) of a way out onto the island's main ground, checked offline by `Scripts/Setup/coast_exits.py` and its test. A way out needs water shallow enough to stand in beside it, since a swimming character never steps up. The harbour is held to the same rule: its pier ladders are not climbable, and neither is the slipway. Built November 5–6:
- 19 climb-outs on Winter1–4, Desert3 and Jungle2–4 (`world_climbouts.py`, placed by `coast_exits.py --plan`; `world_terrain.Climb`).
- Each is an 8 m path with rock-cut sides: a 10° ramp up out of the water, a level 5 m landing, then 20° up the shore. On a cliff it runs as a ledge along the face, or as a ravine where a sheer rim leaves no room. Each ends on broad walkable ground.
- Saltreach's rock steps (owner, November 6): a 14 m inlet with a stone ramp cut into the headland, 150 m out along the harbour's left wall, where 16–25 m of water stood against it (`world_terrain.HARBOUR_STEPS`). The piers' water is unchanged. The whole harbour now lies within 52 m of a way out.
- Trees, rocks, plants and animals keep off them (`world_terrain.near_climb`); `clear_climbouts.py`, the last rebuild step, clears any already standing there.
- The starter's two long straight shores were sheer 57 m underwater walls: its distance was measured along rays from the old east end. They now have a beach and seabed (`StarterIsland.distance`). The shoreline, the arrival end and Saltreach's harbour are unchanged; about 100 m of wall remains by the arrival, with a way out within 43 m.
- Verified in Play: a survivor swims in from deep water and walks out and up every climb-out and Saltreach's steps, and ashore across the starter's fixed shores (`verify_climbouts_play.py`, 25/25 on November 6). Graybox; visual review pending.

Island crossings measured in Play, November 5–6 (`measure_walking_routes_play.py`, along each island's long axis and across it, at walking speed):
- 39 of 40 routes arrive, taking 4.1–15.9 minutes. Starter across is 4.1 minutes, kept by design.
- Swamp routes include 5–39 s of swimming across channels; every other route is on foot.
- Desert3 across did not arrive: its path ran along the brink of the crescent cove and the walker slipped into the water. Left as is (owner, November 6); Desert3's coast has ways out within 150 m.
- The route planner (`estimate_walking_times.py`) uses 38° grid edges and rules out ground surfaces steeper than 44°. It treats cave rock as solid and starts and ends routes on level ground. The walker jumps out of water and hops at banks, as a player does.

Owner, November 6: two rules replace earlier ones.
- **No more walking-route testing.** Do not run `measure_walking_routes_play.py` or re-plan routes with `estimate_walking_times.py`. This replaces the measured-walk parts of section 5.1, the section 5.7 acceptance checks and the island-size row of section 4. The scripts stay for reference.
- **No full world rebuilds.** Each rebuild costs hours and credits. Change only what a task needs: run the single script or `rebuild_world.py` step it touches (`EW_REBUILD_ONLY`), on only the islands it touches (`EW_TERRAIN_ISLANDS`). Placement scripts add what is missing rather than clearing and replacing the world. A full rebuild needs the owner's go-ahead.
- Work toward the end goal: playable gameplay milestones (sections 12 and 16), not repeated re-verification of finished world shape.

Wildlife on every island (November 6). Seven placeholder species were added in the existing lofted style: red deer, caribou, grey wolf, hare, snake, polar bear and crocodile (`build_animals.NEW_SPECIES`, built by `add_wildlife_species.py` without a rebuild). There are now 337 animals, and every island carries land animals from its own region. `place_animals.py` now only adds what each island is missing. Verified in Play: the census, and one of each new species standing on the ground and moving (`verify_wildlife_islands_play.py`). November 7: the other twenty species of the island plan were added the same way (`build_animals.MORE_SPECIES`): wild horse, great egret, mountain goat, red fox, golden eagle, harbour seal, walrus, grey heron, pond turtle, river otter, bullfrog, gazelle, desert scorpion, vulture, golden jackal, oryx, scarlet macaw, tapir, jaguar and capuchin monkey. Most reuse an existing body at the species' size and colours. The jaguar and scorpion attack; the walrus is neutral like the elephant; the rest flee. 174 placed add-only, always loaded; tree dwellers now find the forest stands. 509 animals in all, every island carrying its full planned mix and every species in its region. Verified in Play: the census, and one of each of the twenty standing on the ground and moving (`verify_wildlife_islands_play.py` with `EW_WILDLIFE_SET=MORE`). Every animal is still a rigid placeholder (Phase 5); visual review pending.

Forests (owner, November 6: dense, strategically placed forests with lots of bushes and plenty of open ground; every tree its own size, thickness, shape and kind). Built November 6:
- 231,505 trees in stands with clearings and meadows between, about 40–50% of each island's land (80% in the Jungle), with lone trees in the open. The Desert has palm groves near the shore. Trunks stand at least 5 m apart.
- Species mix per region (`forest_plan.MIX`): Plains oak with ash and birch; Winter birch and spruce; Swamp spruce and ash; Desert palm; Jungle ash and maravai. Six models per species.
- Each tree has its own age (saplings to giants), girth, height, lean and turn.
- 177,567 walk-through bushes, thickest along forest edges.
- Planned offline by `forest_plan.py` (all cores, about 3 minutes) and placed by `build_forests.py` without a world rebuild. The old one-actor island trees are gone (`build_coastal_flora.ISLAND_TREES = False`); the starter keeps its own authored oaks.
- Each stand is an `AEWForest` (C++), instanced and cheap. A hatchet's first blow turns the tree into an ordinary `AEWHarvestTree`, which works, falls and fades as before. The stand regrows the tree after 20 minutes if its place is clear. Felled forest trees are saved with the world (November 6): a reload keeps them down for the time they had left; a tree being chopped but still standing comes back whole (`verify_forest_save_play.py`). A felled log lying on the ground is not saved yet.
- Verified in Play (`verify_forests_play.py`): the census, a chop that gives wood and leaves the forest tree down, and screenshots in each region. Cost measured by `diagnose_forest_cost_play.py` on the RTX 4070 in a dense Plains stand: 25.4 ms per frame with forests, 20.2 ms without. The GTX 1660 Super is not measured yet. Placeholder tree art; visual review pending.

Ice sheets (owner, November 6: different sheets of ice around the Winter mountains only, like the real Arctic, as tall as the nearest cliff or landing; the ice is solid; not literal blocks). Built November 6:
- 41 separate sheets around the Winter mountains (Winter1 9, Winter2 8, Winter3 10, Winter4 14), each 0.7–5.5 ha and longer down the slope than across.
- Each sheet's surface is the slope smoothed and raised by a thickness near the height of the nearest cliff or bank (12–45 m). A high rock can poke through. Each ends in a steep ice wall, about 70°, too steep to climb.
- Shapes come from `glacier_shapes.py`; `build_glaciers.py` makes one mesh per sheet.
- Material: blue ice and crevasses on the walls, snow on the tops.
- Full collision. Trees, bushes, rocks, plants and animals under the ice were removed.
- Verified in Play (`verify_ice_play.py`): on each Winter island a survivor walking at a wall is stopped and one dropped on top stands on the ice. Visual review pending.

World Partition streaming (owner, November 6: "Start streaming"). Built November 6:
- Coastal Playground is now a World Partition map, converted in place (`WorldPartitionConvertCommandlet`). Every actor is its own file under `Content/__ExternalActors__/Elitewake/Maps/Lvl_CoastalPlayground` (22,244 files); the map file itself is 14 KB, which ends the 2 GB GitHub limit. The forests sublevel was merged in and removed.
- `setup_world_partition.py` streams only the ground-cover foliage (2,906 cells); everything else (islands, forests, animals, ports, ships, ice) stays always loaded for now. Near the player about 12 cells (210,000 instances, out to about 400 m) are loaded instead of all 7.9 million; they unload when the player travels.
- Setup scripts open and save the map through `world_map.py` (`open_map` loads every actor on a partitioned map; `save_map` saves each changed actor file).
- Unreal must start with `-SCCProvider=None` (the Play-check runner now does): otherwise it checks each of the 22,000 files against source control at startup and never finishes loading. The local list it keeps is `Saved/SourceControl/UncontrolledChangelists.json`; the 39,000-entry version was moved aside.
- Verified in Play on the converted map: `verify_streaming_play.py` (cells near the start and at Jungle1, unloading after travel, 21-23 ms per frame on the RTX 4070), and the forests, wildlife and ice checks. Video memory of the packaged game at spawn (Windows' per-process counter, 1920×1080, RTX 4070, November 6): Low 4.62 GB, High 4.81 GB; Low with ray tracing off, as a card without ray-tracing hardware runs it, 4.23 GB, under the 4.5 GB budget. The 4070 also gives the texture pool 7 GB (70% of its memory), more than a 6 GB card would. This is an estimate on the RTX 4070, not a GTX 1660 Super measurement, and covers the spawn only, not the densest scene. The minimum-machine test is ready: every package carries "Run 1660 test.bat" beside its Windows folder (Scripts/Release). On the 1660 PC it runs the game's benchmark mode (`-EWBenchmark`, `UEWBenchmarkSubsystem`, not in Shipping: spawn, Saltreach and one island of each other region, frame and GPU times) on Low at 1080p, samples video memory with Windows' counter, and writes a results file. Dry run on the RTX 4070 (Low, ray tracing on): GPU 4-6 ms at every stop, video memory 3.7-4.6 GB at the stops and 4.5 GB at most between them on a second run; the first run of a new build peaked at 6.45 GB, most likely compiling shaders. Still to do: streaming the islands themselves with HLOD for distant ones, and running the test on the GTX 1660 Super.

Open-ocean reefs (owner, October 31: "like 3 reefs out in the ocean"). Built November 6:
- Three reefs, Ocean1-3, on the three shallowest seamounts (`world_reefs.py`): 12-15 m, 17-20 m and 18-20 m deep, each 2.2-2.3 km from the nearest shore and far from every port, in three directions (toward Jungle, Winter and Swamp).
- 70 corals each, in four kinds (branching, mound, fan, pillar) and five glows that breathe slowly; solid. `build_reefs.py` replaces only its own corals, clears the seabed foliage under each reef, and adds a hammerhead and a manta ray over a reef that has none. No rebuild. Reef actors are always loaded (`world_map.keep_loaded`): an actor added to the partitioned map is otherwise streamed, and a client far away would not have it.
- Verified in two-player Play (`verify_reefs_play.py`): every coral on the floor and under water, glowing, solid, and the shark and ray over each reef on server and client. Captures by day, at night and from the surface: `capture_reefs.py`, `Saved/Screenshots/Reefs`. Underwater the blue water tints every glow toward blue; visual review pending.

Mined island specialties (CLAUDE.md 5.7). Built November 7:
- Six ores as items and mineable deposits, each only on its planned islands (`world_specialty_ores.py`): copper ore on P2, D4 and J2; iron ore on P2, W3 and D4; sulfur ore on D2; salt on D3; amber on D4; bog iron on S2. 138 deposits in short veins: copper, iron and amber on hill slopes, sulfur and salt on low flats, bog iron on wet low ground.
- Any pickaxe mines them, except sulfur, which needs a Metal pickaxe or better (section 4). No Stone-tier pickaxe exists yet, so none is required. A deposit holds 4 to 8 and returns an hour after it is emptied.
- `build_specialty_ores.py` replaces only its own deposits; always loaded. Tests: `test_world_specialty_ores.py` (on its islands, absent from the rest of each region, matching the plan). Verified in Play (`verify_specialty_ores_play.py`): the census, a wooden pickaxe mining copper, sulfur refusing it and yielding to a Metal pickaxe.
- A Port's resource trader buys them (Copper each, tuning: copper and iron ore 10, sulfur 18, salt 6, amber 40, bog iron 6); verified in the two-player Saltreach check, where Oskar Brann buys copper and sulfur ore with the wood.
- Smelting (November 7, `add_smelting.py`): at a lit fire, 2 iron ore + 1 wood make an iron ingot, 2 copper ore + 1 wood a copper ingot, 3 bog iron + 1 wood an iron ingot (8 s each; ingots sell for 30 and 28 Copper). The Metalwork skill unlocks them with the Metal Pickaxe. Verified in Play (`verify_smelting_play.py`): no fire, no smelting; beside a lit fire, an iron ingot from 2 ore and 1 wood. Nothing uses ingots yet.

Gathered island specialties (CLAUDE.md 5.7). Built November 7:
- Eleven items gathered by hand with E, each on its planned island only (`world_gathered_specialties.py`): clay and sand on P3, reeds on S1, peat on S2, spruce resin on S3 (at the foot of spruces), mushrooms on S4, dates and coconuts on D1 (under the palms), wild fruit on J1, spices on J3, vines on J4. 180 patches of a few units each; no regrowth yet, like every hand-gathered resource.
- Dates, coconuts and wild fruit are food that spoils like berries; the rest are resources. A Port's resource trader buys them all (tuning: spices 15, resin 6, others 1-4 Copper).
- `build_gathered_specialties.py` replaces only its own patches; always loaded. The generated pile meshes carry a simple box collision, since the aim is a simple-collision trace. Tests: `test_world_gathered_specialties.py`. Verified in Play (`verify_gathered_specialties_play.py`): the census, gathering clay and gathering dates (food) into the pack.
- Not yet: pitch from resin, uses for clay, peat, reeds and vines, and regrowth. Coal still lies on all four Winter islands' mountains (build_crystals.py) though section 5.7 makes it W1's specialty; left as built until the owner decides.

Open bug (November 7): in Play the moored sloop is neither held by the Saltreach shipyard nor owned, though the saved map marks her held (`held_by_yard`, read back in the editor). Elias therefore cannot sell her and `verify_voyage_ready_play.py` fails at step 0. No save file restores her; `diag_sloop_yard_play.py` reproduces it in about two minutes. Suspected: how the World Partition map hands this actor to Play.

The November 3 full rebuild stopped at `build_saltreach_welcome`: the map failed to load after earlier world steps reported success. The November 4 checkpoint restored a usable prior map and preserved recovery files in `C:\ELITEWAKE\Recovery_20261104_MapSaveFailure`; do not treat the failed result as a playable 20-island rebuild. First inspect map integrity, free space and recovery state. Then fix the smallest reproducible blocker, build and verify cavern access, and use the narrowest safe rebuild steps rather than rerunning hours of terrain by default. Keep generated work and recovery copies. Verify Python, C++, Play, map markers, routes, and screenshots before claiming the world playable. Do not commit or push until the resulting state is coherent and verified.

## 16. The next correct build order

After cleanup, do not wander across the backlog. Work in this order:

1. Finish Phase 0 and freeze the canonical baseline.
2. Audit and accept Phase 1 as one uninterrupted 30-minute experience.
3. Complete Phase 2 one island at a time, beginning with Plains/Saltreach interfaces.
4. Complete Phase 3 with one sloop voyage before expanding vessel content.
5. Harden Phase 4 persistence/authority before claims or broad public tests.
6. Use Phase 5 to replace hero placeholders along the already working routes.
7. Run Phase 6 only when the full core loop is stable enough to harden instead of redesign.

If uncertain what to do next, choose the earliest unmet exit criterion in this order and propose the smallest testable slice that advances it.
