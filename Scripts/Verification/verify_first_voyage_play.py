"""Client acceptance for the First Voyage: one coastal session, end to end, as a tester plays it.

Needs Play in /Game/Elitewake/Maps/Test/Lvl_ShipsTest (the island map has no boats since October 14) as a listen server plus one client, with the test starter
kit. Run unattended with run_play_check.py. The title's way onto this map is verify_title_to_coast_play.

Through ordinary owned requests and keys, the client:
  1. arrives on the beach carrying the starter kit, with the sloop's fittings stowed in its hold;
  2. equips the wooden axe and fells Wood and Thatch from an oak;
  3. swims to the moored sloop, takes hold of its ladder and climbs aboard with Up;
  4. opens the hold at the hatch, takes out the helm, the mainsail and the headsail, and closes it with I;
  5. fits all three, raises the anchor at the capstan, takes the helm, sets full sail and trims to the wind;
  6. sails for 4 s, leaves the helm and drops the anchor;
  7. goes over the side, fights a manta ray with the axe in hand until it dies, carries its body ashore and
     harvests it there for 6 to 10 Raw Fish.
Each step waits for its result on the server and on the client's copy, with a timeout.
Writes Saved/FirstVoyagePlayResult.json.
"""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'FirstVoyagePlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
# Crew dependency (owner, October 18): the helm sets only sails with a hired sailhand, so every ship here is crewed first.
for _s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip):
    _s.crew_every_sail()
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop')
peer = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if s.get_name() == ship.get_name())
T = '/Game/Elitewake/Items/Testing'
axe, wood, thatch, helm, mainsail, headsail = (unreal.load_asset(f'{T}/DA_Test{n}') for n in
                                               ('WoodenAxe', 'Wood', 'Thatch', 'ShipHelm', 'SailMedium', 'SailSmall'))
raw_fish = unreal.load_asset('/Game/Elitewake/Items/Food/DA_RawFish')
FITTINGS = (('Helm', helm), ('Mainsail', mainsail), ('Headsail', headsail))
LADDER = 0   # the stern ladder (owner, October 16: one ladder, centred on the stern)
palms = [t for t in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarvestTree)
         if t.get_actor_label().startswith('Oak')]
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None, 'input': None, 'frame': 0}


def count(who, item):
    return who.get_inventory_component().get_item_count(item)


def movement(who):
    return who.get_component_by_class(unreal.CharacterMovementComponent)


def put(spot, rotation=None):
    for p in (owner, pawn):
        assert p.teleport(spot, rotation or ship.get_actor_rotation()), f'no room at {spot}'
        movement(p).stop_movement_immediately()


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def keys(**down):
    for key in ('LeftShift', 'A', 'D', 'Up'):
        lib.send_verification_gameplay_key_state(client, key, bool(down.get(key, False)))


def on_deck(spot_x, spot_y, aim, deck_z=None):
    """Stand on the sloop's deck at (x, y) in its frame (on the deck at deck_z, the main deck by default), looking at
    `aim` (a function giving a world point)."""
    at = ship.get_actor_transform().transform_location(unreal.Vector(spot_x, spot_y, (ship.get_deck_height() if deck_z is None else deck_z) + 98))
    put(at)
    state['aim'] = aim
    keep_aim()


def settled(seconds):
    return time.monotonic() - state['memo'].get('t', 0) >= seconds


# 1. Arrival -------------------------------------------------------------------------------------------------

def to_beach():
    put(unreal.Vector(150, 0, 190), unreal.Rotator())
    state['memo']['t'] = time.monotonic()


def arrived():
    if not settled(0.5) or movement(owner).is_falling():
        return False
    assert count(owner, axe) >= 1 and count(pawn, axe) >= 1, 'no starter axe on server and client'
    cargo = ship.get_cargo()
    stowed = {mount: cargo.get_item_count(item) for mount, item in FITTINGS}
    assert all(stowed.values()), f"the sloop's hold lacks fittings: {stowed}"
    assert not ship.get_installed_fittings() and ship.is_anchored() and peer.is_anchored(), 'the sloop must start bare and anchored'
    state['memo'].update(stowed=stowed)
    return True


# 2. Gather --------------------------------------------------------------------------------------------------

def equip():
    assert lib.send_verification_equipment_request(client, axe, unreal.EWEquipmentSlot.MAIN_HAND)


def equipped():
    return owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) == axe


