"""Debug: why can the survivor not be put beside the freshwater spring? Lists what stands within 3 m of the spot. EW_PLAY_PLAYERS=1. Writes Saved/DebugSpot.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
state = {'at': time.monotonic() + 3}
handle = None


def tick(delta):
    if time.monotonic() < state['at']:
        return
    unreal.unregister_slate_post_tick_callback(handle)
    out = {}
    try:
        src = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWWaterSource))
        base = src.get_actor_location()
        away = unreal.Vector(150 - base.x, -base.y, 0)
        away = away * (1.0 / max(away.length(), 1.0))
        out['source'] = [base.x, base.y, base.z, str(src.get_actor_label())]
        for dist in (150, 220, 300, 450):
            spot = base + away * dist + unreal.Vector(0, 0, 110)
            near = unreal.SystemLibrary.sphere_overlap_actors(world, spot, 160, [], unreal.Actor, [pawn])
            ok = pawn.teleport(spot, unreal.Rotator())
            out[str(dist)] = {'spot': [spot.x, spot.y, spot.z], 'teleported': ok, 'near': [(str(a.get_actor_label()), a.get_class().get_name()) for a in near][:8]}
    except Exception as exc:
        out['error'] = repr(exc)
    Path(unreal.Paths.project_saved_dir(), 'DebugSpot.json').write_text(json.dumps(out, indent=1))


handle = unreal.register_slate_post_tick_callback(tick)
