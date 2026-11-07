"""Diagnostic (not a pass/fail check): what the forests cost per frame, and from what. On Lvl_CoastalPlayground, one player,
standing deep in a Plains2 oak stand looking across it. Each setting is held 4 s and the mean frame time of the last
2.7 s is kept: everything shown; forests hidden; forest shadows off; trees drawn only to 800 m; both; and the bushes
hidden. Writes Saved/ForestCostResult.json.
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check diagnose_forest_cost_play.py -Result ForestCostResult.json
        -Players 1 -Standalone 1 -Timeout 600 -Visible
"""
import json
import math
import time
from pathlib import Path

import unreal

lib = unreal.EWEditorVerificationLibrary
ROOT = Path(unreal.Paths.project_saved_dir())
PLAN = json.loads((ROOT / 'ForestPlan.json').read_text())
world = next(w for w in lib.get_play_worlds() if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
forests = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWForest))
trees = [f.get_editor_property('trees') for f in forests]
bushes = [c for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor)
          for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent)
          if c.get_editor_property('static_mesh') and 'SM_Bush' in c.get_editor_property('static_mesh').get_name()]
report = {'results': {}}
state = {'h': None, 'i': -1, 'until': time.monotonic() + 8.0, 'frames': []}


def shown(on):
    for f in forests:
        f.set_actor_hidden_in_game(not on)


def shadows(on):
    for c in trees:
        c.set_cast_shadow(on)


def cull(far):
    for c in trees:
        c.set_cull_distances(int(far * .85), int(far))


def bush(on):
    for c in bushes:
        c.set_visibility(on)


SETTINGS = [('everything', lambda: None),
            ('forests hidden', lambda: shown(False)),
            ('forest shadows off', lambda: (shown(True), shadows(False))),
            ('trees to 800 m', lambda: (shadows(True), cull(80000))),
            ('shadows off and 800 m', lambda: shadows(False)),
            ('bushes hidden too', lambda: bush(False))]


def place():
    pts = [(t[2], t[3]) for t in PLAN['Plains2']['trees'] if t[0] == 'Oak']
    sample = pts[::30]
    tx, ty = max(sample, key=lambda p: sum(1 for u in sample if abs(u[0] - p[0]) < 2500 and abs(u[1] - p[1]) < 2500))
    hit = unreal.SystemLibrary.line_trace_single_for_objects(world, unreal.Vector(tx + 450, ty, 20000), unreal.Vector(tx + 450, ty, -5000),
        [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], False, [pawn], unreal.DrawDebugTrace.NONE, True)
    z = hit.to_tuple()[4].z if hit else 0.0
    pawn.teleport(unreal.Vector(tx + 450, ty, z + 110), unreal.Rotator())
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=30))
    report['at'] = [round(tx), round(ty)]


def tick(delta):
    try:
        now = time.monotonic()
        if state['i'] < 0:
            if now >= state['until']:
                unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
                place()
                state.update(i=0, until=now + 6.0, frames=[])
            return
        state['frames'].append(delta)
        if now < state['until']:
            return
        f = state['frames'][len(state['frames']) // 3:]
        report['results'][SETTINGS[state['i']][0]] = round(1000 * sum(f) / max(1, len(f)), 1)
        unreal.log(f"EWFORESTCOST {SETTINGS[state['i']][0]}: {report['results'][SETTINGS[state['i']][0]]} ms")
        state['i'] += 1
        if state['i'] >= len(SETTINGS):
            unreal.unregister_slate_post_tick_callback(state['h'])
            report['success'] = True
            (ROOT / 'ForestCostResult.json').write_text(json.dumps(report, indent=2))
            unreal.log('EWPLAYCHECK ForestCost success=True')
            return
        SETTINGS[state['i']][1]()
        state.update(until=now + 4.0, frames=[])
    except Exception as error:
        unreal.unregister_slate_post_tick_callback(state['h'])
        (ROOT / 'ForestCostResult.json').write_text(json.dumps({'success': False, 'error': repr(error), **report}, indent=2))


state['h'] = unreal.register_slate_post_tick_callback(tick)
