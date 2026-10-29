# Wildlife food chains and per-island tables (GR4): PROPOSAL, written October 28, 2026

Status: **proposal for owner approval; nothing here is implemented beyond the populations listed as "now".** Numbers are tuning.
Source of truth for "now": `Scripts/Setup/wildlife_distribution.py` (per-island plan, scaled by the five-island density of 7, plus the
large animals) and `Scripts/Setup/add_spiders.py` (cave and swamp spiders). Only species that exist in `build_animals.py` are used;
no new species are invented. All current animals yield Raw Meat.

## The eleven modelled animals

| Animal | Behaviour now | Eats (proposed) | Eaten by (proposed) |
|---|---|---|---|
| Brown Pelican | docile, shore | fish (the fish system) | nothing hunts it; it flees |
| Flamingo | docile, shore | shrimp and algae of the shallows (flavour only) | alligator, giant crocodile at the water edge |
| Tortoise | docile, inland | low plants | bear, lion (rarely: the shell) |
| Squirrel Monkey | docile, among trees | fruit, berries | none; it flees survivors |
| Cottonmouth | aggressive, swamp low ground | small prey (flavour) | alligator, giant crocodile |
| American Alligator | aggressive, swamp low ground | cottonmouth, flamingo, fish | giant crocodile |
| Giant Crocodile | aggressive, swamp low ground | alligator, flamingo, anything in the water | apex |
| Black Bear | aggressive, Winter inland | fish, berries, tortoise-sized prey | apex of Winter |
| Lion | aggressive, Plains inland | tortoise, docile land animals | apex of Plains |
| Elephant | docile, Jungle, pushes trees over | leaves, bark | none (the largest animal) |
| Cave Spider | aggressive, caves and swamp; rideable | cave insects (flavour), survivors | none |

"Eats" and "eaten by" are flavour for the journal and for a possible ecology display; the game does not simulate predation, and this
proposal does not ask for it. If the owner wants animals to hunt one another, that is a new system and needs its own decision.

## Chains per region (what is on the island now, and the gap)

- **Plains (Starter and the rest of the region):** pelican and flamingo on the shore; the starter island adds a tortoise and two
  squirrel monkeys; one lion inland on the Plains islands (placed 26 m or more from the spawn). Chain: shallows to flamingo and
  pelican; plants to tortoise to lion. Gap: no deer, rabbit or boar is modelled, so the lion has only the tortoise and the survivor
  to hunt. Adding grazers is the first thing the Plains chain needs, and needs owner approval for the species.
- **Jungle:** squirrel monkeys in the trees (3 per island at density 7, so 21), tortoises (7), elephants (2). Chain: fruit and
  canopy to monkey; leaves to elephant (which clears trees). Gap: no jungle predator exists; the cave spider is the only danger.
- **Desert:** tortoises (14), flamingos (14), pelicans (7) at oases and the coast. Chain: oasis shallows to flamingo and pelican;
  scrub to tortoise. Gap: no predator; desert fox, scorpion and snake appear in the owner regional notes but are not modelled.
- **Swamp:** alligators (14), cottonmouths (14), one giant crocodile, spiders on the wet low ground (5 per island). Chain:
  cottonmouth and flamingo prey, then alligator, then giant crocodile. This is the only region with a complete three-step chain.
- **Winter:** two bears per island and nothing else; the chain is bear from fish and berries. Gap: snow leopard, wolf and elk named
  by the owner are not modelled, so Winter inland is nearly empty.

(The per-island counts above are the plan in `wildlife_distribution.py`, not a count of what is placed in the map today.)

## What I would build next (in order, all need approval)

1. A grazer for the Plains and Winter (deer or elk) so the lion and the bear have prey in the world.
2. Wolves or snow leopards for Winter, so it is not a bear-only region.
3. A desert reptile and a desert predator (fox) from the owner regional list.
4. Food-chain notes in the journal (see the journal draft) rather than a predation simulation.

## What this document does not decide

Spawn counts, levels, taming foods and any hunting simulation. The owner earlier notes keep taming foods (Azul and Mary-Dash
berries, bass for a house cat) as they are; nothing here changes them. The approved wildlife notes say saddled or tamed spiders
may jump and climb; the rideable spider built on October 28 is mountable without a saddle for now, and the saddle requirement is
still open.
