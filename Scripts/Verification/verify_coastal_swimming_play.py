"""Actual saved ocean volume + owning-client predicted movement acceptance in two-player PIE.
Only teleports for initial setup; swim/diving phases use ordinary character input.
"""
import json, time
from pathlib import Path
import unreal
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert len(worlds) == 2
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server = next(w for w, c in zip(worlds, pcs) if c.has_authority())
pawn = client.get_controlled_pawn()
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']
owner = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server, unreal.EWCharacter) if pid(a) == pid(pawn))
movement = lambda p: p.get_component_by_class(unreal.CharacterMovementComponent)
checks = []; phase = 0; deadline = time.monotonic() + 1; handle = None
origin = None
def place(xyz):
    for p in [owner, pawn]:
        assert p.teleport(unreal.Vector(*xyz), unreal.Rotator()), ('Setup teleport rejected',xyz,p.get_name())
        movement(p).stop_movement_immediately()
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    pawn.do_jump_end()
    place((150,0,200))
    client.set_control_rotation(unreal.Rotator())
    (Path(unreal.Paths.project_saved_dir())/'CoastalSwimmingResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase, deadline, origin
    if phase in [2,4,8]: pawn.do_move(0,1)
    if time.monotonic() < deadline: return
    deadline = time.monotonic() + 2
    try:
        if phase == 0:
            assert not movement(owner).is_swimming() and not movement(owner).is_falling(), (str(owner.get_actor_location()),str(movement(owner).movement_mode))
            checks.append('Normal beach spawn stays grounded outside swimming volume')
            place((6200,0,-180))
        elif phase == 1:
            assert movement(owner).is_swimming() and movement(pawn).is_swimming(), [(str(p.get_actor_location()),str(movement(p).movement_mode),p.get_component_by_class(unreal.CapsuleComponent).get_physics_volume().get_name()) for p in [owner,pawn]]
            assert owner.get_locomotion_state() == unreal.EWLocomotionState.SWIMMING
            checks.append('Actual saved water brush enters Swimming on authority and client')
            origin = owner.get_actor_location()
            client.set_control_rotation(unreal.Rotator(0,0,0))
        elif phase == 2:
            loc = owner.get_actor_location()
            assert loc.x > origin.x + 100, (origin,loc)
            assert (loc-pawn.get_actor_location()).length() < 150
            checks.append('Owning-client swim input travels over 1 m and reaches server without a teleport/RPC movement bypass')
            origin = loc
            client.set_control_rotation(unreal.Rotator(pitch=-45,yaw=0,roll=0))
        elif phase == 3:
            origin = owner.get_actor_location()
        elif phase == 4:
            assert owner.get_actor_location().z < origin.z - 100, (str(origin),str(owner.get_actor_location()),str(client.get_control_rotation()),str(movement(owner).velocity))
            assert movement(owner).is_swimming()
            checks.append('Looking down and moving forward dives using predicted movement')
            origin = owner.get_actor_location()
            client.set_control_rotation(unreal.Rotator())
            pawn.do_jump_start()
        elif phase == 5:
            assert owner.get_actor_location().z > origin.z + 100, (str(origin),str(owner.get_actor_location()))
            checks.append('Held jump input ascends underwater on the client and authority')
            pawn.do_jump_end()
            client.set_control_rotation(unreal.Rotator(pitch=25,yaw=180,roll=0))
        elif phase == 6:
            # Drain old predicted dive moves before arranging a separate shoreline case.
            place((5500,0,-180))
        elif phase == 7:
            deadline = time.monotonic()+12
        elif phase == 8:
            assert not movement(owner).is_swimming() and not movement(owner).is_falling(), [(str(p.get_actor_location()),str(movement(p).movement_mode),str(movement(p).velocity)) for p in [owner,pawn]]
            assert len(owner.get_inventory_component().get_available_recipes()) == 0
            checks.append('Client swims from offshore up the sloped beach to grounded movement; intro recipe locks remain intact')
            place((6200,0,-400))
            deadline = time.monotonic() + 8
        elif phase == 9:
            # An idle swimmer rises from 3 m down and floats with head and shoulders out (water surface Z -65).
            for p in [owner, pawn]:
                z = p.get_actor_location().z
                assert movement(p).is_swimming() and -140 < z < -90, (p.get_name(), z, str(movement(p).movement_mode))
            checks.append('An idle swimmer floats back up and rests at the surface, head out, on authority and client')
            finish(); return
        phase += 1
    except Exception as e: finish('phase '+str(phase)+': '+repr(e))
handle = unreal.register_slate_post_tick_callback(tick)
