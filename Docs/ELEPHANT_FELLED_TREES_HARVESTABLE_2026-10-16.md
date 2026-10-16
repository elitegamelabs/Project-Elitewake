# Owner decision: elephant-felled trees remain harvestable — October 16, 2026

Approved: On tropical Western Jungle islands, when elephants knock down a destructible tree, **the fallen tree remains on the ground** and **players can chop it with their hatchets to collect wood**. Do not immediately despawn it as a purely cosmetic effect.

Pending implementation milestones:
1. Elephant obstacle interaction triggers credible push, cracking, falling-tree physics and spatialized audio; avoid damaging protected or quest-critical structures.
2. Transition standing tree to persistent fallen-log state, with accurate collision and replication for all players. Maintain natural visual continuity and prevent duplicate resources.
3. Integrate fallen tree with existing hatchet harvesting, inventory, finite resource yield and gathering animation/sounds; no free pickup without player interaction.
4. Define cleanup/persistence and respawn/regrowth policy without inventing a duration; preserve reasonable server and rendering performance.
5. Unreal Play and multiplayer tests: elephant fells tree, log remains, player chops and receives wood exactly once, collision/navmesh updates, save/reload behavior as applicable.

Status: Owner-approved requirement documented; code/assets/testing still pending.
