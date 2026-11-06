"""The canonical map's always-loaded sublevels (November 6). GitHub's large-file storage refuses any file over 2 GB, and
Lvl_CoastalPlayground.umap reached 2.07 GB, so new bulk content lives in a sublevel of its own that loads with the map:
    Lvl_CoastalPlayground_Forests: the forest stands and their bushes (build_forests.py) and the glaciers
    (build_glaciers.py).
World Partition (one file per actor, streamed by distance) is the lasting fix and comes with the streaming work.
Editor only, with the map loaded:
    use(FORESTS)   make the sublevel the one new actors and foliage go into (created and added, always loaded, the first time)
    save()         save the map and its sublevels
"""
import unreal

FORESTS = '/Game/Elitewake/Maps/Lvl_CoastalPlayground_Forests'


def use(path=FORESTS):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    entry = unreal.GameplayStatics.get_streaming_level(world, path)
    if not entry:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            entry = unreal.EditorLevelUtils.add_level_to_world(world, path, unreal.LevelStreamingAlwaysLoaded)
        else:
            entry = unreal.EditorLevelUtils.create_new_streaming_level(unreal.LevelStreamingAlwaysLoaded, path, False)
            entry = unreal.GameplayStatics.get_streaming_level(world, path) or entry
    assert entry, path
    level = entry.get_loaded_level()
    assert level, f'{path} is not loaded'
    unreal.EditorLevelUtils.make_level_current(entry)
    return entry


def save():
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
