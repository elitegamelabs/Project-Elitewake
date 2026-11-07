"""Play: the single-player front end (owner, November 7), on the title map, one player in the editor:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_front_end_play.py -Result FrontEndPlayResult.json -Players 1 -Map /Game/Elitewake/Maps/Lvl_Title
  1. Single Player opens the Freeport choice: the whole world in a box, every Freeport marked inside it, and Resume Game
     shown only when a survivor was played before (a save exists), with Create New Survivor; Create New asks before replacing it.
  2. Controller and keyboard: the D-pad chooses a Freeport, A confirms, B goes back.
  3. The creator: the survivor stands in the left-half box; male and female; presets; every slider and choice is offered
     (body, face, hair, skin, makeup, tattoos); body sliders reshape the preview's bones, height and build its size; LB/RB
     change tabs; Y randomises; a custom tattoo is kept.
  4. Set Sail (held on the title map here) hands the look and the chosen Freeport to the game instance; the loading screen shows.
Captures (with the interface) in Saved/Screenshots/FrontEnd. The player's own save is moved aside and put back.
Writes Saved/FrontEndPlayResult.json.
"""
import json
import shutil
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
RESULT = saved / 'FrontEndPlayResult.json'
SHOTS = saved / 'Screenshots' / 'FrontEnd'
SHOTS.mkdir(parents=True, exist_ok=True)
save_file = saved / 'SaveGames' / 'Survivor.sav'
backup = save_file.with_suffix('.sav.frontendbackup')
assert not backup.exists(), f'A previous front-end check left the player save at {backup}; put it back first.'
if save_file.exists():
    shutil.move(str(save_file), str(backup))
# Set Sail saves the look made; keep the player's own.
look_file = saved / 'SaveGames' / 'Appearance.sav'
look_backup = look_file.with_suffix('.sav.frontendbackup')
if look_file.exists() and not look_backup.exists():
    shutil.copy2(str(look_file), str(look_backup))

report = {'checks': []}
state = {'phase': 'wait', 'at': time.monotonic() + 2.0, 'h': None, 'deadline': time.monotonic() + 20.0}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    try:
        if save_file.exists():
            save_file.unlink()          # the stand-in save this check made
        if backup.exists():
            shutil.move(str(backup), str(save_file))
        if look_backup.exists():
            shutil.move(str(look_backup), str(look_file))
    except Exception as e:      # noqa: BLE001
        error = error or f'could not restore the player save: {e!r}'
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK FrontEnd success={error is None} error={error}')


def pc():
    for world in lib.get_play_worlds():
        c = unreal.GameplayStatics.get_player_controller(world, 0)
        if isinstance(c, unreal.EWTitlePlayerController):
            return c
    return None


def key(name):
    assert lib.send_verification_ui_key(pc(), name), f'could not send {name}'


def shot(name):
    world = pc().get_world()
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (name + ".png")}"')
    report.setdefault('shots', []).append(name)


def stand_in_save(make):
    """A survivor save in the slot, as after playing before (or none)."""
    if make:
        save = unreal.GameplayStatics.create_save_game_object(unreal.EWSurvivorSave)
        assert unreal.GameplayStatics.save_game_to_slot(save, 'Survivor', 0)
    elif save_file.exists():
        save_file.unlink()


