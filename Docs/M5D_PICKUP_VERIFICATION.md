# M5D pickup verification

Verified 2026-10-05 in `C:\UnrealProjects\EW`, Unreal 5.8.3. Slice commit: `Implement M5D authoritative world pickups`.

## Behavior

`EWPickup.*` supplies a replicated world stack and Blueprint-configurable mesh/item/quantity. `EWPlayerController.*` binds the Enhanced Input interaction draft to E and controller X. An assigned designer action replaces the runtime fallback and needs a mapping in the controller's mapping contexts. Interaction is suppressed locally while inventory is open.

The owned player controller sends a target actor only. The server uses its possessed character's eye position/control rotation to trace 250 cm on Visibility, and verifies the same target, world, possession, authority, usable item/quantity and any assigned pickup owner. Walls and looking away block interaction. Public pickups have no owner; an assigned owner must be the collecting character or its controller. This is a pickup access check, not a general ownership/tribe system.

Inventory accepts only what fits its slots/stacks. The world quantity decreases by that accepted count, remains when capacity is insufficient, and destroys the actor only when exhausted. Server operations run serially; a transfer guard also rejects reentrant attempts during inventory change notifications. Clients cannot supply item definitions, quantities or receiving inventories through the interaction RPC.

E and 250 cm are draft tuning, not newly confirmed Bible rules. Controller X follows the authoritative Bible. Preserve zero starting currency and the later rye-sale mission; this slice adds no currency or prologue behavior.

## Evidence

- EWEditor Win64 Development build succeeded, including the editor-only fixture helper.
- `Saved/Logs/M5DRegression.log`: all five tests Success: StanceBlendSpaces, PersistedTestItem, PickupValidation, StackingAndWeight, StanceCollision.
- PickupValidation checks possession, distance, aim, occlusion, foreign ownership, partial/full capacity, exhaustion, repeated intent and count conservation using real collision queries.
- `Saved/M5DPickupPlayResult.json`: five checkpoints pass through the real Enhanced Input action binding in fresh single-player Play.
- `Saved/M5DPickupNetworkResult.json`: five checkpoints pass in listen-server/client Play with 100 ms outgoing lag and 1% loss on both drivers. Both local players send overlapping pickup intents; the original 10 units transfer exactly once. Each inventory with three free units receives three from a later stack, leaving four replicated units. Full inventories preserve that remainder; freeing capacity collects it once. Inventory quantities and world remainders agree in both worlds.
- `Saved/M5DPickupInventory.png`: actual Slate E key collects the placed Blueprint's 10 Wood (Test); I displays Slots 1/24, Wood x10, weight 1.0 kg. Normal Play begins empty before collection.
- `BP_TestWoodPickup` and `Lvl_M5PickupTest` are saved under `/Game/Elitewake/Blueprints` and `/Game/Elitewake/Maps`. The original startup map is unchanged. The map reloads and the placed actor enters Play with the saved item and quantity 10. Face forward from PlayerStart, press E, then I to inspect the inventory.

`Scripts/create_pickup_test_content.py` creates/reconciles only the named fixture content. `Scripts/verify_pickup_play.py` requires that test map in fresh single-player or in-process listen-server/client Play. It clears PIE test inventory, creates temporary stacks, restores packet/throttle settings, removes its callbacks and fixtures on success/failure/Play exit. Stop Play afterward; no inventory is saved. The spawn helper belongs to EWEditor and is not available in game targets. Earlier failed Python spawning/path/content probes are diagnostic only, superseded by the successful records above.

## Boundaries

This is the M5D pickup foundation, not a complete interaction framework for stations, gathering, vendors, loot permissions, ships or hold actions. The eye/control-rotation ray is the accepted aiming convention for this slice; third-person camera-parallax polish, reticle/prompts/feedback and inventory selection follow in presentation work. Controller X is mapped but physical controller testing remains open. Wood's cube and 0.1 kg weight are fixtures. Slot capacity, not a hard weight cap, limits transfer. Dedicated server, packaging, persistence, death drops, moving ships, broader latency/load tests and complete multiplayer inventory UI are not verified.
