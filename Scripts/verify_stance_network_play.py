"""Run in an in-process listen-server plus one-client Play session.

Inject client input and verify its authoritative pawn and animation states in
both worlds. This tests local replication; it does not simulate network latency.
"""
import unreal,json,os,traceback
worlds=unreal.EWEditorVerificationLibrary.get_play_worlds()
assert len(worlds)==2, 'Start an in-process listen server and one client.'
controllers=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
controller=next(c for c in controllers if c and not c.has_authority())
pawn=controller.get_controlled_pawn()
world=next(w for w,c in zip(worlds,controllers) if c==controller)
subsystem=unreal.EWEditorVerificationLibrary.get_player_input_subsystem(controller)
stance=pawn.get_editor_property('stance_action')
sprint=pawn.get_editor_property('sprint_action')
move=pawn.get_editor_property('move_action')
active=False
other_actions={}
report={'success':False,'checkpoints':[],'errors':[]}
path=os.path.join(unreal.Paths.project_saved_dir(),'M2StanceNetworkResult.json')
settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
previous_throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
character_class=unreal.load_class(None,'/Script/EW.EWCharacter')
def player_id(actor):
    state=actor.get_editor_property('PlayerState')
    return json.loads(unreal.ToolsetLibrary.get_object_properties(state,['PlayerId']))['PlayerId']
owner_id=player_id(pawn)

def switch_to_host():
    global controller,pawn,world,subsystem,stance,owner_id
    controller=next(c for c in controllers if c and c.has_authority())
    pawn=controller.get_controlled_pawn()
    world=next(w for w,c in zip(worlds,controllers) if c==controller)
    subsystem=unreal.EWEditorVerificationLibrary.get_player_input_subsystem(controller)
    stance=pawn.get_editor_property('stance_action')
    owner_id=player_id(pawn)
def press():
    global active
    active=True
def release():
    global active
    active=False
def check(label,state):
    rows=[]
    report['checkpoints'].append({'label':label,'pawns':rows})
    for w in worlds:
        p=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,character_class) if player_id(a)==owner_id)
        anim=p.get_editor_property('mesh').get_anim_instance()
        capsule=p.get_editor_property('capsule_component')
        row={'world':w.get_path_name(),'authority':p.has_authority(),'role':str(p.get_local_role()),'state':str(p.get_locomotion_state()),'prone':p.is_prone,'animation_prone':anim.get_editor_property('EWIsProne'),'animation_crouching':anim.get_editor_property('EWIsCrouching'),'half_height_cm':capsule.get_scaled_capsule_half_height(),'sprinting':p.is_sprinting}
        row['root_height_above_capsule_bottom_cm']=p.get_editor_property('mesh').get_socket_location('root').z-p.get_actor_location().z+capsule.get_scaled_capsule_half_height()
        rows.append(row)
        assert p.get_locomotion_state()==state, label+': replicated locomotion differs'
        assert anim.get_editor_property('EWIsProne')==p.is_prone, label+': replicated animation differs'
        lowered=state in (unreal.EWLocomotionState.CROUCHING,unreal.EWLocomotionState.PRONE)
        assert anim.get_editor_property('EWIsCrouching')==lowered, label+': crouch animation differs'
        expected_height=28 if state==unreal.EWLocomotionState.PRONE else (60 if lowered else 90)
        assert abs(row['half_height_cm']-expected_height)<.1, label+': collision size differs'
        assert row['sprinting']==(state==unreal.EWLocomotionState.SPRINTING), label+': sprint state differs'
        assert abs(row['root_height_above_capsule_bottom_cm']-1)<8, label+': remote mesh anchor differs'
S=unreal.EWLocomotionState
steps=[(press,.1),(release,.8),(lambda:check('client tap crouch',S.CROUCHING),.1),
       (press,.8),(release,.8),(lambda:check('client hold prone',S.PRONE),.1),
       (press,.1),(release,.8),(lambda:check('client prone to crouch',S.CROUCHING),.1),
       (press,.1),(release,.8),(lambda:check('client crouch to stand',S.STANDING),.1),
       (press,.8),(release,.8),(lambda:check('client reenter prone',S.PRONE),.1),
       (lambda:other_actions.update({sprint:unreal.Vector(1,0,0),move:unreal.Vector(0,1,0)}),.8),
       (lambda:check('client prone sprint exit',S.SPRINTING),.1),
       (other_actions.clear,.8),(lambda:check('client stop sprint',S.STANDING),.1),
       (switch_to_host,.3),
       (press,.1),(release,.8),(lambda:check('host crouch / simulated proxy',S.CROUCHING),.1),
       (press,.8),(release,.8),(lambda:check('host prone / simulated proxy',S.PRONE),.1),
       (press,.1),(release,.8),(lambda:check('host prone to crouch / simulated proxy',S.CROUCHING),.1),
       (press,.1),(release,.8),(lambda:check('host stand / simulated proxy',S.STANDING),.1)]
index=0
next_time=unreal.GameplayStatics.get_time_seconds(world)+.5
handle=None
def finish():
    release()
    other_actions.clear()
    settings.set_editor_property('bThrottleCPUWhenNotForeground',previous_throttle)
    report['success']=not report['errors'] and index==len(steps)
    with open(path,'w') as f:json.dump(report,f,indent=2)
    unreal.unregister_slate_post_tick_callback(handle)
def tick(delta):
    global index,next_time
    try:
        if any(w not in unreal.EWEditorVerificationLibrary.get_play_worlds() for w in worlds):
            report['errors'].append('Play ended before verification finished.')
            finish()
            return
        if active:subsystem.inject_input_vector_for_action(stance,unreal.Vector(1,0,0),[],[])
        for action,value in list(other_actions.items()):subsystem.inject_input_vector_for_action(action,value,[],[])
        now=unreal.GameplayStatics.get_time_seconds(world)
        if now<next_time:return
        if index==len(steps):
            finish()
            return
        action,wait=steps[index]
        action()
        index+=1
        next_time=now+wait
    except Exception:
        report['errors'].append(traceback.format_exc())
        finish()
handle=unreal.register_slate_post_tick_callback(tick)
