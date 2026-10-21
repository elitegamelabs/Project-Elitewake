# ELITEWAKE — five-island-first recovery plan (owner decision, 2026-10-21)

## Decision
The **immediate playable world contains exactly five islands, one per region**:
1. **Plains:** existing starter island; preserve beach spawn, dock, pond, sloop, safe-area rules, and its stable identifier.
2. **Winter:** one existing Winter island (exact island key **TBD — owner approval after audit**).
3. **Swamp:** one existing Swamp island (exact key **TBD**).
4. **Desert:** one existing Desert island (exact key **TBD**).
5. **Jungle:** one existing Jungle island (exact key **TBD**).

This **supersedes** the earlier 40-island active target (8 per region), and the old 26-island world as a first-playable requirement. The existing 26 and 40 records, tests, assets, layouts, and history are **preserved for possible later expansion**. No blanket removal or irreversible rollback is authorized. Any earlier text saying “owner-approved 40 islands” is historical until the owner reauthorizes expansion.

**Do not confuse target with current implementation:** current `Scripts/Setup/world_layout.py` still generates 40 records, and the saved Unreal coastal map may reflect an earlier rebuild. This PR updates planning and coordination only; it does not change game runtime, map, asset files, or save data.

## Required transition (separate implementation PR)
1. **Audit (Codex):** enumerate original island keys, positions, Port locations, cave/terrain/wildlife assignments, setup builders, map/discovery persistence, multiplayer replication, ocean/nav boundaries, and existing saved-world assumptions. Propose four exact non-starter island keys and identify how one Port per region can coexist with those choices. Do not assume the original Port islands are best without owner review.
2. **Owner selection:** approve the exact five keys, Port treatment, placement and distances, and whether existing saves must load old world versions or remain in a legacy mode. Until decided, preserve all legacy keys and their stable IDs.
3. **Reversible source implementation (Codex):** add a named **five-island playable profile** that filters active generation without mutating or renumbering the historical 26/40 records. Ensure all consumers agree: terrain, ocean, caves, Ports, wildlife, maps/discovery, spawn, persistence, multiplayer, and tests. Make full-world generation explicitly legacy/optional; never silently drop records from saved games.
4. **Asset/map integration (Claude):** after safe backup and exclusive editor slot, generate and save a five-island Unreal map or separately versioned asset. Never destructively overwrite the sole saved coastal map. Run native and two-player Play checks including startup, sailing between regions, shore access, wildlife safety, caves, Ports, discovery, save/load, and performance.
5. **Gate:** mark the five-island milestone DONE only when saved Unreal assets and gameplay acceptance pass. Future additions are one reviewed increment at a time, not an automatic return to 40.

## Acceptance criteria
- Exactly 5 playable islands, exactly one for each region.
- Starter's approved spawn, dock, pond, safe zone, and sloop preserved.
- Stable IDs, no accidental remapping of original islands or player discovery.
- Each selected island's terrain, cave, wildlife and Port behavior explicitly checked; no false assumption that 40-island spawn totals apply.
- Ocean, navigation, ship travel, and multiplayer client replication verified in Unreal.
- Saved-map versioning and legacy-save behavior documented and tested.
- Offline tests + Unreal build + native tests + two-player Play check + visual inspection reported separately.
- No irreversible asset deletion or unapproved world-scale/design change.

## Existing task disposition
- **C-WORLD40:** PAUSED, historical code retained.
- **C-WILDLIFE40:** PAUSED, historical code retained.
- **PR #5 (26-island discovery foundation):** do not merge as-is; review against five-island ID/persistence requirements and resolve its non-mergeable state in a separate PR.
- **C1 felled trees:** PARTIAL; runtime checks still pending, unrelated to world count.
- **Brigantine:** inspect latest local and committed assets before continuing; do not infer completion from a task claim.

## Important open owner decisions
- Which four existing non-starter island keys are selected?
- Should each region's current Port island be prioritized as its one playable island, and how does this affect starter-region Port access?
- What should happen to saves made against 26/40-island worlds?
- Are island positions/spacing kept exactly, or should the five-island first playable be more compact? **Do not change distances without approval.**
