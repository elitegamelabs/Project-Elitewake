"""Captures the menu sections, the damage number and the death screen, for looking at (not a pass/fail check). One player: run with EW_PLAY_PLAYERS=1 and
EW_PLAY_WINDOW=1600x900. Writes PNGs to Saved/Screenshots/MenuScreens and Saved/MenuScreensResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
world = worlds[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
progress = pawn.get_progression_component()
stats = pawn.get_survival_component()
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'MenuScreens')
SHOTS.mkdir(parents=True, exist_ok=True)
for old in SHOTS.glob('*.png'):
    old.unlink()
steps = []
done = []
handle = None
state = {'i': 0, 'at': time.monotonic() + 3}


def key(name):
    return lambda: lib.send_verification_ui_key(pc, name)


def shot(name):
    return lambda: unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (name + ".png")}"')


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWInventoryWidget, False) if w.is_in_viewport())


def level_up():
    progress.grant_experience(progress.get_experience_for_next_level())
    progress.grant_experience(progress.get_experience_for_next_level())


steps = [
    (level_up, 1.0), (lambda: pc.set_inventory_open(True), 2.0), (shot('1_inventory_survivor'), 2.0),
    (key('PageDown'), 2.0), (shot('2_crafting'), 2.0),
    (key('PageDown'), 1.0), (key('PageDown'), 2.0),
    (lambda: menu().get_skills_panel().select_node(1), 1.0), (key('Enter'), 1.5), (lambda: menu().get_skills_panel().select_node(3), 1.0), (shot('3_skills'), 2.0),
    (key('PageDown'), 1.0), (key('PageDown'), 1.0), (key('PageDown'), 2.0), (shot('4_journal'), 2.0),
    (lambda: pc.set_inventory_open(False), 1.5), (lambda: stats.apply_damage(9.0), 0.3), (shot('5_damage_number'), 1.5),
    (lambda: stats.apply_damage(1000.0), 3.2), (shot('6_death'), 1.5),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'MenuScreensResult.json').write_text(json.dumps({'success': error is None, 'shots': sorted(p.name for p in SHOTS.glob('*.png')), 'error': error}, indent=2))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(steps):
            finish()
            return
        action, wait = steps[state['i']]
        action()
        state['i'] += 1
        state['at'] = time.monotonic() + wait
    except Exception as exc:
        finish(f'Step {state["i"]}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
