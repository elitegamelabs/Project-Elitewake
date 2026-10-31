"""Two-player collision acceptance for the glazed cabin windows on Schooner and Brigantine."""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import build_brigantine as brigantine  # noqa: E402
import build_schooner as schooner_builder  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ShipWindowsPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
host_pc = next(c for c in pcs if c.has_authority())
server = host_pc.get_world()


def by_id(world, ship_id):
    return next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
                if str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id)


def point(ship, xyz):
    return ship.get_actor_transform().transform_location(unreal.Vector(*xyz))


def trace(world, a, b):
    # Hull visuals intentionally ignore Visibility; trace the WorldDynamic object type instead.
    return unreal.SystemLibrary.line_trace_single_for_objects(
        world, a, b, [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2], True, [], unreal.DrawDebugTrace.NONE, True)


def sealed_window(world, ship, tag, exterior, interior, expected_local):
    a, b = point(ship, exterior), point(ship, interior)
    hit = trace(world, a, b)
    label = hit.to_tuple()[9].get_actor_label() if hit else None
    assert label == ship.get_actor_label(), f'{tag}: pane did not block the complex visibility trace ({label})'
    impact = ship.get_actor_transform().inverse_transform_location(hit.to_tuple()[4])
    delta = math.sqrt((impact.x - expected_local[0]) ** 2 + (impact.y - expected_local[1]) ** 2
                      + (impact.z - expected_local[2]) ** 2)
    assert delta <= 12.0, f'{tag}: trace hit an unrelated part of the same ship at {impact}, expected pane at {expected_local}'
    return {'window': tag, 'hit_actor': label, 'impact_local': [round(impact.x, 1), round(impact.y, 1), round(impact.z, 1)],
            'pane_offset_cm': round(delta, 1)}


checks = []
mesh_paths = {'Schooner': '/Game/Elitewake/World/Ships/SM_SchoonerHull_Windowed_v1',
              'Brigantine': '/Game/Elitewake/World/Ships/SM_BrigantineHull_Windowed_v1'}
for world in worlds:
    role = 'server' if world == server else 'client'
    schooner = by_id(world, 'Schooner')
    brig = by_id(world, 'Brigantine')
    for ship, ship_id in ((schooner, 'Schooner'), (brig, 'Brigantine')):
        mesh = unreal.load_asset(mesh_paths[ship_id])
        assert mesh, f'Run rebuild_sealed_ship_windows.py first; missing {mesh_paths[ship_id]}'
        visual = next(c for c in ship.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == 'HullVisual')
        visual.set_static_mesh(mesh)  # PIE-only assignment while the existing DataAsset file remains externally locked
        visual.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)

    # Schooner side-light panes: (-900,-980), z 355..400.
    for x in (-900.0, -980.0):
        y_out = schooner_builder.HULL.half_beam(x) + 1.0
        for side in (-1, 1):
            checks.append(sealed_window(world, schooner, f'{role} Schooner side {x:g} {side:+d}',
                                        (x, side * 300.0, 377.5), (x, 0.0, 377.5), (x, side * y_out, 377.5)))
    # The reworked schooner (October 18) has side lights only; its quarters front has a doorway and no window panes, so no front pane is traced.

    # Brigantine captain's quarters (October 20 rebuild: no forecastle): side panes at the builder's CABIN_WINDOWS
    # (z 400..450); front panes at deck+95..140 in the wall at QUARTERDECK's front edge.
    for x in brigantine.CABIN_WINDOWS:
        y_out = brigantine.HULL.half_beam(x) + 1.0
        for side in (-1, 1):
            checks.append(sealed_window(world, brig, f'{role} Brigantine side {x:g} {side:+d}',
                                        (x, side * 520.0, 425.0), (x, 0.0, 425.0), (x, side * y_out, 425.0)))
    front = brigantine.QUARTERDECK[0]
    for y in (-130.0, 130.0):
        checks.append(sealed_window(world, brig, f'{role} Brigantine quarterdeck front {y:+g}',
                                    (front + 100.0, y, 417.5), (front - 150.0, y, 417.5), (front + 4.0, y, 417.5)))

assert len(checks) == 24, len(checks)   # 2 roles x (schooner 4 + brigantine 8)
RESULT.write_text(json.dumps({'success': True, 'checks': checks,
                              'note': 'Generated mesh assets were assigned to HullVisual components in PIE only; map and ship definitions were not saved.'}, indent=2))
