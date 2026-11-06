"""Play check: wildlife on every island (November 6), on Lvl_CoastalPlayground, one player.

1. Census: every one of the twenty islands carries land animals; every animal's species belongs to its island's region
   (world_islands.REGION_SPECIES); all seven species added on November 6 are in the world (build_animals.NEW_SPECIES).
2. For one animal of each new species: the survivor is set down about 12 m away, facing it, and watches for up to 25 s.
   It passes when the animal stands on the ground and either walks off (more than 50 cm) or, if aggressive, comes for
   the survivor. The survivor's health is kept full. Two screenshots each, in Saved/Screenshots/Wildlife.
Run with run_play_check.py, one player:
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check verify_wildlife_islands_play.py -Result WildlifeIslandsPlayResult.json
        -Players 1 -Standalone 1 -Timeout 900 -Visible
Writes Saved/WildlifeIslandsPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
from world_islands import REGION_SPECIES  # noqa: E402

NEW_SPECIES = ('Deer', 'Caribou', 'Wolf', 'Hare', 'Snake', 'PolarBear', 'Crocodile')
ROOT = Path(unreal.Paths.project_saved_dir())
RESULT = ROOT / 'WildlifeIslandsPlayResult.json'
SHOTS = ROOT / 'Screenshots' / 'Wildlife'
SHOTS.mkdir(parents=True, exist_ok=True)
WATCH = 25.0

world = next(w for w in unreal.EWEditorVerificationLibrary.get_play_worlds()
             if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
survival = pawn.get_survival_component()
animals = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal))
report = {'map': '/Game/Elitewake/Maps/Lvl_CoastalPlayground', 'success': False, 'error': None, 'species': []}
state = {'i': -1, 'h': None}


def kind(a):
    return a.get_editor_property('definition').get_name().replace('DA_Animal_', '')


def island_of(a):
    words = f" {a.get_actor_label()} "
    return next((i for i in W.ISLANDS if f' {i.key} ' in words), None)


def feet(a):
    return a.get_actor_location().z - a.get_editor_property('body').get_unscaled_sphere_radius()


def ground(x, y, z, ignore=()):
    hit = unreal.SystemLibrary.line_trace_single_for_objects(
        world, unreal.Vector(x, y, z + 400), unreal.Vector(x, y, z - 3000),
        [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], False, list(ignore), unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else None


def census():
    by_island = {i.key: {} for i in W.ISLANDS}
    wrong = []
    for a in animals:
        island = island_of(a)
        if island is None:
            continue
        k = kind(a)
        by_island[island.key][k] = by_island[island.key].get(k, 0) + 1
        if k not in REGION_SPECIES[island.region] and k != 'Spider':     # cave spiders live in caves in every region
            wrong.append((a.get_actor_label(), island.region))
    land = {key: {k: n for k, n in v.items() if k != 'Spider'} for key, v in by_island.items()}
    report.update(animals=len(animals), by_island=by_island, out_of_region=wrong[:10],
                  empty_islands=[k for k, v in land.items() if not v])
    present = {kind(a) for a in animals}
    report['new_species_missing'] = [k for k in NEW_SPECIES if k not in present]
    return not wrong and not report['empty_islands'] and not report['new_species_missing']


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


def shot(r, name):
    path = SHOTS / f"{r['species']}_{name}.png"
    unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{path}"')
    r.setdefault('screenshots', []).append(str(path))


def look_at(target):
    eye = pawn.get_actor_location() + unreal.Vector(0, 0, 60)
    aim = unreal.MathLibrary.find_look_at_rotation(eye, target.get_actor_location())
    pawn.set_actor_rotation(unreal.Rotator(0, 0, aim.yaw), False)
    # The camera sits behind the survivor: look a little to the right of the animal so the survivor does not hide it.
    pc.set_control_rotation(unreal.Rotator(0, max(-30.0, aim.pitch - 8.0), aim.yaw - 14.0))


def begin(i):
    state['i'] = i
    name = NEW_SPECIES[i]
    r = {'species': name, 'success': False}
    report['species'].append(r)
    choices = [a for a in animals if kind(a) == name and not a.is_dead()]
    if not choices:
        r['error'] = 'none in the world'
        state.update(phase='next', until=now() + .2)
        return
    target = choices[len(choices) // 2]
    at = target.get_actor_location()
    r['animal'], r['island'] = target.get_actor_label(), getattr(island_of(target), 'key', None)
    spot = None
    for turn in range(0, 360, 30):                      # find dry, open ground about 12 m away
        x, y = at.x + 1200 * math.cos(math.radians(turn)), at.y + 1200 * math.sin(math.radians(turn))
        g = ground(x, y, at.z, [target])
        if g is not None and g > -40 and abs(g - at.z) < 600:
            spot = (x, y, g)
            break
    if spot is None:
        spot = (at.x + 1200, at.y, at.z + 200)
    pawn.teleport(unreal.Vector(spot[0], spot[1], spot[2] + 110), unreal.Rotator())
    look_at(target)
    g = ground(at.x, at.y, at.z, [target])
    r['feet_above_ground_cm'] = None if g is None else round(feet(target) - g)
    state.update(target=target, phase='settle', until=now() + 2.0, start=at, t0=now(), moved=0.0, closest=1e9,
                 hurt=False)


def end_species():
    r, target = report['species'][-1], state['target']
    aggressive = target.get_editor_property('definition').get_editor_property('aggressive')
    r.update(moved_cm=round(state['moved']), closest_cm=round(state['closest']), came_for_survivor=state['hurt'],
             aggressive=aggressive)
    standing = r['feet_above_ground_cm'] is not None and abs(r['feet_above_ground_cm']) < 40
    lively = state['moved'] > 50 or (aggressive and (state['hurt'] or state['closest'] < 400))
    r['success'] = standing and lively
    if not r['success']:
        r['error'] = 'not standing on the ground' if not standing else 'did not move while watched'
    shot(r, 'after')
    unreal.log(f"EWWILDLIFE {r['species']} {r['animal']}: {'ok' if r['success'] else r['error']}")
    state.update(phase='next', until=now() + 1.0)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report['error'] = error
    report['passed'] = sum(1 for r in report['species'] if r.get('success'))
    report['success'] = error is None and report['census_ok'] and report['passed'] == len(NEW_SPECIES)
    report['finished_utc'] = time.time()
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f"EWPLAYCHECK Wildlife success={report['success']} passed={report['passed']}/{len(NEW_SPECIES)} "
               f"census={report['census_ok']} error={error}")


def tick(delta):
    try:
        if state['i'] < 0:
            unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
            report['census_ok'] = census()
            begin(0)
            return
        t = now()
        if state['phase'] == 'next':
            if t >= state['until']:
                if state['i'] + 1 < len(NEW_SPECIES):
                    begin(state['i'] + 1)
                else:
                    finish()
            return
        if survival:
            if survival.get_health() < 99.0:
                state['hurt'] = True
            survival.restore_health(1000.0)
        target = state['target']
        if state['phase'] == 'settle':
            look_at(target)
            if t >= state['until']:
                shot(report['species'][-1], 'seen')
                state['phase'] = 'watch'
            return
        p = target.get_actor_location()
        state['moved'] = max(state['moved'], math.hypot(p.x - state['start'].x, p.y - state['start'].y))
        state['closest'] = min(state['closest'], (p - pawn.get_actor_location()).length())
        look_at(target)
        if t - state['t0'] > WATCH or (state['moved'] > 300 and t - state['t0'] > 8.0):
            end_species()
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
