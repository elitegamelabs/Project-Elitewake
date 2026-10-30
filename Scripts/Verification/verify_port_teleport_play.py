"""Play: the testing-phase Port teleport (owner, October 30): Shift + 6 carries the survivor to the nearest Port, in front of its merchant.
For each region, Shift + 1 to 5 first (the region teleport), then the Port teleport: the survivor must stand on that region's Port plaza,
on the ground, facing the nearest general merchant within reach to trade. Calls the same server RPCs the keys call (the key chord itself is
not synthesised). One player (EW_PLAY_PLAYERS=1). Writes Saved/PortTeleportPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
checks, state = [], {'phase': 0, 'region': 0}
next_at = time.monotonic() + 3
handle = None


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'PortTeleportPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def merchants():
    return [m for m in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWMerchant) if not isinstance(m, unreal.EWCrewMaster)]


def tick(delta):
    global next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 2.0
    try:
        if state['phase'] == 0:
            pc.debug_teleport_to_region(state['region'])
            state['phase'] = 1
        elif state['phase'] == 1:
            here = pawn.get_actor_location()
            state['expected'] = min(merchants(), key=lambda m: (m.get_actor_location() - here).length())
            pc.debug_teleport_to_port()
            state['phase'] = 2
        else:
            m, at = state['expected'], pawn.get_actor_location()
            gap = (at - m.get_actor_location()).length()
            assert gap < 450, f'region {state["region"]}: survivor is {gap:.0f} cm from {m.get_actor_label() if hasattr(m, "get_actor_label") else m.get_name()}'
            assert at.z > m.get_actor_location().z - 20, f'region {state["region"]}: survivor fell below the plaza (z={at.z:.0f})'
            to = m.get_actor_location() - at
            yaw = unreal.MathLibrary.make_rot_from_x(unreal.Vector(to.x, to.y, 0)).yaw
            facing = abs(((pc.get_control_rotation().yaw - yaw) + 180) % 360 - 180)
            assert facing < 20, f'region {state["region"]}: survivor faces {facing:.0f} degrees away from the merchant'
            checks.append(f'region {state["region"]}: at the Port merchant {m.get_name()}, {gap:.0f} cm away, z={at.z:.0f}, facing within {facing:.0f} degrees')
            state['region'] += 1
            state['phase'] = 0
            if state['region'] == 5:
                finish()
    except Exception as exc:
        finish(f'Phase {state}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
