"""Client acceptance for the brigantine on the coastal map: fitting out, sailing, and getting about its decks.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the brigantine
from Scripts/Setup/build_brigantine.py. Run unattended with run_play_check.py.

Through ordinary owned requests and its own movement input, the client:
  1. installs a Large sail as the fore course, a Large sail as the gaff mainsail and a ship's wheel on the
     quarterdeck (each granted in Play only, just before it is fitted),
  2. raises the anchor, takes the helm, sets full sail, trims the sails to the wind and sails for 4 s, then leaves the helm and anchors.
     Every frame of the sail is measured: the ship on the server, its copy on the client and the client's own
     survivor at the helm must each move by what the ship's speed asks for that frame, with at most 5% of frames
     stalling or jumping (lag a player would see),
  3. walks down the hatch stairs to the gun deck, aims at a cannon port there, and walks back up,
  4. walks through the doorway into the captain's cabin, then into the crew's quarters under the forecastle,
     and climbs the stairs to the quarterdeck and to the forecastle,
  5. swims beside the hull, looks up at the stern ladder's rungs and climbs aboard.
Each step waits for its result on the server and on the client's copy, with a timeout.
Writes Saved/BrigantinePlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'BrigantinePlayResult.json')
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
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Brigantine')
peer = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if a.get_name() == ship.get_name())
folder = '/Game/Elitewake/Items/Testing'
large, helm = (unreal.load_asset(f'{folder}/DA_Test{n}') for n in ('SailLarge', 'ShipHelm'))
assert large and helm, 'Run Scripts/Setup/build_brigantine.py first.'

settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'aim': None, 'input': None, 'frame': 0, 'frame0': 0, 'handle': None, 'memo': {}}

DECK = ship.get_deck_height()
LOWER, RAISED, BOW = 50.0, DECK + 220.0, DECK + 200.0   # gun deck floor, quarterdeck and forecastle, from build_brigantine.py
STAND = 98.0                            # capsule half height plus clearance
# Where to stand, in the ship's frame, to reach each place: (x, y, floor height).
STANDS = {'ForeCourse': (870, -90, DECK), 'Mainsail': (-620, -90, DECK), 'Helm': (-1110, -110, RAISED),
          'Anchor': (520, -40, DECK), 'StarboardCannon7': (90, 130, LOWER)}


def local_of(actor, ship_copy=ship):
    return ship_copy.get_actor_transform().inverse_transform_location(actor.get_actor_location())


def place(x, y, floor, yaw=0.0):
    spot = ship.get_actor_transform().transform_location(unreal.Vector(x, y, floor + STAND))
    rotation = ship.get_actor_rotation()
    rotation = unreal.Rotator(roll=0, pitch=0, yaw=rotation.yaw + yaw)
    for p in (owner, pawn):
        assert p.teleport(spot, rotation), f'no room to stand at ({x}, {y}, {floor})'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    return rotation


def target(name):
    return ship.get_anchor_point_world() if name == 'Anchor' else ship.get_mount_world_transform(name).translation


def keep_aim():
    if not state['aim']:
        return
    eye = owner.get_actor_location() + unreal.Vector(0, 0, owner.get_editor_property('base_eye_height'))
    rotation = unreal.MathLibrary.find_look_at_rotation(eye, state['aim']())
    owner.get_controller().set_control_rotation(rotation)
    client.set_control_rotation(rotation)


def go(name, item=None):
    def begin():
        if item:
            added = owner.get_inventory_component().add_item(item, 1)
            assert added == 1, f'inventory took {added} {item.get_name()}'
        place(*STANDS[name])
        state['aim'] = lambda: target(name)
        keep_aim()
        assert lib.send_verification_interaction_request(client, peer)
    return begin


def prepare():
    assert not ship.get_installed_fittings(), 'The brigantine must start as a bare hull'
    assert ship.is_anchored() and peer.is_anchored()
    mounts = ship.get_editor_property('definition').get_editor_property('mounts')
    sizes = [m.get_editor_property('sail_size') for m in mounts if m.get_editor_property('type') == unreal.EWShipMountType.SAIL]
    assert (sizes.count(unreal.EWSailSize.LARGE), sizes.count(unreal.EWSailSize.MEDIUM), sizes.count(unreal.EWSailSize.SMALL)) == (4, 0, 2), sizes
    cannons = sum(1 for m in mounts if m.get_editor_property('type') == unreal.EWShipMountType.CANNON)
    assert cannons == 24, cannons


def full_sail():
    state['aim'] = None
    state['frame0'] = state['frame']
    state['input'] = lambda f: pawn.do_move(0, 1) if (f < 5 or 10 <= f < 15) else None


def trim_sails():
    """Shift with A or D swings the sails toward the wind's best angle, as a helmsman trims them."""
    side = 'D' if ship.get_best_sail_angle() > ship.get_sail_angle() else 'A'
    for key in ('LeftShift', side):
        assert lib.send_verification_gameplay_key_state(client, key, True)


