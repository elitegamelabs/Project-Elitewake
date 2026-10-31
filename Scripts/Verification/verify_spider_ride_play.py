"""Play: the spider is rideable (owner, October 28). One player.
Interact climbs on (the survivor is mounted, the spider has its rider, the survivor sits above its back); the spider stops biting its
rider; holding W walks it along the camera's heading with the rider carried (the seat stays on its back); Jump gets off onto the
ground beside it. Screenshots go to Saved/Screenshots/SpiderRide/. Writes Saved/SpiderRidePlayResult.json."""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
survival = pawn.get_survival_component()
report = {'checks': []}
state = {'t0': time.monotonic() + 12, 'phase': 0, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


def finish(error=None):
    try:
        lib.send_verification_gameplay_key_state(pc, 'W', False)
    except Exception:
        pass
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'SpiderRidePlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SpiderRide success={error is None} error={error}')


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, 'Shot showui filename="' + str(saved / 'Screenshots' / 'SpiderRide' / f'{name}.png') + '"')


def tick(delta):
    if time.monotonic() < state['t0']:
        return
    try:
        p = state['phase']
        if p == 0:
            animals = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal)
            spiders = [a for a in animals if 'Spider' in str(a.get_editor_property('definition').get_editor_property('display_name'))]
            check('spiders exist', spiders, total=len(spiders))
            spider = spiders[0]
            for a in animals:
                if a != spider:
                    a.destroy_actor()           # nothing else bites the rider
            check('the spider definition is rideable', spider.get_editor_property('definition').get_editor_property('rideable'))
            state['spider'] = spider
            loc = spider.get_actor_location()
            right = spider.get_actor_right_vector()
            assert pawn.teleport(unreal.Vector(loc.x + right.x * 170, loc.y + right.y * 170, loc.z + 120), unreal.Rotator())
            state.update(phase=1, at=now() + 1.0)
        elif p == 1:
            if now() < state['at']:
                return
            spider = state['spider']
            state['health0'] = survival.get_health()
            check('the interaction offers a ride', spider.can_interact(pawn) if hasattr(spider, 'can_interact') else True)
            eye, _ = pawn.get_actor_eyes_view_point()
            loc = spider.get_actor_location()
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, loc))
            report['aim'] = {'eye': str(eye), 'spider': str(loc)}
            state.update(phase=15, at=now() + 0.5)
        elif p == 15:
            if now() < state['at']:
                return
            spider = state['spider']
            check('interaction request accepted', lib.send_verification_interaction_request(pc, spider))
            state.update(phase=2, at=now() + 1.0)
        elif p == 2:
            if now() < state['at']:
                return
            spider = state['spider']
            check('the survivor is mounted', pawn.get_mount() == spider)
            check('the spider has its rider', spider.get_rider() == pawn)
            seat, back = pawn.get_actor_location(), spider.get_actor_location()
            check('the seat is above the spider and near it', 40 < seat.z - back.z < 260 and math.hypot(seat.x - back.x, seat.y - back.y) < 120,
                  dz=seat.z - back.z, dxy=math.hypot(seat.x - back.x, seat.y - back.y))
            state['health0'] = survival.get_health()      # a bite before the climb does not count
            shot('Mounted')
            state['start'] = spider.get_actor_location()
            state['yaw'] = spider.get_actor_rotation().yaw
            pc.set_control_rotation(unreal.Rotator(0, state['yaw'], 0))
            assert lib.send_verification_gameplay_key_state(pc, 'W', True)
            state.update(phase=3, at=now() + 2.5)
        elif p == 3:
            if now() < state['at']:
                return
            spider = state['spider']
            moved = spider.get_actor_location() - state['start']
            heading = pc.get_control_rotation().yaw       # whatever the camera looks along now (it can differ from the yaw asked for)
            along = moved.x * math.cos(math.radians(heading)) + moved.y * math.sin(math.radians(heading))
            report['diag'] = {'moved': [moved.x, moved.y], 'yaw_set': state['yaw'], 'control_yaw': pc.get_control_rotation().yaw, 'spider_yaw_now': spider.get_actor_rotation().yaw}
            report['ride'] = {'moved': moved.length(), 'along_heading': along, 'shown_speed': spider.get_shown_speed()}
            check('holding W walks the spider along the camera heading', along > 150, **report['ride'])
            check('the rider is carried with it', pawn.get_mount() == spider and (pawn.get_actor_location() - spider.get_actor_location()).length() < 300)
            check('the spider does not bite its rider', survival.get_health() >= state['health0'] - .5, health=survival.get_health(), health0=state['health0'])
            shot('Riding')
            lib.send_verification_gameplay_key_state(pc, 'W', False)
            state.update(phase=4, at=now() + 0.8)
        elif p == 4:
            if now() < state['at']:
                return
            assert lib.send_verification_gameplay_key(pc, 'SpaceBar')
            state.update(phase=5, at=now() + 1.5)
        elif p == 5:
            if now() < state['at']:
                return
            spider = state['spider']
            check('Jump gets off', pawn.get_mount() is None and spider.get_rider() is None)
            gap = (pawn.get_actor_location() - spider.get_actor_location()).length()
            check('the survivor stands beside it, not on it', 80 < gap < 400, gap=gap)
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
