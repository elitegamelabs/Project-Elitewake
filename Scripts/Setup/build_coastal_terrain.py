"""Build the world's ground: a terrain for every island of the five-region world and the sea floor between them.
Safe to run again. Run in the editor (not headless: the ocean has to be rebuilt by a rendering editor after the
ground changes), outside Play with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner direction, October 15: Plains in the centre (the starter island and five more round it), Winter to the north,
Swamp to the south, Desert to the east, Jungle to the west, at least five islands each, 800-2,000 m of sea between
shores. The islands come from world_layout.py and their ground from world_terrain.py (plain Python, shared with the
scripts that dress the islands). Each island gets its own mesh (2 m grid on the starter island, 4 m elsewhere) out to
200 m past its shore, where it dips under one sea-floor mesh covering the whole world; the old -500 m floor stays
underneath as a backstop. The ground carries what covers it in its vertex colour (red snow, green grass, blue mud)
and the terrain material paints sand, grass, mud or snow from it. Animated surf washes up every shore. The ocean,
its water zone and the swimming volume are widened to the whole world. The starter island keeps its exact shape:
the beach spawn, dock landing, pond and sloop keep their places. All heights are tuning.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
MESHES = '/Game/Elitewake/World/Meshes/Islands'
SEA = T.SEA
root = Path(unreal.Paths.project_dir()).resolve()
height = T.height


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
    # The sand repeats every 4 m, in world space (each island's mesh has its own UVs).
    position = node(unreal.MaterialExpressionWorldPosition)
    uv = node(unreal.MaterialExpressionCustom, code='return P.xy / 400.0;', output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    pin = unreal.CustomInput(); pin.set_editor_property('input_name', 'P'); uv.set_editor_property('inputs', [pin])
    link(position, uv, 'P')
    sample = node(unreal.MaterialExpressionTextureSample, texture=sand)
    link(uv, sample, 'UVs')
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
    # Snow where the ground's vertex colour says so (red = snow cover), above the tideline; fine sparkle in it.
    def custom(code, kind, inputs):
        n = node(unreal.MaterialExpressionCustom, code=code, output_type=kind)
        pins = []
        for name in inputs:
            pin = unreal.CustomInput()
            pin.set_editor_property('input_name', name)
            pins.append(pin)
        n.set_editor_property('inputs', pins)
        return n
    paint = node(unreal.MaterialExpressionVertexColor)
    normal = node(unreal.MaterialExpressionVertexNormalWS)
    # Above the tideline the vertex colour lays grass (green), mud (blue) or snow (red) over the sand. Grass keeps
    # off steep faces, which show bare earth; all of it is broken up by noise at two scales so it never reads flat.
    noise = ('float h(float2 c) { return frac(sin(dot(c, float2(12.9898, 78.233))) * 43758.5453); }'
             ' float n2(float2 q) { float2 i = floor(q), f = frac(q); f = f * f * (3 - 2 * f);'
             ' return lerp(lerp(h(i), h(i + float2(1, 0)), f.x), lerp(h(i + float2(0, 1)), h(i + float2(1, 1)), f.x), f.y); }')
    snowy = custom('struct G { ' + noise + ' }; G g;'
                   ' float up = saturate((P.z + 45.0) / 60.0);'
                   ' float big = g.n2(P.xy / 900.0), mid = g.n2(P.xy / 140.0), fine = g.n2(P.xy / 6.0);'
                   ' float flat = saturate((N.z - .72) * 5.0);'
                   ' float3 grass = lerp(float3(.035, .075, .015), float3(.1, .13, .03), big) * lerp(.7, 1.2, mid) * lerp(.88, 1.08, fine);'
                   ' float3 earth = float3(.16, .12, .08) * lerp(.8, 1.1, mid);'
                   ' float3 c = lerp(C, lerp(earth, grass, flat), V.g * up * saturate(mid * 2.5 + .45));'
                   ' float3 mud = lerp(float3(.035, .03, .02), float3(.05, .06, .025), mid) * lerp(.8, 1.2, big);'
                   ' c = lerp(c, mud, V.b * saturate(up + .3));'
                   ' float3 snow = float3(.8, .84, .9) * lerp(.9, 1.05, fine) * lerp(.94, 1.02, big);'
                   ' return lerp(c, snow, V.r * up);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C', 'V', 'P', 'N'))
    snow_rough = custom('float up = saturate((P.z + 45.0) / 60.0);'
                        ' return lerp(lerp(lerp(R, .95, V.g * up), .45, V.b), .62, V.r * up);',
                        unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('R', 'V', 'P'))
    link(colour, snowy, 'C'); link(paint, snowy, 'V'); link(position, snowy, 'P'); link(normal, snowy, 'N')
    link(rough, snow_rough, 'R'); link(paint, snow_rough, 'V'); link(position, snow_rough, 'P')
    assert mel.connect_material_property(snowy, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(snow_rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
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


def build_swash(island, material):
    """A strip lying 3 cm over the sand from 1.2 m offshore to 4.8 m up the beach, all the way round a shore."""
    label = f'{island.key} surf'
    asset = f'{MESHES}/SM_Surf_{island.key}_v1'
    segments = max(240, int(2 * math.pi * island.reach() / 150))
    mesh = unreal.DynamicMesh()
    unreal.GeometryScript_Primitives.append_rectangle_xy(mesh, unreal.GeometryScriptPrimitiveOptions(), unreal.Transform(),
                                                         1000.0, 1000.0, segments, 8)
    flat = unreal.GeometryScript_List.convert_vector_list_to_array(
        unreal.GeometryScript_MeshQueries.get_all_vertex_positions(mesh, False)[1])
    points = []
    for p in flat:
        angle = (p.x / 1000.0 + 0.5) * 2 * math.pi
        r = island.radius(angle) + 120 - (p.y / 1000.0 + 0.5) * 600
        x, y = island.cx + r * math.cos(angle), island.cy + r * math.sin(angle)
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
    actor.set_folder_path('World/Surf')
    component = actor.static_mesh_component
    component.set_static_mesh(strip)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_cast_shadow(False)
    return actor


def sea_floor_height(x, y):
    """The sea floor mesh's height: the sea floor everywhere, but held 15 m under the sea wherever an island's land
    is, so its coarse 200 m grid never pokes up through the land (or into a cave) of the bigger islands; each
    island's own mesh carries the ground there."""
    h = height(x, y)
    if any(i.distance(x, y) < 0 for i in W.ISLANDS if abs(x - i.cx) < i.reach() + 1 and abs(y - i.cy) < i.reach() + 1):
        h = min(h, SEA - 1500.0)
    return h