def trimmed():
    if ship.get_trim_quality() < .9:
        return False
    for key in ('LeftShift', 'A', 'D'):
        lib.send_verification_gameplay_key_state(client, key, False)
    return True


def begin_run():
    m = state['memo']
    m.update(start=ship.get_actor_location(), t=time.monotonic(), frames=[],
             last=(time.monotonic(), ship.get_actor_location(), peer.get_actor_location(), pawn.get_actor_location()))

    def sample(_):
        """Every frame: how far the ship moved on each machine, and the client's survivor standing on it."""
        now = time.monotonic()
        then, s0, c0, p0 = m['last']
        here = (now, ship.get_actor_location(), peer.get_actor_location(), pawn.get_actor_location())
        if now - then > 0:
            m['frames'].append((now - m['t'], now - then, (here[1] - s0).length(), (here[2] - c0).length(),
                                (here[3] - p0).length(), ship.get_speed()))
        m['last'] = here
    state['input'] = sample


def hitches(column):
    """Frames, after the ship is under way, that moved under half or over one and a half times what its speed
    asks for that frame: a stall or a jump that a player sees as lag."""
    frames = [f for f in state['memo']['frames'] if f[0] > 1.0 and f[5] > 100]
    bad = [f for f in frames if not 0.5 <= f[column] / max(f[5] * f[1], 1e-3) <= 1.5]
    return len(bad), len(frames)


def ran():
    m = state['memo']
    if time.monotonic() - m['t'] < 4.0:
        return False
    state['input'] = None
    m['moved'] = (ship.get_actor_location() - m['start']).length()
    m['gap'] = (ship.get_actor_location() - peer.get_actor_location()).length()
    assert m['moved'] > 100, f'moved only {m["moved"]:.0f} cm'
    assert m['gap'] < 300, f'client copy {m["gap"]:.0f} cm from server'
    for name, column in (('server ship', 2), ("client's ship", 3), ("client's helmsman", 4)):
        bad, total = hitches(column)
        m.setdefault('smoothness', {})[name] = f'{bad} of {total} frames hitched'
        assert total >= 30 and bad <= 0.05 * total, f'{name}: {bad} of {total} frames hitched'
    return True


def leave():
    state['aim'] = None
    assert lib.send_verification_interaction_request(client, peer)


def walk(x, y, floor, yaw, until, name):
    """Stand at (x, y) on a floor facing yaw (0 forward, 180 aft) and walk ahead until `until(local z)` holds."""
    def begin():
        state['aim'] = None
        rotation = place(x, y, floor, yaw)
        state['memo'][name] = {'t': time.monotonic()}
        client.set_control_rotation(rotation)
        state['input'] = lambda f: (client.set_control_rotation(rotation), pawn.do_move(0, 1))

    def done():
        z_server, z_client = local_of(owner).z, local_of(pawn, peer).z
        state['memo'][name].update(server_z=round(z_server), client_z=round(z_client))
        if not (until(z_server) and until(z_client) and ship.is_aboard(owner) and peer.is_aboard(pawn)):
            return False
        state['input'] = None
        return True
    return begin, done


def aim_cannon():
    place(*STANDS['StarboardCannon7'])
    state['input'] = None
    state['aim'] = lambda: target('StarboardCannon7')


def climb_ladder():
    state['aim'] = None
    state['input'] = None
    ladder = ship.get_boarding_point_world(0)
    outward = ship.get_actor_forward_vector() * -1.0   # the ladder is centred on the stern, facing aft
    spot = unreal.Vector(ladder.x + outward.x * 150, ladder.y + outward.y * 150, ship.get_actor_location().z - 80)
    for p in (owner, pawn):
        assert p.teleport(spot, ship.get_actor_rotation())
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    # Look up at the rungs, about 2 m above the water, as a swimmer beside the hull sees them.
    state['aim'] = lambda: ship.get_boarding_point_world(0) + unreal.Vector(0, 0, 180)
    state['memo'].update(climb_at=time.monotonic() + 0.5, climb_sent=False)


def climbed():
    m = state['memo']
    if not m['climb_sent']:
        if time.monotonic() < m['climb_at']:
            return False
        assert lib.send_verification_interaction_request(client, peer)
        m['climb_sent'] = True
        return False
    # Holding on, the Up arrow climbs; at the top the survivor steps onto the deck.
    if owner.is_on_ladder() and not m.get('climbing'):
        assert lib.send_verification_gameplay_key_state(client, 'Up', True)
        m['climbing'] = True
    if owner.is_on_ladder() or not (ship.is_aboard(owner) and peer.is_aboard(pawn) and local_of(owner).z > DECK):
        return False
    lib.send_verification_gameplay_key_state(client, 'Up', False)
    return True


