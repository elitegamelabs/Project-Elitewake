# ChatGPT: your tasks

**Handoff rule (owner, October 22): before your usage runs out, close out what you have open, push, and write a `HANDOFF` entry in [INBOX.md](INBOX.md); at the start of each session continue any unpicked `HANDOFF` first ([TEAM_CHARTER](../TEAM_CHARTER.md) section 7).**

**Team rule (owner, October 22): everyone works freely; no locks, claims or ownership of anything.** See [../TEAM_CHARTER.md](../TEAM_CHARTER.md). `CLAIMED` / `IN PROGRESS` below is a courtesy notice only: it blocks nobody. Any teammate may add, take over or finish any task.).

**Owner, October 20: no agent owns any file, API or system.** Claude helps the owner design the game; it holds no locks and reserves nothing. Codex, ChatGPT and Claude may all edit any file. To avoid collisions: pull first, check `git log` and the inbox for recent work on the same files, keep commits small, and say in the inbox when you start on a file another agent changed recently. The shared Unreal editor lock (one editor at a time on this PC) still applies to everyone.

Owner, October 16: Claude coordinates Codex, ChatGPT and Scenario and hands each the work that suits it. This file
is **ChatGPT's list**: design write-ups, research, reference prompt sheets, the art catalogue and reviewing what the
others built. Codex's list is [CODEX.md](CODEX.md); Scenario's generation queue is [SCENARIO.md](SCENARIO.md).


**Report in the shared inbox (owner, October 17):** whenever you claim, finish, get stuck on or stop a task, add an entry to
[INBOX.md](INBOX.md) and push it with your work to `main`. Work left on a local branch or worktree is invisible to
Claude and the owner.

## Before you start

1. `git fetch && git pull --ff-only`. Claude, Codex and the owner all commit to `main`.
2. Read the header of [../DELEGATED_TASKS.md](../DELEGATED_TASKS.md): the shared rules. No files are reserved for any
   agent (owner, October 20).
3. **Claim** a task by changing its status here to `CLAIMED (ChatGPT, <date>)` and pushing that one-line change before
   you start. When finished, set it to `DONE <commit>` and write under it what you did.
4. Write what is decided apart from what is proposed. The owner's latest message wins over older documents. Anything
   the owner has not decided stays **TBD**, and a suggestion is labelled as one. Do not invent stats, sizes or numbers.
5. Do not spend Scenario credits yourself. If a task produces generation prompts, add them to
   [SCENARIO.md](SCENARIO.md) as `QUEUED` jobs and Claude runs them.

## New tasks (October 16)

### G1. Attack and voice matrix for every animal — DONE 6966de2 (ChatGPT, 2026-10-18)
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

### G2. Reconcile the wildlife roster documents for the owner — DONE 6966de2 (ChatGPT, 2026-10-18)
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

### G3. Spider design brief — DONE 6966de2 (ChatGPT, 2026-10-18)
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

### G4. Six-view prompt sheets for the four new animals — DONE 6966de2 (ChatGPT, 2026-10-18)
- **Why:** each animal needs six consistent views (front, back, left, right, top, underside), per
  [the animal requirements](../../Art/Animals/ANIMAL_MODEL_ANIMATION_AUDIO_REQUIREMENTS_2026-10-16.md) and
  `Art/Reference/README.md`.
- **Do:** for Bear, Lion, Giant Crocodile and Elephant, write `Art/Reference/Animals/<Name>/PROMPTS.md`. It holds one
  shared description that every view repeats word for word (species, colouring, markings, proportions, neutral pose,
  plain light background, no text), plus the six per-view camera lines. Follow the current approved region of each
  (see G2). No images: Claude runs a priced pilot first ([SCENARIO.md](SCENARIO.md) S6).
- **Done when:** the four prompt sheets exist and `Art/Reference/README.md` lists them as "prompts written, images
  pending".

