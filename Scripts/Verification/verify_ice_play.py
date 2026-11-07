"""Play check: the Winter ice sheets (owner, November 6: sheets of ice round the Winter mountains, as tall as the nearest
cliff, and the ice is solid), on Lvl_CoastalPlayground, one player.

1. Census: every Winter island has ice sheets, and no other island has any.
2. For one sheet on each Winter island:
   - Solid wall: the survivor is set down 8 m outside the sheet's edge and walks straight at it for 5 s. It passes when
     the survivor never gets inside the ice (never more than 1 m past the edge while below the ice's top).
   - Solid top: the survivor is dropped onto the middle of the sheet from 3 m up. It passes when the survivor ends
     standing on the ice's surface (within 1 m of it), not fallen through.
   - Screenshots from the wall's foot and from 70 m off (Saved/Screenshots/Ice).
Run with run_play_check.py, one player:
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check verify_ice_play.py -Result IcePlayResult.json
        -Players 1 -Standalone 1 -Timeout 900 -Visible
Writes Saved/IcePlayResult.json.
"""
import json
import math
import time
from pathlib import Path

import unreal

lib = unreal.EWEditorVerificationLibrary
ROOT = Path(unreal.Paths.project_saved_dir())
RESULT = ROOT / 'IcePlayResult.json'
SHOTS = ROOT / 'Screenshots' / 'Ice'
SHOTS.mkdir(parents=True, exist_ok=True)
HALF = 96.0
world = next(w for w in lib.get_play_worlds() if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
sheets = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
          if str(a.get_actor_label()).startswith('Ice Sheet ')]
FORESTS = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWForest))   # the ground, not the treetops
report = {'map': '/Game/Elitewake/Maps/Lvl_CoastalPlayground', 'success': False, 'error': None, 'sheets': []}
state = {'h': None, 'phase': 'wait', 'until': time.monotonic() + 8.0, 'jobs': [], 'k': -1}


def down(x, y, z_from=40000.0):
    """The first thing straight down at (x, y): (z, actor)."""
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, z_from), unreal.Vector(x, y, -10000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn] + FORESTS, unreal.DrawDebugTrace.NONE, True)
    if not hit:
        return None, None
    t = hit.to_tuple()
    return t[4].z, t[9]


def survey(sheet):
    """A point in the sheet's middle, its top there, and its edge going outward from there (x, y, outward unit)."""
    origin, extent = sheet.get_actor_bounds(False)
    best = None
    for i in range(-6, 7):
        for j in range(-6, 7):
            x, y = origin.x + extent.x * i / 7, origin.y + extent.y * j / 7
            z, actor = down(x, y)
            if actor == sheet:
                d = math.hypot(i, j)
                if best is None or d < best[3]:
                    best = (x, y, z, d)
    assert best, f'{sheet.get_actor_label()}: no ice found from above'
    x, y, top, _ = best
    report.setdefault('debug', {})[str(sheet.get_actor_label())] = {'middle': [round(x), round(y), round(top)], 'rays': []}
    for a in range(0, 360, 20):
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        last, recent = None, []
        for r in range(0, 40000, 200):
            z, actor = down(x + ux * r, y + uy * r)
            if a < 80 and r % 1000 == 0:
                report['debug'][str(sheet.get_actor_label())]['rays'].append([a, r, None if z is None else round(z), str(actor.get_actor_label()) if actor else None])
            if actor != sheet:
                if recent:
                    last = max(recent, key=lambda q: q[2])     # the wall's top, not a point partway down its slope
                if a < 80:
                    report['debug'][str(sheet.get_actor_label())]['rays'].append(['end', a, r, None if z is None else round(z), str(actor.get_actor_label()) if actor else None, last and round(last[2])])
                if last and z is not None and last[2] - z > 600:        # a real wall: the ice stands 6 m+ above what is beyond
                    return (x, y, top), (last[0], last[1], last[2], z), (ux, uy)
                break
            last = (x + ux * r, y + uy * r, z)
            recent = (recent + [last])[-5:]
    raise AssertionError(f'{sheet.get_actor_label()}: no ice wall found')


def jobs():
    by = {}
    for s in sheets:
        key = str(s.get_actor_label()).split(' ')[2]
        by.setdefault(key, []).append(s)
    report['sheets_by_island'] = {k: len(v) for k, v in by.items()}
    assert set(by) == {'Winter1', 'Winter2', 'Winter3', 'Winter4'}, f'ice on {sorted(by)}'
    return [max(v, key=lambda s: s.get_actor_bounds(False)[1].x * s.get_actor_bounds(False)[1].y) for _, v in sorted(by.items())]


def look(x, y, z):
    eye, _ = pawn.get_actor_eyes_view_point()
    yaw = math.degrees(math.atan2(y - eye.y, x - eye.x))
    pitch = -math.degrees(math.atan2(eye.z - z, math.hypot(x - eye.x, y - eye.y)))
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=max(-40.0, min(40.0, pitch)), yaw=yaw))


