"""Opening and saving the canonical map from editor scripts, World Partition or not (November 6, the streaming work).

On a World Partition map the editor loads only the always-loaded actors when the map opens, and every actor is saved
in its own file. A setup script expects the whole world, so:
    open_map(level, path)   opens the map and, if it is partitioned, loads every actor (the ground-cover cells included)
    save_map()              saves the map and every changed actor and foliage cell
    partitioned()           whether the open map is a World Partition map
    keep_loaded(actor)      always loaded, like everything but the ground cover (setup_world_partition.py); an actor added
                            to a partitioned map is otherwise streamed, and a client far from it would not have it
Editor only.
"""
import unreal


def partitioned():
    try:
        return bool(unreal.WorldPartitionBlueprintLibrary.get_actor_descs())
    except Exception:      # noqa: BLE001  (no World Partition on this map)
        return False


def open_map(level, path):
    if not level.load_level(path):
        return False
    if partitioned():
        descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
        loaded = len(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
        assert loaded >= len(descs) * .99, f'only {loaded} of {len(descs)} actors loaded'
    return True


def save_map():
    """Every changed package: the map, and on a World Partition map each changed actor and foliage cell."""
    return unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)


def keep_loaded(actor):
    """Always loaded (not streamed by distance), the rule for everything but the ground cover (November 6)."""
    try:
        actor.set_editor_property('is_spatially_loaded', False)
    except Exception:      # noqa: BLE001  (not a World Partition map)
        pass
    return actor
