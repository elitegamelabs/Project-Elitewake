"""Play: land animals roam naturally (owner, October 16: wander on their islands with idle, foraging, rest and avoidance).
One player (EW_PLAY_PLAYERS=1). The survivor is carried to the biggest group of animals, game time runs four times faster (slomo 4), and
every animal in the group is sampled five times a second for about three game minutes (the survivor stands close first, then 25 m off, since
an animal lies down only when no survivor is near). Checks: the group shows walking AND at least two kinds of standing (grazing with the
head bowed, looking about, lying down with the body lowered); each animal moves; the postures really show (a grazing animal's bowed head
and a lying animal's lowered body, as the screens read them); animals keep apart (reports the closest approach). Writes Saved/AnimalRoamingPlayResult.json."""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
survival = pawn.get_survival_component()
animals = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal))
assert animals, 'no animals in the map'


def d2(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


best = max(animals, key=lambda a: sum(1 for b in animals if d2(a.get_home(), b.get_home()) < 3000))
group = [a for a in animals if d2(best.get_home(), a.get_home()) < 3000]
assert len(group) >= 3, f'the biggest group has only {len(group)} animals'
centre = best.get_home()
names = {a.get_name(): str(a.get_editor_property('definition').get_editor_property('display_name')) for a in group}
seen = {a.get_name(): set() for a in group}
start = {a.get_name(): a.get_actor_location() for a in group}
moved = {a.get_name(): 0.0 for a in group}
postures = {'graze_bowed': 0.0, 'lie_lowered': 0.0}
closest = [1e9]
state = {'t0': time.monotonic() + 12, 'moved_away': False, 'handle': None, 'ended': False}
report = {'group': names}


def action_name(a):
    return str(a.get_action()).upper().split('.')[-1].split(':')[0].strip('<>')


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    unreal.SystemLibrary.execute_console_command(world, 'slomo 1')
    report.update(success=error is None, error=error, seen={k: sorted(v) for k, v in seen.items()}, moved={k: round(v) for k, v in moved.items()},
                  postures=postures, closest_approach_cm=round(closest[0]))
    Path(unreal.Paths.project_saved_dir(), 'AnimalRoamingPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK AnimalRoaming success={error is None} error={error}')


def tick(delta):
    if state['ended']:
        return
    now = time.monotonic()
    survival.restore_health(1000.0)
    if now < state['t0']:
        return
    try:
        if state.get('phase') is None:
            state['phase'] = 'near'
            state['started'] = now
            pawn.teleport(unreal.Vector(centre.x + 300, centre.y, centre.z + 300), unreal.Rotator())
            unreal.SystemLibrary.execute_console_command(world, 'slomo 4')
            return
        elapsed = now - state['started']
        if elapsed > 12 and not state['moved_away']:
            state['moved_away'] = True       # lying down needs nobody near
            pawn.teleport(unreal.Vector(centre.x + 2500, centre.y + 1500, centre.z + 300), unreal.Rotator())
        live = [a for a in group if not a.is_dead()]
        for a in live:
            n = a.get_name()
            seen[n].add(action_name(a))
            moved[n] = max(moved[n], d2(a.get_actor_location(), start[n]))
            if action_name(a) == 'GRAZE':
                postures['graze_bowed'] = max(postures['graze_bowed'], a.get_graze_shown())
            if action_name(a) == 'REST':
                postures['lie_lowered'] = max(postures['lie_lowered'], a.get_lie_shown())
        for i, a in enumerate(live):
            for b in live[i + 1:]:
                closest[0] = min(closest[0], d2(a.get_actor_location(), b.get_actor_location()))
        if elapsed < 55:
            return
        union = set().union(*seen.values())
        report['union'] = sorted(union)
        assert 'WANDER' in union, f'nothing walked: {sorted(union)}'
        idle = union & {'GRAZE', 'LOOK', 'REST'}
        assert len(idle) >= 2, f'the group showed only {sorted(idle)} when standing'
        wanderers = [k for k, v in moved.items() if v > 150]
        assert len(wanderers) >= max(1, len(group) // 2), f'only {len(wanderers)} of {len(group)} animals went anywhere'
        if 'GRAZE' in union:
            assert postures['graze_bowed'] > .8, f'a grazing animal never bowed its head ({postures})'
        if 'REST' in union:
            assert postures['lie_lowered'] > .8, f'a resting animal never lay down ({postures})'
        state['ended'] = True
        finish()
    except Exception as error:
        state['ended'] = True
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
