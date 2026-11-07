"""Client acceptance for the neutral elephant (owner, November 1: elephants never attack unprovoked; struck, they defend
themselves instead of fleeing). Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one
client (EW_PLAY_PLAYERS=2) with the starter kit (EW_PLAY_STARTER_KIT=1), after Scripts/Setup/set_animal_temperaments.py.
Run unattended with run_play_check.py. Everything the client does goes through its own input.

  1. The client stands 6 m from an elephant for 6 s: it never goes for them and they lose no health.
  2. The client strikes it: it turns on them (the client is its quarry, it is chasing, not fleeing).
  3. It strikes back: the survivor loses health on server and client.
  4. The survivor walks 35 m off: past its give-up range it calms down and wanders again.
Writes Saved/ElephantPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ElephantPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
elephant = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWAnimal)
                if str(a.get_editor_property('definition').get_editor_property('display_name')) == 'Elephant')
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'follow': None, 'swing_at': 0.0}


def health(who):
    return who.get_survival_component().get_health()


def action():
    return str(elephant.get_action()).upper()


def ground(at, above=300):
    hit = unreal.SystemLibrary.line_trace_single_for_objects(
        server_world, unreal.Vector(at.x, at.y, at.z + above), unreal.Vector(at.x, at.y, at.z - 1500),
        [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], False, [], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else None


def place_beside(distance):
    """Stand `distance` cm off the elephant's side, facing it."""
    at = elephant.get_actor_location()
    side = elephant.get_actor_right_vector()
    spot = unreal.Vector(at.x + side.x * distance, at.y + side.y * distance, at.z)
    g = ground(spot)
    spot.z = (g if g is not None else at.z) + 100
    owner.set_actor_location(spot, False, True)
    eye = owner.get_actor_location() + unreal.Vector(0, 0, owner.get_editor_property('base_eye_height'))
    client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, at))


def swing():
    if time.monotonic() >= state['swing_at']:
        state['swing_at'] = time.monotonic() + 1.0
        assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def stand_near():
    place_beside(600)
    owner.get_survival_component().restore_health(1000)
    state['memo'].update(t=time.monotonic(), health0=health(owner))


def left_alone():
    assert elephant.get_quarry() is None, 'the elephant went for a survivor who had not struck it'
    assert 'CHASE' not in action(), f'the elephant charged unprovoked ({action()})'
    if time.monotonic() - state['memo']['t'] < 6.0:
        return False
    assert health(owner) >= state['memo']['health0'], 'the survivor lost health beside an unprovoked elephant'
    return True


def strike():
    state['follow'] = 220
    state['memo'].update(elephant_health0=elephant.get_health(), t=time.monotonic())


def turned_on():
    if state['follow']:
        place_beside(state['follow'])
    if elephant.get_health() >= state['memo']['elephant_health0']:
        swing()
        return False
    assert 'FLEE' not in action(), 'the struck elephant fled'
    if elephant.get_quarry() != owner:
        return False
    state['memo'].update(turned_after=round(time.monotonic() - state['memo']['t'], 2), struck_to=round(elephant.get_health()))
    return True


def wait_for_blow():
    # Stand still 3 m in front of its head and let it come: following its side would keep it turning, never facing.
    state['follow'] = None
    at, ahead = elephant.get_actor_location(), elephant.get_actor_forward_vector()
    spot = unreal.Vector(at.x + ahead.x * 500, at.y + ahead.y * 500, at.z)
    g = ground(spot)
    spot.z = (g if g is not None else at.z) + 100
    owner.set_actor_location(spot, False, True)
    state['memo'].update(health_before=health(owner))


def struck_back():
    if elephant.get_quarry() is None and 'why_lost' not in state['memo']:
        state['memo']['why_lost'] = json.dumps({
            'survivor_in_no_hostiles_zone': bool(unreal.EWSafeZone.keeps_hostiles_out(server_world, owner.get_actor_location())),
            'elephant_in_no_hostiles_zone': bool(unreal.EWSafeZone.keeps_hostiles_out(server_world, elephant.get_actor_location())),
            'swimming': bool(owner.get_movement_component().is_swimming()), 'survivor_health': health(owner),
            'distance_cm': round((owner.get_actor_location() - elephant.get_actor_location()).length()),
            'defend_seconds_def': elephant.get_editor_property('definition').get_editor_property('defend_seconds'),
            'elephant_at': str(elephant.get_actor_location())})
    if health(owner) >= state['memo']['health_before'] or health(pawn) >= state['memo']['health_before']:
        return False
    state['memo'].update(survivor_health_after_blow=round(health(owner)), client_health_after_blow=round(health(pawn)))
    owner.get_survival_component().restore_health(1000)
    return True


def walk_off():
    state['follow'] = None
    place_beside(3600)
    owner.get_survival_component().restore_health(1000)
    state['memo'].update(t=time.monotonic())


def calmed():
    if elephant.get_quarry() is not None:
        return False
    state['memo'].update(calmed_after=round(time.monotonic() - state['memo']['t'], 2), action_after=action())
    return True


STEPS = [
    ('The client stands 6 m from an elephant for 6 s: it never goes for them and they lose no health', stand_near, left_alone, 12),
    ('The client strikes it: it turns on them instead of fleeing', strike, turned_on, 20),
    ('It strikes back: the survivor loses health on server and client', wait_for_blow, struck_back, 20),
    ('The survivor is 36 m off: the elephant calms down', walk_off, calmed, 10),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k != 't'}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Elephant success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; quarry {elephant.get_quarry()}, action {action()}, '
                               f'survivor health {health(owner):.0f}, elephant health {elephant.get_health():.0f}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
