"""Create a saved, isolated M5D fixture. Does not change the normal startup map."""
import unreal
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)
assets = unreal.AssetToolsHelpers.get_asset_tools()
path = '/Game/Elitewake/Blueprints/BP_TestWoodPickup'
if not unreal.EditorAssetLibrary.does_asset_exist(path):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property('parent_class', unreal.load_class(None, '/Script/EW.EWPickup'))
    blueprint = assets.create_asset('BP_TestWoodPickup', '/Game/Elitewake/Blueprints', unreal.Blueprint, factory)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
cls = unreal.EditorAssetLibrary.load_blueprint_class(path)
default = unreal.get_default_object(cls)
item = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
assert item, 'Saved M5C test item must exist before creating pickup content'
default.set_editor_property('item_definition', item)
default.set_editor_property('quantity', 10)
assert unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
map_path = '/Game/Elitewake/Maps/Lvl_M5PickupTest'
if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
    assert level.new_level(map_path)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -25))
    floor.set_actor_label('M5D Test Floor')
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    floor.set_actor_scale3d(unreal.Vector(20,20,.5))
    start = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0,0,92))
    start.set_actor_rotation(unreal.Rotator(), False)
    pickup = actors.spawn_actor_from_class(cls, unreal.Vector(150,0,155))
    pickup.set_editor_property('item_definition', item)
    pickup.set_editor_property('quantity', 10)
    pickup.set_actor_label('M5D Wood x10 - face forward and press E or X')
    light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0,0,600))
    light.set_actor_rotation(unreal.Rotator(-45,0,0), False)
    actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0,0,600))
    assert world_map.save_map()
else:
    assert level.load_level(map_path)
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_class() == cls:
            actor.set_editor_property('item_definition', item)
            actor.set_editor_property('quantity', 10)
    assert world_map.save_map()
unreal.log('M5D pickup Blueprint and isolated test map ready; normal startup map unchanged.')
