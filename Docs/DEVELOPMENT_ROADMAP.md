# Development roadmap

Updated: 2026-10-05. Active project: `C:\UnrealProjects\EW`; repository: `elitegamelabs/Project-Elitewake`.

## Authority and scope

The supplied Design Bible text is the creative reference; the newer development handoff establishes the five-person team and current milestone. Preserve **THE SHIP IS HOME** and the loop Prepare -> Sail -> Discover -> Fight/Explore -> Loot -> Escape -> Upgrade -> Sail Farther. Version 0.01 is a playable vertical slice. Official regional infrastructure and the seamless long-term world are later work, not prerequisites for the first slice.

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
| 5G | Eight-slot hotbar and bindings | 5F and item-use semantics | 1-8 selection; controller flow without conflicts; server validates use |

Controller Y and selection are Design Bible requirements; the current I-only panel is an incremental draft. Establish an asset-manager scan for item Data Assets before relying on primary asset discovery or packaging. Character preview and final artwork follow gameplay and suitable assets.

## Proposed 0.01 work packages after M5

1. Gathering and crafting: harvestable tree, tool interaction, recipes, resource costs and unlock prerequisites. C++ authority; Data Assets for recipes/resources; Blueprints for world content; UMG for crafting. Verify no resource duplication or unaffordable crafting.
2. Skills, simple combat and treasure: basic points/unlocks, shovel/digging, starter map objective and small enemy encounter. Deterministic C++/Blueprint behavior; data-driven rewards. Verify progression and authoritative damage/rewards.
3. Small ocean and starter sloop: helm, hold-to-anchor, cargo, ship weight and two opposing cannons with shared limited ammunition. Depends on movement/interaction/inventory; test boarding, moving deck behavior, cargo transfer, anchoring and overload immobility in multiplayer.
4. Navigation, environment and survival HUD: map discovery persistence, compass, accelerated day/night, contextual conditions, keyboard/mouse and basic controller coverage. Test readability and input conflicts, then cold/water behavior in separate slices.
5. Integrated 0.01 playthrough: Prepare/Sail/Discover/Loot/Upgrade on a small test world. Repeat dedicated-server and two-client checks, packaging, save/load where implemented, and performance checks. This does not imply the full prologue or finished content is ready.

## Longer-term backlog

Villages, specialized vendors, Ferryman routes, currency, shipyard progression, larger customizable vessels and belongings transfer; sail damage/repair and deeper naval combat; storms/adventure encounters, ghost ships, floating salvage and dungeons; tribes and communication; crew roles and shared commands; Beast Mastery, taming/breeding; injuries/surgeon, aging/hair/rejuvenation; world density and official regional hosting.

Preserve the current prologue concept: island awakening -> starter map/shovel/treasure -> first vessel and title sunset -> Village survival/crafting -> voyage and scripted sinking -> swim ashore with shovel -> sword/enemies/treasure -> Ferryman -> larger ship -> wider world. Refine pacing separately when requested.

## Definition of a verified slice

Build the active editor target, run relevant automation, inspect Play mode, and record limitations before committing. Network-ready code is not multiplayer verification. Temporary UI is not final presentation. Update traceability, milestone status and decisions with evidence and a commit reference for each slice. Do not introduce paid dependencies, change the central vision or use character scaling instead of animation.
