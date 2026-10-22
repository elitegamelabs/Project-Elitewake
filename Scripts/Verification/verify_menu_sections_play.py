"""Play: every menu section (inventory, crafting, building, skills, company, tames, journal) is reachable by keyboard and controller, and the Journal pages with the
arrows (owner, October 22). Run with EW_PLAY_PLAYERS=2 like the other menu checks. Writes Saved/MenuSectionsPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
client_world = worlds[pcs.index(client)]
# (key to press, section expected afterwards): forward with PageDown, RB and Tab; back with PageUp, LT and Tab with shift is not sendable here.
STEPS = [('PageDown', 1), ('PageDown', 2), ('PageDown', 3), ('Gamepad_RightShoulder', 4), ('PageDown', 5), ('Tab', 6), ('Tab', 0),
         ('PageUp', 6), ('Gamepad_LeftTrigger', 5), ('PageUp', 4), ('PageUp', 3), ('PageUp', 2), ('PageUp', 1), ('PageUp', 0)]
phase = 0
next_at = time.monotonic() + 2
checks = []
handle = None


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWInventoryWidget, False)
                if w.get_owning_player() == client and w.is_in_viewport())


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(), 'MenuSectionsPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 0.6
    try:
        if phase == 0:
            client.set_inventory_open(True)
        elif phase == 1:
            assert menu().get_selected_section() == 0
        elif 2 <= phase < 2 + len(STEPS):
            if phase > 2:
                key, want = STEPS[phase - 3]
                got = menu().get_selected_section()
                assert got == want, f'{key} led to section {got}, expected {want}'
            if phase - 2 < len(STEPS):
                assert lib.send_verification_ui_key(client, STEPS[phase - 2][0]), STEPS[phase - 2][0]
        elif phase == 2 + len(STEPS):
            key, want = STEPS[-1]
            assert menu().get_selected_section() == want, f'{key} did not return to the inventory'
            checks.append('Tab, PageDown, PageUp, right bumper and left trigger step through all seven sections and wrap')
            # The Journal: Down pages forward, Up pages back.
            menu().open_section(6)
        elif phase == 3 + len(STEPS):
            journal = menu().get_journal_panel()
            assert journal.get_page_count() > 1
            assert journal.get_selected_page() <= 0
            assert lib.send_verification_ui_key(client, 'Down')
        elif phase == 4 + len(STEPS):
            journal = menu().get_journal_panel()
            assert journal.get_selected_page() == 1, f'Down left the Journal on page {journal.get_selected_page()}'
            assert lib.send_verification_ui_key(client, 'Gamepad_DPad_Up')
        elif phase == 5 + len(STEPS):
            assert menu().get_journal_panel().get_selected_page() == 0
            checks.append('The Journal pages with the arrows and the d-pad')
            assert menu().get_selected_section() == 6
            assert lib.send_verification_ui_key(client, 'Escape')
        elif phase == 6 + len(STEPS):
            assert not client.is_inventory_open(), 'Escape did not close the menu from the Journal'
            checks.append('Escape closes the menu from a section other than inventory')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
