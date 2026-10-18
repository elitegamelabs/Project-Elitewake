# ChatGPT reference-art handoff — October 18, 2026
Baseline: main 6c0d7b25f338518062a0d347d8b5a1b37aac3dce; later own claim/report commits change documentation only.

## Verified source
The sloop, schooner and brigantine builders contain lower floors, stairs and raised stern decks. Main's sloop includes an aft furnished cabin and hull-owned mast structure. This differs from newer owner-decision documents specifying no sloop captain's quarters and removable sail assemblies including masts. No code changed here. No fresh Unreal checks run.
Recent commits reviewed: sloop rebuild 6c0d7b2, gunport covers d610439, flags d7147d2, seabed b21d818, plain railings 9658ad6, plus intervening documentation. Commit messages report checks; this handoff does not independently reproduce them.
No copper wallet/payment service or surgeon implementation was found in Source/EW or Scripts/Setup. Content/Elitewake/Items has no named copper-currency item. CopperOre art and DA_TestOre are not currency.

## Documentation and branch conflicts
CLAUDE.md and AGENTS.md retain older Cavalier-larger-than-Brigantine and flag-on-sail instructions. Newer ship-proportions branch documentation instead specifies comparable overall size with three traversable levels; the newer G7 branch explicitly excludes flags on sail modules. Preserve the newer direction; canonical reconciliation is pending.
Read all three chatgpt branches: owner-ship-proportions-modular-sails-20261018, g7-ship-module-reference-prompts-20261018, codex-sailing-rules-20261018. The G7 branch contains one combined prompt document, no images or per-module folders. The owner-proportions branch diverges from main; its files were read, not merged.
The sailing-rules branch records five base ship speeds, six whole-ship nonstacking sail modifiers, five deployment positions and fixed horizontal position with all sails down. Mixed-sail selection and slack propulsion remain unresolved. Finish shipbuilding before implementing sailing changes. No sailing behavior changed here.
Preserve the forward/backward-only swimming decision and existing backward/default animation; directional animation remains a separate task. Preserve regional tree assignments (Winter Birch, Jungle Ash, Desert Palm, Swamp Spruce, Plains Oak) and the latest elephant placement correction to Western Jungle. No wildlife/region changes here.
Claude's branch and the food-consumption branch had no unique changes ahead of inspected main. PR #1 (private Windows playtest release automation) remains open and unrelated; its description says no end-to-end Shipping package/release exists. Nothing was merged.

## Assets and remaining work
The current owner request and newer ship direction exclude scenery. G8's three seabed textures and ten flora/coral sheets remain OPEN and are not generated or integrated. Ordinary natural seabed life stays separate from the six glowing major reefs.
New built-in-generated ship sheets are concept references. Their construction details are proposals, not approved engineering. Mild perspective and cross-view detail differences need refinement before final modeling. A sheet does not satisfy six separately validated view files. Prompts and generation.json record actual output status.
Pending: five-class proportion/layout studies, five deployment states per sail, separate validated orthographic/attachment images, surgeon NPC/animation, additional flags/gunport/cannon/tool/weapon/equipment/crafting references, resource and animal six-view sets. G1-G5 remain open. Existing icons and source art are preserved.
The bounded delivery completes G6/G7 documentation and produces their first visual references. It does not declare the entire art backlog or gameplay complete.

## Delivery verification
Eleven PNG concept sheets decode at 1536x1024; hashes match provenance. All existing catalog entries are preserved and eleven reference entries added. Prompts/S7 queue/index updated. Visual review confirms no scenery or sail flags and no permanently mounted cannons in two-cannon railing. Mild perspective/detail differences remain; no exact orthographic set claimed complete. No build/Play tests run because this is art/documentation only.