def ground_mesh(path, x0, x1, y0, y1, spacing, material, colour=True, height=height):
    """A height-field mesh over a rectangle (world cm) from world_terrain, written to `path`."""
    nx, ny = max(2, int(round((x1 - x0) / spacing))), max(2, int(round((y1 - y0) / spacing)))
    mesh = unreal.DynamicMesh()
    unreal.GeometryScript_Primitives.append_rectangle_xy(mesh, unreal.GeometryScriptPrimitiveOptions(), unreal.Transform(
        location=unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, 0)), x1 - x0, y1 - y0, nx, ny)
    flat = unreal.GeometryScript_List.convert_vector_list_to_array(
        unreal.GeometryScript_MeshQueries.get_all_vertex_positions(mesh, False)[1])
    heights = [height(p.x, p.y) for p in flat]
    unreal.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(mesh, unreal.GeometryScript_List.convert_array_to_vector_list(
        [unreal.Vector(p.x, p.y, z) for p, z in zip(flat, heights)]))
    if colour:
        unreal.GeometryScript_VertexColors.set_mesh_per_vertex_colors(mesh, unreal.GeometryScript_List.convert_array_to_color_list(
            [unreal.LinearColor(*T.cover(p.x, p.y, z), 1) for p, z in zip(flat, heights)]))
    unreal.GeometryScript_Normals.recompute_normals(mesh, unreal.GeometryScriptCalculateNormalsOptions())
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        assert unreal.EditorAssetLibrary.delete_asset(path)
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        mesh, path, unreal.GeometryScriptCreateNewStaticMeshAssetOptions(enable_collision=True,
        enable_recompute_normals=False, enable_recompute_tangents=True))
    assert asset, outcome
    asset.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    asset.set_material(0, material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset, (nx + 1) * (ny + 1)


lib = unreal.EWEditorVerificationLibrary
assert not lib.get_play_worlds(), 'Stop Play first'
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level(MAP)

# The single 504 m terrain and its surf, and any earlier run of this script.
retired_labels = ['Main beach', 'Distant islet beach', 'Island interior', 'Distant islet interior', 'Freshwater basin rim',
                  'Coastal island terrain', 'Main island surf', 'Islet surf', 'Second island surf', 'Winter island surf', 'Sea floor']
removed = []
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() in retired_labels or str(actor.get_folder_path()) in ('World/Islands', 'World/Surf'):
        removed.append(actor.get_actor_label())
        actors.destroy_actor(actor)

material = make_material()
surf_material = make_swash_material()
report = {'removed': len(removed), 'islands': {}}
terrains = []
for island in W.ISLANDS:
    reach = island.reach() + T.SHELF
    spacing = 200.0 if island.key == 'Starter' else 400.0
    asset, verts = ground_mesh(f'{MESHES}/SM_Island_{island.key}_v1', island.cx - reach, island.cx + reach,
                               island.cy - reach, island.cy + reach, spacing, material)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
    actor.set_actor_label(f'{island.key} ({island.region})')
    actor.set_folder_path('World/Islands')
    actor.static_mesh_component.set_static_mesh(asset)
    terrains.append(actor)
    build_swash(island, surf_material)
    report['islands'][island.key] = {'region': island.region, 'centre_m': [round(island.cx / 100), round(island.cy / 100)], 'vertices': verts}

# The sea floor between the islands, over the whole world and a margin.
x0, x1, y0, y1 = W.bounds(3000 * 100)
floor_asset, floor_verts = ground_mesh(f'{MESHES}/SM_SeaFloor_v1', x0, x1, y0, y1, 20000.0, material, colour=False,
                                      height=sea_floor_height)
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
floor.set_actor_label('Sea floor')
floor.set_folder_path('World/Islands')
floor.static_mesh_component.set_static_mesh(floor_asset)
floor.static_mesh_component.set_cast_shadow(False)
terrains.append(floor)
report['sea_floor'] = {'vertices': floor_verts, 'size_km': [round((x1 - x0) / 100000, 1), round((y1 - y0) / 100000, 1)]}

# Keep the fixed places on the ground (the starter island did not change).
start = next(a for a in actors.get_all_level_actors() if isinstance(a, unreal.PlayerStart))
spawn_ground = height(start.get_actor_location().x, start.get_actor_location().y)
start.set_actor_location(unreal.Vector(start.get_actor_location().x, start.get_actor_location().y, spawn_ground + 100), False, False)
report['spawn_ground_cm'] = round(spawn_ground, 1)
deck_bottom = 7.0
for post in [a for a in actors.get_all_level_actors() if a.get_actor_label() == 'Dock support']:
    p = post.get_actor_location()
    bottom = height(p.x, p.y) - 40
    post.set_actor_location(unreal.Vector(p.x, p.y, (deck_bottom + bottom) / 2), False, False)
    s3 = post.get_actor_scale3d()
    post.set_actor_scale3d(unreal.Vector(s3.x, s3.y, (deck_bottom - bottom) / 100))

# The sea over the whole world: the ocean and its water zone, the swimming volume, and the old floor as a backstop.
half = max(x1 - x0, y1 - y0) / 2 + 200000
all_actors = actors.get_all_level_actors()
zone = next(a for a in all_actors if isinstance(a, unreal.WaterZone))
zone.set_editor_property('zone_extent', unreal.Vector2D(half * 2, half * 2))
zone.set_editor_property('render_target_resolution', unreal.IntPoint(4096, 4096))
for terrain in terrains:
    assert unreal.EWWorldEditorLibrary.add_water_terrain(terrain)
ocean = next(a for a in all_actors if isinstance(a, unreal.WaterBodyOcean))
oc = ocean.get_water_body_component()
oc.set_editor_property('ocean_extents', unreal.Vector2D(half * 2, half * 2))
oc.set_editor_property('collision_extents', unreal.Vector(half, half, 10000))
SEA_MATERIAL = '/Game/Elitewake/World/Water/MI_CoastalOcean_v1'
sea = unreal.load_asset(SEA_MATERIAL)
if sea:
    oc.set_water_material(sea)
for label in ('Coastal ocean swimming volume', 'Coastal seabed'):
    thing = next(a for a in all_actors if a.get_actor_label() == label)
    centre, extent = thing.get_actor_bounds(False)
    sc = thing.get_actor_scale3d()
    thing.set_actor_scale3d(unreal.Vector(sc.x * half / extent.x, sc.y * half / extent.y, sc.z))
    thing.set_actor_location(unreal.Vector(0, 0, thing.get_actor_location().z), False, False)
report['sea_half_extent_km'] = round(half / 100000, 1)
report['ocean'] = unreal.EWWorldEditorLibrary.rebuild_water_body(ocean)
report['ground_cm'] = {name: round(height(x, y), 1) for name, (x, y) in {
    'dock_landing': (4000, 900), 'dock_end': (6090, 900), 'sloop': (6200, 1400), 'spring': (-1700, 1500),
    'swim_check_start': (6200, 0), 'swim_check_shore': (5500, 0)}.items()}
assert level.save_current_level()
report['success'] = True
(root / 'Saved/CoastalTerrainResult.json').write_text(json.dumps(report, indent=2))
unreal.log('World terrain saved')
