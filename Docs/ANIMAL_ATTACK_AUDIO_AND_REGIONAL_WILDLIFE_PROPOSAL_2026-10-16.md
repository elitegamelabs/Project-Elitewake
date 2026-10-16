# Animal bite, growl, and regional wildlife proposal — October 16, 2026

## Owner-requested animation and audio milestone (pending)
For every existing or future ELITEWAKE animal where anatomically and behaviorally applicable, implement:
- Distinct head/jaw biting animation with believable anticipation, contact, and recovery.
- Synchronized bite vocalization and contact/impact audio, with timing tied to actual animation events.
- Distinct growl/threat-display animation and species-appropriate growling/vocalization audio.
- Appropriate idle, locomotion, alert, attack, hit, and death transitions; no generic identical sound or motion across unrelated species.
- Correct server-authoritative hit windows, range, damage, cooldown, and multiplayer replication; animation/audio must not imply damage outside validated hits.
- For animals that do not bite or growl, use species-correct attack/defensive motions and calls instead. Do not force growls on birds, fish, or herbivores.
- Test animation synchronization, sound spatialization, behavior and performance in Unreal Play, including multiplayer.

## Proposed regional animal roster — suggestions awaiting owner approval
Retain the five-region world assignment: Central Plains, Northern Winter, Southern Swamp, Eastern Desert, Western Jungle. Preserve all previously approved animals and ecology. These are *suggestions*, not confirmed additions or completed assets.

| Region | Suggested wildlife | Behavioral/audio notes |
| --- | --- | --- |
| Central Plains / starter | Deer, rabbits, foxes, wolves, wild boar, owls | Deer/rabbits flee; foxes and wolves bite/growl when threatened; boars charge and grunt. Keep starter shore approachable. |
| Northern Winter | Elk, snowshoe hares, wolves, lynx, bears, snowy owls | Wolves/bears/lynx bite and vocalize; elk charge; snow muffles footsteps, not vocalizations. |
| Southern Swamp | Alligators, wild boar, frogs, herons, snakes, turtles | Alligators bite and hiss/bellow; snakes strike and hiss; frogs/herons have their own calls. |
| Eastern Desert | Camels, fennec foxes, jackals, lizards, scorpions, snakes | Jackals bite/growl; snakes strike/hiss; scorpions sting, not bite as primary attack. |
| Western Jungle | Jaguars, monkeys, tapirs, parrots, giant spiders, snakes | Jaguars bite/snarl; monkeys call; spiders bite/hiss only if species design supports it. |

## Acceptance criteria / milestones
1. Audit approved existing animal roster and preserve species and biome assignments.
2. Create per-species bite/growl applicability matrix and animation/audio asset checklist.
3. Implement and verify synchronized bite animation, bite sound, threat animation and vocalization for applicable species.
4. Implement species-correct alternatives for animals without bite/growl behaviors.
5. Review proposed regional additions with owner before treating them as canon.
6. Verify placement, AI, multiplayer hit timing, spatial audio, animation quality and frame-rate in Unreal Play.

Status: **requirements documented; implementation and Unreal verification pending**.
