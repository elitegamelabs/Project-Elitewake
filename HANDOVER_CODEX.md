# Elitewake — handover plan for Codex (2026-11-01)

The owner asked for this handover on 2026-11-01. **CLAUDE.md is still the one production authority**: read all of it first
(it supersedes this file wherever they differ; its section 1.2 "no agent handoffs" rule was overridden by the owner for this
pass-over only). This file only says where the work stands and what comes next. Delete it once the work below is picked up.

## 1. State at handover

- Repository: `C:\UnrealProjects\EW_CLEAN`, branch `main`, pushed to GitHub `elitegamelabs/Project-Elitewake`. Engine
  UE 5.8.3 (CL 58210709). Work tree clean; no Unreal process running; no git lock files.
- Commits today, newest last:
  - `896420c8` guide: naturalistic realism, island and swamp direction, controller layout, graphics tiers.
  - `3a03590c` controller hotbar + Build Mode controls.
  - `f1a54896` guide: the twenty-island world, villages, wildlife plan (CLAUDE.md 5.7).
  - `9d6e41ea` neutral elephants that defend themselves.
  - `bc2a9643` graphics quality tiers that stay fair.
  - the handover commit (this file, `world_islands.py` and its tests, the walking-route check, `run_play_check_once.ps1`).
- Phase 1 (slices 1–6) is committed but **not owner-accepted**. The owner moved on to island work (Phase 2 direction).

## 2. Owner decisions in force (all recorded in CLAUDE.md)

- Visual target: high-definition naturalistic realism (9.1). Elephants realistic and **neutral** (done in code; the realistic
  model is Phase 5 asset work).
- World: **20 islands, 4 per region**, each its own shape and land area; **15–20 minutes to cross each on foot** (measured
  in-game, not a diameter); **one village per region** — P1 Starter (Saltreach), W2 Birch Haven, S1 River Isle, D1 Oasis Isle,
  J1 Waterfall Basin. Island-by-island specialties and wildlife: CLAUDE.md 5.7, as data in `Scripts/Setup/world_islands.py`.
- Directions: Winter north, Swamp south, Desert east, Jungle west. North must become world +Y and east −X; **Desert and Jungle
  swap sides** (owner choice). That code exists as a saved patch, not yet applied (section 4).
- Swamp: one coast-to-coast navigable river with tributaries, separate ponds; sized for the Cavalier, which is **not built**
  (owner will supply `cavalier.png`); until then a large provisional river.
- Sulfur: **Desert only**.
- Wildlife: no design cap, technical controls only; species stay in region; mixes differ by island; 150 m / 250 m clear of
  landings and villages. Tame caps 25 per player / 75 per Company are separate and unchanged.
- Controller: hotbar D-pad L/U/R/D = slots 1–4, LB+X/Y/B/A = 5–8, LT+D-pad does nothing. Build Mode: B (keyboard) or
  hold LB + D-pad Right (on foot); radial opens at once on parchment; B closes the radial, B again leaves; R3 demolish;
  RB / LB+RB material. Done and verified.
- Graphics tiers: visuals only, gameplay identical; done (`Config/DefaultScalability.ini` pins view distance and plant density).
- Queued after the islands: the map screen shows a **deep blue ocean** around the islands.
- Inland water (owner, in feet): ponds 15 ft deep, lakes 50 ft deep (`world_islands.POND_DEPTH_CM`, `LAKE_DEPTH_CM`). The
  starter spring pond is done (flat floor at 15 ft, 4 m grid). Re-cut one island's ground with
  `EW_TERRAIN_ISLANDS=Starter` and build_coastal_terrain.py, **with `-SCCProvider=None`**: the editor's git plugin
  otherwise restores the replaced mesh from git.
- Controller icons: the owner's sheet (`C:\Users\elite\Downloads\Glossy Xbox and PlayStation Button Icon Sheet.png`)
  was extracted to a preview only; a plan awaits owner approval (asset names, rich-text prompts, family detection with
  an Options override, trademark/provenance questions). Do not import until approved.

## 3. Walking-route measurement (done 2026-11-01)

`Scripts/Verification/measure_walking_routes_play.py`, two routes per island (long axis and across, 20 m inland ends),
walking speed 5 m/s, game time; a route still short at 30 min is blocked.

