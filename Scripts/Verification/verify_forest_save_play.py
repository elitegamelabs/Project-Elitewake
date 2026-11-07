"""Felled forest trees survive a save and load (November 6; CLAUDE.md 5.4). One player, standalone, on the canonical map:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_forest_save_play.py -Result ForestSavePlayResult.json -Players 1 -Standalone 1

Uses the server's own world save (UEWBuildSave::SaveWorld / RestoreWorld) in a test slot, deleted at the end:
  1. A tree started on (now a harvestable tree, still standing) is saved as standing.
  2. A tree cut down and gone is saved as down, with about 20 minutes to regrow.
  3. After every tree grows back (the world as freshly loaded), restoring the save puts the cut tree down again with the
     time it had left, and leaves the started one standing.
Writes Saved/ForestSavePlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
RESULT = Path(unreal.Paths.project_saved_dir(), 'ForestSavePlayResult.json')
SLOT = 'ForestSaveCheck'
report = {'checks': []}


def check(label, ok, **seen):
    report['checks'].append(dict(label=label, ok=bool(ok), **{k: str(v) for k, v in seen.items()}))
    assert ok, f'{label}: {seen}'


def saved_trees():
    save = unreal.GameplayStatics.load_game_from_slot(SLOT, 0)
    state = save.get_editor_property('world_state')
    return {(str(t.get_editor_property('forest')), t.get_editor_property('index')): t.get_editor_property('regrow_left')
            for t in state.get_editor_property('forest_trees')}


def run():
    forest = next(f for f in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWForest) if 'Plains' in f.get_actor_label())
    name = str(forest.get_fname())
    standing = [i for i in range(forest.get_tree_count()) if forest.is_standing(i)]
    started, cut = standing[0], standing[len(standing) // 2]
    report.update(forest=forest.get_actor_label(), started=started, cut=cut)
    begun = forest.promote(started)
    check('the first tree becomes a harvestable tree', begun is not None and not forest.is_standing(started))
    gone = forest.promote(cut)
    gone.destroy_actor()              # cut down and faded away
    check('the world saves', unreal.EWBuildSave.save_world(world, SLOT))
    trees = saved_trees()
    report['saved'] = {f'{k[1]}': round(v) for k, v in trees.items() if k[0] == name}
    check('the started tree is saved standing', (name, started) not in trees)
    check('the cut tree is saved down, with about 20 minutes to regrow', (name, cut) in trees and 1100 < trees[(name, cut)] <= 1200,
          left=trees.get((name, cut)))
    # The world as freshly loaded: every tree standing again.
    begun.destroy_actor()
    forest.regrow_all_now()
    check('every tree stands again before the load', forest.is_standing(started) and forest.is_standing(cut))
    unreal.EWBuildSave.restore_world(world, SLOT)
    left = forest.get_regrow_left(cut)
    check('after the load the cut tree is down again', not forest.is_standing(cut), left=left)
    check('with the time it had left to regrow', 1100 < left <= 1200, left=left)
    check('and the started tree stands, whole', forest.is_standing(started))
    report['regrow_left_after_load_s'] = round(left)


try:
    run()
    report['success'] = True
except Exception as error:      # noqa: BLE001
    report.update(success=False, error=repr(error))
finally:
    if unreal.GameplayStatics.does_save_game_exist(SLOT, 0):
        unreal.GameplayStatics.delete_game_in_slot(SLOT, 0)
    report['finished_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f"EWPLAYCHECK ForestSave success={report['success']} error={report.get('error')}")
