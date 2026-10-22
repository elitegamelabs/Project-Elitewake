# Grok: your tasks

**Handoff rule (owner, October 22): before your usage runs out, close out what you have open, push, and write a `HANDOFF` entry in [INBOX.md](INBOX.md); at the start of each session continue any unpicked `HANDOFF` first ([TEAM_CHARTER](../TEAM_CHARTER.md) section 7).**

**Team rule (owner, October 22): everyone works freely; no locks, claims or ownership of anything.** See [../TEAM_CHARTER.md](../TEAM_CHARTER.md). Welcome, Grok. Read [../../GROK.md](../../GROK.md)
first. Status in this file is a courtesy notice only. Claude (manager) reviews what you push and writes the verdict in `Docs/REPORTS/<date>_Claude_Manager_Log.md`.

**Report in the shared inbox** ([INBOX.md](INBOX.md)) whenever you start, finish, get stuck or stop a task. Label every proposal as a proposal: the owner decides the design.
Your work reaches the team only when it is pushed to `main` or a visible branch.

## Tasks (October 22, 2026), all `OPEN`

### GR1. Review the October 22 gameplay branch
- **Where:** branch `claude/gameplay-fixes-20261022` (commits `6f74d47`, `9ff2373` and what follows); read `Docs/REPORTS/2026-10-22_Claude_Manager_Log.md` for what each piece is meant to do.
- **Do:** read `Source/EW/EWSurvivalComponent.*`, `EWProgressionComponent.*`, `EWSkillTree.*`, `EWDeathWidget.*`, `EWDeathBag.*`, `EWExplorationComponent.*`, `EWMapWidget.*`, and
  `EWCharacter::RespawnAfterDeath`. Look for multiplayer bugs (replication, authority, RPC abuse), edge cases and anything that contradicts
  `Docs/OwnerDecisions/GAMEPLAY_FIXES_AND_FEATURES_2026-10-22.md`.
- **Done when:** a list in the inbox, each item with file, line, why it is wrong and a suggested fix, ranked by severity. Do not fix by rewriting whole files; small fixes may be pushed directly.

### GR2. Skill tree expansion (a proposal)
- **Why:** the owner wants a constellation skill tree whose stars unlock recipes (`GAMEPLAY_FIXES_AND_FEATURES_2026-10-22.md` item 7). Today there is one nine-star constellation in `Source/EW/EWSkillTree.cpp`.
- **Do:** propose three more constellations (for example Hunter, Cook, Builder) of 8 to 10 stars each: names, positions on the 0..1 star map, prerequisites, costs, what each unlocks (recipes from the
  owner's starter list in `GAMEPLAY_DESIGN_DECISIONS_2026-10-22.md` item 9, cooking recipes of 5 to 12 s) and passive bonuses. Mark every number as tuning.
- **Done when:** `Design/Progression/SKILL_TREE_PROPOSAL_2026-10-22.md` exists. Claude or Codex will implement what the owner approves.

### GR3. The five islands as shapes (a proposal)
- **Why:** islands must be 1,500 to 2,500 m across with organic, irregular coastlines and distinct terrain (`AGENTS.md`; owner item 4). Plains, Winter, Swamp, Desert, Jungle: one each.
- **Do:** for each island write coastline control points (about 24 to 40 polar points: angle, radius in metres), the main landforms (mountains, ridges, valleys, caves, rivers, beaches, cliffs),
  landmark sites, resource and tree-cluster zones (primary trees: Plains Oak, Winter Birch, Swamp Spruce, Desert Palm, Jungle Ash), and the starter port on Plains. No two outlines may be rotations of each other.
- **Done when:** `Design/World/FIVE_ISLAND_SHAPES_PROPOSAL_2026-10-22.md` exists with a machine-readable block (JSON) per island that a Python script can read.

### GR4. Food chains and wildlife tables (a proposal)
- **Do:** from the regional lists in `GAMEPLAY_DESIGN_DECISIONS_2026-10-22.md` item 10 and the existing animal catalog (do not invent species or revive the manatee), write for each island who eats whom,
  densities per square kilometre, day and night behaviour, and warning behaviour before attacks.
- **Done when:** `Design/World/WILDLIFE_FOOD_CHAINS_PROPOSAL_2026-10-22.md` exists.

### GR5. Explorer's journal voice (a draft)
- **Do:** draft 12 journal entries in an old explorer's voice (short, atmospheric, useful): first day on the Plains, water, fire, cooking, the stars and the skill tree, the map and the mist, swimming,
  boarding a ship, each region's dangers. Mark them DRAFT; the owner approves text.
- **Done when:** `Design/Journal/EXPLORER_JOURNAL_DRAFT_2026-10-22.md` exists.
