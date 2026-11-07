"""Captures each island from the sea, 120 m up and a few hundred metres off its shore, for looking at (not pass/fail). EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1600x900.
Writes Saved/Screenshots/Islands/<key>.png and Saved/IslandsCaptureResult.json."""
import unreal, json, math, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Islands')
SHOTS.mkdir(parents=True, exist_ok=True)
for old in SHOTS.glob('*.png'):
    old.unlink()
steps = []
for isle in W.ISLANDS:
    # From the side facing the middle of the world, looking in, and from the opposite side.
    for tag, flip in (('', 1.0),):
        ang = math.atan2(-isle.cy, -isle.cx) if (isle.cx or isle.cy) else math.pi
        r = isle.radius(ang) + 40000
        x, y = isle.cx + r * math.cos(ang), isle.cy + r * math.sin(ang)
        yaw = math.degrees(ang + math.pi)
        steps.append((isle.key, (x, y, 12000.0), yaw))
state = {'i': 0, 'phase': 0, 'at': time.monotonic() + 3}
handle = None


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'IslandsCaptureResult.json').write_text(json.dumps({'success': error is None, 'shots': sorted(p.name for p in SHOTS.glob('*.png')), 'error': error}, indent=2))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(steps):
            finish()
            return
        key, (x, y, z), yaw = steps[state['i']]
        if state['phase'] == 0:
            pawn.teleport(unreal.Vector(x, y, z), unreal.Rotator(0, yaw, 0))
            pc.set_control_rotation(unreal.Rotator(-18, yaw, 0))
            state['phase'] = 1
            state['at'] = time.monotonic() + 1.2
        else:
            pc.set_control_rotation(unreal.Rotator(-18, yaw, 0))
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (key + ".png")}"')
            state['phase'] = 0
            state['i'] += 1
            state['at'] = time.monotonic() + 1.5
    except Exception as exc:
        finish(f'{exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
