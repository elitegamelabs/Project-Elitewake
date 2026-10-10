"""Fresh listen server + one client; session-only ordered objective acceptance."""
import unreal, json, time
from pathlib import Path
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds()
pcs=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
client=next(c for c in pcs if not c.has_authority())
host=next(c for c in pcs if c.has_authority())
server_world=worlds[pcs.index(host)]
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
original=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world,unreal.EWCharacter) if pid(p)==pid(client.get_controlled_pawn()))
server_pc=original.get_controller()
authority=server_pc.get_objective_component()
remote=client.get_objective_component()
assert not authority.get_state().steps and not remote.get_state().steps
first=unreal.EWObjectiveStep();first.set_editor_property('id','Test.First');first.set_editor_property('description','Diagnostic first objective');first.set_editor_property('required_count',2)
last=unreal.EWObjectiveStep();last.set_editor_property('id','Test.Last');last.set_editor_property('description','Diagnostic last objective')
assert authority.start_sequence('Test.Objectives',[first,last])
checks=[];phase=0;next_at=time.monotonic()+3;handle=None;fixture=None
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    if fixture:
        server_pc.possess(original)
        fixture.destroy_actor()
    Path(unreal.Paths.project_saved_dir(),'ObjectivesPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at,fixture
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0:
            state=remote.get_state()
            assert len(state.steps)==2 and state.step_index==0 and state.progress==0
            assert not host.get_objective_component().get_state().steps
            assert not remote.record_progress('Test.First')
            assert not remote.start_sequence('Client.Fake',[last])
            assert not authority.record_progress('Test.Last')
            checks.append('Owning client receives ordered definition; host remains empty; client and out-of-order writes reject')
            assert authority.record_progress('Test.First')
        elif phase==1:
            assert remote.get_state().progress==1 and remote.get_state().step_index==0
            checks.append('Partial server progress replicates to owning client')
            fixture=lib.spawn_verification_recipe_character(server_world,original.get_class(),original.get_actor_location()+unreal.Vector(250,0,0),[])
            assert fixture
            server_pc.possess(fixture)
        elif phase==2:
            assert client.get_controlled_pawn().get_name()==fixture.get_name() and remote.get_state().progress==1
            checks.append('Objective progress survives pawn replacement within controller session')
            assert authority.record_progress('Test.First',2147483647)
        elif phase==3:
            assert remote.get_state().step_index==1 and remote.get_state().progress==0 and not remote.is_complete()
            assert not authority.record_progress('Test.First')
            checks.append('Large count advances only current step; stale report rejects')
            assert authority.record_progress('Test.Last')
        elif phase==4:
            assert remote.is_complete() and not host.get_objective_component().is_complete()
            assert not authority.record_progress('Test.Last')
            assert not authority.start_sequence('Test.Objectives',[last])
            checks.append('Completion replicates only to owner; repeat and restart reject')
            finish();return
        phase+=1
    except Exception as exc: finish(f'Phase {phase}: {exc!r}')
handle=unreal.register_slate_post_tick_callback(tick)
