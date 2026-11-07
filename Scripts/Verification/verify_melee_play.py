"""Client acceptance for Attack (Left Mouse / RT) with bare hands, on the coastal map.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the swing
animations from Scripts/Setup/configure_attack_animations.py. Run unattended with run_play_check.py.

Through its own Attack input (Left Mouse, pressed through the input system), the client:
  1. swings at empty air: the swing plays on its own screen and on the server's copy, and nobody is hurt,
  2. swings at the host standing in front of it: the host loses 10 Health (fists) and flinches,
  3. swings again at once: the swing is refused until a second has passed,
  4. swings after a second: the host loses another 10.
Each step waits for its result on the server and on the client's copy, with a timeout.
Writes Saved/MeleePlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'MeleePlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host_pc = next(c for c in pcs if c.has_authority())
server_world, client_world = worlds[pcs.index(host_pc)], worlds[pcs.index(client)]
host = host_pc.get_controlled_pawn()
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def copy_in(world, character):
    return next(p for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWCharacter) if player_id(p) == player_id(character))


attacker = copy_in(server_world, pawn)        # the client's survivor, on the server
host_seen = copy_in(client_world, host)       # the host's survivor, on the client
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}
BEACH = unreal.Vector(300, 600, 200)


def health(character):
    return character.get_survival_component().get_health()


def swinging(character):
    anim = character.get_editor_property('mesh').get_anim_instance()
    return anim is not None and anim.is_any_montage_playing()


def face(controller, character, yaw):
    rotation = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
    controller.set_control_rotation(rotation)
    if character.get_controller():
        character.get_controller().set_control_rotation(rotation)


def setup():
    # The client stands on the beach with the host 1.2 m to its east; both settle before swinging.
    for p, at in ((attacker, BEACH), (pawn, BEACH), (host, BEACH + unreal.Vector(120, 0, 0))):
        assert p.teleport(at, unreal.Rotator())
    state['memo'].update(t=time.monotonic())


def settled():
    if time.monotonic() - state['memo']['t'] < 1.5:
        return False
    assert lib.get_play_worlds()
    assert attacker.can_attack(), 'the client survivor must be able to attack'
    state['memo']['full'] = health(host)
    return True


def turn(yaw):
    """Turn the client to face yaw and give the new aim a moment to reach the server, as a player's turn would."""
    def begin():
        face(client, attacker, yaw)
        state['memo']['turned'] = time.monotonic()
    return begin


def turned():
    return time.monotonic() - state['memo']['turned'] > 0.5


def swing():
    def begin():
        state['memo'].update(before=health(host), t=time.monotonic(), saw_server=False, saw_client=False)
        # Through the input system, as a player presses it.
        assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')
    return begin


def watch_swings():
    m = state['memo']
    m['saw_server'] = m['saw_server'] or swinging(attacker)
    m['saw_client'] = m['saw_client'] or swinging(pawn)


def missed():
    watch_swings()
    m = state['memo']
    if time.monotonic() - m['t'] < 1.2:
        return False
    assert m['saw_client'], 'the swing must play at once on the client'
    assert m['saw_server'], 'the swing must play on the server copy'
    assert health(host) == m['before'], f'nobody in reach, yet the host went from {m["before"]} to {health(host)}'
    return True


def struck():
    watch_swings()
    m = state['memo']
    if health(host) > m['before'] - 10 or health(host_seen) > m['before'] - 10:
        return False
    assert health(host) == m['before'] - 10, f'one fist blow is 10, the host went from {m["before"]} to {health(host)}'
    m['flinch'] = swinging(host_seen) or swinging(host)
    return True


def refused():
    m = state['memo']
    if time.monotonic() - m['t'] < 0.6:
        return False
    assert health(host) == m['before'], f'a swing within a second must be refused; the host went to {health(host)}'
    return True


STEPS = [
    ('Client and host stand a pace apart on the beach', setup, settled, 5),
    ('', turn(180.0), turned, 2),
    ('Client swings at empty air: the swing shows on both machines and hurts nobody', swing(), missed, 4),
    ('', turn(0.0), turned, 2),
    ('Client swings at the host in front of it: the host loses 10 Health on server and client', swing(), struck, 4),
    ('A second swing at once is refused', swing(), refused, 3),
    ('', lambda: None, lambda: time.monotonic() - state['memo']['t'] > 1.1, 3),
    ('After a second, another swing lands for 10 more', swing(), struck, 4),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    m = state['memo']
    RESULT.write_text(json.dumps({
        'success': error is None, 'checks': [c for c in checks if c], 'error': error,
        'host_health': {'start': m.get('full'), 'end': health(host), 'client_sees': health(host_seen)},
        'flinch_seen': m.get('flinch'),
    }, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Melee success={error is None} error={error}')


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
