"""Play, second half of the world-state save round trip (M7 persistence, October 30); run after verify_world_save_a_play. One player,
a fresh Play session of the coastal map: the resources the first half changed are fresh again; loading the save (slot WorldSaveTest)
puts the world back as it was left: the knocked-over tree lies where it fell, the cut tree and the picked plant are gone, and the
deposit has what was left in it. The test slot is deleted afterwards. Writes Saved/WorldSaveBPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
report = {'checks': []}
state = {'phase': 'start', 'at': time.monotonic() + 12, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    if unreal.GameplayStatics.does_save_game_exist('WorldSaveTest', 0):
        unreal.GameplayStatics.delete_game_in_slot('WorldSaveTest', 0)
    report.update(success=error is None, error=error)
    (saved / 'WorldSaveBPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK WorldSaveB success={error is None} error={error}')


def named(cls, name):
    return next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world, cls) if a.get_name() == name and not a.is_actor_being_destroyed()), None)


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        want = json.loads((saved / 'WorldSaveExpected.json').read_text())
        if p == 'start':
            check('the first half left a save', unreal.EWSurvivorSave.has_save('WorldSaveTest'))
            lying, gone = named(unreal.EWHarvestTree, want['lying_tree']), named(unreal.EWHarvestTree, want['gone_tree'])
            plant, rock = named(unreal.EWHandGatherable, want['gone_plant']), named(unreal.EWMineable, want['rock'])
            check('a fresh map: both trees stand, the plant grows, the deposit is whole',
                  lying and not lying.is_felled() and gone and plant and rock and rock.get_editor_property('remaining') >= 4)   # a fresh deposit holds 4 to 8
            check('the save loads', unreal.EWSurvivorSave.load_save('WorldSaveTest').apply_to(pawn))
            state.update(phase='verify', at=time.monotonic() + 1.0)
        elif p == 'verify':
            lying = named(unreal.EWHarvestTree, want['lying_tree'])
            check('the knocked-over tree lies where it fell', lying and lying.is_felled()
                  and (lying.get_actor_location() - unreal.Vector(*want['lying_at'])).length() < 5
                  and abs(lying.get_actor_rotation().pitch - want['lying_pitch_roll'][0]) < 1 and abs(lying.get_actor_rotation().roll - want['lying_pitch_roll'][1]) < 1)
            check('the cut tree is gone', named(unreal.EWHarvestTree, want['gone_tree']) is None)
            check('the picked plant is gone', named(unreal.EWHandGatherable, want['gone_plant']) is None)
            rock = named(unreal.EWMineable, want['rock'])
            check('the deposit has what was left in it', rock and rock.get_editor_property('remaining') == want['rock_left'],
                  left=rock.get_editor_property('remaining') if rock else None)
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
