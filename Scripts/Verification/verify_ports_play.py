"""Client acceptance for the five regional Ports (owner, October 15). Needs Play in
/Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after build_coastal_terrain.py and
build_ports.py. Run unattended with run_play_check.py.

  1. Exactly one Port in each of the five regions, on the island world_layout.py names, each with its plaza, quay,
     pier, gate tower, landmark tower with a burning lantern, wall, and nine stone buildings of which some are shops;
     the client has them all.
  2. At every Port the buildings and the quay are solid: a survivor cannot walk through a building's wall, and stands
     on the quay rather than falling through it.
  3. A survivor set down at the end of the Plains Port's quay walks (W held) up the quay into the plaza, on the client.
  4. The Port is in its region's climate.
Writes Saved/PortsPlayResult.json.
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
RESULT = Path(unreal.Paths.project_saved_dir(), 'PortsPlayResult.json')
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
REGION = {'Plains': unreal.EWRegion.PLAINS, 'Winter': unreal.EWRegion.WINTER, 'Swamp': unreal.EWRegion.SWAMP,
          'Desert': unreal.EWRegion.DESERT, 'Jungle': unreal.EWRegion.JUNGLE}
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def port_actors(world, region):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
            if a.get_actor_label().startswith(f'Port of the {region}:')] + \
           [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PointLight)
            if a.get_actor_label().startswith(f'Port of the {region}:')]


def labels(world, region):
    return [a.get_actor_label().split(': ', 1)[1] for a in port_actors(world, region)]


def all_ports():
    m = state['memo']
    for region, port in W.PORTS.items():
        names = labels(server_world, region)
        seen = labels(client_world, region)
        need = ['plaza', 'quay', 'pier', 'gate tower', 'landmark tower', 'lantern', 'lantern light']
        missing = [n for n in need if n not in names]
        assert not missing, f'{region} Port lacks {missing}'
        houses = [n for n in names if n.startswith(('shop', 'house'))]
        shops = [n for n in names if n.startswith('shop')]
        walls = [n for n in names if n.startswith('wall')]
        assert len(houses) == 9 and 1 <= len(shops) < 9 and len(walls) >= 6, (region, len(houses), len(shops), len(walls))
        assert sorted(seen) == sorted(names), f'the client sees a different {region} Port'
        plaza = next(a for a in port_actors(server_world, region) if a.get_actor_label().endswith(': plaza'))
        at = plaza.get_actor_location()
        assert math.hypot(at.x - port.cx, at.y - port.cy) < 10 and port.island.region == region
        m[f'{region}_island'] = port.island.key
    return True


def blocked(world, a, b):
    hit = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner, pawn],
                                                 unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[9].get_actor_label() if hit else None


def solid():
    """A trace at chest height toward each building's middle from outside stops on the building; a trace down onto
    the quay stops on the quay."""
    for region, port in W.PORTS.items():
        for a in port_actors(server_world, region):
            label = a.get_actor_label()
            if ': shop' in label or ': house' in label:
                at = a.get_actor_location()
                outside = unreal.Vector(at.x + (port.cx - at.x) * .9, at.y + (port.cy - at.y) * .9, at.z + 150)
                hit = blocked(server_world, outside, unreal.Vector(at.x, at.y, at.z + 150))
                assert hit == label, f'{label}: a walk into it is not stopped ({hit})'
        qx, qy = port.world(W.PORT_INLAND + 2500, 0)
        on = blocked(server_world, unreal.Vector(qx, qy, T.PORT_LEVEL + 600), unreal.Vector(qx, qy, T.PORT_LEVEL - 900))
        assert on and on.endswith(': quay'), f'{region}: nothing to stand on along the quay ({on})'
    return True


def to_quay_end():
    port = W.PORTS['Plains']
    x, y = port.world(W.PORT_INLAND + 3600, 0)
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(x, y, T.PORT_LEVEL + 200), unreal.Rotator(0, 0, math.degrees(port.facing) + 180))
    yaw = math.degrees(port.facing) + 180
    for c in (client, owner.get_controller()):
        c.set_control_rotation(unreal.Rotator(0, 0, yaw))
    state['memo'].update(t=time.monotonic(), start=unreal.Vector(x, y, 0), walking=False)


def walked_in():
    m = state['memo']
    port = W.PORTS['Plains']
    if not m['walking'] and time.monotonic() - m['t'] > 1.0:
        assert lib.send_verification_gameplay_key_state(client, 'W', True)
        m['walking'] = True
    at = pawn.get_actor_location()
    along, across = port.local(at.x, at.y)
    if along > W.PORT_PAD - 600:
        return False
    lib.send_verification_gameplay_key_state(client, 'W', False)
    assert abs(at.z - (T.PORT_LEVEL + 96)) < 140, f'the survivor is at {at.z:.0f}, not walking on the stone'
    m['walked_m'] = round((m['start'] - at).length() / 100)
    m['walk_s'] = round(time.monotonic() - m['t'], 1)
    return True


def climates():
    for region, port in W.PORTS.items():
        c = unreal.EWClimateRegion.sample_climate(server_world, unreal.Vector(port.cx, port.cy, 0))
        assert c.region == REGION[region], (region, c.region)
    return True


STEPS = [
    ('One Port in each region on its island, with plaza, quay, pier, gate and landmark towers, a lit lantern, walls and nine stone buildings (some shops); the client has them all', lambda: None, all_ports, 6),
    ('Every Port is solid: no walking through a building, and the quay holds a survivor up', lambda: None, solid, 6),
    ("From the end of the Plains Port's quay, W walks the survivor up the quay into the plaza", to_quay_end, walked_in, 25),
    ("Each Port lies in its region's climate", lambda: None, climates, 2),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    lib.send_verification_gameplay_key_state(client, 'W', False)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k != 't'}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Ports success={error is None} error={error}')


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
            at = pawn.get_actor_location()
            raise TimeoutError(f'not done within {timeout} s; survivor at ({at.x:.0f}, {at.y:.0f}, {at.z:.0f})')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
