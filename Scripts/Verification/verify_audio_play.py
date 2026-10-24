"""Client acceptance for the first sounds (draft audio from the owner's Scenario account, October 15).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client. Run unattended with
run_play_check.py. Sounds are counted where each machine starts them (UEWSoundLibrary), so this proves which sound
starts on which machine and when, not how it sounds: listening is the owner's. Through ordinary keys, the client:
  1. stands on the beach: the soundscape plays the surf loop at the shore level and the wind loop silent;
  2. presses E at a fiber plant: the rustle starts on both machines, the pickup only on the client;
  3. with the Hatchet at an oak, Left Mouse: the chop starts at the blow's contact on both machines;
  4. with the Pickaxe at a boulder: the pickaxe strike; 5. with the Hatchet at the boulder: the glancing clink;
  6. holds W on the sand: sand footsteps on both machines;
  7. walks up to the alligator: it hisses as it comes for the survivor, on both machines;
  8. stands on the Winter island: the wind rises, the surf falls, and W gives snow footsteps;
  9. stands near a pelican, then a flamingo: each calls on its own, heard on both machines;
 10. holds W inland on a Plains island: grass footsteps; in a Jungle island's middle by day the jungle's chorus plays,
     in a Swamp island's the frogs;
 11. on two islands, stands at the water's edge, then 10 m and 22 m inland, then back at the edge (owner, October
     16): the surf is full at the edge, softer 10 m in, silent past 20 m, and full again back at the edge.
Writes Saved/AudioPlayResult.json.
"""
import json
import time
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
snd = unreal.EWSoundLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'AudioPlayResult.json')
T = '/Game/Elitewake/Items/Testing'
hatchet, pickaxe = (unreal.load_asset(f'{T}/DA_Test{n}') for n in ('WoodenAxe', 'WoodenPickaxe'))
def one(items, what):
    found = next(iter(items), None)
    assert found is not None, f'found no {what}'
    return found


worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = one((c for c in pcs if not c.has_authority()), 'client')
server_world = one((w for w, c in zip(worlds, pcs) if c.has_authority()), 'server world')
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()
scape = client.get_soundscape_component()


def player_id(p):
    state_ = p.get_editor_property('PlayerState')   # survivors nobody plays have none
    return json.loads(unreal.ToolsetLibrary.get_object_properties(state_, ['PlayerId']))['PlayerId'] if state_ else None


owner = one((p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) is not None and player_id(p) == player_id(pawn)), "the server's copy of the client's survivor")
SPAWN = unreal.Vector(150, 0, 0)
near = lambda actors: sorted(actors, key=lambda t: (t.get_actor_location() - SPAWN).length())   # noqa: E731
palm = near([t for t in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarvestTree) if t.get_actor_label().startswith('Oak')])[0]
rock = near(list(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWMineable)))[0]
fiber_plant = near([p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHandGatherable) if p.get_actor_label().startswith('Fiber Plant')])[0]
animals = list(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWAnimal))
gator = one((a for a in animals if a.get_editor_property('definition').get_name() == 'DA_Animal_Alligator'), 'alligator')
winter = one((r for r in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWClimateRegion) if r.get_editor_property('region') == unreal.EWRegion.WINTER), 'Winter region')
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
measured = {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None}


def heard(world, *names):
    return sum(snd.get_play_count(world, n) for n in names)


def both(*names):
    return heard(client_world, *names), heard(server_world, *names)


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def place(spot, look_at=None):
    for p in (owner, pawn):
        assert p.teleport(spot, unreal.Rotator()), f'no room at {spot}'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['aim'] = (lambda: look_at) if look_at else None
    keep_aim()


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(server_world, unreal.Vector(x, y, 20000), unreal.Vector(x, y, -5000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner, pawn],
                                                 unreal.DrawDebugTrace.NONE, True)
    hit = hit[0] if isinstance(hit, tuple) else hit
    assert hit, f'no ground at {x}, {y}'
    return hit.to_tuple()[4].z   # impact point


def approach(target, distance, aim_height):
    base = target.get_actor_location()
    away = unreal.Vector(150 - base.x, -base.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    place(base + away * distance + unreal.Vector(0, 0, 110), base + unreal.Vector(0, 0, aim_height))


def hold(item):
    if owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) != item:
        assert lib.send_verification_equipment_request(client, item, unreal.EWEquipmentSlot.MAIN_HAND)


def walk(on):
    assert lib.send_verification_gameplay_key_state(client, 'W', on)


# 1. The soundscape ashore.
def begin_shore():
    # On the south-east beach (see beach_walk): the spawn point lies 40 m inland, past the surf's reach.
    place(unreal.Vector(1716, -3693, ground(1716, -3693) + 110))
    state['memo'].update(t=time.monotonic())


