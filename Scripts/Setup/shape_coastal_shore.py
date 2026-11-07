"""Author an original irregular sloped shoreline mesh without moving gameplay resources."""
import math, json
from pathlib import Path
import unreal
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)
assert not unreal.EWEditorVerificationLibrary.get_play_worlds()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_name() == 'Lvl_CoastalPlayground'
path = '/Game/Elitewake/World/Meshes/SM_CoastalShore_v2'
mesh = unreal.load_asset(path)
if not mesh:
    segments = 128
    rings = [(.2,0),(.4,0),(.6,0),(.72,0),(.80,-8),(.88,-30),(.94,-70),(1,-130),(1.08,-200)]
    verts = [unreal.Vector()]; triangles = []; uv = [unreal.Vector2D(.5,.5)]
    for radius, height in rings:
        for i in range(segments):
            angle = i*math.tau/segments
            variation = 1 + max(0,radius-.6)*(.12*math.sin(angle*3+.7)+.08*math.sin(angle*7))
            x = 4750*radius*variation*math.cos(angle)
            y = 3750*radius*variation*math.sin(angle)
            verts.append(unreal.Vector(x,y,height)); uv.append(unreal.Vector2D(x/9500+.5,y/7500+.5))
    for i in range(segments): triangles.append(unreal.IntVector(0,1+i,1+(i+1)%segments))
    for ring in range(len(rings)-1):
        for i in range(segments):
            a=1+ring*segments+i; b=1+ring*segments+(i+1)%segments
            c=a+segments; d=b+segments
            triangles += [unreal.IntVector(a,c,d),unreal.IntVector(a,d,b)]
    # A closed island solid gives swimming capsules real collision at the submerged edge.
    bottom_start = len(verts)
    outer_start = 1 + (len(rings)-1)*segments
    for i in range(segments):
        top = verts[outer_start+i]
        verts.append(unreal.Vector(top.x,top.y,-1200)); uv.append(uv[outer_start+i])
    bottom_center = len(verts)
    verts.append(unreal.Vector(0,0,-1200)); uv.append(unreal.Vector2D(.5,.5))
    for i in range(segments):
        j=(i+1)%segments
        a=outer_start+i; b=outer_start+j; c=bottom_start+i; d=bottom_start+j
        triangles += [unreal.IntVector(a,c,d),unreal.IntVector(a,d,b),
                      unreal.IntVector(bottom_center,d,c)]
    dynamic = unreal.DynamicMesh()
    buffers = unreal.GeometryScriptSimpleMeshBuffers(vertices=verts, triangles=triangles, uv0=uv)
    unreal.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,buffers)
    options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions(enable_recompute_normals=True,
        enable_recompute_tangents=True, enable_collision=True,
        collision_mode=unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
    mesh, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,options)
    assert mesh, outcome
    # Explicit simple hulls support CharacterMovement's capsule sweeps, while
    # complex traces retain the authored surface. Do not rely on a render-only mesh.
    assert unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_convex_decomposition_collisions(mesh,32,32,100000)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() == 'Main beach':
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(1,1,1)); actor.set_actor_location(unreal.Vector(),False,False)
    elif actor.get_actor_label() == 'Distant islet beach':
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(.337,.347,1)); actor.set_actor_location(unreal.Vector(9500,2600,0),False,False)
assert world_map.save_map()
(Path(unreal.Paths.project_saved_dir())/'CoastalShoreResult.json').write_text(json.dumps({'success':True,
    'mesh':path,'description':'Original irregular shoreline with sloped water entry; retained flat interior/resource locations',
    'limits':'Prototype island layout; full landscape/vegetation art remains open'},indent=2))
