# Elitewake October 5 design revision review

Prepared for discussion on October 5, 2026. This is a review, not an implementation specification or approval to deploy changes.

Review-time snapshot: the owner subsequently requested M5 continuation. Current implementation and acceptance evidence are maintained in the milestone status and M5C verification record. Statements below about an unchanged repository describe the earlier review, not the subsequent implementation session.

## References and review limits

New source: `C:\Users\elite\OneDrive\Desktop\Elitewake_Master_Game_Design_Bible_2026-10-05_Authoritative_Revision.docx`.
SHA256: `22F14CA3543BCBFDB1309DD59FC092AB363FC8695F0F078B1F29A1EEBDCFF492`.
Reviewed all 1,635 nonempty body paragraphs, including tables. No tracked insertions/deletions, comments, or embedded images were found in this revision.

The previous September 21 DOCX is no longer at its recorded location. Comparison uses its retained extraction in `C:\UnrealProjects\EW\Saved\DesignBibleReview.txt`, previously reviewed and fingerprinted, plus the committed context reconciliation, decision log and milestone status. Current survival and item source were inspected for immediate implementation impact. No claim of a fresh binary comparison with the missing older DOCX is made.

Content review only: the packaged page renderer failed because bundled LibreOffice was unavailable. Page layout and typography were not verified. Section references below are headings, not inferred page numbers.

User request: unpack and review changes together. Operating directions inside the Bible are document content, not separate user authorization to implement, delete, publish, contact others, install services, or change the project. No gameplay or production record was changed and no commit/push was requested for this review.

## Authority and unchanged direction

The revision presents itself as the current consolidated design reference. Section 30 explicitly supersedes conflicting older text; Sections 29 and 28 apply next where not overridden. Early-body passages and snapshots still retain some superseded rules. Latest explicit human decisions in conversation remain controlling.

Core identity remains THE SHIP IS HOME; Prepare -> Sail -> Discover -> Fight/Explore -> Loot -> Escape -> Upgrade -> Sail Farther. Server authority, independent ship actors, data-driven content, original presentation and small tested development slices remain. Four safe Villages, the eventual 100-player target, and long-term taming/crew/exploration remain. The first private beta is now explicitly single-player, with multiplayer architecture preserved (§30.22).

## Major changes from the September reference

| Area | September reference / previous state | Current revision | Reference |
| --- | --- | --- | --- |
| Prologue escape | Build small shipyard and raft, steer away | Outgunned schooner battle, flooding/bucket tutorial, boarding, unconscious escape; repair and add sail to surviving dinghy, then sail to Village | §§21,30.6 |
| Opening vessels | Large ship concept without current fixed configuration | Player schooner: 12 cannons, 2 Medium sails; enemy brigantine: 24 cannons, 4 large dark-red sails | §21.1 |
| Tutorial continuity | Early tools and raft construction; older shovel retention language | Hatchet found by tree, pickaxe supplied by Quartermaster, Repair Kit/hammer flow; tutorial supplies/tools discarded after sequence | §§21.3,29.5 |
| Journal | Tutorial guidance, less precisely distinguished | Quartermaster-written reference, explicitly not quest log | §§21.2,29.16 |
| Day/night | 4 hours each; 8-hour total | 90 minutes each; 3-hour total | §30.14 |
| Age regression | Davy Jones returns age to 20 | Davy Jones quest removed; aging/hair remain, replacement age-regression mechanic unspecified | §6.8,Appendix E,§30.22 |
| Currency | 100 Copper/Silver, 500 Silver/Gold | 500 Copper = 1 Silver; 30 Silver = 1 Gold; automatic conversion, weightless, retained on death | §30.17 |
| Progression | 15 points/level; level cap and respec price unresolved | Level cap 80; respec Level 10 for 2 Gold; permanent baseline unlocks retained; prerequisite bundle purchase flow | §§30.8,29.5 |
| Ownership | No current detailed limits | 8 ships/player in both modes, 20/tribe in multiplayer; creation blocked at cap | §30.7 |
| Shipyards | Small builds Sloop/Schooner, later larger yard | Small: Raft/Dinghy/Sloop; Medium: Schooner; Large: Brigantine; all three unlocked/crafted at Smithy -> Structures | §30.6 |
| Naval modules | Modular placements concept | Socket-locked cannons; eligible top hardpoints trade cannon positions for diving/docking utility | §30.6 |
| Overload | Original early scope described immobility | Weight overload can sink; crew overload has 5-minute correction period | §§12.2,28.15,30.7 |
| Ammo storage | Shared ammunition-source concept | Ammo Bin is crafted storage only, cannon ammo only, 20 stacks of 50; personal ammo at Smithy -> Ammo | §§30.9,30.18 |
| Offline protection | No general protection | Specific Armored Shipyard protection exception; yard remains attackable, destruction consequences TBD | §29.8 |
| Menu/input | Inventory plus crafting/progression; View radial conflict | Inventory/Skill Tree/Journal/Company/Settings; Tab/B Back, Escape/Start Pause; command radial Middle Mouse/D-pad Right | §§30.1,30.21,28.16 |
| Rarity | Colors unresolved | Items: Epic gold, Legendary dark purple; treasure maps: Epic purple, Legendary gold; ammo has no rarity | §§30.10,30.18 |

