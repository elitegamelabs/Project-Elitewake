# Delegated tasks (for ChatGPT / Codex)

**Team rule (owner, October 22): everyone works freely; no locks, claims or ownership of anything.** See [TEAM_CHARTER.md](TEAM_CHARTER.md). `CLAIMED` / `IN PROGRESS` below is a courtesy notice only: it blocks nobody. Any teammate may add, take over or finish any task. Grok has joined ([Delegation/GROK.md](Delegation/GROK.md)).

**Owner, October 20: no agent owns any file, API or system.** Claude helps the owner design the game; it holds no locks and reserves nothing. Codex, ChatGPT and Claude may all edit any file. To avoid collisions: pull first, check `git log` and the inbox for recent work on the same files, keep commits small, and say in the inbox when you start on a file another agent changed recently. The shared Unreal editor lock (one editor at a time on this PC) still applies to everyone.

Owner direction, October 15: Claude keeps this queue full of work it is **not** doing, so another agent can take
it in parallel. Claude adds to it as work comes up; each task is self-contained. Read this whole header before
taking a task.

Owner, October 16: Claude coordinates Scenario (it calls it directly), ChatGPT and Codex. Tasks marked **for Codex**
suit code, native or Python tests and scripts; **for ChatGPT** suit docs, the art catalogue, research and review;
unmarked tasks suit either. Take what fits you.

**Report in the shared inbox (owner, October 17):** every claim, finish, blocker or stop gets an entry in
[Delegation/INBOX.md](Delegation/INBOX.md), pushed to `main`; work left on a local branch is invisible.

**Per-agent lists (October 16):** each agent now has its own file with new tasks and the earlier ones that suit it:
[Delegation/CODEX.md](Delegation/CODEX.md), [Delegation/CHATGPT.md](Delegation/CHATGPT.md), and the Scenario job queue
[Delegation/SCENARIO.md](Delegation/SCENARIO.md). New tasks (C1.., G1.., S1..) are claimed in those files; the T-tasks
below are still claimed here.

## How to work this queue

1. `git fetch && git pull --ff-only` first. Two agents (and the owner) commit to `main`.
2. **Claim** a task: change its status to `CLAIMED (ChatGPT, date)` in this file and push that one-line change
   before starting, so no other agent picks it up.
3. When finished: set the status to `DONE <commit>` and write what you verified (and what you could not) under the
   task. If you stop part-way, set `OPEN` again and say where you got to.
4. No files are reserved (owner, October 20). If a task touches a file another agent changed recently, pull first and
   say in the inbox that you are starting on it.

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

## Where Claude has worked (history only; open to every agent, owner, October 20)

Owner, October 20: these were once reserved for Claude. They are not any more: anyone may edit them. The list stays
only so you know where earlier world, cave and ship work lives.


- **The five-region world rebuild** (owner direction of October 15: Plains centre with the starter island, Winter
  north, Swamp south, Desert east, Jungle west, at least five islands each, 800–2,000 m sea gaps). Claude worked on the
  island layout, terrain, seabed, ocean extent, biome dressing and region actors: `Scripts/Setup/world_layout.py`,
  `build_coastal_terrain.py`, `build_coastal_flora.py`, `build_coastal_rocks.py`, `build_regions.py`, `build_fish.py`
  placement, `build_animals.py` **placement** (ChatGPT may keep editing animal *models* for T6/T7),
  `Source/EW/World/*`, `Source/EW/EWSurvivalComponent.*`, `Source/EW/EWSurvivalWidget.*`, and the map
  `Lvl_CoastalPlayground` itself. Report: `Docs/REPORTS/`.
- **Caves, then Plains grass and island landmarks** (October 15 night): new `Scripts/Setup/build_caves.py`,
  `Scripts/Verification/verify_caves_play.py`, `/Game/Elitewake/World/Caves`, and the cave notches in
  `world_terrain.py`.
- **The bigger islands, their terrain plans, regional trees and cave cobwebs** (October 15 night – 16, the Claude
  session that also does audio; it now holds the world scripts listed above while the five-region session is idle):
  `Scripts/Setup/world_layout.py`, `world_terrain.py`, `rebuild_world.py`, `rebuild_tree_meshes.py`,
  `build_cave_webs.py`, `build_coastal_terrain.py`, `build_coastal_flora.py`, `build_coastal_rocks.py`,
  `Scripts/Art/make_leaf_cluster.py`, `Source/EW/EWCobweb.*`, `Source/EW/Wildlife/EWWildlifeRest.*`, and the checks
  `verify_island_terrain_play.py`, `verify_regional_trees_play.py`, `verify_cave_webs_play.py`,
  `verify_world_performance_play.py`.