def shore_heard():
    if time.monotonic() - state['memo']['t'] < 3.5:
        return False
    assert scape.is_ambience_playing(), 'the surf and wind loops are not playing on the client'
    assert scape.get_heard_region() != unreal.EWRegion.WINTER, scape.get_heard_region()
    assert scape.get_surf_level() >= .69 and scape.get_wind_level() < .01, (scape.get_surf_level(), scape.get_wind_level())
    measured.update(shore_region=str(scape.get_heard_region()), shore_surf=round(scape.get_surf_level(), 2))
    return True


# 2. Hands in the plants.
def begin_gather():
    approach(fiber_plant, 95, 10)
    state['memo'].update(t=time.monotonic(), pressed=False, rustle=both('S_GatherRustle_v1'), pickup=both('S_Pickup_v1'))


def gathered():
    m = state['memo']
    keep_aim()
    if time.monotonic() - m['t'] < .8:
        return False
    if not m['pressed']:
        m['pressed'] = True
        assert lib.send_verification_interaction_request(client, next(a for a in unreal.GameplayStatics.get_all_actors_of_class(
            client_world, unreal.EWHandGatherable) if a.get_name() == fiber_plant.get_name()))
        return False
    rustle, pickup = both('S_GatherRustle_v1'), both('S_Pickup_v1')
    if not (rustle[0] > m['rustle'][0] and rustle[1] > m['rustle'][1] and pickup[0] > m['pickup'][0]):
        return False
    assert pickup[1] == m['pickup'][1], 'the server heard the client put plants in their pack'
    return True


# 3-5. Blows at the palm and the boulder.
def begin_strike(target, item, distance, aim_height, sound):
    def begin():
        hold(item)
        d = distance
        if d is None:
            _, extent = rock.get_actor_bounds(False)
            d = max(extent.x, extent.y) + 55
        approach(target, d, aim_height)
        state['memo'].update(t=time.monotonic(), pressed=0.0, swings=0, sound=sound, before=both(sound),
                             impacts=pawn.get_work_impact_count())
    return begin


def struck():
    m = state['memo']
    keep_aim()
    if time.monotonic() - m['t'] < 1.0:
        return False
    after = both(m['sound'])
    if after[0] > m['before'][0] and after[1] > m['before'][1]:
        # The sound comes with the chips at the blow's contact moment, not when the button went down.
        assert pawn.get_work_impact_count() > m['impacts'], 'a sound without the blow landing'
        measured[f'{m["sound"]}_swings'] = m['swings']
        return True
    if m['swings'] == 0 or (time.monotonic() - m['pressed'] > 1.6 and m['swings'] < 4):
        m['swings'] += 1
        m['pressed'] = time.monotonic()
        assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')
    return False


# 6 and 8. Footsteps.
def begin_walk(spot_fn, names):
    def begin():
        state['aim_point'] = None
        spot = spot_fn()
        place(spot, state['aim_point'])
        state['memo'].update(t=time.monotonic(), walking=False, names=names, before=both(*names))
    return begin


def stepped(region):
    def done():
        m = state['memo']
        if time.monotonic() - m['t'] < 3.0:
            return False   # the wind and surf fade over 2.5 s
        if not m['walking']:
            if region is not None:
                assert scape.get_heard_region() == region, scape.get_heard_region()
                measured.update(winter_surf=round(scape.get_surf_level(), 2), winter_wind=round(scape.get_wind_level(), 2))
                assert scape.get_wind_level() > .99 and scape.get_surf_level() < .31, (scape.get_wind_level(), scape.get_surf_level())
            walk(True)
            m.update(walking=True, start=time.monotonic(), from_=pawn.get_actor_location())
            return False
        after = both(*m['names'])
        if time.monotonic() - m['start'] < 3.0:
            return False
        walk(False)
        steps = (after[0] - m['before'][0], after[1] - m['before'][1])
        moved = (pawn.get_actor_location() - m['from_']).length()
        measured[f'{m["names"][0]}_walk'] = dict(steps=steps, cm=round(moved), speed=round(pawn.get_velocity().length()))
        assert steps[0] >= 3 and steps[1] >= 3, f'steps heard (client, server): {steps} over {moved:.0f} cm'
        return True
    return done


# 7. The alligator.
def gator_spot(distance):
    at = gator.get_actor_location()
    side = gator.get_actor_right_vector()
    spot = unreal.Vector(at.x + side.x * distance, at.y + side.y * distance, at.z)
    return unreal.Vector(spot.x, spot.y, ground(spot.x, spot.y) + 100)