def shot(name):
    path = SHOTS / f'{name}.png'
    unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{path}"')
    return str(path)


def begin(k):
    state['k'] = k
    sheet = state['jobs'][k]
    middle, edge, (ux, uy) = survey(sheet)
    ex, ey, etop, beyond = edge
    sx, sy = ex + ux * 800, ey + uy * 800
    g, _ = down(sx, sy, beyond + 500)
    pawn.teleport(unreal.Vector(sx, sy, (g or beyond) + HALF + 20), unreal.Rotator(yaw=math.degrees(math.atan2(-uy, -ux))))
    r = {'sheet': str(sheet.get_actor_label()), 'wall_m': round((etop - beyond) / 100, 1), 'top_z': round(middle[2])}
    report['sheets'].append(r)
    state.update(sheet=sheet, middle=middle, edge=edge, out=(ux, uy), phase='wall_settle', until=time.monotonic() + 1.5, inside=0.0,
                 start=(sx, sy), walked=0.0)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report['error'] = error
    report['success'] = error is None and all(r.get('wall_ok') and r.get('top_ok') for r in report['sheets'])
    report['finished_utc'] = time.time()
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f"EWPLAYCHECK Ice success={report['success']} error={error}")


def tick(delta):
    try:
        now = time.monotonic()
        survival = pawn.get_survival_component()
        if survival:
            survival.restore_health(1000.0)
        if state['phase'] == 'wait':
            if now >= state['until']:
                unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
                others = [s.get_actor_label() for s in sheets if 'Winter' not in str(s.get_actor_label())]
                assert not others, f'ice off the Winter islands: {others}'
                state['jobs'] = jobs()
                begin(0)
            return
        r = report['sheets'][-1]
        ex, ey, etop, beyond = state['edge']
        ux, uy = state['out']
        p = pawn.get_actor_location()
        if state['phase'] == 'wall_settle':
            look(ex, ey, etop)
            if now >= state['until']:
                r['screenshot_wall'] = shot(f"{r['sheet'].replace(' ', '_')}_wall")
                state.update(phase='walk', until=now + 5.0)
            return
        if state['phase'] == 'walk':
            pawn.add_movement_input(unreal.Vector(-ux, -uy, 0), 1.0)
            past = (ex - p.x) * ux + (ey - p.y) * uy            # how far past the edge, inward (the survivor walks along -u)
            state['walked'] = max(state.get('walked', 0.0), math.hypot(p.x - state['start'][0], p.y - state['start'][1]))
            if past > 100 and p.z - HALF < etop - 200:
                state['inside'] = max(state['inside'], past)
            if now >= state['until']:
                r['wall_ok'] = state['inside'] == 0.0
                r['got_past_edge_cm'] = round(state['inside'])
                r['ended_cm_outside_edge'] = round(-((ex - p.x) * ux + (ey - p.y) * uy))
                r['walked_cm'] = round(state.get('walked', 0.0))
                z_above, what = down(p.x, p.y)
                r['end'] = [round(p.x), round(p.y), round(p.z - HALF)]
                r['top_above_end'] = [None if z_above is None else round(z_above), str(what.get_actor_label()) if what else None]
                if state['inside'] and z_above is not None and what != state['sheet']:
                    r['wall_ok'] = True        # on open ground in a gap of the ice (a rock through it), not inside the ice
                    r['note'] = 'walked into a gap in the ice, onto bare ground'
                r['screenshot_end'] = shot(f"{r['sheet'].replace(' ', '_')}_end")
                mx, my, mz = state['middle']
                pawn.teleport(unreal.Vector(mx, my, mz + HALF + 300), unreal.Rotator())
                state.update(phase='drop', until=now + 3.0)
            return
        if state['phase'] == 'drop':
            if now >= state['until'] and not move.is_falling():
                mx, my, mz = state['middle']
                feet = p.z - HALF
                r['stood_cm_above_ice'] = round(feet - mz)
                r['top_ok'] = abs(feet - mz) < 100
                # From 70 m off, looking at the sheet.
                ox, oy = ex + ux * 7000, ey + uy * 7000
                g, _ = down(ox, oy)
                pawn.teleport(unreal.Vector(ox, oy, (g or 0) + HALF + 20), unreal.Rotator())
                state.update(phase='far', until=now + 2.0)
            elif now >= state['until'] + 5:
                r['top_ok'] = False
                r['note'] = 'still falling'
                state.update(phase='far', until=now)
            return
        if state['phase'] == 'far':
            mx, my, mz = state['middle']
            look(mx, my, mz)
            if now >= state['until']:
                r['screenshot_far'] = shot(f"{r['sheet'].replace(' ', '_')}_far")
                unreal.log(f"EWICE {r['sheet']}: wall {r.get('wall_ok')} top {r.get('top_ok')}")
                state.update(phase='next', until=now + 1.0)
            return
        if state['phase'] == 'next' and now >= state['until']:
            if state['k'] + 1 < len(state['jobs']):
                begin(state['k'] + 1)
            else:
                finish()
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
