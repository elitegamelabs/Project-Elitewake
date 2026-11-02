"""Walking routes, measured in-game (CLAUDE.md 5.1: the island size target is a walking time, measured before dimensions are
decided; owner, November 1: 15-20 minutes across each island). Single player (EW_PLAY_STANDALONE=1, EW_PLAY_PLAYERS=1) on
/Game/Elitewake/Maps/Lvl_CoastalPlayground, run with run_play_check.py (EW_PLAY_TIMEOUT about 3600).

For every island in Scripts/Setup/world_layout.py, two routes: coast to coast along its longest axis through the middle, and
across it at right angles; each starts and ends 20 m inland of the shore. The survivor walks them by ordinary movement input at
walking speed (no sprint, no teleport along the way), steering for the far end; when it stalls (a cliff, a tree, a building)
it sidesteps at an angle for a few seconds and carries on. Time is game time, with the game run faster (slomo) to save real time.
Per route: minutes, metres walked, straight-line metres, metres climbed, seconds swimming, detours, and whether it arrived.
Writes Saved/WalkingRoutesResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

SLOMO = 4.0
INLAND = 2000.0          # cm: route ends this far inside the shore
ARRIVE = 600.0           # cm: close enough to the end
STALL_EVERY = 2.0        # game seconds between progress checks
STALL_PROGRESS = 100.0   # cm toward the end in that time, or it is stalled
DETOUR = 4.0             # game seconds of sidestepping
GIVE_UP = 30 * 60.0      # game seconds on one route (the target is 15-20 minutes; a route still short at 30 is blocked)

lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
move = pawn.get_movement_component()
survival = pawn.get_survival_component()
report = {'routes': [], 'slomo': SLOMO, 'walk_speed_cm_s': move.get_editor_property('max_walk_speed')}


def centroid(island):
    pts = island.outline(240)
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def reach(island, x, y, angle):
    """From (x, y), how far along angle the land runs (stops INLAND short of the shore), cm."""
    c, s, d = math.cos(angle), math.sin(angle), 0.0
    while island.distance(x + (d + 500) * c, y + (d + 500) * s) < -INLAND:
        d += 500
    return d


def routes():
    out = []
    for island in W.ISLANDS:
        x, y = centroid(island)
        a = max((math.pi * k / 72 for k in range(72)), key=lambda t: reach(island, x, y, t) + reach(island, x, y, t + math.pi))
        for name, angle in (('long axis', a), ('across', a + math.pi / 2)):
            r1, r2 = reach(island, x, y, angle), reach(island, x, y, angle + math.pi)
            c, s = math.cos(angle), math.sin(angle)
            out.append({'island': island.key, 'region': island.region, 'route': name,
                        'start': (x + r1 * c, y + r1 * s), 'end': (x - r2 * c, y - r2 * s)})
    return out


ROUTES = routes()


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 40000), unreal.Vector(x, y, -5000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else 0.0


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


state = {'i': -1, 'h': None, 'route': None}


def begin(i):
    r = ROUTES[i]
    sx, sy = r['start']
    pawn.set_actor_location(unreal.Vector(sx, sy, ground(sx, sy) + 120), False, True)
    move.stop_movement_immediately()
    state.update(i=i, route=dict(r, t0=now(), last=(sx, sy), walked=0.0, climbed=0.0, last_z=None, swim=0.0,
                                 detours=0, check_t=now() + STALL_EVERY, check_d=None, detour_until=0.0, detour_sign=1,
                                 last_t=now(), settle_until=now() + 2.0))


def end_route(arrived):
    r = state['route']
    ex, ey = r['end']
    sx, sy = r['start']
    minutes = (now() - r['t0']) / 60.0
    report['routes'].append({'island': r['island'], 'region': r['region'], 'route': r['route'], 'arrived': arrived,
                             'minutes': round(minutes, 2), 'walked_m': round(r['walked'] / 100.0),
                             'straight_m': round(math.hypot(ex - sx, ey - sy) / 100.0), 'climbed_m': round(r['climbed'] / 100.0),
                             'swim_s': round(r['swim']), 'detours': r['detours']})
    save()


def save(done=False, error=None):
    report.update(finished=done, error=error, success=done and error is None)
    Path(unreal.Paths.project_saved_dir(), 'WalkingRoutesResult.json').write_text(json.dumps(report, indent=2))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    unreal.SystemLibrary.execute_console_command(world, 'slomo 1')
    save(done=True, error=error)
    unreal.log(f'EWWALKING done error={error}')


def tick(delta):
    try:
        if state['i'] < 0:
            unreal.SystemLibrary.execute_console_command(world, f'slomo {SLOMO}')
            unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
            begin(0)
            return
        r = state['route']
        t = now()
        survival.restore_health(1000.0)
        survival.set_hunger(100.0)
        survival.set_hydration(100.0)
        p = pawn.get_actor_location()
        if t < r['settle_until']:
            r['last'] = (p.x, p.y)
            r['last_z'] = p.z
            r['check_d'] = None
            return
        # Distance walked and height climbed (ground contact only; a teleport-sized jump would be a fault, not walking).
        step = math.hypot(p.x - r['last'][0], p.y - r['last'][1])
        if step < 2000:
            r['walked'] += step
            if r['last_z'] is not None and p.z > r['last_z'] and not move.is_falling():
                r['climbed'] += p.z - r['last_z']
        r['last'], r['last_z'] = (p.x, p.y), p.z
        if move.is_swimming():
            r['swim'] += t - r['last_t']
        r['last_t'] = t
        ex, ey = r['end']
        to_end = math.hypot(ex - p.x, ey - p.y)
        if to_end < ARRIVE or t - r['t0'] > GIVE_UP:
            end_route(to_end < ARRIVE)
            if state['i'] + 1 >= len(ROUTES):
                finish()
            else:
                begin(state['i'] + 1)
            return
        # Stalled? Then sidestep at an angle for a while, alternating sides.
        if t >= r['check_t']:
            if r['check_d'] is not None and r['check_d'] - to_end < STALL_PROGRESS and t >= r['detour_until']:
                r['detours'] += 1
                r['detour_sign'] = -r['detour_sign']
                r['detour_until'] = t + DETOUR
            r['check_d'], r['check_t'] = to_end, t + STALL_EVERY
        heading = math.atan2(ey - p.y, ex - p.x)
        if t < r['detour_until']:
            heading += r['detour_sign'] * math.radians(70)
        direction = unreal.Vector(math.cos(heading), math.sin(heading), 0)
        pc.set_control_rotation(unreal.Rotator(0, 0, math.degrees(heading)))
        pawn.add_movement_input(direction, 1.0)
        if move.is_swimming():
            pawn.add_movement_input(unreal.Vector(0, 0, 1), .3)        # keep the head up
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
