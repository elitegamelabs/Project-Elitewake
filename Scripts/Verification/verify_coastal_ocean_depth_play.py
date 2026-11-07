"""Saved 1,500 m depth (owner, October 22; was 2,000 m) and deep-water client/server capsule acceptance in PIE: on the
open ocean's deepest, flat floor, both peers stay swimming and a dive stops on the sea floor."""
import json, sys, time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

DEPTH = T.SEA - T.DEEP          # 150,000 cm
x0, x1, y0, y1 = W.bounds(250000)
# A spot deep in the open ocean, at least 1,350 m down where the floor is nearly level (corners of the world first).
def _slope(x, y):
    return max(abs(T.height(x + dx, y + dy) - T.height(x, y)) for dx, dy in ((5000, 0), (0, 5000), (-5000, 0), (0, -5000)))
SPOT = min(((x0 + (x1 - x0) * i / 12, y0 + (y1 - y0) * j / 12) for i in range(13) for j in range(13)
            if T.height(x0 + (x1 - x0) * i / 12, y0 + (y1 - y0) * j / 12) < T.SEA - 135000), key=lambda q: _slope(*q))

worlds = unreal.EWEditorVerificationLibrary.get_play_worlds()
assert len(worlds) == 2
pcs = [unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server = next(w for w,c in zip(worlds,pcs) if c.has_authority())
pawn = client.get_controlled_pawn()
def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if pid(p)==pid(pawn))
checks=[]; phase=0; deadline=time.monotonic()+2; handle=None
move=lambda p:p.get_component_by_class(unreal.CharacterMovementComponent)
volume=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.PhysicsVolume) if a.get_editor_property('water_volume'))
center,extent=volume.get_actor_bounds(False)
assert abs(center.z+extent.z+65)<.1 and abs(2*extent.z-DEPTH)<.1, (center, extent)
checks.append('Saved PIE ocean brush spans exactly 1,500 meters below the mean surface')
_hit = unreal.SystemLibrary.line_trace_single(server, unreal.Vector(SPOT[0], SPOT[1], -1000), unreal.Vector(SPOT[0], SPOT[1], T.DEEP - 5000),
                                              unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
assert _hit, f'no sea floor under {SPOT}'
FLOOR_Z = _hit.to_tuple()[4].z
assert FLOOR_Z >= T.DEEP - 100 and FLOOR_Z < T.SEA - 125000, FLOOR_Z
checks.append(f'The open-ocean floor at {SPOT[0] / 100:.0f}, {SPOT[1] / 100:.0f} m lies {(T.SEA - FLOOR_Z) / 100:.0f} m down, no deeper than 1,500 m')
for p in [owner,pawn]:
    assert p.teleport(unreal.Vector(SPOT[0],SPOT[1],FLOOR_Z+165),unreal.Rotator())
    move(p).stop_movement_immediately()
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    for p in [owner,pawn]:
        p.teleport(unreal.Vector(150,0,200),unreal.Rotator())
        move(p).stop_movement_immediately()
    client.set_control_rotation(unreal.Rotator())
    Path(unreal.Paths.project_saved_dir(),'CoastalOceanDepthPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,deadline
    if phase==1: pawn.do_move(0,1)
    if time.monotonic()<deadline:return
    try:
        if phase==0:
            assert all(move(p).is_swimming() for p in [owner,pawn])
            checks.append('Authority and owning client remain in Swimming near the 1,500 m sea floor')
            client.set_control_rotation(unreal.Rotator(pitch=-90,yaw=0,roll=0))
            phase=1; deadline=time.monotonic()+3
        else:
            for p in [owner,pawn]:
                assert FLOOR_Z + 70 < p.get_actor_location().z < FLOOR_Z + 140, str(p.get_actor_location())
                assert move(p).is_swimming()
            checks.append('Client dives against the seabed; capsule collision prevents passing below the 1,500 m floor on both peers')
            finish()
    except Exception as error:finish(repr(error))
handle=unreal.register_slate_post_tick_callback(tick)
