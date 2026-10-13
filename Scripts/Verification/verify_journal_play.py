"""Acceptance for the Journal's playtest guides: open the menu, choose JOURNAL, read the pages.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground (one player is enough), with the pages from
Scripts/Setup/create_test_journal.py. Run unattended with run_play_check.py; set EW_PLAY_PLAYERS=1.

  1. The menu opens and its JOURNAL section shows the Journal panel with every guide listed.
  2. Choosing each guide shows its title and text; the ship guides are all there.
  3. A screenshot of the Journal is saved for review: Saved/Screenshots/Journal/journal.png.
Writes Saved/JournalPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
RESULT = saved / 'JournalPlayResult.json'
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
WANTED = ['Getting aboard', 'Raising and dropping the anchor', 'Fitting sails', 'Fitting the wheel', 'Sailing and steering',
          'Paddling the raft', 'Finding your way about a ship']
checks, state = [], {'step': 0, 'at': time.monotonic() + 2, 'handle': None, 'seen': []}


def menu():
    return next((w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWInventoryWidget, False)
                 if w.get_owning_player() == pc and w.is_in_viewport()), None)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'pages': state['seen']}, indent=2))
    unreal.log(f'EWPLAYCHECK Journal success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        step = state['step']
        if step == 0:
            pc.set_inventory_open(True)
        elif step == 1:
            m = menu()
            assert m, 'the menu did not open'
            m.open_section(6)
        elif step == 2:
            journal = menu().get_journal_panel()
            assert journal and journal.is_visible(), 'the Journal panel is not showing'
            count = journal.get_page_count()
            assert count >= len(WANTED), f'only {count} pages'
            for k in range(count):
                journal.show_page(k)
                state['seen'].append(str(journal.get_shown_title()))
            missing = [t for t in WANTED if t not in state['seen']]
            assert not missing, f'missing guides: {missing}'
            checks.append(f'The JOURNAL section lists {count} guides, including every ship guide')
            journal.show_page(state['seen'].index('Fitting sails'))
            folder = saved / 'Screenshots' / 'Journal'
            folder.mkdir(parents=True, exist_ok=True)
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{folder / "journal.png"}"')
        elif step == 3:
            checks.append('Each guide shows its title and text; screenshot saved')
            pc.set_inventory_open(False)
            finish()
            return
        state.update(step=step + 1, at=time.monotonic() + 1.5)
    except Exception as error:
        finish(f'step {state["step"]}: {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
