"""Build a small, isolated Play fixture for the Plains3 sea-cavern exit.

This creates a separate preview map and the same cave/ramp mesh assets used by
build_caves.py. It never changes Lvl_CoastalPlayground or startup settings.
The simple landing slab is only a collision fixture; final terrain still needs
the full world build and a real sailing and walking pass.
"""
import json
import math
import sys
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import build_caves as B  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_PlainsCavernExitPreview'
RESULT = Path(unreal.Paths.project_saved_dir(), 'PlainsCavernExitPreviewResult.json')
cave = B.T.CAVES['Plains3']
assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(), 'Save current level first'

level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()).startswith('Preview/PlainsExit'):
            actors.destroy_actor(actor)
else:
    assert level.new_level(MAP)

# Unload the multi-gigabyte gameplay map before meshing the preview cave.
rock, triangles = B.cave_mesh(cave)
ramp = B.exit_ramp_mesh(cave)


def mesh(label, asset, xyz, folder='Preview/PlainsExit'):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*xyz), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_folder_path(folder)
    actor.static_mesh_component.set_static_mesh(asset)
    return actor


mesh('Plains3 sea cavern: rock', rock, (0, 0, cave.floor))
mesh('Plains3 sea cavern: walkable inland ramp', ramp, (0, 0, cave.floor))
for index, u in enumerate((cave.chamber_u, cave.chamber_u + 2400, cave.depth - 300)):
    v, surface = cave.inland_exit_profile(u)
    lx, ly = cave.world(u, v)
    light = actors.spawn_actor_from_class(unreal.PointLight,
                                           unreal.Vector(lx - cave.mx, ly - cave.my, surface + 350))
    light.set_actor_label(f'Preview only: exit inspection light {index + 1}')
    light.set_folder_path('Preview/PlainsExit')
    lamp = light.get_component_by_class(unreal.PointLightComponent)
    lamp.set_editor_property('intensity', 800.0)
    lamp.set_editor_property('attenuation_radius', 4200.0)
end = cave.depth + 700.0
v, landing = cave.inland_exit_profile(end)
x, y = cave.world(end, v)
land = mesh('Preview landing ground (fixture only)', unreal.load_asset('/Engine/BasicShapes/Cube'),
            (x - cave.mx + 800, y - cave.my, landing - 50))
land.set_actor_scale3d(unreal.Vector(18, 14, 1))

start_u = cave.chamber_u + 300.0
start_v, start_z = cave.inland_exit_profile(start_u)
sx, sy = cave.world(start_u, start_v)
player = actors.spawn_actor_from_class(unreal.PlayerStart,
                                       unreal.Vector(sx - cave.mx, sy - cave.my, start_z + 105))
player.set_actor_label('Start on dry cave landing')
player.set_folder_path('Preview/PlainsExit')
player.set_actor_rotation(unreal.Rotator(0, 0, 0), False)

mode = unreal.EditorAssetLibrary.load_blueprint_class('/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode')
assert mode, 'Existing third-person game mode is required'
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode', mode)
sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 10000))
sun.set_actor_label('Preview sun')
sun.set_folder_path('Preview/PlainsExit')
sun.set_actor_rotation(unreal.Rotator(-40, -25, 0), False)
actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector()).set_folder_path('Preview/PlainsExit')
actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector()).set_folder_path('Preview/PlainsExit')
look = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector())
look.set_actor_label('Preview only: restrained cave exposure')
look.set_folder_path('Preview/PlainsExit')
look.set_editor_property('unbound', True)
settings = look.get_editor_property('settings')
settings.set_editor_property('override_auto_exposure_bias', True)
settings.set_editor_property('auto_exposure_bias', -2.5)
look.set_editor_property('settings', settings)
assert level.save_current_level()

cam_u = cave.chamber_u + 2000
cam_v, cam_z = cave.inland_exit_profile(cam_u)
cx, cy = cave.world(cam_u, cam_v)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(
    unreal.Vector(cx - cave.mx, cy - cave.my, cam_z + 450),
    unreal.Rotator(0, -8, math.degrees(cave.heading)))
report = {'success': True, 'map': MAP, 'cave': 'Plains3', 'rock_triangles': triangles,
          'preview_only': True, 'final_terrain_built': False, 'sailing_verified': False}
RESULT.write_text(json.dumps(report, indent=2))
unreal.log('Plains cavern exit preview ready: ' + json.dumps(report))
