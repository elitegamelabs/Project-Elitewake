"""Upgrade the existing coastal scene in place; preserves resources and owner settings.
Run outside Play, with no dirty map packages. Existing upgrade assets are reused.
"""
import json
import runpy
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EWEditorVerificationLibrary
assert not lib.get_play_worlds(), 'Stop Play first'
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(), 'Save current map first'
assert level.load_level('/Game/Elitewake/Maps/Lvl_CoastalPlayground')
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
all_actors = actors.get_all_level_actors()
sea = next(a for a in all_actors if a.get_actor_label().startswith('Coastal sea surface'))
sea.set_actor_label('Coastal sea surface - swimmable ocean')
sea.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
volume = next((a for a in all_actors if a.get_actor_label() == 'Coastal ocean swimming volume'), None)
if volume and 'CoastalWaterV2' not in [str(t) for t in volume.tags]:
    actors.destroy_actor(volume)
    volume = None
if not volume:
    # The shared depth helper below aligns the brush and seabed to owner depth.
    water_mesh = unreal.DynamicMesh()
    unreal.GeometryScript_Primitives.append_box(water_mesh, unreal.GeometryScriptPrimitiveOptions(), unreal.Transform(), 60000, 60000, 3000, origin=unreal.GeometryScriptPrimitiveOriginMode.CENTER)
    volume, _, outcome = unreal.GeometryScript_NewAssetUtils.create_new_volume_from_mesh(water_mesh, world,
        unreal.Transform(location=unreal.Vector(0,0,-1565)), 'CoastalOcean',
        unreal.GeometryScriptCreateNewVolumeFromMeshOptions(volume_type=unreal.PhysicsVolume))
    assert volume, 'Brush-backed swimming volume authoring failed'
    volume.set_editor_property('water_volume', True)
    volume.set_editor_property('physics_on_contact', False)
    volume.set_editor_property('fluid_friction', .3)
    volume.set_editor_property('priority', 10)
    volume.tags = ['CoastalWaterV2']
    volume.set_actor_label('Coastal ocean swimming volume')
    volume.set_folder_path('Coast/Ocean')

assets = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
dest = '/Game/Elitewake/World/Materials'
def expression(mat, cls, **props):
    node = mel.create_material_expression(mat, cls)
    for key, value in props.items(): node.set_editor_property(key, value)
    return node
def link(a, b, pin, output=''):
    names = mel.get_material_expression_input_names(b)
    if pin == 'Coordinates': pin = 'UVs'
    if pin == '': pin = names[0]
    assert pin in names, (b.get_name(), pin, names)
    assert mel.connect_material_expressions(a, output, b, pin), (b.get_name(), pin)
def prop(node, pin): assert mel.connect_material_property(node, '', pin)
def scalar(mat, value): return expression(mat, unreal.MaterialExpressionConstant, r=value)
def color(mat, rgb): return expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(*rgb, 1))

