"""Client acceptance for trimming sails to the wind, and for the compass, on the sloop.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the sloop.
Run unattended with run_play_check.py.

The sloop is fitted out (helm, mainsail and headsail, full sail) and stays anchored, so it holds its heading.
The server turns the wind to blow across the sloop from port. Through its own keys, the client:
  1. at the helm, reads the wind on its compass where it blows from, and the trim readout telling it to trim
     to starboard, with the sails still along the centreline,
  2. holds Shift and D: the sails swing out to starboard on server and client (drawn swung too), the rudder
     stays centred, and once they draw well the wind's share of speed has risen,
  3. holds Shift and A past the centreline to the wrong side: the sails draw badly and the wind's share falls
     back to the least any sail gives,
  4. lets go of Shift: D alone puts the rudder over again;
  5. holds the Right Arrow (owner, October 16: helm-only sail keys): the sails swing to starboard, out to the full
     90 degrees of their 180-degree range, the rudder staying where it was;
  6. holds LB (the controller's left shoulder): they swing back to port, past the centreline;
  7. leaves the helm: the Left Arrow then does nothing to the sails.
Along the way (owner, October 16: sails fill when they catch the wind, go slack when they don't), the client's own
sails are drawn filled while they draw well (fill over 0.8, AEWShip::GetSailFill), and slack (under 0.2) once swung
out to 90 degrees, edge-on to the wind.
Writes Saved/SailTrimPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SailTrimPlayResult.json')
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
peer = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if a.get_name() == ship.get_name())
folder = '/Game/Elitewake/Items/Testing'
items = [unreal.load_asset(f'{folder}/{n}') for n in ('DA_TestShipHelm', 'DA_TestSailMedium', 'DA_TestSailSmall')]
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': False}
KEYS = ('LeftShift', 'A', 'D', 'Right', 'Left', 'Gamepad_LeftShoulder', 'Gamepad_RightShoulder')


def wind_of(world):
    return unreal.EWWindSubsystem.get_for_world(world)


def compass():
    widget = next((w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWCompassWidget, False)
                   if w.get_owning_player() == client), None)
    assert widget, 'no compass on the client screen'
    return widget


def keys(**down):
    for key in KEYS:
        lib.send_verification_gameplay_key_state(client, key, bool(down.get(key, False)))


def keep_aim():
    if not state['aim']:
        return
    helm = ship.get_mount_world_transform('Helm').translation
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, helm))


def bearing(yaw):
    return yaw % 360.0


def angle_gap(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def fit_out():
    for item in items:
        assert item and owner.get_inventory_component().add_item(item, 1) == 1
    assert lib.fit_out_ship_for_review(ship, owner, 2) == 3
    # Wind across the sloop from port: it blows toward starboard, so the sails belong out to starboard.
    wind_of(server_world).set_wind_yaw(ship.get_actor_rotation().yaw + 90.0)
    helm = ship.get_mount_world_transform('Helm').translation
    forward = ship.get_actor_forward_vector()
    spot = unreal.Vector(helm.x + forward.x * 110, helm.y + forward.y * 110, helm.z - 50 + 98)   # on the helm's own deck
    for p in (owner, pawn):
        assert p.teleport(spot, ship.get_actor_rotation())
    state['aim'] = True
    state['memo']['t'] = time.monotonic()


def fitted():
    return time.monotonic() - state['memo']['t'] > 0.5 and all(peer.get_fitting(m) for m in ('Helm', 'Mainsail', 'Headsail'))


def take_helm():
    assert lib.send_verification_interaction_request(client, peer)


def at_helm():
    if not (ship.get_helmsman() == owner and pawn.get_helm_ship() == peer):
        return False
    state['aim'] = False
    state['memo']['t'] = time.monotonic()
    return True


def compass_reads_wind():
    if time.monotonic() - state['memo']['t'] < 1.0:
        return False
    c = compass()
    expected_from = bearing(ship.get_actor_rotation().yaw + 90.0 + 180.0)
    client_wind = wind_of(client_world).get_wind_yaw()
    if angle_gap(client_wind, ship.get_actor_rotation().yaw + 90.0) > 1.0:
        return False  # the wind has not reached the client yet
    assert angle_gap(c.get_wind_from(), expected_from) < 1.0, f'compass wind from {c.get_wind_from()}, expected {expected_from}'
    assert c.is_showing_trim(), 'no trim readout at the helm'
    assert abs(ship.get_sail_angle()) < 0.5, f'sails start at {ship.get_sail_angle()}'
    assert c.get_trim_advice().startswith('Trim to starboard'), c.get_trim_advice()
    assert abs(ship.get_best_sail_angle() - 45.0) < 1.0, f'best angle {ship.get_best_sail_angle()}'
    state['memo'].update(advice_before=c.get_trim_advice(), quality_before=round(ship.get_trim_quality(), 2),
                         factor_before=round(ship.get_wind_factor(), 3), heading=round(c.get_heading(), 1),
                         ship_yaw=round(peer.get_actor_rotation().yaw, 1), view_yaw=round(client.get_control_rotation().yaw, 1))
    return True


def trim_out():
    keys(LeftShift=True, D=True)


def drawing_well():
    assert abs(ship.get_rudder()) < 0.01, f'rudder moved to {ship.get_rudder()} while trimming'
    if ship.get_trim_quality() < 0.97:
        return False
    keys()
    return True


def settled_well():
    angle = ship.get_sail_angle()
    if abs(peer.get_sail_angle() - angle) > 1.0:
        return False
    sail = next((c for c in peer.get_components_by_class(unreal.StaticMeshComponent) if 'Fitting_Mainsail' in c.get_name()), None)
    assert sail, 'no mainsail drawn on the client'
    drawn = sail.get_editor_property('relative_rotation').yaw
    # The sloop's assemblies sit a quarter turn on their mounts (a fore-and-aft yard at zero trim), the look's 90 degrees.
    if angle_gap(drawn, -angle + 90.0) > 3.0:
        return False
    c = compass()
    assert c.get_trim_advice() == 'Sails drawing well', c.get_trim_advice()
    fills = {m: round(peer.get_sail_fill(m), 2) for m in ('Mainsail', 'Headsail')}
    if min(abs(v) for v in fills.values()) < 0.8:
        return False   # the cloth fills over about a second
    state['memo']['fill_well'] = fills
    factor = ship.get_wind_factor()
    # Trimmed well beats untrimmed by a fifth or more (less than before the higher floor of the faster crossings).
    assert factor > state['memo']['factor_before'] * 1.2, f'wind factor {factor} not above {state["memo"]["factor_before"]}'
    state['memo'].update(angle_well=round(angle, 1), drawn_yaw=round(drawn, 1), factor_well=round(factor, 3))
    return True


def trim_wrong():
    keys(LeftShift=True, A=True)


def drawing_badly():
    if ship.get_sail_angle() > -40.0:
        return False
    keys()
    factor = ship.get_wind_factor()
    assert ship.get_trim_quality() < 0.1, f'quality {ship.get_trim_quality()}'
    assert factor < 0.47, f'wind factor {factor}'   # the floor, 0.45 since the faster crossings
    assert compass().get_trim_advice().startswith('Trim to starboard'), compass().get_trim_advice()
    state['memo'].update(angle_wrong=round(ship.get_sail_angle(), 1), factor_wrong=round(factor, 3))
    return True


def steer():
    keys(D=True)
    state['memo']['angle_held'] = ship.get_sail_angle()


def steering():
    if ship.get_rudder() < 0.9:
        return False
    keys()
    assert abs(ship.get_sail_angle() - state['memo']['angle_held']) < 0.5, 'the sails moved without Shift'
    return True


def arrow_right():
    keys(Right=True)
    state['memo'].update(t=time.monotonic(), rudder_held=ship.get_rudder())


def full_starboard():
    if ship.get_sail_angle() < 89.5:
        return False
    keys()
    # D was let go just before: the rudder centres; the arrows must not put it over.
    assert abs(ship.get_rudder()) < 0.05, f'the rudder is at {ship.get_rudder()} with only the arrow held'
    state['memo'].update(arrow_full=round(ship.get_sail_angle(), 1), arrow_full_client=round(peer.get_sail_angle(), 1),
                         arrow_seconds=round(time.monotonic() - state['memo']['t'], 1))
    return True


def watch_slack():
    state['memo']['t'] = time.monotonic()


def slack_at_90():
    fill = peer.get_sail_fill('Mainsail')
    state['memo']['fill_at_90'] = round(fill, 2)
    return abs(fill) < 0.2


def shoulder_left():
    keys(Gamepad_LeftShoulder=True)
    state['memo'].update(t=time.monotonic(), lb_start=ship.get_sail_angle(), via='LB')


def back_to_port():
    m = state['memo']
    # If the injected LB press has not moved the sails in 2 s, try the Left Arrow (same action) and record that LB
    # still wants a real controller to confirm it.
    if m['via'] == 'LB' and time.monotonic() - m['t'] > 2.0 and ship.get_sail_angle() > m['lb_start'] - 5.0:
        keys(Left=True)
        m['via'] = 'Left Arrow (the injected LB press did not arrive)'
    if ship.get_sail_angle() > -10.0:
        return False
    keys()
    m['port_angle'] = round(ship.get_sail_angle(), 1)
    m['port_via'] = m['via']
    return True


def leave_helm():
    assert lib.send_verification_interaction_request(client, peer)
    state['memo']['t'] = time.monotonic()


def arrows_dead():
    m = state['memo']
    if 'held_angle' not in m:
        if ship.get_helmsman() is not None or pawn.get_helm_ship() is not None:
            return False
        keys(Left=True)
        m.update(held_angle=ship.get_sail_angle(), t=time.monotonic())
        return False
    if time.monotonic() - m['t'] < 1.5:
        return False
    keys()
    assert abs(ship.get_sail_angle() - m['held_angle']) < 0.5, f'the sails moved from the arrows away from the helm: {ship.get_sail_angle()}'
    return True


STEPS = [
    ('The sloop is fitted out with full sail at anchor; the wind blows across it from port', fit_out, fitted, 4),
    ('The client takes the helm', take_helm, at_helm, 6),
    ('The compass shows the wind where it blows from; the trim readout says to trim to starboard', lambda: None, compass_reads_wind, 4),
    ('Holding Shift and D swings the sails out to starboard until they draw well; the rudder stays centred', trim_out, drawing_well, 6),
    ('The client sees the sails swung on its screen, "Sails drawing well", and the wind gives more speed', lambda: None, settled_well, 4),
    ('Shift and A swing them to the wrong side: they draw badly and the wind gives the least', trim_wrong, drawing_badly, 8),
    ('Without Shift, D puts the rudder over and leaves the sails where they are', steer, steering, 4),
    ('The Right Arrow swings the sails to starboard, out to 90 degrees, the rudder centred', arrow_right, full_starboard, 8),
    ("Swung out to 90 degrees, edge-on to the wind, the client's mainsail goes slack", watch_slack, slack_at_90, 5),
    ('LB (or the Left Arrow) swings them back to port past the centreline', shoulder_left, back_to_port, 10),
    ('Away from the helm the arrow keys do nothing to the sails', leave_helm, arrows_dead, 8),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    keys()
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': state['memo']},
                                 indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK SailTrim success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; sail angle {ship.get_sail_angle():.1f}, '
                               f'quality {ship.get_trim_quality():.2f}, rudder {ship.get_rudder():.2f}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
