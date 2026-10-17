# Scenario: generation queue

Owner, October 16: Claude coordinates Codex, ChatGPT and Scenario. Scenario is a generation service on the owner's
account; it does not read this repository. This file is its **job queue**: each job's model, prompt, length, cost and
destination, so whoever runs it gets the same result. **Claude runs the jobs** through the Scenario MCP connection.
The owner can also run them in Scenario's web app. ChatGPT and Codex add jobs as `QUEUED` but never spend credits.
Codex's list is [CODEX.md](CODEX.md); ChatGPT's is [CHATGPT.md](CHATGPT.md).

Jobs run by anyone other than Claude are reported in [INBOX.md](INBOX.md).

## How jobs are run

- **Account:** team `team_VYLneaunKSxVDcNF5J2w8BA8`, project `proj_UFoVjNUmi5nHcuBHuGuhSKof` (ids only; no keys
  here).
- **Sound:** model `model_sonilo-v1-1-text-to-sound-effects`, WAV output. Cost is about 1 credit up to 2 s, 2 credits
  for 3–5 s, 4 for 10 s and 8 for 20 s.
- **Two jobs at a time.** The plan runs two in parallel; more than that crossed job ids once. After each job, read it
  back (`job_get`, verbose) and check that its prompt is this job's before saving the result.
- **Saving:** save each result to the destination below (`Art/Audio/<category>/<Name>-v1.wav`, a second take `-v1b`).
  Then import it with `Scripts/Setup/import_audio.py` (add a line to its `SOUNDS` table), list it with its prompt in
  `Art/Audio/README.md`, and set the job's status here to `DONE <commit>`.
- **Drafts only:** these are drafts for timing and placement. Replace them with recorded or properly licensed sound
  before release.
- **Credit rule:** the owner approved working with Scenario on October 16. Batches like the ones below (about 10–25
  credits) go ahead. Anything much larger, and **any image set**, waits for the owner's go-ahead with a priced pilot.
- **Spent so far:** 81 credits on sound (October 15–16, see `Docs/REPORTS/2026-10-15_Claude.md`).

## Queue

Status: `QUEUED` (ready to run) · `WAITING` (needs something first) · `DONE <commit>` · `HELD` (needs the owner).

### S1. Voices for the four approved animals — WAITING (on ChatGPT G1/G2 settling which sounds each needs)

| Job | Prompt | Length | ~Credits | Destination |
|---|---|---|---|---|
| Bear growl | A large brown bear's low rumbling warning growl, close, outdoors, no music | 3 s | 2 | `Art/Audio/Fauna/SFX_BearGrowl-v1.wav` |
| Bear roar | A brown bear's short aggressive roar as it charges, close, outdoors | 3 s | 2 | `Art/Audio/Fauna/SFX_BearRoar-v1.wav` |
| Lion roar | A male lion's deep roar carrying over open grassland, a few grunts after | 5 s | 2 | `Art/Audio/Fauna/SFX_LionRoar-v1.wav` |
| Lion snarl | A lioness's sharp snarl and hiss as she threatens, close | 2 s | 1 | `Art/Audio/Fauna/SFX_LionSnarl-v1.wav` |
| Crocodile bellow | A huge saltwater crocodile's low bellow in a swamp, water rippling | 3 s | 2 | `Art/Audio/Fauna/SFX_CrocodileBellow-v1.wav` |
| Crocodile jaw snap | A giant crocodile's jaws snapping shut with a splash | 2 s | 1 | `Art/Audio/Fauna/SFX_CrocodileSnap-v1.wav` |
| Elephant trumpet | An elephant's loud trumpet call in a jungle, birds startled | 3 s | 2 | `Art/Audio/Fauna/SFX_ElephantTrumpet-v1.wav` |
| Elephant rumble | An elephant's low contented rumble, close, jungle ambience faint | 3 s | 2 | `Art/Audio/Fauna/SFX_ElephantRumble-v1.wav` |

About 14 credits. Wiring them up needs the animals themselves (models, AI), which don't exist yet. The sounds can be
made ahead.

### S2. A tree pushed down — DONE (generated October 16, 3 credits; saved, not imported until CODEX C1 lands)