def to_palm():
    tree = min(palms, key=lambda t: (t.get_actor_location() - unreal.Vector(150, 0, 0)).length())
    base = tree.get_actor_location()
    away = unreal.Vector(150 - base.x, -base.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = base + away * 130 + unreal.Vector(0, 0, 110)
    look = unreal.MathLibrary.find_look_at_rotation(spot + unreal.Vector(0, 0, 60), base + unreal.Vector(0, 0, 120))
    put(spot, unreal.Rotator(yaw=look.yaw))
    client.set_control_rotation(look)
    owner.get_controller().set_control_rotation(look)
    state['memo'].update(tree=tree, t=time.monotonic(), gathered_from=(count(owner, wood), count(owner, thatch)), struck=False)


def gathered():
    m = state['memo']
    if not m['struck']:
        if not settled(0.8):
            return False
        assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')
        m['struck'] = True
        return False
    w0, t0 = m['gathered_from']
    got = (count(owner, wood) - w0, count(owner, thatch) - t0)
    seen = (count(pawn, wood) - w0, count(pawn, thatch) - t0)
    if got != (3, 1) or seen != got:
        return False
    m['gathered'] = got
    return True


# 3. Board ---------------------------------------------------------------------------------------------------

def swim_to_ladder():
    state['aim'] = None
    ladder = ship.get_boarding_point_world(LADDER)
    out = ship.get_actor_forward_vector() * -1.0   # the ladder is centred on the stern, facing aft
    put(unreal.Vector(ladder.x + out.x * 120, ladder.y + out.y * 120, ship.get_actor_location().z - 60))
    state['aim'] = lambda: ship.get_boarding_point_world(LADDER) + unreal.Vector(0, 0, 150)
    state['memo'].update(t=time.monotonic(), pressed=False, climbing=False)


def climbed_aboard():
    m = state['memo']
    if not m['pressed']:
        if not settled(0.8):
            return False
        assert lib.send_verification_gameplay_key(client, 'E')
        m['pressed'] = True
        return False
    if owner.is_on_ladder() and not m['climbing']:
        state['aim'] = None
        keys(Up=True)
        m['climbing'] = True
    if owner.is_on_ladder() or not (ship.is_aboard(owner) and peer.is_aboard(pawn)):
        return False
    keys()
    return True


# 4. The hold ------------------------------------------------------------------------------------------------

def open_hold():
    hatch = ship.get_cargo_hatch_world()
    local = ship.get_actor_transform().inverse_transform_location(hatch)
    on_deck(local.x + 140, local.y, lambda: ship.get_cargo_hatch_world())
    state['memo'].update(t=time.monotonic(), pressed=False)


def hold_open():
    m = state['memo']
    if not m['pressed']:
        if not settled(0.5):
            return False
        assert lib.send_verification_interaction_request(client, peer)
        m['pressed'] = True
        m['t'] = time.monotonic()
        return False
    # The hold's screen opens on the client once the 0.75 s hold completes.
    return client.get_open_container() == peer


def take_fittings():
    state['aim'] = None
    state['memo']['sent_at'] = 0.0


def fittings_carried():
    """One stack at a time, each found where it now lies in the hold (taking one out moves the rest up)."""
    missing = [item for _, item in FITTINGS if count(owner, item) < 1 or count(pawn, item) < 1]
    if not missing:
        return True
    if time.monotonic() - state['memo']['sent_at'] > 0.5:
        entries = peer.get_cargo().get_inventory_entries()
        index = next((i for i, e in enumerate(entries) if e.get_editor_property('item_definition') == missing[0]), -1)
        if index >= 0:
            assert lib.send_verification_container_transfer(client, peer, False, index, 1)
            state['memo']['sent_at'] = time.monotonic()
    return False


def close_hold():
    assert lib.send_verification_gameplay_key(client, 'I')


def hold_closed():
    return client.get_open_container() is None and not client.is_inventory_open()


# 5-6. Fit out and sail --------------------------------------------------------------------------------------

def mount_world(name):
    return ship.get_anchor_point_world() if name == 'Anchor' else ship.get_mount_world_transform(name).translation


def work(name):
    """Stand within reach of the mount (or the capstan) and hold Interact there."""
    def begin():
        local = ship.get_actor_transform().inverse_transform_location(mount_world(name))
        off = {'Helm': 110, 'Mainsail': 110}.get(name, -120)
        # On the deck the mount stands on (mounts sit 50 cm above it; her helm is on the raised stern deck).
        on_deck(local.x + off, local.y if name == 'Anchor' else 0.0, lambda: mount_world(name), None if name == 'Anchor' else local.z - 50)
        assert lib.send_verification_interaction_request(client, peer)
        state['memo']['t'] = time.monotonic()
    return begin


def fitted(name, item):
    return lambda: ship.get_fitting(name) == item and peer.get_fitting(name) == item


def anchor_up():
    if ship.is_anchored() or peer.is_anchored():
        return False
    state['memo']['anchor_seconds'] = round(time.monotonic() - state['memo']['t'], 1)
    return True


def at_helm():
    return ship.get_helmsman() == owner and peer.get_helmsman() == pawn and client.get_controlled_pawn() == pawn


def full_sail():
    state['aim'] = None
    state['memo']['frame0'] = state['frame']
    state['input'] = lambda f: pawn.do_move(0, 1) if any(start <= f < start + 5 for start in (0, 10, 20, 30)) else pawn.do_move(0, 0)


def sails_full():
    return ship.get_sail_state() == unreal.EWSailState.FULL and peer.get_sail_state() == unreal.EWSailState.FULL


def trim():
    state['input'] = None
    side = 'D' if ship.get_best_sail_angle() > ship.get_sail_angle() else 'A'
    keys(LeftShift=True, **{side: True})


def trimmed():
    if ship.get_trim_quality() < .9:
        return False
    keys()
    state['memo'].update(start=ship.get_actor_location(), t=time.monotonic())
    return True


def sailed():
    m = state['memo']
    if not settled(4.0):
        return False
    moved = (ship.get_actor_location() - m['start']).length()
    gap = (ship.get_actor_location() - peer.get_actor_location()).length()
    m.update(sailed=round(moved), gap=round(gap), speed=round(ship.get_speed()))
    assert moved > 300, f'sailed only {moved:.0f} cm'
    assert gap < 400, f"the client's copy is {gap:.0f} cm from the server's"
    return True


def leave_helm():
    assert lib.send_verification_interaction_request(client, peer)


def left_helm():
    return ship.get_helmsman() is None and peer.get_helmsman() is None and pawn.get_helm_ship() is None


def anchored_again():
    m = state['memo']
    # Interaction is a hold: on a ship still running before the wind, the survivor's aim can slip off the capstan and
    # the hold is cancelled, where a player would keep holding E. Until the anchor is down, stand at the capstan again
    # and hold once more every 4 s (longer than the 3 s hold, so a hold in progress is never cut short).
    if not ship.is_anchored():
        if time.monotonic() - m['t'] > 4.0:
            m['anchor_presses'] = m.get('anchor_presses', 1) + 1
            work('Anchor')()
        return False
    return peer.is_anchored() and ship.get_speed() < 1


# 7. Fish ------------------------------------------------------------------------------------------------------

def manta():
    # The one nearest the sloop: the bigger world has mantas off every region's islands, most far beyond the client's reach.
    rays = [f for f in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWFish)
            if str(f.get_editor_property('definition').get_editor_property('display_name')) == 'Manta Ray' and not f.is_dead()]
    return min(rays, key=lambda f: (f.get_actor_location() - ship.get_actor_location()).length())


