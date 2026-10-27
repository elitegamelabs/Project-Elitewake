"""Captures each island's beach: from 120 m and 35 m off the shore looking in, and from the sand looking out to sea, for looking at (not pass/fail). EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1600x900.
Writes Saved/Screenshots/Beaches/<key>_<far|near|onshore>.png and Saved/BeachesCaptureResult.json."""
import unreal, json, math, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Beaches')
SHOTS.mkdir(parents=True, exist_ok=True)
for old in SHOTS.glob('*.png'):
    old.unlink()
steps = []
for isle in W.ISLANDS:
    ang = math.atan2(-isle.cy, -isle.cx) if (isle.cx or isle.cy) else math.pi
    # The shoreline along that ray: out from the island's middle until the outline is passed.
    r = 0.0
    while isle.distance(isle.cx + r * math.cos(ang), isle.cy + r * math.sin(ang)) < 0 and r < 600000:
        r += 100.0
    for tag, off, z, pitch in (('far', 12000, 2500.0, -5), ('near', 3500, 1800.0, -6), ('onshore', -1500, 400.0, -3)):
        x, y = isle.cx + (r + off) * math.cos(ang), isle.cy + (r + off) * math.sin(ang)
        # offshore looks in at the beach; onshore stands on the sand looking out to sea
        yaw = math.degrees(ang + math.pi) if off > 0 else math.degrees(ang)
        steps.append((f'{isle.key}_{tag}', (x, y, z), yaw, pitch))
state = {'i': 0, 'phase': 0, 'at': time.monotonic() + 14}
handle = None


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'BeachesCaptureResult.json').write_text(json.dumps({'success': error is None, 'shots': sorted(p.name for p in SHOTS.glob('*.png')), 'error': error}, indent=2))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(steps):
            finish()
            return
        key, (x, y, z), yaw, pitch = steps[state['i']]
        if state['phase'] == 0:
            pawn.teleport(unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
            state['phase'] = 1
            state['at'] = time.monotonic() + 2.5
        else:
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (key + ".png")}"')
            state['phase'] = 0
            state['i'] += 1
            state['at'] = time.monotonic() + 4.0
    except Exception as exc:
        finish(f'{exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
