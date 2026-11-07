"""Set up the World Partition copy of the canonical map (November 6, the streaming work; CLAUDE.md 9.6: islands stream
and dense foliage exists only near the player). Safe to run again. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"
after WorldPartitionConvertCommandlet has converted the map in place (one file per actor; the grass, seabed plants,
bushes and ferns partitioned into foliage cells).

DECIDED (owner-delegated; the first, safest step):
- Only the ground cover streams: the partitioned foliage, about 7.8 million instances, drawn no further than 120 m.
  It loads in CELL cells within LOADING of the player, well beyond where any of it is drawn.
- Everything else stays loaded as before: the islands' ground (seen from the sea at 1-2 km), landmarks, ports, ice,
  forests, and every actor with game state (plants, rocks, animals, ships, people), so harvesting, saving and the
  server behave exactly as they did. Streaming the islands themselves comes with HLODs.
Writes Saved/WorldPartitionSetupResult.json. EW_QUIT_WHEN_DONE=1 closes the editor at the end.
"""
import json
import os
import time
from pathlib import Path
import unreal
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
CELL, LOADING = 25600, 51200        # cm (tuning)


def describe(obj, depth=0):
    """Names of an object's editor properties, for the log (the runtime hash's layout differs between engine versions)."""
    try:
        return sorted(p for p in dir(obj) if not p.startswith('_'))[:80]
    except Exception as error:      # noqa: BLE001
        return repr(error)


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert world_map.open_map(level, MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    lib = unreal.WorldPartitionBlueprintLibrary
    descs = lib.get_actor_descs()
    report = {'actor_descs': len(descs)}
    report['load_actors_returned'] = lib.load_actors([d.guid for d in descs])
    if not report['load_actors_returned']:
        # Loaded one by one, so one actor that will not load does not keep the rest from loading.
        report['failed'] = [str(d.label) for d in descs if not lib.load_actors([d.guid])][:30]
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    report['loaded_actors'] = len(actors)
    assert len(actors) >= len(descs) * .99, f'only {len(actors)} of {len(descs)} actors loaded'
    streamed, kept = {}, {}
    for actor in actors:
        kind = actor.get_class().get_name()
        foliage = 'InstancedFoliageActor' in kind
        want = foliage                                   # only the ground cover streams
        if actor.get_editor_property('is_spatially_loaded') != want:
            actor.modify()
            actor.set_editor_property('is_spatially_loaded', want)
        (streamed if want else kept)[kind] = (streamed if want else kept).get(kind, 0) + 1
    report.update(streamed=streamed, always_loaded=kept)
    # The runtime grid: CELL cells loaded within LOADING.
    settings = world.get_world_settings()
    grid = {}
    try:
        partition = settings.get_editor_property('world_partition')
        runtime = partition.get_editor_property('runtime_hash')
        grid['hash_class'] = runtime.get_class().get_name()
        if hasattr(runtime, 'runtime_partitions') or 'runtime_partitions' in describe(runtime):
            parts = runtime.get_editor_property('runtime_partitions')
            for desc in parts:
                main = desc.get_editor_property('main_layer')
                for prop, value in (('cell_size', CELL), ('loading_range', LOADING)):
                    try:
                        main.set_editor_property(prop, value)
                    except Exception as error:      # noqa: BLE001
                        grid[f'set_{prop}_failed'] = repr(error)
                grid.setdefault('partitions', []).append({'name': str(desc.get_editor_property('name')),
                                                          'class': main.get_class().get_name(),
                                                          'cell_size': main.get_editor_property('cell_size'),
                                                          'loading_range': main.get_editor_property('loading_range')})
            runtime.set_editor_property('runtime_partitions', parts)
        else:
            grid['runtime_props'] = describe(runtime)
        settings.modify()
    except Exception as error:      # noqa: BLE001
        grid['error'] = repr(error)
        grid['settings_props'] = describe(settings)
    report['grid'] = grid
    assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    report.update(success=True, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    Path(unreal.Paths.project_saved_dir(), 'WorldPartitionSetupResult.json').write_text(json.dumps(report, indent=2, default=str))
    unreal.log(f'EWWP done: {json.dumps(report, default=str)[:1500]}')


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
