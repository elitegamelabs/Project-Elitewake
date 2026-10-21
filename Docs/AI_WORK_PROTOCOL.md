# ELITEWAKE — AI work protocol (owner direction, 2026-10-21)

**Scope:** This is the current operational instruction for ChatGPT, Claude, Codex, and Scenario. The owner's latest explicit decision wins over older instructions. Historical task logs and older design records remain useful evidence, not active orders when superseded.

## Immediate milestone
**Exactly five playable islands total: one in each region** — Plains (starter), Winter, Swamp, Desert, Jungle. Build a stable small world, validate gameplay, then consider gradual expansion only with owner approval. The 26-island baseline and 40-island generated layout are historical source work. **Pause** C-WORLD40 and C-WILDLIFE40. Do not delete existing records, assets, maps, save data, or tests as part of the scope change. See [FIVE_ISLAND_RECOVERY_PLAN.md](FIVE_ISLAND_RECOVERY_PLAN.md).

## Work allocation — one active implementer per task
| Agent | Best-use lane | Do not spend credits on |
| --- | --- | --- |
| ChatGPT | GitHub reviews, owner-decision reconciliation, coordination, acceptance criteria, task/PR triage, reference art briefs | Repeated local Unreal launch attempts; claiming Play tests without evidence |
| Claude | Local Unreal Editor, map and .uasset integration, ship meshes, collision, screenshots, Play checks, editor/process diagnosis | Acting as permanent file owner or coordinator of all agents |
| Codex | C++/Python, test fixtures, deterministic generation, runtime bug fixes from reproducible evidence, source-level migrations | Recreating finished features or retrying blocked editor launches without new evidence |
| Scenario | Specific owner-approved import-ready visual assets and source deliverables | Autonomous generation, broad scenery batches, coding, repeated variants without review |

**No permanent file ownership:** any agent may edit a file when explicitly assigned. **Exclusive active task claim:** only one agent implements a particular task at a time; overlapping file changes require an inbox note and coordination before editing.

## Hard rules
1. Before work: fetch latest main, read this protocol, the five-island plan, relevant latest owner decisions, `Docs/VERIFICATION.md`, and the shared inbox. Inspect code and asset reality before trusting task status.
2. One Unreal Editor/build/Play session on the shared PC at a time. Never force-close unidentified processes, delete arbitrary lock files, or overwrite held DLLs.
3. Never commit owner-local `Config/DefaultEditor.ini`; do not discard uncommitted changes.
4. No force-push, destructive reset, broad asset deletion, save-ID changes, automatic PR merges, or changes to owner-approved designs without explicit owner approval.
5. Work on a narrowly scoped branch/PR for cross-system or risky work; avoid unreviewed direct pushes to main. Do not merge without owner approval.
6. Distinguish: source written, offline tests passing, UE build, .uasset saved, native automation passing, multiplayer Play passing, visually owner-approved. Each is a separate claim.
7. If blocked, collect one reproducible diagnostic and stop. No speculative retries, no new unrelated tasks after completion.
8. Scenario defaults to **IDLE**. Generation needs owner approval, an exact asset brief, source/export requirements, and a designated integration owner.
9. Keep `Docs/Delegation/INBOX.md` as a peer log; preserve historical entries. Report commit/branch, what changed, tests and artifacts, blockers, and next owner.
10. Prefer smallest useful task, lowest-cost validation, and no duplicate research. Preserve all already-paid-for work.

## Work queue and dependencies
**P0 — ChatGPT:** maintain coordination docs and reconcile stale authority. Review PR #1 (release automation) and PR #5 (26-island discovery branch) without merging; PR #5 needs redesign for five-island target.

**P0 — Codex (propose only until owner authorizes code change):** inspect current world generator, consumers, map setup, save/discovery IDs, Ports, and wildlife. Propose a reversible five-island selector and regression tests. Do not hard-code arbitrary selections or modify existing saved maps. Identify the exact four regional island keys and Port implications for owner approval.

**P0 — Claude (wait for source/selection handoff):** inspect saved Unreal map and editor state read-only; report what must be rebuilt for the five-island world. Only after owner approval and a backup/snapshot, integrate and Play-verify the small world.

**P1 — Codex/Claude:** finish C1 felled-tree native and two-player Play verification, without revisiting the already-resolved DLL linker lock unless it recurs. Codex fixes defects; Claude runs editor checks.

**P1 — Claude:** establish whether October 20 brigantine rebuild is completed and saved. Do not regenerate ships unnecessarily.

**P2:** review partial C7 features, ship windows, marine wildlife preservation, claims, and release automation individually after five-island milestone stabilizes.

## Mandatory short task preflight
- **TASK:** exact ID and one owner.
- **CURRENT STATE:** inspected code/asset commit and evidence.
- **NEXT ACTIONS:** at most three.
- **DEPENDENCIES:** other agent, editor slot, owner decision.
- **EFFORT:** low / medium / high.
- **STOP CONDITION:** concrete deliverable, test result, or blocker.

**Do not autonomously start another task when this one ends.**
