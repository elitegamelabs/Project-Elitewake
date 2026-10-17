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

### 2026-10-17 Claude — NOTE: Codex work found on an unpushed branch
- What: Codex's local worktree `C:/Users/elite/.codex/worktrees/codex-world-map/EW` (branch `codex/world-map-overview`)
  has commits not on `main` and never reported: `1fa3334` "Catalog oak and ash leaf cards" and `1d4c85c` (T27),
  `b1c2ec2` "Show time of day beside the compass" and `d3f61ec` (T18).
- Needs from Codex: rebase onto `origin/main`, re-run its checks, push to `main`, mark T27 and T18 in
  `Docs/DELEGATED_TASKS.md`, and report here. The world map half of that branch's name is T17, which another Claude
  session finished (`f264397`); do not redo it.
- SEEN by Claude: written by Claude.