| Job | Prompt | Length | ~Credits | Destination |
|---|---|---|---|---|
| Tree cracks and falls | A jungle tree's trunk cracking and splintering under a heavy push, then falling through branches and thudding onto the ground | 5 s | 2 | `Art/Audio/Work/SFX_TreeFall-v1.wav` |
| Heavy footfalls | One heavy elephant footfall on soft jungle ground, a low thud | 1 s | 1 | `Art/Audio/Fauna/SFX_ElephantStep-v1.wav` |

About 3 credits. They go with Codex's falling trees (CODEX.md C1); the tree-fall sound can be wired as soon as C1 lands.

### S3. Spiders — WAITING (on ChatGPT G3's brief)

| Job | Prompt | Length | ~Credits | Destination |
|---|---|---|---|---|
| Spider scuttle | A large spider's legs skittering quickly over stone in a cave, close | 2 s | 1 | `Art/Audio/Fauna/SFX_SpiderScuttle-v1.wav` |
| Spider hiss | A large spider's dry hiss and clicking chitter as it rears up | 2 s | 1 | `Art/Audio/Fauna/SFX_SpiderHiss-v1.wav` |
| Spider bite | A quick wet bite and click of fangs, close | 1 s | 1 | `Art/Audio/Fauna/SFX_SpiderBite-v1.wav` |
| Spider death | A spider's legs curling and twitching to stillness, soft crackle | 2 s | 1 | `Art/Audio/Fauna/SFX_SpiderDeath-v1.wav` |

About 4 credits. Adjust the prompts to G3's description of the spiders before running.

### S4. Bites and blows landing — DONE (generated October 16, 2 credits; saved, not imported until the attacks exist)

| Job | Prompt | Length | ~Credits | Destination |
|---|---|---|---|---|
| Animal bite contact | An animal's bite landing on a person through cloth, a short muffled crunch, no voice | 1 s | 1 | `Art/Audio/Fauna/SFX_BiteContact-v1.wav` |
| Claw swipe | A large animal's claws swiping through the air and tearing cloth | 1 s | 1 | `Art/Audio/Fauna/SFX_ClawSwipe-v1.wav` |

About 2 credits. These are used by the bite and swipe attacks once the attack animations exist (owner milestone
"Species-appropriate attacks").

### S5. Existing animals' missing sounds — WAITING (on ChatGPT G1's matrix)
The cottonmouth, tortoise and squirrel monkey have no sounds yet, and the alligator, flamingo and pelican have calls
only (`Art/Audio/README.md`). Once G1 lists what each needs, add a row per sound here at about 1–2 credits each.

### S6. Six-view reference images, a priced pilot — HELD (owner go-ahead needed)
- **Why:** owner, October 16: six views (front, back, left, right, top, underside) of every resource and every
  animal, the same object in each (`Art/Reference/README.md`; about 270 images in all).
- **Pilot:** one resource (Oak Wood) and one animal (Bear, from ChatGPT G4's prompt sheet). Pick the model with
  Scenario's recommendation for consistent multi-view images. Price six images per set. Generate the two sets only if
  the pilot's cost is in line with the sound batches. Save to `Art/Reference/Resources/OakWood/` and
  `Art/Reference/Animals/Bear/` as `front.png` … `underside.png`.
- **Then:** show the owner the pilot and the price of the full set; the rest waits for their answer.

### S7. Ship module references — WAITING (on ChatGPT G6/G7 prompt sheets)
Railing modules, sail assemblies, surgeon's table and tools: six views each, priced first as S6 is.

## Done

| Batch | Jobs | Credits | Commit |
|---|---|---|---|
| First sounds (Oct 15) | work, gather, steps, surf, wind, birds, three animal calls | 31 | `9a54ac7` |
| Second batch (Oct 15) | cannons, hulls, splash, bailing, sinking, creak, rigging, deck, swimming, insects, cave | 26 | `b98c572` |
| Third batch (Oct 16) | grass and stone steps, forest wind, jungle, swamp frogs | 14 | `0d0a685` |
| Anchor (Oct 16) | chain drop, catch, raise | 5 | `8ae15b7` |
| S2 + S4 (Oct 16) | tree fall, elephant step, bite contact, claw swipe | 5 | `e0c3f04` |
