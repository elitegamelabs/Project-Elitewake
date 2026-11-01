"""Play: the left trigger no longer changes the d-pad (owner, November 1: hotbar slots 5 to 8 are LB with X, Y, B, A; the
October 22 left-trigger chord is removed). Holding the left trigger, d-pad left is still slot 1, never slot 5.
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
            key('Gamepad_DPad_Down')                                             # d-pad down: slot 4, so a change to slot 1 shows
        elif phase == 3:
            assert bar.get_selected_slot() == 3, f'd-pad down selected slot {bar.get_selected_slot() + 1}'
            event('Gamepad_LeftTrigger', True)
            key('Gamepad_DPad_Left')                                             # LT + d-pad left: slot 1 now, not slot 5
            event('Gamepad_LeftTrigger', False)
        elif phase == 4:
            assert bar.get_selected_slot() == 0, f'LT + d-pad left selected slot {bar.get_selected_slot() + 1}, not slot 1'
            checks.append('Holding the left trigger, d-pad left selects slot 1 (the d-pad\'s own); the left trigger no longer reaches slot 5')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
