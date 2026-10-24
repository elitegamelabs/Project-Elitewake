"""Play: assigning an item to a hotbar slot with the controller alone (owner, October 22: hotbar assignment by controller). Y puts the selected item on the first empty slot;
Y again, with the item already on the bar, opens a slot picker: the d-pad moves the cursor, A moves the item to that slot (or takes it off the slot it is on), B or Y
cancels without closing the menu. One player (EW_PLAY_PLAYERS=1). Writes Saved/HotbarPickerPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
bar = pawn.get_hotbar_component()
pack = pawn.get_inventory_component()
hat = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHat')
checks = []
phase = 0
next_at = time.monotonic() + 3
handle = None


def key(name):
    assert lib.send_verification_ui_key(pc, name), name


def ui():
    return next((u for u in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWInventoryWidget, False) if u.get_owning_player() == pc and u.is_in_viewport()), None)


def bound_slots():
    return [i for i in range(8) if bar.get_bound_item(i) == hat]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    pc.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(), 'HotbarPickerPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 1.0
    try:
        if phase == 0:
            pc.set_inventory_open(False)
            for e in list(pawn.get_equipment_component().get_equipment_entries()):
                pawn.get_equipment_component().unequip_item(e.get_editor_property('slot'))
            for e in list(pack.get_inventory_entries()):
                pack.remove_item(e.get_editor_property('item_definition'), e.get_editor_property('quantity'))
            for i in range(8):
                if bar.get_bound_item(i):
                    assert lib.send_verification_hotbar_request(pc, i, None, False)
            assert pack.add_item(hat, 1) == 1
        elif phase == 1:
            key('Gamepad_FaceButton_Top')                  # Y opens the menu
        elif phase == 2:
            panel = ui()
            assert panel, 'Y did not open the inventory'
            assert panel.get_selected_item_definition() == hat, 'the hat is not selected'
            key('Gamepad_FaceButton_Top')                  # Y with the item off the bar: quick-assign to the first empty slot
        elif phase == 3:
            assert bound_slots() == [0], f'quick-assign put the hat on {bound_slots()}'
            assert ui().get_hotbar_pick() == -1
            key('Gamepad_FaceButton_Top')                  # Y with the item already on the bar: the picker opens on its slot
        elif phase == 4:
            assert ui().get_hotbar_pick() == 0, f'the picker opened on {ui().get_hotbar_pick()}'
            checks.append('Y with the item already on the bar opens the slot picker on that slot')
            key('Gamepad_DPad_Right')
            key('Gamepad_DPad_Right')
        elif phase == 5:
            assert ui().get_hotbar_pick() == 2, f'two presses of d-pad right put the cursor on {ui().get_hotbar_pick()}'
            key('Gamepad_DPad_Left')
            key('Gamepad_DPad_Left')
            key('Gamepad_DPad_Left')
        elif phase == 6:
            assert ui().get_hotbar_pick() == 7, f'three presses of d-pad left from slot 3 put the cursor on {ui().get_hotbar_pick()} (the cursor wraps)'
            checks.append('The d-pad moves the picker cursor and it wraps round the eight slots')
            key('Gamepad_DPad_Left')
            key('Gamepad_DPad_Left')
            key('Gamepad_DPad_Left')
            key('Gamepad_DPad_Left')
            key('Gamepad_DPad_Left')
        elif phase == 7:
            assert ui().get_hotbar_pick() == 2
            key('Gamepad_FaceButton_Bottom')               # A puts the item on slot 3
        elif phase == 8:
            assert bound_slots() == [2], f'A in the picker left the hat on {bound_slots()}'
            assert ui().get_hotbar_pick() == -1, 'the picker stayed open after A'
            assert ui() is not None, 'A closed the menu'
            checks.append('A in the picker moves the item to the chosen slot and closes the picker, not the menu')
            key('Gamepad_FaceButton_Top')                  # Y: picker again, then B cancels
        elif phase == 9:
            assert ui().get_hotbar_pick() == 2
            key('Gamepad_FaceButton_Right')
        elif phase == 10:
            assert ui() is not None, 'B in the picker closed the whole menu'
            assert ui().get_hotbar_pick() == -1, 'B did not cancel the picker'
            assert bound_slots() == [2]
            checks.append('B cancels the picker and leaves the menu open')
            key('Gamepad_FaceButton_Top')
        elif phase == 11:
            assert ui().get_hotbar_pick() == 2
            key('Gamepad_FaceButton_Bottom')               # A on the slot the item is already on takes it off
        elif phase == 12:
            assert bound_slots() == [], f'A on its own slot left the hat on {bound_slots()}'
            checks.append('A on the slot the item is on takes it off')
            key('Gamepad_FaceButton_Right')                # B closes the menu again
        elif phase == 13:
            assert ui() is None, 'B did not close the menu'
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
