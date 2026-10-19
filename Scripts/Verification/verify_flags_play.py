"""Client acceptance for ship flags (owner, October 17: sloop 2 flag positions, brigantine 3, Cavalier 4, all empty at
first; a crafted flag is plain clean white; flags install, remove and swap, flutter in the wind, and weather, fray and
tear only when damaged in combat, never from storms; no repair: destroyed fabric disappears while the pole remains, and
a replacement must be crafted). Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one
client, after build_flags.py and the hull scripts. Run unattended with run_play_check.py.

  1. The sloop has 2 flag mounts (bow jackstaff, stern ensign staff), the brigantine 3, the schooner 3; all empty, on both.
  2. The client hoists a white flag at the masthead halyard (on deck, the flag flies at the masthead): both agree.
  3. It streams downwind (the moored sloop feels the world's wind) on the client, and its cloth is drawn there.
  4. The client hoists a second at the ensign staff, lowers it (back to the inventory, unworn) and hoists it again.
  5. A round shot striking the bow wears both flags a little; one striking by the ensign tears it badly; on both.
  6. Nothing else wears a flag: half a minute of wind later the wear is unchanged.
  7. Taking down the torn ensign loses it (nothing comes back); a new flag goes up there unworn.
  8. Shot to pieces at the masthead, the flag is gone on both machines and nothing returns; its staff (the hull)
     remains and a new flag can go up.
Writes Saved/FlagsPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'FlagsPlayResult.json')
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
flag = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestFlagWhite')
assert flag, 'Run Scripts/Setup/build_flags.py first.'
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks, measured = [], {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'aim': None, 'at': 0.0}
MAST, ENSIGN = 'JackFlag', 'EnsignFlag'   # her bow jackstaff and stern ensign staff (the October 18 bare hull)


def count():
    return owner.get_inventory_component().get_item_count(flag)


def flag_mounts(definition):
    return [str(m.get_editor_property('mount_id')) for m in definition.get_editor_property('mounts')
            if m.get_editor_property('type') == unreal.EWShipMountType.FLAG]


def keep_aim():
    if not state['aim']:
        return
    target = ship.get_mount_world_transform(state['aim']).translation
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, target))


def at_halyard(mount):
    """On deck by the flag's halyard pin, a little inboard and aft of it, looking at it."""
    local = ship.get_actor_transform().inverse_transform_location(ship.get_mount_world_transform(mount).translation)
    # On the deck, inboard of the staff's foot: aft of the bow jackstaff, forward of the stern ensign staff.
    spot = ship.get_actor_transform().transform_location(unreal.Vector(local.x + (90 if mount == ENSIGN else -90), local.y * .4, local.z - 110 + 98))
    for p in (owner, pawn):
        assert p.teleport(spot, ship.get_actor_rotation()), f'no room to stand at {spot} by the {mount} halyard'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['aim'] = mount
    keep_aim()


def interact(mount):
    def begin():
        at_halyard(mount)
        state['at'] = time.monotonic()
    return begin


def send():
    assert lib.send_verification_interaction_request(client, peer), f'the request was refused (aimed on the server: {ship.find_aimed_mount(owner)})'


def visual(on, mount):
    return next((c for c in on.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith(f'Fitting_{mount}')), None)


def counts():
    defs = {n: unreal.load_asset(f'/Game/Elitewake/Ships/DA_Ship_{n}') for n in ('Sloop', 'Schooner', 'Brigantine')}
    found = {n: flag_mounts(d) for n, d in defs.items()}
    measured['flag_mounts'] = found
    assert sorted(found['Sloop']) == sorted([MAST, ENSIGN]), found['Sloop']
    assert len(found['Brigantine']) == 3 and len(found['Schooner']) == 3, found
    for s in (ship, peer):
        assert all(s.get_flag_wear(m) == -1 for m in found['Sloop']), 'a flag flies already'
    assert not any(f.mount_id in (MAST, ENSIGN) for f in peer.get_installed_fittings())
    assert owner.get_inventory_component().add_item(flag, 3) == 3
    return True


def hoisted(mount, inventory_after):
    def done():
        keep_aim()
        if time.monotonic() - state['at'] < .3:
            return False
        if state.get('sent') != (mount, state['at']):
            send()
            state['sent'] = (mount, state['at'])
            return False
        if not (ship.get_fitting(mount) == flag and peer.get_fitting(mount) == flag):
            return False
        assert count() == inventory_after, f'{count()} flags carried, expected {inventory_after}'
        assert ship.get_flag_wear(mount) == 0 and peer.get_flag_wear(mount) == 0, 'a new flag is worn'
        v = visual(peer, mount)
        assert v and v.is_visible() and v.get_editor_property('static_mesh'), f'no flag drawn at {mount} on the client'
        deck = ship.get_actor_location().z + ship.get_deck_height()
        measured[f'{mount}_height_m'] = round((v.get_world_location().z - deck) / 100, 1)
        if mount == MAST:
            assert v.get_world_location().z - deck > 250, f'the masthead flag flies only {(v.get_world_location().z - deck) / 100:.1f} m up'
        return True
    return done


