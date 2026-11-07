"""Play check: a survivor walks out of each sea cavern's berth to island ground on Lvl_CoastalPlayground.

For each cavern in world_layout.SEA_CAVERN_ACCESS (Plains3, Desert3: straight out through the back; Jungle3: the ledge
spiralling up its wall), the player is set down on the walk at the berth and steered along it at ordinary walking speed
(world_terrain.Cave.exit_path). It passes when the character reaches the far end on its feet, never drops more than a
metre below the walk or strays 4 m from it, then steps 6 m on onto the island and back up 3 m onto the walk's end (the
step a returning crew takes). Run with run_play_check.py, one player:
    EW_PLAY_CHECK=Scripts/Verification/verify_cavern_walks_play.py EW_PLAY_RESULT=CavernWalksPlayResult.json
Writes Saved/CavernWalksPlayResult.json and three screenshots per cavern in Saved/Screenshots/CavernWalks. This checks
walking and collision only; sailing a ship in and judging how well it is hidden are separate checks.
"""
import json
import math
import sys
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

ROOT = Path(unreal.Paths.project_saved_dir())
RESULT = ROOT / 'CavernWalksPlayResult.json'
SHOTS = ROOT / 'Screenshots' / 'CavernWalks'
SHOTS.mkdir(parents=True, exist_ok=True)
STRAY = 400.0        # cm from the walk's centre line
DROP = 100.0         # cm below the walk's surface (feet)
HALF_HEIGHT = 96.0   # the capsule's half height: feet are this far below the actor

world = next(w for w in unreal.EWEditorVerificationLibrary.get_play_worlds()
             if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
survival = pawn.get_survival_component()
KEYS = list(W.SEA_CAVERN_ACCESS)
report = {'map': '/Game/Elitewake/Maps/Lvl_CoastalPlayground', 'caverns': {}, 'success': False, 'error': None}
state = {'i': -1, 'h': None}


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


def shot(key, name):
    path = SHOTS / f'{key}_{name}.png'
    unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{path}"')
    report['caverns'][key].setdefault('screenshots', []).append(str(path))


def walk_points(cave):
    """The walk in world coordinates: [(x, y, surface)], and its length in cm."""
    pts = [(*cave.world(u, v), z) for u, v, z, _ in cave.exit_path()]
    return pts, sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def begin(i):
    state['i'] = i
    key = KEYS[i]
    cave = T.CAVES[key]
    pts, length = walk_points(cave)
    x, y, z = pts[3]
    heading = math.atan2(pts[6][1] - y, pts[6][0] - x)
    assert pawn.teleport(unreal.Vector(x, y, z + HALF_HEIGHT + 15), unreal.Rotator(0, 0, math.degrees(heading)))
    pc.set_control_rotation(unreal.Rotator(0, -8, math.degrees(heading)))
    state.update(key=key, pts=pts, k=3, phase='settle', t0=now(), until=now() + 1.5,
                 limit=now() + length / 250.0 + 40.0, mid_shot=False)
    report['caverns'][key] = {'access': W.SEA_CAVERN_ACCESS[key], 'length_m': round(length / 100),
                              'rise_m': round((pts[-1][2] - pts[0][2]) / 100, 1),
                              'max_drop_cm': 0, 'max_stray_cm': 0, 'arrived': False, 'stepped_off': False,
                              'stepped_back_on': False}


def nearest(pts, p, k):
    """Index of the walk point nearest the character, searching on from k (the walk never doubles back)."""
    best = k
    for j in range(k, min(len(pts), k + 40)):
        if math.hypot(pts[j][0] - p.x, pts[j][1] - p.y) < math.hypot(pts[best][0] - p.x, pts[best][1] - p.y):
            best = j
    return best


def steer(tx, ty, p):
    heading = math.atan2(ty - p.y, tx - p.x)
    pc.set_control_rotation(unreal.Rotator(0, -8, math.degrees(heading)))
    pawn.add_movement_input(unreal.Vector(math.cos(heading), math.sin(heading), 0), 1.0)


def end_cavern(error=None):
    r = report['caverns'][state['key']]
    r['error'] = error
    r['seconds'] = round(now() - state['t0'], 1)
    r['success'] = error is None
    if state['i'] + 1 < len(KEYS):
        begin(state['i'] + 1)
    else:
        finish()


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report['error'] = error
    report['success'] = error is None and len(report['caverns']) == len(KEYS) and \
        all(r.get('success') for r in report['caverns'].values())
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK CavernWalks success={report["success"]} error={error}')


def tick(delta):
    try:
        if state['i'] < 0:
            unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
            begin(0)
            return
        if survival:
            survival.restore_health(1000.0)
        key, pts, t = state['key'], state['pts'], now()
        r = report['caverns'][key]
        p = pawn.get_actor_location()
        if state['phase'] == 'settle':
            if t >= state['until']:
                shot(key, 'start')
                state['phase'] = 'walk'
            return
        if t > state['limit']:
            end_cavern(f'{key}: stopped at walk point {state["k"]} of {len(pts) - 1} ({state["phase"]})')
            return
        if state['phase'] == 'walk':
            k = state['k'] = nearest(pts, p, state['k'])
            fx, fy, fz = pts[k]
            stray = math.hypot(fx - p.x, fy - p.y)
            drop = fz - (p.z - HALF_HEIGHT)
            r['max_stray_cm'] = max(r['max_stray_cm'], round(stray))
            if not move.is_falling():
                r['max_drop_cm'] = max(r['max_drop_cm'], round(drop))
            if stray > STRAY or (drop > DROP and not move.is_falling()):
                end_cavern(f'{key}: left the walk at point {k} ({stray:.0f} cm aside, {drop:.0f} cm below)')
                return
            if not state['mid_shot'] and k >= len(pts) // 2:
                state['mid_shot'] = True
                shot(key, 'midway')
            if k >= len(pts) - 2 and math.hypot(pts[-1][0] - p.x, pts[-1][1] - p.y) < 150:
                r['arrived'] = True
                ax, ay = pts[-1][0] - pts[-4][0], pts[-1][1] - pts[-4][1]
                n = math.hypot(ax, ay)
                state['out'] = (pts[-1][0] + ax / n * 600, pts[-1][1] + ay / n * 600)
                state['back'] = (pts[-1][0] - ax / n * 300, pts[-1][1] - ay / n * 300)
                state['phase'] = 'off'
                return
            target = pts[min(k + 4, len(pts) - 1)]
            steer(target[0], target[1], p)
        elif state['phase'] == 'off':
            ox, oy = state['out']
            if math.hypot(ox - p.x, oy - p.y) < 100:
                r['stepped_off'] = True
                r['island_ground_cm'] = round(p.z - HALF_HEIGHT)
                shot(key, 'island')
                state['phase'] = 'back'
                return
            steer(ox, oy, p)
        elif state['phase'] == 'back':
            bx, by = state['back']
            if math.hypot(bx - p.x, by - p.y) < 100:
                feet = p.z - HALF_HEIGHT
                r['stepped_back_on'] = abs(feet - pts[-4][2]) < 60
                end_cavern(None if r['stepped_back_on'] else
                           f'{key}: back on the walk at {feet:.0f} cm, the walk is at {pts[-4][2]:.0f}')
                return
            steer(bx, by, p)
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
