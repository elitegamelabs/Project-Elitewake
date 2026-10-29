# GR1: code review of the October 22 gameplay systems (October 28, 2026)

Reviewer: Claude (findings come from reading; none was reproduced in Play). Afterwards findings 1 and 4 were fixed in `SaveSurvivor` (it now refuses while dead, attached to a ship or mount, or on a ladder); the options menu shows its existing "could not be saved" message. That fix is built but has no Play check of its own yet.
Files read: `EWSurvivalComponent.cpp`, `EWProgressionComponent.cpp`, `EWDeathBag.cpp`, `EWSurvivorSave.cpp`,
`AEWCharacter::FindRespawnPoint` / `RespawnAfterDeath`, the server RPCs in `EWPlayerController.cpp` (respawn, stat points, craft,
food, hotbar, container transfer, region teleport), and `EWInteractionComponent.cpp`.
Not reviewed: exploration/map widget code beyond the save path, the skill-tree data, UI widgets.

What held up: every server RPC reviewed re-checks that the caller owns the pawn and is alive where it matters (craft, food, stat
points, respawn, debug teleport, container transfer), the debug teleport is compiled out of shipping builds, survival values are
authority-only and finite-checked, and the owner-only replicated counters (damage, exhaustion, debuff notices) are `COND_OwnerOnly`.

## Medium

1. **Saving on a ship, ladder or mount stores a moving place.** `SaveSurvivor` records `GetActorLocation()`. At a helm, on a
   ladder, at a cannon or (new) on a spider, that is the vehicle's world position, and ships are not part of the save. Resuming puts
   the survivor where the ship was, which can be open water. Fix: refuse to save (with a message) while attached to anything, or
   save the last grounded location.
2. **Equipped items can vanish on resume when the pack is full.** `ApplyTo` puts equipped items back through `AddToEntries` with
   `Pack->MaxSlots` and ignores the leftover; an item that does not fit is lost before `EquipItem` runs. Fix: check the result and
   keep the item equipped directly, or report it.
3. **Death bags open to any living survivor within reach.** `CanAccess` checks only "alive and near". In multiplayer another player
   can loot a dead player's bag at once. If that is the intent (a corpse run), keep it; if not, add an owner and a short
   owner-only window. The bag also expires after `LifeSeconds` and its contents are lost; worn equipment is not dropped at all.
   These are design questions for the owner, not defects.

## Low

4. `SaveSurvivor` does not refuse when the survivor is dead: a save made at 0 health kills the survivor on resume.
5. The save omits body temperature, stamina and food sickness (a resumed survivor is neutral on these). Probably acceptable; worth
   a line in the design notes.
6. `FindRespawnPoint` traces from above on the visibility channel, so it can choose the top of a cave rock or a player-built roof,
   and it gives no spawn protection or distance from hostile animals.
7. `UEWProgressionComponent::Restore` trusts the save: unspent plus spent points are not checked against the level. Local saves
   only, so low.
8. `ServerBindHotbar` and `ServerActivateHotbar` do not check for death (activation ends in guarded paths, binding is harmless).
9. `UpdateNeeds` calls `NotifyStatsChanged()` on every call even when nothing changed, so each player's widgets refresh every
   server tick; a cheap "changed" test would remove that.
10. `UpdateClimate` computes `bRegionChanged` and discards it (dead code).

## Suggested order

Fix 1, 2 and 4 together (all in `UEWSurvivorSave`, small), then ask the owner about 3.
