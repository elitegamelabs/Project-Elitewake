"""Play: the testing-phase region teleport (owner, October 24): Shift + 1 to 5 carries the survivor to Plains, Jungle, Desert, Swamp, Winter.
Calls the same server RPC the keys call (the key chord itself is not synthesised). One player (EW_PLAY_PLAYERS=1). Writes Saved/RegionTeleportPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
CENTRES = [('Plains', -800, -100), ('Jungle', -380000, 20000), ('Desert', 280000, -30000), ('Swamp', -30000, -270000), ('Winter', -60000, 280000)]
checks, phase = [], 0
next_at = time.monotonic() + 2
handle = None


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'RegionTeleportPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 1.5
    try:
        if phase > 0:
            name, x, y = CENTRES[phase - 1]
            at = pawn.get_actor_location()
            assert abs(at.x - x) < 51000 and abs(at.y - y) < 51000, f'{name}: survivor is at {at.x:.0f},{at.y:.0f}, expected {x},{y}'
            assert at.z > -65, f'{name}: survivor is at z={at.z:.0f}, under the sea (nearest dry ground is searched for within 500 m of the centre)'
            checks.append(f'{name}: arrived at ({at.x:.0f},{at.y:.0f}) z={at.z:.0f}')
        if phase == len(CENTRES):
            finish()
            return
        pc.debug_teleport_to_region(phase)
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
