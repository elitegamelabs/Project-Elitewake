# Owner-approved elephant obstacle interactions, wildlife roaming and spiders — 2026-10-16

## New pending milestones
1. **Tropical elephants knock down obstacles:** Elephants roaming the Western Jungle / tropical islands can push over trees and movable or destructible obstacles that obstruct their path. Use physical contact, believable force, trunk/head/body pushing animation, cracking/impact/foliage sounds, and a visible falling or displaced obstacle. Classify obstacles by destructibility; do not destroy terrain, quest-critical structures, ports, player-built protected objects, or indestructible geometry. Ensure network-authoritative physics and avoid excessive simulation cost. Decide with owner whether felled trees become harvestable resources and whether they regrow.
2. **Island wildlife roaming:** All animals should naturally wander within suitable habitat on their assigned islands rather than remain static at spawn points. Implement roaming, idle, grazing/foraging, resting, alert and fleeing or attacking where appropriate, with collision-aware navigation, no unintended ocean wandering, species-specific speed, animation and spatialized audio. Preserve existing wildlife sleep/performance optimizations at distance and multiplayer authority.
3. **Spiders in every cave:** Populate each cave across all five regions with spiders, with navigable cave placement and appropriate density, collision, pathfinding, and server-authoritative combat where applicable. Verify caves are not empty after world regeneration.
4. **Spiders on Southern Swamp islands:** Add spiders in appropriate swamp terrain outside caves, with natural distribution and movement.
5. **Complete spider animation/audio:** Implement spider idle, leg movement, walking, turning, climbing where supported, alert, attack/bite, hit, death, and web interactions where applicable; synchronize attack sounds, footsteps/scuttling, hissing/chittering where appropriate, web movement/tearing, and bite/impact audio. Do not claim spiders literally growl unless specifically designed as fantasy creatures.
6. **Verification:** Unreal Play tests for elephant collision/knockdown, persistent obstruction state and replication, animal roaming and island bounds, spider presence in every cave and swamp, animation/audio sync, AI pathfinding and performance.

## Existing canon preserved
Elephants belong to Western Jungle tropical islands, lions to Central Plains, bears to Northern Winter, giant crocodiles to Southern Swamp. Preserve all other previously approved fauna and the owner's earlier requirement for bite/growl animations and sounds where species-appropriate.

**Status:** Owner requirements documented, Unreal implementation and Play verification pending.
