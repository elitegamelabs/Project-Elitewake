# Elitewake — handover plan for Codex (2026-11-01)

> **Owner, 2026-11-02 ~12:00: "Claude finishes it."** Claude owns finishing the twenty-island rebuild: verification,
> Play checks, walking measurement, captures and the commit. Codex: read-only watching is fine; do not verify, run Play
> checks, open an editor, edit, commit or push in EW_CLEAN until the owner hands it back.


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
  - `779e4d83` first handover (this file, `world_islands.py` and tests, the walking-route check, `run_play_check_once.ps1`).
  - `6ea16acd` 15 ft starter pond, 6–17 minute crossings, walking routes measured.
  - the final handover commit (this update; the controller-icon preview tools in `Scripts/Art`).
- Claude's own working files (notes, scratch scripts, the icon preview) are copied to
  `C:\ELITEWAKE\Claude_Handover_20261101` (see its README.txt). Nothing outside the repo is needed to continue: the direction patch is also in the repo at
  `Scripts/Setup/patches/`.
- Phase 1 (slices 1–6) is committed but **not owner-accepted**. The owner moved on to island work (Phase 2 direction).

## 2. Owner decisions in force (all recorded in CLAUDE.md)

- Visual target: high-definition naturalistic realism (9.1). Elephants realistic and **neutral** (done in code; the realistic
  model is Phase 5 asset work).
- World: **20 islands, 4 per region**, each its own shape and land area; **6–17 minutes to cross each on foot, preferably in every
  direction** (measured in-game, not a diameter); **one village per region** — P1 Starter (Saltreach), W2 Birch Haven, S1 River Isle, D1 Oasis Isle,
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
- Controller icons: in progress, **awaiting owner approval before any import** — section 7.

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
2. Apply the direction patch: `Scripts/Setup/patches/Phase2_NorthPlusY_DesertJungleSwap_from_31e55329.patch` (same file as
   `C:\ELITEWAKE\BACKUP_CURRENT\Patches\...`; if a checkout's line endings make `git apply` refuse the repo copy, use the
   C:\ELITEWAKE copy or add `--ignore-whitespace`)
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
  — 49 tests pass at handover. Python: `python -m unittest discover -s Scripts/Tests -p "test_*.py"` — all 52 pass.
- Editor scripts that delete and recreate assets (terrain re-cuts): run with `-SCCProvider=None` or the git plugin restores
  the old file from git.
- Pushing large LFS changes may need the owner's explicit "push" in Claude's tooling; ask before pushing.
- Play checks: always through `run_play_check_once.ps1` (outside time limit). A runner that fails to load leaves the editor
  idle forever otherwise — that cost an hour once.
- Python-called server RPCs run locally in Play checks; drive clients with `EWEditorVerificationLibrary` key/interaction
  helpers. Escape with no window open ends PIE.
- Commits: one coherent outcome each; message ends with the co-author line the owner's tooling requires; fast-forward push
  only, never force. Map changes push ~1.2 GB of LFS.
- Report to the owner in plain language, post progress while long runs go, and label visual/audio judgements as owner review
  pending.

## 7. Unfinished: controller-button icons (owner request, November 1)

Source: the owner's sheet `C:\Users\elite\Downloads\Glossy Xbox and PlayStation Button Icon Sheet.png` (1774 × 887,
real alpha). **Owner rule: show the plan and wait for approval before importing or replacing game assets.** Plan shown to
the owner; no answer yet. Questions still open: (a) leave out the two Home logo icons — they are cut off at the sheet's
bottom edge (edge alpha 252/249) and are Microsoft/Sony trademarks; (b) where the sheet came from (provenance, licence,
ASSET_LEDGER.csv row) — Sony's △○×□ symbols and both logos are trademarks used under platform guidelines; (c) the
Options override with a neutral fallback.

Done (preview only, nothing imported):
- `python Scripts/Art/extract_controller_icons.py` cuts the 38 icons (19 Xbox, 19 PlayStation) by their own alpha, grows
  each crop until its edges are transparent, names them, checks edges, and writes `Saved/ControllerIconPreview/`
  (icons\, contact_sheet.png, extraction.json). Residual edge alpha ≤ 8/255 is shared haze: fade the outer 4 px at import.
