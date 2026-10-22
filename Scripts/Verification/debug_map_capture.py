"""Debug: tries several capture heights, sources and widths over the survivor and prints what the map's render target holds. EW_PLAY_PLAYERS=1."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
out = []
state = {'i': 0, 'at': time.monotonic() + 3, 'cases': [(h, s, w) for h in (20000.0, 60000.0, 100000.0, 200000.0, 300000.0) for s in (1,) for w in (12000.0,)], 'phase': 0}
handle = None


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWMapWidget, False))


def sample(m):
    return [[round(c, 3) for c in (lambda p: (p.r, p.g, p.b, p.a))(m.probe_map_pixel(unreal.Vector2D(u, v)))] for u, v in ((.5, .5), (.2, .2), (.8, .8), (.5, .8))]


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['phase'] == 0:
            pc.set_map_open(True)
            state['phase'] = 1
            state['at'] = time.monotonic() + 3
            return
        if state['i'] > 0:
            out.append({'case': state['cases'][state['i'] - 1], 'pixels': sample(menu())})
        if state['i'] >= len(state['cases']):
            unreal.unregister_slate_post_tick_callback(handle)
            Path(unreal.Paths.project_saved_dir(), 'DebugMapCapture.json').write_text(json.dumps({'player': str(pawn.get_actor_location()), 'out': out}, indent=1))
            return
        h, s, w = state['cases'][state['i']]
        menu().debug_capture(h, s, w)
        state['i'] += 1
        state['at'] = time.monotonic() + 0.8
    except Exception as exc:
        unreal.unregister_slate_post_tick_callback(handle)
        Path(unreal.Paths.project_saved_dir(), 'DebugMapCapture.json').write_text(json.dumps({'error': repr(exc), 'out': out}))


handle = unreal.register_slate_post_tick_callback(tick)
