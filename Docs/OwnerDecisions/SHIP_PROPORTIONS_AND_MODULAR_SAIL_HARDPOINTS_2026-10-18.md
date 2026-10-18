# Owner ship proportions, helm placement and sail hardpoints — October 18, 2026

Status: **OWNER DESIGN DIRECTION — NOT IMPLEMENTED**. This is newer than conflicting October 15 ship-size instructions. Claude must reconcile older requirements before coding. Preserve unrelated functionality and coordinate file ownership.

## Relative hull dimensions
- Raft: current size is satisfactory; do not resize.
- Sloop: reduce existing oversized proportions. Target overall height approximately **three raft heights stacked vertically** (a visual scale reference, not an approved meter dimension). Keep accessible below-deck space, but **no captain's quarters**.
- Schooner: approximately the **same width as the sloop**, but **longer and taller**.
- Brigantine: **wider and taller than the schooner**. Length is not specified; do not invent an exact value.
- Cavalier: approximately the **same overall size as the brigantine**, but arranged with **multiple traversable stories**. This newer direction supersedes the older requirement that the Cavalier must be physically larger than the brigantine. Preserve the previously approved three traversable deck levels unless the owner explicitly changes them.
- No exact dimensions, deck clearances, or ship statistics have been approved. Build proportion studies before finalizing scale.

## Modular sail attachment
- For **every ship** (including sloop, schooner, brigantine, Cavalier, and other applicable ships), remove permanently attached sail assemblies from the base ship configuration.
- At each existing sail location, preserve a **clearly identified, functional sail attachment hardpoint** so players can install sails later. Design reference markers should not be mistaken for permanently mounted sails.
- Maintain compatibility with the planned modular sail system; preserve sailing and progression functionality during migration. Distinguish base hull without sails from a configured sailing vessel. Do not silently delete player-owned sail assets.

## Captain's quarters and helm
- **Sloop:** no captain's quarters; retain below-deck access.
- **Schooner:** aft captain's quarters occupying approximately **one eighth of ship length**, extending **across the full width**. Place staircases leading up **on both sides**. The steering wheel is **on top of the captain's quarters**, on the raised aft deck.
- **Brigantine:** captain's quarters **longer than the schooner's**; steering wheel **inside** the captain's quarters.
- **Cavalier:** captain's quarters **the same length as the brigantine's**; steering wheel **inside** the captain's quarters. Maintain multiple levels.
- Retain the existing railings around the ship. Add **fixed, non-editable safety railings** along the staircases and the raised aft deck perimeter around/above the captain's quarters. These are not interchangeable player-built railing modules; preserve the separately approved modular outer railing system.
- Ensure stairs, helm interaction, navigation and collision are functional, not merely decorative.

## Art production and handoff
- ChatGPT creates consistent visual reference images for ships, sail variants and five sail positions, sail hardpoints, railings, gunports, cannons, flags, weapons, tools, equipment and crafting illustrations. **Exclude scenery.**
- Claude translates approved image references into Unreal Engine **5.8.3** implementation, preserving class distinctions and functional systems. Reference art is not proof of in-game assets or integration.
- Progress tracking must distinguish reference images produced, models/materials authored, code committed, and verified in-engine. Do not claim images exist until generated and attached/committed.

## Claude implementation procedure
1. Review current ship code, hull generation, deck access, sail mount definitions, placement/crafting systems, and prior ship specs.
2. Create proportion/plan reference views for all four classes and the raft before changing existing meshes; explicitly reconcile Cavalier's superseded larger-than-brigantine rule.
3. Implement hull dimensions, accessible spaces, stairs, captain's quarters, helm locations, fixed safety railings, and sail hardpoints with player-safe migration.
4. Run Unreal Engine 5.8.3 build and Play verification for ship navigation, sailing, modular fittings, collision, below-deck access and helm use, including multiplayer where relevant. Record screenshots and tests.
5. Respect delegated file ownership and editor lock. Report changes and blockers in the shared coordination inbox. Do not treat this design document as completed implementation.

Any ambiguous exact measurements remain TBD rather than guessed.

## Craftable ship items and shipyard tiers (owner-confirmed October 18)
- Every ship class is its **own distinct craftable item** with its own ship identity/recipe entry; do not treat ships as merely cosmetic variants of one item.
- **Small shipyard:** craft **Raft** and **Sloop**.
- **Medium shipyard:** craft **Schooner** and **Brigantine**.
- **Large shipyard:** craft **Cavalier**.
- Enforce these as the authorized crafting locations. Do not assume higher-tier shipyards can craft lower-tier ships unless separately approved.
- Resource ingredients, crafting duration, unlock costs and prerequisites remain **TBD**; do not invent values.
- Claude should connect the ship item definitions, shipyard UI, recipes and spawn/placement workflow; preserve existing inventories, saves and multiplayer behavior, and verify each ship is craftable only at its approved yard tier.

## Stern boarding ladder placement (owner-confirmed October 18)
- Place the boarding ladder at the **very back center (stern centerline)** of each ship, rather than offset to port or starboard.
- Keep the ladder usable for boarding from the water, with collision, reachable access, and clearance verified for each hull. Preserve unrelated interior ladders and staircases unless their placement conflicts with this boarding requirement.
- Update ship visual reference images and implementation layouts to show this exact stern-center boarding-ladder location. Do not claim the images have been regenerated until they actually have been.


Publication note (October 18): copied as reviewed owner-decision documentation from the existing chatgpt branch into main by a direct documentation commit. No branch merge or implementation is implied. Later gap-filling choices are in Docs/REPORTS/2026-10-18_ChatGPT_Delegated_Decisions.md.
