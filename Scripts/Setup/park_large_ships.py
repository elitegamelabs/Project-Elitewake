"""Take the schooner and the brigantine out of the coastal map while their designs are reworked (owner, October 12).
Safe to run again. Run in the editor, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Their definitions, meshes and build scripts stay: build_schooner.py and build_brigantine.py put them back.
"""
import json
from pathlib import Path
import unreal

MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'  # ships and sea life live in the test map (owner, October 14)
PARKED = ('Schooner', 'Brigantine')


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    removed = []
    for ship in [a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip)]:
        definition = ship.get_editor_property('definition')
        if definition and str(definition.get_editor_property('ship_id')) in PARKED:
            removed.append(ship.get_actor_label())
            actors.destroy_actor(ship)
    assert level.save_current_level()
    remaining = [str(a.get_editor_property('definition').get_editor_property('ship_id'))
                 for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip)]
    Path(unreal.Paths.project_saved_dir(), 'ParkLargeShipsResult.json').write_text(json.dumps(
        {'success': True, 'removed': removed, 'remaining': remaining}, indent=2))
    unreal.log(f'Parked {removed}; remaining {remaining}')


if __name__ == '__main__':
    main()
