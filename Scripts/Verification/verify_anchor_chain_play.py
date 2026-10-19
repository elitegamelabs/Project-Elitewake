"""Client acceptance for the anchor's chain (owner, October 16: Design/Ships/ANCHOR_CHAIN_ANIMATION_AUDIO_2026-10-16.md).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the moored sloop.
Run unattended with run_play_check.py. The sloop starts at anchor; the server fits her out with full sail and turns
the wind to blow from astern. Then:
  1. her anchor lies on the bottom below her bow and her chain is drawn out on the client;
  2. with the wind in her sails she moves off at anchor, the chain paying out its slack;
  3. over the last of the slack the chain slows her smoothly (no instant stop), and she stops at its reach;
  4. the chain comes taut once: the catch counts on server and client, and the client hears the clank;
  5. she stays held there, sails still full.
Writes Saved/AnchorChainPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
snd = unreal.EWSoundLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'AnchorChainPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
host = next(c for c in pcs if c.has_authority()).get_controlled_pawn()
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop')
peer = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if a.get_name() == ship.get_name())
folder = '/Game/Elitewake/Items/Testing'
items = [unreal.load_asset(f'{folder}/{n}') for n in ('DA_TestShipHelm', 'DA_TestSailMedium', 'DA_TestSailSmall')]
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
measured = {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def rng():
    h = ship.get_hawse_world()
    b = ship.get_anchor_bed()
    return ((h.x - b.x) ** 2 + (h.y - b.y) ** 2) ** .5


def anchored_at_start():
    m = state['memo']
    if 't' not in m:
        m['t'] = time.monotonic()
    if time.monotonic() - m['t'] < 1.5:
        return False
    assert ship.is_anchored() and peer.is_anchored(), 'the moored sloop is not anchored'
    reach = ship.get_chain_reach()
    assert 999 <= reach <= 4001, f'chain reach {reach}'
    assert ship.get_anchor_bed().z < ship.get_actor_location().z - 100, 'the anchor is not on the bottom'
    assert peer.get_chain_link_count() > 5 and peer.get_chain_shown_out() > .99, (peer.get_chain_link_count(), peer.get_chain_shown_out())
    measured.update(reach_m=round(reach / 100, 1), depth_m=round((ship.get_actor_location().z - ship.get_anchor_bed().z) / 100, 1),
                    links=peer.get_chain_link_count(), start_range_m=round(rng() / 100, 1))
    return True


def set_sail():
    for item in items:
        assert item and host.get_inventory_component().add_item(item, 1) == 1
    assert lib.fit_out_ship_for_review(ship, host, 4) == 3
    # From astern: it blows toward her bow, filling her sails.
    unreal.EWWindSubsystem.get_for_world(server_world).set_wind_yaw(ship.get_actor_rotation().yaw)
    state['memo'].update(t=time.monotonic(), catches=ship.get_chain_catches(), heard=snd.get_play_count(client_world, 'S_AnchorCatch_v1'),
                         top=0.0, speeds=[])


def moving_off():
    m = state['memo']
    m['top'] = max(m['top'], ship.get_speed())
    return ship.get_speed() > 60.0 and ship.is_anchored()


def snubbed_up():
    m = state['memo']
    now = time.monotonic()
    m['speeds'].append((now, ship.get_speed(), rng()))
    m['top'] = max(m['top'], ship.get_speed())
    if not (ship.is_chain_taut() and ship.get_speed() < 1.0):
        return False
    reach = ship.get_chain_reach()
    assert rng() <= reach * 1.03, f'overran the chain: {rng():.0f} of {reach:.0f} cm'
    # Smooth, not instant: from the speed she had to a stop took a while, over the last of the slack.
    slowing = [t for t, s, r in m['speeds'] if r > reach * .8]
    took = now - slowing[0] if slowing else 0.0
    assert took > 0.5, f'stopped within {took:.2f} s of feeling the chain'
    assert ship.get_chain_catches() == m['catches'] + 1, f'catches {m["catches"]} -> {ship.get_chain_catches()}'
    measured.update(top_speed=round(m['top']), stop_range_m=round(rng() / 100, 1), slowed_over_s=round(took, 2))
    m['t'] = now
    return True


def client_saw_catch():
    m = state['memo']
    heard = snd.get_play_count(client_world, 'S_AnchorCatch_v1') - m['heard']
    if not (peer.get_chain_catches() == ship.get_chain_catches() and heard >= 1):
        return False
    measured.update(client_catches=peer.get_chain_catches(), client_heard=heard)
    return True


def held():
    m = state['memo']
    if time.monotonic() - m['t'] < 3.0:
        return False
    assert ship.get_speed() < 1.0 and rng() <= ship.get_chain_reach() * 1.03, (ship.get_speed(), rng())
    assert ship.get_chain_catches() == m['catches'] + 1, 'the chain snubbed her up more than once'
    measured.update(held_range_m=round(rng() / 100, 1), links_taut=peer.get_chain_link_count())
    # A picture of her riding to her chain: from abeam and forward of her bow, the host's view (the host hidden).
    hawse, bed = ship.get_hawse_world(), ship.get_anchor_bed()
    side = ship.get_actor_right_vector()
    eye = hawse + side * 1600 + ship.get_actor_forward_vector() * 900 + unreal.Vector(0, 0, 250)
    host.get_component_by_class(unreal.CharacterMovementComponent).set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    host.set_actor_location(eye, False, True)
    host.set_actor_hidden_in_game(True)
    pcs[worlds.index(server_world)].set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, (hawse + bed) * 0.5 + unreal.Vector(0, 0, 300)))
    if 'shot' not in m:
        m['shot'] = time.monotonic()
        return False
    if time.monotonic() - m['shot'] < 1.0:
        return False
    shots = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'AnchorChain')
    shots.mkdir(parents=True, exist_ok=True)
    unreal.SystemLibrary.execute_console_command(server_world, f'Shot filename="{shots / "sloop_riding_to_chain.png"}"')
    return True


STEPS = [
    ('The moored sloop lies at anchor, her chain drawn out below her bow on the client', lambda: None, anchored_at_start, 8),
    ('With the wind from astern and full sail she moves off at anchor', set_sail, moving_off, 15),
    ('Over the last of the slack the chain slows her smoothly and stops her at its reach', lambda: None, snubbed_up, 60),
    ('The catch shows on the client and it hears the clank', lambda: None, client_saw_catch, 5),
    ('She stays held there with her sails full', lambda: None, held, 9),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWPLAYCHECK AnchorChain success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; speed {ship.get_speed():.0f}, range {rng():.0f} of {ship.get_chain_reach():.0f}, '
                               f'taut {ship.is_chain_taut()}, catches {ship.get_chain_catches()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
