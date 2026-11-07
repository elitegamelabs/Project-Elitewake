"""Build Mode with a second player (listen server plus one client, EW_PLAY_PLAYERS=2). Owner, October 27: building must work for
other players too, and the server keeps what was built. The client builds through the real server RPC (the component's ServerPlace,
which the server checks again): a foundation, a wall with a doorway, a door in it, an L-shape staircase and a ceiling. Then:
  1. the client sees every piece the server made, the stair steps (height probes), the ceiling cut away over the stairs and solid
     elsewhere (rays in the client's own world);
  2. the door is closed (the doorway blocks a ray); the server opens it (Interact) and the client sees it open and the ray pass;
  3. the server saves the structures (UEWBuildSave) and every piece is removed (the client sees none), then restores them: the client
     sees the same pieces again, the door still open and the ceiling re-cut.
Writes Saved/BuildMultiplayerPlayResult.json."""
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
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
Z = unreal.EWBuildZones
Type = unreal.EWBuildPieceType
comp = client.get_build_component()
SLOT = 'BuildMPTest'
report = {'checks': []}
state = {'step': 0, 'at': time.monotonic() + 14, 'handle': None}


def note(label, **values):
    report['checks'].append({'label': label, **values})
    unreal.log(f'BuildMP: {label} {values}')


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(p) == pid(client.get_controlled_pawn()))


def pieces(w):
    return unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWBuildPiece)


def kind(p):
    return str(p.get_piece_type()).upper().replace('_', '')


def of_kind(w, name):
    return [p for p in pieces(w) if name in kind(p)]


def clear(w, a, b):
    res = unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, list(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWCharacter)), unreal.DrawDebugTrace.NONE, True)
    return not (res[0] if isinstance(res, tuple) else res)


def hit_z(w, x, y, z0, z1):
    res = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, z0), unreal.Vector(x, y, z1), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    return res.to_tuple()[4].z if res else None


def flat(x, y, within=40.0):
    res = Z.get_footprint_ground(server_world, x, y, 200, 200, 0)
    low, high = res[-2], res[-1]
    return -1e6 < low <= high < 1e6 and high - low <= within


def find_site():
    for name in ('Starter', 'Desert1', 'Jungle1', 'Swamp1', 'Winter1'):
        isle = W.island(name)
        r = int(isle.reach())
        cells = sorted(((int(isle.cx) + dx, int(isle.cy) + dy) for dx in range(-r, r, 250) for dy in range(-r, r, 250)),
                       key=lambda c: math.hypot(c[0] - isle.cx, c[1] - isle.cy))
        for x, y in cells:
            if isle.distance(x, y) > -300:
                continue
            if not Z.check_footprint(server_world, x, y, 200, 200, 0) and flat(x, y):
                return x, y
    raise AssertionError('no open site on any island')


def key(name):
    assert lib.send_verification_gameplay_key(client, name), f'key {name} not handled'


def stand(lx, ly, yaw=0.0):
    """Put the survivor (server side) at a spot relative to the site; it replicates to the client."""
    x, y = state['site']
    owner.teleport(unreal.Vector(x + lx, y + ly, T.height(x + lx, y + ly) + 130 + state.get('lift', 0)), unreal.Rotator(roll=0, pitch=0, yaw=yaw))


def cell():
    return of_kind(client_world, 'FOUNDATION')[0]


def local(f, lx, ly, z):
    q = f.get_actor_location()
    return unreal.Vector(q.x + lx, q.y + ly, z)


def s_site():
    x, y = find_site()
    state['site'] = (x, y)
    note('site', x=x, y=y)
    stand(-300, 0)
    state['aim'] = unreal.Vector(x, y, T.height(x, y))


def s_open():
    key('B')
    assert 'PLACE' in str(comp.get_mode()).upper(), f'B did not open Build Mode on the client: {comp.get_mode()}'
    comp.select_slot(11)


def click(label, ok=True):
    note(label + ' aim', placeable=comp.is_aim_placeable(), reason=str(comp.get_aim_reason()))
    assert comp.is_aim_placeable() == ok, f'{label}: client ghost says {comp.is_aim_placeable()} ({comp.get_aim_reason()})'
    key('LeftMouseButton')


def s_foundation():
    click('foundation')


def s_wall():
    n = len(pieces(client_world))
    note('foundation on server and client', server=len(pieces(server_world)), client=n,
         client_made_it_locally=[p.has_authority() for p in pieces(client_world)])
    assert len(pieces(server_world)) == 1 and n == 1, 'the foundation did not come from the server'
    comp.select_slot(0)
    comp.cycle_design(1)       # doorway
    assert comp.get_design() == 1


def s_wall_click():
    click('doorway wall')
    comp.cycle_design(-1)
    comp.select_slot(0)


def s_door_aim():
    x, y = state['site']
    stand(0, 0)
    state['aim'] = unreal.Vector(x + 190, y + 100, of_kind(server_world, 'FOUNDATION')[0].get_top_z() + 100)
    comp.select_fitting(1)


def s_door_click():
    click('door')
    comp.select_slot(8)         # L-shape staircase


