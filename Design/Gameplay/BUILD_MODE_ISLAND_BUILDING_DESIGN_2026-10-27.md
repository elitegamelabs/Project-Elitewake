# Build Mode: building on every island (design, October 27, 2026)

Status: **owner confirmed October 27 (zones only carve out parts of an island, the rest is buildable; beaches are not buildable near docks). Milestone 1 (zone data and `IsBuildable`) is built and verified; milestones 2-5 are not started.** Source of the request: owner, October 26 ("the ability to build on every island that doesn't have an obstruction zone in the way"). Builds on the existing design in [DESIGN_REFERENCE.md, Crafting and building](../../Docs/DESIGN_REFERENCE.md) (Builder's Plan opens Build Mode, blue/red ghost) and the single-player rule in [WORLD_STRUCTURE_OWNER_DECISIONS](../../Docs/WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md) (single player builds anywhere; physical placement and claim permission are separate). Every number below is **tuning, not an owner-approved value**; items marked TBD need the owner.

## What exists now
- `UEWPlacementPreviewComponent` and `EW/UI/M_PlacementGhost_v1`: blue/red ghost, today for ship fittings only.
- `world_layout.near_port(x, y, margin)`: the Port site and waterfront footprint (used to keep trees and animals off).
- No Build Mode, no building pieces, no player-structure persistence, no claim flags.

## Rule: where a piece may be placed
A piece is valid (blue) only if **all** hold; otherwise red with the first failing reason shown as one line of text:
1. **On an island's ground:** the ground under every corner of the piece's footprint is above the waterline (+ a small margin) and is island terrain (not ship deck, not sea floor).
2. **Not in an obstruction zone** (below).
3. **Slope:** ground slope under the footprint no steeper than a limit (the foundation's slab reaches down to the lowest ground under it, so uneven ground up to 250 cm is allowed).
4. **No overlap:** nothing solid (rock, tree, other structure, ship, animal, player) intersects the footprint.
5. **Reach:** within the player's build reach (starting 8 m) and in line of sight.
6. **Claim permission:** multiplayer only. Single player skips this check entirely.

### Obstruction zones (data-driven list, so new ones need no code)
| Zone | Source | Status |
|---|---|---|
| Port site, waterfront and quay | `near_port()` (site radius `PORT_PAD` plus margin) | rule from owner ("Ports excluded") |
| Port islands for claiming | owner: NPC Port islands cannot be claimed | rule from owner (claim only) |
| Cave mouths and the walkway to them | cave sites in `world_terrain` | proposed |
| Landmarks and quest-critical objects | landmark list | proposed |
| Spawn and the starter dock landing | PlayerStart, `world_layout` dock | proposed |
| Ship routes: the strip from every dock/quay out to deep water | dock data | proposed |
| Beaches' first N metres above the waterline (so docks stay reachable) | terrain | owner: beaches are not buildable near docks (5 m radius ring round every dock, ground under 1.5 m above the waterline); other beaches are buildable |

Open question for the owner: the request says "every island that doesn't have an obstruction zone in the way". This design reads that as **zones carve out parts of an island, and the rest of the island is buildable**, not "an island with any zone is closed". Please confirm.

## How the player uses it
- Craft the **Builder's Plan** (existing design). Equip it to open Build Mode: a piece wheel (controller: right stick / D-pad; keyboard: number keys and scroll), the ghost follows the crosshair, snapped to the ground and to neighbouring pieces' sockets.
- Controls (both devices equal): place (primary: left click / R2 or A), rotate (Q-E / bumpers), cycle material variant, cancel, demolish mode.
- First pieces (small, to prove the system, owner can change): foundation (floor), wall, doorway, roof, stairs, storage chest, campfire. Material variants follow the regional woods/stone; all use the one inventory Wood/Stone resources (existing rule).
- Placing consumes items from inventory; demolishing refunds a share (starting 50 %, TBD).
- The ghost uses the existing blue/red highlight; on red, the reason text.

## Technical design (when built)
- `AEWBuildPiece` actor: server-authoritative, replicated, one actor per piece, with a data asset per piece (mesh, footprint, sockets, cost, health, material variants).
- `UEWBuildComponent` on the character: owns Build Mode state, the ghost, and a server RPC `ServerPlace(PieceId, Transform, Variant)`. The server re-runs every validity check; the client's ghost colour is only a prediction.
- `UEWBuildZones` (static helper): `IsBuildable(World, Footprint)` reading the obstruction list (a data table built by a Python script from `world_layout`/`world_terrain`, like the other world data), so editor builds and the game agree.
- Persistence: pieces are saved with the world (server persists buildings per MULTIPLAYER_RULES).
- Performance: cap pieces per island (starting 2,000), instanced static meshes for cosmetic repeats where possible.

## Milestones (each separate, none claimed yet)
1. Zone data and `IsBuildable` with unit tests (Python mirror like `test_world_layout`) and a Play check that probes points on every island: buildable inland, refused at Ports, caves, beaches (if owner says), water.
2. Build component, ghost, place/demolish for one piece (foundation), controller and keyboard parity, Play check in single player.
3. Piece set (wall, door, roof, stairs, chest, campfire) with snapping.
4. Multiplayer: server validation, client prediction, persistence, claim-flag permission.
5. Art: pieces' meshes (six-view references per the project rule), region variants.

## Needs the owner
- Confirm the "zones carve out, rest is buildable" reading.
- Beaches buildable or not (docks need open shore).
- Piece list, costs, refund share, per-island cap (values above are placeholders).
- Interaction with claim flags in multiplayer (durations are already TBD).

## Milestone 1 result (October 27)
- `Scripts/Setup/world_buildzones.py` (the rule and 39 zones), `export_buildzones.py` writes `Content/Elitewake/Data/BuildZones.json`, `UEWBuildZones` (`Source/EW/World`) reads it: `CheckPoint`, `CheckFootprint` (middle, corners, edge middles, unevenness, something in the way). Empty result means buildable.
- Unit tests `BuildZoneTests` in `Scripts/Tests/test_world_layout.py`; Play check `Scripts/Verification/verify_build_zones_play.py` passes: zones loaded, game and layout agree at 387 of 400 sample points (the rest sit within the built ground's 1.5 m tolerance of a limit, mostly the dock-beach height and the Swamp waterline), every Port middle and waterfront and open water refused, every island has a place a 4 m footprint may be built.
- Not packaged: the JSON lives in Content but is not yet listed as a staged non-asset file; packaging needs that (milestone 4).
- Zone values (spawn 8 m, spring 12 m, dock 22 m rings, caves/landmarks margins) are tuning.