### G5. Elephant knock-down rules for the owner — DONE 6966de2 (ChatGPT, 2026-10-18)
- **Why:** owner milestone "Tropical elephant obstacle destruction": elephants push down trees and "appropriate
  obstacles", and protect critical structures. Codex is building the falling-tree half (CODEX.md C1).
- **Do:** a short proposal in `Docs/OPEN_QUESTIONS_2026-10-15.md` covering:
  - which things an elephant may push over: Jungle ash, Maravai, others?
  - what it must never touch: Ports, docks, player buildings, ships, caves, landmarks;
  - when it pushes: wandering, charging, or only when blocked;
  - what the player sees and hears.
  
  Every item is phrased as a question or a labelled suggestion.
- **Done when:** the questions are in the file.

### G6. The ship surgeon: a design brief — DONE f339852 (ChatGPT, 2026-10-18)
- **Why:** owner, October 17: every ship with a walkable deck below the top has an always-present surgeon in the rear
  left corner of the first deck below the top: an operating table, scissors and tools, shelving; 15 copper per
  treatment, restoring 25% of maximum health gradually, with an animation, safe in multiplayer.
- **Do:** `Design/Ships/SHIP_SURGEON_BRIEF_2026-10-17.md`: which ships qualify today (sloop, schooner, brigantine: check
  their decks in `Scripts/Setup/build_*.py`), the room's layout and props list, the interaction flow (approach, pay,
  lie on the table, healing over time, interruptions), what happens with no copper or full health, and the open
  questions (is copper an item yet? check `Content/Elitewake/Items`). Add the six-view prompt lines for the table
  and tools to SCENARIO.md as QUEUED.
- **Done when:** the brief exists and is reported in INBOX.md.

- Delivered: surgeon brief and table/tools concept sheets with prompt/provenance files. Treatment runtime, animation and separate six-view files remain pending.

### G7. Prompt sheets for the railing modules and sail assemblies — DONE f339852 (ChatGPT, 2026-10-18)
- **Why:** owner, October 17: orthographic references (front, back, left, right, top, underside, attachment details)
  for each railing module (plain wooden, dinghy attachment, two-cannon) and the six sail assemblies (small/medium/large
  rectangular draped, small/medium/large triangular weighted).
- **Do:** `Art/Reference/Ships/<Module>/PROMPTS.md` per module, as G4 did for animals, matching the hull timber
  (`Art/Concepts/Boats/2026-10-11`). Queue them in SCENARIO.md (S7); no images.
- **Done when:** sheets exist and are reported in INBOX.md.

- Delivered: nine per-module PROMPTS.md files, nine concept sheets and provenance; S7 queued, index/catalog updated. Separate validated orthographic and deployment-state files remain pending.

### G8. Seabed corals, plants and sand: the design base — DEFERRED (owner excludes scenery in current assignment)
- **Why:** owner, October 17: the sea floor gets dynamic scenery, deeper sand, geography, corals and aquatic plants
  (ocean at most 2 km deep), and **your designs are the base that Claude brings to life in code**. Claude is building the
  geography, sand material and placement now (`Scripts/Setup/world_terrain.py`, `build_coastal_terrain.py`,
  `build_seabed_life.py`), with provisional procedural shapes and colours until your designs land. Nothing seabed-related
  is in the repo from you yet.
