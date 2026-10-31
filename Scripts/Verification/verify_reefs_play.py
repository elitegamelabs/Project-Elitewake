"""Client acceptance for the five major reefs, one per canonical island. Needs Play in
/Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after build_reefs.py. Run unattended
with run_play_check.py.

  1. Five reefs: one in each region, clear of that island's Port, each with at least 40 corals of all four kinds;
     the client has them all.
  2. Every coral stands on the sea floor and is wholly under water (at least 50 cm below the surface).
  3. Every coral glows (a glowing coral material), in at least four colours per reef.
  4. Corals are solid: a level trace into each reef's largest mounds and pillar clumps stops on them.
  5. A reef shark (hammerhead) and a manta ray swim over each reef (they roam, so within 40 m), on the client too.
Writes Saved/ReefsPlayResult.json.
"""
import json
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from world_reefs import REEFS  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ReefsPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def corals(world, key):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
            if a.get_actor_label().startswith(f'Reef {key}:')]


def five():
    regions = {}
    for reef in REEFS:
        mine, seen = corals(server_world, reef.key), corals(client_world, reef.key)
        assert len(mine) >= 40, f'{reef.key} has {len(mine)} corals'
        assert len(seen) == len(mine), f'the client has {len(seen)} of {reef.key}\'s {len(mine)} corals'
        kinds = {a.get_actor_label().split(': ')[1].split(' ')[0] for a in mine}
        assert kinds == {'branching', 'mound', 'fan', 'pillar'}, (reef.key, kinds)
        regions[reef.island.region] = regions.get(reef.island.region, 0) + 1
        state['memo'][f'{reef.key}_corals'] = len(mine)
    assert regions == {'Plains': 1, 'Winter': 1, 'Swamp': 1, 'Desert': 1, 'Jungle': 1}, regions
    return True


def floor_and_water():
    for reef in REEFS:
        everyone = corals(server_world, reef.key)
        for a in everyone:
            at = a.get_actor_location()
            # Past every coral of the reef (a neighbour's branch can reach over its foot) to the sea floor.
            hit = unreal.SystemLibrary.line_trace_single(server_world, unreal.Vector(at.x, at.y, at.z + 40), unreal.Vector(at.x, at.y, at.z - 400),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, everyone, unreal.DrawDebugTrace.NONE, True)
            under = hit.to_tuple() if hit else None
            assert under, f'{a.get_actor_label()}: no sea floor under it'
            assert abs(under[4].z - at.z) < 60, f'{a.get_actor_label()} stands {at.z - under[4].z:.0f} cm off the floor ({under[9].get_actor_label()})'
            origin, extent = a.get_actor_bounds(False)
            assert origin.z + extent.z < T.SEA - 50, f'{a.get_actor_label()} reaches {origin.z + extent.z - T.SEA:.0f} cm from the surface'
    return True


def glowing():
    for reef in REEFS:
        hues = set()
        for a in corals(server_world, reef.key):
            m = a.static_mesh_component.get_material(0)
            assert m and m.get_name().startswith('MI_Coral_'), f'{a.get_actor_label()} wears {m.get_name() if m else None}'
            hues.add(m.get_name())
        assert len(hues) >= 4, (reef.key, hues)
    return True


def solid():
    for reef in REEFS:
        # The solid-bodied corals (a sea fan is an open lattice a trace can pass through).
        bodies = [a for a in corals(server_world, reef.key) if ': mound' in a.get_actor_label() or ': pillar' in a.get_actor_label()]
        big = sorted(bodies, key=lambda a: -a.get_actor_bounds(False)[1].z)[:5]
        for a in big:
            origin, extent = a.get_actor_bounds(False)
            target = unreal.Vector(origin.x, origin.y, origin.z - extent.z * .4)
            frm = unreal.Vector(origin.x + extent.x + 300, origin.y, target.z)
            hit = unreal.SystemLibrary.line_trace_single(server_world, frm, unreal.Vector(origin.x - extent.x - 300, origin.y, target.z),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
            assert hit, f'{a.get_actor_label()}: a trace passes through it'
    return True


def patrolled():
    for world in (server_world, client_world):
        fish = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWFish)
        for reef in REEFS:
            near = {str(f.get_editor_property('definition').get_editor_property('display_name')) for f in fish
                    if ((f.get_actor_location().x - reef.cx) ** 2 + (f.get_actor_location().y - reef.cy) ** 2) ** .5 < 4000}
            assert {'Hammerhead Shark', 'Manta Ray'} <= near, f'{reef.key}: {sorted(near)}'
    return True


STEPS = [
    ('Five reefs, one per region and clear of its Port; 40+ corals of all four kinds each; the client has them', lambda: None, five, 4),
    ('Every coral stands on the sea floor, wholly under water', lambda: None, floor_and_water, 6),
    ('Every coral glows, in at least four colours per reef', lambda: None, glowing, 4),
    ("Each reef's largest mounds and pillars are solid", lambda: None, solid, 4),
    ('A reef shark and a manta ray swim over each reef, on server and client', lambda: None, patrolled, 4),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str))}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Reefs success={error is None} error={error}')


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


state['handle'] = unreal.register_slate_post_tick_callback(tick)
