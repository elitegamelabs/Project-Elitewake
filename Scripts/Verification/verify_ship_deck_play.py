"""Crew on a moving deck: the client rides, walks, goes overboard and climbs back up a ladder.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the
sloop from Scripts/Setup/create_sloop_test_assets.py (helm, sail mounts and boarding ladders).
Run unattended with run_play_check.py.

The host fits out the sloop (test fittings granted in Play only), takes the helm and sails with a little
rudder. The client, through its own movement input and owned requests:
  1. stands on deck and rides along without sliding off or falling through,
  2. walks forward along the deck while the ship sails,
  3. walks off the side into the sea and swims,
  4. climbs back aboard at the starboard ladder once the host has furled the sails.
Each step waits for its result on the server and the client, with a timeout. Background throttling is
off while it runs. Writes Saved/ShipDeckPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ShipDeckPlayResult.json')
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

crew = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
ships = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
assert len(ships) == 1, 'Expected exactly one ship in the map.'
ship = ships[0]
peer = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if a.get_name() == ship.get_name())
folder = '/Game/Elitewake/Items/Testing'
helm, mainsail, headsail = (unreal.load_asset(f'{folder}/{n}') for n in ('DA_TestShipHelm', 'DA_TestSailMedium', 'DA_TestSailSmall'))
assert helm and mainsail and headsail, 'Run Scripts/Setup/create_sloop_test_assets.py first.'

settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)

checks = []
state = {'trace': [], 'next_trace': 0.0, 'index': 0, 'begun': False, 'deadline': 0.0, 'aim': None, 'input': None, 'frame': 0, 'frame0': 0, 'handle': None, 'memo': {}}
DECK_TOP = 100.0     # DA_Ship_Sloop hull half height
HALF_HEIGHT = 98.0   # capsule half height plus clearance

def deck_point(local):
    return ship.get_actor_transform().transform_location(unreal.Vector(local[0], local[1], DECK_TOP + HALF_HEIGHT))

def local_of(actor):
    return ship.get_actor_transform().inverse_transform_location(actor.get_actor_location())

def mode(character):
    return character.get_component_by_class(unreal.CharacterMovementComponent).movement_mode

def teleport_crew(location, rotation=None):
    rotation = rotation or ship.get_actor_rotation()
    for p in (crew, pawn):
        assert p.teleport(location, rotation)

def look(controller, character, target):
    eye = character.get_actor_location() + unreal.Vector(0, 0, character.get_editor_property('base_eye_height'))
    controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, target))

def keep_aim():
    aim = state['aim']
    if aim is None:
        return
    who, target = aim
    if who == 'host':
        look(host_pc, host, target())
    else:
        look(crew.get_controller(), crew, target())
        look(client, crew, target())

# --- Host fits out the ship -------------------------------------------------------------------
def host_install(mount_id):
    def begin():
        mount = ship.get_mount_world_transform(mount_id).translation
        forward = ship.get_actor_forward_vector()
        spot = unreal.Vector(mount.x - forward.x * 120, mount.y - forward.y * 120, ship.get_actor_location().z + DECK_TOP + HALF_HEIGHT)
        assert host.teleport(spot, ship.get_actor_rotation())
        state['aim'] = ('host', lambda: ship.get_mount_world_transform(mount_id).translation)
        keep_aim()
        assert lib.send_verification_interaction_request(host_pc, ship)
    return begin

def grant():
    assert not ship.get_installed_fittings(), 'The sloop must start as a bare hull'
    # The moored sloop faces the islet 15 m east. Move it 5 m north, clear of the dock, and turn it
    # north toward open water for this run.
    location = ship.get_actor_location()
    ship.set_actor_location_and_rotation(unreal.Vector(location.x, location.y + 500, location.z),
                                         unreal.Rotator(roll=0, pitch=0, yaw=90), False, True)
    for item in (helm, mainsail, headsail):
        assert host.get_inventory_component().add_item(item, 1) == 1

# --- Crew rides along --------------------------------------------------------------------------
def board_crew():
    state['aim'] = None
    teleport_crew(deck_point((-150, -60)))

def crew_settled():
    if not (ship.is_aboard(crew) and peer.is_aboard(pawn) and mode(crew) == unreal.MovementMode.MOVE_WALKING):
        return False
    state['memo']['rest'] = local_of(crew)
    return True

def host_full_sail():
    state['aim'] = None
    state['frame0'] = state['frame']
    state['input'] = lambda f: host.do_move(0, 1) if (f < 5 or 10 <= f < 15) else None

def start_voyage():
    m = state['memo']
    m.update(start=ship.get_actor_location(), t=time.monotonic(), rest=local_of(crew))
    state['input'] = None

def rode_along():
    m = state['memo']
    if time.monotonic() - m['t'] < 6.0:
        assert ship.is_aboard(crew), f'crew fell off at {crew.get_actor_location()}'
        return False
    sailed = (ship.get_actor_location() - m['start']).length()
    slid = (local_of(crew) - m['rest']).length()
    gap = (crew.get_actor_location() - pawn.get_actor_location()).length()
    assert sailed > 500, f'ship sailed only {sailed:.0f} cm'
    assert ship.is_aboard(crew) and peer.is_aboard(pawn), 'crew must still be aboard'
    assert mode(crew) == unreal.MovementMode.MOVE_WALKING, f'crew movement {mode(crew)}'
    assert slid < 100, f'crew slid {slid:.0f} cm across the deck'
    assert gap < 100, f'client copy {gap:.0f} cm from server'
    m.update(sailed=sailed, slid=slid, gap=gap)
    return True

def walk_forward():
    m = state['memo']
    m.update(walk_from=local_of(crew), t=time.monotonic())
    assert ship.get_speed() > 200, f'the ship must be under way, speed {ship.get_speed():.0f}'
    client.set_control_rotation(ship.get_actor_rotation())
    state['input'] = lambda f: pawn.do_move(0, 1)

def walked():
    m = state['memo']
    client.set_control_rotation(ship.get_actor_rotation())
    if time.monotonic() - m['t'] < 0.6:
        return False
    state['input'] = None
    advanced = local_of(crew).x - m['walk_from'].x
    m['walk_speed'] = ship.get_speed()
    assert ship.is_aboard(crew) and peer.is_aboard(pawn), 'crew must still be aboard'
    assert advanced > 80, f'walked only {advanced:.0f} cm forward'
    m['walked'] = advanced
    return True

def walk_overboard():
    client.set_control_rotation(ship.get_actor_rotation())
    state['input'] = lambda f: pawn.do_move(1, 0)

def overboard():
    client.set_control_rotation(ship.get_actor_rotation())
    return not ship.is_aboard(crew) and mode(crew) == unreal.MovementMode.MOVE_SWIMMING

def host_furl():
    state['frame0'] = state['frame']
    state['input'] = lambda f: host.do_move(0, -1) if (f < 5 or 10 <= f < 15) else None

def stopped():
    return ship.get_sail_state() == unreal.EWSailState.FURLED and ship.get_speed() < 30

def climb_ladder():
    state['input'] = None
    ladder = ship.get_boarding_point_world(1)
    outward = ship.get_actor_right_vector()
    # Tread water beside the ladder: place the swimmer and drop the momentum from going overboard.
    teleport_crew(unreal.Vector(ladder.x + outward.x * 150, ladder.y + outward.y * 150, ship.get_actor_location().z - 80))
    for p in (crew, pawn):
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['aim'] = ('crew', lambda: ship.get_boarding_point_world(1))
    state['memo'].update(climb_at=time.monotonic() + 0.5, climb_sent=False)

def climbed():
    m = state['memo']
    if not m['climb_sent']:
        if time.monotonic() < m['climb_at']:
            return False
        assert lib.send_verification_interaction_request(client, peer)
        m['climb_sent'] = True
        return False
    return ship.is_aboard(crew) and peer.is_aboard(pawn) and local_of(crew).z > DECK_TOP

def host_leave():
    state['aim'] = None
    assert lib.send_verification_interaction_request(host_pc, ship)

STEPS = [
    ('Bare sloop; host granted test fittings in Play only', grant, lambda: True, 2),
    ('Host installs the helm', host_install('Helm'), lambda: peer.get_fitting('Helm') == helm, 6),
    ('Host installs the mainsail', host_install('Mainsail'), lambda: peer.get_fitting('Mainsail') == mainsail, 6),
    ('Host installs the headsail', host_install('Headsail'), lambda: peer.get_fitting('Headsail') == headsail, 6),
    ('Client crew stands on deck; server and client agree it is aboard and walking', board_crew, crew_settled, 6),
    ('Host takes the helm', host_install('Helm'), lambda: ship.get_helmsman() == host and peer.get_helmsman() is not None, 6),
    ('Host sets full sail', host_full_sail, lambda: ship.get_sail_state() == unreal.EWSailState.FULL, 6),
    ('Crew rides 6 s of sailing without sliding or falling', start_voyage, rode_along, 10),
    ('Crew walks forward along the deck while the ship is under way', walk_forward, walked, 5),
    ('Crew walks off the side into the sea and swims', walk_overboard, overboard, 8),
    ('Host furls the sails and the ship slows', host_furl, stopped, 12),
    ('Crew climbs back aboard at the starboard ladder', climb_ladder, climbed, 8),
    ('Host leaves the helm', host_leave, lambda: ship.get_helmsman() is None and peer.get_helmsman() is None, 6),
]

def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    m = state['memo']
    RESULT.write_text(json.dumps({
        'success': error is None, 'checks': checks, 'error': error,
        'deck': {k: round(m[k], 1) for k in ('sailed', 'slid', 'gap', 'walked', 'walk_speed') if k in m},
        'trace': state['trace'],
        'state': {'ship': str(ship.get_actor_location()), 'speed': ship.get_speed(),
                  'crew_local': str(local_of(crew)), 'crew_mode': str(mode(crew)),
                  'crew_aboard_server': ship.is_aboard(crew), 'crew_aboard_client': peer.is_aboard(pawn)},
    }, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK ShipDeck success={error is None} error={error}')

def record():
    now = time.monotonic()
    if now < state['next_trace']:
        return
    state['next_trace'] = now + 0.5
    def short(v):
        return [round(v.x), round(v.y), round(v.z)]
    base = crew.get_movement_base_object() if hasattr(crew, 'get_movement_base_object') else None
    state['trace'].append({'step': state['index'], 'server_crew': short(local_of(crew)), 'client_crew': short(peer.get_actor_transform().inverse_transform_location(pawn.get_actor_location())),
                           'mode': str(mode(crew)).split('.')[-1].split(':')[0], 'base': base.get_name() if base else None,
                           'ship_speed': round(ship.get_speed())})

def tick(delta):
    state['frame'] += 1
    record()
    if state['input']:
        state['input'](state['frame'] - state['frame0'])
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
