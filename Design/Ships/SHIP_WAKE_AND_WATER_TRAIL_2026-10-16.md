# ELITEWAKE — Ship Wake and Water Trail

## Visual requirement
When a ship moves **forward** through ocean water, render a realistic, slightly foggy/foamy, turbulent wake trailing **approximately 20 meters** behind the vessel (the user's final correction from an initial 50-meter suggestion). Water should visibly part and curl around the bow and hull contours, then merge into a disturbed patch of current and foam behind the stern. The trail should reflect the ship's shape, direction, and movement, rather than appearing as a fixed rectangular cloud.

## Behavior
- Wake is emitted at the hull/water intersection, following the ship's path in world space, and gradually dissipates across a trailing distance of roughly 20 m.
- Scale wake width and intensity to hull size and vessel speed, including larger Brigantine and Cavalier hulls. Slow movement produces a subtle disturbance; faster movement creates a stronger wake, spray and foam.
- Stationary ships must not continuously generate a moving wake; existing foam should fade naturally after stopping. Handle turning and reversing plausibly.
- The 'foggy patch' is **water turbulence, foam, and mist/spray**, not opaque atmospheric fog; it should remain translucent and believable in sunlight and different weather.
- Keep effects performant (Niagara particles, foam decals/materials, water-surface interactions as appropriate for Unreal Engine 5.8), with LOD/distance culling and no unnecessary persistent simulation.
- Support both first- and third-person viewing, with ship movement and wake visually synchronized. Preserve existing sailing mechanics and modular sail attachments.

## Agent instructions
Claude, Codex, ChatGPT and relevant production assistants should inspect the existing ocean/water plugin, ship movement system, and VFX assets before implementation; reuse appropriate systems and test forward speed, turns, stop, multiplayer visibility if applicable, and the roughly 20 m fade-out. This is a committed design specification only; it does not claim Niagara or water effects have been implemented.
