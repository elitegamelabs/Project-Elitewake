"""Client acceptance for the caves, one per island (owner, October 14). Needs Play in
/Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after build_coastal_terrain.py,
build_caves.py and the dressing scripts. Run unattended with run_play_check.py.

  1. Every island has exactly one cave, at its site in world_terrain.py, and the entrances are of all three kinds
     (inland hill, cliff face, coastal rock); the client has every cave.
  2. Every cave is enclosed with a rock floor: from the chamber's middle, rock overhead, to both sides and behind,
     and rock underfoot at the floor's height; overhead and underfoot in the passage too; the way out of the mouth
     is open.
  3. No tree, rock, plant, pickup or animal stands on a cave's formation or in front of its mouth.
  4. A survivor set down outside the starter island's cave walks in (W held, steering along the passage) to the
     chamber, on the client, standing on the cave's floor the whole way.
  5. The same for a cliff-face cave and a Winter mountain-side cave.
Writes Saved/CavesPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'CavesPlayResult.json')
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
DRESSING = [unreal.EWAnimal, unreal.EWHandGatherable, unreal.EWHarvestTree, unreal.EWMineable, unreal.EWPickup, unreal.EWResourceNode]


def caves(world):
    return {a.get_actor_label().split(': ')[0][len('Cave of '):]: a
            for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
            if a.get_actor_label().startswith('Cave of ')}


def one_each():
    found, seen = caves(server_world), caves(client_world)
    keys = sorted(k for k, c in T.CAVES.items() if c)
    assert len(keys) == len(T.CAVES), 'an island has no cave site'
    assert sorted(found) == keys, f'caves {sorted(found)} for islands {keys}'
    assert sorted(seen) == keys, 'the client has a different set of caves'
    labels = [a.get_actor_label() for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.StaticMeshActor)]
    for key, cave in T.CAVES.items():
        assert labels.count(f'Cave of {key}: rock') == 1, f'{key} has more than one cave'
        at = found[key].get_actor_location()
        assert math.hypot(at.x - cave.mx, at.y - cave.my) < 10 and abs(at.z - cave.floor) < 10, key
    kinds = sorted({c.kind for c in T.CAVES.values()})
    assert kinds == ['cliff', 'coastal', 'inland'], kinds
    state['memo'].update(caves=len(keys), **{f'{k}_caves': sum(1 for c in T.CAVES.values() if c.kind == k) for k in kinds})
    return True


def hit(world, a, b):
    out = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [owner, pawn],
                                                 unreal.DrawDebugTrace.NONE, True)
    if not out:
        return None, None
    t = out.to_tuple()
    return t[9].get_actor_label(), t[4]


def at(cave, u, v, z):
    x, y = cave.world(u, v)
    return unreal.Vector(x, y, cave.floor + z)


def enclosed():
    for key, cave in T.CAVES.items():
        rock = f'Cave of {key}: rock'
        mid = at(cave, cave.chamber_u, 0, 200)
        for name, end in (('overhead', at(cave, cave.chamber_u, 0, 4000)), ('left', at(cave, cave.chamber_u, 4000, 200)),
                          ('right', at(cave, cave.chamber_u, -4000, 200)), ('behind', at(cave, cave.chamber_u + 4000, 0, 200))):
            label, _ = hit(server_world, mid, end)
            assert label == rock, f'{key} chamber: nothing {name} but {label}'
        label, where = hit(server_world, mid, at(cave, cave.chamber_u, 0, -600))
        assert label == rock and abs(where.z - cave.floor) < 30, f'{key} chamber floor: {label} at {where}'
        u = cave.length / 2
        inside = at(cave, u, cave.centre_v(u), 200)
        label, _ = hit(server_world, inside, at(cave, u, cave.centre_v(u), 4000))
        assert label == rock, f'{key} passage roof: {label}'
        label, where = hit(server_world, inside, at(cave, u, cave.centre_v(u), -600))
        assert label == rock and abs(where.z - cave.floor) < 30, f'{key} passage floor: {label} at {where}'
        label, _ = hit(server_world, at(cave, 150, cave.centre_v(150), 160), at(cave, -900, 0, 160))
        assert label is None or label != rock, f'{key}: the mouth is blocked by {label}'
    return True


def clear():
    near = []
    for cls in DRESSING:
        for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, cls):
            p = a.get_actor_location()
            for key, cave in T.CAVES.items():
                if cave.inside(p.x, p.y, 0):
                    near.append(f'{a.get_actor_label()} on the {key} cave')
    assert not near, near[:6]
    return True


def walk_into(key):
    cave = T.CAVES[key]

    def begin():
        x, y = cave.world(-350, 0)
        yaw = math.degrees(cave.heading)
        for p in (owner, pawn):
            assert p.teleport(unreal.Vector(x, y, cave.floor + 120), unreal.Rotator(0, 0, yaw))
        for c in (client, owner.get_controller()):
            c.set_control_rotation(unreal.Rotator(0, 0, yaw))
        state['memo'].update(t=time.monotonic(), walking=False, lowest=1e9, path=cave.path())

    def done():
        m = state['memo']
        if not m['walking']:
            if time.monotonic() - m['t'] < 1.0:
                return False
            assert lib.send_verification_gameplay_key_state(client, 'W', True)
            m['walking'] = True
        p = pawn.get_actor_location()
        u, v = cave.local(p.x, p.y)
        if u > 50:
            m['lowest'] = min(m['lowest'], p.z - cave.floor)
        # Steer for the point on the passage 2.5 m ahead, as a player would.
        ahead = next(((x, y) for x, y in m['path'] if cave.local(x, y)[0] > u + 250), m['path'][-1])
        client.set_control_rotation(unreal.Rotator(0, 0, math.degrees(math.atan2(ahead[1] - p.y, ahead[0] - p.x))))
        cx, cy = cave.world(cave.chamber_u, 0)
        if math.hypot(p.x - cx, p.y - cy) > 300:
            return False
        lib.send_verification_gameplay_key_state(client, 'W', False)
        assert abs(p.z - cave.floor - 96) < 60, f'the survivor is {p.z - cave.floor:.0f} cm above the {key} cave floor'
        assert m['lowest'] > 30, f'the survivor dropped to {m["lowest"]:.0f} cm above the floor on the way in'
        label, _ = hit(client_world, p, unreal.Vector(p.x, p.y, p.z - 400))
        assert label == f'Cave of {key}: rock', f'standing on {label} in the {key} chamber'
        m[f'{key}_walk_s'] = round(time.monotonic() - m['t'], 1)
        return True
    return begin, done


def pick(kind, region=None):
    return next(k for k, c in T.CAVES.items() if c.kind == kind and (region is None or c.island.region == region))


CLIFF, MOUNTAIN = pick('cliff'), pick('inland', 'Winter')
STEPS = [
    ('Every island has one cave at its site; inland, cliff and coastal entrances; the client has them all', lambda: None, one_each, 4),
    ('Every cave is enclosed in rock with a rock floor, and its mouth is open', lambda: None, enclosed, 8),
    ('No tree, rock, plant, pickup or animal stands on a cave or before its mouth', lambda: None, clear, 4),
    ("The survivor walks into the starter island's cave to its chamber, on the floor all the way", *walk_into('Starter'), 40),
    (f'... and into a cliff-face cave ({CLIFF})', *walk_into(CLIFF), 40),
    (f'... and into a Winter mountain-side cave ({MOUNTAIN})', *walk_into(MOUNTAIN), 40),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    lib.send_verification_gameplay_key_state(client, 'W', False)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t', 'lowest')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Caves success={error is None} error={error}')


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
