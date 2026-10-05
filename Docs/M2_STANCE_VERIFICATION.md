# M2 stance animation configuration — 2026-10-05

Active project: `C:\UnrealProjects\EW`. Unreal **5.8.3**, changelist 58210709. Owner directed a return to M2 after M5C; M5D remains pending.

## Implementation

- Free Animation Library's 164 files were found in the older OneDrive backup and copied into active `Content/FreeAnimationLibrary`. The backup was neither launched nor modified.
- Library and character mannequin skeletons have matching bone names, parent hierarchy and reference transforms; compatibility is explicitly saved. No character scaling or skeleton substitution is used.
- `ABP_EWLocomotion` retains template standing/running/jumping and adds crouch/prone blend spaces driven by the actual character's crouch and replicated prone state. Each has twelve samples: three idle points and eight movement directions plus a backward seam duplicate. Crossfades are 0.2 seconds.
- Eighteen private animation copies under `Content/Elitewake/Animations/Stances` lock the root to the reference pose. Imported movement clips otherwise translate their root during loops; CharacterMovement must own displacement. Imported animation clips remain unchanged.
- Standing foot-placement IK is bypassed for prone; crouch retains foot placement.
- Fixed prone-to-crouch tap by preserving the existing crouch request when clearing prone. Sprint/jump still explicitly request standing.
- First-person prone eye height targets 40 cm above the capsule bottom. Its calculation uses the requested crouch size because stance callbacks can precede capsule resizing.
- `EWEditor` provides native blend-space compilation and Play verification access; it is an Editor module, excluded from game targets. `Scripts/configure_stance_animations.py` revalidates assets without duplicating an existing configured graph.

## Verification

- Final EWEditor Win64 Development build succeeds on 5.8.3; source uses the supported `GetCrouchedHalfHeight()` getter.
- `Elitewake.Animation.StanceBlendSpaces` passes after reloading saved assets: matching skeleton hierarchy/reference transforms, persisted compatibility, twelve samples per blend space, normalized runtime weights at nine directions and three speeds, and locked animation roots.
- Both existing inventory tests pass: `PersistedTestItem` and `StackingAndWeight`. Final regression log: `Saved/Logs/M2ReleaseRegression.log`.
- `Scripts/verify_stance_play.py` injects normal Enhanced Input actions and checks tap crouch, walking at 300 cm/s, hold prone, crawling at 150 cm/s, both return transitions, mesh scale, root alignment and first-person prone eye height. Results: `Saved/M2StancePlayResult.json`.
- Final Play result is **success** with eight checkpoints: crouch walking 300 cm/s, prone crawling 150 cm/s, root displacement 0 cm, unchanged unit mesh scale, and first-person prone eye height exactly 40 cm. Log: `Saved/Logs/M2AcceptedPlay.log`. Earlier eye-height/transition failures were corrected and retested.
- `Scripts/verify_stance_network_play.py` identifies the client by replicated PlayerId, not local actor names. In a listen-server/one-client session, client inputs and animation state matched on client and authoritative host for crouch, prone and both return transitions. `Saved/M2StanceNetworkResult.json` records success. Inputs are released afterward; the editor is returned to single-player Play for owner inspection.
- Logs/results/screenshots under Saved are local evidence. Earlier failed probes remain in logs; only final successful results establish verification.

## Remaining boundaries

- Prone uses Unreal's crouched vertical capsule, **not** a separate horizontal body collision shape. Active Blueprint standing/crouched half heights are 90/40 cm. Low-clearance obstacles, slopes, overhangs and full-body prone collision tuning remain open; animation does not establish distinct prone clearance.
- Local stance replication is tested. Artificial latency, packet loss, dedicated servers and production multiplayer remain unverified.
- Imported stand-to-prone/prone-to-stand clips are available but are not connected as authored actions; this slice uses responsive crossfades. Final animation polish remains later work.
- Controller B retains its existing shared stance mapping; physical gamepad testing remains pending.
- Packaging and full game acceptance are not claimed. M2's animation gate is configured; its remaining collision/validation gates must not be silently marked complete.
