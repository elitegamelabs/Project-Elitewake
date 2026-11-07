"""The testing teleport (Shift + 1..5) lands on each region's island, on dry ground (November 6: it still used the old
five-island centres and dropped the survivor in deep sea). One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_region_teleport_play.py -Result RegionTeleportPlayResult.json -Players 1 -Standalone 1
Writes Saved/RegionTeleportPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

world = unreal.EWEditorVerificationLibrary.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
RESULT = Path(unreal.Paths.project_saved_dir(), 'RegionTeleportPlayResult.json')
WANT = ['PLAINS', 'JUNGLE', 'DESERT', 'SWAMP', 'WINTER']
state = {'i': 0, 'phase': 'go', 'at': time.monotonic() + 1.0, 'h': None}
report = {'stops': []}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK RegionTeleport success={error is None} error={error}')


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(WANT):
            finish()
            return
        if state['phase'] == 'go':
            pc.debug_teleport_to_region(state['i'])
            state.update(phase='look', at=time.monotonic() + 4.0)
            return
        at = pawn.get_actor_location()
        region = str(unreal.EWClimateRegion.sample_climate(world, at).get_editor_property('region')).upper()
        swimming = pawn.get_movement_component().is_swimming()
        falling = pawn.get_movement_component().is_falling()
        stop = {'index': state['i'], 'at_m': [round(at.x / 100), round(at.y / 100), round(at.z / 100, 1)], 'region': region,
                'swimming': swimming, 'falling': falling}
        report['stops'].append(stop)
        assert WANT[state['i']] in region and not swimming and not falling and at.z > -40, stop
        state.update(i=state['i'] + 1, phase='go', at=time.monotonic() + .5)
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
