"""Escape's OPTIONS menu: live/persistent look and brightness settings plus SAVE GAME and MAIN MENU.

Needs single-player Play (EW_PLAY_STANDALONE=1, one player) in /Game/Elitewake/Maps/Lvl_CoastalPlayground. Run
unattended with run_play_check.py. Through ordinary keys, the survivor:
  1. presses Escape: OPTIONS comes up with brightness and separate mouse/controller look controls, the world pauses;
  2. presses Escape again: back in the game, the world running;
  3. change each setting from keyboard/controller navigation and confirm values persist after reopening;
  4. hungry, thirsty, hurt, carrying stone, the Hatchet in hand and the Pickaxe on the hotbar, somewhere along the
     beach: Escape, select SAVE GAME, and verify it writes the survivor as they are;
  4. (the save put back on a survivor who has since changed restores them exactly, with no doubled tools);
  6. Down to MAIN MENU: the ELITEWAKE title screen;
  6. Single Player from the title: the survivor is back where and as they were saved, tools not doubled.
An existing save in Saved/SaveGames is kept aside and put back afterwards. Writes Saved/OptionsMenuPlayResult.json.
"""
import json
import shutil
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'OptionsMenuPlayResult.json')
SAVE_FILE = Path(unreal.Paths.project_saved_dir(), 'SaveGames', 'Survivor.sav')
BACKUP = SAVE_FILE.with_suffix('.sav.checkbackup')
T = '/Game/Elitewake/Items/Testing'
hatchet, pickaxe, skin, torch, stone = (unreal.load_asset(f'{T}/DA_Test{n}') for n in
    ('WoodenAxe', 'WoodenPickaxe', 'HideWaterFlask', 'InnTorch', 'Stone'))
TOOLS = (hatchet, pickaxe, skin, torch)
HAND = unreal.EWEquipmentSlot.MAIN_HAND
SPOT = unreal.Vector(420, -260, 120)
if SAVE_FILE.exists():
    shutil.copy2(SAVE_FILE, BACKUP)
    SAVE_FILE.unlink()
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def world():
    worlds = lib.get_play_worlds()
    return worlds[0] if worlds else None


def pc():
    w = world()
    return unreal.GameplayStatics.get_player_controller(w, 0) if w else None


def survivor():
    c = pc()
    p = c.get_controlled_pawn() if c else None
    return p if isinstance(p, unreal.EWCharacter) else None


def owned(who, item):
    """In the pack plus in hand."""
    return who.get_inventory_component().get_item_count(item) + (1 if who.get_equipment_component().get_equipped_item(HAND) == item else 0)


def paused():
    return unreal.GameplayStatics.is_game_paused(world())


def ready():
    c, p = pc(), survivor()
    if not (isinstance(c, unreal.EWPlayerController) and p) or not all(owned(p, t) == 1 for t in TOOLS):
        return False
    assert 'Lvl_CoastalPlayground' in world().get_path_name()
    return True


def escape():
    assert lib.send_verification_gameplay_key(pc(), 'Escape'), 'Escape was not taken'


def ui_key(name):
    return lambda: lib.send_verification_ui_key(pc(), name)


def menu_up():
    c = pc()
    menu = c.get_options_widget()
    if not (c.is_options_menu_open() and menu and menu.is_in_viewport()):
        return False
    assert paused(), 'the world did not pause in single player'
    assert c.get_editor_property('bShowMouseCursor'), 'no mouse cursor'
    assert menu.is_save_shown(), 'SAVE GAME is missing in single player'
    assert menu.get_selected() == 0
    if 'initial_user_settings' not in state['memo']:
        state['memo']['initial_user_settings'] = (
            c.get_user_brightness(), c.get_mouse_look_sensitivity(), c.get_controller_look_sensitivity())
    return True


def adjust_settings():
    menu = pc().get_options_widget()
    before = (pc().get_user_brightness(), pc().get_mouse_look_sensitivity(), pc().get_controller_look_sensitivity())
    assert lib.send_verification_ui_key(pc(), 'Right')
    after_brightness = pc().get_user_brightness()
    assert after_brightness > before[0], f'brightness did not apply live: {before[0]} -> {after_brightness}'
    assert lib.send_verification_ui_key(pc(), 'Down')
    assert lib.send_verification_ui_key(pc(), 'Right')
    after_mouse = pc().get_mouse_look_sensitivity()
    assert after_mouse > before[1], f'mouse sensitivity did not apply live: {before[1]} -> {after_mouse}'
    assert lib.send_verification_ui_key(pc(), 'Down')
    assert lib.send_verification_ui_key(pc(), 'Right')
    after_controller = pc().get_controller_look_sensitivity()
    assert after_controller > before[2], f'controller sensitivity did not apply live: {before[2]} -> {after_controller}'
    assert lib.send_verification_ui_key(pc(), 'Down')
    assert menu.get_selected() == 3, 'Down did not select SAVE GAME after settings'
    state['memo']['settings'] = (after_brightness, after_mouse, after_controller)
    checks.append('Brightness and separate look sensitivities adjust live; settings write to the user settings file')


