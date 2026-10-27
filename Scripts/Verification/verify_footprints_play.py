"""Footprints (single-player Play session). Owner, October 26: black footprints on the Plains and on each island by its
weather; on firm ground they fade within a few seconds, in snow, mud and sand they stay but only the last six, one vanishing
at a time as a new one is made.
Walks the survivor on the Plains (prints appear, none are lasting, all gone a few seconds after stopping), then across the
Winter Port's snow (many prints made, exactly six showing, still six when standing still), then on a beach (sand lasts).
Writes Saved/FootprintsPlayResult.json and screenshots to Saved/Screenshots/Footprints."""
import json
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
prints = pawn.get_editor_property('footprint_component')
survival = pawn.get_survival_component()
shots = saved / 'Screenshots' / 'Footprints'
shots.mkdir(parents=True, exist_ok=True)
state = {'step': 0, 'at': time.monotonic() + 12, 'handle': None, 'walk_until': 0.0, 'direction': unreal.Vector(1, 0, 0)}
report = {'checks': []}
SURFACES = {}


def note(label, **values):
    report['checks'].append({'label': label, **values})
    unreal.log(f'Footprints: {label} {values}')


def teleport(x, y, z, heading):
    survival.restore_health(1000.0)
    pawn.set_actor_location(unreal.Vector(x, y, z), False, True)
    pc.set_control_rotation(unreal.Rotator(0, 0, heading))
    state['direction'] = unreal.MathLibrary.get_forward_vector(unreal.Rotator(0, 0, heading))


def walk(seconds):
    state['walk_until'] = time.monotonic() + seconds


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / name}.png"')


def surface():
    return str(prints.get_last_surface())


def plains_start():
    teleport(-1200, 0, 600, 0)


def plains_walked():
    made = prints.get_prints_made()
    loc = pawn.get_actor_location()
    note('plains: walking made prints', x=round(loc.x), y=round(loc.y), z=round(loc.z), mode=str(pawn.character_movement.movement_mode), tick=prints.is_component_tick_enabled(), made=made, showing=prints.get_print_count(), lasting=prints.get_lasting_print_count(), surface=surface())
    assert made >= 3, 'no footprints on the plains'
    assert prints.get_lasting_print_count() == 0 and 'FIRM' in surface().upper(), 'plains prints should not last'
    shot('Plains')


def plains_faded():
    note('plains: after stopping', showing=prints.get_print_count())
    assert prints.get_print_count() == 0, 'plains prints did not fade away'


def winter_start():
    port = W.PORTS['Winter']
    x, y = port.world(W.PORT_INLAND - 3000, 0)
    teleport(x, y, 800, port.facing * 57.29578 + 180)


def winter_walked():
    made = prints.get_prints_made()
    note('winter: walking made prints', made=made, showing=prints.get_print_count(), lasting=prints.get_lasting_print_count(), surface=surface())
    assert 'SNOW' in surface().upper(), f'winter ground is {surface()}'
    assert prints.get_lasting_print_count() == 6, 'snow should hold exactly the last six prints'
    shot('Snow')


def winter_still():
    note('winter: standing still', showing=prints.get_print_count(), lasting=prints.get_lasting_print_count())
    assert prints.get_lasting_print_count() == 6 and prints.get_print_count() <= 7, 'snow prints should stay'
    shot('SnowStill')


def desert_beach():
    # Where the starter island's ground first dips under 0 along the dock's line: its beach, a little above the water.
    x = next(x for x in range(2000, 9000, 50) if T.height(x, 900) < -10)
    note('beach: shore found', x=x, ground=round(T.height(x - 400, 900)))
    teleport(x - 600, 900, 600, 0)


def beach_walked():
    loc = pawn.get_actor_location()
    note('beach: walking', lasting=prints.get_lasting_print_count(), surface=surface(), x=round(loc.x), y=round(loc.y), z=round(loc.z))
    assert prints.get_lasting_print_count() >= 1 and 'SAND' in surface().upper(), 'a Plains beach should hold sand prints'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'FootprintsPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Footprints success={error is None} error={error}')


STEPS = [(plains_start, 2.5), (lambda: walk(3.0), 3.4), (plains_walked, 5.0), (plains_faded, .1),
         (winter_start, 3.0), (lambda: walk(5.0), 5.4), (winter_walked, 1.5), (winter_still, .1),
         (desert_beach, 3.0), (lambda: walk(1.0), 1.1), (beach_walked, .1), (finish, .1)]


def tick(delta):
    survival.restore_health(1000.0)
    survival.set_hunger(100.0)
    survival.set_hydration(100.0)
    if time.monotonic() < state['walk_until']:
        pawn.add_movement_input(state['direction'], 1.0, False)
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
