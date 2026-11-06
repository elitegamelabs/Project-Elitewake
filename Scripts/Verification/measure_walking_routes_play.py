"""Walking routes, measured in-game (owner, November 3: keep the current roughly 5-14 minute island scale).
Single player (EW_PLAY_STANDALONE=1, EW_PLAY_PLAYERS=1) on
/Game/Elitewake/Maps/Lvl_CoastalPlayground, run with run_play_check.py (EW_PLAY_TIMEOUT about 3600).

For every island in Scripts/Setup/world_layout.py, two routes: coast to coast along its longest axis through the middle, and
across it at right angles; each starts and ends 20 m inland of the shore. The survivor walks them by ordinary movement input at
walking speed (no sprint, no teleport along the way), steering for the far end; when it stalls (a cliff, a tree, a building)
it hops, then sidesteps at an angle for a few seconds and carries on. In water it presses jump as a player does to climb
out onto a bank (a swimming character never steps up; November 5, the Swamp's channels stopped a walker that did not). It follows the quickest walkable path the offline estimate
finds (Scripts/Setup/estimate_walking_times.py, same routes), a waypoint some 30 m ahead at a time, so a hill it could walk
round does not stop it; the time is still its own, walked in the game. Time is game time, with the game run faster (slomo) to save real time.
Per route: minutes, metres walked, straight-line metres, metres climbed, seconds swimming, detours, and whether it arrived.
Writes the result named by EW_PLAY_RESULT (default: Saved/WalkingRoutesResult.json). Set EW_WALK_ISLAND and
EW_WALK_ROUTE to run one route without rerunning all islands.
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
import estimate_walking_times as E  # noqa: E402

SLOMO = 4.0
INLAND = 2000.0          # cm: route ends this far inside the shore
ARRIVE = 600.0           # cm: close enough to the end
STALL_EVERY = 2.0        # game seconds between progress checks
STALL_PROGRESS = 100.0   # cm toward the end in that time, or it is stalled
DETOUR = 4.0             # game seconds of a detour: a hop straight on (HOP), then sidestepping
HOP = 1.0                # game seconds of hopping straight at whatever stopped it, first
GIVE_UP = float(os.environ.get('EW_WALK_GIVE_UP_MIN', '30')) * 60.0   # game seconds on one route; a long stop is not a successful crossing

lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
move = pawn.get_movement_component()
survival = pawn.get_survival_component()
report = {'routes': [], 'slomo': SLOMO, 'walk_speed_cm_s': move.get_editor_property('max_walk_speed')}


def routes():
    out = []
    for island in W.ISLANDS:
        for name, start, end in E.routes(island):
            out.append({'island': island.key, 'region': island.region, 'route': name, 'start': start, 'end': end})
    return out


LOOKAHEAD = 1            # waypoints ahead of the nearest one: saved paths keep every third mesh vertex, about 10 m apart
# EW_WALK_ROUTES: a comma-separated list of island:route (e.g. "Winter2:across,Swamp1:long axis") to run only those.
_only = [x.split(':', 1) for x in os.environ.get('EW_WALK_ROUTES', '').split(',') if ':' in x]
ROUTES = [r for r in routes() if (not os.environ.get('EW_WALK_ISLAND') or r['island'] == os.environ['EW_WALK_ISLAND'])
          and (not os.environ.get('EW_WALK_ROUTE') or r['route'] == os.environ['EW_WALK_ROUTE'])
          and (not _only or [r['island'], r['route']] in _only)]
if not ROUTES:
    raise ValueError('No walking routes match EW_WALK_ISLAND and EW_WALK_ROUTE')
# The path to follow on each route: from the last full offline estimate (python Scripts/Setup/estimate_walking_times.py,
# on the island mesh's own grid) when the layout and terrain have not changed since; otherwise worked out here (minutes).
SAVED = E.saved_paths()
for r in ROUTES:
    found = (SAVED or {}).get(r['island'], {}).get(r['route'])
    if found:
        r['path'] = [tuple(p) for p in found['path']] or [r['end']]
        r['estimate_min'] = found['minutes']
    else:
        estimate, path = E.walk_time(W.island(r['island']), r['start'], r['end'])
        r['path'] = path or [r['end']]
        r['estimate_min'] = None if estimate is None else round(estimate / 60.0, 1)
    if len(r['path']) > 1:
        # Start and end where the path does: the offline estimate moves a route's ends onto level ground nearby (a raw
        # end 20 m inland can lie on a cliff's lip, and on November 5 a survivor set down there slid off into the sea).
        r['start'], r['end'] = tuple(r['path'][0]), tuple(r['path'][-1])
report['paths_from'] = 'saved offline estimate' if SAVED else 'worked out in the editor'


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
    ex, ey = r['end']
    state.update(i=i, route=dict(r, t0=now(), last=(sx, sy), walked=0.0, climbed=0.0, last_z=None, swim=0.0,
                                 start_terrain_cm=T.built_height(sx, sy), end_terrain_cm=T.built_height(ex, ey),
                                 detours=0, waypoint=0, check_t=now() + STALL_EVERY, check_d=None, detour_until=0.0, detour_sign=1,
                                 last_t=now(), settle_until=now() + 2.0))


def note_stall(r, p):
    """Where the walker stalled, how far along its path, and what stands in front of it (a knee-high and a chest-high
    trace 1.5 m ahead along the path), so a stuck route says why."""
    path, k = r['path'], r['waypoint']
    tx, ty = path[min(k + LOOKAHEAD, len(path) - 1)] if path else r['end']
    heading = math.atan2(ty - p.y, tx - p.x)
    ahead = []
    for lift in (40.0, 120.0):
        a = unreal.Vector(p.x, p.y, p.z - 50 + lift)
        b = unreal.Vector(p.x + 150 * math.cos(heading), p.y + 150 * math.sin(heading), a.z)
        hit = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn],
                                                     unreal.DrawDebugTrace.NONE, True)
        if hit:
            t = hit.to_tuple()
            actor = t[9]
            ahead.append(actor.get_actor_label() if actor else '?')
        else:
            ahead.append(None)
    r.setdefault('stalls', []).append({'at_m': [round(p.x / 100), round(p.y / 100), round(p.z / 100)],
                                       'along': round(k / max(1, len(path) - 1), 2), 'ahead_knee': ahead[0], 'ahead_chest': ahead[1],
                                       'ground_ahead_m': round((T.built_height(p.x + 150 * math.cos(heading), p.y + 150 * math.sin(heading)) - p.z) / 100, 1)})


def end_route(arrived):
    r = state['route']
    ex, ey = r['end']
    sx, sy = r['start']
    minutes = (now() - r['t0']) / 60.0
    dry_endpoints = r['start_terrain_cm'] >= T.SEA and r['end_terrain_cm'] >= T.SEA
    on_foot = arrived and dry_endpoints and r['swim'] < 0.5
    report['routes'].append({'island': r['island'], 'region': r['region'], 'route': r['route'], 'arrived': arrived,
                             'dry_endpoints': dry_endpoints, 'on_foot': on_foot,
                             'meets_crossing_target': on_foot and E.TARGET_MINUTES[0] <= minutes <= E.TARGET_MINUTES[1],
                             'start_terrain_cm': round(r['start_terrain_cm'], 1),
                             'end_terrain_cm': round(r['end_terrain_cm'], 1), 'sea_cm': T.SEA,
                             'minutes': round(minutes, 2), 'walked_m': round(r['walked'] / 100.0),
                             'straight_m': round(math.hypot(ex - sx, ey - sy) / 100.0), 'climbed_m': round(r['climbed'] / 100.0),
                             'swim_s': round(r['swim']), 'detours': r['detours'], 'estimate_min': r['estimate_min'],
                             'stalls': r.get('stalls', [])[:12] + r.get('stalls', [])[-6:] if len(r.get('stalls', [])) > 18 else r.get('stalls', [])})
    unreal.log(f"EWWALKROUTE {r['island']} {r['route']}: {'arrived' if arrived else 'did not arrive'} in {minutes:.1f} min, "
               f"{'on foot' if on_foot else 'swam ' + str(round(r['swim'])) + ' s'}")
    save()


def save(done=False, error=None):
    failed = [f"{r['island']} {r['route']}: crossing target not met" for r in report['routes']
              if not r['meets_crossing_target']] if done else []
    report.update(finished=done, error=error, errors=failed,
                  success=done and error is None and not failed)
    Path(unreal.Paths.project_saved_dir(), os.environ.get('EW_PLAY_RESULT', 'WalkingRoutesResult.json')).write_text(
        json.dumps(report, indent=2))


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
        # Advance along the walkable route before judging progress. A winding path can temporarily
        # lead away from the far shore; straight-line distance to that shore is not a stall signal.
        path = r['path']
        k = r['waypoint']
        while k + 1 < len(path) and math.hypot(path[k + 1][0] - p.x, path[k + 1][1] - p.y) <= math.hypot(path[k][0] - p.x, path[k][1] - p.y):
            k += 1
        r['waypoint'] = k
        target = min(k + LOOKAHEAD, len(path) - 1)
        remaining = math.hypot(path[target][0] - p.x, path[target][1] - p.y)
        remaining += sum(math.hypot(path[j + 1][0] - path[j][0], path[j + 1][1] - path[j][1])
                         for j in range(target, len(path) - 1))
        # Stalled? Then sidestep at an angle for a while, alternating sides.
        if t >= r['check_t']:
            if r['check_d'] is not None and r['check_d'] - remaining < STALL_PROGRESS and t >= r['detour_until']:
                r['detours'] += 1
                note_stall(r, p)
                r['detour_sign'] = -r['detour_sign']
                r['detour_until'] = t + DETOUR
            r['check_d'], r['check_t'] = remaining, t + STALL_EVERY
        tx, ty = path[target] if k + 1 < len(path) else (ex, ey)
        heading = math.atan2(ty - p.y, tx - p.x)
        hopping = t < r['detour_until'] and r['detour_until'] - t > DETOUR - HOP
        if t < r['detour_until'] and not hopping:
            heading += r['detour_sign'] * math.radians(70)
        direction = unreal.Vector(math.cos(heading), math.sin(heading), 0)
        pc.set_control_rotation(unreal.Rotator(0, 0, math.degrees(heading)))
        pawn.add_movement_input(direction, 1.0)
        if move.is_swimming():
            pawn.add_movement_input(unreal.Vector(0, 0, 1), .3)        # keep the head up
            pawn.jump()          # as a player does to climb out onto a bank (a swimming character never steps up)
        elif hopping:
            pawn.jump()          # a stalled player first hops straight at the ledge, then goes round it
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
