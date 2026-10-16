# Audio sources

**Drafts, not final audio.** Generated on 2026-10-15 through the owner's Scenario account (scenario.com, model
Sonilo V1.1 Text to SFX, WAV, 44.1 kHz stereo): a first batch of 15 (31 credits) and, approved by the owner that
night, a second of 12 for the ships, decks, swimming, night and caves (26 credits), and on October 16 a third of 5
for grass and stone underfoot and the wooded regions' own sounds (14 credits). They give the game its first sounds so timing and
placement can be judged; replace them with recorded or properly licensed sounds, under the same names with a higher
version, before release. Nobody has listened to them yet: the owner's ear is the review.

Imported by `Scripts/Setup/import_audio.py` to `/Game/Elitewake/Audio/<folder>/S_<name>_v1`, where the levels that
even them out live. Played from code (`UEWSoundLibrary`, `UEWSoundscapeComponent`, the animals' `Calls`).

| File | Prompt (abridged) | Length | Plays |
|---|---|---|---|
| Work/SFX_ChopWood-v1 | a hatchet chop biting into a trunk, dry thunk with a wood crack | 1 s | a hatchet's blow lands on a tree |
| Work/SFX_PickaxeStone-v1 | an iron pickaxe on hard rock, ringing clank, chips falling | 1 s | a pickaxe's blow lands on stone |
| Work/SFX_GlanceClink-v1 | a tool skidding off a hard surface, a weak clink | 1 s | the wrong tool glances off |
| Gather/SFX_GatherRustle-v1 | hands rummaging in a leafy bush, rustle and stem snaps | 2 s | a gather by hand starts |
| Gather/SFX_Pickup-v1 | a small item tucked into a cloth satchel | 1 s | what was gathered goes in the pack (gatherer only) |
| Footsteps/SFX_StepSand-v1, -v1b | one boot step on dry beach sand (two takes) | 1 s | each stride ashore, outside the Winter region |
| Footsteps/SFX_StepSnow-v1 | one boot step crunching packed snow | 1 s | each stride in the Winter region |
| Ambience/AMB_OceanSurf-v1 | calm surf washing a sandy beach, even for looping | 20 s | loop, everywhere |
| Ambience/AMB_WinterWind-v1 | steady icy wind over snowfields, low howl | 20 s | loop, the Winter region |
| Ambience/AMB_OceanSurf-v2, AMB_WinterWind-v2 | the v1 takes with their last 3 s cross-faded into the start (`Scripts/Art/make_audio_loops.py`) | 17 s | what the game loops |
| Ambience/AMB_Seabirds-v1 | a few gulls calling at a middle distance | 10 s | now and then, away from the Winter region |
| Fauna/SFX_AlligatorHiss-v1, -v1b | an alligator's long low warning hiss (two takes) | 2 s | an alligator goes for a survivor, or is struck |
| Fauna/SFX_FlamingoCall-v1 | a few nasal honks from one flamingo | 2 s | every 20 to 45 s, or when struck |
| Fauna/SFX_PelicanCall-v1 | a brown pelican's hoarse grunting croak | 2 s | every 30 to 60 s, or when struck |
| Ships/SFX_CannonFire-v1 | an 18th-century ship's cannon: deep boom, sharp crack, rolling echo | 3 s | a shot leaves the muzzle (heard to 400 m) |
| Ships/SFX_HullHit-v1 | a cannonball smashing into a wooden hull, splintering planks | 2 s | a shot strikes a ship |
| Ships/SFX_ShotSplash-v1 | a heavy ball plunging into the sea, tall splash | 2 s | a shot falls in the sea (on land: the pickaxe strike, pitched down) |
| Ships/SFX_Bail-v1 | a bucket scooping bilge water and tossing it over the side | 2 s | each stroke of the bailing bucket |
| Ships/SFX_ShipSinking-v1 | timbers groaning and cracking, water rushing in | 5 s | a ship starts to go down |
| Ships/AMB_HullCreak-v1, -v2 | slow rhythmic timber creaks as a ship rolls (v2: looped) | 10 s / 8 s | loop on every ship, louder making way |
| Ships/AMB_Rigging-v1, -v2 | sails fluttering, ropes and blocks creaking (v2: looped) | 10 s / 8 s | loop on every ship with sail set |
| Footsteps/SFX_StepDeck-v1, -v1b | one boot step on a wooden deck (two takes) | 1 s | each stride on a ship |
| Swimming/SFX_SwimStroke-v1 | an arm pulling through calm water | 1 s | each 1.8 m swum |
| Ambience/AMB_NightInsects-v1, -v2 | crickets, cicadas, distant frogs (v2: looped) | 10 s / 8 s | loop at night ashore, not in the Winter region |
| Footsteps/SFX_StepGrass-v1 | one boot step on soft grass and earth | 1 s | each stride on the green ground inland |
| Footsteps/SFX_StepStone-v1 | one boot step on bare stone with a slight echo | 1 s | each stride in a cave, on a boulder or a landmark |
| Ambience/AMB_ForestWind-v1, -v2 | wind through a forest's leaves (v2: looped, raised 2.5x) | 10 s / 7.5 s | loop ashore in the Plains |
| Ambience/AMB_JungleDay-v1, -v2 | the jungle by day: insects, distant birds and whoops (v2: looped) | 10 s / 8 s | loop in the Jungle by day |
| Ambience/AMB_SwampFrogs-v1, -v2 | bullfrogs and small frogs among reeds (v2: looped, raised 2.5x) | 10 s / 8 s | loop in the Swamp |
| Ambience/AMB_CaveDrips-v1, -v2 | drips into pools with echo (v2: looped and raised 8x, the take was very quiet) | 10 s / 8 s | loop under a cave's roof |

Known draft issues: the snow step may hold
two crunches; the pickaxe strike has a second knock about 0.25 s in. Real pelicans are nearly silent.
