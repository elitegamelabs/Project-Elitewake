"""Build the title screen's map, art and the bodies offered in the character creator. Safe to run again.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

- The owner's title art (Art/UI/Title/Elitewake-Title-v1.png) as a UI texture.
- DA_BodyRoster: the survivor bodies on offer, for now the two Unreal mannequins, a man and a woman, with six
  colourings from fair to deep, worn through the survivor body material. Bodies made later (MetaHumans or
  the owner's own characters) are added here without code.
- Lvl_Title: the front of the game, run by AEWTitleGameMode. Behind the title art, the character creator stands the
  survivor on the end of a weathered dock over a calm sea at sunset, lit warm from the front and backlit by the low
  sun, as in the title art. The camera (tag CreatorCamera) frames the survivor on the right, clear of the panel.
All sizes and lights are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, material_builder, make_timber_material, write_static_mesh  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

ROOT = Path(unreal.Paths.project_dir()).resolve()
ART = ROOT / 'Art/UI/Title/Elitewake-Title-v1.png'
UI = '/Game/Elitewake/UI/Title'
CHARACTERS = '/Game/Elitewake/Characters'
MAP = '/Game/Elitewake/Maps/Lvl_Title'
WORLD = '/Game/Elitewake/World/Title'
MANNEQUINS = '/Game/Characters/Mannequins/Meshes'
BODIES = [('Man', f'{MANNEQUINS}/SKM_Manny_Simple'), ('Woman', f'{MANNEQUINS}/SKM_Quinn_Simple')]
# Linear colours, fair to deep (skin reflects about 60% down to under 10%).
TONES = [(.72, .52, .42), (.6, .4, .3), (.42, .28, .18), (.3, .18, .11), (.16, .09, .055), (.07, .04, .025)]
DOCK_TOP = 40.0


def import_art():
    task = unreal.AssetImportTask()
    for k, v in {'filename': str(ART), 'destination_path': UI, 'destination_name': 'T_TitleScreen_v1', 'automated': True,
                 'replace_existing': True, 'save': True}.items():
        task.set_editor_property(k, v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(f'{UI}/T_TitleScreen_v1')
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('never_stream', True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return texture


def body_materials():
    """The survivor's skin: the chosen tone, softly glossy. (The mannequins' own material only tints their painted
    trim.) One instance per body, so each can take its own skin later."""
    mel = unreal.MaterialEditingLibrary
    material, node, _ = material_builder(f'{CHARACTERS}/M_SurvivorBody_v1')
    material.set_editor_property('used_with_skeletal_mesh', True)   # without it a skinned body falls back to grey
    tone = node(unreal.MaterialExpressionVectorParameter, parameter_name='Tone', default_value=unreal.LinearColor(.78, .6, .48, 1))
    assert mel.connect_material_property(tone, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.5), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.35), '', unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    instances = {}
    for name, _ in BODIES:
        path = f'{CHARACTERS}/MI_SurvivorBody_{name}_v1'
        mi = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            path.rsplit('/', 1)[1], CHARACTERS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, material)
        mel.update_material_instance(mi)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
        instances[name] = mi
    return instances


def roster():
    asset = unreal.load_asset(f'{CHARACTERS}/DA_BodyRoster')
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', unreal.EWBodyRoster)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset('DA_BodyRoster', CHARACTERS, unreal.EWBodyRoster, factory)
    skins = body_materials()
    bodies, found = [], {}
    for name, path in BODIES:
        mesh = unreal.load_asset(path)
        assert mesh, path
        option = unreal.EWBodyOption()
        option.set_editor_property('display_name', name)
        option.set_editor_property('mesh', mesh)
        option.set_editor_property('tone_material', skins[name])
        option.set_editor_property('tone_parameters', ['Tone'])
        found[name] = skins[name].get_name()
        bodies.append(option)
    asset.set_editor_property('bodies', bodies)
    asset.set_editor_property('tones', [unreal.LinearColor(r, g, b, 1) for r, g, b in TONES])
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return found


def dock():
    """The end of a weathered dock: planks over joists on four posts, a low rail at the back."""
    b = Builder()
    for k in range(-9, 10):
        y = k * 21.0
        b.box((0, y, DOCK_TOP - 3), (420, 19.0, 6.0))
    for x in (-180.0, 180.0):
        b.box((x, 0, DOCK_TOP - 12), (14, 400, 12))
    for x in (-190.0, 190.0):
        for y in (-190.0, 190.0):
            b.tube([(x, y, -260), (x, y, DOCK_TOP + 40)], 11.0, sides=10)
    b.tube([(-190, -190, DOCK_TOP + 30), (-190, 190, DOCK_TOP + 30)], 4.0, sides=8)
    return b


def sea_material():
    mel = unreal.MaterialEditingLibrary
    material, node, _ = material_builder(f'{WORLD}/M_TitleSea_v1')
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.01, .03, .05, 1)), '',
                                         unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.06), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=1.0), '', unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def build_map():
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        assert world_map.open_map(level, MAP)
        for actor in actors.get_all_level_actors():
            if not isinstance(actor, unreal.WorldSettings):
                actors.destroy_actor(actor)
    else:
        assert level.new_level(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode', unreal.EWTitleGameMode)

    spawn = lambda cls, loc, rot=unreal.Rotator(): actors.spawn_actor_from_class(cls, unreal.Vector(*loc), rot)
    # Sky, low sun behind the survivor (toward the camera), haze.
    spawn(unreal.SkyAtmosphere, (0, 0, 0))
    sun = spawn(unreal.DirectionalLight, (0, 0, 500), unreal.Rotator(roll=0, pitch=-1.5, yaw=-12))
    sun_light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sun_light.set_editor_property('intensity', 8.0)
    sun_light.set_editor_property('light_color', unreal.Color(255, 190, 130, 255))
    sun_light.set_editor_property('atmosphere_sun_light', True)
    sky = spawn(unreal.SkyLight, (0, 0, 300))
    sky_light = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_light.set_editor_property('real_time_capture', True)
    sky_light.set_editor_property('intensity', .8)
    fog = spawn(unreal.ExponentialHeightFog, (0, 0, -100))
    fog.get_component_by_class(unreal.ExponentialHeightFogComponent).set_editor_property('fog_density', .02)
    spawn(unreal.VolumetricCloud, (0, 0, 0))
    # Warm key light from the camera side so the survivor reads, and a cool rim.
    key = spawn(unreal.RectLight, (260, 160, 230), unreal.Rotator(roll=0, pitch=-20, yaw=-150))
    key_light = key.get_component_by_class(unreal.RectLightComponent)
    key_light.set_editor_property('intensity', 30.0)
    key_light.set_editor_property('light_color', unreal.Color(255, 214, 170, 255))
    key_light.set_editor_property('attenuation_radius', 1200.0)

    timber = make_timber_material()
    dock_mesh = write_static_mesh(dock(), f'{WORLD}/SM_TitleDock_v1', [timber], 120.0)
    dock_actor = spawn(unreal.StaticMeshActor, (0, 0, 0))
    dock_actor.static_mesh_component.set_static_mesh(dock_mesh)
    sea = spawn(unreal.StaticMeshActor, (0, 0, -40))
    sea.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane'))
    sea.set_actor_scale3d(unreal.Vector(800, 800, 1))
    sea.static_mesh_component.set_material(0, sea_material())

    stand = spawn(unreal.TargetPoint, (0, 0, DOCK_TOP), unreal.Rotator(roll=0, pitch=0, yaw=0))
    stand.tags = ['PreviewSpot']
    camera = spawn(unreal.CameraActor, (640, 170, DOCK_TOP + 100), unreal.Rotator(roll=0, pitch=-2, yaw=180))
    camera.tags = ['CreatorCamera']
    camera.camera_component.set_editor_property('field_of_view', 40.0)
    camera.camera_component.set_editor_property('constrain_aspect_ratio', False)
    # The low sun and dark sea make auto exposure brighten too far; hold it down so colourings read true.
    look = camera.camera_component.get_editor_property('post_process_settings')
    look.set_editor_property('override_auto_exposure_bias', True)
    look.set_editor_property('auto_exposure_bias', -1.5)
    camera.camera_component.set_editor_property('post_process_settings', look)
    assert world_map.save_map()


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    import_art()
    found = roster()
    build_map()
    Path(unreal.Paths.project_saved_dir(), 'TitleResult.json').write_text(json.dumps({'success': True, 'skins': found}, indent=2))
    unreal.log('Title built')


if __name__ == '__main__':
    main()
