# ELITEWAKE team charter (owner, October 22, 2026)

**We are one team: the owner, Claude, Codex, ChatGPT, Grok and Scenario. Everybody works on the project freely.** This charter is the shared rulebook. The owner's
latest message always wins over anything here.

## 1. No locks, no claims, no ownership
- **Nobody locks, reserves or owns anything**: no file, folder, system, asset, task, branch or API. Any teammate may edit anything, at any time.
- Older text that says an agent "owns", "reserves" or "claims" something (task files, `DELEGATED_TASKS.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) is superseded. A line such
  as `CLAIMED (Codex, date)` is only a **courtesy notice that someone is working on it**. It blocks nobody; if you want the same task, say so in the log and work with
  them, or take it over if they have stopped.
- Do not add lock files, "do not touch" notes, ownership tables or reservation lists. If you find one, remove it and say so in the log.
- **The one real constraint is physical, not a lock:** two Unreal editors cannot safely open this project at once on the shared PC. Before starting an editor, build or Play
  check, look for `Saved/EditorLock.txt` (a notice, not a claim): if it is fresh, do other work or wait; if it is stale (over 90 minutes, no editor process), delete it and go
  ahead. Remove your note when your run ends.
- Pull before you start, keep commits small, and put work on `main` (or a branch the others can see). Branches nobody can see do not exist for the team.

## 2. Logs: everyone writes down what they did
- **Every session** adds an entry at the top of `Docs/Delegation/INBOX.md` (newest first): what you did, the commits, what you **verified and how**, what you could not verify,
  and what you suggest next. Keep status honest: designed, coded, built, integrated and verified in play are different things.
- Claude keeps a manager's log per working day in `Docs/REPORTS/<date>_Claude_Manager_Log.md`: the state of every task, what was reviewed, what was corrected.
- Record owner decisions in `Docs/OwnerDecisions/` the moment they arrive, in the owner's words, with the date.

## 3. Tasks: write them down, pick them up, hand them on
- Open work lives in the task files: `Docs/DELEGATED_TASKS.md` (shared), and a per-agent list in `Docs/Delegation/` (`CODEX.md`, `CHATGPT.md`, `GROK.md`, `SCENARIO.md`).
  Claude writes new tasks there; **any teammate may add a task** for anyone, including themselves.
- A task says what to do, why (the owner's words), what done looks like (the check that proves it) and where to look. Status words: `OPEN`, `IN PROGRESS (who, date)`,
  `DONE <commit>`, `BLOCKED (why)`.
- Stuck, or unsure what the owner wants? Write the question in the inbox for the owner and carry on with something else.

## 4. Claude manages: review and correction
- Claude acts as the team's manager. After anyone pushes, Claude reads the work, runs its check, and writes the verdict in the manager's log: **accepted**, or **corrected**
  (with what was wrong, the fix, and the commit). Corrections are made directly in the code or as a task for the author when that author is the right one to learn from it.
- Everyone may review everyone. If you see a mistake in another teammate's work, fix it or write it up; do not wait for permission, and do not argue in the code.
- Claude does not take the owner's decisions: design questions go to the owner; anything the owner delegated is written down as `DECIDED (delegated)` and stays reversible.

## 5. Quality rules that apply to everyone
- Reuse working systems; inspect before you change; functional, not placeholder. Keyboard/mouse **and** controller for every interaction.
- Never claim a feature is complete without a build **and** a Play check or native test that proves it. Say what you did not test.
- Do not delete files for good without the owner's approval; move unused assets to quarantine (`C:\ELITEWAKE\QUARANTINE`) instead and log them. Never force-push or rewrite
  shared history. Do not merge pull requests without the owner's approval.
- Preserve approved gameplay and other people's work. Do not overwrite a newer version of a file you have not read.

## 6. Who does what best (a guide, not a fence)
| Teammate | Usually good at |
|---|---|
| Owner | Vision, every design decision, playtesting, final say |
| Claude | Unreal C++ and editor automation, Play checks, UI systems, review and management |
| Codex | Code, native tests, Python verification, packaging, build and CI work |
| ChatGPT | Design write-ups, reference sheets, research, catalogues, reviewing |
| Grok | Research, design analysis, balance and lore drafts, second-opinion review of code and plans (see `Docs/Delegation/GROK.md`) |
| Scenario | Image, audio and 3D generation, run by Claude from the queue |
Anyone can do anything on this list; it only says where to look first.

## 7. Handoff before you run out of usage (owner, October 22)
Every model, including Claude, must hand its work over **before its usage credits run out**, not after:
1. **Stop at about 90% of your limit** (or sooner if a task would not finish). Do not start a new piece of work you cannot finish.
2. **Close out everything you have open**: quit any Unreal editor or build you started and delete your `Saved/EditorLock.txt` note; stop background jobs; save and commit your files; push to `main` or a visible branch.
3. **Write a handoff entry** at the top of `Docs/Delegation/INBOX.md` titled `HANDOFF (<you>, <date>)`: what you were doing, exactly where you stopped, the files and commits, what is verified and what is not, the commands to resume, and the next three steps. Put unfinished tasks back to `OPEN` in the task files with a note of how far they got.
4. **Name who should continue** if you can (the next model with credits), but any teammate may pick it up.
**Picking up:** at the start of every session, read the top of `Docs/Delegation/INBOX.md` first. If there is a `HANDOFF` entry nobody has marked `PICKED UP (<who>, <date>)`, **continue that work before starting anything new**, mark it picked up, and carry on from the stated stopping point. If you find an editor still running or a stale lock note from someone who has stopped, close it (check the editor process first) and tell the team in the inbox.
