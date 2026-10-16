# ELITEWAKE — Directional ship displacement waves

Owner requirement — October 16, 2026.

For every navigable ship, render convincing water displaced outward from beneath and alongside the hull in **all three movement cases**:

1. **Forward travel:** water parts at the bow, with outward-moving bow waves, side wash and foam along the hull; blend into the previously specified wake extending approximately 20 meters behind the vessel.
2. **Reverse / docking:** when backing up, generate directional displacement and ripples at the stern and along the hull, with foam and waves pushed outward consistent with reverse speed. Keep the effect controlled and believable at low docking speeds.
3. **Turning:** when steering port or starboard, produce asymmetric outward water displacement and swirling wash along the hull, especially on the outside of the turn, while retaining bow/stern effects appropriate to actual velocity. The visual direction must follow the ship's motion, not simply play a fixed forward effect.

## Implementation guidance for Claude, Codex and other agents
- First inspect current ship movement, existing water material, Niagara systems, hull dimensions, wake implementation, and recent GitHub commits/PRs. Reuse existing systems rather than duplicating or replacing them.
- Prefer Niagara particles plus water-material interaction, foam, ripples and hull-following emitters. Effects should scale with vessel size, speed, acceleration and turning rate; avoid excessive particles and abrupt popping.
- No strong motion effects while stationary; blend smoothly when stopping, changing direction or leaving the helm. Keep effects visible in first- and third-person views where appropriate.
- Preserve the existing ~20-meter trailing wake, wind-responsive sails, helm controls and propulsion behavior. These are complementary effects, not replacements.
- Verify forward, reverse, left turn, right turn, low-speed docking, stationary, and forward-to-reverse transitions in Unreal Engine 5.8; check performance and multiplayer synchronization if applicable.
- Documentation does not mean the effect is implemented. Report code/asset changes and in-engine test evidence separately.
