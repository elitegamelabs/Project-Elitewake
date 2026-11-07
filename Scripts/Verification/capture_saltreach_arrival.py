"""Reaching Saltreach evidence captures (CLAUDE.md Phase 1, slice 5; section 9.4): pictures to review, not pass/fail.
Run through run_play_check.py on /Game/Elitewake/Maps/Lvl_CoastalPlayground with EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1920x1080,
EW_PLAY_STARTER_KIT=0, EW_PLAY_RESULT=SaltreachArrivalCaptures.json. Writes Saved/Screenshots/SaltreachArrival/*.png, 70-degree view.

  01 the gameplay camera at the track's end, late morning: the town ahead, the sell prompt and the compass mark (HUD);
  02 Oskar Brann's window greeting an empty purse (HUD);
  03 / 04 the strongbox from 3 m and from 25 m with the warehouse behind it, late morning, no UI;
  05 the strongbox open beside the pack (HUD);
  06 the strongbox from 3 m at night, no UI;
  07 the gameplay camera with the shipyard prompt and the compass mark on Elias Thorne (HUD);
  08 the gameplay camera with the Company prompt (HUD).
The capture sets the scenes up with the server's own calls (it is not the gameplay check: verify_saltreach_arrival_play is).
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
shots = saved / 'Screenshots' / 'SaltreachArrival'
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
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
meat = unreal.load_asset('/Game/Elitewake/Items/Food/DA_RawMeat')
hatchet = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenAxe')


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


def strongbox():
    return unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWStrongbox)[0]


def stand(x, y, look_at, z=None):
    """The survivor (gameplay camera) at (x, y), looking at look_at."""
    pc.set_view_target_with_blend(pawn, 0.0)
    pawn.set_actor_location(unreal.Vector(x, y, (ground(x, y) if z is None else z) + 100), False, True)   # a teleport is refused beside a stall
    pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    eye = pawn.get_actor_eyes_view_point()[0]
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, look_at))
    return 4.5                                    # entering the town gives the first view 3 s without a prompt


def view(at, distance, bearing, height=170.0, lift=30.0, base=None):
    """The camera `distance` cm from `at` toward `bearing` degrees, `height` above `base` (else its own ground), looking at `at`.
    In the town the street is level: `base` is the street under the thing looked at, so a roof or awning is never taken for ground."""
    r = math.radians(bearing)
    x, y = at.x + distance * math.cos(r), at.y + distance * math.sin(r)
    eye = unreal.Vector(x, y, (ground(x, y) if base is None else base) + height)
    look = unreal.MathLibrary.find_look_at_rotation(eye, at + unreal.Vector(0, 0, lift))
    cam['a'].set_actor_location_and_rotation(eye, look, False, False)
    pc.set_view_target_with_blend(cam['a'], 0.0)
    return 3.0


def hour(h):
    clock.set_hour(h)
    report['notes'].append(f'hour {h}')
    return 4.0


def setup():
    arrival.set_step_index(99)
    arrival.set_town_steps_done(0)
    pawn.get_wallet_component().set_copper(0)
    pack = pawn.get_inventory_component()
    pack.add_item(wood, 10)
    pack.add_item(meat, 3)
    pack.add_item(hatchet, 1)
    return .5


def track_end():
    end = A.smoothed_route()[-1]
    oskar = person('Oskar Brann').get_actor_location()
    return stand(end[0], end[1], unreal.Vector(oskar.x, oskar.y, ground(end[0], end[1]) + 160))


def talk_to_oskar():
    o = person('Oskar Brann')
    at, ahead = o.get_actor_location(), o.get_actor_forward_vector()
    stand(at.x + ahead.x * 200, at.y + ahead.y * 200, unreal.Vector(at.x, at.y, at.z + 60), z=at.z - 90)
    return 1.0


def press_e():
    assert lib.send_verification_gameplay_key(pc, 'E')
    return 1.5


def sell_and_close():
    o = person('Oskar Brann')
    assert lib.send_verification_dialogue_choice(pc, o, 'SellAll')
    report['notes'].append('sold')
    return 1.0


def escape():
    # Only into an open window: with none open, Escape reaches the editor and ends Play.
    shown = [w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWContainerWidget, False) if w.is_in_viewport()]
    if pc.is_dialogue_open() or pc.is_inventory_open() or shown:
        lib.send_verification_ui_key(pc, 'Escape')
    return 1.0


def at_strongbox():
    b = strongbox()
    at, ahead = b.get_actor_location(), b.get_actor_forward_vector()
    stand(at.x + ahead.x * 170, at.y + ahead.y * 170, at + unreal.Vector(0, 0, 30), z=at.z)
    return 1.0


def box_front(distance, height=170.0):
    b = strongbox()
    at = b.get_actor_location()
    return view(at, distance, b.get_actor_rotation().yaw + 25, height, 30 if distance < 1000 else 150, base=at.z)


def behind_talk():
    """Over the survivor's shoulder at Oskar's stall, so his window is shown over the market, not the stall's planks."""
    o = person('Oskar Brann')
    at = o.get_actor_location()
    return view(at, 520, o.get_actor_rotation().yaw + 15, 120, 40, base=at.z - 90)


def store_hatchet():
    lib.send_verification_ui_key(pc, 'Gamepad_FaceButton_Bottom')
    return 1.0


def to_yard_prompt():
    """Six metres out from the strongbox toward the square, on the street, turned to the shipyard."""
    box = strongbox()
    b, ahead = box.get_actor_location(), box.get_actor_forward_vector()
    elias = person('Elias Thorne').get_actor_location()
    return stand(b.x + ahead.x * 600, b.y + ahead.y * 600, unreal.Vector(elias.x, elias.y, elias.z + 80), z=b.z)


def to_company_prompt():
    arrival.set_town_steps_done(0b0111)          # selling, storing and the shipyard done
    return 3.0


steps = [lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'), lambda: hour(10.5),
         lambda: cam.update(a=lib.spawn_verification_camera(pc, pawn.get_actor_location(), pawn.get_actor_rotation(), 70.0)),
         setup, track_end, lambda: shot('01_track_end_sell_prompt', True),
         talk_to_oskar, press_e, behind_talk, lambda: shot('02_oskar_empty_purse', True), sell_and_close, escape,
         lambda: box_front(300), lambda: shot('03_strongbox_3m_day', False),
         lambda: box_front(2500), lambda: shot('04_strongbox_25m_day', False),
         at_strongbox, press_e, store_hatchet, lambda: box_front(450, 190), lambda: shot('05_strongbox_open', True), escape,
         to_yard_prompt, lambda: hour(22.0), lambda: box_front(300), lambda: shot('06_strongbox_3m_night', False), lambda: hour(10.5),
         to_yard_prompt, lambda: shot('07_shipyard_prompt', True),
         to_company_prompt, lambda: shot('08_company_prompt', True),
         lambda: pc.set_view_target_with_blend(pawn, 0.0)]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error, town_steps=arrival.get_town_steps_done(),
                  copper=pawn.get_wallet_component().get_copper(), stored=pc.get_strongbox().get_item_count(hatchet))
    (saved / 'SaltreachArrivalCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWSALTREACHCAPTURE success={error is None} error={error}')


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
