"""Play: the new menu layout (owner, October 25). One player (EW_PLAY_PLAYERS=1).
  - The menu always opens on the inventory page, whatever section it was closed on; five tabs; the character panel shows on the inventory page only.
  - Down past the last item row moves the cursor into the crafting list beneath the inventory, Up on its first row returns; the picked tile wears the ring.
  - The inventory and crafting search boxes filter their lists.
  - Skills fills the panel; RT starts picking a stat to spend a point on.
  - Company (front-end prototype): search, select, promote, demote, remove with confirmation, invite, rank-dependent actions, activity log.
  - Tames: the list of creatures, and the picked one's name, lineage and level.
Saves a screenshot of each page under Saved/Screenshots/Menus. Writes Saved/MenuLayoutPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
inv = pawn.get_inventory_component()
recipes = [unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_Recipe' + n) for n in ['WoodenShovel', 'WoodenAxe', 'WoodenPickaxe', 'HideWaterFlask']]
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
assert all(recipes) and wood
for recipe in recipes:
    assert inv.unlock_recipe(recipe)
assert inv.add_item(wood, 30) == 30
checks, state = [], {'step': 0, 'at': time.monotonic() + 2, 'handle': None, 'items': 0}
shots = saved / 'Screenshots' / 'Menus'
shots.mkdir(parents=True, exist_ok=True)


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWInventoryWidget, False) if w.get_owning_player() == pc and w.is_in_viewport())


def key(name):
    assert lib.send_verification_ui_key(pc, name), name


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / (name + ".png")}"')


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    pc.set_inventory_open(False)
    (saved / 'MenuLayoutPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))
    unreal.log(f'EWPLAYCHECK MenuLayout success={error is None} error={error}')


def s1():
    pc.set_inventory_open(True)


def s2():
    m = menu()
    assert m.get_selected_section() == 0 and unreal.EWInventoryWidget.get_section_count() == 5
    assert m.is_survivor_info_shown(), 'the character panel is not on the inventory page'
    state['items'] = m.get_shown_item_count()
    assert state['items'] >= 1 and m.get_shown_recipe_count() == 4, f'{state["items"]} items, {m.get_shown_recipe_count()} recipes'
    assert not m.is_crafting_focused()
    checks.append('The menu opens on the inventory page with five tabs, the items, the crafting list and the character panel')
    shot('1_inventory')


def s2b():
    menu().open_section(1)


def s3():
    m = menu()
    assert m.get_selected_section() == 1 and m.is_skills_shown() and not m.is_survivor_info_shown(), 'Skills should fill the panel and hide the character panel'
    checks.append('Skills shows alone, over the whole panel; the character panel is hidden')
    shot('2_skills')


def s3b():
    menu().open_section(2)


def s4():
    m = menu()
    assert not m.is_survivor_info_shown() and not m.is_skills_shown()
    company = m.get_company_panel()
    assert company.get_member_count() == 10 and company.get_shown_member_count() == 10
    checks.append('Company shows its own panel with ten sample members and no character panel')
    shot('3_company')


def s4b():
    menu().open_section(3)


def s5():
    m = menu()
    tames = m.get_tames_panel()
    assert tames.get_tame_count() == 5 and not m.is_survivor_info_shown()
    tames.select_tame(2)
    assert 'Biscuit' in str(tames.get_shown_name()) and 'LEVEL 3' in str(tames.get_shown_level()), f'{tames.get_shown_name()} {tames.get_shown_level()}'
    assert 'Sire' in str(tames.get_shown_lineage())
    key('Down')
    assert tames.get_selected_tame() == 3 and 'Gator Jack' in str(tames.get_shown_name())
    key('Gamepad_DPad_Up')
    assert tames.get_selected_tame() == 2
    checks.append('Tames lists the creatures; the arrows pick one and show its name, level and lineage')
    shot('4_tames')


def s6():
    pc.set_inventory_open(False)


def s7():
    pc.set_inventory_open(True)


def s8():
    m = menu()
    assert m.get_selected_section() == 0, f'the menu reopened on section {m.get_selected_section()}'
    checks.append('Closed on Tames, the menu reopens on the inventory page')
    key('Gamepad_RightTrigger')
    assert m.get_stat_focus() == 0, 'RT did not start picking a stat'
    key('Gamepad_RightTrigger')
    assert m.get_stat_focus() == -1
    checks.append('RT starts and stops picking a stat for the level-up arrows')


def s9():
    m = menu()
    assert m.get_selected_index() >= 0
    last = m.get_selected_index()
    for _ in range(12):                           # Down walks the item rows, then on into the crafting list
        if m.is_crafting_focused():
            break
        last = m.get_selected_index()
        key('Down')
    assert m.is_crafting_focused() and m.get_selected_recipe() == 0, 'Down off the last item row did not enter the crafting list'
    key('Right')
    assert m.get_selected_recipe() == 1
    key('Up')                                     # the second tile is on the first row of the list: Up returns to the inventory
    assert not m.is_crafting_focused() and m.get_selected_index() == last
    checks.append('Down past the last item row enters the crafting list; Up on its first row returns to the inventory')
    key('Down')
    assert m.is_crafting_focused()
    shot('5_crafting_cursor')


def s10():
    m = menu()
    m.set_recipe_search('shovel')
    assert m.get_shown_recipe_count() == 1, f'{m.get_shown_recipe_count()} recipes match "shovel"'
    m.set_recipe_search('')
    assert m.get_shown_recipe_count() == 4
    m.set_inventory_search('zzzz')
    assert m.get_shown_item_count() == 0
    m.set_inventory_search('wood')
    assert m.get_shown_item_count() >= 1
    m.set_inventory_search('')
    assert m.get_shown_item_count() == state['items']
    checks.append('The crafting and inventory search boxes filter their lists')
    m.open_section(2)


def s11():
    company = menu().get_company_panel()
    company.set_search('ren')
    assert company.get_shown_member_count() == 2, f'{company.get_shown_member_count()} members match "ren"'
    company.set_search('')
    company.select_member_by_name('Pip Marlowe')
    assert company.get_selected_rank() == 0 and company.get_viewer_rank() == 2
    assert company.is_action_enabled(0) and not company.is_action_enabled(1) and company.is_action_enabled(3) and not company.is_action_enabled(4)
    before = company.get_log_count()
    company.do_action(0)
    assert company.get_selected_rank() == 1 and company.get_log_count() == before + 1
    company.do_action(1)
    assert company.get_selected_rank() == 0 and company.get_log_count() == before + 2
    checks.append('Company: search filters the members; Promote and Demote change the picked member\'s rank and add to the activity log')
    company.do_action(3)
    assert company.is_confirm_open()
    company.confirm_dialog(False)
    assert company.get_member_count() == 10 and not company.is_confirm_open()
    company.do_action(3)
    company.confirm_dialog(True)
    assert company.get_member_count() == 9 and company.get_log_count() == before + 3
    checks.append('Company: Remove asks first; cancelling keeps the member, confirming removes them and logs it')
    pending = company.get_pending_invite_count()
    company.send_sample_invite('Test Sailor')
    assert company.get_pending_invite_count() == pending + 1 and company.get_log_count() == before + 4
    company.set_sub_tab(1)
    assert company.get_sub_tab() == 1
    company.set_sub_tab(1)
    checks.append('Company: an invitation can be made and shows in the pending list; the bottom panel switches between activity, invitations and ranks')


def s11b():
    shot('6_company_invites')


def s11c():
    menu().get_company_panel().set_sub_tab(2)


def s11d():
    shot('7_company_ranks')


def s12():
    company = menu().get_company_panel()
    company.set_sub_tab(0)
    company.select_member_by_name('Cato Fenwick')
    assert not company.is_action_enabled(4), 'an Officer should not be able to transfer leadership'
    company.cycle_viewer_rank()
    assert company.get_viewer_rank() == 3 and company.is_action_enabled(4), 'as Leader, transferring leadership should be possible'
    company.cycle_viewer_rank()
    assert company.get_viewer_rank() == 0 and not company.is_action_enabled(0) and not company.is_action_enabled(2), 'a Recruit can do nothing here'
    checks.append('Company: actions depend on the rank you view the screen as')
    finish()


STEPS = [(s1, 1.5), (s2, 1.2), (s2b, 1.2), (s3, 1.2), (s3b, 1.2), (s4, 1.2), (s4b, 1.2), (s5, 1.5), (s6, 1.0), (s7, 1.5), (s8, 0.5), (s9, 1.2), (s10, 0.8), (s11, 1.2), (s11b, 1.2), (s11c, 1.2), (s11d, 1.2), (s12, 0.5)]


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        action, wait = STEPS[state['step']]
        action()
        state['step'] += 1
        state['at'] = time.monotonic() + wait
    except Exception as error:
        finish(f'step {state["step"] + 1}: {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
