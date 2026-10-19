# ELITEWAKE — Owner-approved 40-island wildlife distribution (2026-10-18)

Status: **OWNER APPROVED DESIGN DIRECTION; NOT IMPLEMENTED OR VERIFIED IN PLAY**.
Owner explicitly approved the 40-island distribution discussed on October 18 and requested it in the repository. This document is an additive placement specification, **not** a replacement for existing creature spawn points or behaviors.

## Authoritative world layout
Source: `Scripts/Setup/world_layout.py` (read October 18, 2026).
**Owner revision October 18:** eight islands in EACH of five regions: Plains = Starter + Plains2–Plains8; Winter1–8; Swamp1–8; Desert1–8; Jungle1–8. **40 islands total.** This is the requested target; the procedural world generator and gameplay must be migrated and verified separately. Existing island IDs/placements must remain intact.
These are code island keys; do not invent player-facing names. The current implementation uses Plains / Winter / Swamp / Desert / Jungle, NOT an assumed volcanic region.

## Preservation / precedence rules
1. **Audit current spawn data first**: preserve all existing owner-placed animals, spawn transforms, habitats, tame foods, temperament, levels, saddle/riding and combat rules. An item in the proposed additions below never authorizes moving/deleting an existing spawn.
2. For each island, **union** proposed additions with existing species, only when matching actual terrain, habitat, cave, and safety constraints. Do not treat table as an exhaustive replacement list.
3. Keep Port pads and protected starter beach/dock/spawn free of aggressive wild spawns. Use `near_port` world-layout helper where appropriate.
4. Never silently rename taming foods: Monkey—Azul Berries, Warthog—Mary-Dash Berries, Manatee—Mary-Dash Berries. House Cat—Bass, village wildlife; Horse, Black Bear and other TBD taming food remains TBD.
5. Giant Spider: cave species in **all five regions** wherever caves exist; wild spiders aggro on approach, do not jump; saddled/tamed spiders may jump up to 15 m and climb walls/ceilings. Existing level 1–70 rule stands.
6. Sirens aggressive, never tameable, level 45–50. Manta rays aggressive and sting. Bass/Catfish freshwater ponds/lakes only; Piranha aggressive freshwater; Manatee passive warm-water. Preserve existing raft/diver protections and aquatic aggro rules.
7. Scale additions to available island habitat and server budget; exact spawn counts, cooldowns, coordinates, level bands not established by this document. Keep existing levels.
8. Do not create species solely from this plan without reconciling actual creature registry and source design authority. Some species are recommendations from design documents rather than verified game assets.

## Proposed additions by island
These are candidate **additional populations**; existing populations remain regardless of whether listed.

| Island key | Additional wildlife candidates | Preferred habitats |
|---|---|---|
| Starter | Deer, Rabbit, Fox, Eagle, Bass, Catfish | Inland meadow, woodland, cliff; Bass/Catfish only in freshwater pond |
| Plains2 | Deer, Elk, Horse, Wolf, Fox | Grasslands and woodland |
| Plains3 | Wild Boar, Deer, Rabbit, Raccoon, Eagle | Woodland, rocky hills |
| Plains4 | Horse, Elk, Wolf, Black Bear | Valleys, wooded hills |
| Plains5 | Deer, Fox, Wild Boar, Rabbit, Eagle | Mixed forest, coastal grassland |
| Plains6 | Elk, Horse, Wolf, Grizzly Bear | Remote forest and hills |
| Plains7 | Deer, Elk, Fox, Eagle | Meadows, upland woodland |
| Plains8 | Horse, Wild Boar, Wolf, Raccoon | Grassland, distant woods |
| Winter1 | Black Bear, Reindeer, Arctic Hare, Arctic Fox | Snow forest, valleys |
| Winter2 | Wolf, Elk, Moose, Black Bear | Boreal forest, wet valleys |
| Winter3 | Snow Leopard, Mountain Goat, Eagle, Arctic Fox | Mountain slopes, cliffs |
| Winter4 | Grizzly Bear, Wolf, Reindeer, Moose | Forest, lakes, valleys |
| Winter5 | Snow Leopard, Mountain Goat, Wolf, Grizzly Bear | Remote alpine terrain |
| Winter6 | Reindeer, Arctic Hare, Arctic Fox, Eagle | Snow valleys, cliffs |
| Winter7 | Moose, Black Bear, Wolf, Elk | Boreal woods, lakes |
| Winter8 | Snow Leopard, Mountain Goat, Grizzly Bear | High alpine cliffs, remote valleys |
| Swamp1 | Capybara, Beaver, Otter, Bullfrog, Heron | Shallows, riverbanks |
| Swamp2 | American Alligator, Water Buffalo, Wild Boar, Raccoon | Freshwater marsh, flooded forest |
| Swamp3 | Crocodile, Python, Cottonmouth, Heron | River, estuary, mangrove |
| Swamp4 | Water Buffalo, Capybara, Otter, Beaver, American Alligator | Freshwater wetland |
| Swamp5 | Crocodile, American Alligator, Python, Cottonmouth, Wild Boar | Dense wetland; species segregated by suitable water habitat |
| Swamp6 | Capybara, Otter, Heron, Bullfrog | Shallow channels, marsh |
| Swamp7 | Water Buffalo, Wild Boar, American Alligator, Raccoon | Flooded woodland, freshwater |
| Swamp8 | Crocodile, Python, Cottonmouth, Beaver | Estuaries, dense marsh, riverbank |
| Desert1 | Monkey, Gazelle, Desert Tortoise, Eagle | Oasis, rocky scrub |
| Desert2 | Elephant, Rhino, Warthog, Ostrich | Open plains, waterholes |
| Desert3 | Camel, Gazelle, Jackal, Desert Tortoise | Dunes, dry grassland |
| Desert4 | Monkey, Warthog, Hyena, Jackal | Badlands, oasis edge |
| Desert5 | Elephant, Rhino, Camel, Ostrich, Hyena | Remote plains |
| Desert6 | Monkey, Gazelle, Eagle, Desert Tortoise | Oasis and rocky slopes |
| Desert7 | Camel, Ostrich, Jackal, Warthog | Dry plains, watering holes |
| Desert8 | Elephant, Rhino, Hyena, Gazelle | Remote savanna-like desert plains |
| Jungle1 | Horse, Tapir, Parrot, Toucan, Iguana | Clearings, canopy |
| Jungle2 | Gorilla, Jaguar, Tapir, Parrot | Dense forest |
| Jungle3 | Tiger, Wild Boar, Iguana, Giant Tortoise | Understory, clearings |
| Jungle4 | Lion, Horse, Gorilla, Toucan | Open tropical woodland |
| Jungle5 | Tiger, Jaguar, Gorilla, Wild Boar, Giant Tortoise | Remote jungle |
| Jungle6 | Tapir, Iguana, Parrot, Toucan | Humid forest, canopy |
| Jungle7 | Gorilla, Jaguar, Wild Boar, Giant Tortoise | Dense jungle, clearings |
| Jungle8 | Tiger, Horse, Lion, Parrot | Separate dense forest and open woodland habitats |

