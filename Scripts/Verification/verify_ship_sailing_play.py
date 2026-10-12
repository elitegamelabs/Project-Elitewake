"""Client sailing acceptance on the coastal map's bare sloop.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the
sloop from Scripts/Setup/create_sloop_test_assets.py. Run unattended with run_play_check.py, or start
that Play session yourself and run this from the editor's Python console.

Through ordinary owned requests and movement input, the client:
  1. installs the helm, mainsail and headsail at their mounts (test fittings granted in Play only),
  2. raises the anchor at the capstan,
  3. takes the helm, sets full sail with forward input (W) and steers with right input (D),
  4. releases the rudder, leaves the helm, and drops the anchor to stop the ship.
Each step waits for its result on the server and on the client's copy of the ship, with a timeout.
Aim is re-applied every frame while a hold runs, so a stray mouse over the Play window cannot cancel it.
Editor background throttling is turned off while it runs (the deleted prototype failed on throttled frames).
Writes Saved/ShipSailingPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ShipSailingPlayResult.json')
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
ships = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
ship = next(s for s in ships if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop')
peer = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if a.get_name() == ship.get_name())
folder = '/Game/Elitewake/Items/Testing'
helm, mainsail, headsail = (unreal.load_asset(f'{folder}/{n}') for n in ('DA_TestShipHelm', 'DA_TestSailMedium', 'DA_TestSailSmall'))
assert helm and mainsail and headsail, 'Run Scripts/Setup/create_sloop_test_assets.py first.'

settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)

checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'aim': None, 'input': None, 'frame': 0, 'handle': None, 'memo': {}}

def target_of(name):
    return ship.get_anchor_point_world() if name == 'Anchor' else ship.get_mount_world_transform(name).translation

def stand_at(mount_id):
    """Stand on deck within reach of the mount (or the anchor capstan): forward of the helm and mast, aft of the
    headsail and capstan near the bow."""
    mount = target_of(mount_id)
    forward = ship.get_actor_forward_vector()
    off = {'Helm': 110, 'Mainsail': 110}.get(mount_id, -120)
    spot = unreal.Vector(mount.x + forward.x * off, mount.y + forward.y * off, ship.get_actor_location().z + ship.get_deck_height() + 98)
    for p in (owner, pawn):
        assert p.teleport(spot, ship.get_actor_rotation())
    state['aim'] = mount_id

def keep_aim():
    if not state['aim']:
        return
    mount = target_of(state['aim'])
    eye = owner.get_actor_location() + unreal.Vector(0, 0, owner.get_editor_property('base_eye_height'))
    rotation = unreal.MathLibrary.find_look_at_rotation(eye, mount)
    owner.get_controller().set_control_rotation(rotation)
    client.set_control_rotation(rotation)

def interact():
    assert lib.send_verification_interaction_request(client, peer)

def install(mount_id):
    def begin():
        stand_at(mount_id)
        keep_aim()
        interact()
    return begin

def fitted(mount_id, item):
    return lambda: ship.get_fitting(mount_id) == item and peer.get_fitting(mount_id) == item

def begin_sailing():
    state['aim'] = None
    state['frame0'] = state['frame']
    # Forward pressed, released, pressed: furled to half to full.
    state['input'] = lambda f: pawn.do_move(0, 1) if (f < 5 or 10 <= f < 15) else None

def begin_steering():
    state['memo'].update(start=ship.get_actor_location(), yaw=ship.get_actor_rotation().yaw, t=time.monotonic())
    state['input'] = lambda f: pawn.do_move(0.5, 0)

def steered():
    m = state['memo']
    if time.monotonic() - m['t'] < 4.0:
        return False
    moved = (ship.get_actor_location() - m['start']).length()
    turned = ship.get_actor_rotation().yaw - m['yaw']
    gap = (ship.get_actor_location() - peer.get_actor_location()).length()
    assert moved > 300, f'moved only {moved:.0f} cm'
    assert turned > 5, f'turned only {turned:.1f} degrees'
    assert abs(ship.get_rudder() - 0.5) < 0.06, f'rudder {ship.get_rudder()}'
    assert gap < 400, f'client copy {gap:.0f} cm from server'
    m.update(moved=moved, turned=turned, gap=gap)
    return True

def release_rudder():
    state['input'] = None

def rudder_centred():
    if abs(ship.get_rudder()) > 1e-4:
        return False
    assert ship.get_sail_state() == unreal.EWSailState.FULL, 'sails must stay set'
    return True

def left_helm():
    if ship.get_helmsman() is not None or peer.get_helmsman() is not None or pawn.get_helm_ship() is not None:
        return False
    movement = owner.get_component_by_class(unreal.CharacterMovementComponent)
    capsule = pawn.get_component_by_class(unreal.CapsuleComponent)
    return movement.movement_mode != unreal.MovementMode.MOVE_NONE and capsule.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION

def grant():
    assert not ship.get_installed_fittings(), 'The sloop must start as a bare hull'
    assert ship.is_anchored() and peer.is_anchored(), 'The moored sloop must start anchored'
    for item in (helm, mainsail, headsail):
        assert owner.get_inventory_component().add_item(item, 1) == 1

# (description, begin action, completion condition, timeout seconds)
STEPS = [
    ('Bare sloop; test helm and sails granted to the client survivor in Play only', grant, lambda: True, 2),
    ('Client installs the helm; server and client copies agree', install('Helm'), fitted('Helm', helm), 6),
    ('Client installs the Medium mainsail', install('Mainsail'), fitted('Mainsail', mainsail), 6),
    ('Client installs the Small headsail; all three fittings left the inventory', install('Headsail'),
     lambda: fitted('Headsail', headsail)() and owner.get_inventory_component().get_item_count(helm) == 0, 6),
    ('Client raises the anchor at the capstan', install('Anchor'), lambda: not ship.is_anchored() and not peer.is_anchored(), 6),
    ('Client takes the helm; helmsman replicates and the survivor stays possessed', install('Helm'),
     lambda: ship.get_helmsman() == owner and peer.get_helmsman() == pawn and pawn.get_helm_ship() == peer
     and client.get_controlled_pawn() == pawn, 6),
    ('Forward input twice sets full sail on the server and client', begin_sailing,
     lambda: ship.get_sail_state() == unreal.EWSailState.FULL and peer.get_sail_state() == unreal.EWSailState.FULL, 6),
    ('Client sails and steers for 4 s', begin_steering, steered, 8),
    ('Releasing the rudder centres it; the sails stay set', release_rudder, rudder_centred, 4),
    ('Client leaves the helm; movement and collision return', interact, left_helm, 6),
    ('Client drops the anchor and the ship comes to a stop', install('Anchor'),
     lambda: ship.is_anchored() and peer.is_anchored() and ship.get_speed() < 1, 8),
]

def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    m = state['memo']
    RESULT.write_text(json.dumps({
        'success': error is None, 'checks': checks, 'error': error,
        'sailing': {k: round(m[k], 1) for k in ('moved', 'turned', 'gap') if k in m},
        'state': {'server_ship': str(ship.get_actor_location()), 'client_ship': str(peer.get_actor_location()),
                  'speed': ship.get_speed(), 'sail_state': str(ship.get_sail_state()), 'rudder': ship.get_rudder(),
                  'helmsman': str(ship.get_helmsman()), 'fittings': len(ship.get_installed_fittings())},
    }, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK ShipSailing success={error is None} error={error}')

def tick(delta):
    state['frame'] += 1
    if state['input']:
        state['input'](state['frame'] - state.get('frame0', 0))
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
