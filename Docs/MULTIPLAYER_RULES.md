# Multiplayer rules

Owner decisions from October 14, 2026. Shared rules are in [the world structure decisions](WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md); existing network foundations remain in [PROJECT_GUIDE](PROJECT_GUIDE.md).

- Five regions are organized into regional grids. A sufficiently capable server may host all five regions. Inter-grid travel and the grid topology remain open.
- Players have no manual Save button. The server persists characters, ships, buildings and the fixed generated world.
- Hardware requirements follow measured workload: players, wildlife, world simulation and loaded regions. Optimize instead of adding artificial overhead.
- Company island claiming and contests exist only in multiplayer. NPC Port islands cannot be claimed or contested.

## Claim sequence

1. Place a Company's Claim Flag on an eligible island. Its flag rises during the claim timer.
2. A rival placing its flag next to that flag starts a separate contest timer.
3. When the contest period expires, the original flag disappears.
4. Only then does the rival's own claim timer begin. Contest time does not also complete the rival's claim.

Both timer durations and eligible proximity remain TBD. Multiple challengers, defender cancellation, original-timer pausing/resumption, offline behavior and abandonment have not been specified. These are design gaps, not authorization for invented balance values or production rules.

## Shared ocean encounters

Ghost ships are hostile groups of three scattered over the ocean, with neon-colored ship bodies and normal sails. Their types follow player-unlocked ships. Selection for a shared encounter involving players with different unlocks remains unresolved.

This file is a mode-specific design contract, not an assertion that island claims or server persistence are implemented. The current disabled Multiplayer menu preview is not changed merely by adding these documents.
