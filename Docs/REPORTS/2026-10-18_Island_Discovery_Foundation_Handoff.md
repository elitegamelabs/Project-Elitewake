# Island discovery foundation handoff — October 18, 2026

**Status:** code committed on isolated branch; Unreal integration and verification pending.

Added:
- `Scripts/Setup/island_discovery.py`: all 26 approved region-specific names keyed by stable world IDs; per-player first-discovery state; map-label privacy; save/restore; world-key validation; 5-second announcement constant.
- `Scripts/Verification/test_island_discovery.py`: unit tests for 26 keys, uniqueness, one-time triggers, per-player independence, persistence, invalid keys.

**No existing Claude-owned file changed.** Do not mistake these pure-Python foundations for functioning Unreal gameplay. Integrator must:
1. Validate catalogue against `world_layout.ISLANDS` in generation/packaging.
2. Port catalogue and per-player state into authoritative Unreal 5.8.3 server/player save components; do not rely on shared global discovery state.
3. Trigger once at island land/shore volumes; queue centered announcement for 5 seconds then fade.
4. Add discovered-only labels to map UI; avoid leaking names to undiscovered players.
5. Add native and Play tests for save/reconnect, multiple players, all regions, spawn and map.
6. Respect latest global one-server 100-player decision and existing single-player save behavior.

**Verification:** reviewed current main and source/owner docs and open PR #1. Unit tests included but not executed here; no Unreal editor access or Play verification. Do not merge until tests and integration are reviewed.

**Claude coordination:** This is a separate ChatGPT-owned branch and draft PR; it does not alter `main`, ship source, world layout, or map widget.
