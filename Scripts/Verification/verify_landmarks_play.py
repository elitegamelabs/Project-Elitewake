"""Client acceptance for the island landmarks (owner, October 15: each island its own landmarks and skyline). Needs
Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after build_landmarks.py
and the dressing scripts. Run unattended with run_play_check.py.

  1. Every island has its one landmark from world_landmarks.py; all five kinds occur (sea stacks, arch, standing
     stones, spire, snag); the client has them all.
  2. They stand out: sea stacks, spires and snags rise at least 10 m above the sea; every standing stone stands at
     least 2.5 m; under every arch's crown there is at least 2.2 m of headroom.
  3. They are solid: a trace at each piece from outside (from above, or from inside a ring of stones) stops on it.
  4. No tree, rock, plant, pickup or animal stands on a landmark.
  5. A survivor walks (W held) along the shore under an arch, on the client.
Writes Saved/LandmarksPlayResult.json.
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
from world_landmarks import LANDMARKS  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'LandmarksPlayResult.json')
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


def pieces(world, key):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
            if a.get_actor_label().startswith(f'Landmark of {key}:')]


def hit(world, a, b, complex_=True):
    out = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, complex_, [owner, pawn],
                                                 unreal.DrawDebugTrace.NONE, True)
    if not out:
        return None, None
    t = out.to_tuple()
    return t[9].get_actor_label(), t[4]


def one_each():
    kinds = set()
    for key, mark in LANDMARKS.items():
        assert mark, f'{key} has no landmark'
        mine, seen = pieces(server_world, key), pieces(client_world, key)
        want = 1 if mark.kind in ('arch', 'snag', 'spire') else len(mark.parts)
        assert len(mine) == want, f'{key}: {len(mine)} pieces of its {mark.kind}, expected {want}'
        assert sorted(a.get_actor_label() for a in seen) == sorted(a.get_actor_label() for a in mine), f'the client lacks {key}\'s landmark'
        assert all(mark.kind.rstrip('s') in a.get_actor_label().split(': ')[1] for a in mine), [a.get_actor_label() for a in mine]
        kinds.add(mark.kind)
    # The only Plains island is the starter, which gets sea stacks; the retired extra-Plains standing-stone ring
    # does not occur in the canonical world.
    assert kinds == {'stacks', 'arch', 'spire', 'snag'}, kinds
    state['memo'].update({f'{k}_islands': sum(1 for m in LANDMARKS.values() if m.kind == k) for k in sorted(kinds)})
    return True


def stand_out():
    lowest = {}
    for key, mark in LANDMARKS.items():
        for a in pieces(server_world, key):
            origin, extent = a.get_actor_bounds(False)
            top = origin.z + extent.z
            at = a.get_actor_location()
            if mark.kind in ('stacks', 'spire', 'snag'):
                assert top - T.SEA > 1000, f'{a.get_actor_label()} rises only {(top - T.SEA) / 100:.1f} m above the sea'
                lowest[mark.kind] = min(lowest.get(mark.kind, 1e9), round((top - T.SEA) / 100, 1))
            elif mark.kind == 'stones':
                assert top - at.z > 250, f'{a.get_actor_label()} stands only {(top - at.z) / 100:.1f} m'
                lowest['stones'] = min(lowest.get('stones', 1e9), round((top - at.z) / 100, 1))
            elif mark.kind == 'arch':
                (ax, ay, az, _), (bx, by, bz, _) = mark.parts
                best = 0.0
                for f in (.3, .4, .5, .6):
                    x, y = ax + (bx - ax) * f, ay + (by - ay) * f
                    g = max(T.height(x, y), T.SEA)
                    label, where = hit(server_world, unreal.Vector(x, y, g + 20), unreal.Vector(x, y, g + 3000))
                    if label == a.get_actor_label():
                        best = max(best, where.z - g)
                assert best > 220, f'{a.get_actor_label()}: only {best / 100:.1f} m under the crown'
                lowest['arch_headroom'] = min(lowest.get('arch_headroom', 1e9), round(best / 100, 1))
    state['memo'].update({f'lowest_{k}_m': v for k, v in lowest.items()})
    return True


def solid():
    for key, mark in LANDMARKS.items():
        for a in pieces(server_world, key):
            origin, extent = a.get_actor_bounds(False)
            at = a.get_actor_location()
            z = (at.z + 120) if mark.kind in ('stones', 'snag') else max(at.z, T.SEA) + 250
            if mark.kind == 'arch':
                target = unreal.Vector(at.x, at.y, at.z + 100)    # the inland foot
            else:
                target = unreal.Vector(at.x, at.y, z)
            if mark.kind == 'stones':
                # From inside the ring, so the neighbouring stones are not in the way.
                cx = sum(q[0] for q in mark.parts) / len(mark.parts)
                cy = sum(q[1] for q in mark.parts) / len(mark.parts)
                frm = unreal.Vector(cx, cy, target.z)
            else:
                # From above, so a neighbouring stack is not in the way.
                frm = unreal.Vector(at.x, at.y, origin.z + extent.z + 500)
                target = unreal.Vector(at.x, at.y, at.z - 200)
            label, _ = hit(server_world, frm, target, False)
            assert label == a.get_actor_label(), f'{a.get_actor_label()}: a trace from outside meets {label}'
    return True


def clear():
    near = []
    for cls in DRESSING:
        for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, cls):
            p = a.get_actor_location()
            for key, mark in LANDMARKS.items():
                if mark.near(p.x, p.y, -50):
                    near.append(f'{a.get_actor_label()} on the {key} {mark.kind}')
    assert not near, near[:6]
    return True


ARCH = next(k for k, m in LANDMARKS.items() if m.kind == 'arch')


def start_walk():
    mark = LANDMARKS[ARCH]
    (ax, ay, az, _), (bx, by, bz, _) = mark.parts
    # On the shore under the arch: the point between the feet where the ground meets the sea, then along the shore.
    # Only through the middle of the span, clear of the feet (the bigger islands put some feet at the waterline).
    f = min((i / 20 for i in range(6, 15)), key=lambda f: abs(T.height(ax + (bx - ax) * f, ay + (by - ay) * f) - (T.SEA + 40)))
    mx, my = ax + (bx - ax) * f, ay + (by - ay) * f
    span = math.hypot(bx - ax, by - ay)
    tx, ty = -(by - ay) / span, (bx - ax) / span
    sx, sy = mx - tx * 900, my - ty * 900
    yaw = math.degrees(math.atan2(ty, tx))
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(sx, sy, max(T.height(sx, sy), T.SEA) + 120), unreal.Rotator(0, 0, yaw))
    for c in (client, owner.get_controller()):
        c.set_control_rotation(unreal.Rotator(0, 0, yaw))
    state['memo'].update(t=time.monotonic(), walking=False, start=(sx, sy), end=(mx + tx * 900, my + ty * 900), arch_island=ARCH)


def walked():
    m = state['memo']
    if not m['walking']:
        if time.monotonic() - m['t'] < 1.0:
            return False
        assert lib.send_verification_gameplay_key_state(client, 'W', True)
        m['walking'], m['go'] = True, time.monotonic()
    p = pawn.get_actor_location()
    if math.hypot(p.x - m['start'][0], p.y - m['start'][1]) < 1700:
        return False
    lib.send_verification_gameplay_key_state(client, 'W', False)
    assert math.hypot(p.x - m['end'][0], p.y - m['end'][1]) < 400, 'the survivor was turned aside on the way under the arch'
    m['arch_walk_s'] = round(time.monotonic() - m['go'], 1)
    return True


STEPS = [
    ('Every island has its landmark; stacks, arch, standing stones, spire and snag all occur; the client has them all', lambda: None, one_each, 4),
    ('Stacks, spires and snags rise over 10 m above the sea; standing stones over 2.5 m; arches leave 2.2 m of headroom', lambda: None, stand_out, 6),
    ('Every landmark piece is solid to a trace from outside', lambda: None, solid, 4),
    ('No tree, rock, plant, pickup or animal stands on a landmark', lambda: None, clear, 4),
    (f'A survivor walks along the shore under the arch on {ARCH}, on the client', start_walk, walked, 20),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    lib.send_verification_gameplay_key_state(client, 'W', False)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t', 'go')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Landmarks success={error is None} error={error}')


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
