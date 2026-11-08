"""Client acceptance for climbing a ship's ladder and for the ship markers, on the sloop.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the sloop.
Run unattended with run_play_check.py.

Through its own keys, as a player presses them, the client:
  1. swims beside the sloop's stern ladder: its markers label the ladder (larger when aimed at) and the anchor,
  2. presses E once and takes hold of the ladder (no hold needed), on server and client,
  3. holds the Up arrow and climbs; at the top it steps onto the deck, aboard on both machines,
  4. on deck, its markers label the wheel mount, the sail mounts with their sizes, the hold and the anchor; given
     a Small sail, the Small sail mount turns to "Fit Small sail here",
  5. back in the water, takes hold of the ladder again, holds the Down arrow and lets go into the sea at its foot.
Writes Saved/LadderPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'LadderPlayResult.json')
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
small = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestSailSmall')
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None}
LADDER = 0   # the stern ladder (owner, October 16: one ladder, centred on the stern)


def markers():
    widget = next((w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWShipMarkersWidget, False)
                   if w.get_owning_player() == client), None)
    assert widget, 'no ship markers on the client screen'
    return list(widget.get_markers())


def labels():
    return [str(m.get_editor_property('label')) for m in markers()]


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def swim_beside_ladder():
    state['aim'] = None
    for key in ('Up', 'Down'):
        lib.send_verification_gameplay_key_state(client, key, False)
    ladder = ship.get_boarding_point_world(LADDER)
    out = ship.get_actor_forward_vector() * -1.0   # the ladder is centred on the stern, facing aft
    spot = unreal.Vector(ladder.x + out.x * 120, ladder.y + out.y * 120, ship.get_actor_location().z - 60)
    for p in (owner, pawn):
        assert p.teleport(spot, ship.get_actor_rotation())
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['aim'] = lambda: ship.get_boarding_point_world(LADDER) + unreal.Vector(0, 0, 150)
    state['memo']['t'] = time.monotonic()


def ladder_marked():
    if time.monotonic() - state['memo']['t'] < 1.0:
        return False
    found = [m for m in markers() if str(m.get_editor_property('label')) == 'Ladder']
    if not any(m.get_editor_property('aimed') for m in found):
        return False
    assert any(l.startswith('Anchor') for l in labels()), labels()
    state['memo']['outside'] = labels()
    return True


def press_e():
    assert lib.send_verification_gameplay_key(client, 'E')


def holding():
    return owner.is_on_ladder() and pawn.is_on_ladder()


def climb_up():
    state['aim'] = None
    state['memo'].update(t=time.monotonic())
    assert lib.send_verification_gameplay_key_state(client, 'Up', True)


def on_deck():
    if owner.is_on_ladder() or pawn.is_on_ladder():
        return False
    local = ship.get_actor_transform().inverse_transform_location(owner.get_actor_location())
    if not (ship.is_aboard(owner) and peer.is_aboard(pawn) and local.z > ship.get_deck_height()):
        return False
    lib.send_verification_gameplay_key_state(client, 'Up', False)
    state['memo']['climb_s'] = round(time.monotonic() - state['memo']['t'], 1)
    return True


def look_about():
    state['aim'] = lambda: ship.get_actor_location() + unreal.Vector(0, 0, 250)
    state['memo']['t'] = time.monotonic()


def deck_marked():
    if time.monotonic() - state['memo']['t'] < 0.8:
        return False
    found = labels()
    needed = ['Wheel mount', 'Medium sail mount', 'Small sail mount', 'Hold']
    if any(n not in found for n in needed) or not any(l.startswith('Anchor') for l in found):
        return False
    state['memo']['aboard'] = found
    assert owner.get_inventory_component().add_item(small, 1) == 1
    state['memo']['t'] = time.monotonic()
    return True


def fit_marked():
    if time.monotonic() - state['memo']['t'] < 0.8:
        return False
    fits = [m for m in markers() if m.get_editor_property('fits')]
    return any(str(m.get_editor_property('label')).endswith('Fit Small sail here') for m in fits)


def climb_down():
    state['aim'] = None
    state['memo'].update(t=time.monotonic())
    assert lib.send_verification_gameplay_key_state(client, 'Down', True)


def in_the_sea():
    if owner.is_on_ladder() or pawn.is_on_ladder():
        return False
    mode = owner.get_component_by_class(unreal.CharacterMovementComponent).movement_mode
    if mode not in (unreal.MovementMode.MOVE_SWIMMING, unreal.MovementMode.MOVE_FALLING):
        return False
    lib.send_verification_gameplay_key_state(client, 'Down', False)
    return not ship.is_aboard(owner)


STEPS = [
    ('Swimming beside the sloop, the client sees the ladder marked (larger when aimed at) and the anchor', swim_beside_ladder, ladder_marked, 5),
    ('One press of E takes hold of the ladder, on server and client', press_e, holding, 4),
    ('Holding the Up arrow climbs the ladder and steps onto the deck at the top', climb_up, on_deck, 8),
    ('On deck the markers show the wheel mount, the Medium and Small sail mounts, the hold and the anchor', look_about, deck_marked, 4),
    ('Carrying a Small sail, the Small sail mount reads "Fit Small sail here"', lambda: None, fit_marked, 4),
    ('', swim_beside_ladder, lambda: time.monotonic() - state['memo']['t'] > 1.0, 3),
    ('', press_e, holding, 4),
    ('Holding the Down arrow climbs down and lets go into the sea at the foot of the ladder', climb_down, in_the_sea, 6),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    for key in ('Up', 'Down'):
        lib.send_verification_gameplay_key_state(client, key, False)
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    m = state['memo']
    RESULT.write_text(json.dumps({'success': error is None, 'checks': [c for c in checks if c], 'error': error,
                                  'climb_seconds': m.get('climb_s'), 'markers_outside': m.get('outside'),
                                  'markers_aboard': m.get('aboard')}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Ladder success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; markers {labels()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
