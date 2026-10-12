"""Replace the coastal map's blockout ground with a sculpted terrain mesh. Safe to run again.

Run after refresh_coastal_visuals.py, in the editor (not headless: the ocean has to be rebuilt by a rendering
editor after the ground changes), outside Play with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

The island is generated from the shapes below, not painted: a sand island with a wet shoreline,
low dunes and two hills to the west, a hollow for the freshwater spring, the islet to the
north-east, and a sandy shelf that falls away to deep water. The beach spawn, dock landing and
sloop keep their places; the spawn is lifted onto the new ground and the dock posts reach the seabed.
The deep floor stays at the owner's 500 m beyond the terrain's edge. All heights are tuning.
"""
import json
import math
from pathlib import Path
import unreal

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
LABEL = 'Coastal island terrain'
MESH = '/Game/Elitewake/World/Meshes/SM_CoastalTerrain_v1'
SEA = -65.0                  # cm, the swimming volume's surface
QUADS = 252                  # 504 m square at 2 m spacing
SIZE = 50400.0
root = Path(unreal.Paths.project_dir()).resolve()


def radial_distance(x, y, cx, cy, rx, ry, wobble=0.0):
    """Signed distance in cm from an ellipse's edge (negative inside), with an optional wavy shoreline."""
    dx, dy = x - cx, y - cy
    angle = math.atan2(dy, dx)
    edge = 1.0 / math.sqrt((math.cos(angle) / rx) ** 2 + (math.sin(angle) / ry) ** 2)
    edge *= 1.0 + wobble * (0.6 * math.sin(3 * angle + 1.3) + 0.4 * math.sin(7 * angle + 0.4))
    return math.hypot(dx, dy) - edge


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
    d = radial_distance(x, y, -800, -100, 5100, 4100, wobble=0.03)
    if d > 0:
        main = seabed(d) + ripple
    else:
        inland = -d
        dunes = min(1.0, max(0.0, (inland - 1500) / 1500)) * (45 * math.sin(x / 650 + 1) * math.sin(y / 1100))
        main = land(inland) + dunes + bump(x, y, -3300, -1700, 1600, 700) + bump(x, y, -3500, 1300, 1200, 420)
        # Freshwater spring: a flat clearing with a shallow hollow under the pool.
        spring = math.hypot(x + 1700, y - 1500)
        if spring < 900:
            blend = min(1.0, max(0.0, (spring - 500) / 400))
            floor = -25 if spring < 230 else min(20.0, -25 + (spring - 230) * 0.6)
            main = floor * (1 - blend) + main * blend
    # North-east islet.
    di = radial_distance(x, y, 9500, 2600, 1800, 1450, wobble=0.05)
    islet = seabed(di) + ripple if di > 0 else land(-di) + bump(x, y, 9400, 2700, 900, 250)
    return max(main, islet)


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


lib = unreal.EWEditorVerificationLibrary
assert not lib.get_play_worlds(), 'Stop Play first'
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level(MAP)
placed = actors.get_all_level_actors()

# Old blockout ground and the previous terrain, if this ran before.
retired = ['Main beach', 'Distant islet beach', 'Island interior', 'Distant islet interior', 'Freshwater basin rim', LABEL]
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
    'swim_check_start': (6200, 0), 'swim_check_shore': (5500, 0), 'islet_top': (9400, 2700)}.items()}

# A rendering editor rebuilds the ocean against the new ground; headless runs skip this and leave it hidden.
ocean = next(a for a in actors.get_all_level_actors() if isinstance(a, unreal.WaterBodyOcean))
report['ocean'] = unreal.EWWorldEditorLibrary.rebuild_water_body(ocean)
assert level.save_current_level()
report['success'] = True
(root / 'Saved/CoastalTerrainResult.json').write_text(json.dumps(report, indent=2))
unreal.log('Coastal terrain saved')
