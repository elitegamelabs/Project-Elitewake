"""Gives each ship that has a deck below the weather deck her permanent surgeon (design reference; Milestones "Permanent ship surgeon").
Safe to run again. Run in the editor outside Play:
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -nullrhi -run=pythonscript -script=<this file>
The surgeon stands beside the operating-table prop that each hull builder already puts in the first deck below the weather deck
(ship_interior.surgeon_table: sloop (-520, -105), schooner (-900, -50), brigantine (-1300, -90) in the ship's own cm), on that
hold's floor, facing the table. The Raft and Dinghy have no deck below and so no surgeon."""
import json
from pathlib import Path
import unreal

SPOTS = {
    # name: (x, y, yaw) beside the table, standing on the hold floor
    'Sloop': (-520.0, -42.0, -90.0),
    'Schooner': (-900.0, 18.0, -90.0),
    'Brigantine': (-1230.0, -90.0, 180.0),
}


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    done = {}
    for name, (x, y, yaw) in SPOTS.items():
        definition = unreal.load_asset(f'/Game/Elitewake/Ships/DA_Ship_{name}')
        assert definition, name
        floor = definition.get_editor_property('hold_floor_height')
        definition.set_editor_property('has_surgeon', True)
        definition.set_editor_property('surgeon_point', unreal.Vector(x, y, floor))
        definition.set_editor_property('surgeon_yaw', yaw)
        assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
        done[name] = [x, y, floor, yaw]
    Path(unreal.Paths.project_saved_dir(), 'ShipSurgeonsResult.json').write_text(json.dumps({'success': True, 'ships': done}, indent=2))
    unreal.log(f'Ship surgeons set: {done}')


if __name__ == '__main__':
    main()
