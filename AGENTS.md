# AGENTS.md — Codex's brief for Elitewake (November 8 – November 11, 2026)

The owner (Elite Game Labs) has handed this project to Codex from **November 8 until Wednesday, November 11, 2026**, while
Claude's weekly usage is spent. Claude resumes afterwards and will review every commit made in between.

**Read first, in this order:** `CLAUDE.md` (the rulebook), `FUTURE_IMPLEMENTATIONS.txt` (the work list; its Part 7 ends with
the 2026-11-08 HANDOVER note), then `FEATURE_EXPANSION_PLAN.txt` for the design of any feature you pick up. Where `CLAUDE.md`
says "Claude", read it as whoever is working; its "one Claude workload, no Codex" rule is set aside by the owner for this
period. The owner's newest instruction outranks every file.

## 1. What the owner authorizes (the same standing permissions Claude had)

The owner said: *"auto approve, push, decide, until usage runs out"*. Within this repository you may, without asking:

- Read, write and refactor source, scripts, config and Data Assets; add files; run Python and PowerShell.
- Build the editor and game targets; run the editor, Play checks and automation tests; take screenshots.
- Run setup scripts that add or change content **incrementally** (one script, the islands it touches).
- Commit each finished, tested feature on `main` and push with `python Scripts/Release/push_github.py`.
- Make design decisions inside an approved feature: pick tuning values, write them down as tuning, and say so.

Still needs the owner's explicit yes (ask, then wait):

- Packaging or publishing an exe / playtest build (the owner asks for these by name; then zip and compress them as
  `Scripts/Release/publish_playtest_setup.py` does).
- A full world rebuild (`rebuild_world.py` without `EW_REBUILD_ONLY`), or anything that clears and re-places the world.
- Deleting assets, folders or saves; anything irreversible; anything outside `C:\UnrealProjects\EW_CLEAN` except adding a
  dated copy beside the others in `C:\ELITEWAKE`.
- New third-party assets, plugins or paid services; anything public (the main repo is private and stays private).

Never: force-push or rewrite history; use Git LFS; commit `Content/__ExternalActors__` (it stays local; copy it to
`C:\ELITEWAKE\WorldActors_<date>` after world changes); edit `Config/DefaultEditor.ini`; enter passwords or tokens (the owner
signs in to GitHub, Epic and Fab himself); commit `Content/Elitewake/Characters/MetaHumans` or `.../Survivors` (held back on
purpose); run two Unreal editors on the project at once.

## 2. How to work here (what has been learned the hard way)

- **Build:** `"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" EWEditor Win64 Development "C:\UnrealProjects\EW_CLEAN\EW.uproject" -WaitMutex -NoHotReloadFromIDE`
  (and the `EW` target before each commit: it catches unity-build clashes the editor build misses).
- **Python tests:** `python -m unittest discover -s Scripts/Tests -p "test_*.py"` (90 tests, 1 skipped, must pass).
- **Play checks:** `powershell -File Scripts\Verification\run_play_check_once.ps1 -Check <file> -Result <Name>.json -Players 1|2 [-Standalone 1] -Kit 1 -Timeout 600`.
  Results land in `Saved/<Name>.json`. Two players = listen server plus one client.
- **Automation tests:** `UnrealEditor-Cmd.exe EW.uproject -ExecCmds="Automation RunTests Elitewake.<Group>;Quit" -unattended -nullrhi -SCCProvider=None`.
- **Setup scripts in the editor:** set `EW_QUIT_WHEN_DONE=1`, then `UnrealEditor.exe EW.uproject -SCCProvider=None -unattended -ExecCmds="py C:/UnrealProjects/EW_CLEAN/Scripts/Setup/<script>.py"`
  (an ABSOLUTE path; relative paths fail). Always `-SCCProvider=None`, or the 22,000 actor files stall the start.
