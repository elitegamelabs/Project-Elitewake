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

- Snowfall and the next regions (Jungle, Plains, Swamp islands): `Scripts/Setup/build_coastal_terrain.py`,
  `build_coastal_flora.py`, `build_coastal_rocks.py`, `build_regions.py`, `Source/EW/World/*`,
  `Source/EW/EWSurvivalComponent.*`, `Source/EW/EWSurvivalWidget.*`.
- Audio with the owner's Scenario account (a separate Claude session): `Art/Audio/`, `/Game/Elitewake/Audio`,
  sound hooks in `Source/EW/EWCharacter.cpp`.

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

### T2. Native tests for the climate model — OPEN
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

### T3. Native round-trip test for the single-player save — OPEN
- **Why:** `UEWSurvivorSave` (`Source/EW/EWSurvivorSave.*`) is covered only by `verify_options_menu_play.py`.
- **Do:** a native test that fills a survivor (location, health, hunger, hydration, inventory with a food age,
  an equipped tool, two hotbar bindings), saves to a test slot name (add an optional slot parameter if needed,
  defaulting to the real slot), loads, applies to a fresh survivor and compares everything, and confirms tools
  are not duplicated when the starter kit already gave them. Delete the test slot afterwards.
- **Done when:** passes natively; `verify_options_menu_play.py` still passes; docs updated.

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

### T5. The pickaxe's first swing after equipping sometimes misses — OPEN
- **Why:** known since October 14: right after equipping the Pickaxe, the first Left Mouse at a boulder sometimes
  finds nothing (`verify_core_tools_play.py` and `verify_work_feedback_play.py` retry). The hatchet does not do this.
- **Do:** find the cause. Start at `AEWPlayerController::Attack` → `FEWInteractionTargeting::FindTarget`
  (`Source/EW/EWInteractable.cpp`) and `AEWMineable::CanMine` / `CanAccessSource`, and the equip path
  (`UEWEquipmentComponent::EquipItem`, `AEWCharacter::RefreshHeldItem`). Suspects: the aim trace hitting the newly
  attached held mesh, or the client's equipment not yet replicated when the swing is sent. Write the reproduction
  as a Play check that fails before the fix and passes after, then remove the retries from the two checks.
- **Done when:** first-swing success is 10 of 10 in the new check; both existing checks pass without retries.

### T6. A better tortoise shell — OPEN (needs the editor)
- **Why:** the tortoise's scutes read as stripes (`Saved/Screenshots/Animals`, `Docs/VERIFICATION.md` "Land
  animals"). The owner's photo shows a high dome of polygonal plates with dark seams and growth rings.
- **Do:** in `Scripts/Setup/build_animals.py`, function `tortoise()`, replace the `shell()` colouring with a proper
  scute layout: a row of 5 vertebral plates down the spine, 4 costal plates per side, about 11 marginal plates per
  side round the rim; each plate a polygon with a dark seam and concentric growth rings toward its centre, tone
  varied per plate. Keep the function's signature and everything else in the file. Rerun the script in the editor
  (it replaces the animals in the coastal map), then `verify_animals_play.py` must still pass.
- **Done when:** a side and top screenshot clearly show plates; the animals check passes; screenshots saved under
  `Saved/Screenshots/Animals`.

### T7. Snow Leopard for the Winter island — OPEN (needs the editor)
- **Why:** owner habitat direction (October 14): Snow Leopards belong in Winter. No counts or values were set.
- **Do:** add a `snow_leopard()` model to `Scripts/Setup/build_animals.py` in the same style as the others
  (lofted body, four legs with the four-leg gait, long thick tail with tail sway, pale grey-cream coat with dark
  rosettes painted by vertex colour, small rounded head). Add it to `ANIMALS` with habitat `winter`, aggressive,
  placed only on the Winter island (`build_coastal_terrain.py` `WINTER_SHORE`, centre (2000, 17500)). Its numbers
  are *tuning* and must be listed as such in `Docs/DESIGN_REFERENCE.md` (Land animals section) with its yield
  marked DECIDED (delegated) like the others. Extend `verify_animals_play.py`'s kind list.
- **Done when:** it walks on the Winter island in Play, attacks a survivor who comes near, and the animals check passes.

### T8. Asset catalog upkeep — OPEN
- **Why:** many new generated assets landed on October 15 (animal meshes and materials, Maravai and birch trees,
  four stone looks, work animations, leaf textures `Art/Flora/*-Leaves-v1.png`).
- **Do:** run `Scripts/Art/build_art_catalog.py` and fix its status rules so the new folders are classified
  (generated in-editor draft vs reference vs pending model). Update `Art/README.md` accordingly.
- **Done when:** the catalog lists every new asset with a sensible status; no asset is marked final.
