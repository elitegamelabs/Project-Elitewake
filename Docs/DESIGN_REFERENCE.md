# Design reference

Updated October 6, 2026. This is the current authority/requirement/decision index. [Historical source reviews](ARCHIVE/CONTEXT_AND_DESIGN_REVIEWS.md) preserve the original cross-reference work; they are not competing current plans.

<a id="authority"></a>

## Authority

1. Explicit owner decisions take precedence.
2. **Elitewake Shared Design Authority & Cross-Team Guide** is the common design authority: governance, identity, terminology, cross-team contracts, open decisions, retired rules and the authority change log. The supplied copy identifies its source revision as October 5, 2026; the October 6 owner decisions below override its older wording and await incorporation into the working guides.
3. Team guides: **Elitewake Game Development & Systems Bible** (systems and implementation) and **Elitewake Creative & World Bible** (world, characters, narrative and visual story).
4. Repository docs and work notes, including this file. Repository code and verified tests establish implementation, not new design rules.

The October 5 **Elitewake Master Game Design Bible — Authoritative Revision** is an archive only. Do not edit it or treat it as current authority. Its section labels (§§0–30, appendices A–F) remain the source references used by the guides and the tables below. Within that source, Section 30 overrides older conflicts, as the Shared guide records.

Preserve each guide's status labels: **CONFIRMED**, **FUTURE**, **TBD** and **RECOMMENDED**. Unresolved values stay TBD until the owner decides them; do not invent them. Creative changes that affect gameplay update the Shared guide first, then Development. Technical constraints that would change story or world become Shared issues before Creative canon is rewritten.

Ships are the center of play and highly customizable. Land bases are allowed but temporary, and players and wildlife can raid them. Preserve Prepare → Sail → Discover → Fight/Explore → Loot → Escape → Upgrade → Sail Farther. The first private beta focuses on single player while retaining server authority. "THE SHIP IS HOME", the Village name, Davy Jones, the old raft opening, eight-hour cycle and older economy are superseded; do not revive them from historical records.

<a id="october-6"></a>

## October 6 owner decisions

Authority: October 6 owner decision brief supplied by the owner. These supersede conflicting wording in the Shared guide, team guides and archived Master Bible. The reviewed DOCX copies have not yet incorporated these decisions.

1. **Ship identity.** "THE SHIP IS HOME" is retired. Ships are highly customizable. Land bases are allowed but temporary, and players and wildlife can raid them.
2. **Ports.** Villages are renamed **Ports**. Each server has four Port islands, each in a weather biome. Carryover of existing Village rules (PvP safety, specialized vendors, Ferryman links, prologue arrival and Innkeeper mission) is proposed and awaits owner confirmation; the rename does not itself approve new rules.
3. **Servers.** Official servers have wipes, with progression rewards. Unofficial servers use host-defined rules. Players never see a server grid.
4. **Interact.** The keyboard Interact key is **E**, now CONFIRMED. `EWPlayerController.cpp` already maps E and controller X (face button left).
5. **Stamina.** Stamina recovers while walking as well as while stationary. This supersedes the stationary-only wording in §30.15. Five-second base tuning, upgraded-capacity scaling and other survival rules keep their separate gates.
6. **Hand injury from punching trees.** Tree punching uses Attack, not Interact. 25 hits on trees with bare hands injures the hands, which then need a bandage. Without a bandage, the injury becomes an infection after 10 in-game minutes. The infection is fatal without a Surgeon.

TBD from these decisions (ask, do not assume):

- Land bases: how long a base lasts, what makes it decay or expire, and which wildlife raid it and how. Temporary-base lifetime is distinct from the existing five-real-day inactivity threshold unless the owner explicitly unifies them.
- Ports: which weather biome each Port uses, and each Port's identity and vendor stock.
- Wipes: schedule, which progression rewards carry over, and how they are granted. Unofficial servers: which rules hosts can change.
- Hand injury: whether the 25 hits count per tree, per session or across the character's lifetime; whether resting or other actions reset the count; whether gloves or tools affect it; what the injured state does before infection; how long a fatal infection takes and what the Surgeon must do to treat it; how the bandage is crafted or obtained. The real-time length of 10 in-game minutes depends on the game clock, which is not yet defined.

## Owner clarifications

Authority: direct owner message, October 5, 2026. This clarifies the archived Bible's zero-currency start and rare-rye sale without changing the original DOCX. "Village" in the original wording now reads "Port" (October 6 rename).

