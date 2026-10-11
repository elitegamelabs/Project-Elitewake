# Private multiplayer testing and distribution

Recorded October 9, 2026 from the engineer's brief, reviewed and adopted as a development/testing workstream by the owner. This supplements the design authority in DESIGN_REFERENCE.md; it does not replace gameplay requirements or authorize publishing builds, inviting testers, or changing network exposure. Original attachment is preserved outside the repository.

## Target

Owner plays Player 1 while their Windows PC runs a listen server. One approved tester plays Player 2 from another Windows PC. Start with local tests, then LAN, then Internet. Initial testing requires no rented dedicated server. Private Windows distribution will use a restricted itch.io project and Butler; Epic Games Store publication is out of scope. Packaging/distribution never substitutes for implementing and verifying networking.

## Reconciliation with the active project

Current table updated October 10; dated checkpoints below retain their original scopes. Editor startup is unresolved (see PROJECT_GUIDE.md); package acceptance passed independently.

The brief's statement that networking is not implemented is outdated. The project already has replicated gameplay and owned-controller requests with verified in-process listen-server/client tests. Those results are foundations, not two-PC, Internet or packaged-game acceptance. Do not rewrite working systems merely to match the brief's starting assumption.

| Area | Evidence/current structure | Next acceptance work |
| --- | --- | --- |
| Character/movement | ACharacter movement/custom prediction; stance and separate-process movement checks pass | Physical controls, moving decks and two-PC behavior |
| Survival | Replicated stats, owner-only notices, authority and numeric guards; latest full native suite passes 19 tests | Cross-process UI/stat updates and production needs/effects |
| Inventory/equipment/hotbar | Owned transactions and late-join foundations pass; required package presence verified | Owner visibility decision, production reconnect/save and physical controls |
| Interaction/gathering | Owned intent and server validation; separate-process pickup competition/current late-join quantities pass | Production resource content/use and two-PC acceptance |
| Crafting/objectives | Separate-process crafting, owner-only recipe/objective state and session rewards; opt-in Repair Kit client menu passes | Production prologue events, packaged item use and save/reconnect |
| GameMode/spawning | Configured Blueprint classes and independent EW pawns/controllers audited; third-player fixture passes after clearing fallback spawn | Production PlayerStart capacity/placement and fallback policy |
| GameState/PlayerState | Engine defaults supply server time/distinct player IDs; current late join verified within fixture scope | Production shared state and persistent reconnect identity |
| Host/join/disconnect | F10/GameInstance foundation; 10 graceful + 13 cancellation/abrupt-loss lifecycle checkpoints | Packaged physical buttons/recovery, two-PC LAN and future session services |
| Packaging/distribution | Current 071931 Development archive: 16 packages, signed prerequisites, visible label, 5 loopback checks and 3 rendered startup sizes | Packaged menus/item use, clean-PC installation, two PCs, Shipping and approved distribution |

## Responsibility boundaries

- GameMode: server rules, admission and spawning. Clients do not own a GameMode instance.
- GameState: shared world/match state that joining clients need. Add only real shared state.
- PlayerState: player information needed independently of a pawn; persistent saves/reconnect identity require deliberate implementation.
- PlayerController: owns one player's input and validated server requests; local widgets belong to that player. Controller-owned objective continuity currently lasts only for that controller session.
- Character/Pawn: replicated movement and visible character state. The owning client controls input, while the server validates consequential gameplay.
- GameInstance: local host/join/travel lifecycle and connection errors across maps; it is not shared authoritative world state.
- Replicated properties/RepNotify: durable current state and local presentation refresh, including late join. Server RPCs: requests from a valid owning connection. Multicast: only when a transient shared presentation actually needs it; do not use it as persistent inventory/objective storage.

Existing Blueprint assemblies and replicated data assets must be audited alongside C++; source inspection alone does not certify all class defaults or cooking. No blanket 'replicate everything' migration.

## Small implementation and acceptance slices

