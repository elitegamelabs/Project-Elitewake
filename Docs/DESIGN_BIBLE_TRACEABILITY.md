# Design Bible traceability

Reviewed: 2026-10-05. Source: supplied Game Design Bible text attachment (`0e221f0a-76c5-44a3-bb4b-e3191d99870e/Pasted text.txt`); development handoff is newer for team/current status. This is a requirement index, not a claim that future features are implemented.

M0-M5 are established milestones. Later work-package names refer to the proposed roadmap. Planned rows have no production implementation or verification unless explicitly stated. Existing Epic template variants are not evidence of Elitewake feature completion.

| ID / Bible section and requirement | Milestone/package | Status, files/system and commit evidence | Verification, limitations / deferred content |
| --- | --- | --- | --- |
| B01 Core identity: ship is home; adventure interrupts routine; core loop | 0.01 integration / ships | Planned gameplay; `README.md`, roadmap record vision; `50ecc95` | No playable ship loop yet |
| B02 World: dense seamless islands; official regional servers and overflow | Long term world/hosting | Planned world/infrastructure | No MMO-first implementation; 0.01 small world |
| B03 Villages: neutral trade hubs, specialized vendors, limited Ferryman routes | Settlements/prologue | Planned deterministic NPCs and route data | Use Village terminology; not unrestricted fast travel |
| B04 Survival: health/stamina/hydration/weight | M4/M5 | Implemented `EWSurvivalComponent.*`, inventory-weight sync; `55ed2c1`, `9b7f129` | Stamina/weight foundation only; final HUD and multiplayer validation pending |
| B05 Future needs: hunger/temperature/wetness/poison/bleeding/fractures/disease/injuries/environment | Environment / long term survival | Hunger and body-temperature values Implemented in M4; rest Planned | Values do not establish environmental gameplay |
| B06 Fresh water restores hydration; salt water harms; direct drinking | Survival interactions | Planned water-source/use logic | No water consumption verified |
| B07 Character: non-explicit minimal clothing, aging, hair/scissors, Fountain of Youth | Character content / long term | Planned | Template mannequin is not final character content |
| B08 Armor/equipment: body slots, material/protection tiers; cosmetics separate from stats | M5F / crafting | Slot definitions Implemented `EWItemDefinition.h`; `9b7f129`; equip system Planned | Metadata is not equipped gear, protection or appearance |
| B09 Enhanced Input; WASD/mouse, sprint/jump, C/hold C and B/hold B | M1/M2 | Implemented `EWCharacter.*`; `d8ca1dc`, `5f08eb7` | Remapping UI and complete controller checks Planned |
| B10 Third-person default, dynamic first/third person, Z; appropriate animations | M3 / animation | Cameras/states Implemented `fb214b3`; stance animation Postponed | Scaling Replaced by revert `e88acb1`; final animation set pending |
| B11 Inventory I / controller Y; automatic first selection, d-pad/stick and highlight | M5B/E | I empty draft Verified `EWPlayerController.*`, `EWInventoryWidget.*`; Git title `Fix and verify native inventory panel` | Lifecycle repair built/tested; local open/close/reopen and control recovery passed; Y/navigation and populated/network UI Planned |
| B12 Inventory character preview with hair/gear; adjacent crafting and future tabs | M5 presentation / crafting | Planned UMG/preview/content | Functional draft only; no permanent tutorial clutter |
| B13 HUD: readable survival data, conditions/equipment/ship prompts; eight-slot bottom-center hotbar | M4 presentation / M5G | Temporary cyan debug text Implemented; final UMG Planned | Debug text is not final HUD; 1-8 bindings Planned |
| B14 Pause: Escape/Start, Resume/Options/Exit with confirmation | UI/input | Planned | Editor Escape ending Play is not game pause behavior |
| B15 Map M: circular exploration and persistent reveal; physical map/compass with directions | Navigation | Planned C++ discovery/state, UMG and content | Persistence and controller bindings pending |
| B16 Accelerated 24h sun; dark/cold nights; fire/torch/clothing/shelter | Environment | Planned | Template daylight is not a time cycle |
| B17 Interconnected skills, points/recipes; Shipwright gated | Skills/crafting | Planned data-driven unlock framework | Shipwright not immediately available; full tree later |
| B18 Tools/resources: axes, mining, gardening, shovel, harvesting; island variation | Gathering/treasure | Planned actors, item assets and interactions | No harvesting system claimed |
| B19 Climbing picks: steep terrain, stamina and durability | Later traversal | Planned | Access to rare resources/treasure/claims later |
| B20 Stations: smithy, forge, loom, storage; ore processing and sail repair | Crafting/ships | Planned recipes and station access | No station content implemented |
| B21 Ship home placement/removal and transfer belongings to larger vessel | Ships/home | Planned placement/storage/transfer | Must preserve important belongings on upgrade |
| B22 Ship customization; small vessels stay useful | Ships progression | Planned | Hull/deck/masts/sails/weapons/armor/modules/crew/cargo/decor/skins later |
| B23 Ship cargo weight worsens performance; overload prevents movement | Starter sloop | Planned ship inventory/weight model | Player carried weight is not ship weight |
| B24 Hold-to-anchor; anchored ship cannot sail; HUD status | Starter sloop | Planned interaction/ship state | Network anchoring checks pending |
| B25 Preset sloop: helm, anchor, cargo, weight, two opposing cannons, shared limited ammo | Starter sloop / naval combat | Planned | Larger ship manually placed cannons later |
| B26 Shipyard near dock; repair/build/manage/upgrade/customize with progression | Ships/Village | Planned | Depends on Shipwright progression |
| B27 Damageable sails, loom/material repair; cosmetic skins without automatic stats | Crafting/naval combat | Planned | Content and authoritative repair costs pending |
| B28 Readable naval combat: ammo, mast/sail/rudder, flood/fire/boarding/grappling/repair/penetration/injury | Naval combat expansion | Planned future scope | Simple two-cannon slice precedes deeper systems |
| B29 Random hostile ghost ships; defeat and recruit special sailors | Adventure/crew | Planned future encounters | No spawn/reward/crew system |
| B30 Floating crates: notice, anchor, swim, loot, return | Adventure | Planned | Depends on swimming, ship and inventory interactions |
| B31 Bottle treasure maps; reveal rarity, destination, shovel digging; stronger encounters/rewards | Treasure | Planned data assets/objectives/rewards | Rarity colors remain undecided |
| B32 Treasure enemy trigger; dungeons/waves/boss reward; possible territory link | Combat/encounters | Planned | Territory connection is future possibility |
| B33 Tribes: invite/cooperate/sail/territory; blue friendly map indicators | Multiplayer social | Planned | No tribe authority/UI or territory system |
| B34 Shared crew/creature commands: Follow(All), Stay(All), Return to Ship; Stay=Stop | Crew/creatures | Planned deterministic commands | Return All/combat commands future; radial Ctrl/View pending |
| B35 Taming by food/method and Beast Mastery; breeding/imprinting and possible inherited traits | Creatures progression | Planned | Stats/appearance/colors/temperament/abilities/size/mutations/lineage future |
| B36 Deterministic NPC roles; crew names/XP/equipment/traits/loyalty/injury/specialization | Crew/NPCs | Planned | No generative AI for ordinary runtime NPC behavior |
| B37 Surgeon: visible gauze/bandage/stitch/splint/wound/surgery; injuries separate from health | Later injuries | Planned | Health component is not persistent injury system |
| B38 Currency: 100 Copper=1 Silver; 500 Silver=1 Gold; data-driven shops | Economy/Village | Planned | Conversion locked by reference; no economy implementation |
| B39 Text/proximity voice/tribe/crew; possible alliance/direct messaging | Multiplayer communication | Planned | No voice/chat infrastructure claimed |
| B40 Current prologue sequence: awakening/map/shovel/treasure/ship/title; Village survival; sinking/swim/sword/treasure/Ferryman/larger ship/world | Prologue integration | Planned concept | Full sequence preserved in roadmap; not immutable script or completed content |
| B41 0.01: movement/input/perspectives/survival/HUD/inventory/crafting/skills/gathering/trees/combat/shovel/treasure/ocean/sloop/anchor/ship weight/two cannons/cargo/map/compass/day-night/controller/keyboard | 0.01 acceptance | Partial foundations M1-M5; remainder Planned | Final readiness requires integrated playable loop, content and network checks |

## Maintenance

For each slice update status, relevant file paths, exact verification, limitation and commit. Record intentional departures in [DECISION_LOG.md](DECISION_LOG.md). No departure from the central ship-home vision is approved here. Foundations and temporary UI do not satisfy the complete Bible requirement.
