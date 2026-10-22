"""Opens the world map and captures it, for looking at (not a pass/fail check). EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1600x900. Optional: EW_MAP_WALK=1 walks the
survivor a long way first so the fog has been cleared along a path. Writes Saved/Screenshots/MapScreens/*.png and Saved/MapScreensResult.json."""
import unreal, json, os, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'MapScreens')
SHOTS.mkdir(parents=True, exist_ok=True)
for old in SHOTS.glob('*.png'):
    old.unlink()
state = {'i': 0, 'at': time.monotonic() + 3, 'start': pawn.get_actor_location()}
handle = None


def shot(name):
    return lambda: unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (name + ".png")}"')


def move(dx, dy):
    def go():
        here = pawn.get_actor_location()
        pawn.teleport(unreal.Vector(here.x + dx, here.y + dy, here.z + 300), pawn.get_actor_rotation())
    return go


steps = [(lambda: pc.set_map_open(True), 3.0), (shot('1_map_start'), 2.0), (lambda: pc.set_map_open(False), 1.0)]
if os.environ.get('EW_MAP_WALK') == '1':
    for _ in range(6):
        steps += [(move(60000, 0), 3.0)]
    steps += [(lambda: pc.set_map_open(True), 3.0), (shot('2_map_after_walk'), 2.0), (lambda: pc.set_map_open(False), 1.0)]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'MapScreensResult.json').write_text(json.dumps({'success': error is None, 'shots': sorted(p.name for p in SHOTS.glob('*.png')), 'error': error}, indent=2))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(steps):
            finish()
            return
        action, wait = steps[state['i']]
        action()
        state['i'] += 1
        state['at'] = time.monotonic() + wait
    except Exception as exc:
        finish(f'Step {state["i"]}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
