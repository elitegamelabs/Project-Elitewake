"""Put the sloop back at the island (owner, October 15), as it lies in the ships test map: anchored off the beach,
its helm and sails in its hold for the survivor to fit. Safe to run again. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
The raft, dinghy, schooner and brigantine stay in /Game/Elitewake/Maps/Test/Lvl_ShipsTest.
"""
import json
from pathlib import Path
import unreal
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
TEST_MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'


def ships(actors):
    return [a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip)]


def ship_id(ship):
    d = ship.get_editor_property('definition')
    return str(d.get_editor_property('ship_id')) if d else ''


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(TEST_MAP)
    sloop = next(s for s in ships(actors) if ship_id(s) == 'Sloop')
    where = (sloop.get_actor_location(), sloop.get_actor_rotation(), sloop.get_actor_label(), sloop.get_class(),
             sloop.get_editor_property('definition'))
    kit = next(a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWStarterKit))
    cargo = [(e.get_editor_property('item'), e.get_editor_property('quantity')) for e in kit.get_editor_property('ship_cargo')]

    assert world_map.open_map(level, MAP)
    for old in ships(actors):
        if ship_id(old) == 'Sloop':
            actors.destroy_actor(old)
    location, rotation, label, cls, definition = where
    ship = actors.spawn_actor_from_class(cls, location, rotation)
    ship.set_editor_property('definition', definition)
    ship.set_actor_label(label)
    kit = next(a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWStarterKit))
    entries = []
    for item, quantity in cargo:
        e = unreal.EWStarterKitItem()
        e.set_editor_property('item', item)
        e.set_editor_property('quantity', quantity)
        entries.append(e)
    kit.set_editor_property('ship_cargo', entries)
    assert world_map.save_map()
    Path(unreal.Paths.project_saved_dir(), 'RestoreSloopResult.json').write_text(json.dumps({
        'success': True, 'location': [location.x, location.y, location.z], 'label': label,
        'cargo': [f'{i.get_name()} x{q}' for i, q in cargo if i]}, indent=2))
    unreal.log('Sloop restored')


if __name__ == '__main__':
    main()
