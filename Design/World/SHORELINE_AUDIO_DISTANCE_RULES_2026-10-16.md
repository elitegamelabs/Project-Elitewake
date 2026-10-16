# Shoreline ocean audio — ELITEWAKE

Owner requirement (October 16, 2026): Keep ocean surf loud at the beach as it currently is. As the player travels inland, fade the ocean surf down smoothly until it becomes inaudible. Moving back toward the beach gradually restores the existing loud surf sound.

Claude and Codex implementation instructions:
- Inspect existing Unreal Engine 5.8 audio assets, sound attenuation, island geometry, and current ocean ambience before making changes.
- Attenuate based on distance to the nearest relevant shoreline rather than distance to the center of an ocean actor. Support irregular island coastlines and all regions.
- Expose configurable fade start/end distances and a smooth curve; determine values through playtesting instead of assuming arbitrary distances.
- Preserve existing near-shore volume and wave character. Avoid sudden cuts, audio restarts, and surf that remains audible far inland.
- Ensure swimming, ships, and first- and third-person audio continue to work. Test beach, inland, and return-to-beach transitions on different islands.
- Record implementation and in-engine test results separately from this design document.

Related anchor deployment chain sound requirement: Design/Ships/ANCHOR_CHAIN_ANIMATION_AUDIO_2026-10-16.md.

## Confirmed shoreline fade distance (owner clarification)
- Ocean surf must be completely inaudible once the player is **20 meters inland from the nearest shoreline** on an island. Measure the horizontal inland distance to the coastline, not distance to the island center or ocean actor.
- At the coastline/beach, preserve the existing loud wave volume. Fade smoothly from the coast toward zero at 20 m; clamp to silence at 20 m and beyond. The exact shape of the fade curve may be tuned, but **the 20-meter cutoff is a firm requirement**.
- Returning within 20 m of the shoreline smoothly restores surf volume. Validate with Unreal Engine world units (20 m = 2,000 cm), including coves and irregular coastlines.
