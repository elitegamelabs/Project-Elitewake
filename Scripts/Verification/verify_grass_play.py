"""Client acceptance for the grass (owner: Central Plains grassland, October 15). Needs Play in
/Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after build_grass.py. Run unattended
with run_play_check.py.

  1. Every Plains island (the starter's included) and every Jungle island has grass clumps, the Plains thicker than
     the Jungle; the client has the same grass.
  2. No grass on the beach, a Port, a cave or the spring.
  3. Grass is soft: a survivor walks 10 m through the starter island's thickest meadow (W held) at walking pace,
     on the client; grass has no collision and nothing in it blocks even a precise (complex) trace at knee height.
Writes Saved/GrassPlayResult.json.
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
RESULT = Path(unreal.Paths.project_saved_dir(), 'GrassPlayResult.json')
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
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def clumps(world):
    out = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
        for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = comp.get_editor_property('static_mesh')
            if not mesh or 'SM_GrassClump' not in mesh.get_name():
                continue
            for k in range(comp.get_instance_count()):
                p = comp.get_instance_transform(k, True).translation
                out.append((p.x, p.y, p.z))
    return out


def by_island(points):
    count = {}
    for x, y, _ in points:
        i = min(W.ISLANDS, key=lambda isle: isle.distance(x, y))
        count[i.key] = count.get(i.key, 0) + 1
    return count


def everywhere():
    server, seen = clumps(server_world), clumps(client_world)
    assert len(server) > 1000, f'only {len(server)} clumps'
    assert len(seen) == len(server), f'the client has {len(seen)} clumps, the server {len(server)}'
    count = by_island(server)
    density = {}
    for i in W.ISLANDS:
        if i.region in ('Plains', 'Jungle'):
            assert count.get(i.key, 0) > 100, f'{i.key} has {count.get(i.key, 0)} clumps'
            density.setdefault(i.region, []).append(count[i.key] / (math.pi * i.rx * i.ry / 1e4))
        else:
            assert not count.get(i.key), f'{i.key} ({i.region}) has grass'
    plains, jungle = (sum(density[r]) / len(density[r]) for r in ('Plains', 'Jungle'))
    assert plains > 1.5 * jungle, (plains, jungle)
    for actor in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.InstancedFoliageActor):
        for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = comp.get_editor_property('static_mesh')
            if mesh and 'SM_GrassClump' in mesh.get_name():
                assert comp.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION, 'grass has collision'
    state['memo'].update(clumps=len(server), plains_per_m2=round(plains, 2), jungle_per_m2=round(jungle, 2))
    state['points'] = server
    return True


def kept_off():
    bad = []
    for x, y, z in state['points']:
        i = min(W.ISLANDS, key=lambda isle: isle.distance(x, y))
        if i.distance(x, y) > -1200:
            bad.append(f'on the beach of {i.key}')
        elif W.near_port(x, y, 0):
            bad.append('on a Port')
        elif T.near_cave(x, y, -100):
            bad.append('on a cave')
        elif math.hypot(x - T.POND[0], y - T.POND[1]) < T.POND_RADIUS:
            bad.append('in the spring')
    assert not bad, f'{len(bad)} clumps misplaced, e.g. {bad[:4]}'
    return True


def meadow():
    """The 10 m line on the starter island with the most grass along it."""
    pts = [(x, y) for x, y, _ in state['points'] if W.ISLANDS[0].distance(x, y) < -2000]
    best = None
    for x0, y0 in pts[::max(1, len(pts) // 60)]:
        for a in range(0, 360, 30):
            ax, ay = math.cos(math.radians(a)), math.sin(math.radians(a))
            n = sum(1 for x, y in pts if 0 < (x - x0) * ax + (y - y0) * ay < 1000 and abs(-(x - x0) * ay + (y - y0) * ax) < 60)
            ok = all(not T.near_cave(x0 + ax * d, y0 + ay * d, 300) and W.ISLANDS[0].distance(x0 + ax * d, y0 + ay * d) < -1500
                     for d in range(0, 1101, 100))
            if ok and (best is None or n > best[0]):
                best = (n, x0, y0, a)
    return best


def start_walk():
    n, x, y, a = meadow()
    assert n >= 15, f'no thick meadow found ({n} clumps on the best line)'
    z = T.height(x, y) + 120
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(x, y, z), unreal.Rotator(0, 0, a))
    for c in (client, owner.get_controller()):
        c.set_control_rotation(unreal.Rotator(0, 0, a))
    hit = unreal.SystemLibrary.line_trace_single(server_world, unreal.Vector(x, y, T.height(x, y) + 30),
                                                 unreal.Vector(x + 1000 * math.cos(math.radians(a)), y + 1000 * math.sin(math.radians(a)),
                                                               T.height(x + 1000 * math.cos(math.radians(a)), y + 1000 * math.sin(math.radians(a))) + 30),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [owner, pawn], unreal.DrawDebugTrace.NONE, True)
    if hit:
        comp = hit.to_tuple()[10]
        mesh = comp.get_editor_property('static_mesh') if isinstance(comp, unreal.StaticMeshComponent) else None
        assert not (mesh and 'SM_GrassClump' in mesh.get_name()), 'grass blocks a trace at knee height'
    state['memo'].update(t=time.monotonic(), walking=False, start=(x, y), meadow_clumps=n)


def walked():
    m = state['memo']
    if not m['walking']:
        if time.monotonic() - m['t'] < 1.0:
            return False
        assert lib.send_verification_gameplay_key_state(client, 'W', True)
        m['walking'], m['go'] = True, time.monotonic()
    p = pawn.get_actor_location()
    gone = math.hypot(p.x - m['start'][0], p.y - m['start'][1])
    if gone < 1000:
        return False
    lib.send_verification_gameplay_key_state(client, 'W', False)
    seconds = time.monotonic() - m['go']
    m['walk_s'] = round(seconds, 1)
    assert seconds < 6.0, f'10 m through the grass took {seconds:.1f} s'
    return True


STEPS = [
    ('Every Plains and Jungle island has grass, the Plains thicker; the client has the same grass', lambda: None, everywhere, 6),
    ('No grass on the beach, a Port, a cave or the spring', lambda: None, kept_off, 6),
    ("A survivor walks 10 m through the starter island's thickest meadow at walking pace; grass blocks nothing", start_walk, walked, 15),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    lib.send_verification_gameplay_key_state(client, 'W', False)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t', 'go')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Grass success={error is None} error={error}')


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
            p = pawn.get_actor_location()
            raise TimeoutError(f'not done within {timeout} s; survivor at ({p.x:.0f}, {p.y:.0f}, {p.z:.0f})')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
