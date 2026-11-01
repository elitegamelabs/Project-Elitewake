"""Risk and recovery evidence captures (CLAUDE.md Phase 1, slice 4; section 9.4): pictures to review, not pass/fail.
Run through run_play_check.py on /Game/Elitewake/Maps/Lvl_CoastalPlayground with EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1920x1080,
EW_PLAY_STARTER_KIT=0, EW_PLAY_RESULT=RiskRecoveryCaptures.json. Writes Saved/Screenshots/RiskRecovery/*.png, 70-degree view.

  01 the boar pocket from the track's nearest point, eye height, late morning, no UI (what a survivor sees: is it readable?);
  02 a boar from 3 m, side on, late morning, no UI;
  03 the gameplay camera as a boar gores the survivor: the red damage number (HUD);
  04 / 05 the yarrow by the track from 3 m and from 20 m, late morning, no UI;
  06 the yarrow from 3 m at night, no UI;
  07 the gameplay camera with food sickness showing (HUD);
  08 a death bag from 3 m, late morning, no UI.
The capture sets the scenes up with the server's own calls (it is not the gameplay check: verify_risk_recovery_play is).
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import arrival_layout as A  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'RiskRecovery'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
stats = pawn.get_survival_component()
clock = unreal.EWDayNightSubsystem.get_for_world(world)
report = {'shots': [], 'notes': []}
cam = {}
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')


def shot(name, ui):
    unreal.SystemLibrary.execute_console_command(world, f'Shot {"showui " if ui else ""}filename="{shots / (name + ".png")}"')
    report['shots'].append(name + '.png')
    return 1.5


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 3000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else 0.0


def boar():
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal)
                if str(a.get_editor_property('definition').get_editor_property('display_name')) == 'Wild Boar' and not a.is_dead())


def herb():
    _, x, y, _ = A.HERBS[1]
    return next(h for h in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHandGatherable)
                if math.hypot(h.get_actor_location().x - x, h.get_actor_location().y - y) < 50)


def view(at, distance, bearing, height=170.0, lift=30.0):
    """The camera `distance` cm from `at` toward `bearing` degrees, at eye height above its own ground, looking at `at`."""
    r = math.radians(bearing)
    x, y = at.x + distance * math.cos(r), at.y + distance * math.sin(r)
    eye = unreal.Vector(x, y, ground(x, y) + height)
    look = unreal.MathLibrary.find_look_at_rotation(eye, at + unreal.Vector(0, 0, lift))
    pawn.teleport(unreal.Vector(x + 3000, y + 3000, ground(x + 3000, y + 3000) + 100), unreal.Rotator())   # out of the picture
    cam['a'].set_actor_location_and_rotation(eye, look, False, False)
    pc.set_view_target_with_blend(cam['a'], 0.0)
    return 3.0


def hour(h):
    clock.set_hour(h)
    report['notes'].append(f'hour {h}')
    return 4.0


def from_track():
    at = boar().get_home()
    nearest = min(A.smoothed_route(), key=lambda p: math.hypot(p[0] - at.x, p[1] - at.y))
    eye = unreal.Vector(nearest[0], nearest[1], ground(*nearest) + 170)
    pawn.teleport(unreal.Vector(nearest[0] - 3000, nearest[1] - 3000, ground(nearest[0] - 3000, nearest[1] - 3000) + 100), unreal.Rotator())
    look = unreal.MathLibrary.find_look_at_rotation(eye, at)
    cam['a'].set_actor_location_and_rotation(eye, unreal.Rotator(0, -2, look.yaw), False, False)
    pc.set_view_target_with_blend(cam['a'], 0.0)
    report['notes'].append(f'pocket {math.hypot(nearest[0] - at.x, nearest[1] - at.y) / 100:.0f} m from the track')
    return 3.0


def boar_side():
    b = boar()
    at = b.get_actor_location()
    yaw = b.get_actor_rotation().yaw + 90
    return view(at, 300, yaw, 120, 0)


def gored():
    b = boar()
    at = b.get_actor_location()
    pc.set_view_target_with_blend(pawn, 0.0)
    pawn.teleport(unreal.Vector(at.x + 380, at.y, ground(at.x + 380, at.y) + 100), unreal.Rotator(0, 0, 180))
    pc.set_control_rotation(unreal.Rotator(0, -8, 180))      # (roll, pitch, yaw)
    cam['hp'] = stats.get_health()
    return .5


def note_gore():
    report['notes'].append(f'health {stats.get_health():.0f} of {cam["hp"]:.0f} when shot')
    return .1


def sick():
    pc.set_view_target_with_blend(pawn, 0.0)
    _, x, y, _ = A.HERBS[1]
    pawn.teleport(unreal.Vector(x - 300, y, ground(x - 300, y) + 100), unreal.Rotator(0, 0, 0))
    pc.set_control_rotation(unreal.Rotator(0, -5, 0))
    stats.restore_health(100)
    stats.contract_food_sickness(180.0)
    return 2.0


def bag():
    stats.cure_food_sickness()
    _, x, y, _ = A.HERBS[0]
    pawn.teleport(unreal.Vector(x - 600, y, ground(x - 600, y) + 100), unreal.Rotator())
    pawn.get_inventory_component().add_item(wood, 7)
    stats.apply_damage(1000.0)
    return 5.0                                   # the fade to black, then Respawn is offered


def respawn():
    assert lib.send_verification_ui_key(pc, 'Enter')   # the bag drops as the survivor respawns
    return 2.0


def view_bag():
    bags = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWDeathBag)
    report['notes'].append(f'{len(bags)} bag(s)')
    return view(bags[0].get_actor_location(), 300, 200, 170, 10)


steps = [lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'), lambda: hour(10.5),
         lambda: cam.update(a=lib.spawn_verification_camera(pc, pawn.get_actor_location(), pawn.get_actor_rotation(), 70.0)),
         from_track, lambda: shot('01_boars_from_track_day', False),
         boar_side, lambda: shot('02_boar_3m_day', False),
         gored, lambda: 2.2, note_gore, lambda: shot('03_gored_gameplay', True),
         lambda: view(herb().get_actor_location(), 300, 200, 170, 35), lambda: shot('04_herbs_3m_day', False),
         lambda: view(herb().get_actor_location(), 2000, 200, 170, 35), lambda: shot('05_herbs_20m_day', False),
         lambda: hour(22.0), lambda: view(herb().get_actor_location(), 300, 200, 170, 35), lambda: shot('06_herbs_3m_night', False),
         lambda: hour(10.5), sick, lambda: shot('07_food_sickness_gameplay', True),
         bag, respawn, view_bag, lambda: shot('08_death_bag_3m_day', False),
         lambda: pc.set_view_target_with_blend(pawn, 0.0)]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    (saved / 'RiskRecoveryCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWRISKCAPTURE success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(steps):
            finish()
            return
        wait = steps[state['i']]()
        state['i'] += 1
        state['at'] = time.monotonic() + (wait if isinstance(wait, float) else .5)
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
