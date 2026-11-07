"""Keep every climb-out clear (owner, November 5-6: a swimmer must never be stuck; climb-outs and Saltreach's rock steps).
Safe to run again. Run in the editor outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
The dressing steps keep off climb-outs as they place things (world_terrain.near_climb), but a map dressed before a climb-out
was cut, or before the rule, can still have trees, plants or rocks standing on one, and grass or seabed plants floating over
the cut ground. This removes, on and within CLEAR of each climb-out's path and rock-cut sides:
  - tree, gatherable-plant and mineable-rock actors (they would block the way or stand in the air);
  - foliage instances (grass, understory, seabed life): nothing collides with them, but they would float over the cut.
Writes Saved/ClearClimbOutsResult.json.
"""
import json
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_terrain as T  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
CLEAR = 200.0         # cm past the path's rock-cut sides
BLOCKING = ('EWHarvestTree', 'EWHandGatherable', 'EWMineable')


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    removed = {}
    for actor in actors.get_all_level_actors():
        kind = actor.get_class().get_name()
        if kind in BLOCKING:
            p = actor.get_actor_location()
            if T.near_climb(p.x, p.y, CLEAR):
                removed[kind] = removed.get(kind, 0) + 1
                actors.destroy_actor(actor)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    # Circles along every path (millions of grass instances are too many to look at one by one): the engine finds the
    # instances in each, and each is then checked against the path itself.
    reach = T.CLIMB_HALF + T.CLIMB_SIDE + CLEAR
    circles = []
    for climb in {id(c): c for cell in T.CLIMB_INDEX.values() for c in cell}.values():
        for (ax, ay), (bx, by) in zip(climb.line, climb.line[1:]):
            n = max(1, int(((bx - ax) ** 2 + (by - ay) ** 2) ** .5 / reach))
            circles += [(ax + (bx - ax) * k / n, ay + (by - ay) * k / n) for k in range(n + 1)]
    instances = {}
    for foliage in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
        for comp in foliage.get_components_by_class(unreal.InstancedStaticMeshComponent):
            found = set()
            for x, y in circles:
                for z in (-3000.0, 0.0, 3000.0, 6000.0, 9000.0, 12000.0, 15000.0):    # paths run from 25 m under the sea to 110 m up
                    found.update(comp.get_instances_overlapping_sphere(unreal.Vector(x, y, z), reach * 1.6, True))
            doomed = []
            for k in sorted(found):
                t = comp.get_instance_transform(k, True)
                t = t[-1] if isinstance(t, tuple) else t
                if t and T.near_climb(t.translation.x, t.translation.y, CLEAR):
                    doomed.append(k)
            if doomed:
                comp.remove_instances(doomed)
                mesh = comp.get_editor_property('static_mesh')
                name = mesh.get_name() if mesh else 'foliage'
                instances[name] = instances.get(name, 0) + len(doomed)
    assert world_map.save_map()
    report = {'success': True, 'actors_removed': removed, 'foliage_instances_removed': instances,
              'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    Path(unreal.Paths.project_saved_dir(), 'ClearClimbOutsResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Climb-outs cleared: {removed} actors, {sum(instances.values())} foliage instances')


if __name__ == '__main__':
    main()