- **Owner milestones of October 16 for trees and ships** (the same Claude session): fuller leaves and needles on every
  non-palm tree, partial snow on the Winter trees, and boarding ladders centred on every stern (all three done:
  `97c3cf4`, `01dfca1`). Besides the world
  scripts above: `Scripts/Art/make_leaf_cluster.py`, the ship definitions' ladder places, `Scripts/Setup/ship_hull.py` and `ship_geometry.py`.
  The starter island's oaks are done (`2e7404d`).
- **Owner ship systems expansion of October 17** (this Claude session): hulls, hull gunports, cannon mounts and the
  modular railing hardpoints on the sloop, schooner and brigantine (`Scripts/Setup/build_sloop_hull.py`,
  `build_schooner.py`, `build_brigantine.py`, `ship_hull.py`, `Source/EW/Ships/EWShip*`, `EWShipTypes.h`). Codex has
  C4 (sail positions) and C5 (flags), ChatGPT G6 (surgeon) and G7 (module prompt sheets).
- Audio with the owner's Scenario account (a separate Claude session): first drafts landed in `9a54ac7`; that session
  still owns `Art/Audio/`, `/Game/Elitewake/Audio`, `Source/EW/EWSound*`, `Source/EW/EWSoundscapeComponent.*`,
  `Source/EW/Ships/EWShipSoundComponent.*` and `Scripts/Verification/verify_audio*_play.py`.

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

### T6. A better tortoise shell — DONE (asset saved and Play-verified by Claude, 2026-10-20; shell colour for the owner)
- **Why:** the tortoise's scutes read as stripes (Saved/Screenshots/Animals, Docs/VERIFICATION.md "Land animals"). The owner's photo shows a high dome of polygonal plates with dark seams and growth rings.
- **Do:** in Scripts/Setup/build_animals.py, function tortoise(), replace the shell() colouring with a proper scute layout: a row of 5 vertebral plates down the spine, 4 costal plates per side, about 11 marginal plates per side round the rim; each plate a polygon with a dark seam and concentric growth rings toward its centre, tone varied per plate. Keep the function's signature and everything else in the file. Rerun the script in the editor (it replaces the animals in the coastal map), then verify_animals_play.py must still pass.
- **Done when:** a side and top screenshot clearly show plates; the animals check passes; screenshots saved under Saved/Screenshots/Animals.
- **Source checkpoint (published f703632):** tortoise() describes five vertebral, four costal per side and eleven marginal per side, with deterministic plate tone variation, concentric rings, dark seams and slight raised centers. Python compilation and an offline index check for all 35 plate indices pass.
- **Additional source-geometry verification (October 20):** executing the current published tortoise() function with an inert Unreal API stub generated 3,450 vertices and 6,860 triangles. All triangle indices resolve, all coordinates are finite, and bounds are approximately 109.45 × 72 × 55.78 cm. This validates only the in-memory source geometry; no Unreal asset was saved. Added Scripts/Tests/test_tortoise_geometry.py to preserve the mesh-data regression check; the focused test passes 1/1 and the full Python suite passes 27/27.
- **Editor state:** Saved/TortoiseShellRebuild.py reuses the existing tortoise material instance to avoid the standard setup script's unrelated shared-material compilation error. After confirming no process or editor lock, UnrealEditor.exe and UnrealEditor-Cmd.exe both exited in under two seconds with code 0 and produced no new engine log or result. No mesh rebuild, animal Play check or screenshots have been obtained.
- **Next:** run the targeted rebuild from a working editor session or diagnose why UE 5.8.3 exits before startup, then inspect the saved shell from side/top and run verify_animals_play.py. Keep T6 open until those checks pass.
- **Asset and Play (Claude, October 20):** the editor itself starts normally (a probe on the main checkout loaded the
  project and ran Python in 20 s); ChatGPT's launches end within 2 s in its own environment, so its sandbox, not the
  project, stops Unreal. Claude ran `Saved/TortoiseShellRebuild.py` (pointed at its worktree, on main b40c9a9):
  `SM_Tortoise_v1` saved, 3,450 vertices and 6,860 triangles, matching the offline test; the definition already used it.
  `verify_animals_play` passed 9/9; the new `verify_tortoise_look_play` (one player) took side, top and three-quarter
  shots in `Saved/Screenshots/Animals` (`tortoise_side00001`, `tortoise_top00001`, `tortoise_three_quarter00001`):
  the vertebral row, side rows and dark seams read as plates. **For the owner/ChatGPT:** in daylight the shell reads
  pale cream, lighter than the owner's photo; darker plate tones in `tortoise()` would fix it if wanted.
