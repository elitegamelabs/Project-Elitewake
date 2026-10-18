# Owner-approved sailing rules — October 18, 2026

Status: **Approved design; implementation deferred until Codex finishes current ship-building work.** Unreal Engine **5.8.3**.

## Codex priority and ownership
- **Continue the current ship-building and ship redesign tasks first.** Do not interrupt or replace in-progress ship-building work to implement this sailing change.
- Claude is unavailable for now; **Codex is the primary implementation agent** until the owner changes this direction.
- Treat this document as the queued next sailing task, **not permission to start it immediately**. Follow existing claim, coordination, editor-lock, test and verification rules. Do not overwrite other agents' work.
- Preserve the latest owner-approved ship dimensions, modular sail hardpoints, stern-center ladders, and shipyard crafting requirements.

## Base maximum speeds (full sail, favorable wind)
| Vessel | Base speed |
|---|---:|
| Raft | 3 knots |
| Sloop | 8 knots |
| Schooner | 10 knots |
| Brigantine | 12 knots |
| Cavalier | 14 knots |

## Craftable sail modifiers
| Sail | Whole-ship speed multiplier |
|---|---:|
| Small | 1.30x |
| Small weighted | 1.25x |
| Medium | 1.50x |
| Medium weighted | 1.40x |
| Large | 1.80x |
| Large weighted | 1.70x |

These multipliers affect **whole-ship speed**, not a separate multiplicative bonus for each installed sail. Do not stack modifiers per hardpoint. If multiple sail types are installed, their combined selection rule is **TBD**; do not invent one.

## Sail deployment and wind
- Apply to both regular and weighted sails. Sails are modular craftable items attached to ship hardpoints; base ship models do not have permanently installed sails.
- When a sail catches wind, its applicable modifier can engage; when it goes slack because it is not catching wind, its **bonus** is removed, returning toward the ship's ordinary speed as permitted by deployment.
- Increasing sail deployment increases speed, including partially raised sails. Keep the approved five deployment positions **0%, 25%, 50%, 75%, 100%** and progressive raise/lower helm controls.
- Weighted sails provide better stability/handling in strong wind when catching it. Exact stability coefficients are **TBD**.
- At **0% deployment across all sails**, immediately set horizontal ship velocity to zero and hold the ship's horizontal world position fixed. **No drift, coasting, sideways motion, or current/wind/wave displacement**, regardless of weather. Cosmetic bobbing and rocking are allowed without changing horizontal location.
- Once any sail is raised above 0%, sailing propulsion may resume when catching wind. Wind angle and sail orientation matter; ship heading alone is not a substitute for sail-wind alignment.
- Do not assume nonzero propulsion from a slack sail; reconcile the owner's 'base speed when slack' rule with wind-dependent propulsion during implementation and flag any ambiguity before selecting tuning.
- These are **design requirements only**; verify in multiplayer and Play tests before reporting gameplay complete.

## Acceptance checks
Verify each ship's base speed, each sail modifier, progressive deployment, slack versus filled sails, weighted handling, and complete zero horizontal displacement with all sails down during wind, waves, and currents. Document observed results in Docs/VERIFICATION.md. Do not claim implementation based on this design document.


Publication note (October 18): copied as reviewed owner-decision documentation from the existing chatgpt branch into main by a direct documentation commit. No branch merge or implementation is implied. Later gap-filling choices are in Docs/REPORTS/2026-10-18_ChatGPT_Delegated_Decisions.md.