1. Audit configured Blueprint classes, independent spawning and current RPC/replication boundaries. Preserve working gameplay and editor settings. Record findings and gaps.
2. Run two separate local game processes using the same source/build, then validate movement, inventory privacy/ownership, pickup competition and crafting. Existing same-process PIE evidence remains valid only for its stated scope.
3. Add a minimal private-test Host Game / Join Game entry flow and clean connection-failure/leave behavior. Direct connection is an initial candidate, not an approved Internet transport choice. Use a fixed retained test map rather than arbitrary map travel from input.
4. Validate two Windows PCs on LAN with matching build IDs. Verify two independent pawns, mutual movement visibility, world interactions and late join. Record failures with role/build/map/system information.
5. Choose and test Internet transport: direct IP with an explicitly configured router/firewall route, or an online service/relay if the actual network needs it. NAT/CGNAT and tester connectivity are external facts to establish; do not silently configure ports or claim Internet readiness.
6. Cook/package a minimal Windows Development test build for diagnostics; verify runtime assets and launch on another PC. Packaging may be needed before LAN/Internet acceptance if the tester lacks the editor/project. Repeat with the intended release configuration before distribution; Shipping console/debug behavior must not be assumed.
7. Add one visible private-test build identifier and matching release notes (Added, Fixed, Known Issues). Example 0.1.0/0.1.1 is a proposal; do not claim a version is released before it is built/tested. Include revision/configuration in internal evidence.
8. Prepare restricted itch.io access, individual tester download keys, Butler authentication and a stable Windows channel. Verify privacy/access before any upload or invitation; never store credentials or keys in Git. Distribution access does not authenticate multiplayer connections.
9. Upload only after owner approval, verify download/launch and update behavior, then repeat network acceptance with that exact distributed build. Increment the build label and retain concise release notes for each tested upload.

## Beginner-friendly delivery requirements

When a slice is ready for the owner/tester, explain Windows steps in order: where to click/type, which folder/values apply, what success looks like and how common errors are resolved. Provide actual verified paths and separately labeled fake examples; do not present placeholders as working account credentials or build locations. Main-menu layout and final network/distribution setup remain future work.

## External reference checks

