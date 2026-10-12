"""Saved 500 m depth and deep-water client/server capsule acceptance in PIE."""
import json, time
from pathlib import Path
import unreal

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
assert abs(center.z+extent.z+65)<.1 and abs(2*extent.z-50000)<.1
checks.append('Saved PIE ocean brush spans exactly 500 meters below the mean surface')
for p in [owner,pawn]:
    assert p.teleport(unreal.Vector(6200,0,-49900),unreal.Rotator())
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
            checks.append('Authority and owning client remain in Swimming near the 500 m seabed')
            client.set_control_rotation(unreal.Rotator(pitch=-90,yaw=0,roll=0))
            phase=1; deadline=time.monotonic()+3
        else:
            for p in [owner,pawn]:
                assert -49980 < p.get_actor_location().z < -49940, str(p.get_actor_location())
                assert move(p).is_swimming()
            checks.append('Client dives against the seabed; capsule collision prevents passing below the 500 m floor on both peers')
            finish()
    except Exception as error:finish(repr(error))
handle=unreal.register_slate_post_tick_callback(tick)
