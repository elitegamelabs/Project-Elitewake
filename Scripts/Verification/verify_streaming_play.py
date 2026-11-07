"""Play check: World Partition streaming of the ground cover (November 6, the streaming work), one player, on the World
Partition map (run_play_check_once.ps1 -Map /Game/Elitewake/Maps/Lvl_CoastalPlayground_WP).

1. At the start: some foliage cells are loaded round the survivor and none far off (the nearest loaded cell within
   NEAR, the farthest within FAR); grass is drawn round the survivor's feet.
2. Set down on Jungle1, 10 s later: cells round the survivor there are loaded, those round the start are not.
3. Everything that stays loaded is there in both places: all 20 islands' ground, the forests and the animals.
4. Frame time in each place (Saved/Screenshots/Streaming).
Writes Saved/StreamingPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

ROOT = Path(unreal.Paths.project_saved_dir())
RESULT = ROOT / 'StreamingPlayResult.json'
SHOTS = ROOT / 'Screenshots' / 'Streaming'
SHOTS.mkdir(parents=True, exist_ok=True)
NEAR, FAR = 30000.0, 300000.0           # cm
lib = unreal.EWEditorVerificationLibrary
world = next(w for w in lib.get_play_worlds() if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
report = {'success': False, 'error': None, 'places': []}
state = {'h': None, 'phase': 'wait', 'until': time.monotonic() + 12.0, 'frames': []}


def cells():
    """The loaded foliage cells: (centre, instances)."""
    out = []
    for ifa in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
        n = sum(c.get_instance_count() for c in ifa.get_components_by_class(unreal.InstancedStaticMeshComponent))
        if n:
            out.append((ifa.get_actor_bounds(False)[0], n))
    return out


def look(name, extra=None):
    p = pawn.get_actor_location()
    loaded = cells()
    dist = sorted(math.hypot(c.x - p.x, c.y - p.y) for c, _ in loaded)
    frames = state['frames'][len(state['frames']) // 3:]
    here = {'place': name, 'at': [round(p.x), round(p.y)], 'cells_loaded': len(loaded),
            'instances_loaded': sum(n for _, n in loaded), 'nearest_cell_m': round(dist[0] / 100) if dist else None,
            'farthest_cell_m': round(dist[-1] / 100) if dist else None,
            'frame_ms_mean': round(1000 * sum(frames) / max(1, len(frames)), 1)}
    here.update(extra or {})
    path = SHOTS / f"{name.replace(' ', '_')}.png"
    unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{path}"')
    here['screenshot'] = str(path)
    report['places'].append(here)
    unreal.log(f'EWSTREAM {json.dumps(here)}')
    return here, loaded


def kept():
    islands = {str(a.get_actor_label()).split(' ')[0] for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
               if str(a.get_actor_label()).endswith(')') and '(' in str(a.get_actor_label())}
    return {'island_grounds': len(islands & {i.key for i in W.ISLANDS}),
            'forests': len(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWForest)),
            'animals': len(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal))}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report['error'] = error
    report['finished_utc'] = time.time()
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f"EWPLAYCHECK Streaming success={report['success']} error={error}")


def tick(delta):
    try:
        now = time.monotonic()
        state['frames'].append(delta)
        if state['phase'] == 'wait' and now >= state['until']:
            unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
            here, loaded = look('start', kept())
            state['start'] = pawn.get_actor_location()
            assert loaded, 'no foliage cells loaded at the start'
            assert here['nearest_cell_m'] * 100 < NEAR, 'no foliage cell near the survivor'
            assert here['farthest_cell_m'] * 100 < FAR, f"foliage loaded {here['farthest_cell_m']} m away: not streaming"
            jungle = W.island('Jungle1')
            x, y = jungle.cx + 3000, jungle.cy + 2000
            hit = unreal.SystemLibrary.line_trace_single_for_objects(world, unreal.Vector(x, y, 40000), unreal.Vector(x, y, -5000),
                [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], False, [pawn], unreal.DrawDebugTrace.NONE, True)
            z = hit.to_tuple()[4].z if hit else 2000.0
            pawn.teleport(unreal.Vector(x, y, z + 120), unreal.Rotator())
            state.update(phase='travel', until=now + 12.0, frames=[])
            return
        if state['phase'] == 'travel' and now >= state['until']:
            here, loaded = look('Jungle1', kept())
            s = state['start']
            near_start = [c for c, _ in loaded if math.hypot(c.x - s.x, c.y - s.y) < NEAR]
            here['cells_still_loaded_at_start'] = len(near_start)
            assert here['nearest_cell_m'] is not None and here['nearest_cell_m'] * 100 < NEAR, 'no foliage loaded on Jungle1'
            assert not near_start, f'{len(near_start)} cells still loaded at the start, far behind'
            assert here['island_grounds'] == 20 and here['forests'] >= 200 and here['animals'] > 300, 'something that stays loaded is missing'
            report['success'] = True
            state.update(phase='done', until=now + 1.5)
            return
        if state['phase'] == 'done' and now >= state['until']:
            finish()
    except Exception as error:
        report['success'] = False
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
