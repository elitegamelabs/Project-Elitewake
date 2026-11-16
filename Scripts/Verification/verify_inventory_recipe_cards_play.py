"""Recipe-card acceptance through real Slate mouse, keyboard and controller events.

Fresh standalone or listen-server/client PIE; EW_PLAY_STARTER_KIT=0.
Only the transient Play session is changed. Never saves an asset or survivor.
Result: InventoryRecipeCardsPlayResult.json, or InventoryRecipeCardsNetworkResult.json.
"""
import json
import time
import traceback
from pathlib import Path
import unreal as u

lib = u.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
pcs = [u.GameplayStatics.get_player_controller(w, 0) for w in worlds]
pc = next((c for c in pcs if not c.has_authority()), pcs[0])
world = worlds[pcs.index(pc)]
server = next(w for w, c in zip(worlds, pcs) if c.has_authority())


def pid(p):
    return json.loads(u.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in u.GameplayStatics.get_all_actors_of_class(server, u.EWCharacter)
             if pid(p) == pid(pc.get_controlled_pawn()))
pack = owner.get_inventory_component()
remote = pc.get_controlled_pawn().get_inventory_component()
recipes = [u.load_asset('/Game/Elitewake/Crafting/Testing/DA_Recipe' + name)
           for name in ('WoodenShovel', 'WoodenAxe', 'HideWaterFlask')]
wood = u.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
output = recipes[0].get_editor_property('output')
old_times = [r.get_editor_property('craft_seconds') for r in recipes]
old_fire = recipes[0].get_editor_property('needs_fire')
for r in recipes:
    r.set_editor_property('craft_seconds', 2.0)
    pack.unlock_recipe(r)
for e in list(pack.get_inventory_entries()):
    pack.remove_item(e.get_editor_property('item_definition'), e.get_editor_property('quantity'))
pack.add_item(wood, 80)
folder = Path(u.Paths.project_saved_dir(), 'Screenshots', 'InventorySlice2')
folder.mkdir(parents=True, exist_ok=True)
report = dict(success=False, network=len(worlds) > 1, checks=[], error=None)
state = dict(at=time.monotonic() + 2, step=0)
result = Path(u.Paths.project_saved_dir(), 'InventoryRecipeCardsNetworkResult.json'
              if len(worlds) > 1 else 'InventoryRecipeCardsPlayResult.json')


def menu():
    return next(w for w in u.WidgetLibrary.get_all_widgets_of_class(world, u.EWInventoryWidget, False)
                if w.get_owning_player() == pc and w.is_in_viewport())


def check(label, condition):
    report['checks'].append(dict(check=label, passed=bool(condition)))
    assert condition, label


def key(name):
    assert lib.send_verification_ui_key(pc, name)


def click(index=0, double=False):
    assert lib.click_verification_widget(menu(), 'CraftRecipeTile_' + str(index), double)


def shot(name):
    if len(worlds) == 1:
        assert lib.capture_verification_play_viewport(world, str(folder / (name + ".png")))


