# Decision log

Initialized: 2026-10-05 from supplied Design Bible, newer development handoff, inspected source and local Git history. Historical entries record existing decisions; proposed future work is labeled accordingly.

Reconciled later on 2026-10-05 with the September 21 Integrated Master Bible and linked historical chat. [Source reconciliation](CONTEXT_RECONCILIATION.md) records the authority correction; shorter pasted design text does not override explicit integrated-Bible replacements. Earlier local documentation is retained in `286f8d0` history.

| ID | Decision / rationale | Status and authority | Impact / evidence |
| --- | --- | --- | --- |
| D001 | Active project is `C:\UnrealProjects\EW`; OneDrive copy is backup | Implemented; handoff and working directory verified | Builds/launches/Git target active path; `919737f` baseline |
| D002 | Ship is home; keep Prepare/Sail/Discover/Fight-or-Explore/Loot/Escape/Upgrade loop | Design authority: Bible + handoff | No central vision change authorized; all later systems support it |
| D003 | 0.01 first playable slice precedes large online infrastructure | Confirmed reference | Proposed roadmap sequences dependencies; no MMO-first build |
| D004 | C++ gameplay foundations, Blueprint assembly, data-driven assets, Enhanced Input; server authority | Implemented foundation; `50ecc95` and subsequent source | Replicated code still requires multi-client and dedicated-server tests |
| D005 | Walk 500, sprint 750; crouch/prone tap/hold 0.35s | Implemented `d8ca1dc`, `5f08eb7` | Tunable defaults, not final balance |
| D006 | Revert temporary stance scaling; postpone proper animations until suitable assets | Replaced/Postponed; `cf282a8` -> `e88acb1`; handoff | Preserve gameplay/collision states without unnatural shrinking |
| D007 | Third-person default, dedicated first-person camera and local Z toggle; cyan diagnostics temporary | Implemented `fb214b3` | Perspective-specific final animations remain pending |
| D008 | Survival component holds replicated stats; stamina drain 15/s, recovery 10/s | Implemented `55ed2c1` | Hunger/temperature values are groundwork, not full needs/environment gameplay |
| D009 | Inventory uses 24 default slots, item definitions, server mutation and weight-to-survival sync | Implemented `9b7f129` | Slot cap enforced; displayed max carry weight does not enforce weight cap. Encumbrance behavior undecided |
| D010 | Native UMG panel and runtime I action provide a functional draft | Verified local empty panel; inherited four UI files preserved | Incremental scope departure from full Bible UI: Y/navigation/highlight/preview/crafting/hotbar pending; avoids premature artwork |
| D011 | Build native widget tree before Slate rebuild instead of NativeConstruct | Technical repair Verified 2026-10-05; Git title `Fix and verify native inventory panel` | I changed cursor but original panel invisible; `EWInventoryWidget.*` lifecycle fix; build, inventory automation and local Play retest passed |
| D012 | Do not infer equipment behavior from equipment-slot enum | Documentation decision 2026-10-05 | Equip/unequip, appearance/protection and atomic transfer are Planned |
| D013 | Keep NPCs deterministic; cosmetic skins separate from gameplay stats | Bible requirement | Applies to future NPC, clothing and sail systems |
| D014 | Village terminology; limited Ferryman routes; fixed currency conversions | Bible requirement | 100 Copper=1 Silver; 500 Silver=1 Gold; not implemented economy |
| D015 | Keep rarity colors undecided; prologue remains evolving concept | Bible requirement; prologue source corrected in D019 | Original entry relied on older treasure-first reference; revised Bible §§21-22 now govern. No rarity assignments introduced |
| D016 | Team is five developers; Project Elitewake remains working title | Newer handoff supersedes older Bible's solo-development context | Use newer production context without changing creative vision |
| D017 | No paid dependency additions; Meshy not assumed available; Scenario only for relevant assets | Handoff constraint | Existing integrations recorded, asset generation not needed for draft panel |
| D018 | M5 next slice: persisted Wood test asset and opt-in authority grant, then validated pickup | Proposed technical sequencing from authorized handoff | Stable asset references before replicated item testing; no final content balance implied |
| D019 | Revised storm battle/Quartermaster rescue/journal/campfire/shipyard/raft opening replaces treasure-first prologue | Confirmed Bible §§21-22; historical recap agrees | Mission Two starts by talking to innkeeper after Quartermaster leaves. Tour/post-tour TBD; no implementation changed |
| D020 | Davy Jones age-regression boss replaces Fountain/Horse of Youth | Confirmed Bible §§6.8,15.4, Appendix C | Age returns to 20; level/skill allocation preserved; buffs/trigger/repeatability TBD |
| D021 | 15 cumulative points per level; respec from level 10 without level loss | Confirmed Bible §7 | Costs/cooldown/name/max level/tree balance TBD; not implemented |
| D022 | Day and night each last four real hours | Confirmed Bible §4 | Eight-hour full cycle; weather timing remains tunable; not implemented |
| D023 | Combined map/compass uses M and View/Select; walking allowed, sprint/stance/hotbar/inventory blocked; world remains live | Confirmed newer Bible §§5.10,10.2 | Appendix radial View conflict unresolved; controller radial replacement TBD, no invented chord |
| D024 | Eight-slot hotbar controller concept uses hold LB with face buttons/d-pad | Confirmed Bible §5.9, Appendix A | Exact item-use/selection implementation pending |
| D025 | Single-player pause freezes world; multiplayer menu does not; map never pauses | Confirmed Bible §2.2 | Separate from editor Escape behavior |
| D026 | Four safe Villages; up-to-100 multiplayer target; tribe friendly fire disabled; normal hostile pirate ships primarily players | Confirmed Bible §§2-3,18 | Ghost ships are hostile NPC vessels; target is not tested capacity |
| D027 | Death drops carried inventory/equipment; sleeping bodies and ships vulnerable offline; raiders loot without taking ship ownership | Confirmed Bible §2.3 | Wreck crates ~15 real minutes; Village logout displacement needs playtesting; normal death progression effects TBD |
| D028 | Mission One uses raft; persistent two-cannon sloop concept remains | Confirmed Bible §§11.6,12.1,21.3 | Exact sloop progression placement and tutorial Shipwright exception need reconfirmation; no ship implementation yet |
| D029 | Continue M5 while retaining M4 unfinished HUD/needs/testing backlog | Later historical owner explicitly begins M5; source inspection | Earlier survival-next recap is superseded as immediate task order, not acceptance of full M4 completion |
| D030 | Animation packs reported downloaded; integrate later; Scenario authorization reported complete in Cursor | Later owner messages in historical chat | Not verified imported/retargeted animation or Scenario access in current session; Cursor remains optional |
| D031 | Hold remote publication until cross-reference review and explicit push approval | Current owner instruction 2026-10-05 and prior automatic review rejection | `286f8d0` local; GitHub main read at `9b7f129`; reconciliation changes documentation only |

## Open questions / deferred decisions

- Exact player encumbrance penalties and hard weight-cap behavior.
- Equipment transfer semantics when all inventory slots are full; item use/durability model.
- Respawn inventory ownership, persistence, owner-only inventory replication requirements.
- Final controller navigation/remapping and UI art/character preview approach.
- Full rarity definitions/colors, final ship handling balance, prologue pacing and hosting architecture.
- Controller radial-command replacement for View/Select; map has newer confirmed claim on that button.
- Mission One tutorial shipyard unlock/cost versus broader Shipwright gate, and persistent sloop placement after raft.
- Ordinary-death progression retention, maximum level, respec cost/cooldown/name and exact skill point costs.
- Davy Jones trigger/repeatability/extra buffs; Mission Two tour first stop and subsequent sequence.
- Hunger/hydration rates/damage, weather distributions, food/spoilage/farming tuning, diving limits and biome resource distribution.

## Recording changes

Add date, decision, reason, source of authority, related requirements/milestone, files, verification and commit. Label suggestions separately from approved design. Amend status when evidence changes; never erase the record of an experiment/revert or silently mark a foundation complete.
