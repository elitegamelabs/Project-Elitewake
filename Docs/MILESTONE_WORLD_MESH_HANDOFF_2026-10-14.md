# World mesh milestone handoff for Claude

Requested by the owner on October 14: terrain mesh construction is assigned to Claude. The current art-and-design workflow supplies references and requirements; it does not replace terrain during this handoff. This supplements M5 — Living world, whose older four-region description is superseded by the five-region owner decisions.

Authority: [world decisions](WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md), [single-player rules](SINGLE_PLAYER_RULES.md), [multiplayer rules](MULTIPLAYER_RULES.md). Original source documents remain unchanged.

| Deliverable | Acceptance requirement | Status |
| --- | --- | --- |
| Five region island groups | Desert, Winter, Jungle, Plains, Swamp; varied island sizes and shapes, substantial inland exploration and longer sailing voyages | First pass built October 15 (`PENDING`): 26 islands per `Scripts/Setup/world_layout.py`; island sizes are an open question |
| Shores | Approximately ten feet of beach sand, interrupted by appropriate cliff sections; desert is sandy inland too | Pending |
| Regional terrain | Grassy flatland and hills in Plains; tall dense Jungle; Winter rugged mountains, cliffs and smooth snowy slopes; Swamp wetlands | First pass built (`PENDING`, `Scripts/Setup/world_terrain.py`) |
| Varied cliff and cave placement | Selected cliff-bearing islands in every region; exactly one cave system per island, with inland, cliff-face and coastal entrances distributed differently | Pending |
| Fixed generation | Placement generated once per world and retained by save/server persistence | Pending |
| Ocean bathymetry | Shallower shelves and slopes, with selected deepest areas at 500 meters below the water surface | Built (`PENDING`): shelves to ~60–70 m between islands, 500 m in open-sea basins; `verify_coastal_ocean_depth_play` passes |
| Solid terrain and seabed | No swimmer can pass under the floor or beneath an island; continuous distant-ocean coverage and terrain-edge closure | Pending, current prototype escape path needs verification |
| Reachable mountains | Walkable slopes and climbing-axe cliff sections; coordinate with stamina-driven falls | Pending |
| World barriers | Terrain penetration must be blocked throughout the map; edge barriers preventing falls remain an owner question because they conflict with the falling rule | Blocked in part |
| Vegetation model presentation | Thick mature trunks, sturdy tapered branching with finer twigs; thick palms with overlapping pineapple-like old leaf bases; snow on winter trees and berry bushes | Pending model work |
| Three growth-stage meshes | Every plantable tree and seed-grown farm plant has three visually distinct stages; saplings only in their biome; static berry-bush appearance excluded | Pending; exact growth timing remains TBD |

Meaningful verification must sweep or move a real swimmer against the seabed and island edges, check under-island approaches and distant water, confirm maximum depth, and traverse intended slopes/climbing sections. Starting the map or compiling does not prove collision coverage. The complete five-region world is not marked done by adding this checklist.
