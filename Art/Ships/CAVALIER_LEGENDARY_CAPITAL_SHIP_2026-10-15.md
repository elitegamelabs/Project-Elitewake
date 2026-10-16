# ELITEWAKE — Cavalier Legendary Capital Ship
Date: 2026-10-15
Status: CONFIRMED owner direction — design requirements; implementation not yet verified

## Owner decision
The **Cavalier** is a distinct ship class and must be the **largest ship in ELITEWAKE**, larger than the Brigantine. Treat this as the latest owner decision wherever older documentation implies the Brigantine is the largest vessel. Do not rename the Brigantine: both classes remain in the game.

## Design intent
- The Cavalier must read immediately as a massive, high-definition capital vessel when seen beside a Brigantine or any smaller ship.
- Preserve the game's core identity: **THE SHIP IS HOME.** Its scale should support the fantasy of a persistent ship-home, crew headquarters, cargo carrier, exploration platform, and formidable naval-combat vessel.
- Establish its own recognizable silhouette and proportions rather than scaling up the Brigantine mesh. Give it a distinct hull profile, bow and stern treatment, deck arrangement, railings, superstructure, and other class-defining details.
- Design believable hull volume, deck spacing, access routes, crew circulation, boarding points, and visible structural support at this larger scale. Avoid oversized empty decks or details that are too small to read at gameplay distance.
- Maintain the modular sail rule: the base hull has no permanently integrated sails. Sail assemblies are separate attachable/removable modules containing their supporting masts/poles, pre-mounted flags, sail cloth, rigging, sockets, and attachment details. Make the rig plan appropriate to the Cavalier's own silhouette and scale.
- Use high-definition presentation: detailed, coherent geometry; high-resolution physically based materials; convincing timber grain, seams, fasteners, metalwork, ropes, rigging, and weathering; carefully authored normal/roughness/material detail; and strong close-up and gameplay-distance readability. Avoid relying on texture resolution alone to make the ship appear high quality.
- Keep visual detail performant and technically appropriate for Unreal Engine 5.8. Use sensible material instances, LODs, collision, Nanite only where suitable, and texture/streaming budgets consistent with the project's architecture.
- Preserve existing ship controls, sailing, damage, flooding, repair, cargo, crew, module attachment, save/persistence, and multiplayer authority contracts. A larger visual ship must not silently bypass those systems.

## Gameplay and balancing constraints
- The confirmed decision is relative size: **Cavalier > Brigantine**. Exact dimensions, crew capacity, cannon count, cargo capacity, speed, durability, draft, construction cost, shipyard tier, and unlock conditions remain **TBD** until separately approved or reconciled with the authoritative balance tables.
- Do not invent statistics or assume that the largest ship must be fastest or strongest in every category. Present proposed balance values for owner approval before making them canonical.
- Account for the Cavalier's size in turning radius, acceleration, stopping distance, shallow-water access, docking, collision, boarding, camera framing, pathing, network replication, and performance.
- Keep the Brigantine as a distinct existing class. Do not delete, replace, or downgrade its existing identity or assets as a shortcut.

## Asset and implementation workflow
Track these as separate deliverables:
1. Concept/reference design and silhouette comparison against the Brigantine.
2. High-definition hull and deck 3D asset, with materials.
3. Separate Cavalier-compatible sail/rigging attachment assemblies.
4. Collision, sockets, interaction points, deck navigation, LODs, and performance setup.
5. Integration into the existing ship class/module/data architecture.
6. Gameplay validation in Unreal Engine 5.8, including boarding, sailing, docking, damage, cargo, persistence, and multiplayer-relevant behavior where supported.

Inspect the repository's current ship assets, class data, shipyard recipes, and shared design rules before implementation. Reuse existing architecture where appropriate; do not overwrite or remove user assets or make unrelated changes. If the local project is not available, report that limitation and provide a plan rather than claiming implementation.

## Acceptance criteria
- Cavalier is represented as a distinct ship class and is visibly larger than the Brigantine in a controlled side-by-side comparison.
- The Cavalier has its own coherent high-definition design; it is not merely a uniformly scaled Brigantine.
- Base hull and removable sail assemblies follow the modular sail requirements.
- Any class statistics or economy changes are explicitly approved and documented rather than guessed.
- Integration is verified in Unreal Engine 5.8; report design, asset creation, integration, and in-game testing as separate statuses.


## Confirmed three-level deck layout (owner clarification, October 15, 2026)
The Cavalier must have **three traversable levels**:
1. **Upper deck** — the topmost open/main deck.
2. **Second deck** — a distinct deck level directly below the upper deck.
3. **Lower interior deck/floor** — a third level reached by descending a ladder from the level above.

The three levels must be physically legible and connected by usable ladders/access openings, with sufficient headroom, believable structural supports, lighting, collision, and navigation for characters. Do not interpret this as only two levels. Show the three-level arrangement in reference drawings and ensure the 3D layout supports actual in-game traversal. Exact room functions and weapon placements remain TBD unless separately approved; preserve established ship-system and combat requirements.