| Island | Long axis | Across |
|---|---|---|
| Starter (Plains) | 6.65 min, 1980 m walked / 1985 m straight | 6.2 min (swims the pond) |
| Winter1 | blocked (central 360 m mountain) | blocked |
| Swamp1 | 9.79 min | stuck at its start point: measurement fault, re-measure |
| Desert1 | blocked (central plateau) | 5.64 min |
| Jungle1 | blocked (central 261 m hill) | 6.42 min |

Owner target now: **6–17 minutes across, preferably in every direction** (replaces 15–20). Passable ground runs about
4–5 m/s straight-line, so today's 1.3–2.2 km islands already fit; what fails is the impassable central relief. Propose
islands of roughly today's size with several passable hills instead of one mountain; the big World Partition move is
probably unnecessary.

## 4. Next steps, in order (each its own commit; owner approval before terrain changes)

1. Re-measure Swamp1 across from a clear start; get the owner's decision on island sizes (section 3).
2. Apply the direction patch: `C:\ELITEWAKE\BACKUP_CURRENT\Patches\Phase2_NorthPlusY_DesertJungleSwap_from_31e55329.patch`
   (`git apply --check` first; it was made against 31e55329 and later commits touched none of its files except CLAUDE.md,
   so drop its CLAUDE.md hunk — the guide already records north = +Y). Rebuild, run the automation suite.
3. Build the 20-island layout in `Scripts/Setup/world_layout.py` from `world_islands.py` (keys there), keep the Starter
   island and Saltreach exactly where they are, update `Scripts/Tests/test_world_layout.py`, and regenerate the world with
   `Scripts/Setup/rebuild_world.py` (rendering editor, `-ExecCmds="py …"`; read its step list first — the Phase 1 scripts
   after the world steps restore Saltreach, the arrival and the yard's sloop). One island at a time, Plains first (CLAUDE.md
   Phase 2), with captures and the 5.7 acceptance checks.
4. Hillside / cliff-shelf building: today a foundation is refused above 2.5 m of ground variation (`max_slope_rise` in
   `world_buildzones.py` / `Content/Elitewake/Data/BuildZones.json`). Add supported foundations and terrain-marked shelves.
5. Swamp river (CLAUDE.md 5.5), provisional width from the Brigantine (8.4 m beam, 2.3 m below waterline, ~18.5 m masts):
   ≥ ~20 m on straights, wider bends, ≥ ~4 m deep; re-verify when the Cavalier exists.
6. Wildlife by habitat across the 20 islands (CLAUDE.md 5.6–5.7), new resources/items as each island needs them.
7. Map screen deep-blue ocean.
8. Phase 5 asset work: realistic people, animals (elephant first), flora, villages, ships — via the licensed intake.

## 5. Known defects (not caused by today's work)

- `verify_food_play.py` fails at its first step (needs read 100, it set 50): written for the old `Lvl_M5PickupTest` map and
  teleports to the world origin; needs tracing in the editor.
- `verify_animals_play.py` fails at step 0: five cave spiders stand 35 cm above their cave floors (map placement).
- `verify_anchor_chain_play.py` and `verify_small_craft_play.py` fail on the committed map (no chain links drawn on the
  client; no raft/dinghy placed).
- Graphics Low tier: no sun shadows and Lumen GI off, so shade reads very dark — owner visual review pending.
- 35 unused October-22 island meshes in `Content/Elitewake/World/Meshes/Islands` (Desert2–8 etc.): do not reuse or delete
  without owner approval.

## 6. How to work here (from experience today)

- Build: `"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" EWEditor Win64 Development "C:\UnrealProjects\EW_CLEAN\EW.uproject" -WaitMutex -NoHotReloadFromIDE`
  (never while an editor is running).
- Automation: `UnrealEditor-Cmd.exe EW.uproject -ExecCmds="Automation RunTests Elitewake;Quit" -unattended -nullrhi -nosplash`
  — 49 tests pass at handover. Python: `python -m unittest discover -s Scripts/Tests -p "test_*.py"` — 49 pass.
- Play checks: always through `run_play_check_once.ps1` (outside time limit). A runner that fails to load leaves the editor
  idle forever otherwise — that cost an hour once.
- Python-called server RPCs run locally in Play checks; drive clients with `EWEditorVerificationLibrary` key/interaction
  helpers. Escape with no window open ends PIE.
- Commits: one coherent outcome each; message ends with the co-author line the owner's tooling requires; fast-forward push
  only, never force. Map changes push ~1.2 GB of LFS.
- Report to the owner in plain language, post progress while long runs go, and label visual/audio judgements as owner review
  pending.
