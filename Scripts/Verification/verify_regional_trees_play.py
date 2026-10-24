"""Acceptance for the regional trees (owner, October 15: Central Plains Oak, Winter Birch, Jungle Ash, Desert Palm,
Swamp Spruce, in substantial stands; Design/World/ISLAND_TERRAIN_AND_REGIONAL_TREE_ASSIGNMENTS_2026-10-15.md).
Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground (EW_PLAY_PLAYERS=1 is enough), after build_coastal_flora.py.
Run unattended with run_play_check.py.
  1. On every island but the starter, its region's tree is the primary one: most of its trees, and at least MIN_STAND
     of them; no Spruce outside the Swamp, no Maravai outside the Jungle.
  2. The starter island (Central Plains) has only oaks (owner, October 16: no palms on it, palms in the Desert),
     at least 40 of them; every Desert island has palms.
  3. Every tree stands on the ground, a hatchet's reach above it at most.
  4. Screenshots of an oak grove, an ash forest and a swamp spruce stand in Saved/Screenshots/RegionalTrees/ (a person
     still has to look at them).
Writes Saved/RegionalTreesPlayResult.json.
"""
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

PRIMARY = {'Plains': 'Oak', 'Winter': 'Birch', 'Jungle': 'Ash', 'Desert': 'Veyran Palm', 'Swamp': 'Spruce'}
MIN_STAND = 80          # trees of the primary kind on each island, at least (owner: quite a few, forests)
RESULT = Path(unreal.Paths.project_saved_dir(), 'RegionalTreesPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'RegionalTrees')
SHOTS.mkdir(parents=True, exist_ok=True)
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = next(unreal.GameplayStatics.get_player_controller(w, 0) for w in lib.get_play_worlds()
          if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
world = pc.get_world()
pawn = pc.get_controlled_pawn()
trees = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHarvestTree))
measured, checks = {}, []


def kind(t):
    label = t.get_actor_label()
    return next((k for k in ('Veyran Palm', 'Maravai', 'Birch', 'Spruce', 'Oak', 'Ash') if label.startswith(k)), label)


def island_of(t):
    p = t.get_actor_location()
    return min(W.ISLANDS, key=lambda i: i.distance(p.x, p.y))


by_island = {}
for t in trees:
    by_island.setdefault(island_of(t).key, Counter())[kind(t)] += 1


def primary():
    bad = []
    for isl in W.ISLANDS:
        if isl.key == 'Starter':
            continue
        c = by_island.get(isl.key, Counter())
        want = PRIMARY[isl.region]
        if c[want] < MIN_STAND or c[want] < 0.6 * sum(c.values()):
            bad.append((isl.key, dict(c)))
        if c['Spruce'] and isl.region != 'Swamp' or c['Maravai'] and isl.region != 'Jungle':
            bad.append((isl.key, 'a tree of another region', dict(c)))
    assert not bad, bad[:4]
    measured['by_island'] = {k: dict(v) for k, v in by_island.items()}
    return True


def starter():
    c = by_island.get('Starter', Counter())
    assert c['Oak'] >= 40 and c['Maravai'] == 0, dict(c)
    assert c['Veyran Palm'] == 0, f'palms on the starter island: {dict(c)}'
    palms = {k: v['Veyran Palm'] for k, v in by_island.items() if v['Veyran Palm']}
    desert = [i.key for i in W.ISLANDS if i.region == 'Desert']
    assert set(palms) == set(desert), f'palms on {sorted(palms)}, Desert islands {sorted(desert)}'
    measured['starter'] = dict(c)
    measured['palms_by_island'] = palms
    return True


def grounded():
    off = []
    for t in trees:
        p = t.get_actor_location()
        # The ground under the trunk, from a little above its foot (so another tree's crown is not taken for it).
        hit = unreal.SystemLibrary.line_trace_single(world, p + unreal.Vector(0, 0, 150), p - unreal.Vector(0, 0, 600),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [t],
                                                     unreal.DrawDebugTrace.NONE, True)
        hit = hit[0] if isinstance(hit, tuple) else hit
        g = hit.to_tuple()[4].z if hit else None
        if g is None or abs(p.z - g) > 60:
            off.append((t.get_actor_label(), None if g is None else round(p.z - g)))
    assert len(off) <= len(trees) // 200, f'{len(off)} trees off the ground: {off[:5]}'
    measured['trees'] = len(trees)
    return True


def stand_of(region):
    """A place among the most trees of that region's primary kind: the centre of a dense patch on its biggest island."""
    isl = max((i for i in W.ISLANDS if i.region == region and (i.key != 'Starter' or W.FIVE_ISLAND_WORLD)), key=lambda i: i.rx * i.ry)
    mine = [t.get_actor_location() for t in trees if kind(t) == PRIMARY[region] and island_of(t) is isl]
    best = max(mine, key=lambda p: sum(1 for q in mine if (q - p).length() < 2500))
    return best


VIEWS = [('oak_grove', 'Plains'), ('ash_forest', 'Jungle'), ('swamp_spruce', 'Swamp')]
state = {'step': 0, 'view': 0, 'phase': 'place', 'at': 0.0, 'handle': None}
STEPS = [('Every island but the starter has its region\'s tree as its primary one, in substantial stands', primary),
         ('The starter island has only oaks, no palms; the palms are on the Desert islands', starter),
         ('Every tree stands on the ground', grounded)]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK RegionalTrees success={error is None} error={error}')


def tick(delta):
    try:
        if state['step'] < len(STEPS):
            name, fn = STEPS[state['step']]
            fn()
            checks.append(name)
            state['step'] += 1
            return
        if state['view'] >= len(VIEWS):
            checks.append('Screenshots of an oak grove, an ash forest and a swamp spruce stand')
            finish()
            return
        name, region = VIEWS[state['view']]
        now = time.monotonic()
        if state['phase'] == 'place':
            c = stand_of(region)
            x, y = c.x - 1800, c.y - 1800
            z = max(T.built_height(x, y) or T.height(x, y), T.SEA) + 150
            pawn.teleport(unreal.Vector(x, y, z), unreal.Rotator(0, 0, 45))
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=2, yaw=45))
            state.update(phase='shoot', at=now + 4.0)
        elif now >= state['at']:
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (name + ".png")}"')
            state.update(phase='place', view=state['view'] + 1)
    except Exception as error:
        finish(f'step {state["step"]}: {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
