# Scenario: generation queue

**Handoff rule (owner, October 22): before your usage runs out, close out what you have open, push, and write a `HANDOFF` entry in [INBOX.md](INBOX.md); at the start of each session continue any unpicked `HANDOFF` first ([TEAM_CHARTER](../TEAM_CHARTER.md) section 7).**

**Team rule (owner, October 22): everyone works freely; no locks, claims or ownership of anything.** See [../TEAM_CHARTER.md](../TEAM_CHARTER.md). `CLAIMED` / `IN PROGRESS` below is a courtesy notice only: it blocks nobody. Any teammate may add, take over or finish any task.).

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

### S1. Voices for the four approved animals — QUEUED (G1/G2 matrix ready)

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

### S3. Spiders — QUEUED (G3 brief ready)

| Job | Prompt | Length | ~Credits | Destination |
|---|---|---|---|---|
| Spider scuttle | A large spider's legs skittering quickly over stone in a cave, close | 2 s | 1 | `Art/Audio/Fauna/SFX_SpiderScuttle-v1.wav` |
| Spider hiss | A large spider's dry hiss and clicking chitter as it rears up | 2 s | 1 | `Art/Audio/Fauna/SFX_SpiderHiss-v1.wav` |
| Spider bite | A quick wet bite and click of fangs, close | 1 s | 1 | `Art/Audio/Fauna/SFX_SpiderBite-v1.wav` |
| Spider death | A spider's legs curling and twitching to stillness, soft crackle | 2 s | 1 | `Art/Audio/Fauna/SFX_SpiderDeath-v1.wav` |

About 4 credits for the initial rows. Use the shared-species cave/swamp brief; hiss/chitter is designed stridulation foley, not a claimed natural recording. Additional contact/web jobs below.

### S4. Bites and blows landing — DONE (generated October 16, 2 credits; saved, not imported until the attacks exist)

| Job | Prompt | Length | ~Credits | Destination |
|---|---|---|---|---|
| Animal bite contact | An animal's bite landing on a person through cloth, a short muffled crunch, no voice | 1 s | 1 | `Art/Audio/Fauna/SFX_BiteContact-v1.wav` |
| Claw swipe | A large animal's claws swiping through the air and tearing cloth | 1 s | 1 | `Art/Audio/Fauna/SFX_ClawSwipe-v1.wav` |

About 2 credits. These are used by the bite and swipe attacks once the attack animations exist (owner milestone
"Species-appropriate attacks").

### S5. Existing animals' missing sounds — QUEUED (G1 matrix ready)
The cottonmouth, tortoise and squirrel monkey have no sounds yet, and the alligator, flamingo and pelican have calls
only (`Art/Audio/README.md`). Once G1 lists what each needs, add a row per sound here at about 1–2 credits each.

### S6. Six-view reference images — QUEUED (owner delegated approval; Claude prices Scenario use)
- **Why:** owner, October 16: six views (front, back, left, right, top, underside) of every resource and every
  animal, the same object in each (`Art/Reference/README.md`; about 270 images in all).