def begin_gator():
    # First out of its notice (12 m) long enough for the client to have the alligator, as a survivor walking up
    # would; then ashore at its side (as verify_animals_play does): it only goes for a survivor on land.
    for p in (owner, pawn):
        p.set_actor_location(gator_spot(1200), False, True)
    state['aim'] = lambda: gator.get_actor_location()
    keep_aim()
    owner.get_survival_component().restore_health(100)
    state['memo'].update(t=time.monotonic(), closed=False, before=both('S_AlligatorHiss_v1', 'S_AlligatorHiss_v1b'))


def hissed():
    m = state['memo']
    keep_aim()
    if not m['closed']:
        if time.monotonic() - m['t'] < 2.0:
            return False
        for p in (owner, pawn):
            p.set_actor_location(gator_spot(320), False, True)
        m['closed'] = True
    after = both('S_AlligatorHiss_v1', 'S_AlligatorHiss_v1b')
    quarry = gator.get_quarry()
    m.update(hiss=(after[0] - m['before'][0], after[1] - m['before'][1]), quarry=quarry.get_name() if quarry else '')
    return after[0] > m['before'][0] and after[1] > m['before'][1]


def winter_spot():
    # The Winter region is a group of islands with sea at its middle: stand by one of its trees and walk toward
    # another 25 to 60 m off, on the same island.
    region = lambda a: unreal.EWClimateRegion.sample_climate(server_world, a.get_actor_location()).region   # noqa: E731
    trees = [t for t in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarvestTree) if region(t) == unreal.EWRegion.WINTER]
    for a in trees:
        for b in trees:
            gap = (b.get_actor_location() - a.get_actor_location()).length()
            if 2500 < gap < 6000:
                at, to = a.get_actor_location(), b.get_actor_location()
                start = at + (to - at) * (250.0 / gap)
                state['aim_point'] = unreal.Vector(to.x, to.y, start.z)
                return unreal.Vector(start.x, start.y, ground(start.x, start.y) + 110)
    raise AssertionError(f'no pair of Winter trees 25 to 60 m apart among {len(trees)}')


def beach_walk():
    """On the starter island's south-east beach, 2.5 m in from the water and facing along it (away from the dock), so
    every step is on the sand."""
    state['aim_point'] = unreal.Vector(3360, -2040, 0)
    return unreal.Vector(1716, -3693, ground(1716, -3693) + 110)


# 10. Grass underfoot inland, and each wooded region's own sound.
def inland(key):
    isl = W.island(key)
    x, y = isl.cx, isl.cy
    return unreal.Vector(x, y, ground(x, y) + 110)


def begin_region(key):
    def begin():
        place(inland(key))
        state['memo'].update(t=time.monotonic())
    return begin


def region_loop(name):
    def done():
        if time.monotonic() - state['memo']['t'] < 3.5:
            return False
        assert scape.get_region_loop() == name and scape.get_region_loop_level() > .45, \
            (str(scape.get_region_loop()), round(scape.get_region_loop_level(), 2), str(scape.get_heard_region()))
        measured[f'{name}_level'] = round(scape.get_region_loop_level(), 2)
        return True
    return done


# 11. The surf fading inland.
SEA = -65
shores = {}


def shore_line(key):
    """The island's edge, walking out from its middle (toward the south-east, then other ways) until the ground is at
    the sea; and the way inland from there."""
    if key not in shores:
        isl = W.island(key)
        for ux, uy in ((.7071, -.7071), (1, 0), (0, -1), (-.7071, .7071), (0, 1), (-1, 0)):
            d = 0
            while d < 80000 and ground(isl.cx + ux * d, isl.cy + uy * d) > SEA + 5:
                d += 100
            if d >= 80000:
                continue
            edge = (isl.cx + ux * (d - 50), isl.cy + uy * (d - 50))
            # Straight inland for 25 m: no other water within reach of the line's far end.
            if all(ground(edge[0] - ux * s, edge[1] - uy * s) > SEA + 5 for s in range(100, 4600, 100)):
                shores[key] = (edge, (-ux, -uy))
                break
        else:
            raise AssertionError(f'no shore with 45 m of land behind it on {key}')
    return shores[key]


def begin_surf(key, inland_cm):
    def begin():
        (x, y), (ix, iy) = shore_line(key)
        x, y = x + ix * inland_cm, y + iy * inland_cm
        place(unreal.Vector(x, y, ground(x, y) + 110))
        state['memo'].update(t=time.monotonic())
    return begin


