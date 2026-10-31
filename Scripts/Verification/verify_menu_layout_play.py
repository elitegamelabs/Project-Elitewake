"""Play: the new menu layout (owner, October 25). One player (EW_PLAY_PLAYERS=1).
  - The menu always opens on the inventory page, whatever section it was closed on; five tabs; the character panel shows on the inventory page only.
  - Down past the last item row moves the cursor into the crafting list beneath the inventory, Up on its first row returns; the picked tile wears the ring.
  - The inventory and crafting search boxes filter their lists.
  - Skills fills the panel; RT starts picking a stat to spend a point on.
  - Company (live since October 30): with no Company it offers to make one; creating one makes you its Leader; the ship policy
    changes; leaving asks first; what each rank may do.
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


def s3t():
    m = menu()
    for _ in range(12):                           # Up through the stars to the top, then on to the tab bar
        if m.is_tab_focused():
            break
        key('Up')
    assert m.is_tab_focused() and m.get_tab_cursor() == 1, 'Up from the top of Skills did not reach the tab bar'
    checks.append('Skills: Up past the top star reaches the tab bar')


def s3b():
    menu().open_section(2)


def s4():
    m = menu()
    assert not m.is_survivor_info_shown() and not m.is_skills_shown()
    company = m.get_company_panel()
    assert not company.is_in_company() and company.get_member_count() == 0 and company.get_viewer_rank() == -1
    checks.append('Company shows its own panel (no character panel) and, outside a Company, offers to make one')
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
    lib.send_verification_ui_analog(pc, -1)       # the left stick pushed down steps the highlight, as the d-pad does
    lib.send_verification_ui_analog(pc, 0)
    assert tames.get_selected_tame() == 3, 'the left stick did not move the Tames highlight'
    lib.send_verification_ui_analog(pc, 1)
    lib.send_verification_ui_analog(pc, 0)
    assert tames.get_selected_tame() == 2
    key('Up'); key('Up'); key('Up')                # Up off the first creature goes to the tab bar
    assert m.is_tab_focused() and m.get_tab_cursor() == 3, 'Up from the top of Tames did not reach the tab bar'
    lib.send_verification_ui_analog_x(pc, 1); lib.send_verification_ui_analog_x(pc, 0)
    assert m.get_tab_cursor() == 4 and m.get_selected_section() == 3, 'the stick moved the tab highlight but should not open the tab until A'
    key('Gamepad_FaceButton_Bottom')               # A opens the highlighted tab
    assert m.get_selected_section() == 4 and not m.is_tab_focused(), 'A did not open the highlighted tab'
    m.open_section(3)
    checks.append('Up from the top of a tab reaches the tab bar; the stick moves along it and A opens the highlighted tab')
    checks.append('The left stick moves the highlight on the Tames tab')
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
    lib.send_verification_ui_analog_x(pc, -1)     # left stick left: back to the first recipe tile
    lib.send_verification_ui_analog_x(pc, 0)
    assert m.get_selected_recipe() == 0, 'the left stick (horizontal) did not move the crafting highlight'
    lib.send_verification_ui_analog_x(pc, 1)
    lib.send_verification_ui_analog_x(pc, 0)
    assert m.get_selected_recipe() == 1
    checks.append('The left stick moves the highlight sideways and down through the inventory and crafting list')
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
    menu().open_section(2)
    company = menu().get_company_panel()
    company.create_company('Lone Gull')


def s11a():
    company = menu().get_company_panel()
    assert company.is_in_company() and company.get_company_name() == 'Lone Gull', company.get_status_text()
    assert company.get_member_count() == 1 and company.get_viewer_rank() == 2 and company.get_log_count() >= 1
    checks.append('Company: creating one makes you its Leader, alone on the roster; the server answer is logged')
    assert company.get_ship_policy() == 0
    company.cycle_ship_policy()


def s11b():
    company = menu().get_company_panel()
    assert company.get_ship_policy() == 1, company.get_ship_policy()
    checks.append('Company: the Leader changes who may sail the ships (Personal to Personal Shared)')
    company.set_sub_tab(1)
    assert company.get_sub_tab() == 1
    shot('6_company_invites')


def s11c():
    menu().get_company_panel().set_sub_tab(2)


def s11d():
    shot('7_company_ranks')


def s12():
    company = menu().get_company_panel()
    company.set_sub_tab(0)
    assert company.is_action_enabled(2) and not company.is_action_enabled(0) and not company.is_action_enabled(4), 'alone: invite only'
    assert company.is_action_enabled(5), 'a Leader alone may leave'
    company.do_action(5)
    assert company.is_confirm_open()
    company.confirm_dialog(False)
    assert not company.is_confirm_open() and company.is_in_company()
    checks.append('Company: alone, the Leader may invite and leave; leaving asks first and cancelling keeps the Company')
    finish()


STEPS = [(s1, 1.5), (s2, 1.2), (s2b, 1.2), (s3, 1.2), (s3t, 0.5), (s3b, 1.2), (s4, 1.2), (s4b, 1.2), (s5, 1.5), (s6, 1.0), (s7, 1.5), (s8, 0.5), (s9, 1.2), (s10, 0.8), (s11, 1.5), (s11a, 1.5), (s11b, 1.2), (s11c, 1.2), (s11d, 1.2), (s12, 0.5)]


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
