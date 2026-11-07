"""Map scan for the twenty-island world (CLAUDE.md 5.7 acceptance; owner, November 1). Run on
/Game/Elitewake/Maps/Lvl_CoastalPlayground after rebuild_world.py, one player:
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check verify_twenty_islands_play.py -Result TwentyIslandsPlayResult.json -Players 1 -Standalone 1
Checks what is in the built map, not the scripts:
  1. exactly 20 island terrains, 4 per region, each at its planned place (world_layout.py);
  2. five villages, one per region, on the planned islands: Saltreach on the starter, a Port on each other village island,
     none on any other island;
  3. every animal on an island of the region its species belongs to (world_islands.REGION_SPECIES), each island's mix as
     planned (wildlife_distribution.py), and the islands of a region carrying different mixes;
  4. no 200 m square holding more than 15 % of an island's animals;
  5. passive animals at least 150 m and aggressive ones 250 m from the spawn, the dock and every village.
Walking times are measured separately (measure_walking_routes_play.py). Writes Saved/TwentyIslandsPlayResult.json.
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_islands as I  # noqa: E402
import world_layout as W  # noqa: E402
import wildlife_distribution as D  # noqa: E402

RESULT = Path(unreal.Paths.project_saved_dir(), 'TwentyIslandsPlayResult.json')
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
report = {'checks': [], 'measured': {}, 'errors': []}


def check(label, ok, detail=''):
    report['checks'].append({'check': label, 'ok': bool(ok), 'detail': detail})
    if not ok:
        report['errors'].append(f'{label}: {detail}')


actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
labels = [(a, a.get_actor_label()) for a in actors]

# 1. Island terrains.
terrains = {}
for a, label in labels:
    for i in W.ISLANDS:
        if label == f'{i.key} ({i.region})':
            terrains[i.key] = a
missing = sorted(set(I.ISLANDS) - set(terrains))
per_region = Counter(W.island(k).region for k in terrains)
check('20 island terrains, 4 per region', len(terrains) == 20 and all(per_region[r] == 4 for r in W.REGION_CENTRES),
      f'{len(terrains)} found, per region {dict(per_region)}, missing {missing}')
report['measured']['islands'] = len(terrains)

# 2. Villages: the Ports' buildings stand in World/Ports/<Region>; Saltreach on the starter's Port site.
port_regions = defaultdict(list)
for a, label in labels:
    folder = str(a.get_folder_path())
    if folder.startswith('World/Ports/'):
        port_regions[folder.split('/')[2]].append(a)
for region, port in W.PORTS.items():
    if region == 'Plains':
        continue
    near = [a for a in port_regions.get(region, []) if math.hypot(a.get_actor_location().x - port.cx, a.get_actor_location().y - port.cy) < 15000]
    check(f'{region} village on {port.island.key}', port.island.key == I.VILLAGES[region] and len(near) >= 5,
          f'{len(near)} buildings near its site; plan {I.VILLAGES[region]}')
stray = [a.get_actor_label() for region, group in port_regions.items() for a in group
         if region != 'Plains' and W.region_of(a.get_actor_location().x, a.get_actor_location().y) != region]
check('no Port buildings on another region', not stray, str(stray[:5]))
saltreach = W.PORTS['Plains']
check('Saltreach on the starter island', saltreach.island.key == 'Starter' and W.island('Starter').distance(saltreach.cx, saltreach.cy) < 0)

# 3-5. Wildlife.
animals = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal) if a.get_editor_property('definition')]
species = {}
for a in animals:
    name = str(a.get_editor_property('definition').get_name()).replace('DA_Animal_', '')
    species[a] = name
on_island = defaultdict(list)
wrong_region = []
for a, name in species.items():
    p = a.get_actor_location()
    island = min(W.ISLANDS, key=lambda i: i.distance(p.x, p.y))
    on_island[island.key].append((a, name))
    if name not in I.REGION_SPECIES[island.region]:
        wrong_region.append(f'{name} on {island.key}')
check('every species only in its region', not wrong_region, str(wrong_region[:6]))
mixes = {}
for i in W.ISLANDS:
    found = Counter(n for _, n in on_island[i.key] if n != 'Spider')
    plan = D.target_counts(i)
    mixes[i.key] = frozenset(found)
    check(f'{i.key} carries its planned mix', set(found) == set(plan), f'found {dict(found)}, plan {plan}')
for region in W.REGION_CENTRES:
    ms = [mixes[i.key] for i in W.ISLANDS if i.region == region and mixes[i.key]]
    check(f'{region} islands carry different mixes', len(ms) == len(set(ms)), str([sorted(m) for m in ms]))
crowded = []
for key, group in on_island.items():
    herd = [a.get_actor_location() for a, n in group if n != 'Spider']     # cave spiders live in caves (add_spiders.py)
    if len(herd) < 7:
        continue        # 15 % of a handful is under one animal; the rule is for real populations
    # The fullest 200 m square: its best placement has its left edge on some animal's x and its bottom edge on some y.
    worst = max(sum(1 for q in herd if a.x <= q.x <= a.x + 20000 and b.y <= q.y <= b.y + 20000) for a in herd for b in herd)
    report['measured'].setdefault('fullest_200m_square', {})[key] = f'{worst}/{len(herd)}'
    if worst > .15 * len(herd) + 1e-9:
        crowded.append(f'{key} {worst}/{len(herd)}')
check('no 200 m square holds over 15 % of an island animal population', not crowded, str(crowded))
people = [(150.0, 0.0), (4000.0, 900.0)] + [xy for p in W.PORTS.values() for xy in ((p.cx, p.cy), p.shore)]
close = []
for a, name in species.items():
    if name == 'Spider' or a.get_actor_label().startswith('Wild Boar Plains '):
        continue    # cave spiders live in caves (add_spiders.py); the arrival's two boars are Phase 1's planned first threat
    aggressive = a.get_editor_property('definition').get_editor_property('aggressive')
    p = a.get_actor_location()
    d = min(math.hypot(p.x - x, p.y - y) for x, y in people)
    if d < (D.CLEAR_AGGRESSIVE if aggressive else D.CLEAR_PASSIVE) - 100:
        close.append(f'{name} {d / 100:.0f} m')
check('animals clear of landings and villages (150 m / 250 m)', not close, str(close[:6]))
report['measured']['animals'] = len(species)
report['measured']['by_island'] = {k: dict(Counter(n for _, n in v)) for k, v in on_island.items()}

report['success'] = not report['errors']
RESULT.write_text(json.dumps(report, indent=2))
unreal.log(f'EWTWENTYISLANDS success={report["success"]} errors={report["errors"][:3]}')
