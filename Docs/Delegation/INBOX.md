# Reports to Claude (the inbox)

Owner, October 17: "Make sure the other AIs are reporting to you also." Claude coordinates the work; Codex and ChatGPT
cannot message Claude directly, so they report here. **Claude reads this file before starting each piece of work**,
answers under the entry, and marks it `SEEN (Claude, <date>)`.

## How to report (Codex, ChatGPT)

Add an entry at the **top** of "Reports" (newest first) and push it to `main` in the same push as your work, whenever you:

- **claim** a task (also mark it `CLAIMED` in your task file);
- **finish** a task: what you changed (commits), what you verified and how (Play check, native test, which result
  file), what you could not verify;
- **get stuck** or find something Claude must decide or fix (a file on the "Claude is working on" list, a failing
  check, a question for the owner);
- **stop part-way**: where you got to, what is left.

Push your work to `main` (fast-forward after `git pull --ff-only`), not only to a local branch or worktree: work that
stays on a local branch is invisible to Claude and the owner. If you must keep a branch, push it to `origin` and say
which in your entry.

Entry format:

```
### <date> <agent> — <task id> <CLAIMED | DONE | STUCK | PARTIAL | NOTE>
- What: ...
- Commits / branch: ...
- Verified: ... (or "not verified: why")
- Needs from Claude or the owner: ... (or "nothing")
```

## Reports

### 2026-10-18 ChatGPT — C-WORLD40 / C-WILDLIFE40 NOTE (OWNER-APPROVED; OPEN)
- What: Owner revised world to **8 islands per region, 40 total**, and approved expanded animal placements. The 40-island wildlife plan was committed (`d450495`; legacy filename `Docs/WILDLIFE_DISTRIBUTION_26_ISLANDS.md`). I added two implementation tasks to `Docs/Delegation/CODEX.md`: **C-WORLD40** (append 14 islands without moving the original 26) and **C-WILDLIFE40** (add biome-specific populations, preserving all existing animal placements).
- Commits / branch: `d450495` wildlife design, `938afc9` task queue; main.
- Verified: reviewed current `Scripts/Setup/world_layout.py`, which still generates 26 islands, and the wildlife plan; **not verified** in Unreal/Play, no gameplay changes made.
- Needs from Claude/Codex: coordinate ownership of world-generation and animal-spawn scripts; claim tasks and implement/test. Sequential RNG must not reshuffle existing islands. Preserve all original wildlife, locations, starter facilities, ports, and save/discovery compatibility. See queue for acceptance checks.


### ChatGPT — October 18 — delivery verification receipt (UNSEEN)

Published delivery 6966de2: 77 additional PNG references (88 cumulative), 53 resource prompt sets, G1–G5/T27/T30 documentation, updated G6 decisions and owner-doc supersession. PNG decode/hash checks, preserved prior catalogue, allowed-path scope and git whitespace checks passed. No Source/Scripts/Config/Content changes; no runtime build/Play checks, no feature/PR merges, no Scenario spending. Detailed limitations and remaining work are in the expanded delivery report.


### ChatGPT — October 18 — expanded documentation and reference delivery (UNSEEN)

- Finished G1–G5, T27, T30 documentation under the owner's delegation; G6 decisions resolved. Delivery commit: 6966de2. G7 additional references delivered; complete production view sets remain partial.
- 77 additional retained PNGs, prompts/hashes/limitations, 53 resource prompt sets, 21-kind attack/voice matrix, corrected wildlife regions, spider brief, elephant rules and source-backed world/units audit. Failed views excluded.
- Published latest owner ship/sailing documents with provenance and supersession pointers. No branch/PR merge; no Claude code edits. No scenery or Scenario spending.
- [Full delivery, verified source findings and remaining assets](../REPORTS/2026-10-18_ChatGPT_Expanded_Delivery.md), [delegated decisions](../REPORTS/2026-10-18_ChatGPT_Delegated_Decisions.md). Runtime/model/animation/audio acceptance remains pending. G8 excluded as scenery. Gunport opening clearance, hull cross-view consistency, spider color separation and tortoise scute counts require refinement.


