# Development roadmap

Updated: 2026-10-06. Active project: `C:\UnrealProjects\EW`; repository: `elitegamelabs/Project-Elitewake`.

## Authority and scope

The October 5, 2026 Authoritative Revision is the current creative reference, followed by direct owner clarification of the rye sale/introduction. See [revision review](DESIGN_REVISION_2026_10_05.md). Section 30 overrides older conflicting material. The historical development chat and handoff establish the five-person team and current milestone. Preserve **THE SHIP IS HOME** and the loop Prepare -> Sail -> Discover -> Fight/Explore -> Loot -> Escape -> Upgrade -> Sail Farther. Version 0.01 is a playable vertical slice; the first private beta focuses on single player while preserving multiplayer authority. Official regional infrastructure and the seamless long-term world are later work, not prerequisites for this slice.

See [milestone status](MILESTONE_STATUS.md), [requirement traceability](DESIGN_BIBLE_TRACEABILITY.md), and [decisions](DECISION_LOG.md). Dates below are review dates, not delivery promises. Milestones after M5 are proposed work packages, not previously approved numbered milestones.

## Foundation already established

| Milestone | Scope | Remaining gate |
| --- | --- | --- |
| M0 | Active project outside OneDrive, Git baseline and structure | Keep generated files out of source control |
| M1 | Movement, jump, sprint, Enhanced Input | Repeat network validation; controller coverage |
| M2 | Crouch/prone animations, distinct stance clearance and prone body movement query | Collision fixtures/slope/local packet emulation verified; physical controller and final animation polish remain; [collision record](M2_COLLISION_VERIFICATION.md) |
| M3 | First/third-person cameras and locomotion states | Final camera/animation presentation and controller binding |
| M4 | Replicated survival values and stamina | Final HUD, environmental needs and multiplayer validation |
| M5 | Items, inventory, equipment | In Progress; see slices below |

## M5: small, testable slices

| Order | Slice and Unreal system | Dependencies | Acceptance gate |
| --- | --- | --- | --- |
| 5A | C++ item Data Assets and replicated inventory | Character, survival | Stacking/removal/weight automation; implemented in `9b7f129` |
| 5B | Native UMG draft; Enhanced Input inventory toggle | 5A, local controller | Build; empty panel; I open/close; cursor and movement/camera recovery; reopen |
| 5C | Basic Wood test Data Asset and opt-in authority grant | Verified 5B; asset registration | Verified saved fixture scan/load, 250-stack boundary/capacity/weight automation and populated/live-refresh Play panel; normal Play starts empty. [Evidence](M5C_INVENTORY_VERIFICATION.md) |
| 5D | C++ pickup actor and server-validated interaction; Blueprint placement | 5C | Verified range/ownership/visibility, partial capacity and competing host/client intents with packet emulation; [evidence](M5D_PICKUP_VERIFICATION.md) |
| 5E | Inventory item selection and read-only details UI | 5D | First valid focus, highlight, keyboard/D-pad/stick/mouse, confirmation and live refresh verified; [evidence](M5E_SELECTION_VERIFICATION.md) |
| 5F | Replicated equipment component and equip/unequip | Item slot metadata, 5E | Verified server ownership/slot checks, atomic inventory transfers, worn weight and client agreement under packet emulation; [evidence](M5F_EQUIPMENT_VERIFICATION.md) |
| 5G | Eight-slot hotbar and bindings | 5F; other actions depend on their item systems | Verified assignment, 1–8/LB activation and authoritative equipment shortcuts; [evidence](M5G_HOTBAR_VERIFICATION.md). Consumables/maps/taming/harpoon restrictions and persistence remain separate gates |

Controller Y and selection now have draft implementation and scripted input verification; physical hardware testing remains open. The M5C primary item scan is verified; packaging remains a separate gate. Character preview and final artwork follow gameplay and suitable assets.

## Bible build order and remaining gates

