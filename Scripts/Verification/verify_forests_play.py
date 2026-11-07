"""Play check: the forests (owner, November 6: dense, varied forests with open ground and bushes), on
Lvl_CoastalPlayground, one player.

1. Census: every island has its forest stands (AEWForest), the old one-actor trees are gone from the islands, and the
   stands hold at least 200,000 trees in all.
2. Chop: with a hatchet, a blow at a forest oak on Plains2 turns it into an ordinary harvestable tree in the same place
   and gives wood; the forest counts it as down, and it does not grow back while the new tree stands there.
3. In a stand of each region and at a meadow's edge: the survivor stands among the trees for 3 s; the frame time is
   recorded and a screenshot taken (Saved/Screenshots/Forests).
Run with run_play_check.py, one player:
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check verify_forests_play.py -Result ForestsPlayResult.json
        -Players 1 -Standalone 1 -Timeout 900 -Visible
Writes Saved/ForestsPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
ROOT = Path(unreal.Paths.project_saved_dir())
RESULT = ROOT / 'ForestsPlayResult.json'
SHOTS = ROOT / 'Screenshots' / 'Forests'
SHOTS.mkdir(parents=True, exist_ok=True)
PLAN = json.loads((ROOT / 'ForestPlan.json').read_text())
world = next(w for w in lib.get_play_worlds() if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
forests = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWForest))
report = {'map': '/Game/Elitewake/Maps/Lvl_CoastalPlayground', 'success': False, 'error': None, 'views': []}
state = {'phase': 'wait', 'until': time.monotonic() + 8.0, 'h': None, 'frames': []}


def island_key(label):
    return label.split(' ')[1]


def ground(x, y, z=20000.0):
    hit = unreal.SystemLibrary.line_trace_single_for_objects(
        world, unreal.Vector(x, y, z), unreal.Vector(x, y, -5000), [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], False, [pawn],
        unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else None


def census():
    by = {}
    for f in forests:
        k = island_key(f.get_actor_label())
        by[k] = by.get(k, 0) + f.get_tree_count()
    old = [t.get_actor_label() for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHarvestTree)
           if any(f' {i.key} ' in f' {t.get_actor_label()} ' for i in W.ISLANDS)]
    report.update(trees_by_island=by, trees=sum(by.values()), stands=len(forests), old_tree_actors_left=len(old))
    missing = [i.key for i in W.ISLANDS if by.get(i.key, 0) < 1000]
    assert not missing, f'islands without forest: {missing}'
    assert not old, f'old one-actor trees left: {old[:5]}'
    assert report['trees'] >= 200000, f"only {report['trees']} trees"


def aim_at(x, y, z):
    eye, _ = pawn.get_actor_eyes_view_point()
    yaw = math.degrees(math.atan2(y - eye.y, x - eye.x))
    pitch = -math.degrees(math.atan2(eye.z - z, math.hypot(x - eye.x, y - eye.y)))
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))


def begin_chop():
    oaks = [f for f in forests if f.get_actor_label().startswith('Forest Plains2 Oak')]
    forest = max(oaks, key=lambda f: f.get_tree_count())
    # A grown oak with room around it, so the survivor stands clear of the neighbours.
    best = None
    for i in range(0, forest.get_tree_count(), 7):
        t = forest.get_tree_transform(i)
        if .9 < t.scale3d.z < 1.2:
            best = i
            break
    t = forest.get_tree_transform(best)
    at = t.translation
    hatchet = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatchet')
    wood = forest.get_editor_property('wood')
    inv = pawn.get_inventory_component()
    inv.remove_item(wood, 100000)
    inv.add_item(hatchet, 1)
    assert lib.send_verification_equipment_request(pc, hatchet, unreal.EWEquipmentSlot.MAIN_HAND), 'equip refused'
    reach = forest.get_editor_property('trunk_radius') * t.scale3d.x + 90
    for turn in range(0, 360, 45):
        x, y = at.x + reach * math.cos(math.radians(turn)), at.y + reach * math.sin(math.radians(turn))
        g = ground(x, y, at.z + 400)
        if g is not None and pawn.teleport(unreal.Vector(x, y, g + 100), unreal.Rotator()):
            break
    state.update(forest=forest, index=best, at=at, wood=wood, down0=forest.get_down_count(), phase='aim', until=time.monotonic() + 1.5)
    report['chop'] = {'forest': forest.get_actor_label(), 'tree': best, 'at': [round(at.x), round(at.y), round(at.z)]}


def views():
    """(name, x, y, look x, look y): inside a stand in each region, and at a Plains meadow's edge."""
    out = []
    for key in ('Plains2', 'Winter1', 'Swamp1', 'Desert1', 'Jungle1'):
        trees = [(t[2], t[3]) for t in PLAN[key]['trees']]
        grid = {}
        for x, y in trees:
            grid.setdefault((int(x // 1000), int(y // 1000)), []).append((x, y))

        def gap(x, y):
            cx, cy = int(x // 1000), int(y // 1000)
            return min((math.hypot(x - px, y - py) for i in range(cx - 1, cx + 2) for j in range(cy - 1, cy + 2)
                        for px, py in grid.get((i, j), ())), default=1e9)
        # Deep in the densest stand, then a spot between trunks with 4-8 m of open ground round the survivor.
        sample = trees[::40]
        tx, ty = max(sample, key=lambda p: sum(1 for u in sample if abs(u[0] - p[0]) < 2500 and abs(u[1] - p[1]) < 2500))
        spot = (tx + 400, ty)
        for r in range(300, 2000, 150):
            found = next(((tx + r * math.cos(a / 8 * math.pi), ty + r * math.sin(a / 8 * math.pi)) for a in range(16)
                          if 400 < gap(tx + r * math.cos(a / 8 * math.pi), ty + r * math.sin(a / 8 * math.pi)) < 800), None)
            if found:
                spot = found
                break
        out.append((f'{key} in the forest', spot[0], spot[1], spot[0] + 3000, spot[1] + 1500))
    island = W.island('Plains2')
    pts = [(t[2], t[3]) for t in PLAN['Plains2']['trees']]
    cells = {}
    for x, y in pts:
        cells.setdefault((int(x // 2000), int(y // 2000)), []).append((x, y))
    for k in range(4000):
        x = island.cx + (k * 7919 % 3000 - 1500) * 100
        y = island.cy + (k * 104729 % 3000 - 1500) * 100
        if island.distance(x, y) > -3000:
            continue
        cx, cy = int(x // 2000), int(y // 2000)
        near = [p for i in range(cx - 3, cx + 4) for j in range(cy - 3, cy + 4) for p in cells.get((i, j), ())]
        close = min((math.hypot(x - px, y - py) for px, py in near), default=1e9)
        if 2500 < close < 4000 and len(near) > 60:
            fx, fy = min(near, key=lambda p: math.hypot(x - p[0], y - p[1]))
            out.append(('Plains2 meadow edge', x, y, fx, fy))
            break
    return out


VIEWS = []


def begin_view(n):
    name, x, y, lx, ly = VIEWS[n]
    g = ground(x, y) or 0.0
    pawn.teleport(unreal.Vector(x, y, g + 110), unreal.Rotator())
    gz = ground(lx, ly) or g
    aim_at(lx, ly, gz + 500)
    pawn.set_actor_rotation(unreal.Rotator(yaw=pc.get_control_rotation().yaw - 25), False)
    state.update(view=n, phase='settle', until=time.monotonic() + 3.0, frames=[])


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report['error'] = error
    report['success'] = error is None
    report['finished_utc'] = time.time()
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f"EWPLAYCHECK Forests success={report['success']} error={error}")


def tick(delta):
    try:
        now = time.monotonic()
        survival = pawn.get_survival_component()
        if survival:
            survival.restore_health(1000.0)
        if state['phase'] == 'wait':
            if now >= state['until']:
                unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
                census()
                begin_chop()
            return
        if state['phase'] == 'aim':
            at = state['at']
            aim_at(at.x, at.y, at.z + 120)
            if now >= state['until']:
                assert lib.send_verification_attack(pc, state['forest']), 'attack not accepted'
                state.update(phase='chopped', until=now + 1.5)
            return
        if state['phase'] == 'chopped':
            if now < state['until']:
                return
            forest, at = state['forest'], state['at']
            got = pawn.get_inventory_component().get_item_count(state['wood'])
            standing = [t for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHarvestTree)
                        if math.hypot(t.get_actor_location().x - at.x, t.get_actor_location().y - at.y) < 50]
            chop = report['chop']
            chop.update(wood=got, down=forest.get_down_count() - state['down0'], became_tree=len(standing),
                        hidden=not forest.is_standing(state['index']))
            unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{SHOTS / "Chop.png"}"')
            assert got > 0, 'the blow gave no wood'
            assert chop['down'] == 1 and chop['hidden'], 'the forest did not count the tree as down'
            assert len(standing) == 1, 'no harvestable tree took its place'
            forest.regrow_all_now()
            chop['regrew_under_new_tree'] = forest.is_standing(state['index'])
            assert not chop['regrew_under_new_tree'], 'the forest tree grew back through the new tree'
            VIEWS.extend(views())
            begin_view(0)
            return
        if state['phase'] == 'settle':
            state['frames'].append(delta)
            if now >= state['until']:
                name = VIEWS[state['view']][0]
                frames = state['frames'][len(state['frames']) // 3:]
                path = SHOTS / f"{name.replace(' ', '_')}.png"
                unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{path}"')
                report['views'].append({'view': name, 'frame_ms_mean': round(1000 * sum(frames) / max(1, len(frames)), 1),
                                        'frame_ms_worst': round(1000 * max(frames or [0]), 1), 'screenshot': str(path)})
                unreal.log(f"EWFORESTS {name}: {report['views'][-1]['frame_ms_mean']} ms")
                for f in forests:
                    f.set_actor_hidden_in_game(True)          # the same view without the forests: what they cost
                state.update(phase='bare', until=now + 4.0, frames=[])
            return
        if state['phase'] == 'bare':
            state['frames'].append(delta)
            if now >= state['until']:
                frames = state['frames'][len(state['frames']) // 3:]
                report['views'][-1]['frame_ms_without_forests'] = round(1000 * sum(frames) / max(1, len(frames)), 1)
                for f in forests:
                    f.set_actor_hidden_in_game(False)
                state.update(phase='shot', until=now + 1.0)
            return
        if state['phase'] == 'shot' and now >= state['until']:
            if state['view'] + 1 < len(VIEWS):
                begin_view(state['view'] + 1)
            else:
                finish()
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
