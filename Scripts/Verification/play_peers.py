"""The same actor in another Play world (November 7). An actor placed in the map has the same name on the server and every
client; one spawned in Play (a ship the runner spawns for a check, EW_PLAY_SHIPS) gets another name on each client, so it is
matched by its class, its definition if it has one, and the nearest position."""
import unreal


def peer_of(actor, world):
    candidates = list(unreal.GameplayStatics.get_all_actors_of_class(world, actor.get_class()))
    same = next((a for a in candidates if a.get_name() == actor.get_name()), None)
    if same:
        return same
    try:
        definition = actor.get_editor_property('definition')
        candidates = [a for a in candidates if a.get_editor_property('definition') == definition]
    except Exception:      # noqa: BLE001  (no definition on this class)
        pass
    if len(candidates) == 1:
        return candidates[0]           # the only one of its kind (its position may not have reached this machine yet)
    at = actor.get_actor_location()
    near = sorted(candidates, key=lambda a: (a.get_actor_location() - at).length())
    return near[0] if near and (near[0].get_actor_location() - at).length() < 1000 else None
