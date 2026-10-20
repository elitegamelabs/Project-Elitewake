"""Two-player collision acceptance for the glazed cabin windows on Schooner and Brigantine."""
import json
import math
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ShipWindowsPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
host_pc = next(c for c in pcs if c.has_authority())
server = host_pc.get_world()
ships = unreal.GameplayStatics.get_all_actors_of_class(server, unreal.EWShip)


def by_id(ship_id):
    return next(s for s in ships if str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id)


def point(ship, xyz):
    return ship.get_actor_transform().transform_location(unreal.Vector(*xyz))


def trace_label(a, b):
    hit = unreal.SystemLibrary.line_trace_single(server, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                                 [], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[9].get_actor_label() if hit else None


def sealed_window(ship, tag, exterior, interior):
    a, b = point(ship, exterior), point(ship, interior)
    label = trace_label(a, b)
    assert label == ship.get_actor_label(), f'{tag}: pane did not block the complex visibility trace ({label})'
    return {'window': tag, 'hit_actor': label, 'trace_length_cm': round(math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2), 1)}


checks = []
schooner = by_id('Schooner')
brig = by_id('Brigantine')

# Schooner side-light panes: (-900,-980), z 355..400; half-beam is about 200 cm at these stations.
for x in (-900.0, -980.0):
    for side in (-1, 1):
        checks.append(sealed_window(schooner, f'Schooner side {x:g} {side:+d}',
                                    (x, side * 300.0, 377.5), (x, 0.0, 377.5)))
# Schooner aft-quarterdeck bulkhead lights, facing the main deck at x=-825.
for y in (-130.0, 130.0):
    checks.append(sealed_window(schooner, f'Schooner quarterdeck front {y:+g}',
                                (-750.0, y, 377.5), (-890.0, y, 377.5)))

# Brigantine raised cabin and forecastle: side panes use 400..450; front panes sit at deck+95..140.
for x in (-1000.0, -1130.0, -1260.0, 1150.0, 1260.0):
    for side in (-1, 1):
        checks.append(sealed_window(brig, f'Brigantine side {x:g} {side:+d}',
                                    (x, side * 520.0, 425.0), (x, 0.0, 425.0)))
for y in (-130.0, 130.0):
    checks.append(sealed_window(brig, f'Brigantine quarterdeck front {y:+g}',
                                (-800.0, y, 417.5), (-1050.0, y, 417.5)))
    checks.append(sealed_window(brig, f'Brigantine forecastle front {y:+g}',
                                (1000.0, y, 417.5), (1120.0, y, 417.5)))

assert len(checks) == 20, len(checks)
RESULT.write_text(json.dumps({'success': True, 'checks': checks}, indent=2))
