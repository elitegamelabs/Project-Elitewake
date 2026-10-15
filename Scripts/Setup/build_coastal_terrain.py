"""Replace the coastal map's blockout ground with a sculpted terrain mesh. Safe to run again.

Run after refresh_coastal_visuals.py, in the editor (not headless: the ocean has to be rebuilt by a rendering
editor after the ground changes), outside Play with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

The island is generated from the shapes below, not painted: a sand island with a wet shoreline,
low dunes and two hills to the west, a basin for the freshwater pond, the islet to the
north-east, a second, smaller island out to the south-west (owner, October 15), and a sandy shelf that falls away to deep water. Animated surf washes up both beaches. The beach spawn, dock landing and
sloop keep their places; the spawn is lifted onto the new ground and the dock posts reach the seabed.
The deep floor stays at the owner's 500 m beyond the terrain's edge. All heights are tuning.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coastal_layout import POND, POND_DEPTH, POND_RADIUS, POND_SURFACE  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
LABEL = 'Coastal island terrain'
MESH = '/Game/Elitewake/World/Meshes/SM_CoastalTerrain_v1'
SEA = -65.0                  # cm, the swimming volume's surface
QUADS = 252                  # 504 m square at 2 m spacing
SIZE = 50400.0
root = Path(unreal.Paths.project_dir()).resolve()


# Shorelines: centre, radii and how wavy the coast is.
MAIN_SHORE = (-800, -100, 5100, 4100, 0.03)
ISLET_SHORE = (9500, 2600, 1800, 1450, 0.05)
# The second island (owner, October 15): smaller, about 125 m out to the south-west across open water, with a
# rocky crown and a wooded saddle.
SECOND_SHORE = (-15000, -13000, 2800, 2200, 0.06)


def edge_radius(angle, rx, ry, wobble):
    edge = 1.0 / math.sqrt((math.cos(angle) / rx) ** 2 + (math.sin(angle) / ry) ** 2)
    return edge * (1.0 + wobble * (0.6 * math.sin(3 * angle + 1.3) + 0.4 * math.sin(7 * angle + 0.4)))


def radial_distance(x, y, cx, cy, rx, ry, wobble=0.0):
    """Signed distance in cm from an ellipse's edge (negative inside), with an optional wavy shoreline."""
    dx, dy = x - cx, y - cy
    return math.hypot(dx, dy) - edge_radius(math.atan2(dy, dx), rx, ry, wobble)


def seabed(d):
    """Depth below the waterline at d cm offshore: a sandy shelf, a drop-off, then the deep slope."""
    if d < 1500:
        return SEA - 0.3 * d
    if d < 4600:
        return SEA - 450 - 0.8 * (d - 1500)
    return max(-15000.0, SEA - 2930 - 0.25 * (d - 4600))


def land(inland):
    """Height at inland cm from the waterline: a 6 m beach, then a gentle rise."""
    if inland < 600:
        return SEA + inland / 600 * 80
    return 15 + min(inland - 600, 2500) * 0.02


def bump(x, y, cx, cy, radius, height):
    return height * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / radius ** 2)


def height(x, y):
    ripple = 30 * math.sin(x / 700 + 0.5) * math.sin(y / 900 + 1.1) + 15 * math.sin((x + y) / 330)
    # Main island.
    d = radial_distance(x, y, *MAIN_SHORE[:4], wobble=MAIN_SHORE[4])
    if d > 0:
        main = seabed(d) + ripple
    else:
        inland = -d
        dunes = min(1.0, max(0.0, (inland - 1500) / 1500)) * (45 * math.sin(x / 650 + 1) * math.sin(y / 1100))
        main = land(inland) + dunes + bump(x, y, -3300, -1700, 1600, 700) + bump(x, y, -3500, 1300, 1200, 420)
        # Freshwater pond: a round basin, deepest in the middle, with a low bank and a clearing around it.
        spring = math.hypot(x - POND[0], y - POND[1])
        if spring < POND_RADIUS + 300:
            blend = min(1.0, max(0.0, (spring - POND_RADIUS - 50) / 250))
            if spring < POND_RADIUS:
                floor = POND_SURFACE - 10 - POND_DEPTH * (1 - (spring / POND_RADIUS) ** 2)
            else:
                floor = min(20.0, POND_SURFACE - 10 + (spring - POND_RADIUS) * 0.3)
            main = floor * (1 - blend) + main * blend
    # North-east islet.
    di = radial_distance(x, y, *ISLET_SHORE[:4], wobble=ISLET_SHORE[4])
    islet = seabed(di) + ripple if di > 0 else land(-di) + bump(x, y, 9400, 2700, 900, 250)
    ds = radial_distance(x, y, *SECOND_SHORE[:4], wobble=SECOND_SHORE[4])
    second = seabed(ds) + ripple if ds > 0 else (land(-ds) + bump(x, y, -15800, -13600, 1100, 520)
                                                 + bump(x, y, -14000, -12300, 900, 220))
    return max(main, islet, second)


