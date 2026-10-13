"""Client acceptance for the sea creatures on the coastal map.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the creatures
from Scripts/Setup/build_fish.py. Run unattended with run_play_check.py.

  1. The client has every creature the server has, all swimming; each within reach of the client stays close to the
     server's.
  2. A swimmer near a great white is noticed and bitten: health falls on server and client.
  3. Out of the water on the dock, the shark gives up.
  4. Struck once with Left Mouse, a peaceful manatee darts away.
  5. Struck, an aggressive manta ray turns on the swimmer; struck until dead, it floats belly-up on both machines.
  6. Pressing E at the body harvests it: its Raw Fish arrive in the survivor's inventory and the body is gone.
Writes Saved/FishPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'FishPlayResult.json')
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
fish = list(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWFish))
copies = {f.get_name(): f for f in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWFish)}
raw_fish = unreal.load_asset('/Game/Elitewake/Items/Food/DA_RawFish')
DOCK = unreal.Vector(4000, 900, 120)
RELEVANT = 14000.0   # within the default network cull distance, with room to spare
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'follow': None, 'swing_at': 0.0}


def named(display):
    return next(f for f in fish if str(f.get_editor_property('definition').get_editor_property('display_name')) == display)


def copy_of(f):
    return copies[f.get_name()]


def health(who):
    return who.get_survival_component().get_health()


def place(spot, look_at):
    for p in (owner, pawn):
        p.set_actor_location(spot, False, True)
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, look_at))


def follow():
    """Keep the swimmer beside the creature being fought, facing it, as it moves."""
    target, distance = state['follow'] or (None, 0)
    if not target:
        return
    at = target.get_actor_location()
    side = target.get_actor_right_vector()
    place(unreal.Vector(at.x + side.x * distance, at.y + side.y * distance, at.z - 30), at)


def begin_count():
    place(DOCK, DOCK + unreal.Vector(100, 0, 0))
    state['memo']['start'] = {f.get_name(): f.get_actor_location() for f in fish}
    state['memo']['t'] = time.monotonic()


def all_swimming():
    if time.monotonic() - state['memo']['t'] < 3.0:
        return False
    assert len(fish) >= 10, f'only {len(fish)} creatures on the server'
    assert set(copies) == {f.get_name() for f in fish}, 'client and server creatures differ'
    moved = [f for f in fish if (f.get_actor_location() - state['memo']['start'][f.get_name()]).length() > 30]
    assert len(moved) >= len(fish) - 1, f'only {len(moved)} of {len(fish)} moved'
    # Creatures far from a client stop updating for it, as any distant actor does; those near must stay close.
    near = [f for f in fish if (f.get_actor_location() - DOCK).length() < RELEVANT]
    gaps = [(f.get_actor_location() - copy_of(f).get_actor_location()).length() for f in near]
    assert len(near) >= 4 and max(gaps) < 250, f'{len(near)} near; worst client copy {max(gaps or [0]):.0f} cm from the server'
    state['memo'].update(creatures=len(fish), moved=len(moved), near=len(near), worst_gap=round(max(gaps)))
    return True


def near_shark():
    shark = named('Great White Shark')
    at = shark.get_actor_location()
    side = shark.get_actor_right_vector()
    place(unreal.Vector(at.x + side.x * 700, at.y + side.y * 700, -110), at)
    state['memo'].update(shark=shark, health_before=health(owner))


def bitten():
    shark = state['memo']['shark']
    state['memo']['seen'] = (f"quarry {shark.get_quarry()}, mode {owner.get_component_by_class(unreal.CharacterMovementComponent).movement_mode}, "
                             f"apart {(shark.get_actor_location() - owner.get_actor_location()).length():.0f}, "
                             f"shark z {shark.get_actor_location().z:.0f}, survivor z {owner.get_actor_location().z:.0f}")
    if shark.get_quarry() != owner:
        return False
    if health(owner) >= state['memo']['health_before'] or health(pawn) >= state['memo']['health_before']:
        return False
    state['memo']['bitten_to'] = health(owner)
    return True


def to_dock():
    place(DOCK, DOCK + unreal.Vector(100, 0, 0))
    owner.get_survival_component().restore_health(100)


def gave_up():
    return state['memo']['shark'].get_quarry() is None


def strike(target, distance):
    def begin():
        state['follow'] = (target(), distance)
        state['memo'].update(t=time.monotonic(), health0=target().get_health())
    return begin


def swing():
    if time.monotonic() >= state['swing_at']:
        state['swing_at'] = time.monotonic() + 1.1
        assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def manatee_fled():
    swing()
    manatee = state['follow'][0]
    if manatee.get_health() >= state['memo']['health0']:
        return False
    # Stop following: it should now swim off faster than it cruises.
    state['follow'] = None
    state['memo'].update(manatee=manatee, manatee_from=manatee.get_actor_location(), t=time.monotonic(),
                         manatee_health=manatee.get_health())
    return True


def manatee_away():
    m = state['memo']
    if time.monotonic() - m['t'] < 2.0:
        return False
    run = (m['manatee'].get_actor_location() - m['manatee_from']).length()
    cruise = m['manatee'].get_editor_property('definition').get_editor_property('swim_speed') * 2.0
    assert run > cruise * 1.3, f'manatee moved {run:.0f} cm in 2 s; cruising would be {cruise:.0f}'
    m['manatee_ran'] = round(run)
    return True


def manta_killed():
    swing()
    manta = state['follow'][0]
    owner.get_survival_component().restore_health(100)   # its sting must not end the check
    if manta.get_health() < state['memo']['health0']:
        assert manta.get_quarry() == owner or manta.is_dead(), 'the struck manta did not turn on the swimmer'
    if not (manta.is_dead() and copy_of(manta).is_dead()):
        return False
    state['follow'] = None
    state['memo'].update(manta=manta, t=time.monotonic())
    return True


def floated():
    manta = state['memo']['manta']
    seen = copy_of(manta)
    at, roll = seen.get_actor_location(), abs(seen.get_actor_rotation().roll)
    if at.z < manta.get_editor_property('surface_z') - 80 or roll < 150:
        return False
    state['memo'].update(float_z=round(at.z), roll=round(roll))
    return True


def harvest():
    manta = state['memo']['manta']
    at = manta.get_actor_location()
    place(unreal.Vector(at.x - 150, at.y, at.z - 20), at)
    state['memo']['fish_before'] = owner.get_inventory_component().get_item_count(raw_fish)
    state['memo']['pressed'] = 0.0


def harvested():
    manta = state['memo']['manta']
    # Look at the body as it bobs, and press E (again if a bob took the aim off it).
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, manta.get_actor_location()))
    if time.monotonic() - state['memo']['pressed'] > 1.0 and not manta.is_harvested():
        state['memo']['pressed'] = time.monotonic()
        assert lib.send_verification_gameplay_key(client, 'E')
    # Look at the body as it bobs, and press E (again if a bob took the aim off it).
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, manta.get_actor_location()))
    if time.monotonic() - state['memo']['pressed'] > 1.0 and not manta.is_harvested():
        state['memo']['pressed'] = time.monotonic()
        assert lib.send_verification_gameplay_key(client, 'E')
    eye = owner.get_actor_location() + unreal.Vector(0, 0, owner.get_editor_property('base_eye_height'))
    hit = unreal.SystemLibrary.line_trace_single(server_world, eye, manta.get_actor_location(), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                 False, [owner], unreal.DrawDebugTrace.NONE, True)
    state['memo']['aim'] = f"hit {hit.to_tuple()[9] if hit else None}, eye z {eye.z:.0f}, body z {manta.get_actor_location().z:.0f}, "                            f"apart {(manta.get_actor_location() - owner.get_actor_location()).length():.0f}, can {manta.can_interact(owner)}"
    gained = owner.get_inventory_component().get_item_count(raw_fish) - state['memo']['fish_before']
    if not (manta.is_harvested() and copy_of(manta).is_harvested() and gained > 0):
        return False
    expected = manta.get_editor_property('definition').get_editor_property('yield_quantity')
    assert gained == expected, f'gained {gained}, expected {expected}'
    assert not copy_of(manta).get_editor_property('visual').is_visible(), 'the harvested body still shows on the client'
    state['memo']['harvested'] = gained
    return True


STEPS = [
    ('The client sees every creature the server has, all swimming, each copy close to the server', begin_count, all_swimming, 6),
    ('A swimmer near a great white is noticed and bitten: health falls on server and client', near_shark, bitten, 12),
    ('Out of the water on the dock, the shark gives up', to_dock, gave_up, 5),
    ('Struck with Left Mouse, a peaceful manatee is hurt', strike(lambda: named('Manatee'), 140), manatee_fled, 8),
    ('The struck manatee darts away faster than it cruises', lambda: None, manatee_away, 4),
    ('Struck, a manta ray turns on the swimmer; struck until dead, it floats belly-up at the surface on the client',
     strike(lambda: named('Manta Ray'), 120), manta_killed, 25),
    ('', lambda: None, floated, 10),
    ('Pressing E at the body harvests it: its Raw Fish arrive and the body is gone on the client', harvest, harvested, 4),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t',)}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': [c for c in checks if c], 'error': error, 'measured': keep},
                                 indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Fish success={error is None} error={error}')


def tick(delta):
    follow()
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
            raise TimeoutError(f'not done within {timeout} s; survivor health {health(owner):.0f}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