def s_stairs_aim():
    x, y = state['site']
    stand(-300, 0)
    state['aim'] = unreal.Vector(x, y, T.height(x, y))


def s_stairs_click():
    click('stairs')
    comp.select_slot(3)         # right ceiling


def s_ceiling_click():
    click('ceiling')


def look(w, label):
    """Everything a client should see, read by rays in `w`."""
    f = of_kind(w, 'FOUNDATION')[0]
    top = f.get_top_z()
    q = f.get_actor_location()
    kinds = sorted(kind(p) for p in pieces(w))
    note(label + ' pieces', kinds=kinds)
    assert len(kinds) == 5 and sum('STAIRCASE' in k for k in kinds) == 1 and sum('CEILING' in k for k in kinds) == 1, f'unexpected pieces {kinds}'
    for lx, ly, rise in ((-125, -100, 80), (-75, -100, 120), (25, -100, 200), (100, 25, 240), (100, 75, 280)):
        z = hit_z(w, q.x + lx, q.y + ly, top + 400, top - 10)
        assert z is not None and abs(z - top - rise) < 1.5, f'{label}: step at ({lx},{ly}) is {None if z is None else z - top} high, expected {rise}'
    assert clear(w, unreal.Vector(q.x - 125, q.y - 100, top + 400), unreal.Vector(q.x - 125, q.y - 100, top + 290)), f'{label}: ceiling not cut away over the stairs'
    assert not clear(w, unreal.Vector(q.x - 100, q.y + 100, top + 400), unreal.Vector(q.x - 100, q.y + 100, top + 290)), f'{label}: ceiling missing where it should be solid'
    door = of_kind(w, 'DOOR')[0]
    wall = of_kind(w, 'TOPWALL')[0]
    d = wall.get_actor_location()
    # along the doorway's middle, just above the staircase landing (200 cm) and below the lintel
    return door, clear(w, unreal.Vector(d.x - 150, d.y - 30, top + 215), unreal.Vector(d.x + 150, d.y - 30, top + 215)), door.is_open()


def s_client_sees():
    door, through, is_open = look(client_world, 'client')
    note('door on the client, closed', is_open=is_open, doorway_clear=through)
    assert not is_open and not through, 'the closed door should block the doorway for the client'
    key('B')                    # out of Build Mode
    stand(280, 0, 180)
    note('worlds', server=len(pieces(server_world)), client=len(pieces(client_world)), auth=[c.has_authority() for c in pcs], per_world=[len(pieces(w)) for w in worlds], chars=[len(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWCharacter)) for w in worlds], same=server_world == client_world, server_name=server_world.get_name(), client_name=client_world.get_name())
    server_door = of_kind(server_world, 'DOOR')[0]
    assert server_door.interact(owner), 'the server would not open the door for the survivor'


def s_door_open():
    door, through, is_open = look(client_world, 'client')
    note('door on the client, opened by the server', is_open=is_open, alpha=round(door.get_open_alpha(), 2), doorway_clear=through)
    assert is_open and door.get_open_alpha() > .99, 'the client does not see the door open'
    assert through, 'the open door still blocks the doorway for the client'
    assert unreal.EWBuildSave.save_world(server_world, SLOT), 'the server could not save the structures'
    for p in list(pieces(server_world)):
        p.destroy_actor()


def s_gone():
    n_server, n_client = len(pieces(server_world)), len(pieces(client_world))
    note('after removing everything', server=n_server, client=n_client)
    assert n_server == 0 and n_client == 0, f'pieces remain (server {n_server}, client {n_client})'
    built = unreal.EWBuildSave.restore_world(server_world, SLOT)
    note('restored by the server', built=built)
    assert built == 5, f'the server restored {built} pieces, expected 5'


def s_back():
    door, through, is_open = look(client_world, 'client after restore')
    note('after the restore, on the client', is_open=is_open, doorway_clear=through)
    assert is_open and through, 'the door did not come back open on the client'
    look(server_world, 'server after restore')
    unreal.GameplayStatics.delete_game_in_slot(SLOT, 0)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'BuildMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK BuildMultiplayer success={error is None} error={error}')


STEPS = [(s_site, 3.0), (s_open, 1.5), (s_foundation, 2.0), (s_wall, 1.5), (s_wall_click, 2.0), (s_door_aim, 1.5), (s_door_click, 2.0),
         (s_stairs_aim, 1.5), (s_stairs_click, 2.0), (s_ceiling_click, 2.5), (s_client_sees, 2.5),
         (s_door_open, 2.5), (s_gone, 3.0), (s_back, .3), (finish, .1)]


def tick(delta):
    if state.get('aim') is not None:
        cam = unreal.GameplayStatics.get_player_camera_manager(client_world, 0).get_camera_location()
        client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, state['aim']))
    if time.monotonic() < state['at']:
        return
    try:
        action, wait = STEPS[state['step']]
        action()
        state['step'] += 1
        state['at'] = time.monotonic() + wait
    except Exception as error:
        import traceback
        note('failed', step=STEPS[state['step']][0].__name__, trace=traceback.format_exc()[-600:])
        finish(f'step {state["step"]} ({STEPS[state["step"]][0].__name__}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
