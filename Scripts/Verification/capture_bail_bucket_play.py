"""Capture the modeled sloop bucket on deck for T21 visual review.

Run through run_play_check.py on /Game/Elitewake/Maps/Lvl_CoastalPlayground with one player.
The screenshot is saved to Saved/Screenshots/ShipViews/07_bailing_bucket_review.png.
"""
import json
import time
from pathlib import Path
import unreal

saved = Path(unreal.Paths.project_saved_dir())
folder = saved / 'Screenshots' / 'ShipViews'
folder.mkdir(parents=True, exist_ok=True)
result = saved / 'BailBucketScreenshotResult.json'
world = unreal.EWEditorVerificationLibrary.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop')
movement = pawn.get_component_by_class(unreal.CharacterMovementComponent)
bucket = ship.get_bucket_world()
bucket_local = ship.get_actor_transform().inverse_transform_location(bucket)
# Leave enough room for the third-person camera to pull back without hitting the ship's collision.
eye_local = unreal.Vector(bucket_local.x + 650.0, bucket_local.y - 500.0, bucket_local.z + 98.0)
eye = ship.get_actor_transform().transform_location(eye_local)
look = unreal.MathLibrary.find_look_at_rotation(eye, bucket + unreal.Vector(0.0, 0.0, 12.0))
pawn.teleport(eye, unreal.Rotator(0.0, 0.0, look.yaw))
movement.stop_movement_immediately()
pc.set_control_rotation(look)
state = {'phase': 'settle', 'at': time.monotonic() + 2.0}
image_stem = '07_bailing_bucket_review'
image = folder / f'{image_stem}.png'
started = time.time()


def tick(delta):
    if time.monotonic() < state['at']:
        return
    if state['phase'] == 'settle':
        unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
        unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{image}"')
        state.update(phase='write', at=time.monotonic() + 2.0)
        return
    unreal.unregister_slate_post_tick_callback(handle)
    shots = sorted(folder.glob(f'{image_stem}*.png'), key=lambda path: path.stat().st_mtime, reverse=True)
    shot = next((path for path in shots if path.stat().st_mtime >= started and path.stat().st_size > 1024), None)
    result.write_text(json.dumps({'success': shot is not None,
                                  'screenshot': str(shot or image)}, indent=2), encoding='utf-8')


handle = unreal.register_slate_post_tick_callback(tick)