def make_material():
    path = '/Game/Elitewake/World/Materials/M_CoastalTerrain_v1'
    assets = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    material = unreal.load_asset(path) or assets.create_asset('M_CoastalTerrain_v1', '/Game/Elitewake/World/Materials',
                                                              unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(material)
    sand = unreal.load_asset('/Game/Elitewake/World/Materials/T_Sand_v1')
    # Ground textures need mipmaps; the icon setting it was imported with has none and shimmers at distance.
    sand.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    sand.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    assert unreal.EditorAssetLibrary.save_loaded_asset(sand)

    def node(cls, **props):
        n = mel.create_material_expression(material, cls)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def link(a, b, pin='', out=''):
        assert mel.connect_material_expressions(a, out, b, pin), (b.get_name(), pin)

    def const(v):
        return node(unreal.MaterialExpressionConstant, r=v)

    # The terrain mesh's UVs span its 504 m once; repeat the sand every 4 m.
    uv = node(unreal.MaterialExpressionTextureCoordinate, u_tiling=SIZE / 400.0, v_tiling=SIZE / 400.0)
    sample = node(unreal.MaterialExpressionTextureSample, texture=sand)
    link(uv, sample, 'UVs')
    position = node(unreal.MaterialExpressionWorldPosition)
    dry = sample  # its first output is RGB
    # Wet sand from just above the waterline down.
    z = node(unreal.MaterialExpressionDotProduct)  # world height as a single value
    link(position, z, 'A')
    link(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(0, 0, 1, 0)), z, 'B')
    below = node(unreal.MaterialExpressionSubtract)
    link(const(-25.0), below, 'A'); link(z, below, 'B')
    wet_ramp = node(unreal.MaterialExpressionDivide)
    link(below, wet_ramp, 'A'); link(const(60.0), wet_ramp, 'B')
    wet = node(unreal.MaterialExpressionSaturate)
    link(wet_ramp, wet)
    damp = node(unreal.MaterialExpressionMultiply)
    link(dry, damp, 'A'); link(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(0.6, 0.57, 0.52, 1)), damp, 'B')
    colour = node(unreal.MaterialExpressionLinearInterpolate)
    link(dry, colour, 'A'); link(damp, colour, 'B'); link(wet, colour, 'Alpha')
    rough = node(unreal.MaterialExpressionLinearInterpolate)
    link(const(0.92), rough, 'A'); link(const(0.55), rough, 'B'); link(wet, rough, 'Alpha')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


# Shared by the surf material's two outputs. P is world position in cm, Foam a foam texture sample.
SWASH_HLSL = '''
float t = Time / 8.0 + 0.25 * sin(P.x / 450.0 + 0.3) + 0.25 * sin(P.y / 610.0 + 1.7) + 0.15 * sin((P.x + P.y) / 230.0);
float ph = frac(t);
float drain = ph < 0.5 ? 1.0 : (1.0 - ph) * 2.0;
float v = saturate((P.z + 70.0) / 40.0);
float reach = 0.08 + 0.62 * pow(sin(ph * 3.14159), 0.7);
float behind = 1.0 - smoothstep(reach - 0.1, reach, v);
float bubbles = smoothstep(0.25, 0.75, Foam);
float band = exp(-pow((v - reach) / 0.05, 2.0)) * (0.35 + 0.65 * bubbles);
float lace = behind * bubbles * 0.35 * drain;
float fringe = exp(-pow((v - 0.05) / 0.05, 2.0)) * bubbles * 0.7;
float white = saturate(band + lace + fringe);
float sheet = behind * 0.75 * drain;
'''


