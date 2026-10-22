"""Remove the manatee from active gameplay (owner, October 22, 2026): delete its actors from the maps, rebuild the journal pages without it, and
report whether anything still references its assets (which are then moved to quarantine by hand). Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
Writes Saved/RemoveManateeResult.json."""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

MAPS = ('/Game/Elitewake/Maps/Lvl_CoastalPlayground', '/Game/Elitewake/Maps/Test/Lvl_ShipsTest')
ASSETS = ('/Game/Elitewake/Wildlife/Fish/DA_Fish_Manatee', '/Game/Elitewake/Wildlife/Fish/MI_Manatee_v1',
          '/Game/Elitewake/Wildlife/Fish/SM_Manatee_v1', '/Game/Elitewake/Wildlife/Fish/T_Manatee_v1')
report = {'removed': {}, 'references_left': {}}
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for m in MAPS:
    assert level.load_level(m), m
    gone = 0
    for a in list(actors_sub.get_all_level_actors()):
        if isinstance(a, unreal.EWFish):
            d = a.get_editor_property('definition')
            if d and str(d.get_editor_property('display_name')) == 'Manatee':
                actors_sub.destroy_actor(a)
                gone += 1
    report['removed'][m] = gone
    assert level.save_current_level(), m

import create_test_journal
create_test_journal.main()          # the journal pages, without the manatee lines

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.wait_for_completion()
opts = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
for a in ASSETS:
    refs = [str(r) for r in (ar.get_referencers(a, opts) or []) if str(r) != a]
    report['references_left'][a] = refs
report['success'] = True
Path(unreal.Paths.project_saved_dir(), 'RemoveManateeResult.json').write_text(json.dumps(report, indent=2))
unreal.log('Manatee removed from the maps')
unreal.SystemLibrary.quit_editor()
