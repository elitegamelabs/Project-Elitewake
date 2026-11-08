"""Captures a named ship's bow (Part 8, 12) on one player's screen:
    Scripts/Verification/run_play_check_once.ps1 -Check capture_ship_names.py -Result ShipNamesCaptureResult.json -Players 1 -Standalone 1 -Kit 1
Names the ship nearest the survivor "Good Hope" and looks at her starboard and port bows from the water.
Saved/Screenshots/ShipNames/Starboard.png, Port.png. Visual review pending.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'ShipNames'
shots.mkdir(parents=True, exist_ok=True)
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
state = {'phase': 0, 'at': time.monotonic() + 6, 'handle': None}
report = {}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'ShipNamesCaptureResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ShipNamesCapture success={error is None} error={error}')


def look_at_bow(ship, side):
    """A camera a little off her bow on one side, at a sailor's eye height above the water, facing the name."""
    boards = [c for c in ship.get_components_by_class(unreal.TextRenderComponent) if c.get_name().startswith('NameBoard')]
    target = boards[0 if side > 0 else 1].get_world_location() if len(boards) == 2 else ship.get_actor_location()
    right, fwd = ship.get_actor_right_vector(), ship.get_actor_forward_vector()
    side_of = 1 if (target - ship.get_actor_location()).dot(right) > 0 else -1
    at = target + right * (side_of * 1300) - fwd * 400
    at = unreal.Vector(at.x, at.y, max(target.z, 0) + 250)
    camera = lib.spawn_verification_actor(world, unreal.CameraActor, at, unreal.MathLibrary.find_look_at_rotation(at, target))
    camera.get_editor_property('camera_component').set_editor_property('field_of_view', 70)
    pc.set_view_target_with_blend(camera, 0)
    report.setdefault('targets', []).append(str(target))


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            here = pawn.get_actor_location()
            ships = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip),
                           key=lambda s: (s.get_actor_location() - here).length())
            ship = ships[0]
            if ship.get_editor_property('bHeldByYard'):
                ship.release_from_yard(pc)
            report['refused'] = str(ship.rename_or_refuse(pawn, 'Good Hope'))
            report['name'] = ship.get_ship_name()
            state['ship'] = ship
            look_at_bow(ship, 1)
            state.update(phase=1, at=time.monotonic() + 2.5)
        elif p == 1:
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / "Starboard.png"}"')
            state.update(phase=2, at=time.monotonic() + 1)
        elif p == 2:
            look_at_bow(state['ship'], -1)
            state.update(phase=3, at=time.monotonic() + 2.5)
        elif p == 3:
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / "Port.png"}"')
            state.update(phase=4, at=time.monotonic() + 1.5)
        else:
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
