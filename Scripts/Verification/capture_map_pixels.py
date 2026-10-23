"""Reads the world map's own top-down picture (not a screenshot) and writes it as a brightened PNG, for looking at the islands' shapes. EW_PLAY_PLAYERS=1.
Writes Saved/Screenshots/MapPixels/map.png (up is +X, right is +Y) and Saved/MapPixelsResult.json."""
import unreal, json, struct, time, zlib
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
OUT = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'MapPixels')
OUT.mkdir(parents=True, exist_ok=True)
N = 160
state = {'phase': 0, 'at': time.monotonic() + 3}
handle = None


def mapw():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWMapWidget, False) if w.is_in_viewport())


def png(path, w, h, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'MapPixelsResult.json').write_text(json.dumps({'success': error is None, 'error': error}, indent=2))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['phase'] == 0:
            pc.set_map_open(True)
            state['phase'] = 1
            state['at'] = time.monotonic() + 4
            return
        m = mapw()
        rows = []
        for j in range(N):
            row = []
            for i in range(N):
                p = m.probe_map_pixel(unreal.Vector2D((i + .5) / N, (j + .5) / N))
                row += [max(0, min(255, int((c ** 0.45) * 255 * 1.6))) for c in (p.r, p.g, p.b)]
            rows.append(row)
        png(OUT / 'map.png', N, N, rows)
        pc.set_map_open(False)
        finish()
    except Exception as exc:
        finish(repr(exc))


handle = unreal.register_slate_post_tick_callback(tick)
