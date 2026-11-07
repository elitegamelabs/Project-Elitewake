"""Client acceptance for hull gunport covers (owner, October 17: each hull port has a sliding dark opaque glass cover,
The runner spawns any ship the map lacks (EW_PLAY_SHIPS=Brigantine,Schooner): the schooner and brigantine are parked off the map (November 7).
cannon carriage extension and retraction, individually controlled open and close, and a cannon cannot fire shut).
Needs Play in /Game/Elitewake/Maps/Test/Lvl_ShipsTest as a listen server plus one client, after the hull scripts.
Run unattended with run_play_check.py.

  1. The brigantine's 6 hull cannon places and the schooner's 12 are gunports, all shut on both machines, and each
     cover is drawn on the client in the hull's side over its port.
  2. The client fits a cannon at the brigantine's middle starboard port and mans it; it loads.
  3. Shut, it does not fire: Left Mouse sends no shot and it stays loaded; the prompt says the port is shut.
  4. Up opens it, on both: the cover slides aft clear of the port and the cannon runs out to it.
  5. Run out, it fires: the shot leaves the muzzle outside the hull.
  6. Down shuts it again: the cover closes the port and the cannon runs in; reloaded, it still cannot fire.
  7. Throughout, the next port along stayed shut: each is worked on its own.
Writes Saved/GunportsPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from play_peers import peer_of  # noqa: E402  (the same ship on another machine, spawned ones too)
POWDER = unreal.load_asset('/Game/Elitewake/Items/Ships/DA_Gunpowder')   # a powder charge with each round shot (CLAUDE.md 7.4, November 7)

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'GunportsPlayResult.json')
GUN, NEXT = 'StarboardCannon2', 'StarboardCannon1'
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


def copy_in(world, actor):
    found = peer_of(actor, world)
    assert found, f'no copy of {actor.get_name()} in {world.get_name()}'
    return found


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
brig, schooner = ship_named(server_world, 'Brigantine'), ship_named(server_world, 'Schooner')
brig_peer, schooner_peer = copy_in(client_world, brig), copy_in(client_world, schooner)
cannon, shot = (unreal.load_asset(f'/Game/Elitewake/Items/Testing/{n}') for n in ('DA_TestCannon', 'DA_TestRoundShot'))
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks, measured = [], {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'aim': None, 'at': 0.0, 'sent': 0.0}


def gunports(ship):
    return [str(m.get_editor_property('mount_id')) for m in ship.get_editor_property('definition').get_editor_property('mounts')
            if m.get_editor_property('gunport')]


def cover(on, mount):
    return next((c for c in on.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith(f'Cover_{mount}')), None)


def gun(on, mount):
    return next((c for c in on.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith(f'Fitting_{mount}')), None)


def local(ship, where):
    return ship.get_actor_transform().inverse_transform_location(where)


def ports():
    found = {'Brigantine': gunports(brig), 'Schooner': gunports(schooner)}
    measured['gunports'] = {k: len(v) for k, v in found.items()}
    assert len(found['Brigantine']) == 6 and len(found['Schooner']) == 12, measured['gunports']
    for ship, peer, ids in ((brig, brig_peer, found['Brigantine']), (schooner, schooner_peer, found['Schooner'])):
        for m in ids:
            assert not ship.is_gunport_open(m) and not peer.is_gunport_open(m), f'{m} starts open'
            c = cover(peer, m)
            assert c and c.is_visible(), f'no cover drawn at {m} on the client'
            # In the hull's side, level with its cannon place and beside it fore and aft.
            at, mount = local(peer, c.get_world_location()), local(peer, peer.get_mount_world_transform(m).translation)
            assert abs(at.x - mount.x) < 5 and abs(at.y) > abs(mount.y) + 20, f'the {m} cover is not over its port: {at} for {mount}'
    measured['brig_cover_closed_local'] = str(local(brig_peer, cover(brig_peer, GUN).get_world_location()))
    inv = owner.get_inventory_component()
    assert inv.add_item(cannon, 1) == 1 and inv.add_item(shot, 4) == 4 and inv.add_item(POWDER, 4) == 4
    return True


def keep_aim():
    if not state['aim']:
        return
    target = state['aim']()
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, target))


def stand_by_gun():
    at = local(brig, brig.get_mount_world_transform(GUN).translation)
    for dx, fy in ((60, .5), (-60, .5), (60, .3), (120, .4), (-120, .4), (0, .6)):
        spot = brig.get_actor_transform().transform_location(unreal.Vector(at.x + dx, at.y * fy, at.z - 40 + 98))
        if owner.teleport(spot, brig.get_actor_rotation()):
            break
    else:
        raise AssertionError('no room on the gun deck')
    owner.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['aim'] = lambda: brig.get_mount_world_transform(GUN).translation
    keep_aim()


def interact():
    stand_by_gun()
    state['sent'] = time.monotonic()
    assert lib.send_verification_interaction_request(client, brig_peer)


def until(cond):
    """Done when cond() holds; the hold is sent again every 1.5 s if the server cancelled it (the ship rolls)."""
    def done():
        keep_aim()
        if cond():
            return True
        if time.monotonic() - state['sent'] > 1.5:
            state['sent'] = time.monotonic()
            assert lib.send_verification_interaction_request(client, brig_peer)
        return False
    return done


def fitted():
    return brig.get_fitting(GUN) == cannon and brig_peer.get_fitting(GUN) == cannon


def manned():
    if brig.get_cannon_gunner(GUN) != owner:
        return False
    state['aim'] = None
    client.set_control_rotation(unreal.Rotator(roll=0, pitch=2, yaw=brig.get_actor_rotation().yaw + 90))
    return True


def loaded():
    if not brig.is_cannon_loaded(GUN):
        return False
    measured['gun_shut_local'] = str(local(brig_peer, gun(brig_peer, GUN).get_world_location()))
    return True


def fire():
    state['before'] = unreal.EWCannonBall.get_last_shot(server_world)
    assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')
    state['at'] = time.monotonic()


def held_fire():
    if time.monotonic() - state['at'] < 1.0:
        return False
    assert unreal.EWCannonBall.get_last_shot(server_world) == state['before'], 'it fired through its shut port'
    assert brig.is_cannon_loaded(GUN), 'the shot was spent through the shut port'
    try:
        prompt = str(brig.get_interaction_prompt(owner))
    except AttributeError:
        prompt = str(unreal.EWInteractable.get_interaction_prompt(brig, owner))
    measured['prompt_shut'] = prompt
    assert 'Port shut' in prompt, prompt
    return True


def key(name):
    def begin():
        assert lib.send_verification_gameplay_key(client, name), f'the {name} key was not handled'
        state['at'] = time.monotonic()
    return begin


def opened():
    if not (brig.get_gunport_opening(GUN) >= .99 and brig_peer.get_gunport_opening(GUN) >= .99):
        return False
    assert brig.is_gunport_open(GUN) and brig_peer.is_gunport_open(GUN)
    measured['open_seconds'] = round(time.monotonic() - state['at'], 2)
    closed = eval_vector(measured['brig_cover_closed_local'])
    now = local(brig_peer, cover(brig_peer, GUN).get_world_location())
    measured['cover_slid_cm'] = round(closed.x - now.x, 1)
    assert closed.x - now.x > 60, f'the cover slid only {closed.x - now.x:.0f} cm aft'
    run = local(brig_peer, gun(brig_peer, GUN).get_world_location())
    shut = eval_vector(measured['gun_shut_local'])
    measured['run_out_cm'] = round(abs(run.y) - abs(shut.y), 1)
    assert abs(run.y) - abs(shut.y) > 40, f'the cannon ran out only {abs(run.y) - abs(shut.y):.0f} cm'
    assert not brig.is_gunport_open(NEXT) and brig_peer.get_gunport_opening(NEXT) == 0, 'the next port opened too'
    return True


def eval_vector(text):
    import re
    x, y, z = (float(v) for v in re.findall(r'[xyz]: (-?[\d.]+)', text))
    return unreal.Vector(x, y, z)


def fired():
    after = unreal.EWCannonBall.get_last_shot(server_world)
    if after == state['before'] or not after:
        assert time.monotonic() - state['at'] < 3.0, 'no shot left the open port'
        return False
    muzzle = local(brig, brig.get_cannon_muzzle_world(GUN).translation)
    hull_y = brig.get_editor_property('definition').get_editor_property('hull_extent').y
    measured['muzzle_out_of_hull_cm'] = round(abs(muzzle.y) - hull_y, 1)
    return True


def shut():
    if brig.get_gunport_opening(GUN) > 0 or brig_peer.get_gunport_opening(GUN) > 0:
        return False
    back = local(brig_peer, cover(brig_peer, GUN).get_world_location())
    closed = eval_vector(measured['brig_cover_closed_local'])
    assert (back - closed).length() < 1, f'the cover did not close the port: {back} for {closed}'
    return True


def reloaded():
    return brig.is_cannon_loaded(GUN)


STEPS = [
    ('The brigantine has 6 hull gunports and the schooner 12, all shut on both, each cover drawn over its port', lambda: None, ports, 8),
    ('The client fits a cannon at the brigantine\'s middle starboard port', interact, until(fitted), 10),
    ('...and mans it', interact, until(manned), 10),
    ('It loads', lambda: None, loaded, 12),
    ('Shut, it will not fire: no shot, still loaded, and the prompt says the port is shut', fire, held_fire, 5),
    ('Up opens the port on both: the cover slides aft and the cannon runs out; the next port stays shut', key('Up'), opened, 6),
    ('Run out, it fires through the open port', fire, fired, 5),
    ('Down shuts it on both: the cover closes the port and the cannon runs in', key('Down'), shut, 6),
    ('Reloaded, it still cannot fire through the shut port', lambda: None, reloaded, 12),
    ('...no shot leaves', fire, held_fire, 5),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Gunports success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; opening {brig.get_gunport_opening(GUN):.2f}, aimed {brig.find_aimed_mount(owner)}, '
                               f'gunner {brig.get_cannon_gunner(GUN)}, loaded {brig.is_cannon_loaded(GUN)}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