def surf_heard(key, inland_cm, low, high):
    def done():
        if time.monotonic() - state['memo']['t'] < 4.0:
            return False   # sampled twice a second, faded over 2.5 s
        level, reach = scape.get_surf_level(), scape.get_shore_distance()
        measured[f'surf_{key}_{inland_cm}'] = dict(level=round(level, 2), shore_cm=round(reach), region=str(scape.get_heard_region()))
        if high <= .01 and reach < 2100: high = .25      # a bay or cove on the five-island world's irregular coasts brings the water within 22 m of the walker: still soft, not silent
        assert low <= level <= high, f'the surf at {inland_cm} cm in on {key} is {level:.2f} (shore {reach:.0f} cm), not {low}-{high}'
        return True
    return done


def surf_steps(key):
    return [
        (f'On {key} at the water\'s edge the surf is full', begin_surf(key, 0), surf_heard(key, 0, .6, 1.0), 10),
        (f'10 m inland on {key} the surf is softer', begin_surf(key, 1000), surf_heard(key, 1000, .1, .59), 10),
        (f'22 m inland on {key} the surf is silent', begin_surf(key, 2200), surf_heard(key, 2200, 0.0, .01), 10),
        (f'Back at the edge on {key} the surf is full again', begin_surf(key, 0), surf_heard(key, 0, .6, 1.0), 10),
    ]


# 9. The flamingos and pelicans, on their own time: heard by a client standing near one (a far animal's calls are
# neither sent to that client nor audible there).
def begin_bird(kind, sound):
    def begin():
        bird = near([a for a in animals if a.get_editor_property('definition').get_name() == f'DA_Animal_{kind}' and not a.is_dead()])[0]
        base = bird.get_actor_location()
        spot = base + unreal.Vector(250, 250, 0)
        place(unreal.Vector(spot.x, spot.y, ground(spot.x, spot.y) + 110), base)
        state['memo'].update(t=time.monotonic(), sound=sound, before=both(sound))
    return begin


def bird_called():
    m = state['memo']
    after = both(m['sound'])
    measured[f'{m["sound"]}_calls'] = (after[0] - m['before'][0], after[1] - m['before'][1], round(time.monotonic() - m['t']))
    return after[0] > m['before'][0] and after[1] > m['before'][1]


STEPS = [
    ('Ashore the client hears the surf loop at the shore level, the wind loop silent', begin_shore, shore_heard, 8),
    ('E at a fiber plant: the rustle starts on both machines, the pickup only on the client', begin_gather, gathered, 8),
    ('Hatchet at an oak: the chop starts at the blow on both machines', begin_strike(palm, hatchet, 130, 120, 'S_ChopWood_v1'), struck, 14),
    ('Pickaxe at a boulder: the pickaxe strike on both machines', begin_strike(rock, pickaxe, None, 20, 'S_PickaxeStone_v1'), struck, 14),
    ('Hatchet at the boulder: the glancing clink on both machines', begin_strike(rock, hatchet, None, 20, 'S_GlanceClink_v1'), struck, 14),
    ('W along the beach: sand footsteps on both machines', begin_walk(beach_walk, ('S_StepSand_v1', 'S_StepSand_v1b')), stepped(None), 12),
    ('Beside the alligator: it hisses as it comes, on both machines', begin_gator, hissed, 10),
    ('On the Winter island: the wind rises, the surf falls, W gives snow footsteps', begin_walk(winter_spot, ('S_StepSnow_v1',)), stepped(unreal.EWRegion.WINTER), 14),
    ('W inland on a Plains island: grass footsteps on both machines', begin_walk(lambda: inland('Starter'), ('S_StepGrass_v1',)), stepped(None), 12),
    ('In the middle of a Jungle island by day: the jungle\'s chorus plays', begin_region('Jungle1'), region_loop('JungleDay'), 8),
    ('In the middle of a Swamp island: the frogs play', begin_region('Swamp1'), region_loop('SwampFrogs'), 8),
    *surf_steps('Starter'),
    *surf_steps('Jungle1'),
    ('Near a pelican: it calls on its own, heard on both machines', begin_bird('Pelican', 'S_PelicanCall_v1'), bird_called, 70),
    ('Near a flamingo: it calls on its own, heard on both machines', begin_bird('Flamingo', 'S_FlamingoCall_v1'), bird_called, 55),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    try:
        walk(False)
    except Exception:
        pass
    measured.update(seabirds=both('S_AmbSeabirds_v1'), client_total=snd.get_total_play_count(client_world), server_total=snd.get_total_play_count(server_world))
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2, default=str), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Audio success={error is None} error={error}')


def tick(delta):
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
            raise TimeoutError(f'not done within {timeout} s; memo {dict((k, v) for k, v in state["memo"].items() if isinstance(v, (int, float, str, bool, tuple)))}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
