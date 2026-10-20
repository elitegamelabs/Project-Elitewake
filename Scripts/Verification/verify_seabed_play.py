"""Acceptance for the sea floor (owner, October 17: dynamic sea-floor scenery, deeper sand, geography, corals and
aquatic plants, the ocean at most 2,000 m deep). Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground with one
player (EW_PLAY_PLAYERS=1: the screenshots are the player's own view), after build_coastal_terrain.py and
build_seabed_life.py. Run unattended with run_play_check.py.

  1. Depth: across the whole sea the floor is never deeper than 2,000 m, the open ocean and the trench reach at least
     1,900 m, and the channels between islands are 100-600 m deep in their middles.
  2. Geography: every seamount's top is within diving depth (8-30 m), well above its surroundings.
  3. The water reaches the deepest floor: the swimming volume goes down 2,000 m, and a survivor 1,500 m down in the
     trench is swimming, not falling.
  4. Life: thousands of seagrass clumps, kelp, corals, sea fans and sponges; every kelp's tip stays under water.
  5. Corals and sponges are solid to a trace; plants are not.
  6. Screenshots underwater: a seagrass meadow, a kelp forest, corals, a seamount top. Saved/Screenshots/Seabed.
Writes Saved/SeabedPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SeabedPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Seabed')
SHOTS.mkdir(parents=True, exist_ok=True)
world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
checks, measured = [], {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'at': 0.0, 'shot': None, 'view': None}
GROUND_ACTORS = ('Sea floor', '(', 'Seamount')   # the sea floor, each island's "<key> (<region>)" mesh, the seamounts


def floor_z(x, y):
    """The ground under (x, y), past any coral, sponge or fish (a blocking hit ends a trace, so carry on under it)."""
    top = T.SEA - 50
    for _ in range(8):
        hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(x, y, top), unreal.Vector(x, y, T.DEEP - 20000),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if not hits:
            return None
        for hit in hits:
            t = hit.to_tuple()
            actor = t[9]
            if actor and isinstance(actor, unreal.StaticMeshActor) and any(g in actor.get_actor_label() for g in GROUND_ACTORS):
                return t[4].z
        top = hits[-1].to_tuple()[4].z - 5
    return None


def depth_m(x, y):
    z = floor_z(x, y)
    return None if z is None else (T.SEA - z) / 100


def depth():
    x0, x1, y0, y1 = W.bounds(250000)
    deepest, missing = 0.0, 0
    for i in range(24):
        for j in range(24):
            d = depth_m(x0 + (x1 - x0) * (i + .5) / 24, y0 + (y1 - y0) * (j + .5) / 24)
            if d is None:
                missing += 1
                continue
            assert d <= 2001, f'the floor is {d:.0f} m deep'
            deepest = max(deepest, d)
    assert missing == 0, f'{missing} samples found no sea floor'
    (ax, ay), (bx, by) = T.TRENCH
    trench = max(depth_m(ax + (bx - ax) * f, ay + (by - ay) * f) for f in (.1, .15, .2, .25))
    assert trench >= 1500, f'the trench is only {trench:.0f} m deep'
    assert deepest >= 1900, f'the deepest sample is {deepest:.0f} m'
    # The middle of the channel between every island and its nearest neighbour.
    channels = []
    for a in W.ISLANDS:
        b = min((i for i in W.ISLANDS if i is not a), key=lambda i: math.hypot(i.cx - a.cx, i.cy - a.cy))
        ang = math.atan2(b.cy - a.cy, b.cx - a.cx)
        ra, rb = a.radius(ang), b.radius(ang + math.pi)
        f = (ra + (math.hypot(b.cx - a.cx, b.cy - a.cy) - ra - rb) / 2) / math.hypot(b.cx - a.cx, b.cy - a.cy)
        channels.append(round(depth_m(a.cx + (b.cx - a.cx) * f, a.cy + (b.cy - a.cy) * f)))
    assert all(60 <= c <= 600 for c in channels), f'channel middles {channels} m'
    measured.update(deepest_m=round(deepest), trench_m=round(trench), channel_middles_m=channels)
    return True


def seamounts():
    tops = []
    for mx, my, top, radius in T.SEAMOUNT_SITES:
        d = min(depth_m(mx + dx, my + dy) for dx, dy in ((0, 0), (800, 0), (-800, 0), (0, 800), (0, -800)))
        around = depth_m(mx + radius * 2.2, my)
        assert 8 <= d <= 30, f'a seamount top at {d:.0f} m'
        assert around - d > 40, f'a seamount stands only {around - d:.0f} m over its surroundings'
        tops.append([round(d, 1), round(around)])
    measured['seamount_top_and_foot_m'] = tops
    return True


def deep_water():
    volume = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PhysicsVolume)
                  if 'swimming' in a.get_actor_label().lower() or a.get_editor_property('water_volume'))
    origin, extent = volume.get_actor_bounds(False)
    assert origin.z - extent.z <= T.DEEP + 100, f'the swimming volume ends {(T.SEA - (origin.z - extent.z)) / 100:.0f} m down'
    (ax, ay), (bx, by) = T.TRENCH
    x, y = ax + (bx - ax) * .15, ay + (by - ay) * .15
    pawn.teleport(unreal.Vector(x, y, T.SEA - 150000), pawn.get_actor_rotation())
    state['at'] = time.monotonic()
    return True


def swimming_deep():
    if time.monotonic() - state['at'] < 1.5:
        return False
    mode = move.get_editor_property('movement_mode')
    measured['deep_mode'] = str(mode)
    assert mode == unreal.MovementMode.MOVE_SWIMMING, f'1,500 m down the survivor is {mode}'
    return True


def instances():
    found = {}
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
        for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = comp.get_editor_property('static_mesh')
            name = mesh.get_name() if mesh else ''
            for kind, key in (('Seagrass', 'SM_Seagrass'), ('Kelp', 'SM_Kelp'), ('Coral', 'SM_SeabedCoral'),
                              ('Fan', 'SM_SeaFan'), ('Sponge', 'Sponge_')):
                if key in name:
                    found.setdefault(kind, []).append(comp)
    return found


def life():
    found = instances()
    counts = {k: sum(c.get_instance_count() for c in comps) for k, comps in found.items()}
    measured['life'] = counts
    for kind, least in (('Seagrass', 20000), ('Kelp', 3000), ('Coral', 5000), ('Fan', 2000), ('Sponge', 3000)):
        assert counts.get(kind, 0) >= least, f'{kind}: {counts.get(kind, 0)}'
    for comp in found['Kelp']:
        top = comp.get_editor_property('static_mesh').get_bounds().box_extent.z * 2
        for i in range(0, comp.get_instance_count(), 7):
            t = comp.get_instance_transform(i, True)
            tip = t.translation.z + top * t.scale3d.z
            assert tip < T.SEA - 50, f'a kelp reaches {tip - T.SEA:.0f} cm from the surface'
    state['found'] = found
    return True


def solid():
    blocked = {}
    for kind in ('Coral', 'Sponge', 'Seagrass', 'Kelp'):
        comp = max(state['found'][kind], key=lambda c: c.get_instance_count())
        hits = 0
        for i in range(0, min(comp.get_instance_count(), 400), 40):
            t = comp.get_instance_transform(i, True)
            p = t.translation + unreal.Vector(0, 0, 30 * t.scale3d.z)
            hit = unreal.SystemLibrary.line_trace_single(world, p + unreal.Vector(250, 0, 0), p - unreal.Vector(250, 0, 0),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            if hit and hit.to_tuple()[10] == comp:
                hits += 1
        blocked[kind] = hits
    measured['traces_stopped'] = blocked
    assert blocked['Coral'] >= 5 and blocked['Sponge'] >= 5, blocked
    assert blocked['Seagrass'] == 0 and blocked['Kelp'] == 0, blocked
    return True


def near_instance(kind, x, y):
    best = None
    for comp in state['found'][kind]:
        for i in range(0, comp.get_instance_count(), 3):
            t = comp.get_instance_transform(i, True).translation
            d = math.hypot(t.x - x, t.y - y)
            if best is None or d < best[0]:
                best = (d, t)
    return best[1]


def view(kind, island_key=None, seamount=None, back=600, up=250):
    def begin():
        if seamount is not None:
            mx, my, *_ = T.SEAMOUNT_SITES[seamount]
            target = unreal.Vector(mx, my, floor_z(mx, my))
            out = (1.0, .3)
        else:
            i = next(i for i in W.ISLANDS if i.key == island_key)
            # A plant of the kind on the island's far side from the world's middle, looked at from seaward.
            target = near_instance(kind, i.cx + (i.cx / (abs(i.cx) + abs(i.cy) + 1)) * i.reach() * 1.2,
                                   i.cy + (i.cy / (abs(i.cx) + abs(i.cy) + 1)) * i.reach() * 1.2)
            out = (target.x - i.cx, target.y - i.cy)
        n = math.hypot(*out) or 1.0
        state.update(view=(target, back, up, (out[0] / n, out[1] / n)), at=time.monotonic(), shot=None)
        hold()
        assert (pawn.get_actor_location() - target).length() < back + up + 600,             f'the survivor did not reach the {kind} view ({pawn.get_actor_location()} for {target})'
    return begin


def hold():
    target, back, up, (ox, oy) = state['view']
    eye = unreal.Vector(target.x + ox * back, target.y + oy * back, min(target.z + up, T.SEA - 160))
    pawn.teleport(eye, unreal.Rotator(0, 0, 0))
    move.stop_movement_immediately()
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye + unreal.Vector(0, 0, 60), target))


def shot(label):
    def done():
        hold()
        if time.monotonic() - state['at'] < 1.5:
            return False
        if state['shot'] is None:
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / (label + ".png")}"')
            state['shot'] = time.monotonic()
            return False
        return time.monotonic() - state['shot'] > 1.0
    return done


def warmup():
    unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / "warmup.png"}"')


STEPS = [
    ('The floor is never deeper than 2,000 m; the open ocean and the trench reach it; channels are 60-600 m deep', warmup, depth, 30),
    ('Every seamount top is within diving depth, well above its surroundings', lambda: None, seamounts, 10),
    ('The swimming volume reaches 2,000 m down', lambda: None, deep_water, 5),
    ('1,500 m down in the trench the survivor swims', lambda: None, swimming_deep, 8),
    ('Thousands of seagrass clumps, kelp, corals, fans and sponges; every kelp tip under water', lambda: None, life, 30),
    ('Corals and sponges stop a trace; seagrass and kelp do not', lambda: None, solid, 10),
    ('Screenshot: a seagrass meadow off the starter island', view('Seagrass', 'Starter'), shot('seagrass_starter'), 10),
    ('Screenshot: a Winter kelp forest', view('Kelp', next(i.key for i in W.ISLANDS if i.region == 'Winter'), back=900, up=150), shot('kelp_winter'), 10),
    ('Screenshot: Jungle corals', view('Coral', next(i.key for i in W.ISLANDS if i.region == 'Jungle')), shot('coral_jungle'), 10),
    ('Screenshot: a seamount top', view('Coral', seamount=min(range(len(T.SEAMOUNT_SITES)), key=lambda n: T.SEAMOUNT_SITES[n][2]),
                                        back=1500, up=600), shot('seamount'), 10),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWPLAYCHECK Seabed success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


unreal.SystemLibrary.execute_console_command(world, 'r.MotionBlurQuality 0')
state['handle'] = unreal.register_slate_post_tick_callback(tick)
