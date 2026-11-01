"""Client acceptance for the land animals across the five-region world (owner, October 15).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the animals from
Scripts/Setup/build_animals.py. Run unattended with run_play_check.py.

  1. The client has every animal the server has, of all twelve kinds, on the island and the second island, each
     standing on the ground.
  2. Left alone they wander: several walk off from where they stood; on the client their legs move with them (the
     stride advances while the copy walks) and each copy near the survivor stays close to the server's.
  3. A survivor standing right beside a pelican is ignored: naturally docile, it carries on as it was, unhurried,
     and does no harm (owner, October 15).
  4. Struck once with Left Mouse, a flamingo is hurt and runs off faster than it walks.
  5. A survivor who comes too near an alligator on land is noticed and bitten: health falls on server and client.
  6. Away down the beach the alligator gives up.
  7. Struck until dead, a squirrel monkey drops on its side on both machines.
  8. E at the body harvests it: 2 to 5 Raw Meat arrive and the body is gone on the client.
Writes Saved/AnimalsPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'AnimalsPlayResult.json')
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
animals = list(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWAnimal))
copies = {a.get_name(): a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWAnimal)}
raw_meat = unreal.load_asset('/Game/Elitewake/Items/Food/DA_RawMeat')
BEACH = unreal.Vector(150, 0, 150)
KINDS = {'American Alligator', 'Flamingo', 'Brown Pelican', 'Cottonmouth', 'Tortoise', 'Squirrel Monkey', 'Black Bear', 'Lion', 'Giant Crocodile', 'Elephant', 'Cave Spider', 'Wild Boar'}
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'follow': None, 'swing_at': 0.0}


def kind(a):
    return str(a.get_editor_property('definition').get_editor_property('display_name'))


def first(display):
    return next(a for a in animals if kind(a) == display)


def copy_of(a):
    return copies[a.get_name()]


def health(who):
    return who.get_survival_component().get_health()


def feet(a):
    return a.get_actor_location().z - a.get_editor_property('body').get_unscaled_sphere_radius()


def ground(at, above=300):
    hit = unreal.SystemLibrary.line_trace_single_for_objects(
        server_world, unreal.Vector(at.x, at.y, at.z + above), unreal.Vector(at.x, at.y, at.z - 1500),
        [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], False, [], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else None


def place(spot, look_at):
    for p in (owner, pawn):
        p.set_actor_location(spot, False, True)
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, look_at))


def beside(target, distance):
    at = target.get_actor_location()
    side = target.get_actor_right_vector()
    spot = unreal.Vector(at.x + side.x * distance, at.y + side.y * distance, at.z)
    g = ground(spot)
    return unreal.Vector(spot.x, spot.y, (g if g is not None else feet(target)) + 100), at


def follow():
    """Keep the survivor beside the animal being fought, facing it, as it moves."""
    target, distance = state['follow'] or (None, 0)
    if target and not target.is_dead():
        place(*beside(target, distance))


def swing():
    if time.monotonic() >= state['swing_at']:
        state['swing_at'] = time.monotonic() + 1.0
        assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def begin_count():
    place(BEACH, BEACH + unreal.Vector(100, 0, 0))
    state['memo'].update(start={a.get_name(): a.get_actor_location() for a in animals}, t=time.monotonic(),
                         strode=set(), phase={})


def all_present():
    assert len(animals) >= 20, f'only {len(animals)} animals on the server'
    assert set(copies) == {a.get_name() for a in animals}, 'client and server animals differ'
    kinds = {kind(a) for a in animals}
    assert kinds == KINDS, f'kinds: {sorted(kinds)}'
    # Spread over the five-region world (owner, October 15): on many islands, in at least four regions.
    labels = {a.get_actor_label().rsplit(' ', 2)[-2] for a in animals}
    regions = {k.rstrip('0123456789') for k in labels}
    # The five-island world has Plains, Swamp, Desert and Jungle animals (Winter has no land species yet: task GR4).
    assert len(labels) >= 4 and len(regions) >= 4, f'on {len(labels)} islands in {sorted(regions)}'
    second = [a for a in animals if 'Starter' not in a.get_actor_label()]
    off = []
    for a in animals:
        # From just above the animal, so a branch overhead (monkeys keep under the trees) is not taken for the ground.
        g = ground(a.get_actor_location(), 60)
        if g is None or abs(feet(a) - g) > 25:
            off.append((a.get_actor_label(), None if g is None else round(feet(a) - g)))
    assert not off, f'not standing on the ground: {off[:5]}'
    state['memo'].update(animals=len(animals), off_the_starter=len(second), islands=len(labels))
    return True


def to_animals():
    """Stand among the peaceful animals: where the survivor begins there may be none within the client's range."""
    here = owner.get_actor_location()
    calm = [a for a in animals if not a.get_editor_property('definition').get_editor_property('aggressive')]
    if sum(1 for a in calm if (a.get_actor_location() - here).length() < 14000) >= 3:
        return
    target = max(calm, key=lambda a: sum(1 for b in calm if (b.get_actor_location() - a.get_actor_location()).length() < 6000))
    spot = target.get_actor_location() + unreal.Vector(400, 0, 150)
    owner.teleport(spot, unreal.Rotator())


