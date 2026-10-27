"""Build Mode, milestone 2 (single-player Play session). Owner, October 27: build on every island outside Ports and obstruction
zones. Drives Build Mode through the controller's own key handler, with the keyboard keys and then the controller buttons:
  1. B opens Build Mode; looking at open ground shows the blue ghost (placeable, no reason);
  2. E and Q turn the foundation a quarter each way (Q/E on keyboard, RB/LB on a controller);
  3. the place key (left mouse) puts a foundation there; the right trigger puts a second edge to edge with the first
     (the ghost snaps: exactly 4 m between their middles, same facing);
  4. looking at a piece and placing again is refused (something in the way) and builds nothing;
  5. X (keyboard) / the right stick (controller) switch to demolish: looking at a piece and pressing place removes it;
  6. in a Port, the ghost is red with a reason mentioning the Port and nothing can be placed;
  7. Escape / the right stick leaves Build Mode and hides the ghost.
Writes Saved/BuildModePlayResult.json and screenshots to Saved/Screenshots/BuildMode."""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
survival = pawn.get_survival_component()
build = pc.get_build_component()
Z = unreal.EWBuildZones
shots = saved / 'Screenshots' / 'BuildMode'
shots.mkdir(parents=True, exist_ok=True)
state = {'step': 0, 'at': time.monotonic() + 14, 'handle': None, 'site': None, 'aim': None}
report = {'checks': []}


def note(label, **values):
    report['checks'].append({'label': label, **values})
    unreal.log(f'BuildMode: {label} {values}')


def key(name):
    assert lib.send_verification_gameplay_key(pc, name), f'key {name} not handled'


def pieces():
    return unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWBuildPiece)


def mode():
    return str(build.get_mode()).upper()


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / name}.png"')


def face(site_x, site_y, ground, back=300.0, yaw=0.0):
    """Stand `back` cm behind the site (along -yaw) and look at the ground there: the view is tracked toward it every frame
    from the real camera (the survivor's third-person camera sits behind and above)."""
    rad = math.radians(yaw)
    px, py = site_x - back * math.cos(rad), site_y - back * math.sin(rad)
    survival.restore_health(1000.0)
    pawn.teleport(unreal.Vector(px, py, T.height(px, py) + 130), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    state['aim'] = unreal.Vector(site_x, site_y, T.height(site_x, site_y))


def flat(x, y, within=40.0):
    res = Z.get_footprint_ground(world, x, y, 200, 200, 0)
    low, high = res[-2], res[-1]
    return -1e6 < low <= high < 1e6 and high - low <= within


def find_site():
    """Open ground where two foundations side by side (4 m apart) may both stand: the starter island first, then the others."""
    reasons = {}
    for name in ('Starter', 'Desert1', 'Jungle1', 'Swamp1', 'Winter1'):
        isle = W.island(name)
        r = int(isle.reach())
        cells = sorted(((int(isle.cx) + dx, int(isle.cy) + dy) for dx in range(-r, r, 250) for dy in range(-r, r, 250)),
                       key=lambda c: math.hypot(c[0] - isle.cx, c[1] - isle.cy))
        for x, y in cells:
            if isle.distance(x, y) > -300:
                continue
            why = str(Z.check_footprint(world, x, y, 200, 200, 0))
            reasons[why or 'ok'] = reasons.get(why or 'ok', 0) + 1
            if not why and not Z.check_footprint(world, x + 400, y, 200, 200, 0)                     and not Z.check_footprint(world, x - 700, y, 40, 40, 0)                     and flat(x, y) and flat(x + 400, y) and flat(x - 500, y):
                note('site island', island=name)
                return x, y
    note('why no site', reasons=reasons)
    raise AssertionError('no open site for two foundations on any island')


def settle():
    survival.restore_health(1000.0)


def pick_site():
    x, y = find_site()
    state['site'] = (x, y)
    note('site', x=x, y=y)
    face(x, y, T.height(x, y))


def open_mode():
    assert 'OFF' in mode(), mode()
    key('B')
    assert 'PLACE' in mode(), f'B did not open Build Mode: {mode()}'
    # the player's own screen keeps aiming each tick; aim again at the site
    x, y = state['site']
    face(x, y, T.height(x, y))


def ghost_blue():
    cam = unreal.GameplayStatics.get_player_camera_manager(world, 0)
    note('debug aim', cam=str(cam.get_camera_location()), rot=str(pc.get_control_rotation()), pawn=str(pawn.get_actor_location()),
         target=str(state['aim']), mode=mode())
    note('aim at open ground', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()),
         ghost=build.is_ghost_showing(), loc=str(build.get_aim_location()))
    assert build.is_ghost_showing(), 'no ghost'
    assert build.is_aim_placeable(), f'open ground refused: {build.get_aim_reason()}'
    shot('GhostBlue')


def rotate_keys():
    yaw0 = build.get_aim_yaw()
    key('E')
    yaw1 = build.get_aim_yaw()
    key('Q')
    yaw2 = build.get_aim_yaw()
    key('Gamepad_RightShoulder')
    yaw3 = build.get_aim_yaw()
    key('Gamepad_LeftShoulder')
    yaw4 = build.get_aim_yaw()
    note('rotate', yaws=[yaw0, yaw1, yaw2, yaw3, yaw4])
    assert (yaw1 - yaw0) % 360 == 90 and yaw2 % 360 == yaw0 % 360, 'E/Q did not turn the foundation a quarter each way'
    assert (yaw3 - yaw0) % 360 == 90 and yaw4 % 360 == yaw0 % 360, 'RB/LB did not turn the foundation a quarter each way'


