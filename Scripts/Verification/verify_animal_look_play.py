"""Screenshots of the animals up close (single-player Play session), for judging their models by eye.
Takes one picture of each kind listed in KINDS from the side, a few metres off, into Saved/Screenshots/Animals.
Writes Saved/AnimalLookPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

KINDS = ['Lion', 'Black Bear', 'Giant Crocodile', 'Elephant']
lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
animals = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal))
shots = saved / 'Screenshots' / 'Animals'
shots.mkdir(parents=True, exist_ok=True)
state = {'step': 0, 'at': time.monotonic() + 2, 'handle': None}
checks = []


def kind(a):
    return str(a.get_editor_property('definition').get_editor_property('display_name'))


def go(display):
    a = next(x for x in animals if kind(x) == display)
    at = a.get_actor_location()
    side = a.get_actor_right_vector()
    far = {'Elephant': 1000, 'Giant Crocodile': 900}.get(display, 520)
    spot = unreal.Vector(at.x + side.x * far, at.y + side.y * far, at.z + 60)
    pawn.set_actor_location(spot, False, True)
    eye = pawn.get_actor_location() + unreal.Vector(0, 0, pawn.get_editor_property('base_eye_height'))
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, at))


def shot(display):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / (display.replace(" ", "") + ".png")}"')
    checks.append(display)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    (saved / 'AnimalLookPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))
    unreal.log(f'EWPLAYCHECK AnimalLook success={error is None} error={error}')


STEPS = []
for k in KINDS:
    STEPS += [(lambda k=k: go(k), 2.5), (lambda k=k: shot(k), 1.5)]
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
