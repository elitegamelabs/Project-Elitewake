# Spider brief — October 18, 2026
G3. DECIDED (delegated), under the owner's current decision-making authorization. Design handoff; no runtime implementation.

## Identity
One spider species with two material variants, shared anatomy/rig/animations. Use the existing Art/Concepts/Animals/2026-10-12/giant_spider.png as the initial silhouette reference. Eight walking legs, two pedipalps distinct from legs, cephalothorax and abdomen, plausible fangs, no antennae or glowing markings. Cave: charcoal/dark brown with muted rust joint hairs. Swamp: dark olive-brown, subtle mottling. Keep exact eye/marking patterns consistent across the six views of each variant. Size/health/damage/density remain implementation tuning; art does not set them.

## Animation handoff
Idle with subtle leg/pedipalp movement; alternating leg-cycle walk; faster run; planted turn; alert/rear; bite anticipation/contact/recovery; directional hit; death/curl and transition; web contact/tear response. Climb/wall/ceiling variants only when locomotion supports surface attachment and navigation; do not fake a supported climb with floor animation. Smooth transitions and attack contact notifies; multiplayer hit windows remain authoritative.

## Audio handoff
Scuttle by stone/mud; quiet leg contact; faster scuttle; dry designed stridulation/chitter for alert (explicit fantasy foley, no claim of literal animal growls); fang motion/contact; body hit; death settling; silk movement and tearing. Never add a mammal growl or a voiced scream. Match contacts to animation and use existing spatialization/cooldowns. Scenario S3 rows queued for Claude; no credits spent here.

## Cobweb compatibility
Existing AEWCobweb is decorative, nonblocking and torn locally when a visible survivor passes through. RegrowSeconds=600, FallSeconds=2.5, ShredCount=7 in current source. Do not turn those webs into an authoritative trap/damage mechanic in this asset pass. Spider movement must not accidentally trigger survivor-only tearing or change regrowth; add any creature-web behavior explicitly in later code. Respect cave entrances, traversal routes, population performance and wildlife rest distance.

## Decisions and acceptance
The former one-species/two-species question is resolved to one species/two variants under delegation. Every cave and appropriate Southern Swamp ground needs placement in later implementation. Validate eight legs/pedipalps in every reference, grounded contacts, wall support where enabled, real attack contact and client agreement. The brief and queued audio are complete; rigs/clips/audio imports/spawning/Play checks are separate milestones.