1. The survivor has zero currency until the rare rye is sold. The rye remains in the player's inventory through the Port handoff; discarding tutorial tools/supplies must not discard this mission cargo.
2. The player asks the female innkeeper whether they may stay the night for free.
3. She explains that work or goods must be traded to pay for the room and shows the player around the town square.
4. She introduces nearby local shopkeepers. They introduce themselves during this mission; their quests are available later in the game, not activated by these introductions.
5. On reaching the general merchant, the player receives the option to sell the rye in their inventory.
6. The sale's 250 Copper is added to the player's funds as soon as the introduction mission is complete. Do not credit it at the earlier prologue/Port arrival or silently credit it earlier during the tour.

Room price, any later room-payment transaction, refusal/revisit behavior for the sale, and exact mission-completion trigger beyond this sequence remain unspecified. Do not invent a room deduction, forced sale, or extra quest. The Journal remains a tutorial/reference system; a guided introduction mission does not automatically convert it into a quest log.

## Current unresolved design points

1. **Stamina scaling/recovery (§§29.9,30.15):** does the five-second timing apply only at base 100, letting +15 investments extend sprint, or stay constant at every capacity? Walking recovery is confirmed by the owner; five-second base/upgraded-capacity scaling still needs reconciliation. Exact jump scaling is also unspecified.
2. **Needs/stat scaling (§§6.1,29.9,30.15):** is 15 minutes the idle/base benchmark, and how do activity and upgraded food capacity alter it? Earlier movement-versus-idle rule is retained but multiplier is not specified. Health-loss wording says about ten minutes but doesn't define starting/max-health basis or stacking when both needs are empty.
3. **Crafting location (§§5.8,29.16,30.21):** exact five top-level tabs omit Crafting, while other sections call it a normal Crafting tab. Is crafting a nested Inventory panel/tab? Controller virtual cursor is expressly crafting-specific; ordinary inventory focus can remain unless superseded.
4. **Starter raft/claims (§§29.2,29.5,30.6):** baseline raft recipe versus Small Shipyard prerequisite and claimed-territory placement need a precise early-game route, without reviving tutorial shipyard construction.
5. **Ship stat upgrades (§30.7):** are crew counts initial caps or absolute ceilings given Crew Capacity upgrades? Schooner configured-cannon count could change if a utility attachment replaces a cannon. Define handling before implementation.
6. **Currency scope (§§28.5,30.17,30.19):** player UI currency is retained, while crew physically carry wages. Define NPC-loot conversion and avoid treating all Copper as corpse-proof.
7. **Remaining combat/system integration:** Common Magnum 40 vs 42 before headshots is explicitly unresolved; bed cooldown reset/decay rule unresolved; ordinary-death level/skill retention remains open; administrative ban policy needs operational details before multiplayer.

Resolved historical conflicts should not be re-asked as if new: Davy Jones removed; latest 500/30 currency; +50 Health/point; single-player ship cap 8; latest shipyard tiers; Ammo Bin storage-only; item and treasure rarity palettes intentionally differ. Stale earlier references to raft prologue, Ammo Bay crafting, unrestricted single-player ships, and +25 Health are historical.

<a id="requirements"></a>

## Requirements and implementation

Statuses apply to the named foundation only. Planned rows do not imply production gameplay. M0–M5 are established project milestone labels; later packages are proposals rather than approved renamed milestones.

