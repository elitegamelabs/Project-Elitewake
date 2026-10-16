"""Client acceptance for the caves' cobwebs (owner, October 15 night: webs you can walk through that fall apart, only
for show). Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after
build_caves.py and build_cave_webs.py. Run unattended with run_play_check.py.
  1. Both machines hang the webs DA_CaveWebs lists, where it lists them, all whole.
  2. Before the starter island's cave, the client looks in at the first web across the passage (screenshot).
  3. Walking in (W held, steering along the passage) tears both passage webs on the client and on the server; their
     strands fall (screenshot) and are gone a few seconds later.
  4. In the chamber the corner webs, out of reach, are still whole (screenshot), and no other cave's web is torn.
Screenshots in Saved/Screenshots/CaveWebs/ (a person still has to look at them). Writes Saved/CaveWebsPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'CaveWebsPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'CaveWebs')
SHOTS.mkdir(parents=True, exist_ok=True)
listed = unreal.load_asset('/Game/Elitewake/World/Caves/Webs/DA_CaveWebs').get_editor_property('webs')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()


def player_id(p):
    state_ = p.get_editor_property('PlayerState')
    return json.loads(unreal.ToolsetLibrary.get_object_properties(state_, ['PlayerId']))['PlayerId'] if state_ else None


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter)
             if player_id(p) is not None and player_id(p) == player_id(pawn))
cave = T.CAVES['Starter']
checks = []
measured = {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def webs(world):
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWCobweb))


def in_starter(web, part):
    p = web.get_actor_location()
    u, v = cave.local(p.x, p.y)
    return (0 < u < cave.length) if part == 'passage' else (u >= cave.length and cave.inside(p.x, p.y, 200))


def shot(name):
    path = SHOTS / f'{name}.png'
    unreal.SystemLibrary.execute_console_command(client_world, f'Shot showui filename="{path}"')
    measured.setdefault('screenshots', []).append(str(path))


def hung():
    for world, who in ((server_world, 'server'), (client_world, 'client')):
        here = webs(world)
        assert len(here) == len(listed), f'the {who} hangs {len(here)} webs; DA_CaveWebs lists {len(listed)}'
        assert not any(w.is_torn() for w in here), f'a web is torn on the {who} before anyone came'
        for t in listed:
            at = t.translation
            assert min((w.get_actor_location() - at).length() for w in here) < 5, f'no web on the {who} at {at}'
    measured['webs'] = len(listed)
    measured['starter_passage_webs'] = sum(in_starter(w, 'passage') for w in webs(server_world))
    assert measured['starter_passage_webs'] == 2, measured['starter_passage_webs']
    return True


def look_in():
    x, y = cave.world(80, cave.centre_v(80))
    yaw = math.degrees(cave.heading)
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(x, y, cave.floor + 120), unreal.Rotator(0, 0, yaw))
    for c in (client, owner.get_controller()):
        c.set_control_rotation(unreal.Rotator(0, 0, yaw))
    state['memo'].update(t=time.monotonic(), shot=False)


def looked():
    m = state['memo']
    if time.monotonic() - m['t'] < 3.0:
        return False
    if not m['shot']:
        shot('01_web_across_the_passage')
        m.update(shot=True, t=time.monotonic())
        return False
    return time.monotonic() - m['t'] > 1.0


def begin_walk():
    state['memo'].update(t=time.monotonic(), walking=False, path=cave.path(), first_torn=None, falling=0, falling_shot=False)


def walked():
    m = state['memo']
    if not m['walking']:
        assert lib.send_verification_gameplay_key_state(client, 'W', True)
        m['walking'] = True
    p = pawn.get_actor_location()
    u, _ = cave.local(p.x, p.y)
    ahead = next(((x, y) for x, y in m['path'] if cave.local(x, y)[0] > u + 250), m['path'][-1])
    client.set_control_rotation(unreal.Rotator(0, 0, math.degrees(math.atan2(ahead[1] - p.y, ahead[0] - p.x))))
    mine = [w for w in webs(client_world) if in_starter(w, 'passage')]
    torn = [w for w in mine if w.is_torn()]
    m['falling'] = max(m['falling'], max((w.get_falling_strands() for w in mine), default=0))
    if torn and m['first_torn'] is None:
        m['first_torn'] = time.monotonic()
    if m['first_torn'] and not m['falling_shot'] and time.monotonic() - m['first_torn'] > .5:
        client.set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=client.get_control_rotation().yaw))
        shot('02_web_torn_strands_falling')
        m['falling_shot'] = True
    cx, cy = cave.world(cave.chamber_u, 0)
    if math.hypot(p.x - cx, p.y - cy) > 300:
        return False
    lib.send_verification_gameplay_key_state(client, 'W', False)
    assert len(torn) == 2, f'{len(torn)} of the passage webs tore on the client'
    on_server = [w for w in webs(server_world) if in_starter(w, 'passage') and w.is_torn()]
    assert len(on_server) == 2, f'{len(on_server)} of the passage webs tore on the server'
    assert m['falling'] >= 5, f'only {m["falling"]} strands fell'
    measured['strands_falling'] = m['falling']
    return True


def begin_chamber():
    state['memo'].update(t=time.monotonic(), shot=False)


def chamber():
    m = state['memo']
    corner = [w for w in webs(client_world) if in_starter(w, 'chamber')]
    assert len(corner) == 3, f'{len(corner)} corner webs in the chamber'
    if not m['shot']:
        target = corner[1].get_actor_location()
        eye = pawn.get_actor_location() + unreal.Vector(0, 0, 60)
        client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, target))
        if time.monotonic() - m['t'] < 1.5:
            return False
        shot('03_chamber_corner_webs')
        m['shot'] = True
        return False
    if time.monotonic() - m['t'] < 3.5:   # the torn webs' strands have had time to fall away
        return False
    assert not any(w.is_torn() for w in corner), 'a corner web out of reach was torn'
    passage = [w for w in webs(client_world) if in_starter(w, 'passage')]
    assert all(w.get_falling_strands() == 0 for w in passage), 'torn strands are still hanging about'
    others = [w for w in webs(client_world) + webs(server_world) if not in_starter(w, 'passage') and w.is_torn()]
    assert not others, f'{len(others)} webs elsewhere tore'
    return True


STEPS = [
    ('Both machines hang every web DA_CaveWebs lists, where it lists them, all whole', lambda: None, hung, 6),
    ("Before the starter island's cave the client looks in at the web across the passage", look_in, looked, 8),
    ('Walking in tears both passage webs on client and server, their strands falling', begin_walk, walked, 40),
    ('In the chamber the corner webs are whole, the strands gone, and no other web torn', begin_chamber, chamber, 12),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    lib.send_verification_gameplay_key_state(client, 'W', False)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK CaveWebs success={error is None} error={error}')


def tick(delta):
    description, begin, done, timeout = STEPS[state['index']]
    try:
        if not state['begun']:
            begin()
            state.update(begun=True, deadline=time.monotonic() + timeout)
            return
        if done():
            checks.append(description)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
        elif time.monotonic() > state['deadline']:
            raise TimeoutError(f'not done within {timeout} s')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
