# ChatGPT: your tasks

Owner, October 16: Claude coordinates Codex, ChatGPT and Scenario and hands each the work that suits it. This file
is **ChatGPT's list**: design write-ups, research, reference prompt sheets, the art catalogue and reviewing what the
others built. Codex's list is [CODEX.md](CODEX.md); Scenario's generation queue is [SCENARIO.md](SCENARIO.md).


**Report to Claude (owner, October 17):** whenever you claim, finish, get stuck on or stop a task, add an entry to
[INBOX.md](INBOX.md) and push it with your work to `main`. Work left on a local branch or worktree is invisible to
Claude and the owner.

## Before you start

1. `git fetch && git pull --ff-only`. Claude, Codex and the owner all commit to `main`.
2. Read the header of [../DELEGATED_TASKS.md](../DELEGATED_TASKS.md): the shared rules and the **Claude is working on**
   list. Never edit the files on that list; leave a note under your task instead.
3. **Claim** a task by changing its status here to `CLAIMED (ChatGPT, <date>)` and pushing that one-line change before
   you start. When finished, set it to `DONE <commit>` and write under it what you did.
4. Write what is decided apart from what is proposed. The owner's latest message wins over older documents. Anything
   the owner has not decided stays **TBD**, and a suggestion is labelled as one. Do not invent stats, sizes or numbers.
5. Do not spend Scenario credits yourself. If a task produces generation prompts, add them to
   [SCENARIO.md](SCENARIO.md) as `QUEUED` jobs and Claude runs them.

## New tasks (October 16)

### G1. Attack and voice matrix for every animal — OPEN
- **Why:** owner milestone "Species-appropriate attacks and vocalizations" (`Docs/MILESTONES.md`,
  [ANIMAL_ATTACK_AUDIO_AND_REGIONAL_WILDLIFE_PROPOSAL](../ANIMAL_ATTACK_AUDIO_AND_REGIONAL_WILDLIFE_PROPOSAL_2026-10-16.md)):
  bites and growls only where the species really bites or growls, and the right alternative for the rest.
- **Do:** a new `Art/Animals/ATTACK_AND_VOICE_MATRIX_2026-10-16.md`. Make one row per animal that exists today:
  - the land animals in `Content/Elitewake/Wildlife/Animals/DA_Animal_*`: alligator, flamingo, brown pelican, cottonmouth,
    tortoise, squirrel monkey, and any others you find;
  - the sea creatures in `build_fish.py`;
  - the owner-approved additions (bears, lions, giant crocodiles, elephants, spiders).
  
  Columns: does it bite; its threat display; its attack(s) (bite, swipe, charge, tusk, sting, peck, none); the sounds
  it needs (idle, walk, run, threat, attack, contact, hurt, death); and what plays instead where a bite or growl would
  be wrong.
- **Done when:** the matrix covers every animal and links from the animal requirements document.

### G2. Reconcile the wildlife roster documents for the owner — OPEN
- **Why:** the October 16 wildlife documents disagree.
  - [APPROVED_BEAR_ELEPHANT_GIANT_CROCODILE_LION_WILDLIFE](../APPROVED_BEAR_ELEPHANT_GIANT_CROCODILE_LION_WILDLIFE_2026-10-16.md)
    places elephants in the Central Plains.
  - [ELEPHANT_TROPICAL_ISLAND_HABITAT_CORRECTION](../ELEPHANT_TROPICAL_ISLAND_HABITAT_CORRECTION_2026-10-16.md) moves
    them to the Western Jungle.
  - The proposal document lists many suggested species (deer, wolves, jaguars, camels…) that are not approved.
- **Do:** in `Docs/OPEN_QUESTIONS_2026-10-15.md`, list the roster as it stands: approved and placed, approved but not
  built, and suggested but not approved. Each region gets its species, with the source document for each. Mark the
  elephant correction as the latest word. List the suggestions as questions for the owner. Don't edit the owner's
  documents, except to add a "superseded by" note where the correction already says so.
- **Done when:** one clear roster table and its questions are in the open-questions file.

### G3. Spider design brief — OPEN
- **Why:** owner milestone "Spiders in every cave and Southern Swamp", with full movement, bite, hit, death and web
  animations and synchronised sounds
  ([ELEPHANT_DESTRUCTION_WILDLIFE_ROAMING_AND_SPIDER_MILESTONES](../ELEPHANT_DESTRUCTION_WILDLIFE_ROAMING_AND_SPIDER_MILESTONES_2026-10-16.md)).
  Caves already have cobwebs that tear when walked through (`Source/EW/EWCobweb.*`, built by Claude).
- **Do:** a new `Art/Animals/Spider/SPIDER_BRIEF_2026-10-16.md`. Cover:
  - the cave spider and the swamp spider: are they one kind or two? Put this as a question if unsure;
  - their look (body plan, colours, markings) for a consistent six-view set;
  - the animation list: idle, leg cycle, walk, turn, climb if supported, alert, bite, hit, death, web interaction;
  - the sound list: scuttle, chitter or hiss (no growls), bite, impact, web tearing;
  - how they should fit the existing cobwebs.
  
  Leave size, health, damage, aggression and density TBD for the owner, with suggestions marked as suggestions.
  Then add the spiders' Scenario sound jobs to [SCENARIO.md](SCENARIO.md) as `QUEUED`.
- **Done when:** the brief exists, its open questions are in `Docs/OPEN_QUESTIONS_2026-10-15.md`, and the sound jobs
  are queued.

### G4. Six-view prompt sheets for the four new animals — OPEN
- **Why:** each animal needs six consistent views (front, back, left, right, top, underside), per
  [the animal requirements](../../Art/Animals/ANIMAL_MODEL_ANIMATION_AUDIO_REQUIREMENTS_2026-10-16.md) and
  `Art/Reference/README.md`.
- **Do:** for Bear, Lion, Giant Crocodile and Elephant, write `Art/Reference/Animals/<Name>/PROMPTS.md`. It holds one
  shared description that every view repeats word for word (species, colouring, markings, proportions, neutral pose,
  plain light background, no text), plus the six per-view camera lines. Follow the current approved region of each
  (see G2). No images: Claude runs a priced pilot first ([SCENARIO.md](SCENARIO.md) S6).
- **Done when:** the four prompt sheets exist and `Art/Reference/README.md` lists them as "prompts written, images
  pending".

### G5. Elephant knock-down rules for the owner — OPEN
- **Why:** owner milestone "Tropical elephant obstacle destruction": elephants push down trees and "appropriate
  obstacles", and protect critical structures. Codex is building the falling-tree half (CODEX.md C1).
- **Do:** a short proposal in `Docs/OPEN_QUESTIONS_2026-10-15.md` covering:
  - which things an elephant may push over: Jungle ash, Maravai, others?
  - what it must never touch: Ports, docks, player buildings, ships, caves, landmarks;
  - when it pushes: wandering, charging, or only when blocked;
  - what the player sees and hears.
  
  Every item is phrased as a question or a labelled suggestion.
- **Done when:** the questions are in the file.

## Earlier tasks that suit you (full text in [../DELEGATED_TASKS.md](../DELEGATED_TASKS.md); claim them there)

| Task | What | Status |
|---|---|---|
| T30 | List the October 15–16 delegated world decisions for the owner | OPEN |
| T27 | Catalogue the new oak and ash leaf art | OPEN |
| T10 | "Village" becomes "Port" | OPEN |
| T11 | Metric units audit | OPEN |
| T6 | A better tortoise shell | OPEN |

Suggested order: G2 (it settles the roster the others depend on), G1, G3, G4, G5, T30, then the rest.