- **Do:** generate images with your built-in image generation, as you did for `Art/Environment/TropicalSand-v1.png`, into
  `Art/Flora/Seabed/` with a `generation.json` (prompt, sha256, status) in the same format as `Art/Environment/generation.json`:
  - textures (seamless, overhead, albedo only, no baked light): `SeabedRippledSand-v1.png` (wave-rippled sand with shell
    grit, matching TropicalSand's hue), `SeabedSilt-v1.png` (fine grey-green deep silt), `SeabedRock-v1.png`;
  - one clear design sheet per plant or animal-built structure on a plain background, side view plus top view:
    seagrass clump, kelp (stalk, gas bladders, fronds), branching coral, brain/mound coral, table/plate coral, pillar
    coral, sea fan, barrel sponge, tube sponge, sea anemone. Natural (non-glowing) colours; note which region's water each
    suits (Winter cold, Plains temperate, Jungle/Desert warm, Swamp murky) as a **suggestion**.
  - Keep the six glowing major reefs' look (`Content/Elitewake/World/Reefs`) separate: these are the ordinary sea floor.
- **Done when:** the files and `generation.json` are pushed to `main` and reported in INBOX.md. Claude then matches the
  meshes, colours and textures to them.

## Earlier tasks that suit you (full text in [../DELEGATED_TASKS.md](../DELEGATED_TASKS.md); claim them there)

| Task | What | Status |
|---|---|---|
| T30 | List the October 15–16 delegated world decisions for the owner | DONE 6966de2 |
| T27 | Catalogue the new oak and ash leaf art | DONE 6966de2 |
| T10 | "Village" becomes "Port" | DONE c0c5dc1 |
| T11 | Metric units audit | DONE 5f4c165 |
| T6 | A better tortoise shell | PAUSED (owner recovery directive, 2026-10-21) |


T6 update (2026-10-20): the durable tortoise geometry test passes (included in the 27-test Python suite). Unreal asset rebuild/save and the animal Play check are still not verified: the editor launch attempts exited before producing a project log or result. The existing `Saved/Crashes/_0000` artifact is from the earlier `T6BuildAnimalsVisible` launch; its recorded access violation is in CrashReportClient, so it does not identify the root cause in the editor process. Next: diagnose a reliable project editor launch, rebuild/save `SM_Tortoise_v1`, then run `verify_animals_play.py` and capture the requested views.


T6 pause (2026-10-21): owner reprioritized all work to project discovery/recovery and explicitly directed no new gameplay development until recovery is complete. Existing generator geometry test passes; Unreal asset save and Play verification remain pending. Resume only after the recovery phase and then continue the open asset task.

Suggested order: G8 (the owner is waiting on the sea floor), G2 (it settles the roster the others depend on), G1, G3, G4, G5, T30, then the rest.

## October 18 delegated completion notes
G1: 21-kind matrix (14 existing source kinds, five current additions, two earlier approved habitat animals). G2: reconciled region/status/source table in OPEN_QUESTIONS. G3: shared spider species/two variants brief, animation/audio contract and S3 jobs queued. G4: four identical-description six-camera prompt sets and reference images tracked by provenance. G5: obstruction policy resolved under current delegation. T27: oak/ash card provenance/catalogue, no pixels changed. T30: source-inspected world tuning recorded and retained under current delegation. G8 remains scenery-excluded. T6/T10/T11 implementation acceptance is not claimed; no code/build/Play work in this pass.

## New tasks (October 22, 2026), all `OPEN`: anyone may take them

### G-RES. Resource reference images and regional resource table
- **Why:** owner item 5: "Confirm whether all resource reference images are in the GitHub repository." Plan: `Design/World/RESOURCE_DISTRIBUTION_AND_SIX_VIEW_ASSET_PLAN_2026-10-16.md`; target `Art/Reference/Resources/<Name>/` (six views each).
- **Done when:** `Art/Reference/README.md` lists, per resource, which of the six views exist in the repo and which are missing, checked against the files actually on `main`.

### G-EDGE. World-edge design alternatives
- **Why:** owner, October 22: edge teleports that expand outwards as the map grows. Write two or three concrete designs (wrap-around, turn-back with a message, sea-fog barrier that moves), with the effect on ships, wildlife and the map, labelled as proposals for the owner to pick.

### G-REVIEW. Read the UI text and design of the October 22 menus — PARTIAL (ChatGPT, 2026-10-23)
- Read `Source/EW/EWSkillTree.cpp`, `EWProgressionComponent.cpp` (stat names and effects), `EWDeathWidget.cpp`, `EWMapWidget.cpp`, and the journal text. Correct typos, tone and anything that contradicts owner decisions. Small fixes may be pushed directly.