### 2026-10-18 ChatGPT — G1–G5 and remaining non-scenery art CLAIMED
- What: owner says "do everything": complete remaining ChatGPT design/research/prompt/catalogue tasks and non-scenery reference assets. Existing no-code/no-merge/no-Scenario-credit constraints remain. G8 scenery stays excluded.
- Scope: G1–G5, T30/T27, documentation portions of T10/T11, reference-only support for T6, and separate ship orthographic/deployment images. Implementation/Unreal checks remain with the coding owner; no approved decision will be invented to unblock art.
- Verified: main refreshed; previous G6/G7 delivery present. Task-specific evidence and research follow with outputs.
- Needs: unresolved design choices remain questions, not silently settled by generated art.

### 2026-10-18 ChatGPT — G6/G7 DONE (documentation); visual references PARTIAL
- What: surgeon design brief, eleven per-asset prompt sheets, eleven generated concept sheets (three railings, six sails, table/tools), provenance/hashes and catalog/index entries. S7 prompts queued; no Scenario credits spent. Current request authorizes built-in images despite older prompt-only wording.
- Commits / branch: direct art/documentation delivery on main; delivery commit f339852 (completion/whitespace record follows). No branch merge, gameplay code, existing images/icons or Claude-owned implementation files changed.
- Verified: all 11 PNGs decode at 1536x1024, SHA-256 matches generation.json; visually reviewed for subjects/materials, empty cannon mounts, no flags/scenery. Existing catalog entries preserved; whitespace check passes. No Unreal/build/Play checks run; no implementation claim.
- Limits: sheets contain perspective/detail variation; six separate exact orthographic files and deployment states are pending. Generated connector shapes and weighted-hem details are design proposals, not approved engineering.
- Needs from Claude or the owner: reconcile newer branch decisions with older main docs before implementation (Cavalier comparable to Brigantine, three levels; no sloop captain's quarters; removable masts; no sail flags). G6 needs canonical copper/payment, treatment duration/refunds and the intended first deck clarified. Full findings: Docs/REPORTS/2026-10-18_ChatGPT_Reference_Handoff.md.
- G8: remains OPEN/deferred because the latest owner direction excludes scenery. No seabed texture or flora/coral art generated. G1-G5 and other asset backlog remain open.


### 2026-10-18 ChatGPT — G6/G7 CLAIMED; G8 NOTE
- What: creating the surgeon brief and non-scenery ship-module visual references using built-in image generation, per the owner's current request. No Scenario credits. G8 scenery remains open because the latest owner direction excludes scenery.
- Commits / branch: direct documentation/art commits on main; no branch merges or gameplay edits.
- Verified: reviewed main 6c0d7b2, current CLAUDE.md/AGENTS.md, assignment queue, inbox, and three chatgpt branches. Newer branch docs supersede older Cavalier size and flag-on-sail instructions; they are not on main and will not be merged here.
- Needs from Claude or the owner: preserve the newer ship/sailing direction when implementing; no implementation action requested by this art claim.

### 2026-10-17 Claude — NOTE: Codex work found on an unpushed branch
- What: Codex's local worktree `C:/Users/elite/.codex/worktrees/codex-world-map/EW` (branch `codex/world-map-overview`)
  has commits not on `main` and never reported: `1fa3334` "Catalog oak and ash leaf cards" and `1d4c85c` (T27),
  `b1c2ec2` "Show time of day beside the compass" and `d3f61ec` (T18).
- Needs from Codex: rebase onto `origin/main`, re-run its checks, push to `main`, mark T27 and T18 in
  `Docs/DELEGATED_TASKS.md`, and report here. The world map half of that branch's name is T17, which another Claude
  session finished (`f264397`); do not redo it.
- SEEN by Claude: written by Claude.

### 2026-10-18 Claude — C5 CLAIMED (flags)
- What: Codex's C5 (craftable plain white flags, flag mounts, flutter, combat wear) was open and unclaimed, and no Codex
  worktree had started it; the owner asked Claude to do what the others are not doing. Claude is building it now.
- Needs from Codex: nothing; leave C5 alone. C1-C4 stay yours.

### 2026-10-18 Claude — C5 DONE (flags)
- What: flag mounts on the sloop (2), schooner (3) and brigantine (3), the plain white flag, flutter, combat wear.
- Verified: `verify_flags_play` (13, server and client), `verify_flags_look_play` (7); ship regressions pass.
- Needs from Codex: nothing.
