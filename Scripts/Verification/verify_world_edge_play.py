"""Play: the world's edge (owner, October 22): whatever crosses it comes out on the opposite side, and the edge widens once enough of the world has been cleared.
One player (EW_PLAY_PLAYERS=1). Writes Saved/WorldEdgePlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
edge = unreal.GameplayStatics.get_game_mode(world).get_editor_property('world_edge')
phase = 0
next_at = time.monotonic() + 3
checks = []
handle = None
state = {}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'WorldEdgePlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 2.0
    try:
        if phase == 0:
            assert edge is not None and edge.is_world_edge()
            edge.ensure_bounds()
            state['min'] = edge.get_bounds_min()
            state['size'] = edge.get_bounds_size()
            assert state['size'] > 0
            here = pawn.get_actor_location()
            state['z'] = here.z
            pawn.teleport(unreal.Vector(state['min'].x + state['size'] + 5000, here.y, here.z + 300), pawn.get_actor_rotation())
        elif phase == 1:
            x = pawn.get_actor_location().x
            expected = state['min'].x + 5000
            assert abs(x - expected) < 600, f'pawn at x={x}, expected about {expected}'
            checks.append('Crossing the +X edge brings the survivor out 50 m inside the opposite (-X) edge')
            here = pawn.get_actor_location()
            pawn.teleport(unreal.Vector(here.x, state['min'].y - 3000, here.z + 300), pawn.get_actor_rotation())
        elif phase == 2:
            y = pawn.get_actor_location().y
            expected = state['min'].y + state['size'] - 3000
            assert abs(y - expected) < 600, f'pawn at y={y}, expected about {expected}'
            checks.append('Crossing the -Y edge comes out at the +Y side')
            centre = unreal.Vector(state['min'].x + state['size'] * .5, state['min'].y + state['size'] * .5, 0)
            edge.reveal_around(centre, state['size'] * .35)
        elif phase == 3:
            assert edge.get_bounds_size() > state['size'] * 1.2, f'edge did not grow: {edge.get_bounds_size()} from {state["size"]}'
            checks.append(f'Clearing a third of the world widens the edge from {state["size"]/100000:.1f} km to {edge.get_bounds_size()/100000:.1f} km')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
