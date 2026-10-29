# Claude daily report, October 28, 2026

Working alone on the game (owner: Grok removed from the repository, Codex at its limit; solo rule in `CLAUDE.md`).

## Done and checked in Play
- **Crystals, obsidian and coal:** items, meshes, gem material, 62 mineable nodes in caves and Winter mountains. Single-player check
  `verify_crystals_play` and two-player check `verify_crystals_multiplayer_play` pass. Every cave also has 30 decorative crystal clusters with coloured lights (150 in all). Inventory icons added today are drawn
  placeholders and have not been looked at in the inventory screen.
- **Cave spiders:** rebuilt larger (about 1.7 m long, over 3 m across) with banded jointed legs and a dark palette. The earlier
  pale look came from vertex colours reading back brighter than authored. `verify_spiders_play` passes. Still a procedural model:
  it does not look like the concept art and needs the Scenario generation.
- **Rideable spider:** E climbs on, move input steers along the camera, Jump gets off. Single-player and two-player checks pass.
  Seat height is tuning; no saddle requirement yet; the rider stands on its back.
- **Master volume:** slider on the OPTIONS tab, saved in the user settings, Play-checked.
- **Saving:** `SaveSurvivor` now refuses while dead, attached to a ship or mount, or on a ladder (GR1 findings 1 and 4).

## Documents
- GR1 code review (`REPORTS/2026-10-28_GR1_Gameplay_Code_Review.md`): 10 findings; equipped-item loss on a full pack and the
  death-bag access rule are still open.
- GR2 skill-tree proposal, GR4 food chains, GR5 journal draft: all proposals or drafts awaiting the owner. GR3 not written.

## Blocked
- Scenario plan limit (1,500 custom generations, 1,498 used): no new 3D models or audio until the plan is upgraded or renews.
  The spider concept image is already uploaded (`asset_JiuwMoxM4H9MhhxsASLbfvKL`) for a Meshy run at the same settings as the
  other animals. Spider audio and extra animations wait on the same limit (audio) or on that model (animations).

## Open
- Spider audio, bite/hit/death/web animations; the seated rider pose; re-fit of the ride seat when the generated model arrives.
- Cave crystal lighting tuning (blue wash from the sapphire lights). Elephant tree-push two-player check and Winter crystal nodes are done (see below).
- Visual tuning of cave lighting for the crystals (the caves are dark).

## Later today
- **Crystals redone as chunky clusters (owner request):** one fat tall crystal, a thick ring around it and stubby ones at the foot on a wide
  rock base, roughly twice the size (node scale 1.8 to 2.4, decor 1.2 to 2.4; sizes are tuning). Seen in Play; single-player and two-player
  crystal checks pass. The pale blue wash on the emerald is the sapphire cave lights; light colour and intensity still need tuning.
- **Elephant tree push, two players:** `verify_elephant_tree_push_multiplayer_play` passes (the client sees the felled tree, which stays
  down and does not fade).
