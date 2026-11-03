"""Play: the world map renders with nothing hidden (owner, November 3: no fog) and the sea deep blue round the islands
(owner, November 1). One player:
    .\Scripts\Verification\run_play_check_once.ps1 -Check verify_map_open_play.py -Result MapOpenPlayResult.json -Players 1 -Standalone 1
Checks: the map picture is not one flat colour; there is no fog anywhere, even far from where the survivor has been;
open sea between the islands shows deep blue; the ground under the survivor (the starter island) is not painted as sea;
the scale bar reads a distance. Writes Saved/MapOpenPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
phase = 0
next_at = time.monotonic() + 3
checks = []
handle = None


def mapw():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWMapWidget, False) if w.is_in_viewport())


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    pc.set_map_open(False)
    Path(unreal.Paths.project_saved_dir(), 'MapOpenPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def blue(p):
    return p.b > .1 and p.b > p.r * 1.8 and p.b > p.g * 1.2


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 2.0
    try:
        if phase == 0:
            pc.get_exploration().forget_all()      # even with nothing explored the map is open
            pc.set_map_open(True)
        elif phase == 2:
            m = mapw()
            assert m.has_map_capture() and not m.has_fog(), 'no capture, or fog'
            colours = set()
            for u in (.1, .3, .5, .7, .9):
                for v in (.1, .3, .5, .7, .9):
                    p = m.probe_map_pixel(unreal.Vector2D(u, v))
                    colours.add((round(p.r, 2), round(p.g, 2), round(p.b, 2)))
            assert len(colours) >= 2, f'the map picture is flat: {colours}'
            checks.append(f'The map picture is not flat ({len(colours)} distinct colours in 25 samples)')
            here = pawn.get_actor_location()
            for far in (unreal.Vector(here.x - 900000, here.y + 900000, 0), unreal.Vector(here.x + 1200000, here.y - 1200000, 0)):
                assert m.get_fog_alpha_at_world(far) == 0.0, f'fog at a far place: {m.get_fog_alpha_at_world(far)}'
            checks.append('No fog anywhere, even where the survivor has never been')
            corners = [m.probe_map_pixel(unreal.Vector2D(u, v)) for u, v in ((.03, .03), (.97, .03), (.03, .97), (.97, .97))]
            assert all(blue(p) for p in corners), f'the open sea is not blue: {[(round(p.r, 2), round(p.g, 2), round(p.b, 2)) for p in corners]}'
            checks.append('The open sea round the islands is deep blue')
            centre = m.probe_map_pixel(unreal.Vector2D(.5, .5))
            assert not blue(centre), f'the starter island under the survivor is painted as sea: {centre}'
            checks.append('The island under the survivor keeps its own colours')
            assert str(m.get_scale_text()) != '', 'no scale text'
            checks.append(f'The scale bar reads {m.get_scale_text()}')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