changes = []
for name, source, labels, tile in [
    ('Sand', 'TropicalSand-v1.png', ['Main beach', 'Distant islet beach'], 300.0),
    ('Timber', 'WeatheredTimber-v1.png', ['Dock plank', 'Dock landing', 'Dock support'], 180.0)
]:
    filename = root / 'Art/Environment' / source
    if not filename.is_file(): continue
    tex_path = dest + '/T_' + name + '_v1'
    if not unreal.EditorAssetLibrary.does_asset_exist(tex_path):
        task = unreal.AssetImportTask()
        for key, value in {'filename': str(filename), 'destination_path':dest,
            'destination_name':'T_'+name+'_v1', 'automated':True, 'replace_existing':False, 'save':True}.items():
            task.set_editor_property(key, value)
        assets.import_asset_tasks([task])
    texture = unreal.load_asset(tex_path)
    assert isinstance(texture, unreal.Texture2D)
    path = dest + '/M_' + name + '_v1'
    material = unreal.load_asset(path)
    if not material:
        material = assets.create_asset('M_'+name+'_v1', dest, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(material)
    sample = expression(material, unreal.MaterialExpressionTextureSample, texture=texture)
    position = expression(material, unreal.MaterialExpressionWorldPosition)
    mask = expression(material, unreal.MaterialExpressionComponentMask, r=True, g=True)
    uv = expression(material, unreal.MaterialExpressionMultiply)
    link(position, mask, ''); link(mask, uv, 'A'); link(scalar(material, 1/tile), uv, 'B')
    link(uv, sample, 'Coordinates')
    prop(sample, unreal.MaterialProperty.MP_BASE_COLOR)
    prop(scalar(material, .87), unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    for actor in all_actors:
        if any(actor.get_actor_label().startswith(label) for label in labels):
            actor.static_mesh_component.set_material(0, material)
            changes.append(actor.get_actor_label())

path = dest + '/M_Ocean_v1'
ocean = unreal.load_asset(path)
if not ocean:
    ocean = assets.create_asset('M_Ocean_v1', dest, unreal.Material, unreal.MaterialFactoryNew())
mel.delete_all_material_expressions(ocean)
ocean.set_editor_property('tangent_space_normal', False)
# World-space sine-wave normals, animated independently of the static physics surface.
position = expression(ocean, unreal.MaterialExpressionWorldPosition)
clock = expression(ocean, unreal.MaterialExpressionTime)
normals = []; heights = []
for rgb, rate in [((.0005,.00015,0),.09), ((-.0002,.0007,0),.12)]:
    dot = expression(ocean, unreal.MaterialExpressionDotProduct)
    link(position, dot, 'A'); link(color(ocean, rgb), dot, 'B')
    speed = expression(ocean, unreal.MaterialExpressionMultiply)
    link(clock, speed, 'A'); link(scalar(ocean, rate), speed, 'B')
    phase = expression(ocean, unreal.MaterialExpressionAdd)
    link(dot, phase, 'A'); link(speed, phase, 'B')
    sine = expression(ocean, unreal.MaterialExpressionSine); link(phase, sine, '')
    height = expression(ocean, unreal.MaterialExpressionMultiply)
    link(sine, height, 'A'); link(scalar(ocean, 8), height, 'B'); heights.append(height)
    strength = expression(ocean, unreal.MaterialExpressionMultiply)
    link(sine, strength, 'A'); link(scalar(ocean, .09), strength, 'B')
    normals.append(strength)
xy = expression(ocean, unreal.MaterialExpressionAppendVector)
link(normals[0], xy, 'A'); link(normals[1], xy, 'B')
xyz = expression(ocean, unreal.MaterialExpressionAppendVector)
link(xy, xyz, 'A'); link(scalar(ocean, 1), xyz, 'B')
normal = expression(ocean, unreal.MaterialExpressionNormalize); link(xyz, normal, '')
prop(normal, unreal.MaterialProperty.MP_NORMAL)
height_sum = expression(ocean, unreal.MaterialExpressionAdd)
link(heights[0], height_sum, 'A'); link(heights[1], height_sum, 'B')
offset = expression(ocean, unreal.MaterialExpressionAppendVector)
link(expression(ocean, unreal.MaterialExpressionConstant2Vector, r=0, g=0), offset, 'A')
link(height_sum, offset, 'B'); prop(offset, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
prop(color(ocean, (.012,.10,.145)), unreal.MaterialProperty.MP_BASE_COLOR)
prop(scalar(ocean,.15), unreal.MaterialProperty.MP_ROUGHNESS)
prop(scalar(ocean,.65), unreal.MaterialProperty.MP_SPECULAR)
mel.recompile_material(ocean)
assert unreal.EditorAssetLibrary.save_loaded_asset(ocean)
sea.static_mesh_component.set_material(0, ocean)
surface_path = '/Game/Elitewake/World/Meshes/SM_OceanSurface_v1'
surface_mesh = unreal.load_asset(surface_path)
if not surface_mesh:
    dynamic = unreal.DynamicMesh()
    unreal.GeometryScript_Primitives.append_rectangle_xy(dynamic, unreal.GeometryScriptPrimitiveOptions(),
        unreal.Transform(), 60000, 60000, 128, 128)
    surface_mesh, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,
        surface_path, unreal.GeometryScriptCreateNewStaticMeshAssetOptions(enable_collision=False,
        enable_recompute_normals=True, enable_recompute_tangents=True))
    assert surface_mesh, outcome
    assert unreal.EditorAssetLibrary.save_loaded_asset(surface_mesh)
sea.static_mesh_component.set_static_mesh(surface_mesh)
sea.set_actor_scale3d(unreal.Vector(1,1,1))
# Solid seabed keeps players within the ocean's finite vertical extent.
bed = next((a for a in all_actors if a.get_actor_label() == 'Coastal seabed'), None)
if not bed:
    bed = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0,0,-3025))
    bed.set_actor_label('Coastal seabed'); bed.set_folder_path('Coast/Ocean')
    bed.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    bed.set_actor_scale3d(unreal.Vector(600,600,.8))
    bed.static_mesh_component.set_material(0, unreal.load_asset('/Game/Elitewake/World/Blockout/M_CoastalSand'))
depth = runpy.run_path(str(root/'Scripts/Setup/set_coastal_ocean_depth.py'))['apply_depth'](volume, bed, sea.get_actor_location().z)
assert level.save_current_level()
report = {'success':True, 'map':'/Game/Elitewake/Maps/Lvl_CoastalPlayground',
    'water_surface_z':-65, 'water_volume':volume.get_path_name(), 'textured_actors':changes, 'depth':depth,
    'limits':['Prototype static swimming waterline; small animated visual waves; no vessel buoyancy',
              'Swimming animations, oxygen/drowning and underwater presentation remain open',
              'Terrain and vegetation geometry still blockout; generated textures are provisional']}
(root/'Saved/CoastalWaterUpgradeResult.json').write_text(json.dumps(report,indent=2))
unreal.log('Coastal water upgrade saved')
