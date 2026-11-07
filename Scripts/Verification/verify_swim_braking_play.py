"""Play: a swimmer stops quickly when input is released (owner, October 22: swimming and currents; EWCharacter BrakingDecelerationSwimming 1400).
Listen server plus one client (EW_PLAY_PLAYERS=2). The client swims forward at full speed, lets go, and its horizontal speed must fall under 15% of the swim
speed within half a second and reach rest within a second, on authority and client. Writes Saved/SwimBrakingPlayResult.json."""
import json, time
from pathlib import Path
import unreal
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server = next(w for w, c in zip(worlds, pcs) if c.has_authority())
pawn = client.get_controlled_pawn()
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']
owner = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server, unreal.EWCharacter) if pid(a) == pid(pawn))
movement = lambda p: p.get_component_by_class(unreal.CharacterMovementComponent)
def flat(p):
    v = movement(p).velocity
    return (v.x ** 2 + v.y ** 2) ** .5
checks, memo = [], {}
phase, deadline, handle = 0, time.monotonic() + 1, None
released_at = None


def place(xyz):
    for p in [owner, pawn]:
        assert p.teleport(unreal.Vector(*xyz), unreal.Rotator()), ('Setup teleport rejected', xyz)
        movement(p).stop_movement_immediately()


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    place((150, 0, 200))
    Path(unreal.Paths.project_saved_dir(), 'SwimBrakingPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'measured': memo, 'error': error}, indent=2))


def tick(delta):
    global phase, deadline, released_at
    if phase in (2, 3): pawn.do_move(0, 1)
    if phase in (4, 5) and released_at is not None:
        t = time.monotonic() - released_at
        if t >= .5 and 'at_half_second' not in memo:
            memo['at_half_second'] = [flat(owner), flat(pawn)]
        if t >= 1.0 and 'at_one_second' not in memo:
            memo['at_one_second'] = [flat(owner), flat(pawn)]
    if time.monotonic() < deadline: return
    deadline = time.monotonic() + 2
    try:
        if phase == 0:
            place((6200, 0, -180))
        elif phase == 1:
            assert movement(owner).is_swimming() and movement(pawn).is_swimming(), 'not swimming'
            client.set_control_rotation(unreal.Rotator())
        elif phase == 2:
            pass
        elif phase == 3:
            memo['cruise'] = [flat(owner), flat(pawn)]
            assert min(memo['cruise']) > 200, f'the swimmer never got up to speed: {memo["cruise"]}'
            checks.append(f'The swimmer reached {memo["cruise"][0]:.0f} cm/s')
            deadline = time.monotonic() + .1
            released_at = time.monotonic()
        elif phase == 4:
            deadline = time.monotonic() + .1
        elif phase == 5:
            if 'at_one_second' not in memo:
                return
            limit = .15 * 450
            assert max(memo['at_half_second']) < limit, f'half a second after letting go the speed is {memo["at_half_second"]} (limit {limit:.0f})'
            assert max(memo['at_one_second']) < 20, f'a second after letting go the speed is {memo["at_one_second"]}'
            checks.append('Letting go of the stick stops a swimmer within half a second to a second, on authority and client')
            finish(); return
        phase += 1
    except Exception as e: finish('phase ' + str(phase) + ': ' + repr(e))
handle = unreal.register_slate_post_tick_callback(tick)
