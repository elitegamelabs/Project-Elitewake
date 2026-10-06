"""Create the initial stance assets in the active project. Requires EWEditor.

An existing configured animation graph is preserved; its blend spaces are
revalidated and compiled. Run with Unreal's PythonScript commandlet or console.
"""
import unreal, json, os
assert os.path.normcase(os.path.abspath(unreal.Paths.project_dir())) == os.path.normcase('C:/UnrealProjects/EW')
ROOT='/Game/Elitewake/Animations'
LIB='/Game/FreeAnimationLibrary/Animations'
target=unreal.load_asset('/Game/Characters/Mannequins/Meshes/SK_Mannequin')
source=unreal.load_asset('/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SK_Mannequin')
assert source and target, 'Import FreeAnimationLibrary into the active project first.'
sp=unreal.AnimPoseExtensions.get_reference_pose(source)
tp=unreal.AnimPoseExtensions.get_reference_pose(target)
names=unreal.AnimPoseExtensions.get_bone_names(tp)
assert list(names) == list(unreal.AnimPoseExtensions.get_bone_names(sp))
assert all(unreal.AnimPoseExtensions.get_bone_pose(tp,n).is_near_equal(unreal.AnimPoseExtensions.get_bone_pose(sp,n),0.01,0.01,0.01) for n in names)
target.add_compatible_skeleton_soft(source)
source.add_compatible_skeleton_soft(target)
# AddCompatibleSkeletonSoft does not mark its package dirty; force persistence.
unreal.EditorAssetLibrary.save_loaded_asset(target, False)
unreal.EditorAssetLibrary.save_loaded_asset(source, False)
tools=unreal.AssetToolsHelpers.get_asset_tools()
def blendspace(name, folder, speed, clips):
    path=ROOT+'/'+name
    bs=unreal.load_asset(path)
    if not bs:
        factory=unreal.BlendSpaceFactoryNew()
        factory.set_editor_property('target_skeleton',target)
        bs=tools.create_asset(name,ROOT,unreal.BlendSpace,factory)
    params=list(bs.get_editor_property('blend_parameters'))
    for axis,label,low,high,grid in [(0,'Direction',-180,180,8),(1,'Speed',0,speed,4)]:
        p=params[axis]
        p.set_editor_property('display_name',label)
        p.set_editor_property('min',low)
        p.set_editor_property('max',high)
        p.set_editor_property('grid_num',grid)
    bs.set_editor_property('blend_parameters',params)
    samples=[]
    def sample(key,direction,velocity):
        source_path=LIB+'/'+folder+'/'+clips[key]
        owned_path=ROOT+'/Stances/'+clips[key]
        animation=unreal.load_asset(owned_path)
        if not animation:
            animation=unreal.EditorAssetLibrary.duplicate_asset(source_path,owned_path)
        assert animation, source_path
        # These imported clips contain root translation. CharacterMovement owns
        # displacement; lock private copies in place to avoid drifting each loop.
        animation.set_editor_property('enable_root_motion',False)
        animation.set_editor_property('force_root_lock',True)
        animation.set_editor_property('root_motion_root_lock',type(animation.get_editor_property('root_motion_root_lock')).REF_POSE)
        unreal.EditorAssetLibrary.save_loaded_asset(animation)
        value=unreal.BlendSample()
        value.set_editor_property('animation',animation)
        value.set_editor_property('sample_value',unreal.Vector(direction,velocity,0))
        return value
    for direction in [-180,0,180]:
        samples.append(sample('idle',direction,0))
    for direction,key in [(-180,'back'),(-135,'back_left'),(-90,'left'),(-45,'front_left'),(0,'front'),(45,'front_right'),(90,'right'),(135,'back_right'),(180,'back')]:
        samples.append(sample(key,direction,speed))
    assert all(s.get_editor_property('animation') for s in samples)
    bs.set_editor_property('sample_data',samples)
    assert unreal.EWAnimationEditorLibrary.compile_blend_space(bs), name
    unreal.EditorAssetLibrary.save_loaded_asset(bs)
    return bs
crouch=blendspace('BS_EWCrouch','Crouch',300,{'idle':'anim_Crouch_Idle','front':'anim_Crouch_Fwd_Loop','back':'anim_Crouch_Bwd_Loop','left':'anim_Crouch_Left_Loop','right':'anim_Crouch_Right_Loop','front_left':'anim_Crouch_Fwd_Left_Loop','front_right':'anim_Crouch_Fwd_Right_Loop','back_left':'anim_Crouch_Bwd_Left_Loop','back_right':'anim_Crouch_Bwd_Right_Loop'})
prone=blendspace('BS_EWProne','UnarmedProne',150,{'idle':'anim_Prone_Idle','front':'anim_Prone_Fwd_Loop_R','back':'anim_Prone_Bwd_Loop_R','left':'anim_Prone_Left_loop','right':'anim_Prone_Right_Loop','front_left':'anim_Prone_Fwd_Left_Loop','front_right':'anim_Prone_Fwd_Right_Loop','back_left':'anim_Prone_Bwd_Left_Loop','back_right':'anim_Prone_Bwd_Right_Loop'})
bp=unreal.load_asset(ROOT+'/ABP_EWLocomotion')
if not bp:
    bp=unreal.EditorAssetLibrary.duplicate_asset('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed',ROOT+'/ABP_EWLocomotion')
