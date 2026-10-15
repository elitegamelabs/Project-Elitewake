"""Client acceptance for leaks and bailing (M2: holes below the waterline let water in; bailing). Needs Play in
/Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client. Run unattended with run_play_check.py.

The sloop is holed directly (server, Play only: AEWShip::TakeRoundShot, as a cannon ball does), so the check can
place holes above and below the waterline exactly.
  1. The moored sloop starts dry with no leaks, and it has a bailing bucket on deck.
  2. A hole below the waterline leaks: water rises at 6 kg a second (LeakPerHole) on server and client.
  3. A hole above the waterline does not leak.
  4. With many holes below the waterline she fills: the water weighs on her like cargo, so she settles lower and
     her load slows her (a lower speed factor), on the client too.
  5. The client's survivor, aboard, is offered "Bail water" at the bucket and holds Interact there: each stroke
     throws 25 kg over the side.
Writes Saved/LeaksPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'LeaksPlayResult.json')
LEAK, STROKE = 6.0, 25.0         # AEWShip::LeakPerHole, BailPerStroke
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def ship_named(world, ship_id):
    return next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
                if str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id)


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
ship = ship_named(server_world, 'Sloop')
peer = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if s.get_name() == ship.get_name())
definition = ship.get_editor_property('definition')
extent = definition.get_editor_property('hull_extent')
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None}


def hole(local_z, along=0.0):
    """Hole the starboard side at a height in the ship's space (0 = the hull box's middle)."""
    t = ship.get_actor_transform()
    where = t.transform_location(unreal.Vector(along, extent.y, local_z))
    ship.take_round_shot(where, ship.get_actor_right_vector(), None)


def waterline():
    return ship.get_editor_property('surface_z') - ship.get_actor_location().z


def dry():
    assert ship.get_water_aboard() == 0 and peer.get_water_aboard() == 0, 'she starts with water in her'
    assert ship.get_leak_count() == 0, 'she starts leaking'
    assert ship.get_bucket_world().z > ship.get_editor_property('surface_z'), 'no bucket on deck'
    state['memo'].update(waterline_local=round(waterline()), capacity=round(ship.get_weight_capacity()))
    return True


def below():
    hole(waterline() - 40)
    state['memo'].update(t=time.monotonic(), w0=ship.get_water_aboard())


def leaking():
    m = state['memo']
    if time.monotonic() - m['t'] < 5.0:
        return False
    assert ship.get_leak_count() == 1, f'{ship.get_leak_count()} leaks'
    rate = (ship.get_water_aboard() - m['w0']) / (time.monotonic() - m['t'])
    assert abs(rate - LEAK) < LEAK * .25, f'water rises {rate:.1f} kg/s'
    assert abs(peer.get_water_aboard() - ship.get_water_aboard()) < 25, (peer.get_water_aboard(), ship.get_water_aboard())
    m['leak_kg_per_s'] = round(rate, 2)
    return True


def above():
    hole(extent.z - 20, along=-100)
    state['memo']['t'] = time.monotonic()


def not_leaking():
    if time.monotonic() - state['memo']['t'] < 1.0:
        return False
    assert ship.get_hole_count() == 2 and ship.get_leak_count() == 1, (ship.get_hole_count(), ship.get_leak_count())
    return True


def many():
    for k in range(9):
        hole(waterline() - 30, along=-300 + 70 * k)
    state['memo'].update(t=time.monotonic(), factor0=ship.get_load_speed_factor())


def filled():
    if ship.get_water_aboard() < .7 * ship.get_weight_capacity():
        return False
    settle = ship.get_settle()
    factor = peer.get_load_speed_factor()
    assert settle > 25, f'she settles only {settle:.0f} cm'
    assert factor < state['memo']['factor0'] - .05, f'speed factor {factor:.2f} (was {state["memo"]["factor0"]:.2f})'
    assert peer.get_water_aboard() > .6 * ship.get_weight_capacity(), 'the client does not see her fill'
    state['memo'].update(settle_cm=round(settle), speed_factor=round(factor, 2), fill_s=round(time.monotonic() - state['memo']['t'], 1))
    return True


def board():
    # Patch the holes for the bailing step so the water does not rise faster than one survivor bails.
    bucket = ship.get_bucket_world()
    back = ship.get_actor_forward_vector()
    spot = unreal.Vector(bucket.x - back.x * 90, bucket.y - back.y * 90, bucket.z + 110)
    for p in (owner, pawn):
        assert p.teleport(spot, ship.get_actor_rotation()), 'no room on deck by the bucket'
    state['aim'] = lambda: ship.get_bucket_world() + unreal.Vector(0, 0, 20)
    state['memo'].update(t=time.monotonic(), strokes=0, holding=False)


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def bailed():
    """Three strokes: each an Interact held at the bucket until its stroke completes (as a held key does)."""
    m = state['memo']
    keep_aim()
    now = time.monotonic()
    if now - m['t'] < 1.0:
        return False
    if 'w_before' not in m:
        assert ship.is_aboard(owner), 'the survivor is not aboard'
        assert 'Bail water' in str(ship.get_interaction_prompt(owner)), f'the bucket offers "{ship.get_interaction_prompt(owner)}"'
        m['w_before'], m['leaks'], m['bail_t'], m['next'] = ship.get_water_aboard(), ship.get_leak_count(), now, now
    if m['strokes'] < 3:
        if now >= m['next']:
            assert lib.send_verification_interaction_request(client, peer)
            m['strokes'] += 1
            m['next'] = now + 1.0 + .35
        return False
    if now < m['next']:
        return False
    let_in = m['leaks'] * LEAK * (now - m['bail_t'])
    thrown = m['w_before'] + let_in - ship.get_water_aboard()
    assert abs(thrown - 3 * STROKE) < 12, f'{thrown:.0f} kg bailed by three strokes'
    m['bailed_kg'] = round(thrown)
    return True


STEPS = [
    ('The sloop starts dry with no leaks, a bailing bucket on deck', lambda: None, dry, 4),
    ('A hole below the waterline lets water in at 6 kg/s, on server and client', below, leaking, 10),
    ('A hole above the waterline does not leak', above, not_leaking, 4),
    ('Holed nine more times below the waterline she fills, settles and slows (client too)', many, filled, 40),
    ('Aboard, holding Interact at the bucket throws 25 kg over the side a stroke, three strokes', board, bailed, 20),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    lib.send_verification_gameplay_key_state(client, 'E', False)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t', 'w0', 'bail_t', 'end_t', 'w_before', 'factor0', 'holding', 'strokes', 'leaks', 'next')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Leaks success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; water {ship.get_water_aboard():.0f} kg, leaks {ship.get_leak_count()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