| ID / Bible section and requirement | Milestone/package | Status, files/system and commit evidence | Verification, limitations / deferred content |
| --- | --- | --- | --- |
| B01 Core identity: ships central and highly customizable; temporary, raidable land bases; adventure interrupts routine; core loop | 0.01 integration / ships | Planned gameplay; `README.md`, roadmap record vision; `50ecc95` | No playable ship loop yet. "THE SHIP IS HOME" retired [October 6](#october-6); land-base duration and raid rules TBD |
| B02 World: dense seamless islands, no visible server grid; official regional servers and overflow; official wipes with progression rewards; host-defined unofficial servers | Long term world/hosting | Planned world/infrastructure | No MMO-first implementation; 0.01 small world. Wipe schedule/rewards and host-configurable rules TBD |
| B03 §§3.4,14 Ports (formerly Villages): four Port islands per server, each in a weather biome; distinct PvP-safe trade hubs, specialized stock and limited Ferryman routes | Settlements/prologue | Planned deterministic NPCs and route data | Renamed [October 6](#october-6). Ferrymen at selected docks/islands, not necessarily every Port; cyan-blue eyes; routes/fees and biome assignments TBD |
| B04 Survival: health/stamina/hydration/weight | M4/M5 | Stat foundations Implemented; local survival HUD and replicated inventory/equipment weight display Verified | [HUD evidence](VERIFICATION.md#m4-hud), [equipment](VERIFICATION.md#m5f-equipment). Complete survival gameplay, dedicated-server testing and final art remain open |
| B05 §§6,30.15 Survival needs, warnings, regeneration and action-dependent stamina | M4 return / environment / long term injury | Empty food/hydration/stamina HUD warnings Verified; latest drain/effects Planned | [HUD](VERIFICATION.md#m4-hud). [October 6](#october-6) owner decision permits stamina recovery while walking, superseding stationary-only wording. Five-second base tuning, 15-minute needs drain, scaling, regen and needs damage remain open |
| B06 Fresh water restores hydration; salt water harms; direct drinking | Survival interactions | Planned water-source/use logic | No water consumption verified |
| B07 §§6.6,6.8,30.22 Character: non-explicit starter clothing, aging and hair/scissors | Character content / long term | Planned; Davy Jones quest Removed | No current age-regression quest selected; do not revive older Davy Jones/Fountain/Horse implementation |
| B08 Armor/equipment: body slots, material/protection tiers; cosmetics separate from stats | M5F / crafting | Replicated equip/unequip, slot ownership checks and atomic inventory transfers Verified; `EWEquipmentComponent.*` | [M5F evidence](VERIFICATION.md#m5f-equipment); body-slot transfer foundation, opt-in hats. Protection/material stats, cosmetics/meshes, durability and persistence remain Planned |
| B09 Enhanced Input; WASD/mouse, sprint/jump, C/hold C and B/hold B; Interact E / controller X | M1/M2 / M5D | Stance tap/hold, blocked/open exits and collider sizes tested locally and from client to host, including 100 ms outgoing lag/1% loss | Physical gamepad and remapping remain Planned; [M2 collision verification](VERIFICATION.md#m2-collision). Keyboard Interact E CONFIRMED [October 6](#october-6); already mapped in `EWPlayerController.cpp` |
| B10 Third-person default, dynamic first/third person, Z; appropriate animations | M2/M3 / animation | Stance blends, replicated stance, root alignment, prone camera and movement-clearance body query verified | No scaling; authored transitions, terrain-aligned animation and final animation set remain pending |
| B11 §§5.8,25.4 Inventory I / controller Y; first valid focus, d-pad/stick, highlight/confirm | M5B/C/E | M5E selection/details draft Verified in single-player and replicated client UI; [evidence](VERIFICATION.md#m5e-selection) | Scripted controller key/analog/dead-zone tests pass; physical hardware, LB/RB tabs/remapping, durability and structured item tags remain pending |
| B12 Inventory character preview with hair/gear; adjacent crafting and future tabs | M5 presentation / crafting | Planned UMG/preview/content | Functional draft only; no permanent tutorial clutter |
| B13 §§5.6-5.9 HUD: survival/conditions/equipment/ship prompts; eight-slot hotbar | M4 presentation / M5G | Survival gauges/warnings and eight-slot hotbar foundations Verified; conditions/ship/interaction displays and final art Planned | [Survival HUD](VERIFICATION.md#m4-hud); keyboard 1–8, contextual assignments, LB combinations and owned equipment action [verified](VERIFICATION.md#m5g-hotbar). Other item actions remain open |
| B14 §2.2 Pause: Escape/Start, Resume/Options/Exit confirmation | UI/input | Planned | Single player pauses world; multiplayer stays live/vulnerable. Editor Escape ending Play is not game pause |
| B15 §§5.10,10 Map/compass M / View-Select: discovery, rotating emblem, ghost markers visible through fog | Navigation | Planned C++ discovery/state, UMG and content | Walking allowed; sprint/stance/hotbar/inventory blocked; no world pause; independent left/right focus/zoom. Command radial now Middle Mouse / D-pad Right |
| B16 §30.14 Sun/day-night and moving weather | Environment | Planned | 90 real minutes day + 90 night; moving rain/snow clouds, darker ocean, foliage sway, crops/barrel water; other weather timings TBD |
| B17 §30.8 Skills: 15 cumulative points/level, cap 80, respec from level 10 for 2 Gold | Skills/crafting | Planned data-driven framework | Level and permanent baseline recipes preserved on respec; name/cooldown/node costs TBD where unspecified; prerequisite bundle purchase UI |
| B18 Tools/resources: axes, mining, gardening, shovel, harvesting; island variation | Gathering/treasure | Planned actors, item assets and interactions | No harvesting system claimed |
| B19 Climbing picks: steep terrain, stamina and durability | Later traversal | Planned | Access to rare resources/treasure/claims later |
| B20 Stations: smithy, forge, loom, storage; ore processing and sail repair | Crafting/ships | Planned recipes and station access | No station content implemented |
| B21 Ship placement/removal and transfer belongings to larger vessel | Ships/home | Planned placement/storage/transfer | Must preserve important belongings on upgrade |
| B22 Ship customization; small vessels stay useful | Ships progression | Planned | Hull/deck/masts/sails/weapons/armor/modules/crew/cargo/decor/skins later |
| B23 §30.7 Ship cargo/flooding weight and overload sinking | Starter sloop | Planned ship inventory/weight model | Player carried weight is not ship weight; overload timing/curve TBD |
| B24 Hold-to-anchor; anchored ship cannot sail; HUD status | Starter sloop | Planned interaction/ship state | Network anchoring checks pending |
| B25 §§12.1,30.6-9 Persistent sloop: helm/anchor/cargo/weight/two opposing cannons/shared limited ammo | Starter sloop / naval combat | Planned | Prologue escapes on repaired dinghy; persistent sloop placement needs confirmation; socket-locked cannons; Ammo Bin stores cannon ammo only and does not craft |
| B26 Shipyard near dock; repair/build/manage/upgrade/customize with progression | Ships/Port | Planned | Depends on Shipwright progression |
| B27 Damageable sails, loom/material repair; cosmetic skins without automatic stats | Crafting/naval combat | Planned | Content and authoritative repair costs pending |
| B28 Readable naval combat: ammo, mast/sail/rudder, flood/fire/boarding/grappling/repair/penetration/injury | Naval combat expansion | Planned future scope | Simple two-cannon slice precedes deeper systems |
| B29 §§2.1,19 Ghost ships: hostile NPCs in multiple haunt/threat areas, firing and fog-visible map markers | Adventure/crew | Planned | Ordinary hostile open-world pirate ships are player-controlled; special sailor recruitment retained future possibility |
| B30 Floating crates: notice, anchor, swim, loot, return | Adventure | Planned | Depends on swimming, ship and inventory interactions |
| B31 §30.18 Bottle treasure maps; island parchment, X, shovel digging; stronger encounters/rewards | Treasure | Planned data assets/objectives/rewards | Treasure palette Common gray/no glow, Uncommon green, Rare blue, Epic purple, Legendary gold; distinct from item palette |
| B32 Treasure enemy trigger; dungeons/waves/boss reward; possible territory link | Combat/encounters | Planned | Territory connection is future possibility |
| B33 Tribes: invite/cooperate/sail/territory; blue friendly map indicators | Multiplayer social | Planned | No tribe authority/UI or territory system |
| B34 §§28.16,29.12,30.19 Shared crew/creature commands | Crew/creatures | Planned deterministic commands | Follow All, Follow One, Stop All, Stop One plus assignments; hold Middle Mouse / D-pad Right; no four-command-only limit |
| B35 §16 Species-compatible taming/breeding/raising and Beast Mastery/saddles | Creatures progression | Planned | Original raising/bonding terminology; lineage/inherited traits; species/body-appropriate jumps, spider wall/ceiling climbing; exact roster/stats/formulas TBD |
| B36 Deterministic NPC roles; crew names/XP/equipment/traits/loyalty/injury/specialization | Crew/NPCs | Planned | No generative AI for ordinary runtime NPC behavior |
| B37 Surgeon: visible gauze/bandage/stitch/splint/wound/surgery; injuries separate from health; tree-punching hand injury and infection | Later injuries | Planned | Health component is not persistent injury system. [October 6](#october-6): 25 bare-hand tree hits need a bandage, otherwise infection after 10 in-game minutes, fatal without a Surgeon; counting/reset/treatment details TBD |
| B38 §30.17 Currency: 500 Copper=1 Silver; 30 Silver=1 Gold; data-driven shops | Economy/Port | Planned | Player currency weightless and retained on death; NPC wages physical Copper; no economy implementation |
| B39 Text/proximity voice/tribe/crew; possible alliance/direct messaging | Multiplayer communication | Planned | No voice/chat infrastructure claimed |
| B40 §§21,30 and direct owner clarification: schooner/brigantine, bailing/boarding, unconscious rescue, amnesia/journal, dinghy repair/Small Sail, title/Port | Prologue integration | Planned; old raft/shipyard opening Replaced | Rye remains in inventory; start zero currency; innkeeper free-room request/work-trade tour introduces merchants, general merchant offers sale, credit 250 Copper at introduction completion; room payment TBD |
| B41 §24 0.01 foundations: movement/input/perspectives/survival/HUD/inventory/equipment/preview/crafting/skills/gathering/mining/water/combat/treasure/ship/anchor/cargo/cannons/shipyard/Port/map/time | 0.01 acceptance | Partial foundations M1-M5; remainder Planned | Integrated loop and early authority tests; scope firewall keeps full creatures, surgery, territory/global infrastructure from blocking core |
| B42 §§2,29.8,30.20,30.22 Single-player beta / later multiplayer up to 100, tribe friendly fire disabled, carried gear drops but currency retained | Multiplayer / death / persistence | Planned gameplay; replication foundations exist | Target is not tested capacity. No general offline protection; Armored Shipyard is specific exception; loot theft not ship ownership capture |
| B43 §2.3 Wreck loot floating crates ~15 real minutes; closest Port respawn for killed sleepers; Port logout ocean displacement | Death/ships/world | Planned | Ocean displacement specifically needs playtesting; ordinary death progression rules remain TBD |
| B44 §§2.4-2.5 Anti-duplication, authorization and persistent stable identities for players/items/ships/crew/creatures/tribes/claims/currency/map | M5 onwards / persistence | Stable item-ID field Implemented `9b7f129`; M5D pickup/M5F equipment/M5G hotbar foundations Verified | Quantity/weight conservation and owned requests checked under local packet emulation; [pickup](VERIFICATION.md#m5d-pickups), [equipment](VERIFICATION.md#m5f-equipment), [hotbar](VERIFICATION.md#m5g-hotbar). Hotbar references are not extra storage. Save/load/general transfers remain Planned; transient actor names are not persistence IDs |
| B45 §8 Gathering: hands plants/berries/fiber/sticks; punch trees slowly for wood without thatch (hand injury, see B37); hatchet more wood+thatch; mining ores | Gathering | Planned gameplay; saved M5C test item Verified | Island/biome distributions TBD; Test.Wood is a persisted fixture, not production wood variants or approved weight balance |
| B46 §§8.3-8.5 Food/farming: biome berries, corn/tomatoes/beans/sugarcane, ground/planter farming, fertilizer/ rain/manual/barrels | Crafting/environment | Planned | Sugar comes from sugarcane; raw meat sickness; campfire/grill burn/spoil; grill ~3x discussed but final timers/multiplier TBD |
| B47 §§30.9,30.18 Glider from Smithy Weapons/Melee; water-only harpoon; diving platform/fish oil/tether | Later tools/underwater | Planned | 1 Fish Oil per 90 seconds, platform slot 100; unlimited vertical/limited horizontal tether; Harpoon Gun Bolts from Smithy Ammo; glider controlled descent |
| B48 §§3,15,16 Biomes/caves/mountain treasure and traversal options | World/treasure | Planned | X marks actual cave treasure, not entrance; mountain flat diggable area, spiders/guardians and varied traversal; distributions TBD |
| B49 §18 Public communication operations | Multiplayer launch | Planned | Mute/block/report/moderation before public multiplayer launch; not a current prototype feature |
| B50 §§25-27 Architecture and operating rules | All slices | Partially Implemented C++/Blueprint/data/Git LFS foundation | Ship must stay separate authoritative actor; binary assets via Unreal-supported APIs; no competing agent edits; explicit decisions supersede older text, unresolved rules TBD |

## Archived Bible section coverage

The left column uses the archived Master Bible's section labels, which the Shared and team guides also cite as sources. Current wording comes from the guides and the [October 6 decisions](#october-6); for example, §3 and §14 "Villages" are now Ports.

October additions §§28-30 and Appendices E-F are reviewed in full in [revision review](ARCHIVE/CONTEXT_AND_DESIGN_REVIEWS.md#october-review), including startup/save/creator, administration/audio, ship hardpoints/caps/decay, stats/combat, crafting, underwater/fishing, crew wages, and corpse/bed rules. Their exact implementation traceability will grow with each slice; no feature is marked implemented from design text alone.

| Bible section | Traceability IDs |
| --- | --- |
| 0 Authority/status; 1 identity/pillars/fantasy | B01, B50; source reconciliation |
| 2 modes/PvP/death/persistence | B14, B42-B44 |
| 3 world/islands/biomes/Villages | B02-B03, B48 |
| 4 day/night/weather | B16, B46 |
| 5 perspective/controls/animation/HUD/inventory | B09-B15 |
| 6 survival/injury/clothing/aging | B04-B08, B37 |
| 7 progression/respec | B17 |
| 8 gathering/resources/food/farming | B18, B45-B46 |
| 9 crafting/building/traversal/claims | B19-B20, B32-B33, B47 |
| 10 map/compass | B15 |
| 11 ship home/construction/raft | B21-B22, B25-B26, B40 |
| 12 ship systems/naval combat | B23-B28 |
| 13 diving/aquatic life | B47 |
| 14 economy/Villages/Ferryman | B03, B38 |
| 15 treasure/dungeons/Davy Jones | B07, B31-B32, B48 |
| 16 creatures/taming/breeding/saddles/jumps | B35, B48 |
| 17 NPCs/crew/commands/surgeon | B34, B36-B37 |
| 18 tribes/communication/moderation | B33, B39, B42, B49 |
| 19 ghost ships/salvage | B29-B30 |
| 20 cosmetics | B08, B22, B27 |
| 21 revised prologue; 22 Mission Two | B40 |
| 23 official online world | B02, B42 |
| 24 early scope/build order/firewall | B41; development roadmap |
| 25 architecture/workflow; 26 open decisions; 27 continuing design | B44, B50; decision log and reconciliation |
| Appendices A-D controls/status/terminology/core | B01, B09-B15, B17, B35, B41, B50; unresolved View/Select conflict recorded |

## Maintenance

For each slice update status, relevant file paths, exact verification, limitation and commit. Record intentional departures in the [decision history](#decisions). Design changes are approved only by the owner and recorded through the Shared guide; this file does not approve departures. Foundations and temporary UI do not satisfy the complete Bible requirement.

<a id="decisions"></a>

## Decision history

Retained decisions are chronological evidence. Newer owner decisions and the October revision supersede older entries, particularly D019–D028. D045–D047 supersede the "ship is home" framing in D002 and the Village name in D014, D026, D034 and other earlier rows; historical rows keep their original wording. Follow the authority above rather than treating every historical row as simultaneous current design.

| ID | Decision / rationale | Status and authority | Impact / evidence |
| --- | --- | --- | --- |
| D001 | Active project is `C:\UnrealProjects\EW`; OneDrive copy is backup | Implemented; handoff and working directory verified | Builds/launches/Git target active path; `919737f` baseline |
| D002 | Ship is home; keep Prepare/Sail/Discover/Fight-or-Explore/Loot/Escape/Upgrade loop | Design authority: Bible + handoff | No central vision change authorized; all later systems support it |
| D003 | 0.01 first playable slice precedes large online infrastructure | Confirmed reference | Proposed roadmap sequences dependencies; no MMO-first build |
| D004 | C++ gameplay foundations, Blueprint assembly, data-driven assets, Enhanced Input; server authority | Implemented foundation; `50ecc95` and subsequent source | Replicated code still requires multi-client and dedicated-server tests |
| D005 | Walk 500, sprint 750; crouch/prone tap/hold 0.35s | Implemented `d8ca1dc`, `5f08eb7` | Tunable defaults, not final balance |
| D006 | Revert temporary stance scaling; postpone proper animations until suitable assets | Replaced/Postponed; `cf282a8` -> `e88acb1`; handoff | Preserve gameplay/collision states without unnatural shrinking |
| D007 | Third-person default, dedicated first-person camera and local Z toggle; cyan diagnostics temporary | Implemented `fb214b3` | Perspective-specific final animations remain pending |
| D008 | Survival component holds replicated stats; stamina drain 15/s, recovery 10/s | Implemented `55ed2c1` | Hunger/temperature values are groundwork, not full needs/environment gameplay |
| D009 | Inventory uses 24 default slots, item definitions, server mutation and weight-to-survival sync | Implemented `9b7f129` | Slot cap enforced; displayed max carry weight does not enforce weight cap. Encumbrance behavior undecided |
| D010 | Native UMG panel and runtime I action provide a functional draft | Verified local empty panel; inherited four UI files preserved | Incremental scope departure from full Bible UI: Y/navigation/highlight/preview/crafting/hotbar pending; avoids premature artwork |
| D011 | Build native widget tree before Slate rebuild instead of NativeConstruct | Technical repair Verified 2026-10-05; Git title `Fix and verify native inventory panel` | I changed cursor but original panel invisible; `EWInventoryWidget.*` lifecycle fix; build, inventory automation and local Play retest passed |
| D012 | Do not infer equipment behavior from equipment-slot enum | Documentation decision 2026-10-05 | Equip/unequip, appearance/protection and atomic transfer are Planned |
| D013 | Keep NPCs deterministic; cosmetic skins separate from gameplay stats | Bible requirement | Applies to future NPC, clothing and sail systems |
| D014 | Village terminology; limited Ferryman routes; fixed currency conversions | Bible requirement | 100 Copper=1 Silver; 500 Silver=1 Gold; not implemented economy |
| D015 | Keep rarity colors undecided; prologue remains evolving concept | Bible requirement; prologue source corrected in D019 | Original entry relied on older treasure-first reference; revised Bible §§21-22 now govern. No rarity assignments introduced |
| D016 | Team is five developers; Project Elitewake remains working title | Newer handoff supersedes older Bible's solo-development context | Use newer production context without changing creative vision |
| D017 | No paid dependency additions; Meshy not assumed available; Scenario only for relevant assets | Handoff constraint | Existing integrations recorded, asset generation not needed for draft panel |
| D018 | M5 next slice: persisted Wood test asset and opt-in authority grant, then validated pickup | Proposed technical sequencing from authorized handoff | Stable asset references before replicated item testing; no final content balance implied |
| D019 | Revised storm battle/Quartermaster rescue/journal/campfire/shipyard/raft opening replaces treasure-first prologue | Confirmed Bible §§21-22; historical recap agrees | Mission Two starts by talking to innkeeper after Quartermaster leaves. Tour/post-tour TBD; no implementation changed |
| D020 | Davy Jones age-regression boss replaces Fountain/Horse of Youth | Confirmed Bible §§6.8,15.4, Appendix C | Age returns to 20; level/skill allocation preserved; buffs/trigger/repeatability TBD |
| D021 | 15 cumulative points per level; respec from level 10 without level loss | Confirmed Bible §7 | Costs/cooldown/name/max level/tree balance TBD; not implemented |
| D022 | Day and night each last four real hours | Confirmed Bible §4 | Eight-hour full cycle; weather timing remains tunable; not implemented |
| D023 | Combined map/compass uses M and View/Select; walking allowed, sprint/stance/hotbar/inventory blocked; world remains live | Confirmed newer Bible §§5.10,10.2 | Appendix radial View conflict unresolved; controller radial replacement TBD, no invented chord |
| D024 | Eight-slot hotbar controller concept uses hold LB with face buttons/d-pad | Confirmed Bible §5.9, Appendix A | Exact item-use/selection implementation pending |
| D025 | Single-player pause freezes world; multiplayer menu does not; map never pauses | Confirmed Bible §2.2 | Separate from editor Escape behavior |
| D026 | Four safe Villages; up-to-100 multiplayer target; tribe friendly fire disabled; normal hostile pirate ships primarily players | Confirmed Bible §§2-3,18 | Ghost ships are hostile NPC vessels; target is not tested capacity |
| D027 | Death drops carried inventory/equipment; sleeping bodies and ships vulnerable offline; raiders loot without taking ship ownership | Confirmed Bible §2.3 | Wreck crates ~15 real minutes; Village logout displacement needs playtesting; normal death progression effects TBD |
| D028 | Mission One uses raft; persistent two-cannon sloop concept remains | Confirmed Bible §§11.6,12.1,21.3 | Exact sloop progression placement and tutorial Shipwright exception need reconfirmation; no ship implementation yet |
| D029 | Continue M5 while retaining M4 unfinished HUD/needs/testing backlog | Later historical owner explicitly begins M5; source inspection | Earlier survival-next recap is superseded as immediate task order, not acceptance of full M4 completion |
| D030 | Animation packs reported downloaded; integrate later; Scenario authorization reported complete in Cursor | Later owner messages in historical chat | Not verified imported/retargeted animation or Scenario access in current session; Cursor remains optional |
| D031 | Hold remote publication until cross-reference review and explicit push approval | Current owner instruction 2026-10-05 and prior automatic review rejection | `286f8d0` local; GitHub main read at `9b7f129`; reconciliation changes documentation only |
| D032 | Publish reviewed inventory repair and reconciled records within core goals | Owner approval 2026-10-05: "You can do it as long as it aligns with our core goals"; supersedes D031 hold after completed review | Clean tree, diff check and remote tip rechecked; ordinary push `9b7f129` -> `41ee3fc` succeeded. No force push or creative scope change; M5 and verification limits remain recorded |
| D033 | October 5 Authoritative Revision replaces September creative reference; newest §30 wins conflicts | Owner supplied new DOCX and requested review; later requested M5 continuation | Davy Jones Removed; current 90/90-minute cycle, 500/30 currency, Health +50/stat point, hardpoints/shipyard tiers and storage-only Ammo Bin replace older rules. Full revision review linked above; gameplay remains staged |
| D034 | Keep rye through Village arrival; innkeeper introduces town-square shops; general merchant offers sale; credit player 250 Copper at introduction completion | Direct owner clarification in this chat after Bible review | Survivor begins zero currency. Merchant quests later; room payment unspecified. Writing deferred by owner; no mission implementation authorized in M5 slice |
| D035 | M5C uses persisted Test.Wood plus opt-in editor-only authority command | Existing M5C roadmap and current owner request to continue M5 | Resource stack 250 follows §30.17; weight 0.1 kg is a test fixture only. No default grants or client grant RPC; supported Unreal asset creation; packaging/network gates pending |
| D036 | Checkpoint verified M5C before pickup/interaction work | Build, two automation tests, real Play grant/live refresh/I close-reopen/fresh empty check | [M5C verification](VERIFICATION.md#m5c-inventory) preserves exact scope and evidence; M5 equipment/hotbar and M4 backlog remain open |
| D037 | Return to M2 on Unreal 5.8.3; import Free Animation Library, use compatible skeletons/private root-locked stance clips and retain locomotion | Direct owner request after engine update/import; build and local stance evidence | [M2 verification](VERIFICATION.md#m2-stance); its initial shared-capsule gaps are superseded by D038; controller/presentation gates remain open; M5D pending |
| D038 | Add stance-specific clearance and a floor-aligned prone body movement query; carry stance/exit intent in predicted movement and retain accepted stance when blocked | Direct owner request to continue M2 collision/clearance after the usage pause; obstacle/slope and local packet-emulation verification | [Collision record](VERIFICATION.md#m2-collision); 90/60/28 cm root half heights are implementation tuning values; no scaling, new story rules, M5D work or production-multiplayer claim |
| D039 | Resume M5D: replicated world stacks, owned-controller intent and server-validated partial pickup transfer | Direct owner request "Great. Let's start with M5D"; publication authorization D032 persists | [Pickup verification](VERIFICATION.md#m5d-pickups); E/250 cm are draft tuning, controller X follows Bible; saved isolated fixture, competing host/client intents and packet emulation verified; M5E-G and full interaction UI remain pending |
| D040 | M5E adds inventory selection/navigation and read-only item details; confirmation does not equip/use items before those systems exist | Owner request to move on after M5D; accepted next step was M5E; Bible §§5.8/25.4; publication authorization D032 persists | [Selection verification](VERIFICATION.md#m5e-selection); I/Y, first focus, keyboard/controller/mouse, live refresh and scrolling draft; input isolated while panel is open, world remains live; hardware/final art and M5F-G remain open |
| D041 | M5F moves one owned unit into its exact equipment slot; occupied-slot swaps require capacity to return previous gear; full inventory rejects unequip; worn gear retains carried weight | Owner "Let's go" after M5F was identified next; Bible body-slot/weight/anti-duplication requirements; publication authorization D032 persists | [Equipment verification](VERIFICATION.md#m5f-equipment). Atomic return policy and R/X/button are implementation choices, not new Bible rules. Protection/cosmetics/durability/persistence and M5G remain open |
| D042 | M5G provides eight shortcuts to owned definitions, owner-only replicated bindings and authoritative M5F equipment activation; unsupported item actions retain resources without consumption | Owner "Let's begin" after M5 acceptance, then "review your work and continue"; Bible §§5.8–5.9; publication authorization D032 persists | [Hotbar verification](VERIFICATION.md#m5g-hotbar). Exact LB ordering, unique-definition binding and retaining unavailable shortcuts are draft implementation choices. Engine key flush resets modifier state. Other item actions, map integration, hardware and persistence remain open |
| D043 | Return to M4 presentation after M5G: display authoritative survival values and Bible empty-stat warnings; stamina recovery also occurs while walking | Owner "Okay, let's keep going"; accepted survival/HUD return scope and direct October 6 answer "Also while walking" | [HUD verification](VERIFICATION.md#m4-hud). Walking recovery clarification supersedes stationary-only wording. HUD does not retune rates, add needs damage, item consumption or conditions; full M4 remains incomplete |
| D044 | Consolidate repository records and remove audited unused Unreal template variants | Direct owner request to clean the GitHub repository, deleting and combining clutter; core-goal publication authorization persists | [Cleanup evidence](VERIFICATION.md#repository-cleanup). Package/native-type audits precede removal; active assets, creative authority, implementation evidence and Git history remain preserved. Three current documents become the maintained reference set |
| D045 | Adopt three-guide authority: owner -> Shared Design Authority & Cross-Team Guide -> Development & Systems / Creative & World guides -> repo docs and work notes. Master Bible becomes archive only | Owner instruction October 6, 2026; Shared guide §1 guide architecture | [Authority](#authority). Replaces D033's use of the Master Bible as current creative reference; source section labels retained |
| D046 | Retire "THE SHIP IS HOME"; ships highly customizable; land bases allowed but temporary and raidable by players and wildlife. Rename Villages to Ports: four Port islands per server, each in a weather biome. Official wipes with progression rewards; host-defined unofficial servers; no visible grid | Owner decisions October 6, 2026, supplied in October 6 owner decision brief; reviewed Shared DOCX still identifies October 5 source revision | [October 6 decisions](#october-6). Supersedes D002 framing and Village terminology. Base duration/raids, Port biomes/identities, wipe schedule/rewards and host options TBD. Documentation only; no code change |
| D047 | Keyboard Interact = E CONFIRMED; stamina recovers while walking; tree punching uses Attack, not Interact; 25 bare-hand tree hits need a bandage, otherwise infection after 10 in-game minutes, fatal without a Surgeon | Owner decisions October 6, 2026, supplied in October 6 owner decision brief; reviewed Shared DOCX still identifies October 5 source revision | E already mapped in `EWPlayerController.cpp`; walking recovery restates D043. Hand-injury counting, reset, treatment and clock conversion TBD; no injury system implemented |

Update this reference when authority changes; update PROJECT_GUIDE.md when work priorities change and VERIFICATION.md when evidence changes. Keep suggestions distinct from confirmed decisions.
