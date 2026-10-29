# Skill tree expansion (GR2): PROPOSAL, written October 28, 2026

Status: **proposal for owner approval; not implemented.** All costs and bonuses are tuning. The current tree is the Wayfarer
constellation in `Source/EW/EWSkillTree.cpp`: nine stars (First Light at the root; Gatherer, Torchbearer, Hardy, Field Repair,
Strong Back, Second Wind, Metalwork, Deep Reserves). Each level gives one skill point. Stars cost 1 or 2 and some unlock recipes and
small bonuses (+10 health, +10 stamina, +5 or +10 kg).

This proposal adds three constellations that each start from First Light, nine stars apiece, using only systems that already exist
(recipes, carry weight, health, stamina, cooking, building, hunting yields). No star changes combat damage or adds a new system.

## Hunter (animals and the hunt)
| Star | Needs | Cost | Effect |
|---|---|---|---|
| Quiet Step | First Light | 1 | Wild animals notice you from 10% less distance (needs a notice-range multiplier on the survivor) |
| Skinning Knife | Quiet Step | 1 | Unlocks a Skinning Knife recipe; harvesting an animal can give one extra Raw Meat |
| Steady Aim | Quiet Step | 1 | Placeholder for ranged weapons (not in the game yet): keep unlit until they exist |
| Tracker | Skinning Knife | 1 | Animal footprints stay visible longer (uses the footprint component) |
| Light Pack | Skinning Knife | 1 | +5 kg carrying capacity |
| Bite Resistance | Tracker | 2 | Animal bites do 10% less damage |
| Fisher | Tracker | 2 | Fishing is faster (uses the fish system timings) |
| Thick Hide | Bite Resistance | 2 | +15 maximum health |
| Apex | Thick Hide, Fisher | 3 | Unlocks Hunter Stew (a better cooked-meat recipe) |

## Cook (food and healing)
| Star | Needs | Cost | Effect |
|---|---|---|---|
| Campfire Craft | First Light | 1 | Unlocks cooking at a campfire (Cooked Fish and Meat stay with Torchbearer) |
| Preserve | Campfire Craft | 1 | Berries spoil 25% slower |
| Seasoning | Campfire Craft | 1 | Cooked food restores 10% more hunger |
| Clean Water | Preserve | 1 | Unlocks a water-purifying recipe (needs a recipe asset) |
| Stomach of Iron | Seasoning | 2 | Food sickness lasts half as long |
| Herbalist | Clean Water | 2 | Herbal Remedy restores 25% more health |
| Hearty Meals | Seasoning | 2 | Eating gives a short stamina boost |
| Feast | Herbalist, Hearty Meals | 3 | Unlocks a Feast recipe that feeds more than one portion at once |
| Iron Gut | Stomach of Iron | 3 | Immune to food sickness |

## Builder (build mode and the ship)
| Star | Needs | Cost | Effect |
|---|---|---|---|
| Foundations | First Light | 1 | Unlocks the first build pieces beyond the starter set |
| Sound Joinery | Foundations | 1 | Build pieces cost 10% fewer materials |
| Carpenter | Foundations | 1 | Crafting time of wooden recipes 15% shorter |
| Stonework | Sound Joinery | 2 | Unlocks stone build pieces |
| Door and Hinge | Carpenter | 1 | Unlocks doors and shutters |
| Shipwright Eye | Carpenter | 2 | Repair Kit recipes cost less |
| Heavy Lifter | Stonework | 2 | +10 kg carrying capacity |
| Master Builder | Stonework, Door and Hinge | 3 | Unlocks the largest build pieces |
| Harbourmaster | Shipwright Eye | 3 | Faster boarding and anchoring (uses the ship timings) |

## Points budget and open questions
- All four constellations together are about 36 stars costing about 62 points; with one point per level, the owner chooses the
  level cap that makes this a goal and not a trivial finish.
- Stars that need a system (Quiet Step, Bite Resistance, Seasoning, Hearty Meals and others) need small code hooks before they can
  work; stars that only unlock recipes need recipe assets (some exist: Hatchet, Herbal Remedy, Inn Torch, Cooked Fish and Meat,
  Repair Kit, Metal Pickaxe).
- Steady Aim is deliberately a placeholder: do not light it until ranged weapons exist.
