"""Play: crafting takes seconds, shows its progress, and uses the materials only when it finishes (owner, October 22). A survivor who dies mid-craft loses nothing.
Listen-server plus one client (EW_PLAY_PLAYERS=2). Writes Saved/CraftTimePlayResult.json."""
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
inv = owner.get_inventory_component()
stats = owner.get_survival_component()
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
shovel_recipe = unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipeWoodenShovel')
shovel = shovel_recipe.get_editor_property('output')
shovel_recipe.set_editor_property('craft_seconds', 3.0)
assert inv.unlock_recipe(shovel_recipe)
phase = 0
next_at = time.monotonic() + 2
checks = []
handle = None
state = {}


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWInventoryWidget, False)
                if w.get_owning_player() == client and w.is_in_viewport())


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(), 'CraftTimePlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 1.0
    try:
        if phase == 0:
            assert inv.add_item(wood, 40) == 40
            state['shovels'] = inv.get_item_count(shovel)
            client.set_inventory_open(True)
        elif phase == 1:
            menu().focus_crafting()      # the crafting list under the inventory
        elif phase == 2:
            m = menu()
            assert m.is_crafting_focused()
            shown = m.get_shown_recipe()
            assert shown is not None
            # Select the shovel with the d-pad/Up until it is the one shown.
            for _ in range(8):
                if menu().get_shown_recipe() == shovel_recipe:
                    break
                assert lib.send_verification_ui_key(client, 'Up')
        elif phase == 3:
            assert menu().get_shown_recipe() == shovel_recipe, 'could not select the shovel'
            assert menu().is_craft_action_enabled()
            assert lib.send_verification_ui_key(client, 'Enter')
            state['t0'] = time.monotonic()
        elif phase == 4:
            m = menu()
            assert m.is_craft_in_progress(), 'no progress shown after Enter'
            p = m.get_craft_progress()
            assert 0.0 <= p < 1.0
            assert inv.get_item_count(wood) == 40 and inv.get_item_count(shovel) == state['shovels'], 'materials used before the work finished'
            assert not m.is_craft_action_enabled(), 'a second craft could be started during the first'
            checks.append('Enter starts a craft that takes seconds: progress shows, nothing is used up yet, Craft is off while it runs')
        elif phase == 7:
            m = menu()
            assert not m.is_craft_in_progress()
            assert inv.get_item_count(shovel) == state['shovels'] + 1, 'no shovel after the time'
            assert inv.get_item_count(wood) == 20, f'wood {inv.get_item_count(wood)}'
            assert time.monotonic() - state['t0'] >= 2.5
            checks.append('After three seconds the shovel arrives and exactly 20 wood is used up')
            state['shovels'] = inv.get_item_count(shovel)
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 8:
            assert menu().is_craft_in_progress()
            stats.apply_damage(1000.0)
        elif phase == 12:
            assert stats.is_dead()
            assert inv.get_item_count(wood) == 20 and inv.get_item_count(shovel) == state['shovels'], 'a craft finished for a dead survivor'
            checks.append('Dying mid-craft: no item and no materials lost')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