- **Server requests from editor Python run on the client, not over the network.** In two-player checks drive the real UI
  (`lib.send_verification_ui_key(client, 'Enter')`) or a C++ verification helper, never a raw `Server...` RPC from Python.
- `HighResShot` leaves the interface out; use `Shot showui filename="..."`. Two-player screenshots capture the wrong
  window; take pictures in a one-player run.
- In Python, `USlider::SetValue` fires `OnValueChanged`; bool properties named `bX` read as `get_editor_property('bX')`.
- Unity builds: no file-scope `using namespace`.
- PowerShell's `[IO.File]` calls resolve relative paths against .NET's own current folder, not `cd`: always pass full paths.
- Status words (CLAUDE.md 1.5): call nothing "Verified" unless a check ran and passed; visuals and audio stay "Owner visual
  review pending" / "Owner audio audition pending".
- One feature per commit; update `FUTURE_IMPLEMENTATIONS.txt` (move the item to Part 7 with its commit and evidence) in the
  same commit. End commit messages with a co-author line for yourself.

## 3. The game plan, in order (stop at Wednesday; leave the tree clean and pushed)

Each step: read the item in `FUTURE_IMPLEMENTATIONS.txt` Part 8 and `FEATURE_EXPANSION_PLAN.txt`, build the smallest
working slice, add a Play check, run it, run the Python tests and both builds, record it, commit, push.

1. **Armor evidence: DONE by Codex on November 8** (commits 567193d5, 5d107a18: two-player check 16/16, hosted save and
   restore 15/15, Hands/Feet rows hidden, image rights confirmed by the owner, playtest build from 9f041a33 published).
   Left for armor: a real network disconnect and rejoin with armor on (do it if a two-process check exists that can).
0. **FIRST: finish the sailing lessons (64).** Claude stopped mid-check on November 8; read the 2026-11-08 STOPPED HERE
   entry at the end of FUTURE_IMPLEMENTATIONS.txt for the exact state and next steps. Also done since this brief was written:
   the world's day count in the logbook, captain's notes at the harbor master, and the sextant (09, first part).. **Wave A, 60 — remappable controls.** Use Enhanced Input user settings (player-mappable keys) behind the existing
   Options "Controls" page (`EWOptionsWidget`, `EWControlsList.h`): pick a row, press a key or button, warn on a clash,
   save, "Reset to defaults" restores the owner's layout in CLAUDE.md 6.5. Extend `verify_controller_only_play.py` and
   `verify_options_menu_play.py`. Keyboard and controller both.
3. **Wave A, 09 — nautical instruments.** A held compass and a sextant (items, held meshes may be placeholders) that show a
   heading and a latitude reading in a small HUD panel; the world's north is +Y, east is -X (`World/EWNorth.h`).
4. **Wave A, 64 — optional sailing tutorial.** Reuse the arrival prompt system (`UEWArrivalComponent`, one prompt at a
   time): helm, sails, wind, anchor, cargo, damage; skippable and replayable from Options or the Journal.
5. **Wave A, 65 — optional combat tutorial** in the same way (punches, stamina, the cannon's four-step load).
6. **Logbook leftovers (13):** a saved day counter in the world (the clock keeps only the hour; `UEWDayNightSubsystem`,
   `AEWSkyClock`) so log lines read "Day 3, 14:05"; then a captain's own note, typed at the helm or the harbor master.
7. If time remains: the Wave B items in Part 8, in their listed order.

Not yours this week: production 3D garments for the armor (needs art), the pirate MetaHuman skin (needs Epic/Fab access),
any further exe or playtest publish unless the owner asks again, and any world rebuild.

## 4. Before you stop (Wednesday)

- `git status` clean apart from the two held-back MetaHuman folders; everything pushed with `push_github.py`.
- Add a dated "CODEX HANDBACK" entry at the end of `FUTURE_IMPLEMENTATIONS.txt` Part 7: what you finished (commits and
  checks), what is half done, anything you changed in how the project works, and every assumption you made.
- No editor, build or Play check left running.