def save_game():
    menu = pc().get_options_widget()
    assert menu.get_selected() == 3, 'SAVE GAME is not selected'
    assert lib.send_verification_ui_key(pc(), 'Enter')


def menu_gone():
    c = pc()
    if c.is_options_menu_open() or paused():
        return False
    assert not c.get_editor_property('bShowMouseCursor')
    return True


def prepare():
    p = survivor()
    needs = p.get_survival_component()
    needs.set_hunger(41.0)
    needs.set_hydration(57.0)
    needs.apply_damage(23.0)
    p.get_inventory_component().add_item(stone, 7)
    assert lib.send_verification_equipment_request(pc(), hatchet, HAND)
    assert lib.send_verification_hotbar_request(pc(), 2, pickaxe)
    assert p.teleport(SPOT, unreal.Rotator(0, 0, 35))
    pc().set_control_rotation(unreal.Rotator(0, -10, 35))
    state['memo']['t'] = time.monotonic()


def prepared():
    p = survivor()
    if p.get_equipment_component().get_equipped_item(HAND) != hatchet or p.get_hotbar_component().get_bound_item(2) != pickaxe:
        return False
    if time.monotonic() - state['memo']['t'] < 1.0:   # let it land on the sand
        return False
    state['memo']['where'] = p.get_actor_location()
    state['memo']['health'] = p.get_survival_component().get_health()
    escape()
    return True


def saved():
    menu = pc().get_options_widget()
    if not unreal.EWSurvivorSave.has_save():
        return False
    assert 'Game saved' in str(menu.get_status()), str(menu.get_status())
    assert abs(pc().get_user_brightness() - state['memo']['settings'][0]) < .001
    assert abs(pc().get_mouse_look_sensitivity() - state['memo']['settings'][1]) < .001
    assert abs(pc().get_controller_look_sensitivity() - state['memo']['settings'][2]) < .001
    assert pc().is_options_menu_open(), 'saving closed the menu'
    s = unreal.EWSurvivorSave.load_save()
    where = state['memo']['where']
    assert (s.get_editor_property('location') - where).length() < 1, s.get_editor_property('location')
    assert abs(s.get_editor_property('hunger') - 41) < .5 and abs(s.get_editor_property('hydration') - 57) < .5
    assert abs(s.get_editor_property('health') - state['memo']['health']) < .5
    assert 'Lvl_CoastalPlayground' in s.get_editor_property('map_path') and 'UEDPIE' not in s.get_editor_property('map_path')
    pack = {e.item_definition.get_name(): e.quantity for e in s.get_editor_property('inventory')}
    assert pack.get('DA_TestStone') == 7 and 'DA_TestWoodenAxe' not in pack, pack
    assert [e.item_definition for e in s.get_editor_property('equipment') if e.item_definition] == [hatchet]
    assert s.get_editor_property('hotbar')[2] == pickaxe
    state['memo']['save'] = s
    return True


def restore():
    """Change everything, then put the save back on the survivor (the same code Single Player resumes with)."""
    assert lib.send_verification_ui_key(pc(), 'Escape')
    p = survivor()
    p.get_survival_component().set_hunger(95.0)
    p.get_inventory_component().remove_item(stone, 7)
    assert lib.send_verification_equipment_request(pc(), torch, HAND)
    state['memo']['t'] = time.monotonic()


def restored():
    p = survivor()
    if p.get_equipment_component().get_equipped_item(HAND) != torch or time.monotonic() - state['memo']['t'] < .5:
        return False
    assert p.teleport(unreal.Vector(-300, 300, 200), unreal.Rotator())
    assert state['memo']['save'].apply_to(p), 'the save would not go back on'
    assert_as_saved(p)
    return True


