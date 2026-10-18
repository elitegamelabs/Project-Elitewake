# Ship surgeon brief
Updated October 18, 2026. G6. Design handoff; no surgeon gameplay implemented by this change.

## Confirmed owner requirements
Every ship with a walkable deck below its top has an always-present surgeon in the rear left corner of the first deck below the top. Include an operating table, scissors/tools and shelving. Treatment costs 15 copper and gradually restores 25% of maximum health, with an animation and multiplayer safety.

## Current source evidence
Inspected main 6c0d7b2; subsequent own claim/report commits change documentation only.
- Sloop: build_sloop_hull.py constructs a walkable hold floor, HATCH stairs, and a raised stern deck with a cabin beneath. Structurally qualifies.
- Schooner: build_schooner.py constructs lower_deck(), hatch stairs and a raised quarterdeck with a cabin beneath. Structurally qualifies.
- Brigantine: build_brigantine.py constructs gun_deck(), hatch stairs, quarterdeck and forecastle. Structurally qualifies.
- These are source inspections, not a fresh Unreal traversal check. Where a quarterdeck exists, the meaning of first deck below the top needs confirmation; do not silently choose the deepest hold.
- Cavalier has three approved traversable levels; apply the same rule when built. No Cavalier builder was found in the inspected main tree. Raft/dinghy do not qualify without a walkable lower deck.
- Source-wide copper/currency/surgeon search found no payment service or surgeon implementation; one schooner crew comment mentions Surgeon. No named copper-currency item appears in Content/Elitewake/Items. DA_TestOre maps to a CopperOre icon: ore is not currency. Currency concept art does not implement payment.

## Layout and props
Interpret rear left as aft-port facing the bow; confirm this interpretation. Reserve the corner on the qualifying deck, with approach, table entry and safe exit clear of stairs, hatches, frames, mast sockets, gun recoil, doors and stern-center boarding routes. Keep the surgeon beside the table. Shelves need retaining lips or straps.
Props: secured timber operating table, reusable plain linen pad, scissors, forceps, small tool tray, secured shelving. Generated prop construction is a proposal, with exact dimensions TBD. Do not add captain's quarters to the sloop: newer owner direction removes them even though main currently builds an aft cabin.

## Interaction and multiplayer
Confirmed sequence: approach, request treatment, pay 15 copper, lie on the table, play treatment animation, receive gradual healing of 25% maximum health.
Suggested contract: the server validates reach, living patient, available station, missing health and canonical copper balance; atomically reserves the station and charges once. Reject replayed/duplicate requests. Server owns healing and clamps at maximum health; all clients see the same patient, surgeon and treatment state. Attach the station/patient appropriately to the moving ship.
Suggested no-benefit behavior: full health offers no purchase and charges nothing. Insufficient copper leaves the patient free to move with a clear price message. No automatic repeat purchases.
Suggested interruption behavior: stop future healing on cancel, death, disconnect, sinking/unusable station or departure; release reservation and restore a safe exit when feasible. Refunds, partial charges, retained healing and allowed interruption causes remain owner questions.

## Open questions
- Does top mean highest quarterdeck or main weather deck? Confirm the exact aft-port corner per class.
- How is copper represented, earned and spent? Never use Copper Ore as payment.
- Treatment duration, healing cadence/curve, animation assets, patient controls, cooldown and refund policy are TBD.
- Is the station exclusive to one patient? What ship access permissions apply to enemies and other players?
- Suggested interpretation: restore a fixed amount equal to 25% max health, capped at full, for the same price when less health is missing; owner confirmation pending.

## Acceptance handoff
Keep references, separate six-view files, models, animation, currency, integration and in-game checks separate. Check qualifying-deck traversal; busy/no-copper/full-health rejection without charge; one charge; gradual capped healing; cancellation/disconnect cleanup; listen-server/client agreement; treatment aboard a moving ship. No implementation checks run by this art handoff.
Table/tools prompts are in Art/Reference/Ships/SurgeonTable/PROMPTS.md and SurgeonTools/PROMPTS.md. Scenario S7 remains queued for pricing by Claude if needed; built-in-generated concept sheets spend no Scenario credits.

## Delegated resolutions — October 18
The open choices above are now resolved by the owner's decision-making delegation: first level below main weather deck, aft-port; integer copper wallet; one patient; 20-second gradual treatment; server charge/heal; no charge without benefit; interrupt on cancel/movement/attack/damage/death/disconnect/sinking; no refund after healing starts. See Docs/REPORTS/2026-10-18_ChatGPT_Delegated_Decisions.md for the complete contract. These choices are requirements/tuning, not implementation.
