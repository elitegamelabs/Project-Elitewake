"""Screenshots of the first ship in the coastal map for visual review. Run through run_play_check.py with
EW_PLAY_PLAYERS=1. Views are placed relative to the ship, into Saved/Screenshots/ShipViews/.
A screenshot is not acceptance by itself: a person still has to look at it.
"""
import json
import math
import time
from pathlib import Path
import unreal

saved = Path(unreal.Paths.project_saved_dir())
folder = saved / 'Screenshots' / 'ShipViews'
folder.mkdir(parents=True, exist_ok=True)
world = unreal.EWEditorVerificationLibrary.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
movement = pawn.get_component_by_class(unreal.CharacterMovementComponent)
SHIP_ID = 'Sloop'
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == SHIP_ID)
deck = ship.get_deck_height()
HALF = 98

# name, survivor position in the ship's frame (x forward, y starboard, z up from the waterline), look-at point
VIEWS = [
    ('01_port_bow', (900, -700, 20), (0, 0, 150)),
    ('02_starboard_quarter', (-900, 650, 20), (0, 0, 150)),
    ('03_deck_forward', (-380, -110, deck + HALF), (500, 0, deck + 60)),
    ('04_deck_aft', (300, 90, deck + HALF), (-500, 0, deck + 60)),
    ('05_hold', (230, 0, 30 + HALF), (-300, 0, 120)),
    ('06_hatch_from_hold', (60, 40, 30 + HALF), (-120, 0, 260)),
]
state = {'index': 0, 'phase': 'place', 'at': time.monotonic(), 'shots': []}


def to_world(p):
    return ship.get_actor_transform().transform_location(unreal.Vector(*p))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    if state['index'] >= len(VIEWS):
        unreal.unregister_slate_post_tick_callback(handle)
        (saved / 'ShipViewsResult.json').write_text(json.dumps({'success': True, 'shots': state['shots']}, indent=2))
        return
    name, where, target = VIEWS[state['index']]
    eye = to_world(where)
    look = unreal.MathLibrary.find_look_at_rotation(eye, to_world(target))
    if state['phase'] == 'place':
        pawn.teleport(eye, unreal.Rotator(0, 0, look.yaw))
        movement.stop_movement_immediately()
        pc.set_control_rotation(look)
        state.update(phase='shoot', at=time.monotonic() + 3.0)
    else:
        pc.set_control_rotation(look)
        path = folder / f'{name}.png'
        unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{path}"')
        state['shots'].append(str(path))
        state.update(phase='place', index=state['index'] + 1, at=time.monotonic() + 1.5)


handle = unreal.register_slate_post_tick_callback(tick)
