# Wind-driven sail propulsion — ELITEWAKE

Implementation requirement for Claude, Codex, and other game agents (Unreal Engine 5.8):

- When a player mounts a ship helm, allow sail rotation using the previously specified left/right controls, including controller LB/RB; do not rotate sails through these controls when unmounted.
- Calculate propulsion from the relative angle between world wind direction and each sail's orientation, using the existing sailing movement system. As sails are trimmed into an effective wind-catching angle, increase forward propulsive force and let the vessel accelerate smoothly toward a higher speed, subject to hull-specific speed limits and drag. Misaligned sails produce less propulsion; avoid instantaneous speed changes.
- Coordinate sail visuals with physics: wind-filled sails billow when producing strong propulsion; slack sails ripple gently with low propulsion. Account for wind strength and ship heading; do not assume every ship heading can sail directly into the wind.
- Keep the world wind direction consistent across islands, with natural strength variation, and preserve existing helm controls, modular sail attachments, and the approximately 20-meter foamy ship wake, scaling wake intensity with speed.
- Apply to all ships including Brigantine and Cavalier, tuning acceleration and maximum speed by hull class. Preserve existing assets and test helm-only input, acceleration, speed cap, heading changes, sail animations, and multiplayer replication if applicable.

Status: design requirement only; Unreal implementation and tests remain pending.
