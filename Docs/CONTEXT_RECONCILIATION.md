# Context reconciliation

Reviewed 2026-10-05 before any remote push. This record reconciles design references, development history and inspected implementation so future sessions can distinguish confirmed design from historical summaries.

Publication update, 2026-10-05: after this review, the owner approved publication provided it aligns with core goals. Remote main was rechecked at `9b7f129`; the ordinary push of `286f8d0` and `41ee3fc` succeeded. Hold/local-only statements below describe the review-time state, not the current publication status. No core design change was introduced.

## Sources and authority

1. **Current explicit owner instructions** control the work. The owner asked to review the linked historical chat and cross-reference everything before pushing. Remote publication remains on hold.
2. **Integrated Master Game Design Bible, September 21, 2026** is the current design reference identified in that chat. Read its 27 numbered sections, authority section and appendices A-D, including table contents. Local source: `C:\Users\elite\OneDrive\Desktop\Elitewake_Integrated_Master_Game_Design_Bible_2026-09-21.docx`. SHA256: `5DD0001BC2F8BEA7A50361D0FF9074262288C6E70C737E88AC8950B557B2921F`. Reading this reference does not make the OneDrive backup an active development checkout.
3. **Historical development chat**: [View provided item](https://chatgpt.com/s/cx_6ac35bcf93fc819187d17835a7f29cac), reviewed in browser. It records owner decisions and reports of earlier work; historical assistant claims are not fresh verification.
4. **Development handoff** identifies the active path, five-person team, commits and M5 UI files. These match inspected history/source. The other pasted design text is an older general reference: its prologue, rejuvenation and control descriptions conflict with explicit replacements in the integrated Bible. A later paste does not establish an intentional new creative decision.
5. **Repository and tests** establish implementation, not creative intent. Local `286f8d0` contains the repaired inventory panel and initial production documents. GitHub `main` was read through the GitHub connector and remained at `9b7f129f5fe007d7ce77db1ddc97d44421f99341` during this review. The documentation correction follows `286f8d0` locally; no push has occurred.

The initial documentation in `286f8d0` relied on the shorter pasted design text. This review corrects that incomplete source selection. No gameplay code, source Bible, backup checkout or remote history was changed by reconciliation.

## Reconciled decisions

| Subject | Current reference / evidence | Resolution |
| --- | --- | --- |
| Team/title | Historical owner introduction and newer handoff | Five-person Elite Game Labs; Elitewake remains working title |
| Active project | Owner relocation approval, Git history, current workspace | `C:\UnrealProjects\EW`; OneDrive project is backup |
| Current milestone | Owner later says to begin M5; `9b7f129`, inherited UI, `286f8d0` | M5 In Progress. Earlier requests to finish survival/HUD do not make M4 fully complete; its remaining work stays tracked |
| Prologue | Bible §§21-22 explicitly replace September 20 opening; chat recap agrees | Storm battle/helm/cannons -> boarding/sword fight -> head injury -> Quartermaster dinghy rescue -> island amnesia/journal -> wood/campfire/tools -> small shipyard/raft -> player steers offshore/title -> docked raft at Village |
| Mission Two | Bible §22 | Quartermaster leaves; player speaks to innkeeper to start tour. First stop and subsequent content TBD |
| Raft vs sloop | Bible §§11.6,12.1,21.3 | Mission One escape uses raft. Persistent sloop retains helm/anchor/cargo/weight/two cannons/shared limited ammo; exact progression placement needs reconfirmation |
| Age regression | Bible §§6.8,15.4, Appendix C | Davy Jones supersedes Fountain/Horse of Youth. Victory returns age to 20, preserving level/skill allocation; trigger, repeatability and extra buffs TBD |
| Progression | Bible §7 | 15 cumulative skill points per level; respec from level 10 without level loss. Costs/cooldown/name/max level/tree costs TBD |
| Time cycle | Bible §4 | Four real hours of day + four of night = eight-hour full cycle. Weather dynamic; example timings are tuning guidance |
| Map input/actions | Bible §§5.10,10.2 and newer-control note in Appendix A | M / View-Select combined map-compass; walking allowed, sprint/stance/hotbar/inventory disabled while map open; no world pause |
| Controller hotbar | Bible §5.9 and Appendix A | Hold LB + face buttons/d-pad concept; exact implementation not present |
| Pause | Bible §2.2 | Single-player world pauses; multiplayer menu leaves world running/player vulnerable; map never pauses |
| Multiplayer/world | Bible §§2-3,18,23 | Single player and multiplayer planned, target up to 100 per session/world; four Village PvP safe zones; tribe friendly fire disabled; ordinary hostile pirate ships primarily player-controlled, ghost ships NPC |
| Death/logout/raiding | Bible §2.3 | Full carried inventory/equipment drops on death; sleeping bodies vulnerable; offline ship raid/sink permitted, cargo stolen without claiming ship ownership; wreck crates ~15 real minutes. Village logout ocean displacement is intended but requires playtesting |
| Animation | Owner rejected scaling and explicitly postponed integration; revert `e88acb1` | Keep animation postponed. Owner reported downloading two packs; download report is not imported/retargeted/verified assets |
| Scenario | Early chat lacked authorization; later owner says connected/authorized | Cursor authorization reported complete. Config URLs inspected; end-to-end Scenario access in this session not freshly tested |
| Inventory verification | Historical empty panel awaited Play test; fresh build/test/Play in this chat | `286f8d0` verifies empty local draft and recovery. No persisted Wood item asset, grant, pickup, equip behavior or multiplayer verification evidenced |
| Wood tuning | `EWInventoryComponentTests.cpp` creates transient Wood with stack 5 / weight 2 | Unit-test fixtures, not approved production item balance |

## Unresolved reference conflicts

- **Controller View/Select**: newer map rule assigns it to map/compass, while Appendix A retains it for radial commands. Preserve map binding; radial replacement remains TBD before either system is implemented. Do not invent a chord.
- **Stale Bible passages**: §24.4 still names Fountain of Youth despite explicit Davy Jones replacement; older treasure/shovel and return/sinking references remain elsewhere. Explicit replacement sections govern current direction; retained treasure systems remain valid outside the replaced opening.
- **Milestone numbering**: early chat planning uses inconsistent numbers. Keep the later M0-M5 handoff labels; Bible §24.3 build-order numbers are separate. Do not equate every milestone number with a Bible list item.
- **Shipyard scope**: the revised raft tutorial builds a small shipyard, while Shipwright gates broader shipyard progression. Record the tutorial requirement and postpone exact unlock handling to mission/progression design.
- **Death exceptions**: older prologue mentions retaining shovel through sinking; general death drops all carried gear. Revised opening changes that sequence; any future scripted retention exception needs explicit design, not accidental code behavior.

## Verification and publication limits

Latest editor build succeeded; `Elitewake.Inventory.StackingAndWeight` succeeded; local empty-panel Play check passed open/close/reopen, cursor/input transitions, walking and camera recovery. These do not establish dedicated-server readiness, persistence, final animation, controller UI, or populated replicated item references.

Before a future push, inspect status and the remote tip again, check the exact pending commits, and obtain explicit current push approval. The prior push to shared `main` was rejected by automatic approval review. The historical chat is context, not a workaround for that rejection. Keep the review correction in a separate local commit to preserve history.