- `python Scripts/Art/preview_controller_prompts.py` renders example prompts at 1920×1080 in-game size
  (`prompt_preview_1080p.png`): 44 px icons read well; R3's label is borderline; at 26 px the D-pad arm vanishes, so the
  hotbar needs ≥ 32 px.
- Names: `T_Icon_Xbox_{A,B,X,Y,DPad_Up,DPad_Down,DPad_Left,DPad_Right,LB,RB,LT,RT,LeftStick,RightStick,LeftStickPress,
  RightStickPress,Menu,View,Home}` and `T_Icon_PlayStation_{Cross,Square,Triangle,Circle,DPad_*,L1,R1,L2,R2,LeftStick,
  RightStick,L3,R3,Options,Create,Home}`. Note: the sheet labels the Xbox stick presses "L3/R3", not Xbox's own naming.

Findings about the game:
- Prompts are plain FText with Xbox letters (`EWArrivalComponent.cpp` PromptFor/TownPromptFor, the build radial and
  debug line in `World/EWBuildComponent.cpp`, `EWHotbarWidget.cpp` GamepadHints, map/dialogue/options hints).
- Device detection is keyboard vs gamepad only (`AEWPlayerController::RecordInputDevice` → `UsesControllerPrompts`);
  nothing distinguishes Xbox from PlayStation; no GameInput or CommonUI plugin is enabled.
- Bindings are positional (FaceButton_Bottom = A / Cross, Left = X / Square, Top = Y / Triangle, Right = B / Circle,
  LeftShoulder = LB / L1), so "hold L1 + D-pad Right" is the same binding as "hold LB + D-pad Right": no remap.

To do once approved (one commit each, tests and 1080p captures):
1. Import into `/Game/Elitewake/UI/Icons/Controller/Xbox/` and `/PlayStation/` (UI texture group, no mips, 4 px edge fade);
   ASSET_LEDGER.csv rows with provenance.
2. A data asset mapping each FKey to its icon per family; prompts look up the key actually bound (BuildComponent's
   ResolveKey, HotbarSlotForKey, the interaction key), never a hard-coded letter.
3. Rich text prompts (URichTextBlock + an image decorator) in the arrival/town prompt, interaction prompt, build radial,
   hotbar hints (≥ 32 px), map/dialogue/options hints. Build prompt: Xbox hold LB + D-pad Right, PlayStation hold L1 +
   D-pad Right, keyboard B; entering opens the radial on parchment (already implemented).
4. Family choice: Options "Button icons: Automatic / Xbox / PlayStation"; Automatic uses device identity if available
   (test GameInput with a real DualSense); unknown → neutral position words ("Left face button") until chosen, so no
   player sees the wrong brand.
5. Tests: every bound key has an icon in both families; families never mix; fallback text when unknown.

## 8. Overnight decisions for the owner's 9 am review (2026-11-01/02)

The owner said: "automatically approve the decisions going forward until i wake up … choose the best option and i'll change it
in the morning if i don't like it." Each decision below can be reversed; say which you want changed.

1. **Rebuild recovery (approved by the owner before sleeping).** `place_animals.py` label NameError fixed; `material_builder`
   now keeps an existing material instead of clearing it (UE 5.8.3 asserts in `DeleteAllMaterialExpressions`). The rebuild
   resumed from the failed step; terrain and grass were not rerun.
2. **Controller family detection.** Windows Raw Input reads each connected pad's maker: Sony = PlayStation; Microsoft or
   any XInput pad = Xbox; anything else = Unknown (plain words such as "Left button", never a guessed symbol). If a Sony pad
   is connected beside an Xbox-style one, PlayStation wins (DS4Windows/Steam show a PlayStation pad as a virtual Xbox
   pad). Checked every 3 s, so plugging in a pad switches the icons within seconds. Why not GameInput/CommonUI: neither
   plugin is enabled; Raw Input needs no new dependency.
3. **Options → "Button icons": Automatic / Xbox / PlayStation** (default Automatic), saved with the other user settings.
4. **Where icons show:** the arrival and Saltreach prompts, the interaction prompt ("Square: Drink fresh water"), the
   hotbar slot hints (32 px) and its LB/L1 modifier, and a new build hint right of the hotbar on foot: "Build: hold LB +
   D-pad Right" / "hold L1 + D-pad Right" / "Build: B". The build dial's middle text uses the pad's names as words
   (RB / LB+RB, B: close → R1 / L1+R1, Circle: close) — words, not pictures, because it is drawn in Slate outside UMG;
   icons there are a small follow-up if wanted. The keyboard shows keyboard keys (C / Z, Esc).
