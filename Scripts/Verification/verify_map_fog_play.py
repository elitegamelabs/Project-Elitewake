"""Play: the world map renders and is covered in mist that clears round the survivor and stays clear (owner, October 22). One player (EW_PLAY_PLAYERS=1).
Checks: the map picture is not one flat colour; the mist is thick far away and clear at the survivor; after the survivor moves on, the place they left stays clear
(permanent discovery), the new place is clear, and a place far from the path is still thick; the scale bar reads a distance. Writes Saved/MapFogPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
explore = pc.get_exploration()
assert explore is not None
phase = 0
next_at = time.monotonic() + 3
checks = []
handle = None
state = {}


def mapw():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWMapWidget, False) if w.is_in_viewport())


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    pc.set_map_open(False)
    Path(unreal.Paths.project_saved_dir(), 'MapFogPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 2.0
    try:
        if phase == 0:
            state['start'] = pawn.get_actor_location()
            explore.forget_all()
            pc.set_map_open(True)
        elif phase == 1:
            m = mapw()
            assert m.has_map_capture() and m.has_fog(), 'no capture or no mist'
            colours = set()
            for u in (.1, .3, .5, .7, .9):
                for v in (.1, .3, .5, .7, .9):
                    p = m.probe_map_pixel(unreal.Vector2D(u, v))
                    colours.add((round(p.r, 2), round(p.g, 2), round(p.b, 2)))
            assert len(colours) >= 2, f'the map picture is flat: {colours}'
            checks.append(f'The map picture is not flat ({len(colours)} distinct colours in 25 samples)')
            far = unreal.Vector(state['start'].x - 900000, state['start'].y + 900000, 0)
            assert m.get_fog_alpha_at_world(far) > 0.95, f'mist at a far place: {m.get_fog_alpha_at_world(far)}'
            assert m.get_fog_alpha_at_world(state['start']) < 0.2, f'mist at the survivor: {m.get_fog_alpha_at_world(state["start"])}'
            checks.append('Grey mist lies thick over far places and is clear round the survivor')
            assert explore.is_revealed(state['start'])
            assert str(m.get_scale_text()) != '', 'no scale text'
            checks.append(f'The scale bar reads {m.get_scale_text()}')
            state['far'] = far
            pc.set_map_open(False)
        elif phase == 2:
            here = pawn.get_actor_location()
            state['moved'] = unreal.Vector(here.x + 150000, here.y, here.z + 300)
            pawn.teleport(state['moved'], pawn.get_actor_rotation())
        elif phase == 4:
            pc.set_map_open(True)
        elif phase == 6:
            m = mapw()
            state['moved'] = pawn.get_actor_location()
            assert m.get_fog_alpha_at_world(state['moved']) < 0.2, f'the new place is not clear ({state["moved"]}, alpha {m.get_fog_alpha_at_world(state["moved"])}, revealed {explore.is_revealed(state["moved"])})'
            assert m.get_fog_alpha_at_world(state['start']) < 0.2, 'the place the survivor left has clouded over again'
            assert m.get_fog_alpha_at_world(state['far']) > 0.95
            frac = explore.get_revealed_fraction()
            assert 0.0 < frac < 0.5, f'revealed fraction {frac}'
            checks.append('Moving on clears the new place, the old place stays clear, far places stay misty (permanent discovery)')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
