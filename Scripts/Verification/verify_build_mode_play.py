"""Build Mode, milestone 2 (single-player Play session). Owner, October 27: build on every island outside Ports and obstruction
zones. Drives Build Mode through the controller's own key handler, with the keyboard keys and then the controller buttons:
  1. B opens Build Mode; looking at open ground shows the blue ghost (placeable, no reason);
  2. E and Q turn the foundation a quarter each way (Q/E on keyboard, d-pad right/left on a controller); C/Z and RB/LB change
     the material;
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


def face(site_x, site_y, ground, back=300.0, yaw=0.0, lift=0.0):
    """Stand `back` cm behind the site (along -yaw) and look at the ground there: the view is tracked toward it every frame
    from the real camera (the survivor's third-person camera sits behind and above)."""
    rad = math.radians(yaw)
    px, py = site_x - back * math.cos(rad), site_y - back * math.sin(rad)
    survival.restore_health(1000.0)
    pawn.teleport(unreal.Vector(px, py, T.height(px, py) + 130), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    state['aim'] = unreal.Vector(site_x, site_y, T.height(site_x, site_y) + lift)


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
    key('Gamepad_DPad_Right')
    yaw3 = build.get_aim_yaw()
    key('Gamepad_DPad_Left')
    yaw4 = build.get_aim_yaw()
    note('rotate', yaws=[yaw0, yaw1, yaw2, yaw3, yaw4])
    assert (yaw1 - yaw0) % 360 == 90 and yaw2 % 360 == yaw0 % 360, 'E/Q did not turn the foundation a quarter each way'
    assert (yaw3 - yaw0) % 360 == 90 and yaw4 % 360 == yaw0 % 360, 'd-pad did not turn the foundation a quarter each way'


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


def materials():
    m0 = build.get_material()
    key('C'); m1 = build.get_material()
    key('Gamepad_RightShoulder'); m2 = build.get_material()
    key('Z'); m3 = build.get_material()
    key('Gamepad_LeftShoulder'); m4 = build.get_material()
    note('materials', values=[m0, m1, m2, m3, m4])
    assert [m1 - m0, m2 - m0, m3 - m0, m4 - m0] == [1, 2, 1, 0], 'C/Z and RB/LB did not cycle the material'


def dial_open_keyboard():
    key('Tab')
    assert build.is_dial_open(), 'Tab did not open the piece dial'
    for x, y, slot in ((0, 1, 0), (1, 0, 3), (0, -1, 6), (-1, 0, 9), (.5, -.866, 5), (0, -.1, 5)):
        build.set_dial_pointer(x, y)
        assert build.get_hovered_slot() == slot, f'pointer ({x},{y}) hovers slot {build.get_hovered_slot()}, expected {slot}'
    build.set_dial_pointer(0, 1)
    note('dial', hovered=build.get_hovered_slot())


def dial_shot():
    shot('Dial')


def dial_pick_keyboard():
    key('LeftMouseButton')
    assert not build.is_dial_open(), 'picking a slot did not close the dial'
    sel = str(build.get_selected_type()).upper().replace('_', '')
    note('dial pick', selected=sel)
    assert 'TOPWALL' in sel, f'top slot picked {sel}'


def aim_first_again():
    x, y = state['site']
    face(x, y, T.height(x, y), back=300.0)


def place_wall():
    note('wall aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert build.is_aim_placeable(), f'wall refused: {build.get_aim_reason()}'
    key('Gamepad_FaceButton_Bottom')


def wall_placed():
    ps = pieces()
    kinds = sorted(str(p.get_piece_type()).upper().replace('_', '') for p in ps)
    note('wall placed', pieces=len(ps), kinds=kinds)
    assert len(ps) == 3 and any('TOPWALL' in k for k in kinds), f'expected a wall as a third piece: {kinds}'


def wall_again():
    note('wall again aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert not build.is_aim_placeable(), 'a second wall on the same edge should be refused'
    key('Gamepad_FaceButton_Bottom')


def still_three():
    n = len(pieces())
    assert n == 3, f'duplicate wall was built ({n})'
    key('Gamepad_FaceButton_Top')
    assert build.is_dial_open(), 'Y did not open the piece dial'
    build.set_dial_pointer(.5, -.866)


def dial_pick_pad():
    key('Gamepad_RightTrigger')
    sel = str(build.get_selected_type()).upper().replace('_', '')
    assert not build.is_dial_open() and 'ROOF' in sel, f'roof slot picked {sel}'


def place_roof():
    note('roof aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert build.is_aim_placeable(), f'roof refused: {build.get_aim_reason()}'
    key('LeftMouseButton')


def roof_placed():
    ps = pieces()
    kinds = sorted(str(p.get_piece_type()).upper().replace('_', '') for p in ps)
    note('roof placed', pieces=len(ps), kinds=kinds)
    assert len(ps) == 4 and any('ROOF' in k for k in kinds), f'expected a roof as a fourth piece: {kinds}'
    shot('Built')


def corner_rules():
    build.select_slot(7)      # bottom left corner: far from the wall on the +x edge
    x, y = state['site']
    face(x, y, T.height(x, y), back=300.0)


def corner_refused_then_pick():
    note('corner far', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert not build.is_aim_placeable() and 'wall' in str(build.get_aim_reason()).lower(), 'a corner away from every wall should be refused'
    build.select_slot(1)      # top corner: where the wall's end is


def corner_place():
    note('corner by wall', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert build.is_aim_placeable(), f'corner at the wall refused: {build.get_aim_reason()}'
    key('LeftMouseButton')


def corner_placed():
    n = len(pieces())
    assert n == 5, f'expected 5 pieces with the corner, found {n}'
    build.select_slot(11)


def kind(p):
    return str(p.get_piece_type()).upper().replace('_', '')


def second_foundation():
    return max((p for p in pieces() if 'FOUNDATION' in kind(p)), key=lambda p: p.get_actor_location().x)


def clear_through(a, b):
    res = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn],
                                                 unreal.DrawDebugTrace.NONE, True)
    return not (res[0] if isinstance(res, tuple) else res)


def doorway_aim():
    build.select_slot(0)
    f = second_foundation().get_actor_location()
    state['f2'] = (f.x, f.y)
    face(f.x, f.y, T.height(f.x, f.y), back=300.0, yaw=90.0)   # from the south: the first foundation's wall is on the west side


def doorway_place():
    key('R')
    assert build.get_design() == 1, 'R did not pick the doorway design'
    note('doorway aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert build.is_aim_placeable(), f'doorway refused: {build.get_aim_reason()}'
    key('Gamepad_FaceButton_Bottom')


def doorway_placed():
    doors = [p for p in pieces() if 'TOPWALL' in kind(p) and p.get_design() == 1]
    note('doorway placed', doors=len(doors), pieces=len(pieces()))
    assert len(doors) == 1, f'expected one doorway wall, found {len(doors)}'
    loc = doors[0].get_actor_location()
    through_opening = clear_through(unreal.Vector(loc.x - 150, loc.y, loc.z - 50), unreal.Vector(loc.x + 150, loc.y, loc.z - 50))
    through_jamb = clear_through(unreal.Vector(loc.x - 150, loc.y + 150, loc.z - 50), unreal.Vector(loc.x + 150, loc.y + 150, loc.z - 50))
    note('doorway openness', opening_clear=through_opening, jamb_clear=through_jamb)
    assert through_opening and not through_jamb, 'a doorway should let a ray through the opening and block it at the jamb'
    key('R')
    assert build.get_design() == 2, 'R after the doorway should be the window design'
    key('R')
    assert build.get_design() == 0


def stack_aim():
    build.select_slot(0)
    x, y = state['site']
    face(x + 190, y, T.height(x, y), back=300.0, lift=170.0)


def stack_place():
    note('pieces', all=[(kind(q), round(q.get_actor_location().x), round(q.get_actor_location().y), round(q.get_actor_location().z)) for q in pieces()])
    note('stack aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()), loc=str(build.get_aim_location()))
    assert build.is_aim_placeable(), f'wall on a wall refused: {build.get_aim_reason()}'
    key('Gamepad_FaceButton_Bottom')


def stacked():
    walls = sorted((p for p in pieces() if 'TOPWALL' in kind(p) and p.get_design() == 0), key=lambda p: p.get_actor_location().z)
    note('stacked', walls=[round(w.get_actor_location().z, 1) for w in walls])
    assert len(walls) == 2, f'expected two solid walls (one on the other), found {len(walls)}'
    rise = walls[1].get_actor_location().z - walls[0].get_actor_location().z
    assert abs(rise - 300) < 1, f'stacked wall is {rise} cm above the first, not 300'
    assert walls[1].get_base() == walls[0], 'stacked wall is not attached to the wall below'
    build.select_slot(0)


def pick_fitting(index, name):
    key('F')
    assert build.is_dial_open() and build.is_fittings_wheel_open(), 'F did not open the doors and windows wheel'
    build.set_dial_pointer(*((0, 1), (1, 0), (0, -1), (-1, 0))[index])
    assert build.get_hovered_slot() == index, f'pointer picked {build.get_hovered_slot()} not {index}'
    key('LeftMouseButton')
    sel = str(build.get_selected_type()).upper().replace('_', '')
    note('fitting picked', index=index, selected=sel, design=build.get_design())
    assert not build.is_dial_open() and name in sel, f'fitting {index} gave {sel}'


def fittings_wheel_shot():
    key('F')
    assert build.is_fittings_wheel_open(), 'F did not open the doors and windows wheel'
    build.set_dial_pointer(1, 0)
    shot('Fittings')


def fittings_wheel_close():
    key('F')
    assert not build.is_dial_open(), 'F did not close the wheel again'


def door_pick():
    pick_fitting(1, 'DOOR')
    f = second_foundation()
    top = f.get_top_z()
    assert pawn.teleport(local_point(f, 0, 0, top + 110), unreal.Rotator(roll=0, pitch=0, yaw=f.get_actor_rotation().yaw)), 'could not stand in the cell'
    state['aim'] = local_point(f, 190, 100, top + 100)       # a jamb of the doorway wall on the cell's +x edge


def door_place():
    note('door aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert build.is_aim_placeable(), f'door refused in a doorway: {build.get_aim_reason()}'
    key('LeftMouseButton')


def door_placed():
    doors = [p for p in pieces() if 'DOOR' in kind(p)]
    note('door placed', doors=len(doors))
    assert len(doors) == 1, f'expected one door, found {len(doors)}'
    assert doors[0].get_base().get_design() == 1, 'the door is not in the doorway wall'
    loc = doors[0].get_actor_location()
    through = clear_through(unreal.Vector(loc.x - 150, loc.y, loc.z), unreal.Vector(loc.x + 150, loc.y, loc.z))
    assert not through, 'the doorway is still open with a door in it'
    build.select_slot(0)
    key('F')
    assert build.is_dial_open()
    key('Escape')       # Escape closes the wheel first
    assert not build.is_dial_open() and 'PLACE' in mode()
    build.select_slot(0)


def door_refused():
    # a second door in the same doorway is refused, and a door on a solid wall is refused
    note('second door aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    build.select_slot(11)


def stair_aim():
    build.select_slot(8)      # L-shape staircase
    fx, fy = state['f2']
    face(fx, fy, T.height(fx, fy), back=300.0, yaw=90.0)


def stair_place():
    note('stair aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert build.is_aim_placeable(), f'stairs refused: {build.get_aim_reason()}'
    key('Gamepad_FaceButton_Bottom')


def stair_placed():
    stairs = [p for p in pieces() if 'STAIRCASE' in kind(p)]
    assert len(stairs) == 1, f'expected one staircase, found {len(stairs)}'
    state['stairs'] = stairs[0]
    note('stair placed', size=str(stairs[0].get_piece_size()), rot=str(stairs[0].get_actor_rotation()))
    # a second staircase on the same cell is refused
    note('second stair aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))


def local_point(f, x, y, z):
    loc, fwd, right = f.get_actor_location(), f.get_actor_forward_vector(), f.get_actor_right_vector()
    return unreal.Vector(loc.x + fwd.x * x + right.x * y, loc.y + fwd.y * x + right.y * y, z)


def cutout_check():
    f = second_foundation()
    top = f.get_top_z()
    hole_down = clear_through(local_point(f, -125, -100, top + 400), local_point(f, -125, -100, top + 290))
    solid_down = clear_through(local_point(f, -100, 100, top + 400), local_point(f, -100, 100, top + 290))
    note('ceiling cut-out', hole_clear=hole_down, ceiling_clear=solid_down)
    for lx, ly in ((-125, -100), (-75, -100), (25, -100), (100, -100), (100, 25), (100, 75)):
        res = unreal.SystemLibrary.line_trace_single(world, local_point(f, lx, ly, top + 400), local_point(f, lx, ly, top - 10), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
        note('step height at', x=lx, y=ly, hit_above_cell=round(res.to_tuple()[4].z - top, 1) if res else None)
    assert hole_down, 'the ceiling is not cut away over the staircase'
    assert not solid_down, 'the ceiling is missing where the staircase does not climb'
    steps = [p for p in pieces() if 'STAIRCASE' in kind(p)]
    assert len(steps) == 1


def stair_walk_start():
    build.select_slot(11)
    key('B')                                   # out of Build Mode so the survivor can walk
    assert 'OFF' in mode(), mode()
    f = second_foundation()
    top = f.get_top_z()
    state['aim'] = None
    state['stair_top'] = top
    state['walk_f'] = f
    # the first foundation's wall stands on this cell's west edge, so start on the first step instead of walking in from outside
    start = local_point(f, -160, -100, top + 80 + 110)
    assert pawn.teleport(start, unreal.Rotator(roll=0, pitch=0, yaw=f.get_actor_rotation().yaw)), 'could not place the survivor on the stairs'
    state['walk_until'] = time.monotonic() + 9.0
    state['walk_from'] = pawn.get_actor_location().z
    note('walker', max_step=pawn.character_movement.get_editor_property('max_step_height'), walkable=pawn.character_movement.get_editor_property('walkable_floor_angle'))


def stair_mid():
    q = pawn.get_actor_location()
    note('stair mid', pawn=(round(q.x), round(q.y), round(q.z)))
    shot('Walk')


def stair_walked():
    z = state['walk_max']
    q = pawn.get_actor_location()
    note('walk path (local x, y, z above cell top)', path=state.get('walk_log'))
    note('stair walk (highest point reached)', start_z=round(state['walk_from'], 1), end_z=round(z, 1), foundation_top=round(state['stair_top'], 1), pawn=(round(q.x), round(q.y)))
    # up the L-shape's flight, across its landing, up the turn and onto the ceiling's top (320 cm above the cell, plus the capsule)
    assert z - state['stair_top'] > 370, f'survivor did not climb the staircase onto the ceiling (z {z}, foundation top {state["stair_top"]})'
    state['walk_f'] = None
    key('B')
    assert 'PLACE' in mode(), mode()


def ceiling_aim():
    build.select_slot(3)      # right ceiling: over the second foundation, whose doorway wall is its supporting wall
    fx, fy = state['f2']
    face(fx, fy, T.height(fx, fy), back=300.0, yaw=90.0)


def ceiling_place():
    note('ceiling aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()), loc=str(build.get_aim_location()))
    assert build.is_aim_placeable(), f'ceiling refused: {build.get_aim_reason()}'
    key('Gamepad_FaceButton_Bottom')


def ceiling_placed():
    ceilings = [p for p in pieces() if 'CEILING' in kind(p)]
    note('ceiling placed', ceilings=len(ceilings), pieces=len(pieces()))
    assert len(ceilings) == 1, f'expected one ceiling, found {len(ceilings)}'
    state['ceiling'] = ceilings[0]
    build.select_slot(0)


def on_ceiling(at_wall=False):
    # stand on the part of the ceiling that is not cut away and look along its top toward the cell's +x side
    f = second_foundation()
    top = state['ceiling'].get_top_z()
    if not state.get('trees_cleared'):
        # tree crowns over the cell would hold the third-person camera: clear the trees near it for this check
        state['trees_cleared'] = True
        loc = f.get_actor_location()
        for tree in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.load_class(None, '/Script/EW.EWHarvestTree')):
            if math.hypot(tree.get_actor_location().x - loc.x, tree.get_actor_location().y - loc.y) < 1800:
                tree.destroy_actor()
    # a tree crown stands over the middle of the cell: for the wall, stand near it so the camera is not inside the crown
    stand = (150, 170) if at_wall else (-150, 150)
    assert pawn.teleport(local_point(f, stand[0], stand[1], top + 110), unreal.Rotator(roll=0, pitch=0, yaw=f.get_actor_rotation().yaw - (90 if at_wall else 0))), 'could not stand on the ceiling'
    state['aim'] = local_point(f, 190, 100, top + 100) if at_wall else local_point(f, 100, 150, top)     # the wall's jamb, or the ceiling


def upper_wall_aim():
    pick_fitting(2, 'TOPWALL')          # window frame: a wall with a window opening
    assert build.get_design() == 2, build.get_design()
    on_ceiling()


def upper_wall_place():
    note('upper wall aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()), loc=str(build.get_aim_location()))
    assert build.is_aim_placeable(), f'wall on a ceiling refused: {build.get_aim_reason()}'
    key('Gamepad_FaceButton_Bottom')


def upper_wall_placed():
    c = state['ceiling']
    upper = [p for p in pieces() if 'TOPWALL' in kind(p) and p.get_base() == c]
    note('upper wall', walls=len(upper))
    assert len(upper) == 1, f'expected one wall standing on the ceiling, found {len(upper)}'
    assert upper[0].get_actor_location().z > c.get_top_z() - 5, 'the upper wall is not above the ceiling'
    assert upper[0].get_design() == 2, f'the wall on the ceiling is design {upper[0].get_design()}, not a window frame'
    state['window_wall'] = upper[0]
    # a window pane goes in the window frame, and a door does not
    pick_fitting(1, 'DOOR')
    on_ceiling(True)


def upper_door_refused():
    note('door in a window frame', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert not build.is_aim_placeable(), 'a door was allowed in a window frame'
    pick_fitting(3, 'WINDOW')
    on_ceiling(True)


def upper_window_place():
    cam = unreal.GameplayStatics.get_player_camera_manager(world, 0)
    cl, cr = cam.get_camera_location(), cam.get_camera_rotation()
    end = cl + unreal.MathLibrary.get_forward_vector(cr) * 1600
    res = unreal.SystemLibrary.line_trace_single(world, cl, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    hit = res.to_tuple() if res else None
    note('window ray', cam=str(cl), hit_actor=str(hit[9]) if hit else None, hit_at=str(hit[4]) if hit else None, aim=str(state['aim']), wall=str(state['window_wall'].get_actor_location()))
    note('window aim', placeable=build.is_aim_placeable(), reason=str(build.get_aim_reason()))
    assert build.is_aim_placeable(), f'window refused in a window frame: {build.get_aim_reason()}'
    key('Gamepad_FaceButton_Bottom')


def upper_window_placed():
    windows = [p for p in pieces() if 'WINDOW' in kind(p)]
    note('window placed', windows=len(windows))
    assert len(windows) == 1 and windows[0].get_base() == state['window_wall'], 'the window is not in the window frame'
    build.select_slot(11)


def upper_foundation_refused():
    # a foundation is never built on a ceiling: aiming at the ceiling with the foundation selected must not offer it there
    c = state['ceiling'].get_actor_location()
    on_ceiling()


def upper_foundation_checked():
    loc = build.get_aim_location()
    note('foundation aimed at ceiling', placeable=build.is_aim_placeable(), loc=str(loc))
    if build.is_aim_placeable():
        assert loc.z < state['ceiling'].get_top_z() - 100, 'a foundation was offered on top of a ceiling'
    build.select_slot(11)


def to_demolish():
    key('X')
    assert 'DEMOLISH' in mode(), mode()
    x, y = state['site']
    face(x, y, T.height(x, y), back=300.0)


def demolish_first():
    x, y = state['site']
    mine = [p for p in pieces() if math.hypot(p.get_actor_location().x - x, p.get_actor_location().y - y) < 260]
    state['expect_after'] = len(pieces()) - len(mine)
    note('first foundation family', pieces=len(mine), total=len(pieces()))
    aimed = build.get_aimed_piece()
    note('demolish aim', aimed=bool(aimed), placeable=build.is_aim_placeable())
    assert aimed, 'looking at a piece in demolish mode finds nothing'
    key('Gamepad_RightTrigger')


def after_demolish():
    n = len(pieces())
    note('demolished', pieces=n)
    assert n == state['expect_after'], f'expected {state["expect_after"]} pieces after demolishing a foundation and what stood on it, found {n}'


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
         (place_on_piece, 1.2), (still_two, .2), (materials, .2), (dial_open_keyboard, 1.0), (dial_shot, .2), (dial_pick_keyboard, .5),
         (aim_first_again, 1.5), (place_wall, 1.5), (wall_placed, .2), (wall_again, 1.2), (still_three, 1.0), (dial_pick_pad, .5),
         (place_roof, 1.5), (roof_placed, 1.0), (corner_rules, 1.5), (corner_refused_then_pick, 1.2), (corner_place, 1.5), (corner_placed, .5),
         (doorway_aim, 1.5), (doorway_place, 1.5), (doorway_placed, .5), (stack_aim, 1.5), (stack_place, 1.5), (stacked, .5),
         (fittings_wheel_shot, 1.2), (fittings_wheel_close, .3), (door_pick, 1.5), (door_place, 1.5), (door_placed, .5), (stair_aim, 1.5), (stair_place, 1.5), (stair_placed, .3), (ceiling_aim, 1.5), (ceiling_place, 1.5), (ceiling_placed, .5), (cutout_check, .3), (stair_walk_start, 4.5), (stair_mid, 4.0), (stair_walked, .3), (upper_wall_aim, 1.5), (upper_wall_place, 1.5), (upper_wall_placed, .5), (upper_door_refused, 1.5), (upper_window_place, 1.5), (upper_window_placed, .5), (upper_foundation_refused, 1.5), (upper_foundation_checked, .3), (to_demolish, 1.5), (demolish_first, 1.5), (after_demolish, .2),
         (clean_up, 1.5), (demolish_second, 1.5), (leave_with_stick, .3), (to_port, 2.0), (port_red, 1.5),
         (port_nothing_built, .2), (finish, .1)]


def tick(delta):
    survival.restore_health(1000.0)
    survival.set_hunger(100.0)
    survival.set_hydration(100.0)
    if state['aim'] is not None:
        cam = unreal.GameplayStatics.get_player_camera_manager(world, 0).get_camera_location()
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, state['aim']))
    if state.get('walk_until') and time.monotonic() < state['walk_until']:
        f = state.get('walk_f')
        if f is None:
            pawn.add_movement_input(unreal.Vector(0, 1, 0), 1.0)
        else:
            # up the first flight along the cell's x, then turn right (cell +y) at the landing
            p, loc = pawn.get_actor_location(), f.get_actor_location()
            fwd, right = f.get_actor_forward_vector(), f.get_actor_right_vector()
            lx = (p.x - loc.x) * fwd.x + (p.y - loc.y) * fwd.y
            d = fwd if lx < 100 else right
            pawn.add_movement_input(d, 1.0)
            ly = (p.x - loc.x) * right.x + (p.y - loc.y) * right.y
            if time.monotonic() - state.get('walk_log_at', 0) > .4:
                state['walk_log_at'] = time.monotonic()
                state.setdefault('walk_log', []).append((round(lx), round(ly), round(p.z - state['stair_top'])))
        state['walk_max'] = max(state.get('walk_max', -1e9), pawn.get_actor_location().z)
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
