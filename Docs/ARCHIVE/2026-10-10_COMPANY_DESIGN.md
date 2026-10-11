# Company design direction

The owner supplies the [ATLAS Company page](https://atlas.fandom.com/wiki/Company)
as the reference for Elitewake's multiplayer organization system. Its accessible
search-index content describes membership management, leadership succession,
crew groups, alliances, activity history, governance and company mergers.
Direct page access was blocked; the linked
[Governance reference](https://atlas.fandom.com/wiki/Governance) was also available
through search-index content. This is a mechanics reference, not imported code,
artwork, text, branding or an assertion of current ATLAS behavior.

## Compatible feature direction

Build original Elitewake Company screens within the approved Company menu tab:

- Company overview, creation and invitations; member list and online filter.
- Authorized promotion, demotion, removal and voluntary departure.
- Owner transfer and company identity management.
- Crew groups for organizing members; distinct from NPC crew AI behavior.
- Alliances and configurable cooperation permissions.
- Activity history for membership and relevant ship, structure and tame events,
  with event locations where applicable.
- Governance for role permissions and asset access/ownership, once policy is
  approved. Sharing access must remain separate from transferring ownership.
- Company merger support later, after membership, assets, persistence and tame
  caps can be handled together without loss or duplication. Do not silently
  adopt the reference's asset-transfer exceptions or invitation requirements.

The first local implementation adds session-only Company creation, invitations,
accept/decline, roster/online status, owner renaming, manager promotion/demotion,
member removal/departure, leadership transfer and separate selectable ownership
policies in the Company tab. Alliances, crew groups, logs, mergers, persistence
and applying those policies to world assets remain design targets.

## Elitewake rules that still apply

The consolidated guide already requires company name, member usernames, levels,
ranks and activity log; authorized ranks promote/demote. Only the Company owner
may rename it. Ordinary members and game/server administrators cannot rename
Companies. Company officers are gameplay roles, not server-administrator powers.

Nameplates show friendly members green, allies light blue and enemies red;
the player's own nameplate is hidden. Alliance building and offline shipyard
access exist as design direction, with exact permissions pending. Broad alliance
membership must not automatically authorize every destructive action.

Keep the hard limits of 25 tames per player and 75 per Company. Wild creatures
must not attack player items unless tamed and directly controlled by a player.
Land structures remain temporary and player-raidable; NPC Ports retain their
PvP protection and one-Port-per-region constraint.

The reference does not authorize replacing these rules with territory conquest,
taxation, permanent land ownership or leaderboard rewards. Territory claiming
remains future work under the existing guide. The reference itself marks its
historical top-company bonuses as needing confirmation; no such bonuses are
adopted for Elitewake.

## Confirmed owner decisions

1. Leaders can configure personal, shared-access personal and collective
   ownership separately for ships, structures and tames. Asset transfer consent
   and production default policies remain to be specified. The session prototype
   starts policies at Personal and never converts an existing world asset.
2. Members' personal tames count toward the 75-Company cap as well as their
   individual 25-player cap. Future joining, taming and merger transactions must
   enforce those authoritative totals without silently destroying or reassigning
   tames. No production tame ownership exists yet; a tested native capacity guard
   is only a foundation until connected to actual animal/member totals.

The initial roles are Owner, Manager and Member as a prototype permission model.
Only Owner renames, changes policies, promotes/demotes and transfers leadership;
Manager can invite and remove ordinary members. Owner cannot leave an occupied
Company before transferring leadership. Removing/departing changes membership
only; asset retention and transfer are not implemented. Company records survive
pawn death in the same world but are reset by ending the session or map travel.
Offline members stay in the roster; account-based reconnect/owner recovery needs
the future persistence layer. A player-name list is used to select a target;
names need not be unique because actions use server-validated player identifiers.

Open I → Company to use this first screen. Create/rename uses the Company-name
field; select a player by name below the action buttons before inviting or
managing them. An invited player explicitly accepts or declines. Policy buttons
cycle Personal → Personal/shared access → Company owned. The first interface is
functional prototype presentation; role-based action disabling, confirmation for
destructive membership changes and full controller navigation remain to refine.
The server rejects unauthorized requests even when the prototype shows a button.

Member limits, rank names, permission matrix, invitation expiry, alliance limits,
log retention and merger handling remain unspecified. They need authoring before
dependent production behavior, but do not block the coastal/sloop world slice.

Implementation order when Company work begins: authoritative Company identity
and membership → owned requests and role checks → roster/menu → access policies
and logs → alliances → persistent asset transfer and mergers. Reuse existing
networked gameplay foundations; do not replace them with client-only menu state.
