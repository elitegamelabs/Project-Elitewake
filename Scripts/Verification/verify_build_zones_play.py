"""Build Mode zones (single-player Play session). Owner, October 26-27: build on every island outside Ports and obstruction
zones; beaches near docks are not buildable. Checks UEWBuildZones (the game's rule) against world_buildzones.py (the layout's):
  1. the zone list loaded (the same number of zones as the layout makes);
  2. at 80 sample points on every island the game and the layout agree on whether a piece may stand there (the built ground
     is within 1.5 m of the layout's, so a point right on a limit may differ: at most 4 % do);
  3. every Port's middle, its waterfront, and open water are refused, and each says why;
  4. every island has ground where a 4 m footprint may be built, with nothing in the way.
Writes Saved/BuildZonesPlayResult.json."""
import json
import math
import random
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_buildzones as B  # noqa: E402
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
Z = unreal.EWBuildZones
state = {'at': time.monotonic() + 12, 'handle': None}
report = {'checks': []}


def note(label, **values):
    report['checks'].append({'label': label, **values})
    unreal.log(f'BuildZones: {label} {values}')


def run():
    assert Z.get_zone_count() == len(B.ZONES), f'game loaded {Z.get_zone_count()} zones, layout has {len(B.ZONES)}'
    note('zones loaded', count=Z.get_zone_count())
    rng = random.Random(7)
    total = mismatch = 0
    for isle in W.ISLANDS:
        island_mismatch, found = [], 0
        for _ in range(80):
            a = rng.random() * 2 * math.pi
            d = rng.random() * isle.radius(a)
            x, y = isle.cx + d * math.cos(a), isle.cy + d * math.sin(a)
            game = Z.check_point(world, x, y)
            layout = B.point_reason(x, y)
            total += 1
            if bool(game) != bool(layout):
                mismatch += 1
                island_mismatch.append((round(x), round(y), game, layout))
        note(f'{isle.key}: agreement', mismatches=len(island_mismatch), sample=island_mismatch[:3])
        # a place where a 4 m footprint is allowed
        for _ in range(300):
            a = rng.random() * 2 * math.pi
            d = rng.random() * isle.radius(a) * .9
            x, y = isle.cx + d * math.cos(a), isle.cy + d * math.sin(a)
            if B.footprint_reason(x, y, 200, 200, 0) is None and not Z.check_footprint(world, x, y, 200, 200, 0):
                found += 1
                break
        note(f'{isle.key}: buildable footprint found', found=found)
        assert found, f'{isle.key} has nowhere a 4 m footprint may be built'
    note('agreement overall', total=total, mismatches=mismatch)
    assert mismatch <= total * .04, f'{mismatch} of {total} points disagree'
    for region, p in W.PORTS.items():
        for label, (x, y) in (('middle', (p.cx, p.cy)), ('waterfront', p.world(W.PORT_INLAND + 3000.0, 0.0))):
            why = str(Z.check_point(world, x, y))
            note(f'{region} Port {label}', why=why)
            assert why, f'{region} Port {label} is buildable'
    why = str(Z.check_point(world, 0.0, -60000.0))
    note('open water', why=why)
    assert why, 'open water is buildable'


def tick(delta):
    if time.monotonic() < state['at']:
        return
    unreal.unregister_slate_post_tick_callback(state['handle'])
    error = None
    try:
        run()
    except Exception as exc:
        error = repr(exc)
    report.update(success=error is None, error=error)
    (saved / 'BuildZonesPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK BuildZones success={error is None} error={error}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
