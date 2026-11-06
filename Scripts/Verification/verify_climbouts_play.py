"""Play check: a swimmer climbs out of the sea up every climb-out onto island ground (owner, November 5: a swimmer must
never be stuck against a steep coast), and swims ashore across the starter island's straight shores, on
Lvl_CoastalPlayground.

For each climb-out in world_climbouts.CLIMB_OUTS the survivor is set down in the water 16 m off the path's foot and steered
along the path (world_terrain.Climb) at ordinary walking speed, up its ramp out of the water, to its top and 6 m on. It passes when the survivor ends
on its feet (not swimming or falling) on ground within 1.5 m of the planned height there, having never strayed 4 m from
the path. For each of the starter's straight shores (world_layout.StarterIsland._oblique, where a sheer underwater wall
stood until November 5), the survivor is set down 15 m offshore at two points and steered 35 m straight inland; it
passes when it ends on its feet, out of deep water (points by the arrival and in Saltreach's harbour, left as built, are
skipped). A failed path records what stands in front of the survivor and a screenshot. Set EW_CLIMB_ONLY to a comma-
separated list of names ("Jungle4 climb-out 1") to run just those. Run with run_play_check.py, one player:
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check verify_climbouts_play.py -Result ClimbOutsPlayResult.json
        -Players 1 -Timeout 3600 -Visible
Writes Saved/ClimbOutsPlayResult.json and two screenshots per path in Saved/Screenshots/ClimbOuts.
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from world_climbouts import CLIMB_OUTS  # noqa: E402

ROOT = Path(unreal.Paths.project_saved_dir())
RESULT = ROOT / 'ClimbOutsPlayResult.json'
SHOTS = ROOT / 'Screenshots' / 'ClimbOuts'
SHOTS.mkdir(parents=True, exist_ok=True)
STRAY = 400.0
HALF_HEIGHT = 96.0
SETTLE = 1.5

world = next(w for w in unreal.EWEditorVerificationLibrary.get_play_worlds()
             if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
survival = pawn.get_survival_component()


def densify(points, step=100.0):
    out = []
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / step))
        out += [(ax + (bx - ax) * k / n, ay + (by - ay) * k / n) for k in range(n)]
    return out + [points[-1]]


def jobs():
    out = []
    for key in sorted(CLIMB_OUTS):
        for n, points in enumerate(CLIMB_OUTS[key]):
            climb = T.Climb(points)
            (ax, ay), (bx, by) = climb.points[0], climb.points[1]
            d = math.hypot(bx - ax, by - ay)
            dx, dy = (bx - ax) / d, (by - ay) / d
            (cx, cy), (ex, ey) = climb.points[-2], climb.points[-1]
            e = math.hypot(ex - cx, ey - cy)
            on = (ex + (ex - cx) / e * 600, ey + (ey - cy) / e * 600)
            route = densify([(ax - dx * 1600, ay - dy * 1600)] + climb.points + [on])
            out.append({'name': f'{key} climb-out {n + 1}', 'route': route, 'end_z': T.height(*on),
                        'length_m': round(climb.length / 100), 'rise_m': round(T.climb_profile(climb.length) / 100 + .65, 1)})
    starter = W.island('Starter')
    segs, _ = starter._oblique()
    for n, (x1, y1, x2, y2) in enumerate(segs):
        d = math.hypot(x2 - x1, y2 - y1)
        nx, ny = -(y2 - y1) / d, (x2 - x1) / d
        for t in (.45, .75):
            mx, my = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
            port = W.PORTS['Plains']
            if math.hypot(mx - starter.old.cx, my - starter.old.cy) < starter.OLD_END_KEPT[1] + 4000 or                     math.hypot(mx - port.cx, my - port.cy) < starter.HARBOUR_KEPT[1] + 4000:
                continue     # left as built by the arrival and in Saltreach's harbour (its piers have ladders)
            side = 1.0 if starter.distance(mx + 500 * nx, my + 500 * ny) > 0 else -1.0     # out to sea
            sx, sy = mx + side * nx * 1500, my + side * ny * 1500
            ex, ey = mx - side * nx * 2000, my - side * ny * 2000
            out.append({'name': f'Starter straight shore {n + 1} at {round(t * 100)}%', 'route': densify([(sx, sy), (ex, ey)]),
                        'end_z': T.height(ex, ey), 'length_m': 35, 'rise_m': None})
    only = [s.strip() for s in os.environ.get('EW_CLIMB_ONLY', '').split(',') if s.strip()]
    return [j for j in out if not only or j['name'] in only]


JOBS = jobs()
report = {'map': '/Game/Elitewake/Maps/Lvl_CoastalPlayground', 'paths': [], 'success': False, 'error': None}
state = {'i': -1, 'h': None}


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


def shot(r, name):
    path = SHOTS / f"{r['name'].replace(' ', '_').replace('%', '')}_{name}.png"
    unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{path}"')
    r.setdefault('screenshots', []).append(str(path))


def begin(i):
    state['i'] = i
    job = JOBS[i]
    route = job['route']
    x, y = route[0]
    heading = math.atan2(route[3][1] - y, route[3][0] - x)
    assert pawn.teleport(unreal.Vector(x, y, T.SEA + 20), unreal.Rotator(0, 0, math.degrees(heading)))
    pc.set_control_rotation(unreal.Rotator(0, -10, math.degrees(heading)))
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(route, route[1:]))
    state.update(job=job, k=0, phase='settle', t0=now(), until=now() + SETTLE, limit=now() + SETTLE + length / 200.0 + 30.0)
    report['paths'].append({'name': job['name'], 'length_m': job['length_m'], 'rise_m': job['rise_m'], 'max_stray_cm': 0,
                            'swim_s': 0.0, 'arrived': False})


def nearest(route, p, k):
    best = k
    for j in range(k, min(len(route), k + 30)):
        if math.hypot(route[j][0] - p.x, route[j][1] - p.y) < math.hypot(route[best][0] - p.x, route[best][1] - p.y):
            best = j
    return best


def ahead_of(p, heading):
    """What stands in front of the survivor: knee- and chest-high traces 1.5 m ahead."""
    found = []
    for lift in (40.0, 120.0):
        a = unreal.Vector(p.x, p.y, p.z - HALF_HEIGHT + lift)
        b = unreal.Vector(a.x + 150 * math.cos(heading), a.y + 150 * math.sin(heading), a.z)
        hit = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn],
                                                     unreal.DrawDebugTrace.NONE, True)
        actor = hit.to_tuple()[9] if hit else None
        found.append(actor.get_actor_label() if actor else None)
    return found


def end_path(error=None):
    r = report['paths'][-1]
    r['error'] = error
    if error:
        p = pawn.get_actor_location()
        route, k = state['job']['route'], state['k']
        tx, ty = route[min(k + 3, len(route) - 1)]
        r['ahead_knee'], r['ahead_chest'] = ahead_of(p, math.atan2(ty - p.y, tx - p.x))
        r['stuck_at'] = [round(p.x), round(p.y), round(p.z)]
        shot(r, 'stuck')
    r['seconds'] = round(now() - state['t0'] - SETTLE, 1)
    r['success'] = error is None
    unreal.log(f"EWCLIMBOUT {r['name']}: {'ok' if error is None else error}")
    state.update(phase='next', until=now() + 1.0)      # hold still while the screenshot is taken


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report['error'] = error
    report['passed'] = sum(1 for r in report['paths'] if r.get('success'))
    report['success'] = error is None and len(report['paths']) == len(JOBS) and report['passed'] == len(JOBS)
    report['finished_utc'] = time.time()
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ClimbOuts success={report["success"]} passed={report["passed"]}/{len(JOBS)} error={error}')


def tick(delta):
    try:
        if state['i'] < 0:
            unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
            begin(0)
            return
        if survival:
            survival.restore_health(1000.0)
        job, r, t = state['job'], report['paths'][-1], now()
        route = job['route']
        p = pawn.get_actor_location()
        if state['phase'] == 'next':
            if t >= state['until']:
                if state['i'] + 1 < len(JOBS):
                    begin(state['i'] + 1)
                else:
                    finish()
            return
        if state['phase'] == 'settle':
            if t >= state['until']:
                shot(r, 'start')
                state['phase'] = 'go'
            return
        if t > state['limit']:
            end_path(f"stopped at {state['k']} of {len(route) - 1} ({p.x:.0f}, {p.y:.0f}, {p.z:.0f})")
            return
        if move.is_swimming():
            r['swim_s'] = round(r['swim_s'] + delta, 2)
        k = state['k'] = nearest(route, p, state['k'])
        stray = math.hypot(route[k][0] - p.x, route[k][1] - p.y)
        r['max_stray_cm'] = max(r['max_stray_cm'], round(stray))
        if stray > STRAY:
            end_path(f'left the path at {k} of {len(route) - 1}, {stray:.0f} cm aside')
            return
        if k >= len(route) - 2 and math.hypot(route[-1][0] - p.x, route[-1][1] - p.y) < 120:
            if move.is_falling() or move.is_swimming():
                return
            r['arrived'] = True
            feet = p.z - HALF_HEIGHT
            r['end_feet_cm'], r['end_ground_cm'] = round(feet), round(job['end_z'])
            shot(r, 'top')
            ok = abs(feet - job['end_z']) < 150          # on its feet (not swimming) where the ground is
            end_path(None if ok else f'ended at {feet:.0f} cm, the ground there is planned at {job["end_z"]:.0f}')
            return
        tx, ty = route[min(k + 3, len(route) - 1)]
        heading = math.atan2(ty - p.y, tx - p.x)
        pc.set_control_rotation(unreal.Rotator(0, -10, math.degrees(heading)))
        pawn.add_movement_input(unreal.Vector(math.cos(heading), math.sin(heading), 0), 1.0)
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
