"""Campfire evidence captures (CLAUDE.md Phase 1, slice 3; section 9.4): pictures to review, not pass/fail.
Run through run_play_check.py on /Game/Elitewake/Maps/Lvl_CoastalPlayground with EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1920x1080,
EW_PLAY_STARTER_KIT=0, EW_PLAY_RESULT=CampfireCaptures.json. Writes Saved/Screenshots/Campfire/*.png.

  01 gameplay camera holding the campfire: its blue ghost on open grass (HUD);
  02 the same aimed beside a laid fire: the red ghost (HUD);
  03 / 04 the lit fire from 3 m, late morning / night, no UI;
  05 / 06 the lit fire from 20 m, late morning / night (the night's warm focal point), no UI;
  07 the menu by the fire with the berry dish ready (HUD);
  08 the cold ring after it burns down, 3 m, late morning, no UI.
The capture sets the scene up with the server's own calls (it is not the gameplay check: verify_campfire_play is).
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
shots = saved / 'Screenshots' / 'Campfire'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
clock = unreal.EWDayNightSubsystem.get_for_world(world)
report = {'shots': [], 'notes': []}
cam = {}
I = '/Game/Elitewake/Items/'
campfire = unreal.load_asset(I + 'Building/DA_Campfire')
berry = unreal.load_asset(I + 'Testing/DA_TestAzulBerry')
dish = unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipeCookedBerryDish')
STAND = (A.SPAWN[0] + 276.0 * 3, A.SPAWN[1] + 961.0 * 3)
FACING = 74.0


def shot(name, ui):
    unreal.SystemLibrary.execute_console_command(world, f'Shot {"showui " if ui else ""}filename="{shots / (name + ".png")}"')
    report['shots'].append(name + '.png')
    return 1.5


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 3000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4] if hit else unreal.Vector(x, y, 0)


def fire():
    found = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWCampfire)
    return found[0] if found else None


def stand_and_aim(ahead=250.0, side=0.0):
    pc.set_view_target_with_blend(pawn, 0.0)
    g = ground(*STAND)
    pawn.teleport(unreal.Vector(STAND[0], STAND[1], g.z + 100), unreal.Rotator(0, 0, FACING))
    r, s = math.radians(FACING), math.radians(FACING + 90)
    cam['aim'] = ground(STAND[0] + ahead * math.cos(r) + side * math.cos(s), STAND[1] + ahead * math.sin(r) + side * math.sin(s))
    return 1.0


def aim():
    eye = pawn.get_actor_eyes_view_point()[0]
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, cam['aim']))
    return 2.0


def hold_campfire():
    pawn.get_inventory_component().add_item(campfire, 2)
    assert lib.send_verification_equipment_request(pc, campfire, unreal.EWEquipmentSlot.MAIN_HAND)
    return 1.5


def lay():
    lib.send_verification_gameplay_key(pc, 'LeftMouseButton')
    return 2.0


def view_fire(distance, pitch_down=True):
    at = fire().get_actor_location()
    r = math.radians(FACING + 180 + 25)
    spot = unreal.Vector(at.x + distance * math.cos(r), at.y + distance * math.sin(r), 0)
    eye = unreal.Vector(spot.x, spot.y, ground(spot.x, spot.y).z + 170)
    look = unreal.MathLibrary.find_look_at_rotation(eye, at + unreal.Vector(0, 0, 30))
    pawn.teleport(unreal.Vector(spot.x - 500 * math.cos(r), spot.y - 500 * math.sin(r), eye.z), unreal.Rotator())
    cam['a'].set_actor_location_and_rotation(eye, unreal.Rotator(0, look.pitch if pitch_down else -2, look.yaw), False, False)
    pc.set_view_target_with_blend(cam['a'], 0.0)
    return 3.0


def hour(h):
    clock.set_hour(h)
    report['notes'].append(f'hour {h}')
    return 4.0


def menu_by_fire():
    at = fire().get_actor_location()
    pc.set_view_target_with_blend(pawn, 0.0)
    pawn.teleport(unreal.Vector(at.x - 150, at.y, at.z + 100), unreal.Rotator(0, 0, 0))
    pawn.get_inventory_component().add_item(berry, 3)
    pc.set_inventory_open(True)
    menu = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWInventoryWidget, False) if w.is_in_viewport())
    menu.focus_crafting()
    for _ in range(6):
        if menu.get_shown_recipe() == dish:
            break
        lib.send_verification_ui_key(pc, 'Right')
    report['notes'].append(f'dish shown: {menu.get_shown_recipe() == dish}, ready: {menu.is_craft_action_enabled()}')
    return 1.5


steps = [lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'), lambda: hour(10.5),
         lambda: cam.update(a=lib.spawn_verification_camera(pc, pawn.get_actor_location(), pawn.get_actor_rotation(), 70.0)),
         hold_campfire, stand_and_aim, aim, lambda: shot('01_ghost_blue_gameplay', True), lay,
         lambda: stand_and_aim(330.0, 60.0), aim, lambda: shot('02_ghost_red_gameplay', True),
         lambda: view_fire(300), lambda: shot('03_fire_3m_day', False),
         lambda: hour(22.0), lambda: shot('04_fire_3m_night', False),
         lambda: view_fire(2000, False), lambda: shot('06_fire_20m_night', False),
         lambda: hour(10.5), lambda: shot('05_fire_20m_day', False),
         menu_by_fire, lambda: shot('07_cooking_menu_by_fire', True), lambda: pc.set_inventory_open(False),
         lambda: fire().set_fuel(0.0), lambda: view_fire(300), lambda: shot('08_cold_ring_3m_day', False),
         lambda: pc.set_view_target_with_blend(pawn, 0.0)]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    (saved / 'CampfireCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWCAMPFIRECAPTURE success={error is None} error={error}')


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
