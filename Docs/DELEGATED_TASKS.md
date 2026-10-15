# Delegated tasks (for ChatGPT / Codex)

Owner direction, October 15: Claude keeps this queue full of work it is **not** doing, so another agent can take
it in parallel. Claude adds to it as work comes up; each task is self-contained. Read this whole header before
taking a task.

## How to work this queue

1. `git fetch && git pull --ff-only` first. Two agents (and the owner) commit to `main`.
2. **Claim** a task: change its status to `CLAIMED (ChatGPT, date)` in this file and push that one-line change
   before starting, so Claude does not pick it up.
3. When finished: set the status to `DONE <commit>` and write what you verified (and what you could not) under the
   task. If you stop part-way, set `OPEN` again and say where you got to.
4. Never edit files listed under **Claude is working on** below. If a task needs one, leave a note here instead.

## Shared rules (from the owner; these override convenience)

- Do not stage or revert `Config/DefaultEditor.ini`. Do not force-push or rewrite history.
- One small system at a time: build, test in Play, checkpoint. **Compiling is not proof it works.** Every gameplay
  change needs a Play check (see `Scripts/Verification/run_play_check.py`) or a native automation test, and the
  result recorded in `Docs/VERIFICATION.md`.
- Never commit credentials, API keys or download keys.
- Missing balance values stay **unresolved** rather than invented. Working numbers are labelled *tuning*; a choice
  made on the owner's behalf is recorded as "DECIDED (delegated)" in the doc it affects. Owner questions are listed,
  not guessed.
- Generated images are references, not final art.
- Authority order when documents disagree: the owner's latest message, then
  `Docs/WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md`, then `Docs/DESIGN_REFERENCE.md`, then older notes.
- Match the surrounding code: comment density, naming, idiom. Setup scripts are re-runnable (`Scripts/Setup/*.py`,
  run inside the editor); verification scripts live in `Scripts/Verification/`.
- Commit messages describe the player-facing change; record the commit hash in the docs in a follow-up commit, as
  the history shows.

## One Unreal Editor at a time (both agents)

The project has one editor and one set of asset files, so only one agent may run Unreal (setup scripts, Play
checks, native tests, builds) at a time. Before launching `UnrealEditor.exe`, `UnrealEditor-Cmd.exe` or `Build.bat`:
1. If `Saved/EditorLock.txt` exists and was written less than 90 minutes ago, wait and look again later (it names
   who holds it and why).
2. Otherwise write `Saved/EditorLock.txt` with one line: `<agent> <UTC time> <what is running>`.
3. Delete it when your run has exited (and make sure the editor process has quit). A lock older than 90 minutes is
   stale and may be removed.
`Saved/` is not tracked by git; this file is only for coordination on this PC.

## Useful facts

- Engine: Unreal 5.8 at `C:\Program Files\Epic Games\UE_5.8`. Project: `C:\UnrealProjects\EW\EW.uproject`.
- Build: `"C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" EWEditor Win64 Development -Project="C:/UnrealProjects/EW/EW.uproject" -WaitMutex -NoHotReloadFromIDE` (close the editor first).
- A Play check: set `EW_PLAY_MAP`, `EW_PLAY_CHECK` (absolute path), `EW_PLAY_RESULT` (file in `Saved/`),
  optionally `EW_PLAY_PLAYERS` (default 2 = listen server + client), `EW_PLAY_STANDALONE=1`, `EW_PLAY_TIMEOUT`,
  `EW_PLAY_WINDOW=1280x720`; then launch
  `UnrealEditor.exe EW.uproject <map> -unattended -nosplash -ExecCmds="py C:\UnrealProjects\EW\Scripts\Verification\run_play_check.py"`.
  Launch from PowerShell (Git Bash rewrites `/Game/...` values).