- **Shell colour (owner, October 20: "a darker brown like my photo"):** the plate, ring and plastron tones in
  `tortoise()` lowered to about a seventh; rebuilt and rechecked (`verify_tortoise_look_play` 4/4): a dark brown dome
  with the plates and seams still clear.

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

### T9. Map zoom and the whole-world overview — CLAIMED (Codex, 2026-10-20)
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
- **October 20 owner addition:** replace "Surrounding Area" with the current island/region name; allow free pan and zoom without following or recentering on the player; keep the player marker visible; remove only the map's "Walking remains available" and "World continues" messages. Map implementation proceeds under C7.
- **Codex, October 20 (`41a050b`):** source now derives an overview extent from the placed island-region actors, adds free pan/zoom and a player marker, and samples the current region label. Build and focused hotbar native verification passed; Play verification did not run in this session, so T9 remains partial. See `Docs/REPORTS/2026-10-20_C7_GAME_IMPROVEMENTS_PARTIAL.md`.
- **World source:** `Source/EW/World/*` is open to edit (owner, October 20); add the field there if region actors do not provide sufficient map data.

### T10. "Village" becomes "Port" — DONE 7ba3cff (ChatGPT, 2026-10-20)
- **Why:** owner direction in `Docs/PORT_TERMINOLOGY_AND_REGIONAL_PORT_DESIGN_2026-10-15.md`.
- **Do:** replace Village/Villages (and "Free Port") with Port/Ports in current authoritative docs, player-facing text, journal, and onboarding while preserving historical mentions and serialized IDs/assets.
- **Done when:** non-archive current text uses only deliberate historical mentions; player-facing implementation checks pass if affected text changed.
- **Result / verified (October 20):** changed the two active terminology uses in `Docs/WILDLIFE_DISTRIBUTION_26_ISLANDS.md` to Port wording. A repository search found no remaining source, setup-script or runtime UI references to Village/Free Port. Remaining occurrences are deliberate historical/retired terminology, task labels, or the rename-policy source itself. No code, runtime journal or UI text changed, so no build or Play check was required.

- **Why:** owner direction in `Docs/PORT_TERMINOLOGY_AND_REGIONAL_PORT_DESIGN_2026-10-15.md`.
- **Do:** replace Village/Villages (and "Free Port") with Port/Ports in current authoritative docs, player-facing
  text (search `Source/` for NSLOCTEXT/FText strings and `Scripts/Setup/` for display names and descriptions),
  journal and onboarding text. Leave `Docs/ARCHIVE/` as history. **Do not rename C++ symbols or Unreal assets**
  without checking references and save compatibility; list any that would need renaming as a follow-up instead.
- **Done when:** `git grep -i village` outside the archive only shows deliberate historical mentions, the build
  passes, and the journal check (`verify_journal_play.py`) still passes if journal text changed.

