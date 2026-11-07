"""Create an opt-in saved coastal gameplay blockout; never overwrite an existing map.

Resource pools use retained prototype definitions/yields. No recipe grants, new
canon island counts, swimming, wildlife or ship behavior are implied by scenery.
Run from the editor console with Play stopped and the current level saved.
"""
import json, math
from pathlib import Path
import unreal
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
assert not unreal.EditorLoadingSavingUtils.get_dirty_map_packages(), 'Save or discard your current level changes first'
assert not unreal.EditorAssetLibrary.does_asset_exist(MAP), 'Map exists: inspect it; never regenerate over edits'
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assets = unreal.AssetToolsHelpers.get_asset_tools()
shapes = {n: unreal.load_asset('/Engine/BasicShapes/' + n) for n in ['Cube', 'Cylinder', 'Sphere', 'Cone', 'Plane']}
items = {n: unreal.load_asset('/Game/Elitewake/Items/Testing/DA_Test' + n) for n in ['Wood', 'Thatch', 'Stone', 'Fiber', 'Sticks', 'AzulBerry']}
assert all(shapes.values()) and all(items.values())
materials = {}
for name, rgb, roughness in [('Sand', (.43,.32,.18),.95), ('Grass', (.045,.12,.025),.95), ('Rock', (.12,.14,.15),.9), ('Timber', (.12,.055,.022),.85), ('Leaves', (.025,.16,.045),.85), ('Sea', (.015,.15,.23),.18), ('FreshWater', (.025,.24,.28),.2)]:
    path = '/Game/Elitewake/World/Blockout/M_Coastal' + name
    material = unreal.load_asset(path)
    if not material:
        material = assets.create_asset('M_Coastal' + name, '/Game/Elitewake/World/Blockout', unreal.Material, unreal.MaterialFactoryNew())
        color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
        color.set_editor_property('constant', unreal.LinearColor(*rgb, 1))
        unreal.MaterialEditingLibrary.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
        rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
        rough.set_editor_property('r', roughness)
        unreal.MaterialEditingLibrary.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        unreal.MaterialEditingLibrary.recompile_material(material)
        assert unreal.EditorAssetLibrary.save_asset(path)
    materials[name] = material

assert level.new_level(MAP)
spawned = []
def mesh(label, shape, xyz, scale, mat, folder='Coast/Scenery', collision=True):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*xyz))
    a.set_actor_label(label); a.set_folder_path(folder)
    a.static_mesh_component.set_static_mesh(shapes[shape])
    a.static_mesh_component.set_material(0, materials[mat])
    a.set_actor_scale3d(unreal.Vector(*scale))
    if not collision: a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    spawned.append(a)
    return a

# Flat interior and terraced beach provide predictable collision for the first movement pass.
mesh('Coastal sea surface - visual only', 'Plane', (0,0,-65), (600,600,1), 'Sea', collision=False)
mesh('Main beach', 'Cylinder', (0,0,-160), (95,75,3.2), 'Sand', 'Coast/Terrain')
mesh('Island interior', 'Cylinder', (-1700,0,-126), (46,55,2.6), 'Grass', 'Coast/Terrain')
mesh('Distant islet beach', 'Cylinder', (9500,2600,-150), (32,26,3), 'Sand', 'Coast/Terrain')
mesh('Distant islet interior', 'Cylinder', (9500,2600,-116), (24,20,2.4), 'Grass', 'Coast/Terrain')
for i in range(20):
    t = i * math.tau / 20
    mesh('Coast rock %02d'%i, 'Sphere', (-2500+2300*math.cos(t),2100*math.sin(t),65), (3.2,2.4,2), 'Rock')

# Walkable dock boards, ramps and supports. No functional vessel is represented here.
for i in range(20):
    mesh('Dock plank %02d'%i, 'Cube', (4000+i*110,900,18), (1.05,5,.22), 'Timber', 'Coast/Dock')
for x in [4100,4600,5100,5600,6000]:
    for y in [650,1150]: mesh('Dock support', 'Cylinder', (x,y,-100), (.3,.3,2.5), 'Timber','Coast/Dock')
mesh('Dock landing', 'Cube', (4000,900,5), (5,7,.12), 'Timber','Coast/Dock')