def downwind():
    if time.monotonic() - state['at'] < 3.0:
        return False
    wind = unreal.EWWindSubsystem.get_for_world(client_world)
    want = wind.get_wind_yaw()
    got = peer.get_flag_yaw(MAST)
    drawn = visual(peer, MAST).get_world_rotation().yaw
    diff = lambda a, b: abs((a - b + 180) % 360 - 180)
    measured.update(wind_yaw=round(want, 1), flag_yaw=round(got, 1), drawn_yaw=round(drawn, 1))
    assert diff(want, got) < 8, f'the flag streams to {got:.0f}, the wind blows to {want:.0f}'
    assert diff(got, drawn) < 2, f'the flag is drawn at {drawn:.0f}, not {got:.0f}'
    return True


def lowered():
    keep_aim()
    if state.get('sent') != ('lower', state['at']):
        send()
        state['sent'] = ('lower', state['at'])
        return False
    if ship.get_fitting(ENSIGN) or peer.get_fitting(ENSIGN):
        return False
    assert count() == 2, f'the lowered (unworn) flag did not come back: {count()} carried'
    return True


def shoot(local, near=None):
    def begin():
        where = ship.get_actor_transform().transform_location(unreal.Vector(*local)) if near is None else visual(ship, near).get_world_location()
        state['before'] = {m: ship.get_flag_wear(m) for m in (MAST, ENSIGN)}
        ship.take_round_shot(where, ship.get_actor_right_vector(), None)
        state['at'] = time.monotonic()
    return begin


def worn(expect):
    def done():
        now = {m: (ship.get_flag_wear(m), peer.get_flag_wear(m)) for m in (MAST, ENSIGN)}
        for m, add in expect.items():
            want = min(1.0, state['before'][m] + add) if state['before'][m] >= 0 else -1
            if want >= 1.0:
                want = -1   # destroyed: gone
            if abs(now[m][1] - want) > .01:
                return False
            assert abs(now[m][0] - want) < .01, (m, now[m], want)
        measured.setdefault('wear', []).append({m: round(v[1], 2) for m, v in now.items()})
        return True
    return done


def no_storm_wear():
    if time.monotonic() - state['at'] < 30.0:
        return False
    for m in (MAST, ENSIGN):
        assert abs(peer.get_flag_wear(m) - state['before_wait'][m]) < 1e-4, f'{m} wore without combat'
    return True


def torn_lost():
    keep_aim()
    if state.get('sent') != ('torn', state['at']):
        state['carried'] = count()
        send()
        state['sent'] = ('torn', state['at'])
        return False
    if ship.get_fitting(ENSIGN) or peer.get_fitting(ENSIGN):
        return False
    assert count() == state['carried'], 'the torn flag came back to the inventory'
    return True


def destroyed():
    if ship.get_fitting(MAST) or peer.get_fitting(MAST):
        return False
    assert count() == state['carried_before_shot'], 'something came back when the flag was destroyed'
    assert ship.is_mount_open(MAST), 'the masthead staff no longer takes a flag'
    return True


def remember_wait():
    state['before_wait'] = {m: peer.get_flag_wear(m) for m in (MAST, ENSIGN)}
    state['at'] = time.monotonic()


def remember_carried():
    state['carried_before_shot'] = count()


BOW = (0.0, 210.0, 100.0)   # the hull's starboard side amidships, far from both flags (more than 5 m)
STEPS = [
    ('The sloop has 2 flag mounts (masthead, ensign), the schooner and brigantine 3; all empty; 3 flags granted', lambda: None, counts, 5),
    ('The client hoists a white flag at the masthead halyard: it flies at the masthead on both', interact(MAST), hoisted(MAST, 2), 8),
    ('It streams downwind of the wind felt aboard on the client', lambda: state.update(at=time.monotonic()), downwind, 8),
    ('The client hoists a second at the ensign staff', interact(ENSIGN), hoisted(ENSIGN, 1), 8),
    ('Lowered, the unworn ensign comes back to the inventory', interact(ENSIGN), lowered, 8),
    ('Hoisted again, a swap', interact(ENSIGN), hoisted(ENSIGN, 1), 8),
    ('A round shot at the bow wears both flags a little, on both machines', shoot(BOW), worn({MAST: .12, ENSIGN: .12}), 6),
    ('A round shot by the ensign tears it badly', shoot(None, ENSIGN), worn({MAST: .12, ENSIGN: .57}), 6),
    ('Nothing but combat wears a flag: half a minute later the wear is unchanged', remember_wait, no_storm_wear, 40),
    ('Taking down the torn ensign loses it: nothing comes back', interact(ENSIGN), torn_lost, 8),
    ('A new flag goes up at the ensign staff, unworn', interact(ENSIGN), hoisted(ENSIGN, 0), 8),
    ('Two shots by the masthead flag shred it', shoot(None, MAST), worn({MAST: .57, ENSIGN: .12}), 6),
    ('Shot to pieces: the masthead flag is gone on both, nothing returns, its staff still takes a flag',
     lambda: (remember_carried(), shoot(None, MAST)()), destroyed, 6),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Flags success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; wear {ship.get_flag_wear(MAST):.2f}/{ship.get_flag_wear(ENSIGN):.2f}, '
                               f'aimed {ship.find_aimed_mount(owner)}, carried {count()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
