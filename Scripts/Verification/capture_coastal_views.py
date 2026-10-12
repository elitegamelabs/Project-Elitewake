"""Screenshots of the coastal test map for visual review. Run through run_play_check.py with EW_PLAY_PLAYERS=1.

Moves the survivor to a few fixed viewpoints and captures each with the HUD, into Saved/Screenshots/CoastalViews/.
A screenshot is not acceptance by itself: a person still has to look at it.
"""
import json
import time
from pathlib import Path
import unreal

saved = Path(unreal.Paths.project_saved_dir())
folder = saved / 'Screenshots' / 'CoastalViews'
folder.mkdir(parents=True, exist_ok=True)
world = unreal.EWEditorVerificationLibrary.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
movement = pawn.get_component_by_class(unreal.CharacterMovementComponent)

# name, survivor location, view rotation (pitch, yaw)
VIEWS = [
    ('01_beach_north', (150, 0, 200), (-8, 0)),
    ('02_dock_to_ship', (5300, 900, 140), (-10, 35)),
    ('03_shore_to_islet', (3200, 1500, 120), (-6, 10)),
    ('04_swimming', (6600, -300, -80), (-5, 60)),
    ('05_underwater', (6600, -300, -400), (5, 60)),
    ('06_shoreline', (3700, -1400, 200), (-18, 50)),
]
state = {'index': 0, 'phase': 'place', 'at': time.monotonic(), 'shots': []}

def tick(delta):
    if time.monotonic() < state['at']:
        return
    if state['index'] >= len(VIEWS):
        unreal.unregister_slate_post_tick_callback(handle)
        (saved / 'CoastalViewsResult.json').write_text(json.dumps({'success': True, 'shots': state['shots']}, indent=2))
        return
    name, location, (pitch, yaw) = VIEWS[state['index']]
    if state['phase'] == 'place':
        pawn.teleport(unreal.Vector(*location), unreal.Rotator(0, 0, yaw))
        movement.stop_movement_immediately()
        pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
        state.update(phase='shoot', at=time.monotonic() + 4.0)
    else:
        pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
        path = folder / f'{name}.png'
        unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{path}"')
        state['shots'].append(str(path))
        state.update(phase='place', index=state['index'] + 1, at=time.monotonic() + 1.5)

handle = unreal.register_slate_post_tick_callback(tick)