- **Pilot:** one resource (Oak Wood) and one animal (Bear, from ChatGPT G4's prompt sheet). Pick the model with
  Scenario's recommendation for consistent multi-view images. Price six images per set. Generate the two sets only if
  the pilot's cost is in line with the sound batches. Save to `Art/Reference/Resources/OakWood/` and
  `Art/Reference/Animals/Bear/` as `front.png` … `underside.png`.
- **Then:** show the owner the pilot and the price of the full set; the rest waits for their answer.

### S7. Ship module references — QUEUED (prompts ready; Claude prices any Scenario run first)
Railing modules, sail assemblies, surgeon's table and tools: six views each, priced first as S6 is. Eleven built-in-generated concept sheets now exist; do not rerun them blindly or spend credits without the existing priced-pilot procedure. Separate orthographic files remain pending.

Shared job: repeat each asset's exact shared identity in PROMPTS.md with the front/back/left/right/top/underside camera line and an attachment detail; destination Art/Reference/Ships/<Module>/<view>.png. Cost/model TBD; Claude runs Scenario only.

- QUEUED: [DinghyRailing](../../Art/Reference/Ships/DinghyRailing/PROMPTS.md).
- QUEUED: [LargeRectangularSail](../../Art/Reference/Ships/LargeRectangularSail/PROMPTS.md).
- QUEUED: [LargeWeightedSail](../../Art/Reference/Ships/LargeWeightedSail/PROMPTS.md).
- QUEUED: [MediumRectangularSail](../../Art/Reference/Ships/MediumRectangularSail/PROMPTS.md).
- QUEUED: [MediumWeightedSail](../../Art/Reference/Ships/MediumWeightedSail/PROMPTS.md).
- QUEUED: [PlainRailing](../../Art/Reference/Ships/PlainRailing/PROMPTS.md).
- QUEUED: [SmallRectangularSail](../../Art/Reference/Ships/SmallRectangularSail/PROMPTS.md).
- QUEUED: [SmallWeightedSail](../../Art/Reference/Ships/SmallWeightedSail/PROMPTS.md).
- QUEUED: [SurgeonTable](../../Art/Reference/Ships/SurgeonTable/PROMPTS.md).
- QUEUED: [SurgeonTools](../../Art/Reference/Ships/SurgeonTools/PROMPTS.md).
- QUEUED: [TwoCannonRailing](../../Art/Reference/Ships/TwoCannonRailing/PROMPTS.md).

## Done

| Batch | Jobs | Credits | Commit |
|---|---|---|---|
| First sounds (Oct 15) | work, gather, steps, surf, wind, birds, three animal calls | 31 | `9a54ac7` |
| Second batch (Oct 15) | cannons, hulls, splash, bailing, sinking, creak, rigging, deck, swimming, insects, cave | 26 | `b98c572` |
| Third batch (Oct 16) | grass and stone steps, forest wind, jungle, swamp frogs | 14 | `0d0a685` |
| Anchor (Oct 16) | chain drop, catch, raise | 5 | `8ae15b7` |
| S2 + S4 (Oct 16) | tree fall, elephant step, bite contact, claw swipe | 5 | `e0c3f04` |

## G1/G3 additional queued sound jobs — October 18

Drafts only; Claude runs/prices these, no credits spent by ChatGPT. Follow the matrix. Idle/locomotion/contact variants need visual synchronization and licensing provenance.

| Status | Job / exact prompt | Length | Destination |
|---|---|---|---|
| QUEUED | Dry snake scales sliding across leaf litter, close, no growl or rattle | 2 s | Art/Audio/Fauna/SFX_CottonmouthSlither-v1.wav |
| QUEUED | Short defensive snake hiss, no rattlesnake rattle, no music | 2 s | Art/Audio/Fauna/SFX_CottonmouthHiss-v1.wav |
| QUEUED | Slow heavy tortoise clawed footfalls and shell brush on dry ground, no voice | 2 s | Art/Audio/Fauna/SFX_TortoiseStep-v1.wav |
| QUEUED | Short quiet tortoise withdrawal breath and shell scrape, no growl | 1 s | Art/Audio/Fauna/SFX_TortoiseWithdraw-v1.wav |
| QUEUED | Squirrel monkey alarm chitter, close, no human voice or music | 2 s | Art/Audio/Fauna/SFX_MonkeyChitter-v1.wav |
| QUEUED | Small primate light quick steps and branch rustle, no voice | 2 s | Art/Audio/Fauna/SFX_MonkeyStep-v1.wav |
| QUEUED | Short small fang contact through cloth, no voice, no gore emphasis | 1 s | Art/Audio/Fauna/SFX_SpiderContact-v1.wav |
| QUEUED | Thin dry silk strands stretching and tearing, close, no voice | 2 s | Art/Audio/Fauna/SFX_SpiderWebTear-v1.wav |
| QUEUED | Light segmented spider legs contacting stone in a short alternating cycle, no voice | 2 s | Art/Audio/Fauna/SFX_SpiderLegStone-v1.wav |
| QUEUED | Light segmented spider legs contacting damp mud, no voice | 2 s | Art/Audio/Fauna/SFX_SpiderLegMud-v1.wav |

Additional species movement/hurt/death contacts follow the matrix, reusing suitable existing generic contact foley only where timbre matches. Do not generate predator voices for peaceful fish, manta or squid. Model/cost remains Claude-priced per current queue policy.

October 18 update: the owner authorized autonomous decisions and approval in the current chat. Built-in image generation is authorized and is producing references without Scenario credits. ChatGPT still does not spend Scenario credits. Claude prices any Scenario follow-up and avoids duplicating delivered references. Approval is not a claim that all image files exist or pass QA.
