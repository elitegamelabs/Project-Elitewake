# Elitewake saved work and controller repair — November 16, 2026

## Scope and status

Owner authorized saving, committing and publishing the accumulated project work to the existing GitHub repository. This is a development checkpoint, not a packaged game release or a claim that every feature is owner accepted.

Project: `C:/UnrealProjects/EW_CLEAN/EW.uproject`, Unreal Engine 5.8, branch `main`.

## Windows PlayStation controller repair

The project previously loaded XInputDevice only. Sony HID enumeration in EWControllerIcons selected PlayStation button pictures but did not deliver controller inputs.

- Enable Unreal's bundled GameInputWindows plugin (and its GameInput dependency).
- Disable XInputDevice to avoid two backends reporting the same gamepad.
- Enable both gamepad and generic controller processing using the Windows **per-object** settings section in DefaultInput.ini. Keyboard and mouse retain the existing Windows input path.
- Configure Sony DualShock 4 original/revision 2, DualSense and DualSense Edge product IDs. Face buttons, shoulders, digital/analog triggers, stick clicks, Share/Create and Options map to existing Gamepad keys. D-pad uses the switch processor. Stick Y axes are inverted into Unreal's convention.
- Preserve existing gameplay mappings and PlayStation glyphs. No third-party driver, emulator, OS setting change or PlayStation SDK is installed.

Both Editor Development and Windows game Development builds succeed. The latter compiles and links the current EW.exe, but no cooking/packaging or distributable release is performed. Runtime logs confirm GameInput 3.1.26100.6879 initializes and subscribes to ControllerAxis, ControllerButton, ControllerSwitch and Gamepad input. This is stronger than plugin mounting alone, but does not prove physical button correctness.

Input regression run: **3 passed, 0 failed, 0 warnings** (BuildModeKeys, ControllerFamilyAndButtonNames, HotbarKeyboardAndControllerBindings). These validate existing generic bindings/glyph behavior, not physical Sony HID reports. The first unattended test launch stalled during editor startup and was stopped; a clean retry on the empty Entry map with source control disabled completed successfully. See `Docs/Verification/2026-11-16/ControllerRepair.json`.

Physical acceptance remains pending. A Sony USB controller was detected in the initial diagnosis, but was no longer present when rechecked during repair. No DualSense hardware test has completed. Verify USB and Bluetooth independently, including Cross/Circle, all D-pad directions and repeated holds, both sticks, both trigger axes, Options, inventory navigation, inspect/craft, hotbar, focus loss and disconnect/reconnect. Test Xbox and keyboard/mouse regressions too. Do not report unperformed hardware checks as passed.

Primary technical references: [Epic's GameInput settings API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/GameInputBase/UGameInputPlatformSettings) and [Epic's D-pad issue UE-230486, fixed for 5.8](https://issues.unrealengine.com/issue/UE-230486). Configuration was checked against the installed 5.8 public headers.

## Accumulated work included in this checkpoint

- Title/menu artwork and animation materials; coordinated loading artwork and wave treatment.
- Maritime survival HUD/icons, hotbar styling, status effects and treatment assets represented by the existing working changes.
- Inventory Slice 1: three-column UI, warm 70%/80% panel fills, shared wood/brass styling, actual survivor portrait and layout refinements.
- Slice 2: stable crafting tiles with recipe inspection, existing authoritative crafting, keyboard/controller actions and validation.
- Slice 3: five displayed equipment slots, boots/accessory definitions, recipes and placeholder worn meshes. **Owner reports equipment does not work satisfactorily; this remains unresolved and deferred.** Automated fixture results do not close it.
- Slice 4: pending attribute allocation, server validation, confirmation, persistence/rollback and exactly 5-gold attribute reset. Constellation progression is preserved. Oxygen/Intelligence effects were not invented.
- Nine existing clothing icons reimported with transparency. Existing cropped artwork and long-caption clipping remain follow-up work.
- Existing MetaHuman/survivor source assets are preserved, without asserting finished character appearance.

The individual Inventory slice reviews and Clothing-Icon-Transparency-Review.md contain the detailed test history and limitations. Copies of their existing result summaries are in `Docs/Verification/2026-11-16`; those earlier results retain their original dates and are not represented as new test runs.

## Preservation and rebuilding

- Saved games, recovery backups, generated builds and logs remain local under existing ignore rules.
- Intentionally removed AGENTS.md, CLAUDE.md, FEATURE_EXPANSION_PLAN.txt and FUTURE_IMPLEMENTATIONS.txt are neither restored nor included as deletion changes in this checkpoint.
- World configuration remains 20 islands, four in each of Plains, Winter, Swamp, Desert and Jungle. No world geometry is edited for this repair.
- Existing policy excludes `Content/__ExternalActors__/` from GitHub. A fresh clone alone therefore **cannot reproduce the full current world**; the owner's local world-actor backups are still required. Marketplace source exclusions also remain in force.
- Two MetaHuman source assets exceed the repository's conservative 95 MB file limit. Their exact bytes are stored as parts under `Art/SourceAssets/MetaHumanArchives`, with lengths and SHA-256 hashes in manifest.json. Run `python Scripts/Setup/restore_archived_metahumans.py` after a fresh checkout. It verifies existing assets and refuses to overwrite differing files. The original local assets are retained.
- Rebuild using Unreal 5.8: `Build.bat EWEditor Win64 Development C:/UnrealProjects/EW_CLEAN/EW.uproject -WaitMutex`. GameInput requires its compatible Microsoft runtime on the testing machine; this PC has it installed. A later installer/distribution must verify that prerequisite.
- GitHub publication here means source/assets pushed to the existing remote. No new packaged EXE, public downloadable release, deployment or store submission is produced.