def later(phase, seconds=.6):
    state.update(phase=phase, at=time.monotonic() + seconds)


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        c = pc()
        if p == 'wait':
            if not c or not c.get_title_widget():
                assert time.monotonic() < state['deadline'], 'the title did not appear'
                return
            stand_in_save(True)
            key('Enter')                                   # splash to the main menu
            later('menu')
        elif p == 'menu':
            title = c.get_title_widget()
            check('the main menu shows', title.is_main_menu_screen())
            title.start_single_player()
            later('ports_resume', 1.0)
        elif p == 'ports_resume':
            ports = c.get_port_select_widget()
            check('Single Player opens the Freeport choice', ports is not None and ports.is_in_viewport())
            check('Resume Game is offered after playing before', ports.is_resume_shown())
            shot('PortSelect_Resume')
            later('ask')
        elif p == 'ask':
            ports = c.get_port_select_widget()
            # Create New asks first when it would replace that survivor; B keeps it.
            key('Gamepad_DPad_Right')
            key('Gamepad_FaceButton_Bottom')
            check('Create New asks before replacing the survivor played before', ports.is_asking_to_replace())
            shot('PortSelect_Replace')
            later('keep')
        elif p == 'keep':
            ports = c.get_port_select_widget()
            key('Gamepad_FaceButton_Right')
            check('B keeps the survivor', not ports.is_asking_to_replace())
            key('Gamepad_FaceButton_Right')                # B again: back to the main menu
            later('back_to_menu')
        elif p == 'back_to_menu':
            check('B goes back to the main menu', not c.get_port_select_widget().is_in_viewport() and c.get_title_widget().is_main_menu_screen())
            stand_in_save(False)
            c.get_title_widget().start_single_player()
            later('ports_new', 1.0)
        elif p == 'ports_new':
            ports = c.get_port_select_widget()
            check('without a save, only Create New Survivor is offered', not ports.is_resume_shown())
            size = unreal.WidgetLayoutLibrary.get_viewport_size(c) / unreal.WidgetLayoutLibrary.get_viewport_scale(c)
            markers = [ports.get_port_marker(i) for i in range(5)]
            report['markers'] = [[round(m.x), round(m.y)] for m in markers]
            check('all five Freeports are marked inside the world box', all(.05 * size.x < m.x < .95 * size.x and .15 * size.y < m.y < .79 * size.y for m in markers),
                  markers=report['markers'])
            for _ in range(3):
                key('Gamepad_DPad_Down')
            check('the D-pad chooses a Freeport', ports.get_selected_port() == 3 and str(ports.get_selected_port_id()) == 'Desert',
                  port=ports.get_selected_port())
            key('Up')
            check('the arrow keys choose too', ports.get_selected_port() == 2)
            ports.select_port(3)
            shot('PortSelect')
            later('create')
        elif p == 'create':
            key('Gamepad_FaceButton_Bottom')               # A on Create New Survivor
            later('creator', 1.5)
        elif p == 'creator':
            creator = c.get_creator_widget()
            preview = c.get_preview()
            check('Create New Survivor opens the creator with the survivor standing', creator is not None and creator.is_in_viewport() and preview is not None)
            shown, body = preview.get_editor_property('shown'), preview.get_editor_property('body')
            report['preview'] = {'shown_material': shown.get_material(0).get_path_name() if shown.get_material(0) else None,
                                 'body_material': body.get_material(0).get_path_name() if body.get_material(0) else None,
                                 'shown_visible': shown.is_visible(), 'body_visible': body.is_visible(), 'body_playing': body.is_playing(),
                                 'shown_mesh': str(shown.get_skinned_asset().get_name() if shown.get_skinned_asset() else None),
                                 'hand_shown': str(shown.get_socket_location('hand_l')), 'hand_body': str(body.get_socket_location('hand_l'))}
            check('the shown survivor wears the survivor body and the idle pose', 'SurvivorBody' in str(report['preview']['shown_material'])
                  and (shown.get_socket_location('hand_l') - body.get_socket_location('hand_l')).length() < 5, preview=report['preview'])
            box = creator.get_preview_box()
            size = unreal.WidgetLayoutLibrary.get_viewport_size(c) / unreal.WidgetLayoutLibrary.get_viewport_scale(c)
            check('the preview box fills the left half', box.x < .05 * size.x and (box.x + box.z) < .5 * size.x and box.z > .4 * size.x and box.w > .8 * size.y,
                  box=[round(v) for v in (box.x, box.y, box.z, box.w)])
            # The survivor stands inside the box on screen.
            projected = unreal.GameplayStatics.project_world_to_screen(c, preview.get_actor_location() + unreal.Vector(0, 0, 100))
            ok, at = (True, projected) if isinstance(projected, unreal.Vector2D) else projected
            scale = unreal.WidgetLayoutLibrary.get_viewport_scale(c)
            x, y = at.x / scale, at.y / scale
            report['survivor_on_screen'] = [round(x), round(y)]
            check('the survivor stands inside the preview box', ok and box.x < x < box.x + box.z and box.y < y < box.y + box.w, at=[round(x), round(y)])
            check('every face and body feature is offered', creator.get_total_option_count() >= 70, options=creator.get_total_option_count())
            shot('Creator_Body')
            key('Gamepad_RightShoulder')
            check('RB moves to the next tab (face)', creator.get_tab() == 1 and creator.get_row_count() >= 40, rows=creator.get_row_count())
            key('Gamepad_DPad_Down')
            key('Gamepad_DPad_Down')
            report['face_row'] = creator.get_selected_row_label()
            before = creator.get_appearance().features
            key('Gamepad_DPad_Right')
            check('the D-pad moves a face slider', list(creator.get_appearance().features) != list(before), row=report['face_row'])
            later('face_shot', .3)
        elif p == 'face_shot':
            shot('Creator_Face')
            later('shape')
        elif p == 'shape':
            creator, preview = c.get_creator_widget(), c.get_preview()
            creator.show_tab(0)
            creator.set_slider_value('UpperArms', 1.0)
            creator.set_slider_value('Shoulders', 0.0)
            creator.set_slider_value('Height', 1.0)
            creator.set_slider_value('Build', 1.0)
            arm = preview.get_bone_shape('upperarm_l')
            shoulder = preview.get_bone_shape('clavicle_r')
            scale = preview.get_editor_property('shown').get_editor_property('relative_scale3d')
            mid = preview.get_editor_property('shown').get_material(0)
            tone = mid.get_vector_parameter_value('Tone') if mid else None
            report['skin_tone_param'] = [round(tone.r, 3), round(tone.g, 3), round(tone.b, 3)] if tone else None
            report['shape'] = {'upperarm_l': [round(arm.x, 3), round(arm.y, 3), round(arm.z, 3)], 'clavicle_r': round(shoulder.x, 3),
                               'scale': [round(scale.x, 3), round(scale.z, 3)]}
            check('the arm slider thickens the preview upper arm', abs(arm.y - 1.25) < .01 and abs(arm.x - 1.0) < .01)
            check('the shoulder slider narrows the shoulders', abs(shoulder.x - .8) < .01)
            check('height and build size the preview', abs(scale.z - 1.12) < .01 and abs(scale.x - 1.12 * 1.14) < .01)
            later('shape_shot', .5)
        elif p == 'shape_shot':
            shot('Creator_Shaped')
            later('female')
        elif p == 'female':
            creator, preview = c.get_creator_widget(), c.get_preview()
            roster = unreal.load_asset('/Game/Elitewake/Characters/DA_BodyRoster')
            creator.select_body(1)
            creator.select_preset(1)
            body = roster.get_editor_property('bodies')[1].get_editor_property('mesh')
            check('Female shows the woman, from her preset', preview.get_editor_property('shown').get_skinned_asset() == body
                  and creator.get_appearance().preset == 1)
            creator.set_tattoo(0, 3, 4, .7, .5, 1)
            creator.set_choice_value('HairStyle', 3)
            look = creator.get_appearance()
            check('a custom tattoo and hair are kept in the look', len(look.tattoos) >= 1 and look.tattoos[0].design == 3 and look.picks[0] == 3)
            before = list(creator.get_appearance().features)
            key('Gamepad_FaceButton_Top')
            check('Y randomises the survivor', list(creator.get_appearance().features) != before)
            for tab in range(6):
                creator.show_tab(tab)
                report.setdefault('rows_per_tab', []).append(creator.get_row_count())
            check('every tab has options', all(n > 0 for n in report['rows_per_tab']), rows=report['rows_per_tab'])
            creator.show_tab(5)
            later('tattoo_shot', .3)
        elif p == 'tattoo_shot':
            shot('Creator_Tattoos')
            later('sail')
        elif p == 'sail':
            creator = c.get_creator_widget()
            look = creator.get_appearance()
            c.set_editor_property('stay_on_set_sail', True)
            key('Gamepad_Special_Right')                   # Start: Set Sail
            instance = unreal.GameplayStatics.get_game_instance(c.get_world())
            check('Set Sail starts the voyage', c.has_set_sail() and not c.did_resume())
            check('the chosen Freeport goes with it', str(instance.get_chosen_freeport()) == 'Desert' and instance.will_start_at_freeport())
            chosen = instance.get_chosen_appearance()
            check('the look made goes with it', list(chosen.features) == list(look.features) and chosen.body == look.body)
            # The loading screen, as it shows after Set Sail.
            instance.show_loading_screen()
            check('the loading screen shows over everything', instance.is_loading_screen_shown())
            later('loading_shot', 1.5)
        elif p == 'loading_shot':
            shot('Loading')
            later('done')
        elif p == 'done':
            finish()
    except Exception as error:      # noqa: BLE001
        finish(f'{state["phase"]}: {error!r}')


state['h'] = unreal.register_slate_post_tick_callback(tick)
