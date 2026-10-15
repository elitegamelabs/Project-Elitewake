# ELITEWAKE Map Zoom, Player Location, and World Overview Requirements

**Status:** Owner-requested design requirements  
**Date:** 2026-10-15

## Map zoom controls
- Keyboard and mouse: use the mouse scroll wheel to zoom in and out.
- Xbox-style controller: RT zooms in and LT zooms out while the map is open.
- Keep zoom transitions smooth and responsive.
- Avoid conflicting with gameplay weapon inputs while the map is closed; map input context must be active only when appropriate.

## Maximum zoom-out: world overview
- At maximum zoom-out, fit every island in the world within a square map view.
- Preserve geographic relationships and readable spacing; do not present islands as unrelated menu icons.
- Reflect the planned world layout: Winter north, Swamp south, Desert east, Jungle west, and Plains in the center.
- The starter island belongs to the central Plains region, with at least five nearby islands around it.
- Preserve the minimum of five islands per region (at least 25 across the five regions), with more allowed if useful to exploration.
- Add subtle animated ocean/wave motion around the islands, but keep island outlines, labels, and player indicators legible.

## Zoomed-in map: current area and player position
- As the player zooms in, show the currently relevant/local area with more detail.
- Clearly indicate the player's current position on the map, using a distinct, consistently styled player marker.
- Keep the marker accurately synchronized with the player's world position as they move.
- Orient and frame the local view so the player can understand where they are relative to nearby coastlines, islands, landmarks, and discovered locations.
- Transition smoothly between the local view and the full-world overview without losing the player's geographic context.
- Do not imply unexplored terrain or undiscovered locations have been revealed; follow the game's exploration/fog-of-war rules if present.

## Implementation and validation
- Use Unreal Engine Enhanced Input and respect the project's input-device prompt conventions.
- Opening the map must not pause gameplay, consistent with existing development requirements.
- Test mouse-wheel zoom and controller RT/LT zoom, minimum and maximum zoom limits, marker accuracy while moving, readability at each scale, and the complete-world square overview.
- This document defines design intent; it does not claim that the map UI or behavior has already been implemented or tested.