**Cross-island cave overlay:** Giant Spider on Starter, Plains2–8, Winter1–8, Swamp1–8, Desert1–8, Jungle1–8 **only where appropriate caves exist**; preserve any existing cave spawns.

**Freshwater overlay:** Bass and Catfish only in actual freshwater ponds/lakes; Piranha in appropriate warmer freshwater, never in saltwater. No automatic fish spawn on islands lacking those waters.

**Saltwater overlay:** Manatee in warm sheltered coastal water; Manta Ray warm coast/offshore; Reef Shark at reefs (including owner's deep-ocean coral reef plan); Great White Shark, Hammerhead Shark, Squid and Siren in appropriate offshore/open-ocean zones. Water habitats are **world/ocean zones**, not arbitrary island-land spawns.

**Village overlay:** House Cat only in villages where appropriate; preserve existing village placements.

## Roster reconciliation required before gameplay implementation
Owner estimates approximately 60 animals. The October 7 ecology guide documents Northern: Black Bear, Grizzly Bear, Snow Leopard, Elk, Moose, Reindeer, Arctic Hare, Arctic Fox, Wolf, Mountain Goat, Eagle; Desert: Monkey, Rhino, Elephant, Warthog, Camel, Gazelle, Ostrich, Jackal, Hyena, Desert Tortoise, Eagle; Swamp: American Alligator, Crocodile, Wild Boar, Water Buffalo, Capybara, Beaver, Otter, Raccoon, Python, Cottonmouth, Bullfrog, Heron, Giant Spider; Jungle: Tiger, Lion, Gorilla, Horse, Wild Boar, Tapir, Jaguar, Parrot, Toucan, Iguana, Giant Tortoise. Other canon includes House Cat, Bass, Catfish, Piranha, Manatee, Manta Ray, Great White Shark, Hammerhead Shark, Reef Shark, Squid, Siren, plus possible other creatures in the actual repo. **These lists are not proof of a complete ~60-creature registry**. Deer/Rabbit/Fox on Plains are proposed additions from the approved spoken table; check existing creature registry before implementation.

## Migration caution
This October 18 owner revision expands the approved **design** to 40 islands; existing world generator still requires an additive 26-to-40 migration. Preserve coordinates, silhouettes, ports, current island keys and all placed wildlife for the original 26; simply changing the random generator counts may reshuffle existing islands. Build and verify an append-only island expansion, then update procedural generation, navigation, discovery/milestones, maps, save compatibility, and spawn data.

## Implementation acceptance checklist (not yet completed)
- Enumerate current actual creature classes/data assets and all current island spawn placements; save baseline.
- Reconcile every creature against existing rules and this owner-approved table; flag ambiguous names and missing species without silently creating replacements.
- Add data-driven island and water-biome spawn rules **additively**; no relocation of existing spawn points.
- Verify safety areas, predator density, aquatic habitat correctness, cave spawning, taming and rider behavior.
- Run automated and Unreal 5.8.3 Play verification, including multiplayer where possible, and record results in `Docs/VERIFICATION.md`.
- Report implementation claim/completion and unresolved issues in `Docs/Delegation/INBOX.md`.

Source of approved table: owner voice conversation, October 18, 2026; source of island keys: current `Scripts/Setup/world_layout.py`; source of animal ecology: ELITEWAKE World Resource & Ecology Guide v2 (2026-10-07) and Consolidated Design Guide. No gameplay implementation is claimed here.
