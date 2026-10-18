# Decisions made under the owner's delegation — October 18, 2026

Authority: the owner asked ChatGPT to make the choices it expects the owner would make, approve remaining decisions and continue working. All choices below are DECIDED (delegated), reversible by the owner/Claude. They are implementation requirements, not claims of runtime behavior. Earlier explicit owner decisions remain unchanged. No gameplay code, merges or Scenario spending are authorized by this document.

## Scope and wildlife
- Complete existing approved species before adding proposed deer, wolves, jaguars, camels or other suggested roster additions. Suggestions remain deferred, not approved new wildlife.
- Keep bears in Northern Winter, lions in Central Plains, giant crocodiles in Southern Swamp and elephants in Western Jungle. Horses remain Plains, Snow Leopards Winter. Preserve existing six coastal animals and eight aquatic kinds.
- Use the existing grizzly/brown-bear reference as the Bear G4 production-reference identity; this does not remove the existing black-bear concept or approve a new spawn entry. Preserve lion/crocodile/elephant identities from the existing concept images.
- One spider species with cave and swamp material variants sharing a rig and core animations. Cave: dark charcoal-brown body and muted rust joints; Swamp: dark olive-brown body and subdued mottling. Eight legs, two pedipalps, two main body sections, no extra limbs/glowing markings. Exact size/combat statistics stay existing-owner/implementation tuning rather than art-invented numbers.
- Mantas have no functional sting. Keep the mismatch in the current sting attack visible to the implementation owner; use non-stinging manta references. Do not change the existing game behavior in this art pass.

## Elephant obstruction rules
- Only trees explicitly tagged destructible and ordinary movable/destructible clutter may be pushed when blocking an elephant's valid route; eligible Jungle trees include Ash and Maravai. Do not push arbitrary nearby objects or flatten a roaming corridor for decoration.
- Never damage Ports/docks, player buildings, ships, caves/terrain, landmarks, quest objects or protected/indestructible geometry. Protection tags override destructibility. Avoid protected obstacles by navigation; if no route exists, choose another destination.
- Telegraph a push with a pause, trunk/head/body contact animation, creak/crack and foliage/impact; server-authoritative state, client-visible fall. Do not duplicate collision damage/loot from cosmetic physics. Use current regrowth/resource rules until a separate implementation change is tested.

## Surgeon
- First deck below the top means the first walkable level below the main weather deck, not the roof of a raised aft cabin. Place at aft-port facing the bow: sloop hold, schooner/brigantine first lower deck, Cavalier middle deck. Preserve clear access and cannon recoil zones.
- Canonical integer copper wallet, not Copper Ore inventory consumption. Preserve 500 copper to silver and 30 silver to gold display conversion; no new ore/currency item duplication.
- Treatment duration 20 seconds (delegated tuning); heal continuously for 25% maximum health capped at full. Charge 15 copper once when treatment starts; no charge on full health, insufficient funds, occupied station or validation failure.
- One patient per station. Explicit interact purchase; no automatic repeat. Ship-authorized allies may use it. Movement/cancel, attack, incoming damage, death, disconnect or sinking stops further healing and releases the station. No invulnerability. Full refund if treatment never starts; no refund after healing begins; already delivered healing stays. No extra cooldown beyond station occupancy.
- Server validates/reserves/charges/heals. Clients cannot submit amounts. Exit safely with the moving ship and release on loss of station.

## Sailing decisions queued after shipbuilding
- Retain all owner-approved base speeds and six whole-ship multipliers. Multiple sails do not stack: take the highest effective contribution among installed wind-catching sails. For a sail with deployment d from 0 to 1 and approved multiplier m, its effective cap contribution is d*m; apply the largest eligible value to the class base cap. This is a speed cap, not guaranteed propulsion.
- A slack sail generates no propulsion/bonus. Any remaining motion while some sail is raised follows the existing drag model; never invent powered motion from slack cloth. If every sail is at 0%, immediately hold horizontal position with zero horizontal velocity as explicitly required.
- Retain 0/25/50/75/100% controls. Weighted sails use 10% more roll/pitch damping when catching strong wind (delegated tuning); do not silently alter hull health, cargo or base speed. Shipbuilding remains first.

## Existing world tuning retained under delegation
Keep the inspected 500–900 m non-starter island range and about 620 m starter extent; 500 tree, 220 rock and 220-per-plant caps; 200 m wildlife rest distance; 600 s cobweb regrowth with two passage webs and three chamber webs per cave; current per-region terrain-plan vocabulary; sparse Maravai beneath Jungle Ash. These are retained delegated tuning, not newly generated scenery or proof of Play verification. Latest explicit Plains tree reduction remains authoritative.
