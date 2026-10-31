"""Play: on a controller, holding the left trigger turns the d-pad into hotbar slots 5 to 8 (owner, October 22), and the d-pad alone is still slots 1 to 4.
One player (EW_PLAY_PLAYERS=1). Uses the starter kit's tools. Writes Saved/HotbarTriggerPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
bar = pawn.get_hotbar_component()
pack = pawn.get_inventory_component()
axe = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenAxe')
pick = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenPickaxe')
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
phase = 0
next_at = time.monotonic() + 3
checks = []
handle = None


def key(name):
    assert lib.send_verification_ui_key(pc, name), name


def event(name, pressed):
    assert lib.send_verification_ui_key_event(pc, name, pressed), name


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'HotbarTriggerPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 1.0
    try:
        if phase == 0:
            pc.set_inventory_open(False)
            pack.add_item(axe, 1) if pack.get_item_count(axe) == 0 and not pawn.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) else None
            pack.add_item(wood, 5)
            assert lib.send_verification_hotbar_request(pc, 0, wood, False)      # slot 1: wood
            assert lib.send_verification_hotbar_request(pc, 4, wood, False)      # slot 5: wood (moves the single shortcut to slot 5)
        elif phase == 2:
            assert bar.get_bound_item(4) == wood, 'slot 5 not bound'
            key('Gamepad_DPad_Left')                                             # d-pad alone: slot 1 (unbound now: nothing)
        elif phase == 3:
            assert bar.get_selected_slot() != 4, 'the d-pad alone reached slot 5'
            event('Gamepad_LeftTrigger', True)
            key('Gamepad_DPad_Left')                                             # LT + d-pad left: slot 5
            event('Gamepad_LeftTrigger', False)
        elif phase == 4:
            assert bar.get_selected_slot() == 4, f'LT + d-pad left selected slot {bar.get_selected_slot()}'
            checks.append('Holding the left trigger, d-pad left activates hotbar slot 5; the d-pad alone does not')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