def source(class_name, label, xyz, shape, scale, mat, props):
    a = actors.spawn_actor_from_class(unreal.load_class(None,'/Script/EW.'+class_name),unreal.Vector(*xyz))
    a.set_actor_label(label); a.set_folder_path('Coast/Resources')
    for k,v in props.items(): a.set_editor_property(k,v)
    component = a.get_editor_property('mesh')
    component.set_static_mesh(shapes[shape]); component.set_material(0,materials[mat])
    component.set_relative_scale3d(unreal.Vector(*scale))
    spawned.append(a)
    return a

for i, (x,y) in enumerate([(400,-120),(600,-200),(850,-160),(1050,-260)]):
    source('EWPickup','Loose Wood %d - E to collect'%(i+1),(x,y,25),'Cube',(1.4,.18,.18),'Timber',{'item_definition':items['Wood'],'quantity':5})
for i,(x,y) in enumerate([(450,160),(680,220),(900,160),(1120,240)]):
    source('EWPickup','Loose Stone %d - E to collect'%(i+1),(x,y,24),'Sphere',(.55,.45,.4),'Rock',{'item_definition':items['Stone'],'quantity':5})
for i,(x,y) in enumerate([(-700,-700),(-1400,-950),(-2000,-700),(-2600,450),(-1100,950),(-2200,1200)]):
    source('EWHarvestTree','Harvestable palm %d - equipped axe'%(i+1),(x,y,240),'Cylinder',(.55,.55,4.8),'Timber',{'wood':items['Wood'],'thatch':items['Thatch']})
    for j in range(5):
        leaf = mesh('Palm frond %d/%d'%(i,j),'Sphere',(x+125*math.cos(j*math.tau/5),y+125*math.sin(j*math.tau/5),485),(3.8,.65,.18),'Leaves','Coast/Vegetation',False)
        leaf.set_actor_rotation(unreal.Rotator(-15,j*72,0),False)
for i,(x,y) in enumerate([(-500,600),(-900,450),(-1500,650),(-1900,300)]):
    source('EWHandGatherable','Fiber plant %d - E to gather'%i,(x,y,45),'Cone',(1.2,1.2,.9),'Leaves',{'item_definition':items['Fiber'],'quantity':10})
for i,(x,y) in enumerate([(-850,750),(-1600,900)]):
    source('EWHandGatherable','Azren berry shrub %d - E to gather'%i,(x,y,50),'Sphere',(1.5,1.5,1),'Leaves',{'item_definition':items['AzulBerry'],'quantity':6,'gathering_kind':unreal.EWHandGatheringKind.BERRIES})
for i,(x,y) in enumerate([(-800,-250),(-1200,-450)]):
    source('EWMineable','Stone node %d - equipped pickaxe'%i,(x,y,55),'Sphere',(2,1.8,1.1),'Rock',{'resource':items['Stone']})
mesh('Freshwater basin rim','Cylinder',(-1700,1500,5),(5,5,.1),'Rock','Coast/FreshWater')
mesh('Freshwater surface','Cylinder',(-1700,1500,13),(4.5,4.5,.08),'FreshWater','Coast/FreshWater',False)
water = actors.spawn_actor_from_class(unreal.load_class(None,'/Script/EW.EWWaterSource'),unreal.Vector(-1700,1500,23))
water.set_actor_label('Freshwater spring - E to drink'); water.set_folder_path('Coast/FreshWater')
water.get_editor_property('interaction_surface').set_box_extent(unreal.Vector(205,205,18),False)
start = actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(150,0,100))
start.set_actor_rotation(unreal.Rotator(0,0,0),False)
start.set_actor_label('Beach landing spawn')
gm=unreal.EditorAssetLibrary.load_blueprint_class('/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode')
assert gm
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',gm)
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,1000))
sun.set_actor_rotation(unreal.Rotator(-35,-35,0),False)
sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',3)
actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector())
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,800))
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property('real_time_capture',True)
actors.spawn_actor_from_class(unreal.ExponentialHeightFog,unreal.Vector(0,0,-150))
assert world_map.save_map()
unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(5800,-6200,3600),unreal.Rotator(-22,140,0))
report={'map':MAP,'saved':True,'actors':len(actors.get_all_level_actors()),'resources':len([a for a in spawned if str(a.get_folder_path())=='Coast/Resources']),'limits':['Blockout geometry and provisional finite resource pools','Sea is visual only; no swimming or sailing','No wildlife actors yet','No starter recipe grants or introduction completion','Startup maps unchanged']}
Path(unreal.Paths.project_saved_dir(),'CoastalCreationResult.json').write_text(json.dumps(report,indent=2))
unreal.log('Coastal gameplay map saved: '+json.dumps(report))
