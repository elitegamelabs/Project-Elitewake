"""The integrated two-cannon fight (M2 goal: "a simple two-cannon fight before the deeper systems"). Needs Play in
/Game/Elitewake/Maps/Test/Lvl_ShipsTest (the sloop and the schooner) as a listen server plus one client, after build_cannon.py. Run unattended
with run_play_check.py.

Two survivors, two ships, two cannons, everything through play (only the cannons, shot and some cargo are granted, and
the schooner is brought alongside, server, Play only):
  1. The client fits a cannon at the sloop's starboard hardpoint and mans it; the host fits one at the schooner's
     port hardpoint and mans it; the schooner lies 40 m off the sloop's starboard side.
  2. They exchange fire: the client's shot holes the schooner and the host's holes the sloop; both machines agree on
     both hulls' health and holes.
  3. The host keeps firing until the sloop's hull is destroyed: she sinks, her gunner is let go, and her hold floats
     up in wreck crates; she is gone, on both machines; the schooner, holed, stays afloat.
Writes Saved/CannonFightPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'CannonFightPlayResult.json')
# The sloop's cannon stands behind a two-cannon railing at her railing hardpoint (owner, October 17: no hull gunports).
SLOOP_GUN, SLOOP_RAILING, SCHOONER_GUN = 'StarboardCannon1', 'StarboardRailing', 'PortCannon1'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host_pc = next(c for c in pcs if c.has_authority())
server_world = host_pc.get_world()
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()
host = host_pc.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def ship_named(world, ship_id):
    return next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
                if str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id)


def copy_in(world, actor):
    return next((s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip) if s.get_name() == actor.get_name()), None)


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
sloop, schooner = ship_named(server_world, 'Sloop'), ship_named(server_world, 'Schooner')
sloop_name = sloop.get_name()
sloop_peer, schooner_peer = copy_in(client_world, sloop), copy_in(client_world, schooner)
cannon, shot = (unreal.load_asset(f'/Game/Elitewake/Items/Testing/{n}') for n in ('DA_TestCannon', 'DA_TestRoundShot'))
assert cannon and shot, 'Run Scripts/Setup/build_cannon.py first.'
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aims': {}}


def look(controller, who, target):
    eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
    controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, target))


def keep_aim():
    for (controller, who), target in list(state['aims'].items()):
        look(controller, who, target())


def stand_at(ship, mount, people):
    """On deck, inboard of a cannon mount, looking at it."""
    at = ship.get_mount_world_transform(mount).translation
    local = ship.get_actor_transform().inverse_transform_location(at)
    # On the floor the gun stands on (a schooner's guns are on her lower deck), CannonMountHeight below the mount,
    # inboard of it, wherever there is room (masts, stairs and hatches stand about).
    for dx, fy, dz in ((60, .5, 0), (60, .3, 0), (-60, .5, 0), (120, .4, 0), (-120, .4, 0), (0, .6, 0), (60, .5, 10), (-60, .3, 10)):
        spot = ship.get_actor_transform().transform_location(unreal.Vector(local.x + dx, local.y * fy, local.z - 40 + 98 + dz))
        if people[0].teleport(spot, ship.get_actor_rotation()):
            break
    else:
        raise AssertionError(f'no room on the {ship.get_name()} deck by {mount}')
    for p in people:
        assert p.teleport(spot, ship.get_actor_rotation()) or p is people[0], f'no room on the {ship.get_name()} deck'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()


def grant_and_place():
    for who, shots in ((owner, 6), (host, 14)):
        inv = who.get_inventory_component()
        assert inv.add_item(cannon, 1) == 1 and inv.add_item(shot, shots) == shots
    assert owner.get_inventory_component().add_item(unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestRailingTwoCannon'), 1) == 1
    for name, n in (('DA_TestStone', 20), ('DA_TestWood', 30), ('DA_TestFiber', 15)):
        sloop.get_cargo().add_item(unreal.load_asset(f'/Game/Elitewake/Items/Testing/{name}'), n)
    # The schooner parallel to the sloop, 40 m off her starboard side: her port side faces the sloop.
    right, at = sloop.get_actor_right_vector(), sloop.get_actor_location()
    schooner.set_actor_location_and_rotation(unreal.Vector(at.x + right.x * 4000, at.y + right.y * 4000, schooner.get_actor_location().z),
                                             sloop.get_actor_rotation(), False, True)
    state['memo']['t'] = time.monotonic()


def fit(ship, peer, mount, controller, who, people):
    """Stand by the mount, look at it and press Interact: `controller` is the player's own (local) controller."""
    def begin():
        stand_at(ship, mount, people)
        target = lambda: ship.get_mount_world_transform(mount).translation
        state['aims'] = {(controller, who): target}
        if who is owner:
            state['aims'] = {(client, pawn): target, (owner.get_controller(), owner): target}
        keep_aim()
        assert lib.send_verification_interaction_request(controller, peer), 'the interaction request was refused'
    return begin


