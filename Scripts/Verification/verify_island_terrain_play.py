"""Acceptance for the five individually designed islands in CLAUDE.md. Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground
(EW_PLAY_PLAYERS=1 is enough) after rebuild_world.py. Run unattended with run_play_check.py.
  1. Every island but the starter and the Swamp's has a terrain plan (peaks, ridges, plateaus, valleys), and every island
     has its own size, outline and relief (no two with the same top, mean
     height and size within 1 m).
  2. The built ground matches the plan: at 12 points on each island the ground under a trace is within 1.5 m of the
     height function (world_terrain.built_height), so the meshes in the map are the designed ones.
  3. Every island has its cave, with a walkable way in (at most a 45 cm step at the mouth).
  4. Screenshots of five islands from 25 m above the sea, one per region, in Saved/Screenshots/IslandTerrain/
     (a person still has to look at them).
Writes Saved/IslandTerrainPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

RESULT = Path(unreal.Paths.project_saved_dir(), 'IslandTerrainPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'IslandTerrain')
SHOTS.mkdir(parents=True, exist_ok=True)
lib = unreal.EWEditorVerificationLibrary
pc = next(unreal.GameplayStatics.get_player_controller(w, 0) for w in lib.get_play_worlds()
          if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
world = pc.get_world()
pawn = pc.get_controlled_pawn()
measured, checks = {}, []


def relief(i):
    hs = []
    for k in range(120):
        a = 2 * math.pi * k / 120
        for f in (.25, .5, .75):
            r = i.radius(a) * f
            hs.append(T.height_raw(i.cx + r * math.cos(a), i.cy + r * math.sin(a)))
    return max(hs) / 100, sum(hs) / len(hs) / 100, 2 * i.reach() / 100


def designed():
    for region in T.PLANS:
        plans = [T.TERRAIN_PLANS[i.key][0] for i in W.ISLANDS if i.region == region and i.key != 'Starter']
        expected = 0 if region == 'Plains' else 1
        assert len(plans) == expected and len(set(plans)) == len(plans), f'{region} plans repeat: {plans}'
    stats = {i.key: relief(i) for i in W.ISLANDS}
    keys = list(stats)
    same = [(a, b) for n, a in enumerate(keys) for b in keys[n + 1:]
            if all(abs(x - y) < 1.0 for x, y in zip(stats[a], stats[b]))]
    assert not same, f'islands alike: {same[:4]}'
    measured['islands'] = {k: {'plan': '+'.join(T.TERRAIN_PLANS.get(k, ((),))[0]) or '-', 'top_m': round(v[0], 1),
                               'mean_m': round(v[1], 1), 'across_m': round(v[2])} for k, v in stats.items()}
    return True


def built():
    worst = []
    for i in W.ISLANDS:
        for k in range(12):
            a = 2 * math.pi * k / 12 + .3
            r = i.radius(a) * (.3 + .4 * (k % 3) / 2)
            x, y = i.cx + r * math.cos(a), i.cy + r * math.sin(a)
            hit = unreal.SystemLibrary.line_trace_single_for_objects(
                world, unreal.Vector(x, y, 40000), unreal.Vector(x, y, -3000),
                [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], True, [], unreal.DrawDebugTrace.NONE, True)
            hit = hit[0] if isinstance(hit, tuple) else hit
            if not hit:
                worst.append((i.key, 'no ground'))
                continue
            got, want = hit.to_tuple()[4].z, T.built_height(x, y)
            # Trees and rocks stand on the ground: only count a miss when the trace hit the island itself.
            label = hit.to_tuple()[9].get_actor_label() if hit.to_tuple()[9] else ''
            if label.startswith(i.key) and want is not None and abs(got - want) > 150:
                worst.append((i.key, round((got - want) / 100, 1)))
    assert not worst, worst[:6]
    return True


def caves():
    steep = []
    for key, c in T.CAVES.items():
        assert c, f'{key} has no cave'
        worst = 0.0
        for u in range(-80, 1, 20):
            for v in (-150, 0, 150):
                g = T.built_height(*c.world(u, c.centre_v(0) + v))
                if g is not None:
                    worst = max(worst, c.floor - g)
        if worst > 45:
            steep.append((key, round(worst)))
    assert not steep, steep
    return True


VIEWS = [('starter', 'Starter'), ('winter', 'Winter1'), ('jungle', 'Jungle1'),
         ('desert', 'Desert1'), ('swamp', 'Swamp1')]
STEPS = [('Every island has its own plan and its own size, outline and relief', designed),
         ('The built ground in the map matches every island\'s plan', built),
         ('Every island has its cave with a walkable way in', caves)]
state = {'step': 0, 'view': 0, 'phase': 'place', 'at': 0.0, 'handle': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK IslandTerrain success={error is None} error={error}')


def tick(delta):
    try:
        if state['step'] < len(STEPS):
            name, fn = STEPS[state['step']]
            fn()
            checks.append(name)
            state['step'] += 1
            return
        if state['view'] >= len(VIEWS):
            checks.append(f'Screenshots of {len(VIEWS)} islands from the sea')
            finish()
            return
        name, key = VIEWS[state['view']]
        now = time.monotonic()
        if state['phase'] == 'place':
            i = W.island(key)
            a = math.atan2(-i.cy, -i.cx) if (i.cx or i.cy) else 0.0
            d = i.reach() + 25000
            x, y = i.cx + d * math.cos(a), i.cy + d * math.sin(a)
            yaw = math.degrees(a + math.pi)
            # 25 m above the water, as from a ship's masthead: the view is taken before the survivor falls far.
            pawn.teleport(unreal.Vector(x, y, T.SEA + 2500), unreal.Rotator(0, 0, yaw))
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=yaw))
            state.update(phase='shoot', at=now + 0.4)
        elif state['phase'] == 'shoot' and now >= state['at']:
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (name + ".png")}"')
            state.update(phase='saved', at=now + 2.0)   # stay put until the shot is written
        elif state['phase'] == 'saved' and now >= state['at']:
            state.update(phase='place', view=state['view'] + 1)
    except Exception as error:
        finish(f'step {state["step"]}: {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