def make_swash_material():
    """Surf washing up the beach: a broken foam front climbs up to about 1.6 m of sand on an 8 s cycle (tuning),
    leaving a glossy sheet of water laced with foam that drains back, over a foam fringe at the waterline.
    Each stretch of coast runs out of step with its neighbours."""
    path = '/Game/Elitewake/World/Materials/M_ShoreSwash_v1'
    assets = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    material = unreal.load_asset(path) or assets.create_asset('M_ShoreSwash_v1', '/Game/Elitewake/World/Materials',
                                                              unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(material)
    # Masked with dithered coverage, so the surf is lit exactly like the sand under it.
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)

    def node(cls, **props):
        n = mel.create_material_expression(material, cls)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def custom(code, kind, inputs):
        n = node(unreal.MaterialExpressionCustom, code=code, output_type=kind)
        pins = []
        for name in inputs:
            pin = unreal.CustomInput()
            pin.set_editor_property('input_name', name)
            pins.append(pin)
        n.set_editor_property('inputs', pins)
        return n

    position = node(unreal.MaterialExpressionWorldPosition)
    clock = node(unreal.MaterialExpressionTime)
    # Foam texture drifting slowly so the surf never looks stamped.
    uv = custom('return P.xy / 200.0 + float2(T * 0.02, T * 0.013);', unreal.CustomMaterialOutputType.CMOT_FLOAT2, ('P', 'T'))
    assert mel.connect_material_expressions(position, '', uv, 'P') and mel.connect_material_expressions(clock, '', uv, 'T')
    foam = node(unreal.MaterialExpressionTextureSample,
                texture=unreal.load_asset('/Water/Textures/Foam/T_WaterFlow_01_Foam_Tiled'))
    assert mel.connect_material_expressions(uv, '', foam, 'UVs')
    outputs = {
        unreal.MaterialProperty.MP_BASE_COLOR: (unreal.CustomMaterialOutputType.CMOT_FLOAT3,
            'return lerp(float3(0.16, 0.34, 0.34), float3(0.92, 0.94, 0.94), white);'),
        unreal.MaterialProperty.MP_ROUGHNESS: (unreal.CustomMaterialOutputType.CMOT_FLOAT1,
            'return lerp(0.05, 0.6, white);'),
        # Coverage dithered per pixel and frame (interleaved gradient noise); temporal AA blends it smooth.
        unreal.MaterialProperty.MP_OPACITY_MASK: (unreal.CustomMaterialOutputType.CMOT_FLOAT1,
            'float a = saturate(sheet + white) * saturate(v * 10.0);'
            ' float n = frac(52.9829189 * frac(dot(Parameters.SvPosition.xy + View.StateFrameIndexMod8 * 5.588238,'
            ' float2(0.06711056, 0.00583715))));'
            ' return a - n + 0.3333;'),
    }
    for prop, (kind, tail) in outputs.items():
        n = custom(SWASH_HLSL + tail, kind, ('P', 'Time', 'Foam'))
        for pin, src, out in (('P', position, ''), ('Time', clock, ''), ('Foam', foam, 'R')):
            assert mel.connect_material_expressions(src, out, n, pin), (prop, pin)
        assert mel.connect_material_property(n, '', prop)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def build_swash(label, shore, material):
    """A strip lying 3 cm over the sand from 1.2 m offshore to 4.8 m up the beach, all the way round a shore."""
    cx, cy, rx, ry, wobble = shore
    asset = '/Game/Elitewake/World/Meshes/SM_' + label.title().replace(' ', '') + '_v1'
    mesh = unreal.DynamicMesh()
    unreal.GeometryScript_Primitives.append_rectangle_xy(mesh, unreal.GeometryScriptPrimitiveOptions(), unreal.Transform(),
                                                         1000.0, 1000.0, 720, 8)
    flat = unreal.GeometryScript_List.convert_vector_list_to_array(
        unreal.GeometryScript_MeshQueries.get_all_vertex_positions(mesh, False)[1])
    points = []
    for p in flat:
        angle = (p.x / 1000.0 + 0.5) * 2 * math.pi
        r = edge_radius(angle, rx, ry, wobble) + 120 - (p.y / 1000.0 + 0.5) * 600
        x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
        points.append(unreal.Vector(x, y, height(x, y) + 3))
    unreal.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(
        mesh, unreal.GeometryScript_List.convert_array_to_vector_list(points))
    unreal.GeometryScript_Normals.recompute_normals(mesh, unreal.GeometryScriptCalculateNormalsOptions())
    if unreal.EditorAssetLibrary.does_asset_exist(asset):
        assert unreal.EditorAssetLibrary.delete_asset(asset)
    strip, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        mesh, asset, unreal.GeometryScriptCreateNewStaticMeshAssetOptions(enable_collision=False))
    assert strip, outcome
    strip.set_material(0, material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(strip)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
    actor.set_actor_label(label)
    actor.set_folder_path('Coast/Terrain')
    component = actor.static_mesh_component
    component.set_static_mesh(strip)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_cast_shadow(False)
    return actor


lib = unreal.EWEditorVerificationLibrary
assert not lib.get_play_worlds(), 'Stop Play first'
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level(MAP)
placed = actors.get_all_level_actors()

# Old blockout ground and the previous terrain, if this ran before.
SURF = ['Main island surf', 'Islet surf', 'Second island surf']
retired = ['Main beach', 'Distant islet beach', 'Island interior', 'Distant islet interior', 'Freshwater basin rim', LABEL] + SURF
removed = []
for actor in placed:
    if actor.get_actor_label() in retired:
        removed.append(actor.get_actor_label())
        actors.destroy_actor(actor)

material = make_material()
mesh = unreal.DynamicMesh()
geo = unreal.GeometryScript_Primitives
geo.append_rectangle_xy(mesh, unreal.GeometryScriptPrimitiveOptions(), unreal.Transform(), SIZE, SIZE, QUADS, QUADS)
positions = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(mesh, False)[1]
flat = unreal.GeometryScript_List.convert_vector_list_to_array(positions)
moved = unreal.GeometryScript_List.convert_array_to_vector_list([unreal.Vector(p.x, p.y, height(p.x, p.y)) for p in flat])
unreal.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(mesh, moved)
unreal.GeometryScript_Normals.recompute_normals(mesh, unreal.GeometryScriptCalculateNormalsOptions())
if unreal.EditorAssetLibrary.does_asset_exist(MESH):
    assert unreal.EditorAssetLibrary.delete_asset(MESH)
terrain_mesh, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
    mesh, MESH, unreal.GeometryScriptCreateNewStaticMeshAssetOptions(enable_collision=True,
    enable_recompute_normals=False, enable_recompute_tangents=True))
