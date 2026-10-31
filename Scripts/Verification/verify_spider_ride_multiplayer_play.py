"""Riding a spider with a second player (listen server plus one client, EW_PLAY_PLAYERS=2). The client climbs on through the real
interaction request, steers with W (the client's own movement input, sent to the server), and gets off with Jump. Checks, on the
server and in the client's own world: the client is mounted and the spider has the client as rider; the spider walks along the
client's camera heading and the client's copy of it follows; the client's pawn sits on the client's copy of the spider; Jump gets
the client off (mount cleared on both). Writes Saved/SpiderRideMultiplayerPlayResult.json."""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 14, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def sw():
    return unreal.GameplayStatics.get_time_seconds(server_world)


def is_spider(a):
    return 'Spider' in str(a.get_editor_property('definition').get_editor_property('display_name'))


def spiders(w):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWAnimal) if a.get_editor_property('definition') and is_spider(a)]


def finish(error=None):
    try:
        lib.send_verification_gameplay_key_state(client, 'W', False)
    except Exception:
        pass
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'SpiderRideMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SpiderRideMultiplayer success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            owner = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            state['owner'] = owner
            server_spiders = spiders(server_world)
            check('spiders exist on the server and the client', server_spiders and spiders(client_world), server=len(server_spiders))
            spider = server_spiders[0]
            for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWAnimal):
                if a != spider:
                    a.destroy_actor()
            state['spider'] = spider
            loc, right = spider.get_actor_location(), spider.get_actor_right_vector()
            assert owner.teleport(unreal.Vector(loc.x + right.x * 170, loc.y + right.y * 170, loc.z + 120), unreal.Rotator())
            state['at'] = time.monotonic() + 3.0
            state['phase'] = 1
        elif p == 1:
            spider = state['spider']
            near = min(spiders(client_world), key=lambda a: (a.get_actor_location() - spider.get_actor_location()).length())
            state['client_spider'] = near
            pawn = client.get_controlled_pawn()
            eye, _ = pawn.get_actor_eyes_view_point()
            client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, near.get_actor_location()))
            state['at'] = time.monotonic() + 1.0
            state['phase'] = 2
        elif p == 2:
            check('the client asks to ride', lib.send_verification_interaction_request(client, state['client_spider']))
            state['at'] = time.monotonic() + 2.0
            state['phase'] = 3
        elif p == 3:
            owner, spider, mine = state['owner'], state['spider'], state['client_spider']
            pawn = client.get_controlled_pawn()
            check('server: the client survivor is mounted and is the rider', owner.get_mount() == spider and spider.get_rider() == owner)
            check('client: its own pawn is mounted on its copy of the spider', pawn.get_mount() == mine)
            gap = (pawn.get_actor_location() - mine.get_actor_location()).length()
            check('client: the pawn sits on the spider copy', gap < 300, gap=gap)
            state['start'] = spider.get_actor_location()
            assert lib.send_verification_gameplay_key_state(client, 'W', True)
            state['at'] = time.monotonic() + 3.0
            state['phase'] = 4
        elif p == 4:
            spider, mine = state['spider'], state['client_spider']
            heading = client.get_control_rotation().yaw
            moved = spider.get_actor_location() - state['start']
            along = moved.x * math.cos(math.radians(heading)) + moved.y * math.sin(math.radians(heading))
            report['ride'] = {'along': along, 'heading': heading}
            check('server: holding W on the client walks the spider along its camera', along > 150, along=along)
            seen = (mine.get_actor_location() - spider.get_actor_location()).length()
            check('client: its copy of the spider follows the server', seen < 400, gap=seen)
            check('client: the rider still sits on it', (client.get_controlled_pawn().get_actor_location() - mine.get_actor_location()).length() < 300)
            lib.send_verification_gameplay_key_state(client, 'W', False)
            state['at'] = time.monotonic() + 1.0
            state['phase'] = 5
        elif p == 5:
            check('the client presses Jump', lib.send_verification_gameplay_key(client, 'SpaceBar'))
            state['at'] = time.monotonic() + 2.0
            state['phase'] = 6
        elif p == 6:
            owner, spider = state['owner'], state['spider']
            check('server: the client got off', owner.get_mount() is None and spider.get_rider() is None)
            check('client: its pawn is no longer mounted', client.get_controlled_pawn().get_mount() is None)
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