def fit_railing():
    """Stand by the railing's first cannon place, look at the railing hardpoint and press Interact."""
    stand_at(sloop, SLOOP_GUN, (owner, pawn))
    target = lambda: sloop.get_mount_world_transform(SLOOP_RAILING).translation + unreal.Vector(0, 0, 40)
    state['aims'] = {(client, pawn): target, (owner.get_controller(), owner): target}
    keep_aim()
    assert not sloop.is_mount_open(SLOOP_GUN), 'a cannon place is open with no cannon railing fitted'
    assert lib.send_verification_interaction_request(client, sloop_peer), 'the interaction request was refused'
    state['memo']['railing_sent'] = time.monotonic()


def railing_fitted():
    """Fitted on both. A hold the server cancels (the aim slips off as the moored ship rolls) is held again, as a
    player would, every 1.5 s."""
    if sloop.is_mount_open(SLOOP_GUN) and sloop_peer.is_mount_open(SLOOP_GUN):
        return True
    if time.monotonic() - state['memo'].get('railing_sent', 0) > 1.5:
        assert lib.send_verification_interaction_request(client, sloop_peer), 'the interaction request was refused'
        state['memo']['railing_sent'] = time.monotonic()
    return False


def fitted(ship, peer, mount):
    return lambda: ship.get_fitting(mount) == cannon and peer.get_fitting(mount) == cannon


def manned(ship, mount, who):
    def done():
        if ship.get_cannon_gunner(mount) != who:
            return False
        state['aims'] = {}
        return True
    return done


def lay_guns():
    yaw = sloop.get_actor_rotation().yaw
    # The sloop's gun sits low too (her deck is 2.25 m up): a level shot can fall short at 34 m, so her gunner lays it up a little.
    client.set_control_rotation(unreal.Rotator(roll=0, pitch=2, yaw=yaw + 90))
    # The schooner's guns sit low, on her gun deck: a level shot falls about 2 m in 40 m and goes into the sea short
    # of the sloop, so her gunner lays it a few degrees up, as a gunner would.
    host_pc.set_control_rotation(unreal.Rotator(roll=0, pitch=3, yaw=yaw - 90))
    # Her gun stands behind a hull gunport, shut until its gunner opens it (owner, October 17): Up opens it.
    assert lib.send_verification_gameplay_key(host_pc, 'Up'), 'the Up key was not handled'
    state['memo'].update(t=time.monotonic(), sloop0=sloop.get_hull_health(), schooner0=schooner.get_hull_health())


def guns_ready():
    if time.monotonic() - state['memo']['t'] < 1.5:
        return False
    return (sloop.is_cannon_loaded(SLOOP_GUN) and schooner.is_cannon_loaded(SCHOONER_GUN)
            and schooner.get_gunport_opening(SCHOONER_GUN) >= .99 and schooner_peer.get_gunport_opening(SCHOONER_GUN) >= .99)


def exchange():
    m = state['memo']
    m['before'] = unreal.EWCannonBall.get_last_shot(server_world)
    assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')
    assert lib.send_verification_gameplay_key(host_pc, 'LeftMouseButton')
    m['t'] = time.monotonic()