5. **Icons:** 36 of the 38 on the sheet imported (`/Game/Elitewake/UI/Icons/Controller/...`); the two Home logos left out
   (cut off at the sheet edge, and they are platform logos the game never needs). Each keeps its own shape, longer side
   256 px, outer 4 px faded. Source PNGs in `Art/UI/ControllerIcons/`.
6. **Rights:** ASSET_LEDGER row EW-UI-CTRL-001 marks the sheet's source and licence UNKNOWN — please record where it came
   from. Xbox/PlayStation button symbols are trademarks: fine for development, needs a trademark/platform-terms check
   before any public release.
7. **Cave spiders** (the animals Play check's known failure): they were lifted by a fixed 25 cm but their body radius is
   60 cm, so their feet sat 35 cm under the floor. `add_spiders.py` now lifts by the real radius and was rerun alone.
8. **North fix follow-ups:** three Play checks (Saltreach arrival, voyage ready, sail trim) still worked out bearings with
   the old north and failed by exactly 90°; they now use north = +Y like the game.
9. Three older checks that expect "X: …" now pin the Xbox names for the check only (not saved), so they pass whatever pad
   is plugged in.

## 9. RESUME HERE (kept current overnight; owner: "if you run out of credits create a handoff for codex")

Committed locally (not pushed; push only when the owner says "push"):
- 35203c4f world rebuild with north at +Y, rebuild fixes, spider lift, bearing fixes in three checks.
- the next commit: Xbox/PlayStation detection and button icons (section 8).

Verified tonight on the rebuilt map: EWEditor builds; automation 51/51; Python 51/51. Play checks PASS: arrival,
Saltreach arrival, voyage ready, first voyage, animals (second run; the first saw only 3 calm animals near the start, none
walking in 14 s — the check's sample is small), elephant, sail trim, build mode, options (with the Button icons row),
hotbar (no starter kit), capture_controller_icons (keyboard / Xbox / PlayStation words and icons, no mixing; pictures in
Saved/Screenshots/ControllerIcons, owner visual review pending). Not runnable here: verify_berry, verify_hand_gathering,
verify_water (and verify_food) are written for the retired Lvl_M5PickupTest map — port them to Coastal or retire them.

Next, if continuing: nothing is blocked. Owner review at 9 am of section 8; a real DualSense / Xbox pad test on hardware
(the Raw Input path has only been exercised with no pad connected); then CLAUDE.md Phase 2 work as section 4 lists.

## 10. Phase 2 twenty-island world — RESUME HERE (2026-11-02)

Owner (2026-11-02): "work on the next milestone or phase". Done in plain Python, NOT committed, NOT yet in the map:
- `Scripts/Setup/world_layout.py`: 20 islands (4 per region; keys = world_islands.py). Plains: Starter unchanged plus
  Plains2-4 on the diagonals ~4.5 km out; each other region's four in its direction (REGION_SLOTS: village island 5.3 km
  out, flanks ~9 km, far island ~11 km). Sizes stepped so every island has its own land area. Ports only on the villages
  (Starter, Winter2, Swamp1, Desert1, Jungle1), harbours facing the centre. `_organic(..., spread=True)` spreads hills
  round the ring; the Starter's west half keeps `spread=False` so its ground is unchanged (its height tests pass).
- `Scripts/Setup/world_terrain.py`: terrain plans of 2-4 raised shapes on a ring 35-70 % out, ridges running round the
  island; no central mountain. Winter tops ~230-275 m, Jungle ~140-245 m, Desert 60-85 m, Plains 35-45 m.
- `Scripts/Setup/estimate_walking_times.py` (new): quickest walkable path (10 m grid, 38 degrees, 4.5 m/s) on the same
  routes as `measure_walking_routes_play.py`. All 19 generated islands 6-13 min both ways; calibrated within ~1 min of the
  November 1 in-game walks. The in-game walker steers straight and gets stuck on hills: next, make it follow the
  estimator's path (`walk_time` returns it) so the in-game number is a real measurement.
- `Scripts/Setup/wildlife_distribution.py` + `place_animals.py`: each island's planned species that exist today
  (world_islands), 150 m / 250 m clear of spawn, dock and villages. Seven islands have no existing species yet.
- Tests: `Scripts/Tests/test_twenty_islands.py` (renamed from test_five_islands), wildlife tests rewritten; 55/55 pass.
  `Content/Elitewake/Data/BuildZones.json` re-exported (103 zones) — it describes the NEW world, so commit it only with
  the rebuilt map.
- Picture: `Saved/TwentyIslandLayout.png`.

OWNER APPROVED the rebuild 2026-11-02 ("Yes, rebuild"), including overwriting the 15 matching old meshes. Rebuild
started ~10:55 local: `Saved/Logs/TwentyIslandRebuild.log`, progress in `Saved/WorldRebuildResult.json` (expect ~6-7 h;
if it stops, resume with EW_REBUILD_FROM=<failed step>). The previous five-island result is kept as
`Saved/WorldRebuildResult_fiveisland_final.json`. `measure_walking_routes_play.py` now follows the estimator's path.
Background (was the question): it overwrites 15 old October-22 island meshes whose names match new keys
(`SM_Island_{Plains,Winter,Swamp,Desert,Jungle}{2,3,4}_v1`, CLAUDE.md 3 says not to reuse them without approval); the
`...5-8` meshes stay untouched. Then: rebuild_world.py from the start with `-SCCProvider=None` (hours; terrain for 20
islands), automation, Play checks, in-game walking measurement, captures, one commit.

### 10a. Grass ran the graphics card out of memory (2026-11-02, 18:25)
First run: terrain (2 h 50 min), caves, webs, landmarks passed and were saved (map saved 13:47). build_grass at the old
densities tried ~24 million instances; D3D12 E_OUTOFMEMORY on an 804 MB buffer (RTX 4070, 12 GB) and the editor sat idle
on the error. Fix in `build_grass.py`: Starter keeps 7 clumps/m2 (unchanged), other Plains 1.0, Jungle 0.35, understory
x0.25, about 6.9 M in all; MAX_INSTANCES = 9 M stops it before the card fills. Stuck editor closed; rebuild resumed
19:02 with EW_REBUILD_FROM=build_grass (log `Saved/Logs/TwentyIslandRebuild2.log`; first run's result kept as
`Saved/WorldRebuildResult_twenty_run1.json`). Later: stream grass per island (World Partition) so density can rise.
- 20:22: the second grass run stopped on its own budget check (9.59 M at Jungle2): new Plains islands are open grassland,
  ~2 M clumps each at 1.0/m2. Measured with spots' own rules on a 2 % sample (scratch script): densities now Plains 0.4,
  Jungle 0.25, understory x0.2, Starter 7 -> 6.76 M total. Third run from build_grass started 20:37
  (`Saved/Logs/TwentyIslandRebuild3.log`); run 2's result kept as `Saved/WorldRebuildResult_twenty_run2.json`.

### 10b. Minimum PC (owner, 2026-11-02)
"I have a geforce 1660 super ... that will need to be able to at least run and test the game on." GTX 1660 Super = 6 GB
VRAM, no ray-tracing hardware. Target 1080p Low within about 4.5 GB VRAM. Next slice after the twenty-island commit:
World Partition streaming + HLOD, grass only near the player, Foliage detail wired to plant counts, packaged build measured
on that card. CLAUDE.md should record this (Phase 6 target machine) when the guide is next edited.

### 10c. Rebuild done; verification state (2026-11-03 ~01:00)
Rebuild complete (all 23 steps; grass 6.8 M at measured densities). Fixed on the way: add_spiders/build_plains_threat
narrowed build_animals.ANIMALS in the shared editor process (now importlib.reload), committed 2fa63cc9 for a unity-build
clash in EWControllerIcons.cpp (not pushed). Play runner now waits up to 6 min for Play to start (EW_PLAY_START_WAIT);
the 2.1 GB map takes minutes to load per Play world. Results: map scan passes except cave spiders outside the Swamp
(owner decision pending: October "spiders in every cave" vs November "species stay in region"); animals placement now
enforces the 200 m / 15 % rule. Play: arrival, Saltreach arrival, voyage ready, elephant, directions PASS. Two-player Play
runs at 2-5 fps (three world copies on one GPU); single player ~30 fps in the editor (spawn, Saltreach, sea). first_voyage
and animals failed on timing at that speed: their frame-counted steps now get 30 s, animals watched 30 s. Island terrain
check updated for 20 islands. Running: island terrain, build mode, walking routes (Saved/TwentyChecks2.log).
