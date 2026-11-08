"""Captures the discovery banner and the Journal's Discoveries pages (Part 8, 63) on one player's screen:
    Scripts/Verification/run_play_check_once.ps1 -Check capture_discoveries.py -Result DiscoveriesCaptureResult.json -Players 1 -Standalone 1 -Kit 1
Saved/Screenshots/Discoveries/Banner.png, JournalSummary.png, JournalIsland.png. Visual review pending.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'Discoveries'
shots.mkdir(parents=True, exist_ok=True)
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
state = {'phase': 0, 'at': time.monotonic() + 8, 'handle': None}
report = {}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'DiscoveriesCaptureResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK DiscoveriesCapture success={error is None} error={error}')


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / name}"')


def hud():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWSurvivalWidget, False) if w.is_in_viewport())


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWInventoryWidget, False) if w.is_in_viewport())


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            # Let the start's own discoveries pass first.
            if str(hud().get_displayed_discovery()):
                state['at'] = time.monotonic() + 1
                return
            i = W.island('Plains2')
            a = 0.0
            r = i.radius(a) - 2500
            x, y = i.cx + r * math.cos(a), i.cy + r * math.sin(a)
            pawn.teleport(unreal.Vector(x, y, T.height(x, y) + 150), unreal.Rotator())
            state.update(phase=1, at=time.monotonic() + 2.2)
        elif p == 1:
            report['banner'] = str(hud().get_displayed_discovery())
            shot('Banner.png')
            state.update(phase=2, at=time.monotonic() + 8)
        elif p == 2:
            pc.set_inventory_open(True)
            state.update(phase=3, at=time.monotonic() + 1)
        elif p == 3:
            m = menu()
            m.open_section(4)
            journal = m.get_journal_panel()
            journal.refresh_discoveries()
            journal.show_page(0)
            report['titles'] = [str(t) for t in journal.get_page_titles()]
            state.update(phase=4, at=time.monotonic() + 1)
        elif p == 4:
            shot('JournalSummary.png')
            journal = menu().get_journal_panel()
            journal.show_page(report['titles'].index('Copper Downs'))
            state.update(phase=5, at=time.monotonic() + 1.5)
        elif p == 5:
            shot('JournalIsland.png')
            state.update(phase=6, at=time.monotonic() + 1.5)
        else:
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
