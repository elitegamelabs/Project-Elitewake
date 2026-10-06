# M2 collision and clearance — 2026-10-05

Active project: `C:\UnrealProjects\EW`, Unreal 5.8.3. This continues the [stance animation pass](M2_STANCE_VERIFICATION.md) under the owner's request to finish M2 collision/clearance. M5D remains pending.

## Accepted behavior

`UEWCharacterMovementComponent` checks clearance before changing the accepted stance. Standing uses the active Blueprint's 90 cm capsule half height; crouch uses 60 cm. Prone uses a 28 cm radius/half-height root sphere and a horizontal capsule query with 28 cm radius and 105 cm half length. Its body query has a 2 cm floor skin and follows the supporting floor normal. These are implementation tuning values, not new Bible rules or character scaling.

- Low ceilings block crouch-to-stand, prone-to-crouch, and prone sprint/jump exits. Rejection preserves the existing collider, animation stance and speed. Removing an obstacle permits a new exit request.
- Prone entry checks the space around the body, including obstacles outside the standing root capsule. Swept movement checks the body; intermediate orientations check turn clearance. Prone stepping is disabled so crawling cannot use a standing step-up to bypass an obstacle.
- Capsule resizing preserves its bottom and updates the mesh's normal crouch offsets. Standing radius is restored when leaving prone. The first-person eye targets remain 40 cm above the capsule bottom in prone and 96 cm in crouch.
- Prone intent travels in CharacterMovement saved moves/compressed flags rather than a separate prone RPC. Sprint-held intent accompanies stance movement so the server accepts sprint after a successful exit. Jump clearance resolves before jump processing on the owner and server; a one-frame jump press no longer gets consumed by deferred uncrouching.
- Simulated proxies follow replicated accepted stance rather than applying absent local input intent. Their collision size updates when the host changes between prone, crouch and standing.
- Airborne prone entry is rejected. An already-prone character retains its collider while falling rather than expanding it midair.

## Verification

- EWEditor Win64 Development build succeeded on 5.8.3.
- All four automation tests passed: `Elitewake.Animation.StanceBlendSpaces`, `Elitewake.Inventory.PersistedTestItem`, `Elitewake.Inventory.StackingAndWeight`, and `Elitewake.Movement.StanceCollision`. The new test checks real blocking geometry, stance sizes, preserved capsule bottom, body movement/turn clearance, airborne entry, movement flags, and prone entry/sweep on a 10-degree inclined surface. Log: `Saved/Logs/M2CollisionRegression.log`.
- `Scripts/verify_stance_play.py` passes eight animation/camera checkpoints in a temporary clear area: crouch 300 cm/s, crawl 150 cm/s, unit mesh scale, aligned animation roots, both return transitions and prone eye target 40 cm. `Saved/M2StancePlayResult.json` records success.
- `Scripts/verify_stance_clearance_play.py` passes sixteen single-player checkpoints, including blocked rises, blocked prone entry, crawling under a 65 cm roof, body stopping at a wall, turn rejection, open crawl, sprint exit, prone jump and landing. `Saved/M2ClearancePlayResult.json` records success.
- The same obstacle course passes from a client with **100 ms outgoing packet lag and 1% packet loss on both PIE drivers**. Client and authoritative host agree on accepted stance/collider at all sixteen checkpoints. This is configured packet emulation, not a measured internet round-trip time. `Saved/M2ClearanceNetworkResult.json` records success.
- `Scripts/verify_stance_network_play.py` passes eleven client/host checkpoints, including client sprint exit and host stance changes observed by a simulated proxy. Stance/collider/animation flags agree; settled animation roots remain 1 cm above their capsule bottoms in both representations. `Saved/M2StanceNetworkResult.json` records success.

The fixtures exist only in Play worlds; scripts release injected input, remove fixtures, unregister callbacks and restore throttling/network settings. Generated logs/results stay under ignored `Saved`. Earlier failures remain as diagnostic history; only the final successful runs establish acceptance. The animation-only speed route was moved to clear space after the new body guard correctly encountered an obstacle in the template map.

## Scope and remaining work

The collision/clearance foundation is verified for the fixtures above. The horizontal body query is a movement-clearance approximation, not skeletal damage hitboxes. Other actors are tested against their existing blocking geometry. Teleports/network corrections use normal engine placement; the body guard applies to swept locomotion and turning.

Physical controller B testing, authored transition polish and terrain-aligned animation remain open. The slope check is one planar 10-degree fixture; complex terrain edges, moving ship decks, dedicated servers, broader latency/loss conditions, performance and packaging are not established by this pass. No full-game or finished-M2-presentation claim is made.
