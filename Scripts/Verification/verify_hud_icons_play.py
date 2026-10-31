"""Screenshots of the five survival icons at full, about half, and nearly empty (single-player Play session), to judge by eye
that every icon drains and refills with its stat. Also reads the fill fractions the widget reports.
Takes pictures into Saved/Screenshots/Hud and writes Saved/HudIconsPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
survival = pawn.get_survival_component()
shots = saved / 'Screenshots' / 'Hud'
shots.mkdir(parents=True, exist_ok=True)
state = {'step': 0, 'at': time.monotonic() + 3, 'handle': None}
checks = []
LEVELS = {'full': 1.0, 'half': .5, 'low': .12}


def hud():
    return next(x for x in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWSurvivalWidget, False)
                if x.get_owning_player() == pc and x.is_in_viewport())


def settle():
    start = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)[0]
    pawn.set_actor_location(start.get_actor_location() + unreal.Vector(0, 0, 120), False, True)
    pc.set_control_rotation(unreal.Rotator(0, -10, 0))
    checks.append({'pawn': str(pawn.get_actor_location())})


def setlevel(name):
    f = LEVELS[name]
    survival.restore_health(1000.0)
    survival.apply_damage(100.0 * (1 - f)) if f < 1 else None
    survival.set_hunger(100.0 * f)
    survival.set_hydration(100.0 * f)
    survival.set_carried_weight(survival.get_max_carry_weight() * f)


def shot(name):
    fills = [round(x, 2) for x in hud().get_displayed_fill_fractions()]
    checks.append({'level': name, 'fills': fills, 'summary': str(hud().get_displayed_summary())})
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / (name + ".png")}"')


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    (saved / 'HudIconsPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))
    unreal.log(f'EWPLAYCHECK HudIcons success={error is None} error={error}')


STEPS = [(settle, 3.0)]
for n in LEVELS:
    STEPS += [(lambda n=n: setlevel(n), 1.5), (lambda n=n: shot(n), 1.5)]
STEPS.append((finish, 0.1))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        action, wait = STEPS[state['step']]
        action()
        state['step'] += 1
        state['at'] = time.monotonic() + wait
    except Exception as error:
        finish(f'step {state["step"] + 1}: {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
