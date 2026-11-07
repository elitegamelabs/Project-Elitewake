"""First-resources evidence captures (CLAUDE.md Phase 1, slice 2; section 9.4): pictures to review, not pass/fail.
Run through run_play_check.py on /Game/Elitewake/Maps/Lvl_CoastalPlayground with EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1920x1080,
EW_PLAY_STARTER_KIT=0, EW_PLAY_RESULT=FirstResourcesCaptures.json. Late morning (10.5). Writes Saved/Screenshots/FirstResources/*.png.

  01-04 sticks, fibre, stones and berries from 20 m, eye height, 70 degrees, no UI;
  05-08 the same from 3 m, looking down at them, no UI;
  09 the gameplay camera at the stone pile with its prompt (HUD);
  10 the Stone Hatchet in hand, close, from the side, no UI;
  11 the gameplay camera mid-swing at an arrival oak (HUD).
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import arrival_layout as A  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'FirstResources'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
report = {'shots': [], 'notes': []}
cam = {}
hatchet = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenAxe')


def shot(name, ui):
    unreal.SystemLibrary.execute_console_command(world, f'Shot {"showui " if ui else ""}filename="{shots / (name + ".png")}"')
    report['shots'].append(name + '.png')
    return 1.5


def node(label):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHandGatherable) if str(a.get_actor_label()) == label)


def view_of(label, distance, pitch_to_target=True):
    """A 70-degree eye-height camera `distance` from the pile, on the spawn's side, looking at it."""
    origin, extent = node(label).get_actor_bounds(False)
    away = unreal.Vector(A.SPAWN[0] - origin.x, A.SPAWN[1] - origin.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = unreal.Vector(origin.x, origin.y, 0) + away * distance
    eye = unreal.Vector(spot.x, spot.y, T.height(spot.x, spot.y) + 170)
    look = unreal.MathLibrary.find_look_at_rotation(eye, origin)
    pawn.teleport(unreal.Vector(spot.x + away.x * 600, spot.y + away.y * 600, T.height(spot.x, spot.y) + 150), unreal.Rotator())
    cam['a'].set_actor_location_and_rotation(eye, unreal.Rotator(0, look.pitch if pitch_to_target else -2, look.yaw), False, False)
    pc.set_view_target_with_blend(cam['a'], 0.0)
    return 4.0


def gameplay_at(label, distance=150.0):
    origin, extent = node(label).get_actor_bounds(False)
    away = unreal.Vector(A.SPAWN[0] - origin.x, A.SPAWN[1] - origin.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = unreal.Vector(origin.x, origin.y, node(label).get_actor_location().z) + away * distance + unreal.Vector(0, 0, 100)
    pc.set_view_target_with_blend(pawn, 0.0)
    pawn.teleport(spot, unreal.Rotator())
    cam['aim'] = origin + unreal.Vector(0, 0, extent.z * .5)
    return 1.0


def aim():
    eye = pawn.get_actor_eyes_view_point()[0]
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, cam['aim']))
    return 2.0


def give_hatchet():
    pawn.get_inventory_component().add_item(hatchet, 1)     # capture setup only: the craft itself is verify_first_resources_play
    assert lib.send_verification_equipment_request(pc, hatchet, unreal.EWEquipmentSlot.MAIN_HAND)
    return 2.0


def hand_closeup():
    hand = pawn.get_component_by_class(unreal.SkeletalMeshComponent).get_socket_location('hand_r')
    # In front of the survivor and off to their right, looking back at the right hand and the head above it.
    yaw = math.radians(pawn.get_actor_rotation().yaw)
    fx, fy, rx, ry = math.cos(yaw), math.sin(yaw), -math.sin(yaw), math.cos(yaw)
    eye = unreal.Vector(hand.x + 80 * fx + 45 * rx, hand.y + 80 * fy + 45 * ry, hand.z + 15)
    cam['a'].set_actor_location_and_rotation(eye, unreal.MathLibrary.find_look_at_rotation(eye, hand + unreal.Vector(0, 0, 25)), False, False)
    pc.set_view_target_with_blend(cam['a'], 0.0)
    return 2.0


def to_oak():
    oak = next(t for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHarvestTree) if str(t.get_actor_label()) == 'Arrival oak 3')
    base = oak.get_actor_location()
    away = unreal.Vector(A.SPAWN[0] - base.x, A.SPAWN[1] - base.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = base + away * 140 + unreal.Vector(0, 0, 110)
    pc.set_view_target_with_blend(pawn, 0.0)
    pawn.teleport(spot, unreal.Rotator())
    cam['aim'] = base + unreal.Vector(0, 0, 120)
    return 1.0


def swing():
    lib.send_verification_gameplay_key(pc, 'LeftMouseButton')
    return .35


steps = [lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'),
         lambda: unreal.EWDayNightSubsystem.get_for_world(world).set_hour(10.5) or 4.0,
         lambda: cam.update(a=lib.spawn_verification_camera(pc, pawn.get_actor_location(), pawn.get_actor_rotation(), 70.0))]
for n, label in enumerate(('Arrival sticks 2', 'Arrival fiber 2', 'Arrival stones 2', 'Arrival berries 1')):
    kind = label.split()[1]
    steps += [lambda l=label: view_of(l, 2000, False), lambda n=n, k=kind: shot(f'{n + 1:02d}_{k}_20m_day', False)]
for n, label in enumerate(('Arrival sticks 2', 'Arrival fiber 2', 'Arrival stones 2', 'Arrival berries 1')):
    kind = label.split()[1]
    steps += [lambda l=label: view_of(l, 300), lambda n=n, k=kind: shot(f'{n + 5:02d}_{k}_3m_day', False)]
steps += [lambda: gameplay_at('Arrival stones 2'), aim, lambda: shot('09_stones_gameplay_prompt', True),
          give_hatchet, hand_closeup, lambda: shot('10_stone_hatchet_in_hand', False),
          to_oak, aim, swing, lambda: shot('11_hatchet_strike_gameplay', True),
          lambda: pc.set_view_target_with_blend(pawn, 0.0)]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    (saved / 'FirstResourcesCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWFIRSTRESOURCESCAPTURE success={error is None} error={error}')


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