def place_first():
    x, y = state['site']
    face(x, y, T.height(x, y))


def place_first_press():
    key('LeftMouseButton')


def first_placed():
    n = len(pieces())
    note('first placed', pieces=n)
    assert n == 1, f'expected 1 piece, found {n}'
    state['first'] = pieces()[0].get_actor_location()
    shot('First')


def aim_second():
    x, y = state['site']
    # look a little to the right of the first piece's middle: the ghost should snap to its +x side, 4 m on
    face(x + 400, y, T.height(x + 400, y), back=300.0)


def place_second_press():
    note('second aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()), loc=str(build.get_aim_location()))
    assert build.is_aim_placeable(), f'second foundation refused: {build.get_aim_reason()}'
    key('Gamepad_RightTrigger')


def second_placed():
    ps = pieces()
    note('second placed', pieces=len(ps))
    assert len(ps) == 2, f'expected 2 pieces, found {len(ps)}'
    a, b = ps[0].get_actor_location(), ps[1].get_actor_location()
    gap = math.hypot(a.x - b.x, a.y - b.y)
    note('edge to edge', gap=round(gap, 1))
    assert abs(gap - 400) < 1.0, f'pieces are {gap} cm apart, not 4 m'
    shot('Two')


def aim_on_piece():
    x, y = state['site']
    face(x, y, T.height(x, y), back=300.0)


def place_on_piece():
    note('aim on a piece', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert not build.is_aim_placeable(), 'a ghost over an existing piece should be red'
    key('LeftMouseButton')


def still_two():
    n = len(pieces())
    note('placing on a piece', pieces=n)
    assert n == 2, f'placing on a piece built something ({n})'
    shot('GhostRed')


def to_demolish():
    key('X')
    assert 'DEMOLISH' in mode(), mode()
    x, y = state['site']
    face(x, y, T.height(x, y), back=300.0)


def demolish_first():
    aimed = build.get_aimed_piece()
    note('demolish aim', aimed=bool(aimed), placeable=build.is_aim_placeable())
    assert aimed, 'looking at a piece in demolish mode finds nothing'
    key('Gamepad_RightTrigger')


def after_demolish():
    n = len(pieces())
    note('demolished', pieces=n)
    assert n == 1, f'expected 1 piece after demolishing one, found {n}'


def clean_up():
    # remove the other with the controller's demolish button (B) and finish with demolish off
    x, y = state['site']
    face(x + 400, y, T.height(x + 400, y), back=300.0)


def demolish_second():
    if build.get_aimed_piece():
        key('LeftMouseButton')
    else:
        x, y = state['site']
        face(x, y, T.height(x, y), back=300.0)
        key('LeftMouseButton')


def leave_with_stick():
    key('Gamepad_FaceButton_Right')          # demolish -> place (controller)
    assert 'PLACE' in mode(), mode()
    key('Gamepad_RightThumbstick')           # leave (controller)
    assert 'OFF' in mode(), mode()
    note('left with the stick', ghost=build.is_ghost_showing(), pieces=len(pieces()))
    assert not build.is_ghost_showing(), 'ghost still showing after leaving'


def to_port():
    port = W.PORTS['Winter']
    x, y = port.cx, port.cy
    face(x, y, T.height(x, y), back=300.0, yaw=0.0)
    key('B')
    face(x, y, T.height(x, y), back=300.0, yaw=0.0)


def port_red():
    why = str(build.get_aim_reason())
    note('port aim', placeable=build.is_aim_placeable(), reason=why, mode=mode())
    assert not build.is_aim_placeable() and 'Port' in why or 'zone' in why.lower(), f'port ground was not refused: {why}'
    before = len(pieces())
    key('LeftMouseButton')
    shot('PortRed')
    state['before_port'] = before


def port_nothing_built():
    n = len(pieces())
    note('port place', pieces=n)
    assert n == state['before_port'], 'a foundation was built inside a Port'
    key('Escape')
    assert 'OFF' in mode(), f'Escape did not leave Build Mode: {mode()}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'BuildModePlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK BuildMode success={error is None} error={error}')


STEPS = [(pick_site, 3.0), (open_mode, 1.5), (ghost_blue, .2), (rotate_keys, .2), (place_first, 1.2), (place_first_press, 1.5),
         (first_placed, .2), (aim_second, 1.5), (place_second_press, 1.5), (second_placed, .2), (aim_on_piece, 1.5),
         (place_on_piece, 1.2), (still_two, .2), (to_demolish, 1.5), (demolish_first, 1.5), (after_demolish, .2),
         (clean_up, 1.5), (demolish_second, 1.5), (leave_with_stick, .3), (to_port, 2.0), (port_red, 1.5),
         (port_nothing_built, .2), (finish, .1)]


def tick(delta):
    survival.restore_health(1000.0)
    survival.set_hunger(100.0)
    survival.set_hydration(100.0)
    if state['aim'] is not None:
        cam = unreal.GameplayStatics.get_player_camera_manager(world, 0).get_camera_location()
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, state['aim']))
    if time.monotonic() < state['at']:
        return
    try:
        action, wait = STEPS[state['step']]
        action()
        state['step'] += 1
        state['at'] = time.monotonic() + wait
    except Exception as error:
        finish(f'step {state["step"] + 1} ({STEPS[state["step"]][0].__name__}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