assert terrain_mesh, outcome
body = terrain_mesh.get_editor_property('body_setup')
body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
terrain_mesh.set_material(0, material)
assert unreal.EditorAssetLibrary.save_loaded_asset(terrain_mesh)
terrain = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
terrain.set_actor_label(LABEL)
terrain.set_folder_path('Coast/Terrain')
terrain.static_mesh_component.set_static_mesh(terrain_mesh)
surf_material = make_swash_material()
for label, shore in zip(SURF, (MAIN_SHORE, ISLET_SHORE, SECOND_SHORE)):
    build_swash(label, shore, surf_material)

# Keep the fixed places on the new ground.
report = {'removed': removed}
start = next(a for a in actors.get_all_level_actors() if isinstance(a, unreal.PlayerStart))
spawn_ground = height(start.get_actor_location().x, start.get_actor_location().y)
start.set_actor_location(unreal.Vector(start.get_actor_location().x, start.get_actor_location().y, spawn_ground + 100), False, False)
report['spawn_ground_cm'] = round(spawn_ground, 1)
deck_bottom = 7.0
for post in [a for a in actors.get_all_level_actors() if a.get_actor_label() == 'Dock support']:
    p = post.get_actor_location()
    bottom = height(p.x, p.y) - 40
    post.set_actor_location(unreal.Vector(p.x, p.y, (deck_bottom + bottom) / 2), False, False)
    s = post.get_actor_scale3d()
    post.set_actor_scale3d(unreal.Vector(s.x, s.y, (deck_bottom - bottom) / 100))
report['ground_cm'] = {name: round(height(x, y), 1) for name, (x, y) in {
    'dock_landing': (4000, 900), 'dock_end': (6090, 900), 'sloop': (6200, 1400), 'spring': (-1700, 1500),
    'swim_check_start': (6200, 0), 'swim_check_shore': (5500, 0), 'islet_top': (9400, 2700), 'second_island_top': (-15800, -13600)}.items()}

# The ocean learns the ground's shape (shallows, shoreline foam, waves easing onto the beach), then a rendering
# editor rebuilds it against the new ground; headless runs leave it hidden.
assert unreal.EWWorldEditorLibrary.add_water_terrain(terrain)
ocean = next(a for a in actors.get_all_level_actors() if isinstance(a, unreal.WaterBodyOcean))
# Epic's ocean flattens waves in water under 1 m deep; let them run in to 25 cm and foam harder (tuning).
SEA_MATERIAL = '/Game/Elitewake/World/Water/MI_CoastalOcean_v1'
sea = unreal.load_asset(SEA_MATERIAL) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    'MI_CoastalOcean_v1', '/Game/Elitewake/World/Water', unreal.MaterialInstanceConstant,
    unreal.MaterialInstanceConstantFactoryNew())
mel = unreal.MaterialEditingLibrary
mel.set_material_instance_parent(sea, unreal.load_asset('/Water/Materials/WaterSurface/Water_Material_Ocean'))
mel.update_material_instance(sea)
for name, value in {'Water Depth to Mask Waves': 25.0, 'Foam Boost': 2.0, 'Foam Distance': 512.0}.items():
    mel.set_material_instance_scalar_parameter_value(sea, name, value)
    assert abs(mel.get_material_instance_scalar_parameter_value(sea, name) - value) < 0.01, name
mel.update_material_instance(sea)
assert unreal.EditorAssetLibrary.save_loaded_asset(sea)
ocean.get_water_body_component().set_water_material(sea)
report['ocean'] = unreal.EWWorldEditorLibrary.rebuild_water_body(ocean)
assert level.save_current_level()
report['success'] = True
(root / 'Saved/CoastalTerrainResult.json').write_text(json.dumps(report, indent=2))
unreal.log('Coastal terrain saved')
