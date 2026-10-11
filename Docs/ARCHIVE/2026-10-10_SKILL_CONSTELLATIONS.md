# Skill constellation presentation

## Direct owner requirement

Opening **Skills** pans upward into a night sky. The player selects separate
constellations in that sky. Every constellation pattern contains **ten
unlockable skills**. This replaces the Skills tab's eventual generic panel
presentation; the existing inventory/crafting layout remains its own section.

The owner supplied two Honkai: Star Rail skill-tree screenshots as visual
references. Use the readable connected-node presentation as inspiration with
original Elitewake constellations, icons and backgrounds.

## Presentation approach to validate in the editor

The sky overview should show selectable constellations. Selecting one focuses
its ten connected skill stars, with a selected-skill description, rank or unlock
state, prerequisite information and the approved cost when authored. Distinguish
locked, available, unlocked and selected nodes with shapes/text as well as color.
Provide a way back to the overview and then the normal menu without changing
the survivor's position or enabling movement while the menu is open.

Implementation assumption: this is a menu sky presentation available regardless
of the world's daytime or camera obstruction. Opening Skills should not advance
world time or require waiting for night. The upward transition must preserve the
player's gameplay camera when closed. This assumption is not a new gameplay rule
and should be adjusted if the owner intends the physical world sky instead.

## Existing rules and open authoring

- Exactly 1 character stat point and 7 skill-tree points per level; cap 80.
- Respec availability at levels 10, 15, 20 onward, costing 2 Gold.
- Capability families and deeper specialization remain part of the design.
- Ten skills per constellation does not mean ten skill points per level or one
  point per skill. Do not assign costs, effects, prerequisite chains or ranks
  from the reference screenshots.
- The owner confirmed ten constellations: Survival, Building, Cooking, Farming,
  Smithing, Weapons, Seamanship, Medicine, Trade and Beast Mastery. Each contains
  ten unlockable skills, for 100 skills total. Individual effects, costs, ranks
  and connections still need authoring.

Current status: requirements recorded; Skills remains a menu placeholder. The
constellation presentation, progression backend and authoritative purchases are
not implemented. The connected coastal world/sloop milestone remains active;
this visual direction is an additional requirement, not a replacement for it.