assert bp
def configure_graph(bp):
    graph=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'AnimGraph')
    event=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
    if 'EWIsProne' in [str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp,False)]:
        unreal.log('Stance blend spaces compiled; existing configured animation graph preserved.')
        return
    def pin(n,name):
        return next(p for p in n.list_all_pins() if str(p.get_pin_name())==name)
    def link(a,b):
        assert a.try_create_connection(b), str(a.get_pin_name())+' -> '+str(b.get_pin_name())
    def node(g,kind,x,y):
        n=g.create_node_from_name(kind,unreal.Vector2D(x,y),[])
        assert n,kind
        return n
    def get(g,name,x,y):
        n=g.add_get_member_variable_node(name)
        n.set_node_pos(unreal.IntPoint(x,y))
        return n
    for var in ['EWIsCrouching','EWIsProne']:
        assert event.add_member_variable(var)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    players=[]
    for bs,y in [(crouch,500),(prone,850)]:
        player=node(graph,'Animation|BlendSpaces|BlendspacePlayer',200,y)
        data=player.get_editor_property('node')
        data.set_editor_property('blend_space',bs)
        player.set_editor_property('node',data)
        direction=get(graph,'Direction',-50,y)
        speed=get(graph,'GroundSpeed',-50,y+80)
        link(pin(direction,'Direction'),pin(player,'X'))
        link(pin(speed,'GroundSpeed'),pin(player,'Y'))
        players.append(player)
    blends=[node(graph,'Animation|Blends|BlendPosesbybool',600,y) for y in [500,850]]
    slot=next(n for n in graph.list_all_nodes() if n.get_class().get_name()=='AnimGraphNode_Slot')
    base=pin(slot,'Source').list_connected_pins()[0]
    pin(slot,'Source').break_pin_links()
    link(base,pin(blends[0],'BlendPose_1')) # Bool false = index 1; true = index 0.
    link(pin(players[0],'Pose'),pin(blends[0],'BlendPose_0'))
    link(pin(blends[0],'Pose'),pin(blends[1],'BlendPose_1'))
    link(pin(players[1],'Pose'),pin(blends[1],'BlendPose_0'))
    link(pin(blends[1],'Pose'),pin(slot,'Source'))
    for b,var,y in [(blends[0],'EWIsCrouching',500),(blends[1],'EWIsProne',850)]:
        link(pin(get(graph,var,400,y-100),var),pin(b,'bActiveValue'))
        pin(b,'BlendTime_0').set_pin_value('0.2')
        pin(b,'BlendTime_1').set_pin_value('0.2')
    # Prone must bypass the standing foot-placement rig, which would lift crawling feet.
    rig=next(n for n in graph.list_all_nodes() if n.get_class().get_name()=='AnimGraphNode_ControlRig')
    alpha=graph.add_call_function_node('/Script/Engine.KismetMathLibrary.SelectFloat')
    pin(alpha,'A').set_pin_value('0')
    pin(alpha,'B').set_pin_value('1')
    link(pin(get(graph,'EWIsProne',850,950),'EWIsProne'),pin(alpha,'bPickA'))
    link(pin(alpha,'ReturnValue'),pin(rig,'Alpha'))
    # Refresh stance from this character on every animation update, including remote pawns.
    update=event.find_event_node('BlueprintUpdateAnimation')
    old=pin(update,'then').list_connected_pins()[0]
    pin(update,'then').break_pin_links()
    cast=node(event,'Utilities|Casting|CastToEWCharacter',-1000,-400)
    owner=event.add_call_function_node('/Script/Engine.AnimInstance.GetOwningActor')
    link(pin(owner,'ReturnValue'),pin(cast,'Object'))
    link(pin(update,'then'),pin(cast,'execute'))
    is_prone=event.add_call_function_node('/Script/EW.EWCharacter.IsProne')
    link(pin(cast,'AsEWCharacter'),pin(is_prone,'self'))
    crouching=event.add_get_member_variable_node('bIsCrouched','/Script/Engine.Character')
    link(pin(cast,'AsEWCharacter'),pin(crouching,'self'))
    set_prone=event.add_set_member_variable_node('EWIsProne')
    set_crouch=event.add_set_member_variable_node('EWIsCrouching')
    link(pin(cast,'then'),pin(set_prone,'execute'))
    link(pin(is_prone,'ReturnValue'),pin(set_prone,'EWIsProne'))
    link(pin(set_prone,'then'),pin(set_crouch,'execute'))
    link(pin(crouching,'bIsCrouched'),pin(set_crouch,'EWIsCrouching'))
    link(pin(set_crouch,'then'),old)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errors=[]
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        errors += list(unreal.BlueprintGraphEditor.get_graph_editor(g).list_nodes_with_errors())
    assert not errors, [n.get_name() for n in errors]
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    character=unreal.load_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
    cdo=unreal.get_default_object(character.generated_class())
    cdo.get_editor_property('mesh').set_editor_property('anim_class',bp.generated_class())
    unreal.BlueprintEditorLibrary.compile_blueprint(character)
    unreal.EditorAssetLibrary.save_loaded_asset(character)
    with open('C:/UnrealProjects/EW/Saved/M2ConfigurationResult.json','w') as f:json.dump({'success':True,'animation_blueprint':bp.get_path_name(),'crouch_samples':len(crouch.get_editor_property('sample_data')),'prone_samples':len(prone.get_editor_property('sample_data'))},f,indent=2)

configure_graph(bp)
