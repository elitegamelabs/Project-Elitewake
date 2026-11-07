"""The HUD's region is right from the first moments after spawn (November 6: a packaged first frame showed "Open Sea" on the
starter beach). One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_spawn_region_play.py -Result SpawnRegionPlayResult.json -Players 1 -Standalone 1
Reads the survivor's climate on the first frames the check runs (Play has just begun) and expects Plains.
Writes Saved/SpawnRegionPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

world = unreal.EWEditorVerificationLibrary.get_play_worlds()[0]
pawn = unreal.GameplayStatics.get_player_controller(world, 0).get_controlled_pawn()
RESULT = Path(unreal.Paths.project_saved_dir(), 'SpawnRegionPlayResult.json')
state = {'frames': 0, 'seen': [], 'h': None}


def tick(_):
    climate = pawn.get_survival_component().get_climate()
    state['seen'].append(str(climate.get_editor_property('region')))
    state['frames'] += 1
    if state['frames'] < 3:
        return
    unreal.unregister_slate_post_tick_callback(state['h'])
    ok = all('PLAINS' in s.upper() for s in state['seen'])
    RESULT.write_text(json.dumps({'success': ok, 'regions_by_frame': state['seen'], 'error': None if ok else 'not Plains at spawn',
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWPLAYCHECK SpawnRegion success={ok}')


state['h'] = unreal.register_slate_post_tick_callback(tick)
