"""Visual pass on the coastal test map. Safe to run again; run outside Play with no unsaved maps.

- Removes the primitive-shape blockout props: palms and fronds, sphere rocks, stone nodes, loose wood and
  stone, berry and fiber blobs. Their gameplay classes stay; real meshes replace them in the coast art pass.
- Replaces the flat sea plane with an Unreal Water ocean. The saved swimming volume still drives swimming,
  and ships sail a flat waterline, so the swell is kept gentle (under a metre) and runs with the wind.
- Adds volumetric clouds.
- Places a starter kit: survivors in this test map begin with tools and light materials, and the sloop's
  hold starts with a helm and two sails to fit. Normal starts are unchanged and still begin empty.
- Imports the survival HUD art (the matte v2 set) from Art/UI/Survival/2026-10-11/Matte-v2.
- Turns off the on-screen movement debug text on the survivor Blueprint.

Run in the editor, not headless: water bodies created without a renderer save broken helper meshes.
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
Then run build_coastal_terrain.py.
"""
import json
from pathlib import Path
import unreal

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
SEA_Z = -65.0
root = Path(unreal.Paths.project_dir()).resolve()
assets = unreal.AssetToolsHelpers.get_asset_tools()
report = {}

# HUD art.
hud = []
for key in ['Health', 'Stamina', 'Hunger', 'Hydration', 'Weight']:
    path = f'/Game/Elitewake/UI/HUD/T_{key}_Matte_v2'
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        source = root / f'Art/UI/Survival/2026-10-11/Matte-v2/{key}-Matte-Full-v2.png'
        assert source.is_file(), source
        task = unreal.AssetImportTask()
        for name, value in {'filename': str(source), 'destination_path': '/Game/Elitewake/UI/HUD',
                            'destination_name': f'T_{key}_Matte_v2', 'automated': True,
                            'replace_existing': False, 'save': True}.items():
            task.set_editor_property(name, value)
        assets.import_asset_tasks([task])
    texture = unreal.load_asset(path)
    assert isinstance(texture, unreal.Texture2D), path
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
    hud.append(path)
report['hud_textures'] = hud

# Survivor Blueprint: no movement debug text.
survivor = unreal.load_class(None, '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C')
survivor_cdo = unreal.get_default_object(survivor)
survivor_cdo.set_editor_property('show_movement_debug', False)
assert unreal.EditorAssetLibrary.save_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', only_if_is_dirty=False)

# Map.
lib = unreal.EWEditorVerificationLibrary
assert not lib.get_play_worlds(), 'Stop Play first'
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
placed = actors.get_all_level_actors()

def doomed(actor):
    folder, label = str(actor.get_folder_path()), actor.get_actor_label()
    return (folder in ('Coast/Resources', 'Coast/Vegetation') or label.startswith('Coast rock ')
            or label.startswith('Coastal sea surface'))

removed = sorted(a.get_actor_label() for a in placed if doomed(a))
for actor in [a for a in placed if doomed(a)]:
    actors.destroy_actor(actor)
report['removed'] = removed

# Ocean, created fresh each run. The spline marks land the ocean leaves dry, so a small loop under the main
# island keeps water everywhere else; the island and dock rise through it.
for old in [a for a in actors.get_all_level_actors() if isinstance(a, (unreal.WaterBodyOcean, unreal.WaterZone))]:
    actors.destroy_actor(old)
ocean = actors.spawn_actor_from_class(unreal.WaterBodyOcean, unreal.Vector(0, 0, SEA_Z))
ocean.set_actor_label('Ocean')
ocean.set_folder_path('Coast/Ocean')
spline = ocean.get_water_body_component().get_water_spline()
for i, (x, y) in enumerate([(-1200, -600), (-1200, 600), (-2200, 600), (-2200, -600)]):
    spline.set_location_at_spline_point(i, unreal.Vector(x, y, SEA_Z), unreal.SplineCoordinateSpace.WORLD, True)
zone = next(a for a in actors.get_all_level_actors() if isinstance(a, unreal.WaterZone))
zone.set_actor_label('Ocean water zone')
zone.set_folder_path('Coast/Ocean')
# Keep the landscape out of the zone's water-info capture: with it included the ocean is hidden across the
# whole landscape. Single Layer Water still shades shallows from the real scene depth.
zone.set_editor_property('auto_include_landscapes_as_terrain', False)
mesh = zone.get_component_by_class(unreal.WaterMeshComponent)
mesh.set_editor_property('far_distance_material', unreal.load_asset('/Water/Materials/WaterSurface/Water_FarMesh'))
mesh.set_editor_property('far_distance_mesh_extent', 4000000.0)
# Gentle swell travelling with the game wind (EWWindSubsystem blows toward yaw 45). Tuning.
SWELL = '/Game/Elitewake/World/Water/WA_CoastalSwell_v1'
swell = unreal.load_asset(SWELL) or unreal.EditorAssetLibrary.duplicate_asset('/Water/Waves/GerstnerWaves_Ocean', SWELL)
world_lib = unreal.EWWorldEditorLibrary
crest = world_lib.configure_gerstner_swell(swell, 12, 400.0, 3000.0, 2.0, 14.0, 45.0, 600.0)
assert 0 < crest < 100, crest
assert unreal.EditorAssetLibrary.save_loaded_asset(swell, only_if_is_dirty=False)
assert world_lib.set_water_body_waves(ocean, swell)
component = ocean.get_water_body_component()
# No landscape here yet: an ocean that carves landscape is not drawn without one.
component.set_editor_property('affects_landscape', False)
report['ocean'] = {'zone_extent': str(zone.get_editor_property('zone_extent')),
                   'max_wave_height_cm': component.get_max_wave_height(),
                   'collision': [(c.get_name(), str(c.get_collision_profile_name())) for c in component.get_collision_components()]}

# Sky.
if not any(isinstance(a, unreal.VolumetricCloud) for a in actors.get_all_level_actors()):
    actors.spawn_actor_from_class(unreal.VolumetricCloud, unreal.Vector(0, 0, 0)).set_actor_label('Volumetric clouds')

# Starter kit for this test map.
kit = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWStarterKit)), None)
if not kit:
    kit = actors.spawn_actor_from_class(unreal.EWStarterKit, unreal.Vector(150, 0, 200))
    kit.set_actor_label('Test starter kit')
carried = [('WoodenAxe', 1), ('WoodenPickaxe', 1), ('WoodenShovel', 1), ('HideWaterFlask', 1), ('InnTorch', 1),
           ('Wood', 20), ('Stone', 10), ('Fiber', 10), ('AzulBerry', 10)]
hold = [('ShipHelm', 1), ('SailMedium', 1), ('SailSmall', 1)]

def kit_entries(contents):
    entries = []
    for name, quantity in contents:
        entry = unreal.EWStarterKitItem()
        entry.set_editor_property('item', unreal.load_asset(f'/Game/Elitewake/Items/Testing/DA_Test{name}'))
        entry.set_editor_property('quantity', quantity)
        assert entry.get_editor_property('item'), name
        entries.append(entry)
    return entries

kit.set_editor_property('items', kit_entries(carried))
kit.set_editor_property('ship_cargo', kit_entries(hold))
report['starter_kit'] = {'carried': [f'{q} x {n}' for n, q in carried], 'ship_hold': [f'{q} x {n}' for n, q in hold]}

assert level.save_current_level()
report['success'] = True
(root / 'Saved/CoastalVisualsResult.json').write_text(json.dumps(report, indent=2))
unreal.log('Coastal visual pass saved')