def wandered():
    m = state['memo']
    # Watch the legs on the client: a copy that is walking should be striding.
    for a in animals:
        c = copy_of(a)
        before = m['phase'].get(a.get_name())
        if c.get_shown_speed() > 10 and before is not None and abs(c.get_stride_phase() - before) > .05:
            m['strode'].add(kind(a))
        m['phase'][a.get_name()] = c.get_stride_phase()
    if time.monotonic() - m['t'] < 14.0:
        return False
    # Wildlife rests more than 200 m from every survivor (FEWWildlifeRest, October 15 night): those within it wander.
    peaceful = [a for a in animals if not a.get_editor_property('definition').get_editor_property('aggressive')
                and (a.get_actor_location() - owner.get_actor_location()).length() < 19000]
    moved = [a for a in peaceful if (a.get_actor_location() - m['start'][a.get_name()]).length() > 100]
    assert peaceful and len(moved) >= min(5, len(peaceful) - 1), f'only {len(moved)} of the {len(peaceful)} peaceful animals near the survivor wandered'
    # Only animals near enough to be sent to the client move there (about 150 m; the starter island is about 620 m
    # across since October 15 night), so ask for striding from the kinds that near, up to three of them.
    close = {kind(a) for a in animals if (a.get_actor_location() - owner.get_actor_location()).length() < 14000}
    need = min(3, len(close))
    assert need and len(m['strode'] & close) >= need, f'legs seen striding on the client for {sorted(m["strode"])}; near: {sorted(close)}'
    near = [a for a in animals if (a.get_actor_location() - owner.get_actor_location()).length() < 9000]
    gaps = [(a.get_actor_location() - copy_of(a).get_actor_location()).length() for a in near]
    assert near and max(gaps) < 250, f'worst client copy {max(gaps or [0]):.0f} cm from the server'
    m.update(wandered=len(moved), striding=', '.join(sorted(m['strode'])), worst_gap=round(max(gaps)))
    return True


def beside_pelican():
    bird = first('Brown Pelican')
    place(*beside(bird, 140))
    owner.get_survival_component().restore_health(100)
    state['memo'].update(bird=bird, bird_from=bird.get_actor_location(), t=time.monotonic(), bird_health=bird.get_health())


def pelican_ignores():
    m = state['memo']
    bird = m['bird']
    assert health(owner) >= 100 and health(pawn) >= 100, 'the pelican hurt the survivor'
    if time.monotonic() - m['t'] < 5.0:
        return False
    moved = (bird.get_actor_location() - m['bird_from']).length()
    walk = bird.get_editor_property('definition').get_editor_property('walk_speed') * 5.0
    assert moved < walk * 1.25 + 30, f'the pelican moved {moved:.0f} cm in 5 s beside the survivor; walking it would cover {walk:.0f}'
    assert bird.get_health() == m['bird_health']
    m['pelican_moved'] = round(moved)
    return True


def strike(display, distance):
    def begin():
        target = first(display)
        state['follow'] = (target, distance)
        state['memo'].update(target=target, health0=target.get_health(), t=time.monotonic())
    return begin