def assert_as_saved(p):
    assert (p.get_actor_location() - state['memo']['where']).length() < 60, p.get_actor_location()
    needs = p.get_survival_component()
    assert abs(needs.get_hunger() - 41) < 1.5 and abs(needs.get_hydration() - 57) < 1.5, (needs.get_hunger(), needs.get_hydration())
    assert abs(needs.get_health() - state['memo']['health']) < .5, needs.get_health()
    assert p.get_inventory_component().get_item_count(stone) == 7
    assert p.get_equipment_component().get_equipped_item(HAND) == hatchet
    assert p.get_hotbar_component().get_bound_item(2) == pickaxe
    for tool in TOOLS:
        assert owned(p, tool) == 1, f'{tool.get_name()} x{owned(p, tool)}'


def to_main_menu():
    escape()
    state['memo']['t'] = time.monotonic()


def main_menu_chosen():
    if not pc().is_options_menu_open() or time.monotonic() - state['memo']['t'] < .3:
        return False
    for _ in range(4):
        assert lib.send_verification_ui_key(pc(), 'Down')
    assert pc().get_options_widget().get_selected() == 4, 'Down navigation did not move to MAIN MENU'
    assert lib.send_verification_ui_key(pc(), 'Enter')
    return True


def at_title():
    c = pc()
    if not (isinstance(c, unreal.EWTitlePlayerController) and c.get_title_widget()):
        return False
    assert 'Lvl_Title' in world().get_path_name(), world().get_path_name()
    assert not paused(), 'the title opened paused'
    return True


def single_player():
    title = pc().get_title_widget()
    title.start_journey()
    title.start_single_player()
    state['memo']['t'] = time.monotonic()


def resumed():
    c, p = pc(), survivor()
    if isinstance(c, unreal.EWTitlePlayerController) or not p or 'Lvl_CoastalPlayground' not in world().get_path_name():
        return False
    if time.monotonic() - state['memo']['t'] < 2.0 or p.get_inventory_component().get_item_count(stone) != 7:
        return False
    assert not unreal.GameplayStatics.get_game_instance(world()).will_resume_saved_survivor()
    assert_as_saved(p)
    return True


STEPS = [
    ('Single Player on the island with the four tools', lambda: None, ready, 30),
    ('Escape brings up OPTIONS with controls and save/menu; the world pauses and the mouse shows', escape, menu_up, 4),
    ('Escape again returns to the game and the world runs', ui_key('Escape'), menu_gone, 4),
    ('Hurt, hungry and thirsty with stone, the Hatchet in hand and the Pickaxe on the hotbar, Escape', prepare, prepared, 6),
    ('', lambda: None, menu_up, 4),
    ('Change brightness/mouse/controller settings and move to SAVE GAME', adjust_settings, lambda: pc().get_options_widget().get_selected() == 3, 4),
    ('Enter on SAVE GAME saves the survivor as they are; the menu stays up', save_game, saved, 4),
    ('The save, put back on a survivor who has since changed, restores them exactly, tools not doubled', restore, restored, 4),
    ('Escape, Down, Enter on MAIN MENU', to_main_menu, main_menu_chosen, 4),
    ('MAIN MENU opens the ELITEWAKE title screen', lambda: None, at_title, 30),
    ('Single Player from the title resumes the saved survivor where and as they were, tools not doubled', single_player, resumed, 40),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    try:
        initial = state['memo'].get('initial_user_settings')
        if initial and world() and pc():
            pc().set_user_brightness(initial[0])
            pc().set_mouse_look_sensitivity(initial[1])
            pc().set_controller_look_sensitivity(initial[2])
    except Exception as e:  # noqa: BLE001
        error = error or f'could not restore the original user settings: {e!r}'
    try:
        if SAVE_FILE.exists():
            SAVE_FILE.unlink()
        if BACKUP.exists():
            shutil.move(BACKUP, SAVE_FILE)
    except Exception as e:  # noqa: BLE001
        error = error or f'could not put the earlier save back: {e!r}'
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK OptionsMenu success={error is None} error={error}')


def tick(delta):
    try:
        label, act, until, seconds = STEPS[state['index']]
        if not state['begun']:
            act()
            state.update(begun=True, deadline=time.monotonic() + seconds)
        if until():
            if label:
                checks.append(label)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
            return
        if time.monotonic() > state['deadline']:
            raise TimeoutError('timed out')
    except Exception as error:  # noqa: BLE001
        finish(f'step {state["index"] + 1} ({STEPS[state["index"]][0] or "continued"}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
