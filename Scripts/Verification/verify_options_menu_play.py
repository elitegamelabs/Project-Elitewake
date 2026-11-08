"""Escape's pause menu (owner, October 30): RESUME GAME, SAVE GAME, OPTIONS and MAIN MENU as buttons; OPTIONS opens the settings
(brightness for the whole picture, mouse and controller look speed each horizontal and vertical, master volume with a dial) and BACK.

Needs single-player Play (EW_PLAY_STANDALONE=1, one player) in /Game/Elitewake/Maps/Lvl_CoastalPlayground. Run
unattended with run_play_check.py. Through ordinary keys, the survivor:
  1. presses Escape: the pause menu comes up on RESUME GAME, the world pauses;
  2. Enter on RESUME GAME: back in the game, the world running;
  3. OPTIONS (Down, Down, Enter): each setting changes live by keys, brightness moves the display gamma, the dial follows the
     volume, mouse horizontal and vertical speeds turn the view by their own amounts; BACK returns to the buttons;
  4. hungry, thirsty, hurt, carrying stone, the Hatchet in hand and the Pickaxe on the hotbar, somewhere along the
     beach: Escape, select SAVE GAME, and verify it writes the survivor as they are;
  4. (the save put back on a survivor who has since changed restores them exactly, with no doubled tools);
  6. Down to MAIN MENU: the ELITEWAKE title screen;
  6. Single Player from the title, then Resume Game on the Freeport choice: the survivor is back where and as they were saved, tools not doubled.
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
    assert menu.get_tab() == 0 and menu.get_selected() == 10, 'the menu does not open on its buttons at RESUME GAME'
    if 'initial_user_settings' not in state['memo']:
        state['memo']['initial_user_settings'] = (c.get_user_brightness(), [c.get_look_sensitivity(i) for i in range(4)])
    return True


def look_start():
    """The view turns with the game running: mouse horizontal 2.0 and vertical 0.5, one look of (2, 2)."""
    c = pc()
    state['memo']['looks_kept'] = (c.get_look_sensitivity(0), c.get_look_sensitivity(1))
    c.set_look_sensitivity(0, 2.0)
    c.set_look_sensitivity(1, 0.5)
    c.set_control_rotation(unreal.Rotator(0, 0, 90))
    state['memo']['look_from'] = c.get_control_rotation()
    survivor().do_look(2.0, 2.0)
    state['memo']['t'] = time.monotonic()


def look_done():
    if time.monotonic() - state['memo']['t'] < .3:
        return False
    c = pc()
    before, after = state['memo']['look_from'], c.get_control_rotation()
    yaw = abs(unreal.MathLibrary.normalize_axis(after.yaw - before.yaw))
    pitch = abs(unreal.MathLibrary.normalize_axis(after.pitch - before.pitch))
    kept = state['memo']['looks_kept']
    c.set_look_sensitivity(0, kept[0])
    c.set_look_sensitivity(1, kept[1])
    assert yaw > 0.5 and yaw > 3.5 * pitch, f'mouse horizontal 2.0 and vertical 0.5 turned {yaw} and {pitch} degrees'
    return True


def adjust_settings():
    c = pc()
    menu = c.get_options_widget()
    key = lambda name: lib.send_verification_ui_key(c, name)
    before = (c.get_user_brightness(), [c.get_look_sensitivity(i) for i in range(4)])
    assert key('Down') and key('Down') and menu.get_selected() == 12, f'Down, Down did not reach OPTIONS ({menu.get_selected()})'
    assert key('Enter') and menu.get_tab() == 1 and menu.get_selected() == 0, 'Enter on OPTIONS did not open the settings at Brightness'
    gamma = c.get_display_gamma()
    assert key('Right')
    after_brightness = c.get_user_brightness()
    assert after_brightness > before[0], f'brightness did not apply live: {before[0]} -> {after_brightness}'
    assert c.get_display_gamma() > gamma, f'the display gamma did not rise: {gamma} -> {c.get_display_gamma()}'
    looks = []
    for which in range(4):
        assert key('Down') and menu.get_selected() == 1 + which, f'Down did not reach look setting {which}'
        assert key('Right')
        assert c.get_look_sensitivity(which) > before[1][which], f'look setting {which} did not apply live'
        looks.append(c.get_look_sensitivity(which))
    assert key('Down') and menu.get_selected() == 5, 'Down did not reach master volume'
    c.set_master_volume(1.0)      # the setting is saved between runs
    for _ in range(5):
        assert key('Left')
    volume = c.get_master_volume()
    assert volume < .95, f'master volume did not apply live: 1.0 -> {volume}'
    assert abs(menu.get_dial_value() - volume) < .001, f'the dial ({menu.get_dial_value()}) does not show the volume ({volume})'
    # The volume reaches the audio devices themselves, so it scales every sound (not only a saved number).
    applied = unreal.EWGameInstance.get_applied_master_volume()
    assert abs(applied - volume) < .001, f'the audio devices were given {applied}, not the volume {volume}'
    state['memo']['volume_applied'] = round(applied, 3)
    c.set_master_volume(1.0)      # leave the saved setting as found
    # Sound effects and ambience volumes (owner, November 7), each under the master volume; left at full.
    gi = unreal.EWGameInstance
    for row, getter, setter, label in ((6, gi.get_sound_effects_volume, gi.set_sound_effects_volume, 'sound effects'),
                                       (7, gi.get_ambience_volume, gi.set_ambience_volume, 'ambience')):
        assert key('Down') and menu.get_selected() == row, f'Down did not reach the {label} volume'
        setter(1.0)
        for _ in range(5):
            assert key('Left')
        assert getter() < .95, f'the {label} volume did not apply live: 1.0 -> {getter()}'
        state['memo'][f'{label}_volume_after_keys'] = round(getter(), 3)
        setter(1.0)
    # Graphics (owner, November 1): the overall quality, then five groups, a whole level per Left / Right.
    gus = unreal.GameUserSettings.get_game_user_settings()
    found = gus.get_overall_scalability_level()
    assert key('Down') and menu.get_selected() == 8, 'Down did not reach graphics quality'
    for _ in range(3):
        assert key('Left')
    assert gus.get_overall_scalability_level() == 0, f'three Lefts did not set Low ({gus.get_overall_scalability_level()})'
    for _ in range(3):
        assert key('Right')
    assert gus.get_overall_scalability_level() == 3, f'three Rights did not set Epic ({gus.get_overall_scalability_level()})'
    assert menu.get_selected() == 8, f'changing the quality moved the selection to {menu.get_selected()}'
    assert key('Down') and menu.get_selected() == 9, 'Down did not reach textures'
    assert key('Left') and gus.get_texture_quality() == 2, f'Left on textures did not set High ({gus.get_texture_quality()})'
    assert gus.get_overall_scalability_level() == -1, 'a mixed setting is not shown as custom'
    assert key('Right') and gus.get_texture_quality() == 3 and gus.get_overall_scalability_level() == 3, 'Right did not restore Epic textures'
    for row in range(10, 14):
        assert key('Down') and menu.get_selected() == row, f'Down did not reach graphics row {row}'
    if found in (0, 1, 2, 3):
        gus.set_overall_scalability_level(found)    # leave the saved setting as found
        gus.apply_non_resolution_settings()
        gus.save_settings()
    state['memo']['graphics'] = 'Low, Epic, custom textures, back to Epic'
    # Button icons (owner, November 1): Automatic, Xbox, PlayStation; left as found.
    assert key('Down') and menu.get_selected() == 14, 'Down did not reach button icons'
    icons_found = pc().get_button_icons_choice()
    for _ in range(3):
        assert key('Left')
    assert pc().get_button_icons_choice() == unreal.EWButtonIconsChoice.AUTOMATIC, 'Left did not reach Automatic button icons'
    assert key('Right') and pc().get_button_icons_choice() == unreal.EWButtonIconsChoice.XBOX, 'Right did not choose Xbox icons'
    assert key('Right') and pc().get_button_icons_choice() == unreal.EWButtonIconsChoice.PLAY_STATION, 'Right did not choose PlayStation icons'
    pc().set_button_icons_choice(icons_found, True)
    # Interface size (Part 8, 62; November 8): 80% to 150% in 5% steps, applied to every screen at once; left as found.
    assert key('Down') and menu.get_selected() == 15, 'Down did not reach interface size'
    size_found = unreal.EWGameInstance.get_interface_scale()
    for _ in range(20):
        key('Left')
    assert abs(unreal.EWGameInstance.get_applied_interface_scale() - .8) < .001, f'Left did not reach 80% ({unreal.EWGameInstance.get_applied_interface_scale()})'
    assert key('Right') and abs(unreal.EWGameInstance.get_applied_interface_scale() - .85) < .001, 'Right did not grow the interface 5%'
    for _ in range(20):
        key('Right')
    assert abs(unreal.EWGameInstance.get_applied_interface_scale() - 1.5) < .001, f'Right did not reach 150% ({unreal.EWGameInstance.get_applied_interface_scale()})'
    state['memo']['interface'] = '80% to 150%'
    unreal.EWGameInstance.set_interface_scale(size_found)
    # Controls (owner, November 7): every control, for the keyboard or the controller in use.
    assert key('Down') and menu.get_selected() == 16, 'Down did not reach CONTROLS'
    assert key('Enter') and menu.get_tab() == 2, 'Enter on CONTROLS did not open the Controls page'
    count = menu.get_controls_count()
    assert count >= 30, f'the Controls page lists only {count} controls'
    assert not menu.are_controls_shown_for_controller() and menu.get_control_text(0).startswith('W A S D'),         f'the Controls page does not show the keyboard first: {menu.get_control_text(0)}'
    assert key('Gamepad_DPad_Down')            # a controller button: the page switches to the controller
    assert menu.are_controls_shown_for_controller(), 'a controller button did not switch the Controls page'
    pad_jump = menu.get_control_text(2)
    assert pad_jump in ('A', 'Cross', 'Bottom button'), f'jump is not shown as the controller button: {pad_jump}'
    state['memo']['controls'] = {'count': count, 'pad_jump': pad_jump, 'pad_hotbar_5_8': menu.get_control_text(11)}
    assert key('Escape') and menu.get_tab() == 1 and menu.get_selected() == 16, 'Escape did not return from Controls to CONTROLS'
    assert key('Down') and menu.get_selected() == 17, 'Down did not reach BACK'
    assert key('Enter') and menu.get_tab() == 0 and menu.get_selected() == 12, 'BACK did not return to the buttons at OPTIONS'
    state['memo']['settings'] = (after_brightness, looks)
    assert key('Up') and menu.get_selected() == 11, 'Up from OPTIONS did not reach SAVE GAME'
    checks.append('OPTIONS opens the settings: brightness (the display gamma), four look speeds and the volume (its dial following) '
                  'change live by keys; sound effects and ambience volumes too; CONTROLS lists every control, switching to the controller buttons; graphics quality steps Low to Epic, a group alone makes it custom; button icons step Automatic, Xbox, PlayStation; interface size steps 80% to 150%; BACK returns to the buttons')


def save_game():
    menu = pc().get_options_widget()
    assert menu.get_selected() == 11, 'SAVE GAME is not selected'
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
    assert all(abs(pc().get_look_sensitivity(i) - state['memo']['settings'][1][i]) < .001 for i in range(4))
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
    for _ in range(3):
        assert lib.send_verification_ui_key(pc(), 'Down')
    assert pc().get_options_widget().get_selected() == 13, 'Down navigation did not move to MAIN MENU'
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
    # Single Player opens the Freeport choice (November 7); a survivor was saved, so Resume Game is offered.
    ports = pc().get_port_select_widget()
    assert ports and ports.is_resume_shown(), 'Resume Game is not offered after saving'
    ports.resume()
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
    ('Escape brings up the pause menu on RESUME GAME; the world pauses and the mouse shows', escape, menu_up, 4),
    ('Enter on RESUME GAME returns to the game and the world runs', ui_key('Enter'), menu_gone, 4),
    ('Hurt, hungry and thirsty with stone, the Hatchet in hand and the Pickaxe on the hotbar, Escape', prepare, prepared, 6),
    ('', lambda: None, menu_up, 4),
    ('', adjust_settings, lambda: pc().get_options_widget().get_selected() == 11, 4),
    ('Enter on SAVE GAME saves the survivor as they are; the menu stays up', save_game, saved, 4),
    ('The save, put back on a survivor who has since changed, restores them exactly, tools not doubled', restore, restored, 4),
    ('Mouse horizontal and vertical speeds turn the view left-right and up-down by their own amounts', look_start, look_done, 3),
    ('Escape, Down to MAIN MENU, Enter', to_main_menu, main_menu_chosen, 4),
    ('MAIN MENU opens the ELITEWAKE title screen', lambda: None, at_title, 30),
    ('Single Player from the title resumes the saved survivor where and as they were, tools not doubled', single_player, resumed, 40),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    try:
        initial = state['memo'].get('initial_user_settings')
        if initial and world() and pc():
            pc().set_user_brightness(initial[0])
            for i in range(4):
                pc().set_look_sensitivity(i, initial[1][i])
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
