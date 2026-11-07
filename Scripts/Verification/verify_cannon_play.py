"""Client acceptance for a ship's cannon on the coastal map's sloop.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after
Scripts/Setup/build_cannon.py. Run unattended with run_play_check.py.

Through ordinary owned requests and keys, the client:
  1. fits a two-cannon railing at the sloop's starboard railing hardpoint (owner, October 17: she has no hull
     gunports), which opens two cannon places, and a cannon (test fittings granted in Play only) in the first;
  2. holds Interact at it to man it: it stands behind the carriage, riding the ship, on both machines;
  3. carrying round shot, sees the cannon load itself within its loading time, one shot leaving the inventory;
  4. aims with the view: the barrel follows on the client, clamped to the port's arc on the server;
  5. fires with Left Mouse: the shot leaves the muzzle on server and client and falls into the sea or onto
     the ground well away from the ship, and the cannon starts loading again;
  6. leaves the cannon with Interact and walks again.
Writes Saved/CannonPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal
POWDER = unreal.load_asset('/Game/Elitewake/Items/Ships/DA_Gunpowder')   # a powder charge with each round shot (CLAUDE.md 7.4, November 7)

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'CannonPlayResult.json')
# The sloop has no hull gunports (owner, October 17): her cannons stand behind a two-cannon railing module fitted at
# a railing hardpoint, which opens two cannon places.
MOUNT, RAILING = 'StarboardCannon1', 'StarboardRailing'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop')
peer = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if s.get_name() == ship.get_name())
cannon, shot, railing = (unreal.load_asset(f'/Game/Elitewake/Items/Testing/{n}') for n in ('DA_TestCannon', 'DA_TestRoundShot', 'DA_TestRailingTwoCannon'))
assert cannon and shot and railing, 'Run Scripts/Setup/build_cannon.py and build_railings.py first.'
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None}


def count(who, item):
    return who.get_inventory_component().get_item_count(item)


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def mount_world(which=None):
    return ship.get_mount_world_transform(which or MOUNT).translation


def railing_world():
    return mount_world(RAILING) + unreal.Vector(0, 0, 40)


def interact_at_railing():
    """On deck inboard of the railing hardpoint, looking at it, and hold Interact."""
    local = ship.get_actor_transform().inverse_transform_location(mount_world(RAILING))
    spot = ship.get_actor_transform().transform_location(unreal.Vector(local.x + 60, local.y * .35, ship.get_deck_height() + 98))
    for p in (owner, pawn):
        assert p.teleport(spot, ship.get_actor_rotation()), f'no room to stand at {spot} by the railing'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['aim'] = railing_world
    keep_aim()
    assert not ship.is_mount_open(MOUNT), 'the cannon place is open with no cannon railing fitted'
    # Until then the hardpoint carries a plain railing, solid to people.
    plain = plain_railing(peer)
    assert plain and plain.is_visible(), 'no plain railing at the empty hardpoint on the client'
    assert plain.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN) == unreal.CollisionResponseType.ECR_BLOCK, 'the plain railing does not stop people'
    assert lib.send_verification_interaction_request(client, peer), f'the interaction request was refused (aimed mount on the server: {ship.find_aimed_mount(owner)})'


def plain_railing(on):
    """The plain railing standing at the empty hardpoint (owner, October 17), if this machine shows one."""
    return next((c for c in on.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith(f'Empty_{RAILING}')), None)


def railing_fitted():
    if not (ship.get_fitting(RAILING) == railing and peer.get_fitting(RAILING) == railing and ship.is_mount_open(MOUNT)
            and peer.is_mount_open(MOUNT)):
        return False
    assert plain_railing(peer) is None, 'the plain railing still stands under the fitted module on the client'
    return True


def interact_at_mount():
    """On deck, well inboard of the cannon, looking at its mount, and hold Interact."""
    local = ship.get_actor_transform().inverse_transform_location(mount_world())
    spot = ship.get_actor_transform().transform_location(unreal.Vector(local.x + 60, local.y * .35, ship.get_deck_height() + 98))
    for p in (owner, pawn):
        assert p.teleport(spot, ship.get_actor_rotation())
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['aim'] = mount_world
    keep_aim()
    assert lib.send_verification_interaction_request(client, peer)


def grant():
    assert not ship.get_installed_fittings(), 'the sloop must start bare'
    inventory = owner.get_inventory_component()
    assert inventory.add_item(cannon, 1) == 1 and inventory.add_item(shot, 3) == 3 and inventory.add_item(railing, 1) == 1      # no powder yet
    state['memo']['shot_start'] = count(owner, shot)


def fitted():
    return ship.get_fitting(MOUNT) == cannon and peer.get_fitting(MOUNT) == cannon and count(owner, cannon) == 0


def manned():
    if not (ship.get_cannon_gunner(MOUNT) == owner and peer.get_cannon_gunner(MOUNT) == pawn and owner.get_gun_ship() == ship
            and pawn.get_gun_ship() == peer and pawn.get_gun_mount() == MOUNT):
        return False
    state['aim'] = None
    seat = ship.get_actor_transform().inverse_transform_location(owner.get_actor_location())
    mount = ship.get_actor_transform().inverse_transform_location(mount_world())
    state['memo']['seat_from_mount'] = round((seat - mount).length())
    assert owner.get_attach_parent_actor() == ship, 'the gunner does not ride the ship'
    state['memo']['t'] = time.monotonic()
    return True


def no_powder_no_load():
    """Manned with shot but no powder: after a few seconds it has not loaded and no shot is gone; then the powder comes."""
    m = state['memo']
    if time.monotonic() - m['t'] < 4.0:
        return False
    assert not ship.is_cannon_loaded(MOUNT) and str(ship.get_cannon_load_step(MOUNT)) == 'None', 'it loaded without powder'
    assert count(owner, shot) == m['shot_start'], 'a shot was taken without powder'
    assert owner.get_inventory_component().add_item(POWDER, 3) == 3
    m['powder_start'] = count(owner, POWDER)
    m['t'] = time.monotonic()
    return True


def loaded():
    if not (ship.is_cannon_loaded(MOUNT) and peer.is_cannon_loaded(MOUNT)):
        return False
    m = state['memo']
    m['load_seconds'] = round(time.monotonic() - m['t'], 1)
    assert count(owner, shot) == m['shot_start'] - 1 and count(pawn, shot) == m['shot_start'] - 1, 'loading did not take one round shot'
    assert count(owner, POWDER) == m['powder_start'] - 1, 'loading did not take one powder charge'
    return True


def aim():
    rest = ship.get_actor_rotation().yaw + 90   # the starboard port faces out to the ship's right
    client.set_control_rotation(unreal.Rotator(roll=0, pitch=5, yaw=rest + 10))
    state['memo']['t'] = time.monotonic()


def aimed():
    want = (5.0, 10.0)
    got, seen = ship.get_cannon_aim(MOUNT), peer.get_cannon_aim(MOUNT)
    if abs(got.pitch - want[0]) > 3 or abs(got.yaw - want[1]) > 3 or abs(seen.yaw - got.yaw) > .5:
        return False
    barrel = next((c for c in peer.get_components_by_class(unreal.StaticMeshComponent) if f'Turning_{MOUNT}' in c.get_name()), None)
    assert barrel, "no barrel drawn on the client"
    turned = barrel.get_editor_property('relative_rotation')
    state['memo'].update(aim=[round(got.pitch, 1), round(got.yaw, 1)], barrel=[round(turned.pitch, 1), round(turned.yaw, 1)])
    # Far past the port's arc is held at its edge.
    client.set_control_rotation(unreal.Rotator(roll=0, pitch=40, yaw=ship.get_actor_rotation().yaw + 90 + 60))
    state['memo']['t'] = time.monotonic()
    return True


def clamped():
    if time.monotonic() - state['memo']['t'] < 1.0:
        return False
    got = ship.get_cannon_aim(MOUNT)
    assert got.yaw <= 15.01 and got.pitch <= 8.01, f'aimed past the port: {got}'
    state['memo']['clamped'] = [round(got.pitch, 1), round(got.yaw, 1)]
    client.set_control_rotation(unreal.Rotator(roll=0, pitch=5, yaw=ship.get_actor_rotation().yaw + 90 + 10))
    return True


def fire():
    m = state['memo']
    m['muzzle'] = ship.get_cannon_muzzle_world(MOUNT).translation
    m['before'] = unreal.EWCannonBall.get_last_shot(server_world)
    m['t'] = time.monotonic()
    assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def landed():
    m = state['memo']
    shot_server = unreal.EWCannonBall.get_last_shot(server_world)
    if not shot_server or shot_server == m['before']:
        return False
    if 'seen' not in m:
        seen = unreal.EWCannonBall.get_last_shot(client_world)
        if seen and seen.get_name() == shot_server.get_name():
            m['seen'] = True
    if not shot_server.has_landed():
        return False
    where = shot_server.get_landed_at()
    struck = shot_server.get_struck()
    m.update(range_m=round((where - m['muzzle']).length() / 100, 1), struck=str(struck.get_actor_label()) if struck else 'the sea',
             flight_s=round(time.monotonic() - m['t'], 2))
    assert m.get('seen'), 'the client never saw the shot'
    assert struck != ship, 'the shot struck its own ship'
    assert m['range_m'] > 15, f"the shot fell {m['range_m']} m away"
    assert shot_server.get_fired_from() == ship and shot_server.get_gunner() == owner
    assert not ship.is_cannon_loaded(MOUNT), 'still loaded after firing'
    return True


def reloading():
    if not (ship.is_cannon_loading(MOUNT) and peer.is_cannon_loading(MOUNT)):
        return False
    return count(owner, shot) == state['memo']['shot_start'] - 2


def leave():
    assert lib.send_verification_interaction_request(client, peer)


def left():
    if owner.get_gun_ship() or pawn.get_gun_ship() or ship.get_cannon_gunner(MOUNT):
        return False
    movement = owner.get_component_by_class(unreal.CharacterMovementComponent)
    return movement.movement_mode != unreal.MovementMode.MOVE_NONE and owner.get_attach_parent_actor() is None


STEPS = [
    ('A two-cannon railing, a cannon and 3 round shot (no powder yet), granted in Play only; the sloop starts bare', grant, lambda: True, 2),
    ('The client fits the two-cannon railing at the starboard railing hardpoint: its two cannon places open', interact_at_railing, railing_fitted, 6),
    ('The client fits the cannon in the first place behind the railing; server and client agree', interact_at_mount, fitted, 6),
    ('It holds Interact at the cannon to man it, standing behind the carriage and riding the ship on both machines', interact_at_mount, manned, 6),
    ('Without powder it does not load and keeps its shot (CLAUDE.md 7.4, November 7); then 3 powder are given', lambda: None, no_powder_no_load, 8),
    ('Carrying round shot and powder, the cannon loads itself in its loading time, taking one of each', lambda: None, loaded, 10),
    ('The view aims it: the server and the client\'s barrel follow', aim, aimed, 5),
    ('Aiming far past the port holds the cannon at the edge of its arc', lambda: None, clamped, 4),
    ('Left Mouse fires: the shot leaves the muzzle on both machines and falls well away from the ship', fire, landed, 10),
    ('Still manned and carrying shot, the cannon starts loading again', lambda: None, reloading, 4),
    ('Interact leaves the cannon; the survivor walks again', leave, left, 6),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = ('seat_from_mount', 'load_seconds', 'aim', 'barrel', 'clamped', 'range_m', 'struck', 'flight_s')
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error,
                                  'measured': {k: state['memo'][k] for k in keep if k in state['memo']}}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Cannon success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
