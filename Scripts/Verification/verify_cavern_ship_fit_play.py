"""Play check: the brigantine, the biggest ship built today, fits each sea cavern and is hidden from the sea when parked.

On Lvl_CoastalPlayground in Play (one player; nothing is spawned or moved), for each cavern in
world_layout.SEA_CAVERN_ACCESS:
  1. Entry: the brigantine's own hull collision box (DA_Ship_Brigantine HullExtent, keel at the waterline less its
     draft) is swept from 90 m off the mouth along the passage's centre line (world_terrain.Cave.centre_v), then eased
     into the berth (Cave.berth), and a 50 cm square column from her deck to the top of her tallest mast with it (her
     rigging has no collision, so this is the overhead clearance). Any blocking hit fails.
  2. Turning: at the berth, the hull box is tested every 15 degrees through a half turn, so she can leave bow first;
     any overlap fails.
  3. Concealment: from up to 246 viewpoints on the open water before the mouth (150, 300 and 600 m out, 3 m and 20 m above
     the sea, every 4 degrees across 160), sight lines to her hull ends, middle and masthead in the berth. A clear line to the
     hull fails; a clear line to the masthead only is reported.
The Cavalier is not built; its fit stays pending (CLAUDE.md 5.5). Writes Saved/CavernShipFitPlayResult.json.
"""
import json
import math
import sys
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

RESULT = Path(unreal.Paths.project_saved_dir(), 'CavernShipFitPlayResult.json')
MAST = 1850.0 + 50.0   # cm above her deck: the mainsail assembly, her tallest (build_brigantine.py)
world = next(w for w in unreal.EWEditorVerificationLibrary.get_play_worlds()
             if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pawn = unreal.GameplayStatics.get_player_controller(world, 0).get_controlled_pawn()
definition = unreal.load_asset('/Game/Elitewake/Ships/DA_Ship_Brigantine')
hull = definition.get_editor_property('hull_extent')
deck = definition.get_editor_property('deck_height')
draft = definition.get_editor_property('hull_draft')
CHANNEL = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1      # Visibility
report = {'map': '/Game/Elitewake/Maps/Lvl_CoastalPlayground', 'ship': 'Brigantine',
          'hull_half_extent_cm': [round(hull.x), round(hull.y), round(hull.z)], 'draft_cm': round(draft),
          'mast_top_above_water_cm': round(deck + MAST), 'cavalier': 'not built; fit pending', 'caverns': {}}


def label(hit):
    actor = hit.to_tuple()[9]
    return actor.get_actor_label() if actor else '?'


def sweep(a, b, half, yaw, z):
    hit = unreal.SystemLibrary.box_trace_single(
        world, unreal.Vector(a[0], a[1], z), unreal.Vector(b[0], b[1], z), half, unreal.Rotator(0, 0, yaw), CHANNEL,
        False, [pawn], unreal.DrawDebugTrace.NONE, True)
    return hit


def check(key):
    cave = T.CAVES[key]
    out = {'access': W.SEA_CAVERN_ACCESS[key], 'blocked': [], 'turn_blocked': [], 'hull_seen_from': [],
           'masthead_seen_from': []}
    # Keel at -draft below the waterline: the box spans keel to deck.
    hull_half = unreal.Vector(hull.x, hull.y, (deck + draft) / 2)
    hull_z = T.SEA + (deck - draft) / 2
    mast_half = unreal.Vector(25, 25, MAST / 2)
    mast_z = T.SEA + deck + MAST / 2
    bu, bv = cave.berth()
    local = [(u, cave.centre_v(max(0.0, u))) for u in range(-9000, int(cave.length) + 1, 150)]
    for i in range(1, 13):                                 # eased across into the berth, level at both ends
        t = i / 12
        local.append((cave.length + (bu - cave.length) * t, bv * t * t * (3 - 2 * t)))
    pts = [cave.world(u, v) for u, v in local]
    for a, b in zip(pts, pts[1:]):
        yaw = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        # The hull's ends lead and trail the point by hull.x: sweep the box centred on the path.
        for part, half, z in (('hull', hull_half, hull_z), ('mast', mast_half, mast_z)):
            hit = sweep(a, b, half, yaw, z)
            if hit:
                u, v = cave.local(*a)
                out['blocked'].append({'part': part, 'metres_in': round(u / 100), 'against': label(hit)})
    out['entry_clear'] = not out['blocked']
    berth = cave.world(bu, bv)
    for turn in range(0, 181, 15):
        yaw = math.degrees(cave.heading) + turn
        hit = sweep(berth, (berth[0] + 1, berth[1]), hull_half, yaw, hull_z)
        if hit:
            out['turn_blocked'].append({'degrees': turn, 'against': label(hit)})
    out['turns_in_berth'] = not out['turn_blocked']
    # Concealment.
    c, s = math.cos(cave.heading), math.sin(cave.heading)
    targets = {'bow': (berth[0] + c * hull.x * .9, berth[1] + s * hull.x * .9, T.SEA + deck),
               'stern': (berth[0] - c * hull.x * .9, berth[1] - s * hull.x * .9, T.SEA + deck),
               'middle': (berth[0], berth[1], T.SEA + deck + 200), 'masthead': (berth[0], berth[1], T.SEA + deck + MAST)}
    views = 0
    for distance in (15000.0, 30000.0, 60000.0):
        for height in (300.0, 2000.0):
            for angle in range(-80, 81, 4):
                a = cave.heading + math.pi + math.radians(angle)
                x, y = cave.mx + distance * math.cos(a), cave.my + distance * math.sin(a)
                if T.built_height(x, y) > T.SEA - 100.0:
                    continue                          # land, not open water
                views += 1
                eye = unreal.Vector(x, y, T.SEA + height)
                for name, (tx, ty, tz) in targets.items():
                    hit = unreal.SystemLibrary.line_trace_single(world, eye, unreal.Vector(tx, ty, tz), CHANNEL, False,
                                                                 [pawn], unreal.DrawDebugTrace.NONE, True)
                    if hit:
                        loc = hit.to_tuple()[4]
                        if math.dist((loc.x, loc.y, loc.z), (tx, ty, tz)) > 300.0:
                            continue                  # stopped well short: hidden
                    seen = {'metres_out': round(distance / 100), 'eye_m': round(height / 100), 'degrees': angle,
                            'target': name}
                    (out['masthead_seen_from'] if name == 'masthead' else out['hull_seen_from']).append(seen)
    out['viewpoints'] = views
    out['hidden_from_sea'] = not out['hull_seen_from']
    out['success'] = out['entry_clear'] and out['turns_in_berth'] and out['hidden_from_sea']
    for k in ('blocked', 'turn_blocked', 'hull_seen_from', 'masthead_seen_from'):
        out[f'{k}_count'] = len(out[k])
        out[k] = out[k][:20]
    return out


try:
    for key in W.SEA_CAVERN_ACCESS:
        report['caverns'][key] = check(key)
    report['success'] = all(r['success'] for r in report['caverns'].values())
    report['error'] = None
except Exception as error:
    report.update(success=False, error=repr(error))
RESULT.write_text(json.dumps(report, indent=2))
unreal.log(f'EWPLAYCHECK CavernShipFit success={report["success"]} error={report["error"]}')