def both_holed():
    m = state['memo']
    if time.monotonic() - m['t'] < 2.0:
        return False
    if not (sloop.get_hole_count() >= 1 and schooner.get_hole_count() >= 1):
        if time.monotonic() - m['t'] >= 5.0:
            shot = unreal.EWCannonBall.get_last_shot(server_world)
            struck = shot.get_struck() if shot else None
            raise AssertionError(f'holes: sloop {sloop.get_hole_count()}, schooner {schooner.get_hole_count()}; last shot landed {shot.has_landed() if shot else None} '
                                 f'on {struck.get_actor_label() if struck else "the sea"} at {shot.get_landed_at() if shot else None}, loaded sloop {sloop.is_cannon_loaded(SLOOP_GUN)} '
                                 f'schooner {schooner.is_cannon_loaded(SCHOONER_GUN)}')
        return False
    for ship, peer in ((sloop, sloop_peer), (schooner, schooner_peer)):
        assert peer.get_hull_health() == ship.get_hull_health() and peer.get_hole_count() == ship.get_hole_count(), ship.get_name()
    assert sloop.get_hull_health() < m['sloop0'] and schooner.get_hull_health() < m['schooner0']
    m.update(after_exchange=f'sloop {sloop.get_hull_health():.0f}, schooner {schooner.get_hull_health():.0f}')
    return True


def keep_firing():
    state['memo'].update(t=time.monotonic(), shots=1, next=0.0)


def sunk():
    m = state['memo']
    alive = copy_in(server_world, sloop) if any(s.get_name() == sloop_name for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)) else None
    if alive and not alive.is_sinking():
        now = time.monotonic()
        if schooner.is_cannon_loaded(SCHOONER_GUN) and now >= m['next']:
            assert m['shots'] < 16, f'16 shots and the sloop still floats at {alive.get_hull_health():.0f}'
            assert lib.send_verification_gameplay_key(host_pc, 'LeftMouseButton')
            m['shots'] += 1
            m['next'] = now + 1.0
        return False
    if alive and alive.is_sinking() and 'sank_after' not in m:
        m['sank_after'] = m['shots']
        assert alive.get_cannon_gunner(SLOOP_GUN) is None, 'the sinking sloop keeps her gunner'
        crates = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWWreckCrate)
        assert crates, 'no wreck crates'
        m['crates'] = len(crates)
    if alive:
        return False
    if copy_in(client_world, sloop):
        return False
    assert not schooner.is_sinking() and schooner.get_hull_health() > 0, 'the schooner sank too'
    assert unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWWreckCrate), 'the client sees no crates'
    m['fight_s'] = round(time.monotonic() - m['t'], 1)
    return True


STEPS = [
    ('Cannons, shot and cargo granted in Play only; the schooner lies 40 m off the sloop\'s starboard side', grant_and_place, lambda: True, 2),
    ('The client fits a two-cannon railing at the starboard railing hardpoint of the sloop', fit_railing, railing_fitted, 8),
    ('The client fits a cannon at the sloop\'s starboard hardpoint', fit(sloop, sloop_peer, SLOOP_GUN, client, owner, (owner, pawn)),
     fitted(sloop, sloop_peer, SLOOP_GUN), 6),
    ('...and mans it', fit(sloop, sloop_peer, SLOOP_GUN, client, owner, (owner, pawn)), manned(sloop, SLOOP_GUN, owner), 6),
    ('The host fits a cannon at the schooner\'s port hardpoint', fit(schooner, schooner, SCHOONER_GUN, host_pc, host, (host,)),
     fitted(schooner, schooner_peer, SCHOONER_GUN), 6),
    ('...and mans it', fit(schooner, schooner, SCHOONER_GUN, host_pc, host, (host,)), manned(schooner, SCHOONER_GUN, host), 6),
    ("Both guns laid at each other and loaded; the schooner's gunner opens her port", lay_guns, guns_ready, 12),
    ('They fire together: each ship is holed, and both machines agree on both hulls', exchange, both_holed, 8),
    ('The host keeps firing until the sloop\'s hull gives: she sinks, lets her gunner go, leaves wreck crates and is gone; the schooner floats',
     keep_firing, sunk, 160),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t', 'next', 'before')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK CannonFight success={error is None} error={error}')


def tick(delta):
    keep_aim()
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
            raise TimeoutError(f'not done within {timeout} s; sloop {sloop.get_hull_health() if sloop else None}, shots {state["memo"].get("shots")}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
