"""Graphics tiers, evidence (CLAUDE.md 9.6; owner, November 1): the same view at Low, Medium, High and Epic, each tier's average
frame time, and the gameplay actors counted at each tier (they must not differ). Run through run_play_check.py on
/Game/Elitewake/Maps/Lvl_CoastalPlayground with EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1920x1080, EW_PLAY_STARTER_KIT=0,
EW_PLAY_RESULT=GraphicsTiersCaptures.json. Writes Saved/Screenshots/GraphicsTiers/*.png. Frame times are the editor's Play window
on this machine: comparative only, not the agreed minimum-machine budget. 'success' also requires identical gameplay counts.
"""
import json
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'GraphicsTiers'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
gus = unreal.GameUserSettings.get_game_user_settings()
found = gus.get_overall_scalability_level()
clock = unreal.EWDayNightSubsystem.get_for_world(world)
NAMES = ('Low', 'Medium', 'High', 'Epic')
GAMEPLAY = [c for c in (getattr(unreal, n, None) for n in ('EWAnimal', 'EWHarvestTree', 'EWMineable', 'EWWaterSource', 'EWResourceNode')) if c]
report = {'tiers': {}, 'notes': ['frame times: editor Play window, this machine, comparative only']}
state = {'level': 0, 'phase': 'warm', 'at': time.monotonic() + 2.0, 'deltas': [], 'h': None}


def counts():
    out = {c.__name__: len(unreal.GameplayStatics.get_all_actors_of_class(world, c)) for c in GAMEPLAY}
    out['all_actors'] = len(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor))
    return out


def setup():
    clock.set_hour(10.5)
    unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages')
    # Saltreach's waterfront and the green behind it: water, buildings, trees, grass and shadow in one view.
    port = W.PORTS['Plains']
    x, y = port.world(1500, -2500)
    pawn.set_actor_location(unreal.Vector(x, y, 400), False, True)
    tx, ty = port.world(-1500, 1500)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(x, y, 570), unreal.Vector(tx, ty, 200)))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    if found in (0, 1, 2, 3):
        gus.set_overall_scalability_level(found)
        gus.apply_non_resolution_settings()
        gus.save_settings()
    tiers = list(report['tiers'].values())
    same = bool(tiers) and all(t['gameplay'] == tiers[0]['gameplay'] for t in tiers)
    report.update(success=error is None and same, gameplay_identical=same, error=error)
    (saved / 'GraphicsTiersCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWGRAPHICSTIERS success={report["success"]} error={error}')


def tick(delta):
    try:
        now = time.monotonic()
        if state['phase'] == 'measure':
            state['deltas'].append(delta)
        if now < state['at']:
            return
        level = state['level']
        if state['phase'] == 'warm':
            # Stand at the view first and let the world stream in, so the first tier is not measured mid-load.
            setup()
            state.update(phase='set', at=now + 6.0)
        elif state['phase'] == 'set':
            gus.set_overall_scalability_level(level)
            gus.apply_non_resolution_settings()
            state.update(phase='measure', at=now + 4.0, deltas=[])
        elif state['phase'] == 'measure':
            d = state['deltas'][len(state['deltas']) // 4:]        # past the switch's first hitches
            ms = 1000.0 * sum(d) / max(len(d), 1)
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{shots / f"{level}_{NAMES[level]}.png"}"')
            report['tiers'][NAMES[level]] = {'avg_frame_ms': round(ms, 2), 'fps': round(1000.0 / ms, 1) if ms else None,
                                             'worst_frame_ms': round(1000.0 * max(d), 2) if d else None, 'gameplay': counts()}
            state.update(phase='set', at=now + 1.5, level=level + 1)
            if level + 1 >= len(NAMES):
                finish()
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
