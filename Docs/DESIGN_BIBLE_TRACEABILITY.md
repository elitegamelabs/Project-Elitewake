# Design Bible traceability

Reviewed: 2026-10-05. Current source: **October 5 Authoritative Revision**, §§0-30 and appendices A-F, plus direct owner clarification of the rye sale/introduction. Section 30 supersedes older conflicts. See [current revision review](DESIGN_REVISION_2026_10_05.md). September reconciliation remains historical. This is a requirement index, not a claim that future features are implemented.

M0-M5 are established milestones. Later work-package names refer to the proposed roadmap. Planned rows have no production implementation or verification unless explicitly stated. Existing Epic template variants are not evidence of Elitewake feature completion.

| ID / Bible section and requirement | Milestone/package | Status, files/system and commit evidence | Verification, limitations / deferred content |
| --- | --- | --- | --- |
| B01 Core identity: ship is home; adventure interrupts routine; core loop | 0.01 integration / ships | Planned gameplay; `README.md`, roadmap record vision; `50ecc95` | No playable ship loop yet |
| B02 World: dense seamless islands; official regional servers and overflow | Long term world/hosting | Planned world/infrastructure | No MMO-first implementation; 0.01 small world |
| B03 §§3.4,14 Villages: four distinct PvP-safe trade hubs, specialized stock and limited Ferryman routes | Settlements/prologue | Planned deterministic NPCs and route data | Ferrymen at selected docks/islands, not necessarily every Village; cyan-blue eyes; routes/fees TBD |
| B04 Survival: health/stamina/hydration/weight | M4/M5 | Implemented `EWSurvivalComponent.*`; inventory plus equipment carried-weight sync Verified in M5F | Equipment transfers conserve carried weight locally and on replicated client; [evidence](M5F_EQUIPMENT_VERIFICATION.md). Final HUD/full survival multiplayer validation pending |
| B05 §§6,30.15 Survival needs, warnings, regeneration and action-dependent stamina | M4 return / environment / long term injury | Stat foundations Implemented; latest drain/warnings/effects Planned | Base needs empty in 15 minutes; base sprint drains/recovery take 5 seconds, stationary recovery; activity/upgraded-capacity scaling and health-loss interpretation need clarification |
| B06 Fresh water restores hydration; salt water harms; direct drinking | Survival interactions | Planned water-source/use logic | No water consumption verified |
| B07 §§6.6,6.8,30.22 Character: non-explicit starter clothing, aging and hair/scissors | Character content / long term | Planned; Davy Jones quest Removed | No current age-regression quest selected; do not revive older Davy Jones/Fountain/Horse implementation |
| B08 Armor/equipment: body slots, material/protection tiers; cosmetics separate from stats | M5F / crafting | Replicated equip/unequip, slot ownership checks and atomic inventory transfers Verified; `EWEquipmentComponent.*` | [M5F evidence](M5F_EQUIPMENT_VERIFICATION.md); body-slot transfer foundation, opt-in hats. Protection/material stats, cosmetics/meshes, durability and persistence remain Planned |
| B09 Enhanced Input; WASD/mouse, sprint/jump, C/hold C and B/hold B | M1/M2 | Stance tap/hold, blocked/open exits and collider sizes tested locally and from client to host, including 100 ms outgoing lag/1% loss | Physical gamepad and remapping remain Planned; [M2 collision verification](M2_COLLISION_VERIFICATION.md) |
| B10 Third-person default, dynamic first/third person, Z; appropriate animations | M2/M3 / animation | Stance blends, replicated stance, root alignment, prone camera and movement-clearance body query verified | No scaling; authored transitions, terrain-aligned animation and final animation set remain pending |
| B11 §§5.8,25.4 Inventory I / controller Y; first valid focus, d-pad/stick, highlight/confirm | M5B/C/E | M5E selection/details draft Verified in single-player and replicated client UI; [evidence](M5E_SELECTION_VERIFICATION.md) | Scripted controller key/analog/dead-zone tests pass; physical hardware, LB/RB tabs/remapping, durability and structured item tags remain pending |
| B12 Inventory character preview with hair/gear; adjacent crafting and future tabs | M5 presentation / crafting | Planned UMG/preview/content | Functional draft only; no permanent tutorial clutter |
| B13 §§5.6-5.9 HUD: survival/conditions/equipment/ship prompts; eight-slot hotbar | M4 presentation / M5G | Eight-slot hotbar foundation Verified; complete survival/conditions/ship HUD and final art Planned | Keyboard 1–8, contextual assignments, LB combinations and owned equipment action verified; [hotbar](M5G_HOTBAR_VERIFICATION.md). Other item actions remain open |
| B14 §2.2 Pause: Escape/Start, Resume/Options/Exit confirmation | UI/input | Planned | Single player pauses world; multiplayer stays live/vulnerable. Editor Escape ending Play is not game pause |
| B15 §§5.10,10 Map/compass M / View-Select: discovery, rotating emblem, ghost markers visible through fog | Navigation | Planned C++ discovery/state, UMG and content | Walking allowed; sprint/stance/hotbar/inventory blocked; no world pause; independent left/right focus/zoom. Command radial now Middle Mouse / D-pad Right |
| B16 §30.14 Sun/day-night and moving weather | Environment | Planned | 90 real minutes day + 90 night; moving rain/snow clouds, darker ocean, foliage sway, crops/barrel water; other weather timings TBD |
| B17 §30.8 Skills: 15 cumulative points/level, cap 80, respec from level 10 for 2 Gold | Skills/crafting | Planned data-driven framework | Level and permanent baseline recipes preserved on respec; name/cooldown/node costs TBD where unspecified; prerequisite bundle purchase UI |
| B18 Tools/resources: axes, mining, gardening, shovel, harvesting; island variation | Gathering/treasure | Planned actors, item assets and interactions | No harvesting system claimed |
| B19 Climbing picks: steep terrain, stamina and durability | Later traversal | Planned | Access to rare resources/treasure/claims later |
| B20 Stations: smithy, forge, loom, storage; ore processing and sail repair | Crafting/ships | Planned recipes and station access | No station content implemented |
| B21 Ship home placement/removal and transfer belongings to larger vessel | Ships/home | Planned placement/storage/transfer | Must preserve important belongings on upgrade |
| B22 Ship customization; small vessels stay useful | Ships progression | Planned | Hull/deck/masts/sails/weapons/armor/modules/crew/cargo/decor/skins later |
| B23 §30.7 Ship cargo/flooding weight and overload sinking | Starter sloop | Planned ship inventory/weight model | Player carried weight is not ship weight; overload timing/curve TBD |
| B24 Hold-to-anchor; anchored ship cannot sail; HUD status | Starter sloop | Planned interaction/ship state | Network anchoring checks pending |
| B25 §§12.1,30.6-9 Persistent sloop: helm/anchor/cargo/weight/two opposing cannons/shared limited ammo | Starter sloop / naval combat | Planned | Prologue escapes on repaired dinghy; persistent sloop placement needs confirmation; socket-locked cannons; Ammo Bin stores cannon ammo only and does not craft |
| B26 Shipyard near dock; repair/build/manage/upgrade/customize with progression | Ships/Village | Planned | Depends on Shipwright progression |
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
| B37 Surgeon: visible gauze/bandage/stitch/splint/wound/surgery; injuries separate from health | Later injuries | Planned | Health component is not persistent injury system |
| B38 §30.17 Currency: 500 Copper=1 Silver; 30 Silver=1 Gold; data-driven shops | Economy/Village | Planned | Player currency weightless and retained on death; NPC wages physical Copper; no economy implementation |
| B39 Text/proximity voice/tribe/crew; possible alliance/direct messaging | Multiplayer communication | Planned | No voice/chat infrastructure claimed |
| B40 §§21,30 and direct owner clarification: schooner/brigantine, bailing/boarding, unconscious rescue, amnesia/journal, dinghy repair/Small Sail, title/Village | Prologue integration | Planned; old raft/shipyard opening Replaced | Rye remains in inventory; start zero currency; innkeeper free-room request/work-trade tour introduces merchants, general merchant offers sale, credit 250 Copper at introduction completion; room payment TBD |
| B41 §24 0.01 foundations: movement/input/perspectives/survival/HUD/inventory/equipment/preview/crafting/skills/gathering/mining/water/combat/treasure/ship/anchor/cargo/cannons/shipyard/Village/map/time | 0.01 acceptance | Partial foundations M1-M5; remainder Planned | Integrated loop and early authority tests; scope firewall keeps full creatures, surgery, territory/global infrastructure from blocking core |
| B42 §§2,29.8,30.20,30.22 Single-player beta / later multiplayer up to 100, tribe friendly fire disabled, carried gear drops but currency retained | Multiplayer / death / persistence | Planned gameplay; replication foundations exist | Target is not tested capacity. No general offline protection; Armored Shipyard is specific exception; loot theft not ship ownership capture |
| B43 §2.3 Wreck loot floating crates ~15 real minutes; closest Village respawn for killed sleepers; Village logout ocean displacement | Death/ships/world | Planned | Ocean displacement specifically needs playtesting; ordinary death progression rules remain TBD |
| B44 §§2.4-2.5 Anti-duplication, authorization and persistent stable identities for players/items/ships/crew/creatures/tribes/claims/currency/map | M5 onwards / persistence | Stable item-ID field Implemented `9b7f129`; M5D pickup/M5F equipment/M5G hotbar foundations Verified | Quantity/weight conservation and owned requests checked under local packet emulation; [pickup](M5D_PICKUP_VERIFICATION.md), [equipment](M5F_EQUIPMENT_VERIFICATION.md), [hotbar](M5G_HOTBAR_VERIFICATION.md). Hotbar references are not extra storage. Save/load/general transfers remain Planned; transient actor names are not persistence IDs |
| B45 §8 Gathering: hands plants/berries/fiber/sticks; punch trees slowly for wood without thatch; hatchet more wood+thatch; mining ores | Gathering | Planned gameplay; saved M5C test item Verified | Island/biome distributions TBD; Test.Wood is a persisted fixture, not production wood variants or approved weight balance |
| B46 §§8.3-8.5 Food/farming: biome berries, corn/tomatoes/beans/sugarcane, ground/planter farming, fertilizer/ rain/manual/barrels | Crafting/environment | Planned | Sugar comes from sugarcane; raw meat sickness; campfire/grill burn/spoil; grill ~3x discussed but final timers/multiplier TBD |
| B47 §§30.9,30.18 Glider from Smithy Weapons/Melee; water-only harpoon; diving platform/fish oil/tether | Later tools/underwater | Planned | 1 Fish Oil per 90 seconds, platform slot 100; unlimited vertical/limited horizontal tether; Harpoon Gun Bolts from Smithy Ammo; glider controlled descent |
| B48 §§3,15,16 Biomes/caves/mountain treasure and traversal options | World/treasure | Planned | X marks actual cave treasure, not entrance; mountain flat diggable area, spiders/guardians and varied traversal; distributions TBD |
| B49 §18 Public communication operations | Multiplayer launch | Planned | Mute/block/report/moderation before public multiplayer launch; not a current prototype feature |
| B50 §§25-27 Architecture and operating rules | All slices | Partially Implemented C++/Blueprint/data/Git LFS foundation | Ship must stay separate authoritative actor; binary assets via Unreal-supported APIs; no competing agent edits; explicit decisions supersede older text, unresolved rules TBD |

## Integrated Bible section coverage

October additions §§28-30 and Appendices E-F are reviewed in full in [revision review](DESIGN_REVISION_2026_10_05.md), including startup/save/creator, administration/audio, ship hardpoints/caps/decay, stats/combat, crafting, underwater/fishing, crew wages, and corpse/bed rules. Their exact implementation traceability will grow with each slice; no feature is marked implemented from design text alone.

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

For each slice update status, relevant file paths, exact verification, limitation and commit. Record intentional departures in [DECISION_LOG.md](DECISION_LOG.md). No departure from the central ship-home vision is approved here. Foundations and temporary UI do not satisfy the complete Bible requirement.
