"""Play: how the cave spider looks and walks (owner, October 29: hair, legs on the ground, a real crawl). One player.
A spider is brought to open ground near the survivor: close-up shots from the side and the front while it stands, then a run of shots
while it crawls toward the survivor (its legs step in two groups). Saves Saved/Screenshots/SpiderLook/*.png and
Saved/SpiderLookPlayResult.json (the spider moved and the legs' pose changed between frames is judged by looking at the shots)."""
import json
import math
import time
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
report = {'checks': []}
state = {'t0': time.monotonic() + 12, 'phase': 0, 'handle': None, 'n': 0}


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, 'Shot showui filename="' + str(saved / 'Screenshots' / 'SpiderLook' / f'{name}.png') + '"')


def look(target, up=60):
    cam = unreal.GameplayStatics.get_player_camera_manager(world, 0).get_camera_location()
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, unreal.Vector(target.x, target.y, target.z + up)))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    unreal.SystemLibrary.execute_console_command(world, 'slomo 1')
    report.update(success=error is None, error=error)
    (saved / 'SpiderLookPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SpiderLook success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['t0']:
        return
    try:
        p = state['phase']
        if p == 0:
            spiders = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal)
                       if 'Spider' in str(a.get_editor_property('definition').get_editor_property('display_name'))]
            check('a spider exists', spiders)
            spider = spiders[0]
            for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal):
                if a != spider:
                    a.destroy_actor()
            # the cave mouth in daylight, as in verify_spiders_play (its pictures show the whole spider); held still for the standing shots, then let loose to chase the survivor (the crawl)
            cave = T.CAVES['Starter']
            state['cave'] = cave
            state['spider'] = spider
            spider.set_actor_tick_enabled(False)
            mx, my = cave.world(-650, 0.0)
            spider.set_actor_location_and_rotation(unreal.Vector(mx, my, cave.floor + 90), unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(cave.heading) + 90), False, True)
            ux, uy = cave.world(-1450, 0.0)
            pawn.teleport(unreal.Vector(ux, uy, cave.floor + 330), unreal.Rotator())
            state.update(phase=2, at=now() + 1.2)
        elif p == 2:
            if now() < state['at']:
                return
            look(state['spider'].get_actor_location(), 70)
            state.update(phase=3, at=now() + .8)
        elif p == 3:
            if now() < state['at']:
                return
            shot('Standing_a')
            h = state['cave'].heading
            loc = state['spider'].get_actor_location()
            pawn.teleport(unreal.Vector(loc.x + (-math.sin(h)) * 520, loc.y + math.cos(h) * 520, loc.z + 330), unreal.Rotator())
            state.update(phase=4, at=now() + 1.0)
        elif p == 4:
            if now() < state['at']:
                return
            look(state['spider'].get_actor_location(), 70)
            state.update(phase=5, at=now() + .8)
        elif p == 5:
            if now() < state['at']:
                return
            shot('Standing_b')
            state['spider'].set_actor_tick_enabled(True)      # let it wander: the crawl
            state.update(phase=6, at=now() + .5, start=state['spider'].get_actor_location())
            unreal.SystemLibrary.execute_console_command(world, 'slomo 0.3')
        elif p == 6:
            if now() < state['at']:
                return
            look(state['spider'].get_actor_location(), 60)
            shot(f'Crawl_{state["n"]}')
            state['n'] += 1
            state['at'] = now() + .35
            if state['n'] >= 6:
                moved = (state['spider'].get_actor_location() - state['start']).length()
                report['moved'] = moved
                finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
