"""Client acceptance for round shot striking a hull: hull health and shot holes, on the coastal map.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after
Scripts/Setup/build_cannon.py. Run unattended with run_play_check.py.

The client fits and mans the sloop's starboard cannon (as verify_cannon_play does) and lets it load. The schooner
is moved (server, Play only) to lie 40 m off the sloop's starboard side, and the client fires level at it:
  1. the shot strikes the schooner's planking: not the box around its hull, and not the sloop;
  2. the schooner's hull health falls by one shot's damage on server and client;
  3. a shot hole is drawn where it struck, on the client too.
Writes Saved/HullDamagePlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'HullDamagePlayResult.json')
MOUNT = 'StarboardCannon'
SHOT_DAMAGE = 100.0   # AEWShip::RoundShotDamage
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
    return next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip) if s.get_name() == actor.get_name())


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
ship = ship_named(server_world, 'Sloop')
peer = copy_in(client_world, ship)
target = ship_named(server_world, 'Schooner')
target_peer = copy_in(client_world, target)
cannon, shot = (unreal.load_asset(f'/Game/Elitewake/Items/Testing/{n}') for n in ('DA_TestCannon', 'DA_TestRoundShot'))
assert cannon and shot, 'Run Scripts/Setup/build_cannon.py first.'
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None}


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def mount_world():
    return ship.get_mount_world_transform(MOUNT).translation


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
    assert inventory.add_item(cannon, 1) == 1 and inventory.add_item(shot, 3) == 3


def fitted():
    return ship.get_fitting(MOUNT) == cannon and peer.get_fitting(MOUNT) == cannon


def manned():
    if not (ship.get_cannon_gunner(MOUNT) == owner and peer.get_cannon_gunner(MOUNT) == pawn):
        return False
    state['aim'] = None
    return True


def place_target():
    """The schooner, parallel to the sloop and 40 m off its starboard side; the gun laid level at it."""
    right, at = ship.get_actor_right_vector(), ship.get_actor_location()
    target.set_actor_location_and_rotation(unreal.Vector(at.x + right.x * 4000, at.y + right.y * 4000, target.get_actor_location().z),
                                           ship.get_actor_rotation(), False, True)
    client.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=ship.get_actor_rotation().yaw + 90))
    state['memo'].update(t=time.monotonic(), health_before=target.get_hull_health(), max_health=target.get_max_hull_health())


def target_ready():
    m = state['memo']
    if time.monotonic() - m['t'] < 2.0 or not ship.is_cannon_loaded(MOUNT):
        return False
    gap = (target.get_actor_location() - target_peer.get_actor_location()).length()
    assert gap < 100, f"the client's schooner is {gap:.0f} cm from the server's"
    assert m['health_before'] == m['max_health'] and target.get_hole_count() == 0, 'the schooner starts damaged'
    return True


def fire():
    m = state['memo']
    m['before'] = unreal.EWCannonBall.get_last_shot(server_world)
    assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def struck():
    m = state['memo']
    fired = unreal.EWCannonBall.get_last_shot(server_world)
    if not fired or fired == m['before'] or not fired.has_landed():
        return False
    hit = fired.get_struck()
    m['struck'] = str(hit.get_actor_label()) if hit else 'the sea'
    where, at = fired.get_landed_at(), target.get_actor_location()
    local = target.get_actor_transform().inverse_transform_location(where)
    assert hit == target, (f"the shot struck {m['struck']}, not the schooner: landed at {where}, the schooner's frame {local}, "
                           f"muzzle {ship.get_cannon_muzzle_world(MOUNT).translation}, aim {ship.get_cannon_aim(MOUNT)}")
    return True


def damaged():
    m = state['memo']
    want = m['health_before'] - SHOT_DAMAGE
    if not (target.get_hull_health() == want and target_peer.get_hull_health() == want):
        return False
    if target.get_hole_count() != 1 or target_peer.get_hole_count() != 1:
        return False
    local = target.get_hole(0).get_editor_property('local')
    extent = target.get_editor_property('definition').get_editor_property('hull_extent')
    # On the planking: within the hull's length, out at its side, between the keel and the rail.
    assert abs(local.x) < extent.x and abs(local.y) > 60 and local.z < target.get_deck_height() + 120, f'hole at {local}'
    visual = next((c for c in target_peer.get_components_by_class(unreal.StaticMeshComponent) if 'ShotHole' in c.get_name()), None)
    assert visual, 'no shot hole drawn on the client'
    drawn = target_peer.get_actor_transform().inverse_transform_location(visual.get_world_location())
    m.update(health=[target.get_hull_health(), target_peer.get_hull_health()], hole=[round(local.x), round(local.y), round(local.z)],
             drawn_off=round((drawn - local).length(), 1))
    assert m['drawn_off'] < 10, f"the client draws the hole {m['drawn_off']} cm from where it struck"
    return True


def leave():
    assert lib.send_verification_interaction_request(client, peer)


def left():
    return not (owner.get_gun_ship() or pawn.get_gun_ship() or ship.get_cannon_gunner(MOUNT))


STEPS = [
    ('A cannon and 3 round shot, granted in Play only; the sloop starts bare', grant, lambda: True, 2),
    ('The client fits the cannon at the starboard hardpoint', interact_at_mount, fitted, 6),
    ('It mans the cannon', interact_at_mount, manned, 6),
    ("The cannon loads; the whole schooner lies 40 m off the sloop's starboard side; the gun is laid level at it", place_target, target_ready, 10),
    ("Left Mouse fires: the shot strikes the schooner's planking (not its hull box, not the sloop)", fire, struck, 6),
    ("The schooner's hull health falls by one shot on server and client, and a shot hole is drawn where it struck, on the client too",
     lambda: None, damaged, 4),
    ('Interact leaves the cannon', leave, left, 6),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = ('struck', 'health', 'hole', 'drawn_off')
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error,
                                  'measured': {k: state['memo'][k] for k in keep if k in state['memo']}}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK HullDamage success={error is None} error={error}')


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
