# Single-player rules

Owner decisions from October 14, 2026. Shared geography, resources, growth-stage art and traversal requirements are in [the world structure decisions](WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md); general systems remain in [DESIGN_REFERENCE](DESIGN_REFERENCE.md).

- All five neighboring regions are accessible within the single-player world: Desert, Winter, Jungle, Plains and Swamp.
- Generated island shapes and feature placements remain fixed for that saved world.
- Normal single-player saving is retained.
- No island claiming, Claim Flags, contests or company ownership requirement to build. The owner wants to build anywhere; claim permission must not block construction.
- Optimize single-player performance and load only what the simulation needs. No artificially inflated resource requirements.
- Shared resource, planting, climate, collision and traversal rules still apply. Building without claims does not authorize placing geometry inside solid terrain.

This file records intended behavior, not proof that world generation, farming or climate are already implemented. NPC Port claim exclusion belongs to multiplayer; single-player building permissions around NPC structures require specific placement implementation rather than silently importing multiplayer ownership gates.
