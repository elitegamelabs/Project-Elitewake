# ELITEWAKE — Wind-reactive sail animation

## Desired behavior
When a mounted ship's sail orientation is aligned to catch the wind, the fabric should **fill and billow outward ('poof out')**, with a convincing curved, tensioned profile and subtle flutter. When sails are not catching the wind, they should **go slack** and hang loosely but **continue to wave/flap gently**, rather than becoming rigid or motionless.

## Wind and sail state
- Derive sail fill from the relative angle between world wind direction and the sail's facing/normal, taking account of sail geometry and whether the wind is striking the useful side of the sail. Do not assume that sailing directly into the wind fills sails; distinguish sail facing from ship heading.
- Blend continuously between slack, partly filled and fully billowed states as the player rotates the modular sail attachments using helm-only left/right arrow or LB/RB controls.
- Animate soft, speed- and gust-responsive cloth motion; filled sails have tension and shape, slack sails sag and ripple. Avoid abrupt pops or excessive clipping through mast, boom or rigging.
- Keep mast/pole and flag attachments aligned with their modular assembly; flags may flutter separately.
- One consistent world wind vector drives all ships and wind-reactive visuals, with optional coherent gust variation. Wind is independent of the previously specified single global sun direction.
- Preserve existing ship models, hull-without-sails architecture, steering controls and 20-meter wake requirements. Use performant Unreal Engine 5.8 cloth, skeletal blendshapes or material deformation according to the project's existing setup; apply appropriate LODs.
- Test stopped and moving vessels, sail rotation through its 180-degree range, wind shifts, multiple ship sizes, and first/third-person camera views.

## Status
This document is an instruction for Claude, Codex, ChatGPT and relevant production agents. It does **not** mean sail cloth animation or wind logic has been built or tested.