Bible §24.3 specifies: baseline -> locomotion/input -> camera/animation state -> survival/HUD -> items/inventory/equipment -> interaction -> gathering -> crafting/skills -> sword/enemy -> shovel/map objective/treasure -> ship/helm/anchor/cargo/weight -> cannons/shared ammo -> day/night/cold/fire/clothing -> Village/vendors -> prologue logic -> map/compass -> additional encounters/polish. Use this dependency order as the reference; the later conversational M0-M5 labels are not a one-to-one numbering of that list.

M4 remains partially implemented. Preserve a separate survival/HUD return slice for health/stamina/hunger/hydration/weight display, activity-dependent hunger/hydration drain, starvation/dehydration consequences and fresh/salt drinking. October §30.15 now specifies base sprint/recovery timing, 15-minute needs depletion, warnings and regeneration; upgraded-stat/activity scaling and health-loss interpretation still require clarification. The owner move to M5 does not verify or cancel these requirements.

## Proposed 0.01 work packages after M5

1. Gathering and crafting: harvestable tree, tool interaction, recipes, resource costs and unlock prerequisites. C++ authority; Data Assets for recipes/resources; Blueprints for world content; UMG for crafting. Verify no resource duplication or unaffordable crafting.
2. Skills, simple combat and treasure: 15 cumulative points per level, character cap 80, respec from level 10 for 2 Gold, shovel/digging, map objective and small enemy encounter. Deterministic C++/Blueprint behavior; data-driven rewards. Verify progression and authoritative damage/rewards; node costs remain TBD where not assigned.
3. Small ocean and starter sloop: helm, hold-to-anchor, cargo, ship weight and two opposing cannons with shared limited ammunition. Depends on movement/interaction/inventory; test boarding, moving deck behavior, cargo transfer, anchoring and overload sinking in multiplayer. Implement current hardpoint and storage-only Ammo Bin rules.
4. Environment, Village/prologue and navigation: 90 real minutes each for day/night, contextual conditions, basic Village vendors, revised schooner battle/dinghy repair/journal opening, then map/compass. M/View opens map; walking allowed, sprint/stance/hotbar/inventory suppressed, world still runs. Command radial uses Middle Mouse / D-pad Right. Survival/HUD return work above must not be silently delayed until final polish.
5. Integrated 0.01 playthrough: Prepare/Sail/Discover/Loot/Upgrade on a small test world. Repeat dedicated-server and two-client checks, packaging, save/load where implemented, and performance checks. This does not imply the full prologue or finished content is ready.

## Longer-term backlog

Villages, specialized vendors, Ferryman routes, currency, shipyard progression, larger customizable vessels and belongings transfer; sail damage/repair and deeper naval combat; storms/adventure encounters, ghost ships, floating salvage and dungeons; tribes and communication; crew roles and shared commands; Beast Mastery, taming/breeding; injuries/surgeon, aging/hair; world density and official regional hosting. Davy Jones quest is Removed, not a planned rejuvenation implementation.

Preserve October §§21,30: far-offshore schooner vs brigantine -> flooding/bailing -> boarding and sword fight -> head injury and lost sword -> unconscious Quartermaster rescue with rare rye -> island amnesia/journal -> gathering/tools -> Repair Kit/hammer and Small Sail on surviving dinghy -> sail/title/Village. Tutorial tools/supplies are discarded, but rare rye stays in player inventory. Survivor starts with zero currency. Innkeeper responds to request for free lodging with work/trade, introduces town-square merchants (quests later), and general merchant offers rye sale. Credit 250 Copper when the introduction mission completes; room charge remains unspecified. Raft/shipyard construction is no longer the opening. Persistent sloop progression placement remains to be designed.

## Definition of a verified slice

Build the active editor target, run relevant automation, inspect Play mode, and record limitations before committing. Network-ready code is not multiplayer verification. Temporary UI is not final presentation. Update traceability, milestone status and decisions with evidence and a commit reference for each slice. Do not introduce paid dependencies, change the central vision or use character scaling instead of animation.