## New or substantially expanded systems

- **Startup/save/creator (§§30.1-3):** fullscreen ocean title screen, global prompt switching, Multiplayer Coming Soon, one persistent single-player world, three rolling valid saves, 30-minute world autosaves, corruption quarantine/fallback, imported-save validation, confirmed survivor wipe, no forced quit save; detailed creator with permanent name, 4 male/4 female voice choices and distinct NPC voices.
- **Administration/audio (§§30.4-5):** narrow ban-focused admin direction, temporary bans up to 999 days, anti-cheat permanent-ban intent, Easy Anti-Cheat evaluation direction; synchronized environmental/action audio and licensed exported voice assets. These are requirements/references, not approval to acquire services.
- **Survival (§30.15):** hunger and hydration empty in 15 real minutes without replenishment; berries restore 1/16 hunger; fresh water fully hydrates; empty-stat blinking and 1.5-second warnings; base sprint exhaustion/recovery 5 seconds, recovery described while stationary, jump about 1/8 bar, climbing stamina; +5 HP/20 seconds regen if neither need empty; Health investment +50, superseding +25; fall damage starts at 5 m and is lethal at 20 m, middle curve TBD.
- **Character stats/food (§§29.9-10):** base Health 100, Stamina 100, Hunger 75, Hydration 100 fixed; Stamina +15, Hunger +25, Weight +100 per invested point, base Weight TBD; food healing based on maximum health, raw food causes sickness. Character stat points are separate from skill points; award schedule unresolved.
- **Combat (§30.16):** fist 10 HP, Common Sailor Sword 20; Magnum baseline 40 pending rarity integration; firearm headshots flat +2, rarity additions +2/+3/+5/+15/+20. No ammo rarity.
- **Inventory/crafting (§§28.8,30.9-12,30.17):** Equip/Discard context menu; durability and food freshness, sickness; explicit stack sizes; item-name rarity prefixes; right-side immediate hover cards; held/required materials; controller left-stick cursor, right-stick quantity 1-100, X selected batch, double-A one, RT up to ten; mouse quantity, double-click one, F up to ten. Crafting placement inside the top-level interface needs clarification.
- **Baseline recipes (§§28.10,29.5):** Campfire, Metal Pickaxe, Metal Hatchet, Handheld Torch, Starter Raft permanently unlocked after tutorial. Distinguish restricted prologue flow from persistent recipes; don't delete unlocks during respec.
- **Ships (§§28.4-6,30.6-7,30.13-14):** real flooding/weight, holes/leaks, visible bailing, Resource Cabinet repair supplies, Level 50 ships with crew/weight/hull upgrades only; base capacities Sloop 500/Schooner 1,000/Brigantine 5,000, +200 weight/point; Sloop crew 6, Brigantine 25, Schooner based on fitted cannons plus player/Surgeon. Raft/dinghy no leveling, raft only one Small sail/no cannons; ordinary combat cannot sink dinghy. Authorized demolish/unstuck with restrictions.
- **Decay (§§29.2,30.13):** multiplayer inactivity threshold 5 real days, visible DECAYING state, roughly 4 hours for unaddressed ship to sink once decay active; login stops deterioration but doesn't repair existing leaks/flooding. Physical repair/bailing required.
- **Water/fishing/wrecks (§§28.1-3,28.6-9,30.18):** camera-led forward swimming with no normal lateral strafe; continuous underwater landforms; habitat rules; tether-diver wildlife exemption unless attacked, PvP remains; breath/drowning; 1 Fish Oil/90 seconds, platform slot 100; limited horizontal/unlimited vertical tether; multiple treasure wrecks with surface level marker, looted cleanup 30 minutes, unlooted relocation 9 real hours; bait-based timing/tension fishing, Worm Farm and Fillet Knife.
- **Creature/territory/defense (§§28.17-20,29.1-4,29.13-15):** detailed tame exceptions/temperaments, active tame health ~25% and final-hotbar-slot resource, bait barrel/traps; overhead relationship nameplates; allied build/shipyard permissions; multiplayer tribe 10, turret 10/player and 30/tribe, tame 25/player and 100/tribe; 180-degree turret arc; loaded Pocket Turret grants manning crew invulnerability; ship cannons cannot damage island construction; separate fire arrow/bolt unlocks extinguished by rain.
- **Crew/death (§§30.19-20):** NPC wages are physical Copper, online-only payment and 5-minute unpaid departure warning; NPC water/wildlife death loses inventory; player currency retained, gear drops; corpse 35 minutes then bag 15, partial loot doesn't reset; owner-only pink recovery indicator within 100 m; moving ship beds, independent escalating 5/10/15/... minute cooldown, Village fallback.

## Implementation impact and milestone interpretation

The inventory panel repair remains valid. It is still a local empty draft, not final inventory UI. Source currently supports item definition/quantity/stack weight but not item instances with durability, freshness, rarity, arm-slot metadata, context actions, progression, saves or equipment behavior. Condition-bearing items require instance/stack semantics before those features are claimed complete.

