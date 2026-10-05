# Development roadmap

Updated: 2026-10-05. Active project: `C:\UnrealProjects\EW`; repository: `elitegamelabs/Project-Elitewake`.

## Authority and scope

The Integrated Master Game Design Bible dated September 21, 2026 is the creative reference. The historical development chat and handoff establish the five-person team and current milestone. The shorter pasted design text contains older rules explicitly replaced in the integrated Bible. See [context reconciliation](CONTEXT_RECONCILIATION.md) for sources, conflicts and their resolution. Preserve **THE SHIP IS HOME** and the loop Prepare -> Sail -> Discover -> Fight/Explore -> Loot -> Escape -> Upgrade -> Sail Farther. Version 0.01 is a playable vertical slice. Official regional infrastructure and the seamless long-term world are later work, not prerequisites for the first slice.

See [milestone status](MILESTONE_STATUS.md), [requirement traceability](DESIGN_BIBLE_TRACEABILITY.md), and [decisions](DECISION_LOG.md). Dates below are review dates, not delivery promises. Milestones after M5 are proposed work packages, not previously approved numbered milestones.

## Foundation already established

| Milestone | Scope | Remaining gate |
| --- | --- | --- |
| M0 | Active project outside OneDrive, Git baseline and structure | Keep generated files out of source control |
| M1 | Movement, jump, sprint, Enhanced Input | Repeat network validation; controller coverage |
| M2 | Crouch/prone state and collision | Proper animation assets and integration are Postponed |
| M3 | First/third-person cameras and locomotion states | Final camera/animation presentation and controller binding |
| M4 | Replicated survival values and stamina | Final HUD, environmental needs and multiplayer validation |
| M5 | Items, inventory, equipment | In Progress; see slices below |

## M5: small, testable slices

| Order | Slice and Unreal system | Dependencies | Acceptance gate |
| --- | --- | --- | --- |
| 5A | C++ item Data Assets and replicated inventory | Character, survival | Stacking/removal/weight automation; implemented in `9b7f129` |
| 5B | Native UMG draft; Enhanced Input inventory toggle | 5A, local controller | Build; empty panel; I open/close; cursor and movement/camera recovery; reopen |
| 5C | Basic Wood test Data Asset and opt-in server grant | Verified 5B; asset registration | Real persisted item reference, live populated panel, weight, stacking; no default free items in normal gameplay |
| 5D | C++ pickup actor and server-validated interaction; Blueprint placement | 5C | Range/ownership checks, partial capacity, no duplication with competing clients, replication |
| 5E | Inventory item selection and interaction UI | 5D | Keyboard/controller selection, visible highlight; exact operations defined per slice |
| 5F | Replicated equipment component and equip/unequip | Item slot metadata, 5E | Server validates ownership/slot; inventory transfer atomic; weight conserved; client views agree |
| 5G | Eight-slot hotbar and bindings | 5F and item-use semantics | 1-8 selection; controller LB modifier with face buttons/d-pad; server validates use |

Controller Y and selection are Design Bible requirements; the current I-only panel is an incremental draft. Establish an asset-manager scan for item Data Assets before relying on primary asset discovery or packaging. Character preview and final artwork follow gameplay and suitable assets.

## Bible build order and remaining gates

Bible §24.3 specifies: baseline -> locomotion/input -> camera/animation state -> survival/HUD -> items/inventory/equipment -> interaction -> gathering -> crafting/skills -> sword/enemy -> shovel/map objective/treasure -> ship/helm/anchor/cargo/weight -> cannons/shared ammo -> day/night/cold/fire/clothing -> Village/vendors -> prologue logic -> map/compass -> additional encounters/polish. Use this dependency order as the reference; the later conversational M0-M5 labels are not a one-to-one numbering of that list.

M4 remains partially implemented. Preserve a separate survival/HUD return slice for health/stamina/hunger/hydration/weight display, activity-dependent hunger/hydration drain, starvation/dehydration consequences and fresh/salt drinking. Rates remain TBD. The later owner move to M5 does not verify or cancel these requirements.

## Proposed 0.01 work packages after M5

1. Gathering and crafting: harvestable tree, tool interaction, recipes, resource costs and unlock prerequisites. C++ authority; Data Assets for recipes/resources; Blueprints for world content; UMG for crafting. Verify no resource duplication or unaffordable crafting.
2. Skills, simple combat and treasure: 15 cumulative points per level, respec from level 10, shovel/digging, map objective and small enemy encounter. Deterministic C++/Blueprint behavior; data-driven rewards. Verify progression and authoritative damage/rewards; costs and maximum level remain TBD.
3. Small ocean and starter sloop: helm, hold-to-anchor, cargo, ship weight and two opposing cannons with shared limited ammunition. Depends on movement/interaction/inventory; test boarding, moving deck behavior, cargo transfer, anchoring and overload immobility in multiplayer.
4. Environment, Village/prologue and navigation: four real hours each for day/night, contextual conditions, basic Village vendors, revised raft/journal opening, then map/compass. M/View opens map; walking allowed, sprint/stance/hotbar/inventory suppressed, world still runs. Test controller View conflict before radial commands. Survival/HUD return work above must not be silently delayed until final polish.
5. Integrated 0.01 playthrough: Prepare/Sail/Discover/Loot/Upgrade on a small test world. Repeat dedicated-server and two-client checks, packaging, save/load where implemented, and performance checks. This does not imply the full prologue or finished content is ready.

## Longer-term backlog

Villages, specialized vendors, Ferryman routes, currency, shipyard progression, larger customizable vessels and belongings transfer; sail damage/repair and deeper naval combat; storms/adventure encounters, ghost ships, floating salvage and dungeons; tribes and communication; crew roles and shared commands; Beast Mastery, taming/breeding; injuries/surgeon, aging/hair/rejuvenation; world density and official regional hosting.

Preserve the revised prologue in Bible §§21-22: storm aboard a large ship -> steering/cannons and losing battle -> boarding and sword fight alongside Quartermaster -> head injury -> Quartermaster rescue in dinghy -> island awakening/amnesia/journal -> wood/campfire/tools -> small shipyard and raft -> player steers offshore/title reveal -> raft docked at starter Village. Quartermaster leaves; speaking to the innkeeper starts Mission Two. Tour first stop and later content remain TBD. The older treasure-first opening is Replaced. The persistent two-cannon sloop remains planned, but its exact placement after the raft needs reconfirmation.

## Definition of a verified slice

Build the active editor target, run relevant automation, inspect Play mode, and record limitations before committing. Network-ready code is not multiplayer verification. Temporary UI is not final presentation. Update traceability, milestone status and decisions with evidence and a commit reference for each slice. Do not introduce paid dependencies, change the central vision or use character scaling instead of animation.
