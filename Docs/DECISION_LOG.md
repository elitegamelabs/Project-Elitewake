# Decision log

Initialized: 2026-10-05 from supplied Design Bible, newer development handoff, inspected source and local Git history. Historical entries record existing decisions; proposed future work is labeled accordingly.

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
| D015 | Keep rarity colors undecided; retain current prologue sequence as evolving concept | Bible requirement | Changes need explicit design discussion; no rarity assignments introduced |
| D016 | Team is five developers; Project Elitewake remains working title | Newer handoff supersedes older Bible's solo-development context | Use newer production context without changing creative vision |
| D017 | No paid dependency additions; Meshy not assumed available; Scenario only for relevant assets | Handoff constraint | Existing integrations recorded, asset generation not needed for draft panel |
| D018 | M5 next slice: persisted Wood test asset and opt-in authority grant, then validated pickup | Proposed technical sequencing from authorized handoff | Stable asset references before replicated item testing; no final content balance implied |

## Open questions / deferred decisions

- Exact player encumbrance penalties and hard weight-cap behavior.
- Equipment transfer semantics when all inventory slots are full; item use/durability model.
- Respawn inventory ownership, persistence, owner-only inventory replication requirements.
- Final controller navigation/remapping and UI art/character preview approach.
- Full rarity definitions/colors, final ship handling balance, prologue pacing and hosting architecture.

## Recording changes

Add date, decision, reason, source of authority, related requirements/milestone, files, verification and commit. Label suggestions separately from approved design. Amend status when evidence changes; never erase the record of an experiment/revert or silently mark a foundation complete.