down = walk(40, 0, DECK, 0.0, lambda z: z < LOWER + STAND + 30, 'down')
up = walk(500, 0, LOWER, 180.0, lambda z: z > DECK + 60, 'up')
raised = walk(-590, -287, DECK, 180.0, lambda z: z > RAISED + 60, 'raised')
forecastle = walk(760, -248, DECK, 0.0, lambda z: z > BOW + 60, 'forecastle')


def into_quarters():
    """From the main deck, walk forward through the doorway under the forecastle into the crew's quarters."""
    begin, _ = walk(900, 0, DECK, 0.0, lambda z: True, 'quarters')

    def done():
        here, there = local_of(owner), local_of(pawn, peer)
        state['memo']['quarters'].update(server=[round(here.x), round(here.z)], client=[round(there.x), round(there.z)])
        inside = lambda p: p.x > 1150 and p.z < BOW
        if not (inside(here) and inside(there) and ship.is_aboard(owner) and peer.is_aboard(pawn)):
            return False
        state['input'] = None
        return True
    return begin, done


def into_cabin():
    """From the main deck, walk aft through the doorway under the raised deck until well inside the cabin."""
    begin, _ = walk(-760, 0, DECK, 180.0, lambda z: True, 'cabin')

    def done():
        here, there = local_of(owner), local_of(pawn, peer)
        state['memo']['cabin'].update(server=[round(here.x), round(here.z)], client=[round(there.x), round(there.z)])
        inside = lambda p: p.x < -1000 and p.z < RAISED
        if not (inside(here) and inside(there) and ship.is_aboard(owner) and peer.is_aboard(pawn)):
            return False
        state['input'] = None
        return True
    return begin, done
STEPS = [
    ('Bare brigantine, anchored, with 4 Large and 2 Small sail mounts and 24 cannon hardpoints', prepare, lambda: True, 2),
    ('Client installs a Large sail as the fore course', go('ForeCourse', large),
     lambda: ship.get_fitting('ForeCourse') == large and peer.get_fitting('ForeCourse') == large, 6),
    ('Client installs a Large sail as the gaff mainsail', go('Mainsail', large),
     lambda: ship.get_fitting('Mainsail') == large and peer.get_fitting('Mainsail') == large, 6),
    ('Client installs the wheel on the quarterdeck', go('Helm', helm),
     lambda: ship.get_fitting('Helm') == helm and peer.get_fitting('Helm') == helm, 6),
    ('Client raises the anchor', go('Anchor'), lambda: not ship.is_anchored() and not peer.is_anchored(), 6),
    ('Client takes the helm', go('Helm'), lambda: ship.get_helmsman() == owner and peer.get_helmsman() == pawn, 6),
    ('Forward input twice sets full sail', full_sail,
     lambda: ship.get_sail_state() == unreal.EWSailState.FULL and peer.get_sail_state() == unreal.EWSailState.FULL, 6),
    ('Shift with A or D trims the sails until they draw well', trim_sails, trimmed, 8),
    ('The brigantine sails for 4 s, smoothly every frame on server and client, and the client copy keeps up', begin_run, ran, 8),
    ('Client leaves the helm', leave, lambda: ship.get_helmsman() is None and peer.get_helmsman() is None, 6),
    ('Client drops the anchor', go('Anchor'), lambda: ship.is_anchored() and peer.is_anchored(), 6),
    # Under sail she runs out her chain's slack before it holds her (owner, October 16: the anchor's chain).
    ('She runs out her chain and stops, held by it', lambda: None, lambda: ship.get_speed() < 1, 45),
    ('Client walks down the hatch stairs to the gun deck', *down, 8),
    ('Client aims at a starboard cannon port from the gun deck', aim_cannon,
     lambda: str(ship.find_aimed_mount(owner)) == 'StarboardCannon7', 4),
    ('Client walks back up the stairs to the main deck', *up, 8),
    ("Client walks through the doorway into the captain's cabin under the quarterdeck", *into_cabin(), 8),
    ("Client walks through the doorway into the crew's quarters under the forecastle", *into_quarters(), 8),
    ('Client climbs the stairs to the quarterdeck', *raised, 8),
    ('Client climbs the stairs to the forecastle', *forecastle, 8),
    ('Client, swimming beside the hull, looks up at the stern ladder, takes hold and climbs aboard', climb_ladder, climbed, 14),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    m = state['memo']
    RESULT.write_text(json.dumps({
        'success': error is None, 'checks': checks, 'error': error,
        'run': {k: round(m[k]) for k in ('moved', 'gap') if k in m},
        'smoothness': m.get('smoothness'),
        'walks': {k: m[k] for k in ('down', 'up', 'cabin', 'quarters', 'raised', 'forecastle') if k in m},
        'client_local': str(local_of(pawn, peer)), 'server_local': str(local_of(owner)),
    }, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Brigantine success={error is None} error={error}')


def tick(delta):
    state['frame'] += 1
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
