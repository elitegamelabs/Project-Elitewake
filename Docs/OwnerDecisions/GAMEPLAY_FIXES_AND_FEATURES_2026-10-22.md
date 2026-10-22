# Owner direction — gameplay fixes and features (October 22, 2026)

Source: the owner's "Updated Development Tasks" message to Claude, recorded in substance. It sets the priority: **stop developing new ships; build a
functional, playable world and the core systems before expanding.** Status of each item is tracked in `Docs/MILESTONES.md` and the inbox; this file is the
specification, not a claim that anything is done.

Instructions that apply to every item: inspect the existing implementation before changing it; follow the ELITEWAKE design documents and resource guides; reuse
working systems; make features functional, not visual placeholders; support controller and keyboard/mouse throughout; test in the current game project; do **not**
introduce new ships or expand ship development; preserve working features; quarantine removed assets where instructed; **do not claim a feature complete unless it is
implemented and tested.** After implementation, give a concise report: completed, tested, unfinished, blockers.

## 1. Controller support and hotbar
- Every keyboard/mouse action has an equivalent controller input, using standard MMORPG-style controller mappings.
- Redesign hotbar assignment so players can easily assign, switch and activate abilities with a controller.
- Every interface and interaction supports both control methods.

## 2. Death, respawning and damage indicators
- Death when health reaches zero. Fade to black, a frost effect around the edges, and an interactive respawn option.
- Respawn at a randomized, safe location in the surrounding area, a meaningful distance from the death location.
- A small red indicator that briefly bounces or flashes off the character when it takes damage.

## 3. Inventory and menu navigation
- Fix the issue that only Inventory and Crafting are accessible. Every intended menu section is reachable by mouse, keyboard and controller.

## 4. Island geography and ocean
- The Central Region is a plains biome where all players begin. Keep **five islands, one per region**.
- Islands about **1,500 to 2,500 m** across, with organic, irregular coastlines, not rectangular. Remove rigid island measurements that force unnatural geometry.
- **Ocean depth 2,000 m to 1,500 m.**

## 5. Wildlife and resources
- More naturally roaming land animals and sea life in appropriate habitats. More harvestable resources per the resource guide.
- Confirm whether all resource reference images are in the GitHub repository.
- **Remove the manatee from active gameplay; move its artwork and related assets into quarantine.**

## 6. World map and fog of war
- A square map interface with basic navigational information. Unexplored areas covered by misty grey fog with visible clouds.
- Fog disperses in a circular radius around the player as they explore; discovered areas stay permanently visible.

## 7. Skill tree and crafting progression
- The previously planned constellation skill tree with interconnected nodes and unlockable skills.
- Unlocking skills adds the associated recipes to the crafting menu. Hovering a craftable item shows a smaller side panel of required materials; controller selection shows the same.
- Crafting checks available resources, consumes the materials, takes several seconds and puts the item into the inventory.
- Prioritize this functional progression over more ship development.

## 8. Character creation and Survivor interface
- Basic male/female character creation with customizable physical features, shown consistently in gameplay, spawning, cutscenes and the Survivor inventory section.
- If not feasible immediately, show the existing player character in the Survivor section as an interim. Begin implementing testable character systems now.

## 9. Leveling and stat points
- One assignable stat point per level. Stats shown beside the character in the Survivor interface, including before any points are earned.
- Interactive allocation controls; increase arrows are blurred/disabled until a point is available, then clear and interactive. Mouse and controller.

## 10. Journal
- Redesign the journal pages to look like authentic aged paper from an old explorer's journal.

## 11. Swimming and water
- More natural swimming animation and movement. Reduce excessively strong currents and drifting; releasing the stick or keys must not carry the player away quickly.
- Players must be able to catch a drifting ship, climb aboard and collect ocean resources and treasure chests without fighting excessive currents.