def finish(error=None):
    for r, seconds in zip(recipes, old_times):
        r.set_editor_property('craft_seconds', seconds)
    recipes[0].set_editor_property('needs_fire', old_fire)
    lib.send_verification_ui_recipe_scroll(pc, 0)
    pc.set_inventory_open(False)
    report['error'] = error
    report['success'] = error is None and all(c['passed'] for c in report['checks'])
    result.write_text(json.dumps(report, indent=2))
    u.unregister_slate_post_tick_callback(handle)


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        n = state['step']
        delay = .5
        if n == 0:
            lib.resize_verification_play_viewport(world, 1920, 1080)
            pc.set_inventory_open(True)
            menu().focus_crafting()
            check('Three actual unlocked recipes', menu().get_shown_recipe_count() == 3)
            state['tile'] = menu().get_recipe_tile(0)
            state['neighbor'] = menu().get_recipe_tile(1)
            delay = 1
        elif n == 1:
            shot('1080p-item-faces')
            click()
        elif n == 2:
            check('Single mouse click inspects without crafting', menu().is_recipe_inspected()
                  and pack.get_item_count(output) == 0 and not menu().is_craft_in_progress())
            check('Card has actual material and owned quantities', 'Have 80' in str(menu().get_recipe_card_requirements()) and 'Need 20' in str(menu().get_recipe_card_requirements()))
            check('Flip preserves tile and neighboring tile identity', menu().get_recipe_tile(0) == state['tile']
                  and menu().get_recipe_tile(1) == state['neighbor'])
            shot('1080p-recipe-card')
            click()
        elif n == 3:
            check('Click selected tile restores item face', not menu().is_recipe_inspected())
            click()
        elif n == 4:
            click(1)
        elif n == 5:
            check('Another recipe restores previous and opens selected', menu().is_recipe_inspected()
                  and menu().get_shown_recipe() == recipes[1] and menu().get_recipe_tile(0) == state['tile'])
            click(2)
        elif n == 6:
            assert lib.scroll_verification_widget(menu(), 'CraftRecipeTile_2', -4)
            delay = 1
        elif n == 7:
            check('Mouse wheel scrolls inside inspected tile', menu().get_recipe_card_scroll_offset() > 0)
            state['wheel_offset'] = menu().get_recipe_card_scroll_offset()
            assert lib.send_verification_ui_recipe_scroll(pc, 1)
            delay = .7
        elif n == 8:
            assert lib.send_verification_ui_recipe_scroll(pc, 0)
            check('Controller right stick scrolls without navigating or crafting',
                  menu().get_recipe_card_scroll_offset() < state['wheel_offset']
                  and menu().get_shown_recipe() == recipes[2] and pack.get_item_count(output) == 0)
            click()
            key('R')
        elif n == 9:
            check('Keyboard inspect toggles off', not menu().is_recipe_inspected())
            key('Gamepad_FaceButton_Left')
        elif n == 10:
            check('Controller X inspects without crafting', menu().is_recipe_inspected() and pack.get_item_count(output) == 0)
            click(double=True)
            delay = .65
        elif n == 11:
            check('True Slate double-click starts one timed craft', menu().is_craft_in_progress()
                  and pack.get_item_count(output) == 0 and pack.get_item_count(wood) == 80)
            check('Craft start retains tile identity', menu().get_recipe_tile(0) == state['tile'])
            key('Enter')
            delay = 3
        elif n == 12:
            check('Double-click yields exactly one output and one ingredient charge', pack.get_item_count(output) == 1
                  and remote.get_item_count(output) == 1 and pack.get_item_count(wood) == 60)
            check('Card quantities refresh after authoritative inventory change', 'Have 60' in str(menu().get_recipe_card_requirements()) and 'Need 20' in str(menu().get_recipe_card_requirements()))
            key('Enter')
            delay = 3
        elif n == 13:
            check('Keyboard Enter crafts through existing system', pack.get_item_count(output) == 2 and pack.get_item_count(wood) == 40)
            key('Gamepad_FaceButton_Bottom')
            delay = 3
        elif n == 14:
            check('Controller A crafts through existing system', pack.get_item_count(output) == 3 and pack.get_item_count(wood) == 20)
            pack.remove_item(wood, 20)
            delay = 1
        elif n == 15:
            check('Missing resources disable crafting and explain why', not menu().is_craft_action_enabled()
                  and 'Not enough materials' in str(menu().get_recipe_card_requirements()))
            click(double=True)
            delay = 3
        elif n == 16:
            check('Ineligible double-click grants nothing', pack.get_item_count(output) == 3)
            pack.add_item(wood, 20)
            recipes[0].set_editor_property('needs_fire', True)
            delay = 1
        elif n == 17:
            check('Station readiness updates without inventory event', not menu().is_craft_action_enabled()
                  and 'campfire' in str(menu().get_recipe_card_requirements()))
            recipes[0].set_editor_property('needs_fire', False)
            menu().set_recipe_search(str(recipes[1].get_editor_property('output').get_editor_property('display_name')))
        elif n == 18:
            check('Search still filters actual recipes', menu().get_shown_recipe_count() == 1 and menu().get_shown_recipe() == recipes[1])
            menu().set_recipe_search('')
            menu().focus_crafting()
            lib.resize_verification_play_viewport(world, 1280, 720)
            delay = 1.5
        elif n == 19:
            click()
        elif n == 20:
            check('720p recipe card remains interactive', menu().is_recipe_inspected())
            shot('720p-recipe-card')
            delay = 1
        elif n == 21:
            key('Enter')
            delay = .6
        elif n == 22:
            check('Final revalidation fixture starts a valid timed craft', menu().is_craft_in_progress())
            pack.remove_item(wood, 20)
            delay = 3
        elif n == 23:
            check('Materials lost during craft prevent output at completion', pack.get_item_count(output) == 3
                  and remote.get_item_count(output) == 3 and pack.get_item_count(wood) == 0)
            finish()
            return
        state['step'] += 1
        state['at'] = time.monotonic() + delay
    except Exception:
        finish(traceback.format_exc())


handle = u.register_slate_post_tick_callback(tick)