def copy_of(fish):
    return next(f for f in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWFish) if f.get_name() == fish.get_name())


def over_the_side():
    target = manta()
    state['memo'].update(manta=target, swing_at=0.0, health0=target.get_health())
    state['aim'] = lambda: state['memo']['manta'].get_actor_location()


def follow_manta():
    target = state['memo']['manta']
    at, side = target.get_actor_location(), target.get_actor_right_vector()
    for p in (owner, pawn):
        p.set_actor_location(unreal.Vector(at.x + side.x * 120, at.y + side.y * 120, at.z - 30), False, True)


def manta_dead():
    m = state['memo']
    target = m['manta']
    if not target.is_dead():
        follow_manta()
        keep_aim()   # from where the swimmer is now, not where it was before following the ray
        owner.get_survival_component().restore_health(100)   # its sting must not end the check
        if time.monotonic() >= m['swing_at']:
            m['swing_at'] = time.monotonic() + 1.1
            assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')
        return False
    return copy_of(target).is_dead()


def press_e_every(seconds):
    if time.monotonic() - state['memo'].get('pressed', 0.0) > seconds:
        state['memo']['pressed'] = time.monotonic()
        assert lib.send_verification_gameplay_key(client, 'E')


def to_body():
    target = state['memo']['manta']
    at = target.get_actor_location()
    for p in (owner, pawn):
        p.set_actor_location(unreal.Vector(at.x - 150, at.y, at.z - 20), False, True)
    state['memo'].update(fish_before=count(owner, raw_fish), pressed=0.0)


