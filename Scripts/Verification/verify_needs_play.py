"""Play: hunger and thirst, starvation, food values, food sickness and its cure, and cooking (owner, October 22: design decisions 2, 8).
Listen server plus one client (EW_PLAY_PLAYERS=2). Item sickness chances are set to 0 or 1 in memory for the checks and put back. Writes Saved/NeedsPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(p) == pid(client.get_controlled_pawn()))
remote = client.get_controlled_pawn()
inv = owner.get_inventory_component()
stats = owner.get_survival_component()
remote_stats = remote.get_survival_component()
FOOD = '/Game/Elitewake/Items/Food/DA_'
raw_fish, raw_meat, cooked_fish, cooked_meat, herb = (unreal.load_asset(FOOD + n) for n in ('RawFish', 'RawMeat', 'CookedFish', 'CookedMeat', 'MedicinalHerb'))
fish_recipe = unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipeCookedFish')
meat_recipe = unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipeCookedMeat')
assert all((raw_fish, raw_meat, cooked_fish, cooked_meat, herb, fish_recipe, meat_recipe))
chances = {raw_fish: raw_fish.get_editor_property('sickness_chance'), raw_meat: raw_meat.get_editor_property('sickness_chance')}
checks = []
memo = {}
unreal.SystemLibrary.execute_console_command(None, 'ew.NeedsDepletion 1')
phase = 0
next_at = time.monotonic() + 3
handle = None


def notices(s):
    return {str(n.get_editor_property('id')) for n in s.get_debuff_notices()}


def clear():
    for e in list(inv.get_inventory_entries()):
        inv.remove_item(e.get_editor_property('item_definition'), e.get_editor_property('quantity'))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(None, 'ew.NeedsDepletion 0')
    for item, chance in chances.items():
        item.set_editor_property('sickness_chance', chance)
    Path(unreal.Paths.project_saved_dir(), 'NeedsPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'measured': memo, 'error': error}, indent=2))


def near(a, b, tol=.05):
    return abs(a - b) <= tol


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 1.0
    try:
        if phase == 0:
            clear()
            stats.cure_food_sickness()
            stats.set_hunger(100)
            stats.set_hydration(100)
            stats.update_needs(False, 60.0)
        elif phase == 1:
            hunger, thirst = stats.get_hunger(), stats.get_hydration()
            memo.update(hunger_after_60s=hunger, hydration_after_60s=thirst)
            assert near(100 - hunger, 100 / 2700 * 60, .15), f'hunger fell {100 - hunger:.3f} in a minute (45 minutes to empty is 2.222)'
            assert near(100 - thirst, 100 / 1500 * 60, .15), f'thirst fell {100 - thirst:.3f} in a minute (25 minutes to empty is 4.000)'
            assert near(remote_stats.get_hunger(), hunger, .5) and near(remote_stats.get_hydration(), thirst, .5), 'the client does not see the needs'
            checks.append('Hunger empties in 45 minutes and thirst in 25 of ordinary activity, on server and client')
            stats.set_hunger(100)
            stats.set_hydration(100)
            stats.update_needs(True, 60.0)
        elif phase == 2:
            assert near(100 - stats.get_hydration(), 100 / 1500 * 60 * 1.5, .2) and near(100 - stats.get_hunger(), 100 / 2700 * 60 * 1.5, .2), 'sprinting does not quicken the needs'
            checks.append('Sprinting quickens hunger and thirst by half again')
            stats.set_hunger(0)
            stats.set_hydration(60)
            memo['health_before_starving'] = stats.get_health()
            stats.update_needs(False, 20.0)
        elif phase == 3:
            lost = memo['health_before_starving'] - stats.get_health()
            memo['starving_loss_20s'] = lost
            assert near(lost, .25 * 20, 1.0), f'20 s at zero hunger cost {lost:.2f} health (expected 5)'
            assert stats.get_health() > 0, 'zero hunger killed at once'
            checks.append('At zero hunger health falls gradually, not at once')
            stats.set_hunger(100)
            stats.set_hydration(0)
            stats.restore_health(100)
            memo['health_before_thirst'] = stats.get_health()
            stats.update_needs(False, 20.0)
        elif phase == 4:
            lost = memo['health_before_thirst'] - stats.get_health()
            assert near(lost, .35 * 20, 1.0), f'20 s at zero thirst cost {lost:.2f} health (expected 7)'
            checks.append('At zero thirst health falls gradually')
            stats.restore_health(100)
            stats.set_hydration(100)
            # Food values: cooked fish +20 hunger +3 health; cooked meat +30 +5; raw meat +12 -3; raw fish +8.
            stats.set_hunger(10)
            stats.apply_damage(20)
            clear()
            inv.add_item(cooked_fish, 1)
            inv.add_item(cooked_meat, 1)
            memo['hp'] = stats.get_health()
            assert inv.consume_food(cooked_fish) == unreal.EWFoodUseResult.SUCCESS
        elif phase == 5:
            assert near(stats.get_hunger(), 30, .3) and near(stats.get_health(), memo['hp'] + 3, .3), (stats.get_hunger(), stats.get_health(), memo['hp'])
            assert inv.consume_food(cooked_meat) == unreal.EWFoodUseResult.SUCCESS
        elif phase == 6:
            assert near(stats.get_hunger(), 60, .3) and near(stats.get_health(), memo['hp'] + 8, .3), (stats.get_hunger(), stats.get_health())
            checks.append('Cooked fish gives +20 hunger +3 health and cooked meat +30 +5')
            raw_meat.set_editor_property('sickness_chance', 0.0)
            raw_fish.set_editor_property('sickness_chance', 0.0)
            stats.set_hunger(20)
            memo['hp2'] = stats.get_health()
            inv.add_item(raw_meat, 1)
            inv.add_item(raw_fish, 1)
            assert inv.consume_food(raw_meat) == unreal.EWFoodUseResult.SUCCESS
            assert inv.consume_food(raw_fish) == unreal.EWFoodUseResult.SUCCESS
        elif phase == 7:
            assert near(stats.get_hunger(), 40, .3) and near(stats.get_health(), memo['hp2'] - 3, .3), (stats.get_hunger(), stats.get_health(), memo['hp2'])
            assert not stats.is_food_sick(), 'with a zero chance the food made them sick'
            checks.append('Raw meat gives +12 hunger -3 health and raw fish +8; with no sickness chance neither makes them sick')
            assert near(chances[raw_fish], .15, .001) and near(chances[raw_meat], .25, .001), 'sickness chances are not 15% and 25%'
            raw_meat.set_editor_property('sickness_chance', 1.0)
            inv.add_item(raw_meat, 1)
            stats.set_hunger(20)
            assert inv.consume_food(raw_meat) == unreal.EWFoodUseResult.SUCCESS
        elif phase == 8:
            assert stats.is_food_sick(), 'raw meat that certainly sickens did not'
            assert 'FoodSickness' in notices(stats) and 'FoodSickness' in notices(remote_stats), 'the sickness notice does not show on both machines'
            left = stats.get_food_sickness_left()
            assert near(left, 180, 10), f'sickness lasts {left:.0f} s (expected 180)'
            checks.append('Food sickness lasts three minutes and shows as a notice')
            stats.set_hydration(100)
            stats.update_needs(False, 60.0)
            memo['sick_thirst_minute'] = 100 - stats.get_hydration()
            assert near(memo['sick_thirst_minute'], 100 / 1500 * 60 * 1.5, .2), f'sick thirst {memo["sick_thirst_minute"]:.2f} in a minute (expected 6.0)'
            checks.append('Food sickness quickens thirst by half')
        elif phase == 9:
            assert stats.get_food_sickness_left() < 125, 'the sickness did not count down'
            inv.add_item(herb, 1)
            assert inv.consume_food(herb) == unreal.EWFoodUseResult.SUCCESS
        elif phase == 10:
            assert not stats.is_food_sick() and 'FoodSickness' not in notices(stats), 'the medicinal herb did not cure the sickness'
            checks.append('A medicinal herb ends food sickness early')
            stats.contract_food_sickness(5.0)
            stats.update_needs(False, 6.0)
            assert not stats.is_food_sick(), 'sickness did not run out'
            assert stats.get_health() > 0, 'sickness killed'
            checks.append('Food sickness runs out by itself')
            clear()
            assert inv.unlock_recipe(fish_recipe) and inv.unlock_recipe(meat_recipe)
            memo['cook_seconds'] = [fish_recipe.get_editor_property('craft_seconds'), meat_recipe.get_editor_property('craft_seconds')]
            assert all(5 <= s <= 12 for s in memo['cook_seconds']), f'cooking takes {memo["cook_seconds"]} s, outside the owner\'s 5 to 12'
            checks.append('Cooking recipes take 5 to 12 seconds')
            assert fish_recipe.get_editor_property('output') == cooked_fish and meat_recipe.get_editor_property('output') == cooked_meat
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
