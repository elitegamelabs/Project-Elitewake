# Audio sources

**Drafts, not final audio.** Generated on 2026-10-15 through the owner's Scenario account (scenario.com, model
Sonilo V1.1 Text to SFX, WAV, 44.1 kHz stereo; 31 credits in all). They give the game its first sounds so timing and
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
| Ambience/AMB_Seabirds-v1 | a few gulls calling at a middle distance | 10 s | now and then, away from the Winter region |
| Fauna/SFX_AlligatorHiss-v1, -v1b | an alligator's long low warning hiss (two takes) | 2 s | an alligator goes for a survivor, or is struck |
| Fauna/SFX_FlamingoCall-v1 | a few nasal honks from one flamingo | 2 s | every 20 to 45 s, or when struck |
| Fauna/SFX_PelicanCall-v1 | a brown pelican's hoarse grunting croak | 2 s | every 30 to 60 s, or when struck |

Known draft issues: the 20 s loops were not cut to loop seamlessly, so a seam may be heard; the snow step may hold
two crunches; the pickaxe strike has a second knock about 0.25 s in. Real pelicans are nearly silent.