def picked_up():
    target = state['memo']['manta']
    if target.get_carrier() != owner:
        press_e_every(1.0)
        return False
    return copy_of(target).get_carrier() == pawn


def ashore():
    state['aim'] = None
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(150, 0, 190), unreal.Rotator())
    state['memo'].update(pressed=time.monotonic() - 4.0)


def set_down():
    target = state['memo']['manta']
    if not target.is_on_land():
        press_e_every(1.5)
        return False
    if not copy_of(target).is_on_land():
        return False
    state['aim'] = lambda: state['memo']['manta'].get_actor_location()
    state['memo']['pressed'] = 0.0
    return True


def harvested():
    m = state['memo']
    target = m['manta']
    if not target.is_harvested():
        press_e_every(1.0)
        return False
    gained = count(owner, raw_fish) - m['fish_before']
    if not (copy_of(target).is_harvested() and gained > 0 and count(pawn, raw_fish) == count(owner, raw_fish)):
        return False
    assert 6 <= gained <= 10, f'a manta ray gave {gained} Raw Fish; it should give 6 to 10'
    m['raw_fish'] = gained
    return True


STEPS = [
    ('The client arrives on the beach carrying the starter kit; the bare, anchored sloop has its fittings in the hold', to_beach, arrived, 6),
    ('It equips the wooden axe', equip, equipped, 6),
    ('It fells 3 Wood and 1 Thatch from an oak with Left Mouse, on server and client', to_palm, gathered, 6),
    ("It swims to the sloop's ladder, takes hold with E and climbs aboard with Up", swim_to_ladder, climbed_aboard, 14),
    ('It opens the hold at the hatch', open_hold, hold_open, 6),
    ('It takes the helm, the mainsail and the headsail out of the hold', take_fittings, fittings_carried, 6),
    ('I closes the hold screen', close_hold, hold_closed, 4),
    ('It fits the helm', work('Helm'), fitted('Helm', helm), 6),
    ('It fits the mainsail', work('Mainsail'), fitted('Mainsail', mainsail), 6),
    ('It fits the headsail', work('Headsail'), fitted('Headsail', headsail), 6),
    ('It raises the anchor at the capstan', work('Anchor'), anchor_up, 8),
    ('It takes the helm', work('Helm'), at_helm, 6),
    ('Four forward taps set full sail', full_sail, sails_full, 6),
    ('Shift with A or D trims the sails to the wind', trim, trimmed, 8),
    ('The sloop sails for 4 s and the client keeps up', lambda: None, sailed, 8),
    ('It leaves the helm', leave_helm, left_helm, 6),
    # Under sail she runs out her chain's slack before it snubs her up (owner, October 16).
    ('It drops the anchor and the sloop stops, held by her chain', work('Anchor'), anchored_again, 45),
    ('Over the side, it fights a manta ray with the axe in hand until the ray dies, on server and client', over_the_side, manta_dead, 75),
    ('E at the floating body picks it up', to_body, picked_up, 6),
    ('Carried ashore, E sets it down on the beach', ashore, set_down, 6),
    ('E at it on land harvests 6 to 10 Raw Fish', lambda: None, harvested, 6),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    keys()
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = ('stowed', 'gathered', 'anchor_seconds', 'sailed', 'gap', 'speed', 'raw_fish')
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error,
                                  'measured': {k: state['memo'][k] for k in keep if k in state['memo']}}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK FirstVoyage success={error is None} error={error}')


def tick(delta):
    state['frame'] += 1
    if state['input']:
        state['input'](state['frame'] - state['memo'].get('frame0', 0))
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
            m = state['memo']
            seen = {k: (round(v.get_health(), 1), v.is_dead(), round((v.get_actor_location() - pawn.get_actor_location()).length()))
                    if k == 'manta' else v for k, v in m.items() if k == 'manta' or isinstance(v, (int, float, str, bool, tuple))}
            raise TimeoutError(f'not done within {timeout} s; memo {seen}; swimming {pawn.get_component_by_class(unreal.CharacterMovementComponent).is_swimming()}; '
                               f'holding {owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