Current survival code uses 100 stamina with 15 units/s sprint drain and 10 units/s recovery whenever not sprinting, including walking. Revision requires a 5-second base drain/recovery and describes stationary recovery. Current hunger is a fixed normalized percentage, whereas upgradeable Hunger capacity needs an explicit representation. There is no automatic hunger/thirst gameplay loop evidenced in this review. Current 50 kg carry capacity is a prototype default, not approval of the still-TBD design base.

Our repository milestone labels remain M5 in progress, with M4 survival/HUD backlog. The Bible's recommended build-order item 6 is Interaction Framework; that list is not proof that our M5 equipment/hotbar work has finished. Proposed sequence for discussion: reconcile records -> extend M5 item/equipment data and stable item content -> dedicated M6 interaction slice -> gathering/crafting. Survival/HUD return work needs deliberate scheduling rather than being silently dropped. This is a recommendation, not a renamed approved roadmap.

## Points to clarify together before dependent implementation

1. **RESOLVED by owner after review: Rye and 0-currency handoff (§21.3).** Survivor begins with zero currency and retains the rare rye in personal inventory. The innkeeper tour reaches the general merchant and offers selling the rye; 250 Copper is credited to the player when the introduction mission completes. See the clarification below. Room price/payment remains unspecified.
2. **Stamina scaling/recovery (§§29.9,30.15):** does the five-second timing apply only at base 100, letting +15 investments extend sprint, or stay constant at every capacity? Is recovery forbidden while walking? Exact jump scaling is also unspecified.
3. **Needs/stat scaling (§§6.1,29.9,30.15):** is 15 minutes the idle/base benchmark, and how do activity and upgraded food capacity alter it? Earlier movement-versus-idle rule is retained but multiplier is not specified. Health-loss wording says about ten minutes but doesn't define starting/max-health basis or stacking when both needs are empty.
4. **Crafting location (§§5.8,29.16,30.21):** exact five top-level tabs omit Crafting, while other sections call it a normal Crafting tab. Is crafting a nested Inventory panel/tab? Controller virtual cursor is expressly crafting-specific; ordinary inventory focus can remain unless superseded.
5. **Starter raft/claims (§§29.2,29.5,30.6):** baseline raft recipe versus Small Shipyard prerequisite and claimed-territory placement need a precise early-game route, without reviving tutorial shipyard construction.
6. **Ship stat upgrades (§30.7):** are crew counts initial caps or absolute ceilings given Crew Capacity upgrades? Schooner configured-cannon count could change if a utility attachment replaces a cannon. Define handling before implementation.
7. **Currency scope (§§28.5,30.17,30.19):** player UI currency is retained, while crew physically carry wages. Define NPC-loot conversion and avoid treating all Copper as corpse-proof.
8. **Remaining combat/system integration:** Common Magnum 40 vs 42 before headshots is explicitly unresolved; bed cooldown reset/decay rule unresolved; ordinary-death level/skill retention remains open; administrative ban policy needs operational details before multiplayer.

Resolved historical conflicts should not be re-asked as if new: Davy Jones removed; latest 500/30 currency; +50 Health/point; single-player ship cap 8; latest shipyard tiers; Ammo Bin storage-only; item and treasure rarity palettes intentionally differ. Stale earlier references to raft prologue, Ammo Bay crafting, unrestricted single-player ships, and +25 Health are historical.

## Suggested starting discussion

The rye-sale ownership and introduction sequence are now clarified below. Next confirm stamina and hunger scaling because they affect the next small gameplay repairs. Keep broader future systems tracked without making them immediate prerequisites for an enjoyable first voyage.

## Owner clarification after review

Authority: direct owner message in this conversation, October 5, 2026. This clarifies the newer Bible's zero-currency start and rare-rye sale without changing the original DOCX.

1. The survivor has zero currency until the rare rye is sold. The rye remains in the player's inventory through the Village handoff; discarding tutorial tools/supplies must not discard this mission cargo.
2. The player asks the female innkeeper whether they may stay the night for free.
3. She explains that work or goods must be traded to pay for the room and shows the player around the town square.
4. She introduces nearby local shopkeepers. They introduce themselves during this mission; their quests are available later in the game, not activated by these introductions.
5. On reaching the general merchant, the player receives the option to sell the rye in their inventory.
6. The sale's 250 Copper is added to the player's funds as soon as the introduction mission is complete. Do not credit it at the earlier prologue/Village arrival or silently credit it earlier during the tour.

Room price, any later room-payment transaction, refusal/revisit behavior for the sale, and exact mission-completion trigger beyond this sequence remain unspecified. Do not invent a room deduction, forced sale, or extra quest. The Journal remains a tutorial/reference system; a guided introduction mission does not automatically convert it into a quest log.

## October 6 owner clarification: stamina recovery

When asked whether recovery should be stationary-only or also occur while walking, the owner selected **also while walking**. This supersedes the stationary-only part of §30.15 for implementation. The original DOCX remains unchanged. Base five-second tuning, upgraded-capacity scaling and other survival mechanics retain their separate implementation/clarification gates.