def flamingo_hit():
    swing()
    bird = state['memo']['target']
    if bird.get_health() >= state['memo']['health0']:
        return False
    state['follow'] = None
    place(BEACH, BEACH + unreal.Vector(100, 0, 0))
    state['memo'].update(bird_from=bird.get_actor_location(), t=time.monotonic(), bird_health=bird.get_health())
    return True


def flamingo_ran():
    m = state['memo']
    if time.monotonic() - m['t'] < 2.0:
        return False
    run = (m['target'].get_actor_location() - m['bird_from']).length()
    walk = m['target'].get_editor_property('definition').get_editor_property('walk_speed') * 2.0
    assert run > walk * 1.5, f'flamingo moved {run:.0f} cm in 2 s; walking would be {walk:.0f}'
    m['flamingo_ran'] = round(run)
    return True


def near_alligator():
    gator = first('American Alligator')
    place(*beside(gator, 320))
    state['memo'].update(gator=gator, health_before=health(owner))


def bitten():
    gator = state['memo']['gator']
    if gator.get_quarry() != owner:
        return False
    if health(owner) >= state['memo']['health_before'] or health(pawn) >= state['memo']['health_before']:
        return False
    state['memo']['bitten_to'] = round(health(owner))
    return True


def away():
    place(BEACH, BEACH + unreal.Vector(100, 0, 0))
    owner.get_survival_component().restore_health(100)


def gave_up():
    return state['memo']['gator'].get_quarry() is None


def monkey_killed():
    swing()
    monkey = state['memo']['target']
    if not (monkey.is_dead() and copy_of(monkey).is_dead()):
        return False
    state['follow'] = None
    up = copy_of(monkey).get_editor_property('visual').get_up_vector().z   # a model turned to face +X lies down as pitch, not roll
    assert up < .5, f'the dead monkey is not on its side on the client (up.z {up:.2f})'
    at = monkey.get_actor_location()
    place(unreal.Vector(at.x - 140, at.y, feet(monkey) + 100), at)
    state['memo'].update(meat_before=owner.get_inventory_component().get_item_count(raw_meat), pressed=0.0)
    return True


def harvested():
    monkey = state['memo']['target']
    at = monkey.get_actor_location()
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, at))
    if not monkey.is_harvested():
        if time.monotonic() - state['memo']['pressed'] > 1.0:
            state['memo']['pressed'] = time.monotonic()
            assert lib.send_verification_gameplay_key(client, 'E')
        return False
    gained = owner.get_inventory_component().get_item_count(raw_meat) - state['memo']['meat_before']
    if not copy_of(monkey).is_harvested() or gained <= 0:
        return False
    assert 2 <= gained <= 5, f'a squirrel monkey gave {gained} Raw Meat; it should give 2 to 5'
    assert not copy_of(monkey).get_editor_property('visual').is_visible(), 'the harvested body still shows on the client'
    state['memo']['meat'] = gained
    return True


STEPS = [
    ('The client has every animal the server has, all twelve kinds, across the islands of the world, each standing on the ground',
     begin_count, all_present, 4),
    ('Left alone they wander; on the client their legs stride as they walk, each copy close to the server', to_animals, wandered, 20),
    ('A survivor right beside a pelican is ignored: docile, it carries on unhurried and does no harm', beside_pelican, pelican_ignores, 8),
    ('Struck with Left Mouse, a flamingo is hurt', strike('Flamingo', 110), flamingo_hit, 8),
    ('The struck flamingo runs off faster than it walks', lambda: None, flamingo_ran, 4),
    ('A survivor too near an alligator on land is noticed and bitten: health falls on server and client', near_alligator, bitten, 12),
    ('Away down the beach the alligator gives up', away, gave_up, 5),
    ('Struck until dead, a squirrel monkey drops on its side on both machines', strike('Squirrel Monkey', 95), monkey_killed, 20),
    ('E at the body harvests it: 2 to 5 Raw Meat arrive and the body is gone on the client', lambda: None, harvested, 6),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t', 'pressed')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': [c for c in checks if c], 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Animals success={error is None} error={error}')


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
