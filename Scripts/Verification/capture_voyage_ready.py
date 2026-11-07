"""Making the first voyage ready, evidence captures (CLAUDE.md Phase 1, slice 6; section 9.4): pictures to review, not pass/fail.
Run through run_play_check.py on /Game/Elitewake/Maps/Lvl_CoastalPlayground with EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1920x1080,
EW_PLAY_STARTER_KIT=0, EW_PLAY_YARD_SHIPS=held, EW_PLAY_RESULT=VoyageReadyCaptures.json. Writes Saved/Screenshots/VoyageReady/*.png,
70-degree view.

  01 the gameplay camera in the square: the boat prompt and the compass mark on Elias Thorne (HUD);
  02 Elias's window: the raft for 60, the yard's sloop for 2500 where she lies (HUD);
  03 the bought raft afloat at the foot of the slipway from 25 m, late morning, no UI;
  04 the gameplay camera at the town well with an empty waterskin in hand: "Fill the waterskin" (HUD);
  05 the raft's hold open, loaded with food, the full waterskin and wood (HUD);
  06 the gameplay camera on the raft, turned to sea: the voyage prompt and the compass mark on the Swamp island (HUD);
  07 the yard's sloop at the east dock from 20 m, late morning, no UI;
  08 the gameplay camera at her ladder: whose she is (HUD).
The capture sets the scenes up with the server's own calls (it is not the gameplay check: verify_voyage_ready_play is).
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'VoyageReady'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
arrival = pawn.get_arrival_component()
clock = unreal.EWDayNightSubsystem.get_for_world(world)
report = {'shots': [], 'notes': []}
cam = {}
ITEMS = '/Game/Elitewake/Items'
item = {'Wood': unreal.load_asset(f'{ITEMS}/Testing/DA_TestWood'), 'Meat': unreal.load_asset(f'{ITEMS}/Food/DA_CookedMeat'),
        'Skin': unreal.load_asset(f'{ITEMS}/Testing/DA_TestHideWaterFlask'), 'Full': unreal.load_asset(f'{ITEMS}/Testing/DA_TestWaterskinFull')}
RAFT = unreal.load_asset('/Game/Elitewake/Ships/DA_Ship_Raft')
SLOOP = unreal.load_asset('/Game/Elitewake/Ships/DA_Ship_Sloop')
HAND = unreal.EWEquipmentSlot.MAIN_HAND
port = W.PORTS['Plains']


def shot(name, ui):
    unreal.SystemLibrary.execute_console_command(world, f'Shot {"showui " if ui else ""}filename="{shots / (name + ".png")}"')
    report['shots'].append(name + '.png')
    return 1.5


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 4000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else 0.0


def person(name):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWTownsfolk) if str(a.get_editor_property('npc_name')) == name)


def ship(definition):
    found = [s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip) if s.get_editor_property('definition') == definition]
    return found[0] if found else None


def stand(x, y, look_at, z=None, wait=4.5):
    pc.set_view_target_with_blend(pawn, 0.0)
    pawn.set_actor_location(unreal.Vector(x, y, (ground(x, y) if z is None else z) + 100), False, True)
    pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    eye = pawn.get_actor_eyes_view_point()[0]
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, look_at))
    return wait


def view(at, distance, bearing, height=170.0, lift=30.0, base=None):
    r = math.radians(bearing)
    x, y = at.x + distance * math.cos(r), at.y + distance * math.sin(r)
    eye = unreal.Vector(x, y, (ground(x, y) if base is None else base) + height)
    cam['a'].set_actor_location_and_rotation(eye, unreal.MathLibrary.find_look_at_rotation(eye, at + unreal.Vector(0, 0, lift)), False, False)
    pc.set_view_target_with_blend(cam['a'], 0.0)
    return 3.0


def hour(h):
    clock.set_hour(h)
    report['notes'].append(f'hour {h}')
    return 4.0


def escape():
    shown = [w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWContainerWidget, False) if w.is_in_viewport()]
    if pc.is_dialogue_open() or pc.is_inventory_open() or shown:
        lib.send_verification_ui_key(pc, 'Escape')
    return 1.0


def setup():
    arrival.set_step_index(99)
    arrival.set_town_steps_done(0b1111)
    pawn.get_wallet_component().set_copper(75)
    pack = pawn.get_inventory_component()
    pack.add_item(item['Wood'], 20)
    pack.add_item(item['Meat'], 2)
    return .5


def square():
    x, y = port.world(-600, -200)
    e = person('Elias Thorne').get_actor_location()
    return stand(x, y, unreal.Vector(e.x, e.y, e.z + 80))


def talk_to_elias():
    e = person('Elias Thorne')
    at, ahead = e.get_actor_location(), e.get_actor_forward_vector()
    stand(at.x + ahead.x * 200, at.y + ahead.y * 200, unreal.Vector(at.x, at.y, at.z + 60), z=at.z - 90, wait=1.0)
    assert lib.send_verification_gameplay_key(pc, 'E')
    return 1.5


def over_elias():
    e = person('Elias Thorne')
    at = e.get_actor_location()
    return view(at, 520, e.get_actor_rotation().yaw + 15, 120, 40, base=at.z - 90)


def buy_raft():
    assert lib.send_verification_dialogue_choice(pc, person('Elias Thorne'), 'Ship0')
    report['notes'].append(str(pc.get_last_dialogue_reply()))
    return 2.0


def raft_view():
    r = ship(RAFT)
    at = r.get_actor_location()
    return view(at, 2500, r.get_actor_rotation().yaw + 120, 400, 0, base=at.z)


def at_well():
    pawn.get_inventory_component().add_item(item['Skin'], 1)
    pawn.get_equipment_component().equip_item(item['Skin'], HAND)
    x, y = port.world(-600 + 150, -900)
    wx, wy = port.world(-600, -900)
    return stand(x, y, unreal.Vector(wx, wy, ground(x, y) + 70), wait=2.0)


def fill():
    assert lib.send_verification_gameplay_key(pc, 'E')
    return 1.5


def stow_skin():
    pawn.get_equipment_component().unequip_item(HAND)
    return .5


def open_hold():
    r = ship(RAFT)
    at = r.get_actor_location()
    stand(at.x, at.y, r.get_cargo_hatch_world(), z=at.z, wait=1.0)
    assert lib.send_verification_interaction_request(pc, r)
    return 1.5


def load_all():
    for _ in range(3):
        lib.send_verification_ui_key(pc, 'Gamepad_FaceButton_Bottom')
    return 1.5


def to_sea():
    r = ship(RAFT)
    at = r.get_actor_location()
    swamp = W.PORTS['Swamp']
    return stand(at.x, at.y, unreal.Vector(swamp.cx, swamp.cy, at.z + 100), z=at.z, wait=3.0)


def sloop_view():
    s = ship(SLOOP)
    at = s.get_actor_location()
    return view(at, 2000, s.get_actor_rotation().yaw + 70, 300, 200, base=at.z)


def at_ladder():
    s = ship(SLOOP)
    # The boarding ladder is centred at the stern (CLAUDE.md 7.1): swim just off it, looking up at its rungs (as
    # verify_first_voyage_play does before taking hold).
    ladder, out = s.get_boarding_point_world(0), s.get_actor_forward_vector() * -1.0
    return stand(ladder.x + out.x * 160, ladder.y + out.y * 160, ladder + unreal.Vector(0, 0, 60),
                 z=s.get_actor_location().z - 60, wait=3.0)


steps = [lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'), lambda: hour(10.5),
         lambda: cam.update(a=lib.spawn_verification_camera(pc, pawn.get_actor_location(), pawn.get_actor_rotation(), 70.0)),
         setup, square, lambda: shot('01_boat_prompt', True),
         talk_to_elias, over_elias, lambda: shot('02_elias_sells_the_raft', True), buy_raft, escape,
         raft_view, lambda: shot('03_raft_at_slipway_25m', False),
         at_well, lambda: shot('04_well_fill_waterskin', True), fill, stow_skin,
         open_hold, load_all, lambda: shot('05_raft_hold_loaded', True), escape,
         to_sea, lambda: shot('06_voyage_prompt', True),
         sloop_view, lambda: shot('07_yard_sloop_20m', False),
         at_ladder, lambda: shot('08_yard_sloop_ladder', True),
         lambda: pc.set_view_target_with_blend(pawn, 0.0)]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    r = ship(RAFT)
    report.update(success=error is None, error=error, town_steps=arrival.get_town_steps_done(),
                  copper=pawn.get_wallet_component().get_copper(), raft=bool(r),
                  hold={n: r.get_cargo().get_item_count(i) for n, i in item.items()} if r else None)
    (saved / 'VoyageReadyCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWVOYAGECAPTURE success={error is None} error={error}')


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