### T11. Metric units audit — DONE 6e02b7e (ChatGPT, 2026-10-20)
- **Why:** owner direction in `Docs/METRIC_WORLD_SCALE_AND_ISLAND_SPACING_2026-10-15.md`: player-facing distances in metres.
- **Do:** search player-facing text and UI (`Source/EW/**/*Widget*.cpp`, journal text, item descriptions in `Scripts/Setup/*.py`) for feet, yards, miles, knots or unitless distances shown to players; convert to metres (cm internally stays as Unreal's unit). Record findings and changes in `Docs/VERIFICATION.md`.
- **Done when:** no imperial unit is shown to players; affected checks still pass.
- **Result / verified (October 20):** source review of player-facing widget strings, Journal widget/data setup, and item-description setup found no feet/yards/miles/knots distance labels or unitless numeric distance displays. The raft Journal text expresses pace as 2.5 metres per second. No gameplay text was changed; no affected Play check was required. Findings are recorded in `Docs/VERIFICATION.md`. Runtime visual review was not performed in this documentation-only audit.

- **Why:** owner direction in `Docs/METRIC_WORLD_SCALE_AND_ISLAND_SPACING_2026-10-15.md`: player-facing distances
  in metres.
- **Do:** search player-facing text and UI (`Source/EW/**/*Widget*.cpp`, journal text, item descriptions in
  `Scripts/Setup/*.py`) for feet, yards, miles, knots or unitless distances shown to players; convert to metres
  (cm internally stays as Unreal's unit). Record findings and changes in `Docs/VERIFICATION.md`.
- **Done when:** no imperial unit is shown to players; affected checks still pass.

### T12. Tests for the world layout rules — DONE `414bfff` (Claude)
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
- **Verified (Claude, October 16):** `Scripts/Tests/test_world_layout.py` added (import-only, `world_layout.py`
  and `world_terrain.py` untouched). `python -m unittest` from the repo root: 14 of 14 pass, covering every rule
  above plus the cave addition below. Added empty `Scripts/__init__.py` / `Scripts/Tests/__init__.py` — Python
  3.13's `unittest` discovery otherwise finds nothing from the repo root without them. Not covered: this only
  checks the Python generator's own output, not what lands in the editor (that's `verify_caves_play` and the
  world/coastal Play checks).
- **Addition (Claude, October 15 night):** caves now exist (`world_terrain.CAVES`). Also assert: every island has
  exactly one cave; all three kinds (`inland`, `cliff`, `coastal`) occur; every cave's `footprint()` lies on its
  island (`island.distance < 0`) and off every Port (`world_layout.near_port`); the ground 3 m and 6 m in front of
  each mouth is no more than 2 m / 4 m below the floor.

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

### T15. Ship leaks and bailing (M2) — DONE `a0374fa` (Claude)
- Built by Claude: `AEWShip` water aboard (replicated), leaks through holes below the waterline, settling, slowing
  through the load, a bailing bucket on deck; `verify_leaks_play.py` (5). Repair and sinking stay open.
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

### T17. World map picture with Ports and caves — DONE `f264397` (Claude)
- **Why:** `Docs/images/world_layout_v1.png` (drawn by `Scripts/Art/draw_world_layout.py`) shows the islands only.
  The owner reads the docs to follow the world.
- **Do:** extend the drawing (plain Python, PIL, no Unreal) to mark each Port (`world_layout.PORTS`: site centre,
  a small quay line along `facing`) and each cave mouth (`world_terrain.CAVES`: `mx`, `my`, an arrow along
  `heading`, coloured by `kind`), with a legend; save as `Docs/images/world_layout_v2.png` and point
  `Docs/DESIGN_REFERENCE.md`'s layout link at it. Do not edit `world_layout.py` / `world_terrain.py`.
- **Done when:** the picture renders, every Port and all 26 caves are visible, and the link is updated.
- **Verified (Claude, October 16):** `Docs/images/world_layout_v2.png` renders: 26 islands, 5 Ports (square plus
  quay line) and all 26 caves (arrow along heading, coloured by kind) visible, with a legend. Image ran through
  `python Scripts/Art/draw_world_layout.py` from a clean checkout. `Docs/DESIGN_REFERENCE.md`'s layout link updated
  to v2. `world_layout.py` / `world_terrain.py` untouched. Not covered: a person judging the look; `world_layout_v1.png`
  stays in `Docs/images/` as a static file but the script no longer regenerates it under that name.


### T18. Show the time of day — OPEN
- **Why:** day and night now run (`Source/EW/World/EWDayNight.*`, commit `2ac71d9`): 90 real minutes each. Players
  have no way to read the hour except by the sun.
- **Do:** a small, quiet indicator on the HUD (next to the compass, `Source/EW/EWSurvivalWidget.*` is Claude's, so
  add it to the compass widget or a new widget) showing a sun or moon symbol and the hour as `HH:MM`, read from
  `UEWDayNightSubsystem::GetForWorld(this)->GetHour()` on the owning client. Do not edit `Source/EW/World/*`.
  Decide nothing about clocks being an item the player must craft (owner question; list it in
  `Docs/OPEN_QUESTIONS_2026-10-15.md`).
- **Done when:** a Play check (listen server plus client) sets the hour on the server with
  `unreal.EWDayNightSubsystem.get_for_world(server_world).set_hour(...)` and reads the client's indicator text and
  symbol for noon and midnight; screenshots at both.

### T19. Keep the hour in a single-player save — OPEN
- **Why:** the single-player save (`Source/EW/EWSurvivorSave.*`) keeps the survivor but the world restarts at 08:00.
- **Do:** save `GetHour()` with the survivor and, on load (`UEWGameInstance::ResumeSavedSurvivorOnArrival` /
  `ApplyTo`), call `SetHour` on the server. Keep old saves loading (no hour → leave the clock alone). Extend the
  native save round-trip test (T3's) for the hour.
- **Done when:** the native test and `verify_options_menu_play.py` pass, and a save made at 21:00 loads at 21:00.

### T20. Native tests for leaks and bailing — OPEN
- **Why:** `AEWShip` now takes water through holes below the waterline (`GetLeakCount`, `GetWaterAboard`,
  `GetSettle`, `UpdateLeaks`, bailing in `Interact_Implementation` at the bucket). Only a Play check covers it.
- **Do:** a new `Source/EW/Tests/EWShipLeakTests.cpp` (leave `EWShipTests.cpp` alone; it has someone's uncommitted
  work) under `Elitewake.Ships.Leaks`: a spawned ship (see how the hull damage test builds one) holed below and
  above its waterline counts one leak; `UpdateLeaks(1.f)` adds `LeakPerHole` per leak; water counts in `GetLoad()`;
  `GetSettle()` is `MaxSettle` at capacity and 0 when dry; the water stops at 1.5 x capacity. Do not change
  gameplay code (ask here if something is private and needs exposing).
- **Done when:** the native run passes with the new test.

### T23. Native tests for the sound library — OPEN
- **Why:** `UEWSoundLibrary` (`Source/EW/EWSound.*`) maps every `EEWSound` to its assets under `/Game/Elitewake/Audio`
  and counts what each world starts; only a Play check (`verify_audio_play.py`) covers it.
- **Do:** a new `Source/EW/Tests/EWSoundTests.cpp`: for every `EEWSound` value, `GetSound` returns a loaded asset (try
  several times for the two-take sounds and check both takes appear); `PlaySoundAt` in a test world raises
  `GetPlayCount` for that asset's name, `GetTotalPlayCount` and `GetLastPlayed`; a null context or asset changes
  nothing. Do not change gameplay code; the audio session owns `EWSound*`, so ask here if something needs exposing.
- **Done when:** the native run passes with the new tests (Elitewake filter) and the count is recorded in VERIFICATION.

### T24. Move the hull damage check to the ships test map — OPEN
- **Why:** `Scripts/Verification/verify_hull_damage_play.py` stops before its first step on
  `/Game/Elitewake/Maps/Lvl_CoastalPlayground` (runner error StopIteration at load, October 15 night): it looks for
  the schooner, which now lies only in `/Game/Elitewake/Maps/Test/Lvl_ShipsTest` with the large ships.
- **Do:** point the check at the ships test map (its header, and how it finds the sloop, the schooner and the
  survivors, as `verify_cannon_fight_play.py` does there), keeping its three checks and result file. Skip survivors
  with no PlayerState when matching the client's survivor. Do not change gameplay code.
- **Also (October 17):** the sloop has no hull gunports now: her cannon places `StarboardCannon1/2` open only with a
  two-cannon railing (`DA_TestRailingTwoCannon`) fitted at `StarboardRailing`; fit it first, as
  `verify_cannon_play.py` does.
- **Done when:** it passes on the ships test map with run_play_check.py and VERIFICATION's hull row says where.

### T25. Measure a packaged game's frame rate on the bigger world — OPEN
- **Why:** since the bigger islands (October 15 night) the only frame-rate numbers are from the editor's Play window
  (`Scripts/Verification/verify_world_performance_play.py`: 45–53 fps on an RTX 4070), which carries the editor's own
  cost. A standalone `-game` run with the CSV profiler did not start in our attempts.
- **Do:** build a Development package with the existing private build scripts (no upload), run it on
  `Lvl_CoastalPlayground`, and record frame, game, draw and GPU times at the same four places the check uses (the
  starter beach, the biggest Jungle and Winter islands, the Plains Port), e.g. with `stat unit` screenshots.
- **Done when:** the numbers are in VERIFICATION's "World performance" row.

### T26. Find what fills video memory with two players' views — OPEN
- **Why:** with a listen server and a client in one editor the engine reports video memory about 0.9 GB over budget
  on the bigger world (RTX 4070, 12 GB); with one view it does not. Ray tracing geometry also exceeds its resident
  budget (235 of 400 MB).
- **Do:** with `stat memory`, `stat rhi` and `r.Streaming.Dump` (or memreport), find the largest users (grass instances,
  the island meshes' distance fields and ray tracing geometry, textures) and propose cuts with their visual cost. Do
  not change the world scripts (`Scripts/Setup/world_*`, `build_*`): write the findings here for Claude.
- **Done when:** a short findings note with numbers is in this file or `Docs/REPORTS/`.

### T27. Catalogue the new tree leaf art — DONE (ChatGPT, 2026-10-18; delivery hash in INBOX.md)
- **Why:** `Art/Flora/Oak-Leaves-v1.png` and `Art/Flora/Ash-Leaves-v1.png` (drawn by `Scripts/Art/make_leaf_cluster.py`,
  used by the Plains oaks and Jungle ash since `468ce0d`) are not in `Art/CATALOG.json` / `Art/README.md`.
- **Do:** add them the way the other flora cards are listed (generated by script, integrated), with your catalogue
  tooling; do not change the images.
- **Done when:** both appear in the catalogue with their status and source script.

### T28. Python tests for the world scripts (for Codex) — OPEN
- **Why:** `Scripts/Setup/world_layout.py` and `world_terrain.py` are plain Python that every world script and check
  builds on (islands, terrain plans, caves, ground height); only Play checks cover them, and each takes minutes.
- **Do:** a new `Scripts/Tests/test_world.py` (standard `unittest`, no Unreal), importing them by path as the setup
  scripts do: `world_layout.check(world_layout.ISLANDS)` returns no problems; every island outside the Swamp and the
  starter has a terrain plan in `world_terrain.TERRAIN_PLANS`, no two in a region alike; every cave in
  `world_terrain.CAVES` exists and its mouth needs a step of at most 45 cm (`built_height` over u -80..0, v -150..150
  across `centre_v(0)`, against `floor`, as `verify_island_terrain_play.py` does); the starter keeps its old ground at
  the spawn (150, 0), the dock landing (4000, 900) and the spring (-1700, 1500) (heights 67, -27 and -265 cm). Do not
  change the world scripts; if a test fails, write it up here.
- **Done when:** `python -m unittest Scripts/Tests/test_world.py` passes and VERIFICATION has a line for it.

### T29. Native tests for the cobweb and wildlife rest (for Codex) — OPEN
- **Why:** `AEWCobweb` (`Source/EW/EWCobweb.*`) and `FEWWildlifeRest` (`Source/EW/Wildlife/EWWildlifeRest.*`) are
  covered only by Play checks.
- **Do:** a new `Source/EW/Tests/EWWorldDressingTests.cpp` (Elitewake filter): a spawned web starts whole, `Tear()`
  makes it torn with `ShredCount` strands falling, they are gone after `FallSeconds` of ticks, and it is whole again
  after `RegrowSeconds`; `FEWWildlifeRest::IsAwake` is false with no `AEWCharacter` within `RestRange` once its look
  comes round, true with one inside it, and `Wake()` makes it awake at once. Do not change gameplay code; ask here if
  something needs exposing.
- **Done when:** the native run passes with the new tests and the count is in VERIFICATION.

### T30. List the October 15–16 delegated world decisions for the owner (for ChatGPT) — DONE (ChatGPT, 2026-10-18; delivery hash in INBOX.md)
- **Why:** several choices were made under the owner's delegation that the owner may want to confirm or change.
- **Do:** add them to `Docs/OPEN_QUESTIONS_2026-10-15.md` as "decided under delegation, confirm?" items, each with
  its working value and where it lives: island sizes 500–900 m and the starter about 620 m (`world_layout.py`);
  dressing caps 500 trees / 220 rocks / 220 of each plant per island; wildlife resting beyond 200 m (`EWWildlifeRest`);
  cobwebs respun after 10 minutes and their count per cave (`EWCobweb`, `build_cave_webs.py`); the terrain plan
  vocabulary per region (`world_terrain.PLANS`); a few Maravai kept under the Jungle's ash. Read
  `Docs/DESIGN_REFERENCE.md` for the wording; do not change it.
- **Done when:** the items are in the open-questions file with links.

### T31. Find why the sinking check sometimes cannot open a crate (for Codex) — OPEN
- **Why:** on October 16 `Scripts/Verification/verify_sinking_play.py` step 4 timed out once: the survivor swam beside a
  wreck crate and the interaction was sent (`opened: True`) but the client's open container stayed empty for 12 s; the
  rerun passed. Intermittent failures hide real ones.
- **Do:** run the check several times (`run_play_check.py`, coastal map); if it fails again, find whether the request
  is lost (crate not yet relevant to the client after the survivor is set down, a reach check, or the container
  screen's open RPC) and fix the check or, if it is a game bug, the code (`Source/EW/Ships/EWWreckCrate.*`,
  `EWPlayerController` container opening), with a note here.
- **Done when:** five runs in a row pass, and the cause is written here.

### T32. Directional swimming animations (for Codex) — OPEN
- **Why:** owner, October 16 (`Design/Gameplay/SWIMMING_DIRECTIONAL_ANIMATION_REQUIREMENTS_2026-10-16.md`): stationary
  in water plays the existing water idle; forward (and forward diagonals) plays a forward-swimming cycle; backward keeps
  the existing default swim (the owner's "spinning animation": find which asset that is, do not guess or delete it).
  The movement half is done (`AEWCharacter::DoMove`, verified by `verify_swim_directions_play.py`); the animations are not.
- **Do:** inspect how the survivor's swim animations are chosen today (`EEWLocomotionState::Swimming`, the anim
  blueprint and `UpdateLoopAnimation` in `Source/EW/EWCharacter.cpp`), add the forward/backward/idle choice from the
  survivor's velocity relative to its facing, smoothly blended, in first and third person. If no forward-swim animation
  exists, list what is needed here rather than inventing one. Do not change movement.
- **Done when:** a Play check shows each state's animation on the client and the server's copy, and VERIFICATION has it.

### T21. A modelled bailing bucket — OPEN
- **Why:** every ship now has a bailing bucket on deck, drawn as an engine cylinder until
  `/Game/Elitewake/World/Ships/SM_BailBucket_v1` exists (the ship loads it automatically when it does).
- **Do:** a small wooden bucket (staves, two iron hoops, a rope handle), about 30 cm across and 30 cm high, origin
  at the centre of its base, built by a setup script like the other ship props (`Scripts/Setup/`, with
  `ship_geometry.Builder` and the timber material) and saved at that path. Reference art is welcome but not required.
- **Done when:** `verify_leaks_play.py` passes and a screenshot of the sloop's deck shows the bucket.

### T22. A modelled wreck crate, and a native test for fill-sinking — OPEN
- **Why:** sinking ships leave `AEWWreckCrate`s (`Source/EW/Ships/EWWreckCrate.*`), drawn as stand-in cubes until
  `/Game/Elitewake/World/Ships/SM_WreckCrate_v1` exists (loaded automatically, origin at its centre, about 70 x 70 x
  55 cm). A ship also sinks when she holds 1.5 x her capacity in water; only the hull-destroyed case has a Play check.
- **Do:** (a) model the crate: weathered planks, rope lashings, a little weed; a setup script like the other ship
  props. (b) In your T20 test file (or a new `EWShipSinkingTests.cpp`), a native test that fills a spawned ship's
  water to 1.5 x capacity (you may need `UpdateLeaks` with holes below the waterline over simulated time) and checks
  `IsSinking()`, that a definition with `bCannotSink` never sinks, and that `StartSinking` moves the hold into crates
  of six stacks. Do not change gameplay code; ask here if something needs exposing.
- **Done when:** `verify_sinking_play.py` passes with the modelled crate (screenshot), and the native run passes.


## ChatGPT audit note — October 18
T10: one current milestone phrase corrected to Port; remaining inspected Village mentions are historical/rename-policy/task labels. T11: current widget/journal text audit found no imperial distance label; documented nautical speed values are preserved as later owner authority. No gameplay text changed, no fresh build/journal/Play checks. T6: new tortoise top/side reference only; exact modeled scutes and Unreal acceptance remain implementation work. T27/T30 completion is documentation/catalogue work, not a new world build.