- Native tests: `UnrealEditor-Cmd.exe EW.uproject -unattended -nop4 -NullRHI -ExecCmds="Automation RunTests Elitewake" -TestExit="Automation Test Queue Empty" -log`.
  Known baseline: 28 pass, 1 known failure (the title's `RoutedKeyboardMouseAndWheel` input test under NullRHI).
- Maps: `/Game/Elitewake/Maps/Lvl_CoastalPlayground` (the playable world), `/Game/Elitewake/Maps/Test/Lvl_ShipsTest`
  (ships, cannons), `/Game/Elitewake/Maps/Lvl_M5PickupTest` (inventory/crafting fixtures), `/Game/Elitewake/Maps/Lvl_Title`.
- Python editor scripting runs server RPCs locally; drive gameplay in checks through
  `EWEditorVerificationLibrary.send_verification_gameplay_key` / `send_verification_ui_key` (real input).

## Claude is working on (do not edit these)

- **The five-region world rebuild** (owner direction of October 15: Plains centre with the starter island, Winter
  north, Swamp south, Desert east, Jungle west, at least five islands each, 800–2,000 m sea gaps). Claude owns the
  island layout, terrain, seabed, ocean extent, biome dressing and region actors: `Scripts/Setup/world_layout.py`,
  `build_coastal_terrain.py`, `build_coastal_flora.py`, `build_coastal_rocks.py`, `build_regions.py`, `build_fish.py`
  placement, `build_animals.py` **placement** (ChatGPT may keep editing animal *models* for T6/T7),
  `Source/EW/World/*`, `Source/EW/EWSurvivalComponent.*`, `Source/EW/EWSurvivalWidget.*`, and the map
  `Lvl_CoastalPlayground` itself. Report: `Docs/REPORTS/`.
- **Caves, then Plains grass and island landmarks** (October 15 night): new `Scripts/Setup/build_caves.py`,
  `Scripts/Verification/verify_caves_play.py`, `/Game/Elitewake/World/Caves`, and the cave notches in
  `world_terrain.py`.
- Audio with the owner's Scenario account (a separate Claude session): first drafts landed in `9a54ac7`; that session
  still owns `Art/Audio/`, `/Game/Elitewake/Audio`, `Source/EW/EWSound*`, `Source/EW/EWSoundscapeComponent.*`.

---

## Queue

### T1. Repair the stale title-screen Play check — DONE `533380c`
- **Why:** `Scripts/Verification/verify_title_play.py` has failed since the October 13 title rework (`1f7d505`):
  it calls `title.get_start_button_rect()`, which no longer exists. The current widget
  (`Source/EW/Title/EWTitleWidget.h`) exposes `GetSinglePlayerButtonRect()`, `IsSplashScreen()`,
  `IsMainMenuScreen()`, `StartJourney()`, `ContinueToMenu()`, `StartSinglePlayer()`.
- **Do:** read `Docs/TITLE_INPUT_VERIFICATION.md` and the current title flow (`Source/EW/Title/*`), then rewrite the
  check's steps to the current screens: splash (art fills the screen) → any key → main menu (Single Player button
  rect in the art's lower middle; Multiplayer shown but unavailable) → Single Player travels to the coastal map.
  Keep its existing structure and result file (`Saved/TitlePlayResult.json`). Note: Single Player now resumes a
  saved survivor if `Saved/SaveGames/Survivor.sav` exists (`UEWSurvivorSave`); move any existing save aside during
  the check and restore it after, as `verify_options_menu_play.py` does.
- **Done when:** the check passes with `EW_PLAY_MAP=/Game/Elitewake/Maps/Lvl_Title`, `EW_PLAY_PLAYERS=1`, and
  `Docs/VERIFICATION.md` records it.
- **Result:** rewrote the check for the current splash, menu and Single Player flow. It protects an existing
  survivor slot, checks the visible title/prompt, splash key transition, menu panel geometry and disabled
  Multiplayer state, then confirms the coastal map and normal survivor pawn. Added result notes to
  `Docs/VERIFICATION.md` and `Docs/TITLE_INPUT_VERIFICATION.md`.
- **Verified:** Standalone Play, 1280×720, 3/3 passed; `git diff --check` and Python syntax check passed. The routed
  mouse/key behavior is separately covered by the Slate native automation (its headless NullRHI limitation remains
  as documented). No existing survivor save was present. Play result: `Saved/TitlePlayResult.json`.

### T2. Native tests for the climate model — DONE `a59f508`
- **Why:** `UEWSurvivalComponent::UpdateClimate` (`Source/EW/EWSurvivalComponent.cpp`) only has a Play check.
  The rules are pure arithmetic and deserve fast native coverage.
- **Do:** add `Source/EW/Tests/EWClimateTests.cpp` (new file; do not edit `EWShipTests.cpp`, the other writer has
  it open). Cover, with an actor + component in a test world as the existing tests do:
  1. comfortable air (20 C) keeps the target at 37 C;
  2. cold air (-12 C) without clothing: target below 35 C, body moves toward it at `BodyRate` per second;
  3. the same in water (felt = water temperature) cools harder (`WaterChill`);
  4. insulation 1.0 answers the cold (target back near 37 C);
  5. hot humid air (34 C, 75 %) with no clothing stays at 37 C; with insulation it rises;
  6. below `FreezingBelow` health falls by `FreezeDamage` per second and the `Freezing` notice appears; it clears
     when warm again;
  7. `AEWClimateRegion::SampleClimate`: inside an oval → its climate; 50 m out with `OffshoreReach` 100 m → halfway
     to the open sea; beyond → `OpenSea` (22 C, 60 %).
  Read the constants from the class (they are `static constexpr`), do not copy numbers.
- **Done when:** the new tests pass with the native command above and the baseline is otherwise unchanged; record
  the count in `Docs/VERIFICATION.md`.
- **Result:** added native coverage for all seven requested climate and region cases. Equal air and water
  temperatures isolate the water-chill modifier.
- **Verified (October 15):** `ClimateModel` passes alone and in the full native suite. The full run performed 30
  tests: 29 passed and the existing `Title.RoutedKeyboardMouseAndWheel` test failed under headless `-NullRHI`
  because it requires full-screen geometry. The climate test passes; the known title-input limitation is unchanged.
  Build succeeded. Results: `Saved/Logs/ClimateFullNative.log`.

### T3. Native round-trip test for the single-player save — DONE `0a3e6ad`
- **Why:** `UEWSurvivorSave` (`Source/EW/EWSurvivorSave.*`) is covered only by `verify_options_menu_play.py`.
- **Do:** a native test that fills a survivor (location, health, hunger, hydration, inventory with a food age,
  an equipped tool, two hotbar bindings), saves to a test slot name (add an optional slot parameter if needed,
  defaulting to the real slot), loads, applies to a fresh survivor and compares everything, and confirms tools
  are not duplicated when the starter kit already gave them. Delete the test slot afterwards.
- **Done when:** passes natively; `verify_options_menu_play.py` still passes; docs updated.
- **Result:** added isolated slot-name parameters to the survivor save API and a native round-trip test covering
  location/facing, health, hunger, hydration, an aged berry stack, an equipped axe and two hotbar bindings. The
  test starts the fresh survivor with an axe in inventory and confirms applying the save leaves exactly one
  owned axe, equipped rather than duplicated.
- **Verified (October 15):** the native `SurvivorRoundTrip` test and the complete options-menu Play check both
  pass. The test deletes and confirms removal of its temporary save slot. The full suite performed 31 tests:
  30 passed and the known headless `Title.RoutedKeyboardMouseAndWheel` geometry test failed as before. Build
  succeeded. Results: `Saved/Logs/SaveRoundTripNative.log`, `Saved/OptionsMenuPlayResult.json`, and
  `Saved/Logs/SaveRoundTripFinalNative.log`.

### T4. Consolidate the owner's open questions — DONE `79ef146`
- **Why:** open values are scattered through the docs; the owner needs one list to answer.
- **Do:** create `Docs/OPEN_QUESTIONS_2026-10-15.md`. Collect every unresolved value or rule from
  `DESIGN_REFERENCE.md`, `MILESTONES.md`, `REMAINING_WORK_2026-10-14.md`, `WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md`,
  `MULTIPLAYER_RULES.md`, `SINGLE_PLAYER_RULES.md` (search for TBD, open, unresolved, owner question, *tuning*,
  DECIDED (delegated)). Group by system. For each: the question, where it is used in code (file and symbol), the
  working value currently in the game if any, and what is blocked on it. Include at least: climate thresholds and
  damage rates and each region's temperature/humidity; clothing insulation values and the clothing list;
  land-animal yields (currently the fish rule carried over); Raw Fish vs "Fish Meat" naming; whether the squid is
  a "bigger creature"; waterskin capacity (open question 11); campfire values; recipes (open question 1);
  invisible barriers vs falls; claim/contest timers; ghost-ship values; Port islands (open question 7).
  Link it from `Docs/MILESTONES.md`. **Do not answer any question.**
- **Done when:** the file exists, every entry cites its source document, and nothing in it invents a value.
- **Result:** `Docs/OPEN_QUESTIONS_2026-10-15.md` groups open decisions by world/climate, traversal/gathering/wildlife,
  crafting/ships/economy, and prologue/company/progression/multiplayer. It cites the governing docs and current C++ data
  symbols/working values where available; explicitly distinguishes absent implementations from tunable values; and
  reconciles decisions already made (five regions, Port exclusion, habitat directions, two sloop hardpoints, recipe
  trigger, Journal location, berry rules, and squid size classification). Linked from `Docs/MILESTONES.md`.
- **Verified:** `git diff --check` passed. Reviewed the listed climate, item, wildlife, ship and inventory declarations;
  `git status` confirms editor, project-guide, private-release, ship-test and asset-bundle work stayed unstaged. No
  gameplay check was run because this documentation-only task changes no behavior.

### T5. The pickaxe's first swing after equipping sometimes misses — DONE `04735ca`
- **Why:** known since October 14: right after equipping the Pickaxe, the first Left Mouse at a boulder sometimes
  finds nothing (`verify_core_tools_play.py` and `verify_work_feedback_play.py` retry). The hatchet does not do this.
- **Do:** find the cause. Start at `AEWPlayerController::Attack` → `FEWInteractionTargeting::FindTarget`
  (`Source/EW/EWInteractable.cpp`) and `AEWMineable::CanMine` / `CanAccessSource`, and the equip path
  (`UEWEquipmentComponent::EquipItem`, `AEWCharacter::RefreshHeldItem`). Suspects: the aim trace hitting the newly
  attached held mesh, or the client's equipment not yet replicated when the swing is sent. Write the reproduction
  as a Play check that fails before the fix and passes after, then remove the retries from the two checks.
- **Done when:** first-swing success is 10 of 10 in the new check; both existing checks pass without retries.
- **Result:** the checks were retrying a click sent inside the shared one-second attack interval immediately after
  a preceding swing. With the single input sent after the equip and cadence interval, the local attack is admitted;
  the held-mesh and equipment-replication suspicions were not reproduced. The mining checks now aim at the boulder's
  bounds center and send exactly one Left Mouse input. No gameplay code change was warranted by the reproduction.
- **Verified (October 15):** the dedicated `verify_pickaxe_first_swing_play.py` check passed 10 of 10 first swings
  after alternating Hatchet → Pickaxe, with one click per trial and no retry. `verify_core_tools_play.py` passed all
  11 steps with no mining retry, and `verify_work_feedback_play.py` passed all five steps with one pickaxe swing.
  The first no-retry core run with its 0.8 s settle failed to animate/mine; after waiting 1.5 s, the 10-trial check
  passed. Python syntax and `git diff --check` passed. Play results: `Saved/PickaxeFirstSwingPlayResult.json`,
  `Saved/CoreToolsPlayResult.json`, `Saved/WorkFeedbackPlayResult.json`.

### T6. A better tortoise shell — OPEN
- **Why:** the tortoise's scutes read as stripes (`Saved/Screenshots/Animals`, `Docs/VERIFICATION.md` "Land
  animals"). The owner's photo shows a high dome of polygonal plates with dark seams and growth rings.
- **Do:** in `Scripts/Setup/build_animals.py`, function `tortoise()`, replace the `shell()` colouring with a proper
  scute layout: a row of 5 vertebral plates down the spine, 4 costal plates per side, about 11 marginal plates per
  side round the rim; each plate a polygon with a dark seam and concentric growth rings toward its centre, tone
  varied per plate. Keep the function's signature and everything else in the file. Rerun the script in the editor
  (it replaces the animals in the coastal map), then `verify_animals_play.py` must still pass.
- **Done when:** a side and top screenshot clearly show plates; the animals check passes; screenshots saved under
  `Saved/Screenshots/Animals`.
- **Progress (October 15):** drafted raised polygonal vertebral, costal, and marginal scutes with dark seams and
  nested ring tones in `tortoise()`; Python syntax and `git diff --check` pass. The editor built the updated static
  mesh in memory, but saving existing animal assets fails with Windows sharing violation (error 32). The standard
  setup script also stops while recompiling/saving the shared animal material, which reports a missing Transform
  Position input. Existing material, tortoise mesh, material instance, and definition files are currently locked by
  another process; no Unreal Editor process is running in this workspace. No regenerated asset, Play result, or
  screenshot is committed. The local function edit remains uncommitted.
- **Next:** release the asset file locks, resolve or bypass the shared-material save failure without changing
  unrelated material behavior, rerun the in-editor setup, then capture side/top views and run the animal Play check.

- **Note from Claude (October 15):** the "sharing violation" was four of these build editors still running
  (`UnrealEditor.exe ... build_animals.py` and `TortoiseShellRebuild.py`, started 05:25-05:32, all hung, each locking
  the others' files). With the owner's approval Claude closed all four; the asset locks are gone. Your uncommitted
  `build_animals.py` edit and the animal assets on disk were left untouched. Please launch one build at a time and
  make sure it exits (`quit` after the script, or a wrapper that quits) before starting another.
- **Retry (October 15):** after the owner confirmed Unreal Editor was closed, retried the asset access check. Windows
  still denies exclusive access to `SM_Tortoise_v1.uasset`, `MI_Tortoise_v1.uasset`, and `DA_Animal_Tortoise.uasset`;
  no Unreal Editor process is visible in this session, and the system's open-file listing is unavailable. The live
  `Saved/Logs/EW.log` identifies a separate Claude `run_then_quit.py` Unreal automation that is actively creating
  port meshes and saving the coastal map. A new T6 launch did not reach its wrapper while that run was active, so it
  was stopped to avoid overlapping writes. The previous in-memory mesh build is the latest verified T6 result; no
  saved tortoise asset, screenshots, or Play test yet.
- **Handoff to Claude (October 15):** Codex stopped its waiting launch on the owner's pause request; no Unreal
  process is visible in this session. The latest exclusive-access check now succeeds for the tortoise mesh, material
  instance, and definition, and `Saved/Logs/EW.log` has stopped advancing (last write 08:30 local). The `tortoise()`
  scute draft in `Scripts/Setup/build_animals.py` remains uncommitted; Python syntax and diff checks pass. No T6
  wrapper completion, saved shell update, screenshots, or Play result were produced by the retry. Please review the
  working-tree changes before resuming; other animal and world files are also modified and must be preserved.

### T7. Snow Leopard for the Winter island — OPEN (needs the editor)
- **Why:** owner habitat direction (October 14): Snow Leopards belong in Winter. No counts or values were set.
- **Do:** add a `snow_leopard()` model to `Scripts/Setup/build_animals.py` in the same style as the others
  (lofted body, four legs with the four-leg gait, long thick tail with tail sway, pale grey-cream coat with dark
  rosettes painted by vertex colour, small rounded head). Add it to `ANIMALS` with habitat `winter`, aggressive,
  placed only on the Winter island (`build_coastal_terrain.py` `WINTER_SHORE`, centre (2000, 17500)). Its numbers
  are *tuning* and must be listed as such in `Docs/DESIGN_REFERENCE.md` (Land animals section) with its yield
  marked DECIDED (delegated) like the others. Extend `verify_animals_play.py`'s kind list.
- **Done when:** it walks on the Winter island in Play, attacks a survivor who comes near, and the animals check passes.

### T8. Asset catalog upkeep — DONE `08c7e27`
- **Why:** many new generated assets landed on October 15 (animal meshes and materials, Maravai and birch trees,
  four stone looks, work animations, leaf textures `Art/Flora/*-Leaves-v1.png`).
- **Do:** run `Scripts/Art/build_art_catalog.py` and fix its status rules so the new folders are classified
  (generated in-editor draft vs reference vs pending model). Update `Art/README.md` accordingly.
- **Done when:** the catalog lists every new asset with a sensible status; no asset is marked final.
- **Result:** the catalog uses path-component rules, so growth references, current and legacy survival art,
  inventory icons, generated fish cutouts, leaf-card textures and animal modeling references receive distinct
  classifications. The machine-readable catalog also lists the files and draft status in six Unreal folders for
  wildlife, flora, rocks, world materials and tool animations. The README explains each class and links the folders.
- **Verified:** rebuilt with the script; it indexed 179 PNGs and 322 named atlas slots, with 82 references,
  52 pending-model references, 11 generated intermediate drafts, 29 in-game UI art sources and 5 legacy images.
  All indexed files exist, all classifications have definitions, all six Unreal folder records are present, and no
  image status is labeled final. Python syntax compilation and JSON assertions passed. Git-wide checks hit the
  environment's Git LFS filter startup error on concurrent audio files; the files changed for this task were
  individually reviewed and checked.

### T9. Map zoom and the whole-world overview — OPEN
- **Why:** owner requirements in `Design/MAP_ZOOM_AND_PLAYER_LOCATION_REQUIREMENTS_2026-10-15.md` (read it fully).
  The current map (`Source/EW/EWMapWidget.*`, opened with M in `AEWPlayerController::SetMapOpen`) shows a fixed
  scene capture around the survivor.
- **Do:** mouse wheel and controller RT/LT zoom while the map is open only (Enhanced Input, a map-only mapping
  context added and removed with the map; RT/LT must not fire weapons while it is open); smooth zoom between a local
  view and a world overview that fits every island in a square; a distinct player marker that tracks position and
  facing; subtle animated water in the overview; island outlines and labels stay legible. **Data source for the
  overview:** every island has an `AEWClimateRegion` actor (centre = actor location, half-sizes `Radii`, `Region`);
  Claude is rebuilding the world into 25+ islands with these, so draw from them rather than from hard-coded
  coordinates, and do not edit `Source/EW/World/*` (ask in this file if you need a field added). Do not reveal
  undiscovered places beyond what the doc allows (no fog of war exists yet: record that as an open question rather
  than inventing rules). The map must not pause the game.
- **Done when:** a Play check covers wheel and RT/LT zoom, the min/max limits, marker accuracy while walking, and
  that the overview contains every region actor; screenshots at both ends of the zoom range.

- **Addition (Claude, October 15):** the five Ports now exist. Mark each on the map at its plaza actor (a
  `StaticMeshActor` labelled `Port of the <Region>: plaza`; the site centre and waterfront bearing are also in
  `Scripts/Setup/world_layout.py` `PORTS`). Label them "Port" (names are still the owner's to set).

### T10. "Village" becomes "Port" — OPEN
- **Why:** owner direction in `Docs/PORT_TERMINOLOGY_AND_REGIONAL_PORT_DESIGN_2026-10-15.md`.
- **Do:** replace Village/Villages (and "Free Port") with Port/Ports in current authoritative docs, player-facing
  text (search `Source/` for NSLOCTEXT/FText strings and `Scripts/Setup/` for display names and descriptions),
  journal and onboarding text. Leave `Docs/ARCHIVE/` as history. **Do not rename C++ symbols or Unreal assets**
  without checking references and save compatibility; list any that would need renaming as a follow-up instead.
- **Done when:** `git grep -i village` outside the archive only shows deliberate historical mentions, the build
  passes, and the journal check (`verify_journal_play.py`) still passes if journal text changed.

### T11. Metric units audit — OPEN
- **Why:** owner direction in `Docs/METRIC_WORLD_SCALE_AND_ISLAND_SPACING_2026-10-15.md`: player-facing distances
  in metres.
- **Do:** search player-facing text and UI (`Source/EW/**/*Widget*.cpp`, journal text, item descriptions in
  `Scripts/Setup/*.py`) for feet, yards, miles, knots or unitless distances shown to players; convert to metres
  (cm internally stays as Unreal's unit). Record findings and changes in `Docs/VERIFICATION.md`.
- **Done when:** no imperial unit is shown to players; affected checks still pass.

### T12. Tests for the world layout rules — OPEN
- **Why:** `Scripts/Setup/world_layout.py` places the 26 islands; its `check()` enforces the owner's spacing and
  region rules. It runs as a script but nothing stops a later change breaking it.
- **Do:** add plain-Python tests (e.g. `Scripts/Tests/test_world_layout.py`, standard `unittest`, no Unreal) that
  import `world_layout` and assert: at least five islands per region; at least five round the starter (Plains);
  every pair at least 800 m apart along shorelines; every island's nearest within 2,000 m; each region's islands on
  its side of the world (Winter +Y, Swamp -Y, Desert +X, Jungle -X); the starter island's centre, radii and wobble
  unchanged (-800, -100, 5100, 4100, 0.03 in cm). Also test `world_terrain.height` at the fixed places listed in
  `Saved/CoastalTerrainResult.json` `ground_cm` (spawn 67.2 cm at (150, 0), dock landing -27.2 at (4000, 900), spring
  -265 at (-1700, 1500)). Document how to run them in `Docs/VERIFICATION.md`. Do not edit `world_layout.py` or
  `world_terrain.py` (Claude's); report a failing rule here instead.
- **Done when:** `python -m unittest` from the repo root runs them green.

### T13. Remove the retired terrain assets — OPEN (needs the editor)
- **Why:** the five-region world replaced the single coastal terrain. These assets are no longer placed:
  `/Game/Elitewake/World/Meshes/SM_CoastalTerrain_v1`, `SM_MainIslandSurf_v1`, `SM_IsletSurf_v1`,
  `SM_SecondIslandSurf_v1`, `SM_WinterIslandSurf_v1`, and `/Game/Elitewake/World/Rocks/M_CoastalRock_v1`.
- **Do:** in the editor, confirm each has no referencers (Reference Viewer or
  `unreal.EditorAssetLibrary.find_package_referencers_for_asset`), then delete those with none. Leave anything still
  referenced and list it here. Run `verify_coastal_play.py` afterwards.
- **Done when:** the unreferenced ones are gone, the coastal check passes, and the result is noted here.

### T14. Native tests for swing kinds and gather gains — OPEN
- **Why:** `Source/EW/EWWorkFeedback.*` and the character's attack variant (low 2 bits = swing kind: 0 plain,
  1 chop, 2 mine; see `AEWCharacter::SwingKindAt`) have only Play checks. A refactor could silently break the
  bit packing or the refusal reasons.
- **Do:** add `Source/EW/Tests/EWWorkFeedbackTests.cpp` (a new file; leave `EWShipTests.cpp` to its current
  owner) with automation tests under `Elitewake.WorkFeedback.*`: swing kind packing and unpacking for every kind and
  several sequence numbers; `FEWGatherGain` equality/merging if it has any; each `EEWWorkRefusal` maps to a
  non-empty player message. Do not change gameplay code; if something is untestable without a change, note it here.
- **Done when:** the new tests pass in the native run (`Automation RunTests Elitewake`) with no new failures.

### T15. Ship leaks and bailing (M2) — OPEN
- **Why:** `Docs/REMAINING_WORK_2026-10-14.md` M2: hull health and shot damage are done (`verify_hull_damage_play`);
  leaks, bailing and repairs are not. The prologue (DESIGN_REFERENCE, prologue step 2) has the player bail water.
- **Do:** read the hull damage code (`Source/EW/Ships/*`, search `HullHealth`) and the M2 section of
  `Docs/MILESTONES.md`. Add replicated water-in-hull that rises while hull health is below full (rate *tuning*),
  lowers the ship's freeboard/top speed as it rises (*tuning*), and a Bail interaction at a deck spot that lowers it.
  Leave sinking and repair costs unresolved (list them in `Docs/OPEN_QUESTIONS_2026-10-15.md`). Do not touch
  `Source/EW/World/*` or the world scripts.
- **Done when:** a Play check on `Lvl_ShipsTest` (server plus client) shows water rising after a hit, the client
  seeing the same level, speed falling, and bailing lowering it; native tests still pass.

### T16. Fall damage (M6) — OPEN
- **Why:** owner rule (REMAINING_WORK M6): falls of more than 25 m onto solid ground are fatal, lower falls scaled,
  deep water exempt. The safe height and the lower-height curve are **owner TBD**.
- **Do:** server-side landing damage in the character (`Landed`), measured from the highest point of the fall:
  fatal above 25 m onto solid ground; none when landing in swimmable water; between a safe height and 25 m a linear
  curve, with the safe height and curve exposed as clearly labelled *tuning* properties and recorded as open in
  `Docs/OPEN_QUESTIONS_2026-10-15.md`. Ship decks and ladders count as solid ground.
- **Done when:** a Play check on `Lvl_CoastalPlayground` drops a survivor from 30 m onto land (dies), 30 m into deep
  water (lives) and from a mid height (hurt, alive), checked on the client too; native tests pass.