- [Epic multiplayer testing](https://dev.epicgames.com/documentation/en-us/unreal-engine/testing-multiplayer-in-unreal-engine): editor player count/net mode and single-process versus separate-process testing.
- [itch.io access controls](https://itch.io/docs/creators/access-control): Restricted grants approved access and avoids public discovery; Draft is not the tester-download workflow.
- [Butler build uploads](https://itch.io/docs/butler/pushing.html): stable channel uploads and incremental update workflow. Upload efficiency does not guarantee every tester receives a small patch; verify the actual installation/update route.

Status: four in-process class/spawn checkpoints and four headless separate-process loopback connection checks recorded. Cross-process movement, owned crafting and pickup conservation now pass in an opt-in headless test; inventory visibility and remaining lifecycle checks stay open; Host/Join/Leave and connection recovery are now verified locally; a local Development package now passes the smoke check below. No two-PC result, external account, installation, firewall/router change or upload is claimed.

## Separate-process local connection checkpoint

`Scripts/Verification/verify_separate_process_connection.ps1` launches only two disposable hidden game processes against the retained ThirdPerson map. The listen host binds exclusively to 127.0.0.1; the script verifies the actual UDP endpoint before joining. Separate host/client logs confirm admission, client welcome and two distinct runtime character instances. A bounded observation confirms both processes remain running with no recorded network/travel failure or saved-move overflow. It terminates only its own processes and preserves the owner editor. Results: `Saved/SeparateProcessConnectionResult.json`; logs under `Saved/Logs/SeparateProcessHost.log` and `SeparateProcessClient.log`.

This uses the editor executable in game mode with NullRHI and a 60 fps cap, not a cooked package or visual/input test. Initial uncapped execution connected but emitted saved-move timing warnings; the final capped repeat passed all four checks. Engine ToolsetRegistry startup reports a missing PythonTestRunner in game mode in both runs; connection succeeds despite that unrelated tooling error. Audit development-only plugin loading before packaging rather than modifying original editor settings here. The opt-in gameplay acceptance below extends this checkpoint. Host/Join/failure UI foundation now passes the local lifecycle checkpoint below. Next address inventory visibility and broaden lifecycle/hardware acceptance before two-PC testing.

## Separate-process gameplay checkpoint

Run `Scripts/Verification/verify_separate_process_connection.ps1 -Gameplay` to use the retained isolated pickup map. The opt-in C++ harness is guarded by WITH_EDITOR and starts only with EWVerifyRole=Host/Client; it is absent from non-editor game targets. The wrapper adds these flags only to its own loopback processes and removes exact prior diagnostic markers before each run. Normal editor/game launches remain unaffected; no saved content or starting unlocks are assigned.

The final run passes movement in both directions, replicated recipe/material resolution, client mutation rejection, owner-only recipe knowledge, exactly 20 Wood consumed for one Axe, unchanged host crafting inventory, competing ten-unit pickup conservation/destruction and rejected unaffordable/invalid repeat requests. Both process reports pass; the combined report has 13 recorded observations, including the explicitly separate public-inventory visibility observation. Results: Saved/SeparateProcessGameplayResult.json and Saved/SeparateGameplay/{HostResult,ClientResult}.txt. The same diagnostic host/client log paths are regenerated per run.

Inventory Entries currently replicate without OwnerOnly while AvailableRecipes are owner-only. The client observed the host's three Wood; this is recorded behavior, not private-inventory acceptance. Mutation ownership passed. Review visibility before adding inspection/loot/raid interactions; none of those permissions are invented by this harness. The initial general-arena run reached movement/crafting but timed out targeting the pickup; the final isolated-map repeat passes. Hardware controls, rendered UI, late join, reconnect, graceful leave/host departure, packet emulation, two PCs and cooked packaging remain separate.

## Host/Join panel and recovery foundation

UEWGameInstance is configured in DefaultEngine.ini; owner DefaultEditor.ini is preserved. F10 is a temporary private-test panel key, not a final pause/controller binding. It closes inventory/map, owns cursor/focus, suppresses gameplay input and does not pause the world. Closing balances move/look locks. Host/Join use the retained ThirdPerson map and direct connections; the panel displays that Host/Join/Leave reload the map without saved session progress and that host departure disconnects other players. It supports Leave/Cancel and readable retained connection errors. Final main-menu integration remains pending.

Join accepts localhost or private/loopback IPv4 with an optional port (default 7777); it rejects public addresses, arbitrary travel URLs, hostnames, IPv6 and malformed ports. This intentionally limits the initial prototype to local/LAN targets; it is not authentication or access control. Host uses the ordinary listen driver; all automated tests launch with explicit loopback binding. No router/firewall configuration, Internet transport, online session service or external access is added.

Owner test steps: open EW, choose Play > Standalone Game, then press F10. Host Game starts a fresh local listen session. In a second standalone game with the same build, F10 > Join Game with 127.0.0.1:7777 connects on the same PC. Two-PC LAN remains unverified; it uses the host PC's private address rather than localhost and may need explicitly approved network setup. Return to game closes the panel; Leave/Cancel returns to fresh local play. In ordinary in-editor Play the panel is a preview with Host/Join/Leave disabled and instructions to use Standalone Game.

Scripts/Verification/verify_session_lifecycle.ps1 passes ten headless separate-process loopback checkpoints: F10 cycles and inventory/map switching, Host travel, Join, client Leave/server controller cleanup, rejoin, host Leave, persistent host-loss message, unavailable-host timeout recovery and restored controls. Address validation adds one native test (18 total). The initial failure tests exposed possession timing, error-message overwrite and null-world pending-connection routing; those were corrected before final acceptance. The unavailable-host timeout observed in the final run was about 20 seconds; no production timeout tuning was changed. Physical clicks, controller binding, LAN, cooked assets, save/reconnect identity and privacy are still separate work.

## Cooked Windows diagnostic checkpoint

Local archive: `C:\UnrealProjects\EW\Saved\PrivateBuilds\local-20261010-022851`. Double-click `Windows\EW.exe` for a manual local test; keep the whole Windows folder in place. The build contains ThirdPerson and M5PickupTest maps, Development Win64, dirty source revision 52678ecb34333205fc095d9a9bb38b3db286de02. It has not been uploaded or released. The manifest at the archive root records these facts.

Build with `Scripts/Verification/build_private_windows.ps1` while the editor and games are closed. Repeat connection acceptance with `Scripts/Verification/verify_separate_process_connection.ps1 -PackagedExecutable "C:/UnrealProjects/EW/Saved/PrivateBuilds/local-20261010-022851/Windows/EW/Binaries/Win64/EW.exe" -Port 27887`. Use the actual runtime executable for this check, rather than the bootstrap launcher. The test's two disposable hidden processes bind exclusively to loopback and are stopped afterward. Five checks pass in Saved/PackagedConnectionResult.json, including both runtimes loading the archived build label. Startup logs contain no ensure or fatal errors. Editor-only gameplay harnesses are deliberately absent from packaged game targets, so -Gameplay is rejected with this option.

ModelContextProtocol remains enabled in the editor and is restricted to editor targets; the runtime manifest excludes it and its editor tool dependencies. The formerly runtime GameFeatureData scan is now editor-only, clearing a cooked startup ensure without adding unused GameFeatures runtime dependencies. Editor connectivity and unchanged owner preferences were confirmed after packaging. No new full native rerun is claimed for these config/script changes; prior 18-test evidence remains scoped to the preceding code build.

Still pending: rendered packaged HUD/menu/input and map art, cooked item/recipe behavior, two PCs, LAN, prerequisite portability, Shipping configuration, privacy/access and distribution/update acceptance. This archive did not stage a UE prerequisite installer; successful launch on this development PC does not certify a clean tester PC. Inventory owner-only replication remains a pending owner question. F10 Host/Join/Leave remains a diagnostic entry flow, not a finished main menu.

The latest archive includes PrivateBuildLabel.txt inside Windows/EW and TEST_NOTES.md at the archive root. Press F10 to read the diagnostic label before comparing versions on two PCs. It includes the unique package label, short source revision, Development configuration and local-change marker. A missing/invalid label falls back to Unlabelled development build. Matching labels are not enforced on admission and do not authenticate a player. The label file must travel with the entire Windows folder; metadata alone does not reproduce dirty source changes.

October 10 archive includes the generated starter icons and saved starter item/recipe fixtures. The diagnostic packaging script explicitly cooks Content/Elitewake and fails if any of fourteen required starter packages is absent from the cooked registry or archived IoStore listing. CookedStarterContentResult.json and StarterContainerListing.csv at the archive root record package presence, not rendered gameplay acceptance. No automatic inventory grants or production unlocks are added. Five connection checks passed on this exact archive; no two-PC or packaged tool-use acceptance is inferred.

## Late-join checkpoint — October 10

Run `Scripts/Verification/verify_separate_process_connection.ps1 -Gameplay -LateJoin -Port 27888` for three separate editor-build game processes bound to localhost. A third player joins only after the first two finish movement, crafting and competing pickup acceptance. Saved/SeparateProcessLateJoinResult.json passes seventeen acceptance checks plus three separately labelled public-inventory observations. The late client receives two existing players and one current seven-unit pickup, never the consumed ten-unit pickup; its own inventory/recipe knowledge starts empty and rejects local grants and an owned unavailable craft request. Reports are under Saved/SeparateGameplay; the wrapper terminates only its own processes.

The initial attempt exposed test pawns parked on the retained map's fallback spawn, blocking the third pawn. The fixture now clears that area before late admission without editing the saved map or overriding normal spawn rules. This does not certify production-world spawn capacity or fallback selection. Headless editor-build scope only: no packaged late-join gameplay, rendering, LAN, inventory privacy, reconnect identity/save, packet loss or dedicated-server acceptance. Handshake cancellation and abrupt host crash now pass within the recovery scope below.

## Pending cancellation and abrupt shutdown — October 10

`Scripts/Verification/verify_session_lifecycle.ps1 -Recovery -Port 27889` passes thirteen headless editor-build checkpoints using two disposable localhost processes. The client cancels a pending connection to an unused port after two seconds, closes its arrival panel and remains in local play for twenty-five seconds without a stale failure; then successfully joins, leaves and rejoins the host. The wrapper kills only its own host after both role markers confirm readiness. The established client detects the lost host after the unchanged engine timeout, returns locally with a lost-connection message, and can attempt another join and recover from its closed-port timeout. Saved/SessionRecoveryResult.json records acceptance; raw role logs/reports are preserved under Saved/SessionRecovery before another lifecycle run overwrites its scratch directory.

This exposed and fixed two runtime bugs: local map travel did not cancel PendingNetGame, and an established host timeout used the initial-join failure text. Leave/Cancel now invokes the public world-based CancelPending API and clears queued callbacks. GameInstance tracks joined-host arrival for failure wording and resets it on leave/new attempts. The original ten graceful lifecycle checkpoints and eighteen native tests passed afterward. The refreshed Windows archive includes these fixes and passes five packaged connection checks, but the WITH_EDITOR recovery harness is absent from it: packaged cancellation/crash behavior and physical buttons are not separately certified. Timeout/saved-move warnings after deliberately killing the host are expected in recovery logs; no timeout tuning changed. Internet, accounts, firewall/router configuration, uploads and tester invitations remain outside this slice.

## Rendered packaged startup — October 10

Run `Scripts/Verification/verify_packaged_rendered_startup.ps1 -PackagedExecutable "C:/UnrealProjects/EW/Saved/PrivateBuilds/local-20261010-022851/Windows/EW/Binaries/Win64/EW.exe"` for three 16:9 captures, or add `-CaptureSet AspectRatios` for 1024x768 and 3440x1440. It starts one disposable hidden/offscreen rendered process at a time, captures the UI, verifies the label/PNG dimensions, preserves each image/log in a unique Saved/RenderedStartup folder, and terminates only that process. Each result starts with visualReview pending; capture success alone does not approve layout. It does not inject desktop input or load opt-in inventory fixtures.

All five captured sizes on the local-20261010-022851 archive were visually reviewed: prototype scene/character, stat icons/percentages and centered empty hotbar render without overlap or clipping. Recorded results: Saved/RenderedStartup/20261010-031925/Result.json and 20261010-032123/Result.json. Default health/stamina/hunger/hydration are full and weight zero; this does not test other values, debuff timers, selected-slot highlighting or generated assigned art in the packaged UI. Menu interactions, keyboard/controller, DPI/HDR/other devices, performance, two-PC LAN and clean-PC prerequisites still need separate acceptance. No new archive, build or native rerun was needed for this script-only slice.

## Prerequisite bundling — October 10

Archive at this checkpoint: `C:\UnrealProjects\EW\Saved\PrivateBuilds\local-20261010-042407`. Launch Windows/EW.exe and retain the complete Windows folder. Packaging now stages engine-provided prerequisites with -prereqs. On this installed UE 5.8, the files are Windows/Engine/Extras/Redist/en-us/vc_redist.x64.exe and vc_redist.arm64.exe. Both archived copies have valid Microsoft signatures and match the supplied engine files by SHA256. Verification records PrerequisitesResult.json and never invokes installation. Use the x64 installer interactively on an x64 tester PC if needed; installation/elevation belongs to the tester's setup, not this automation. The ARM64 file is staged by the engine for emulation and is not native ARM64 acceptance. GameInput redist is not opted in.

Build/cook/archive, fourteen starter package presence checks, five headless loopback checks and three rendered 16:9 startup-frame reviews pass for this label. Connection reports/logs are copied into this archive; screenshots and review live at Saved/RenderedStartup/20261010-042540. The first socket-inspection attempt failed to observe an endpoint under restricted execution and stopped its owned host; it did not establish an actual non-loopback binding. The repeated check with OS inspection available passed. Its failed report/log remain at Saved/PackagedPrerequisitesFirstAttempt. The verifier now distinguishes failed/missing socket inspection from an observed wrong address; the final version also passes.

Older paragraphs describe the prior 022851 archive, which did not bundle installers; they remain historical scoped evidence. Prerequisite presence does not establish bootstrap prompting, installation success, missing-runtime recovery or clean-PC portability. Next owner-assisted acceptance still needs packaged menus/keyboard/controller, two PCs with this same complete build, private LAN and clean-PC setup. No LAN/Internet exposure, firewall/router changes, account creation, installation, tester messages or uploads occurred.

## Current private package — October 10

Current archive is `C:\UnrealProjects\EW\Saved\PrivateBuilds\local-20261010-071931`; launch Windows/EW.exe and retain the complete Windows folder. The archive includes the numeric survival fix and opt-in Repair Kit assets, with sixteen required starter/prologue packages confirmed in cooked registry and archived container. No normal recipe grants, prologue sequence, repair behavior or final fixture weights are introduced. PrerequisitesResult.json confirms two signed Microsoft runtime installers matching this engine; none were executed. RuntimeBinaryResult.json confirms the archived executable matches the current compiled Game Development target.

Five fresh headless loopback checks on port 27891 pass with label loading, exclusive loopback binding, distinct processes, welcome/admission and two character instances during bounded stability. PackagedConnectionResult.json and raw host/client logs are copied to this archive. Fresh startup rendering review at three 16:9 sizes passes in Saved/RenderedStartup/20261010-072151. This does not certify packaged kit/menu use, physical keyboard/controller, prerequisite installation, clean-PC portability, two-PC LAN, Shipping or distribution. Older labels retain their original scoped evidence. Next owner-assisted acceptance still needs packaged menus/controls and the same complete build on clean/tester PCs. Original editor settings and old archives preserved; no upload, installation, tester invitations or network configuration.
