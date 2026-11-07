"""Play: Saltreach Freeport's sounds (owner, October 30: a lived-in town; synthesized placeholders by Scripts/Art/make_town_sounds.py).
One player. By day the tavern's voices, the market's voices, the shipyard at work and the water at the piles all play; at night the market
and the yard fall quiet while the tavern and the water go on; the harbor bell waits for its interval. Whether they sound right is judged by
ear. Writes Saved/FreeportSoundsPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 10, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'FreeportSoundsPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK FreeportSounds success={error is None} error={error}')


def sounds():
    return {str(a.get_actor_label()).split('sound, ')[-1]: a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWTownSound)}


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        clock = unreal.EWDayNightSubsystem.get_for_world(world)
        if p == 0:
            found = sounds()
            report['sounds'] = sorted(found)
            check('the town has its sounds', len(found) == 10, found=sorted(found))
            clock.set_hour(11.0)
            state.update(phase=1, at=time.monotonic() + 6.0)
        elif p == 1:
            s = sounds()
            for name in ('tavern voices', 'market voices', 'shipyard at work', 'water at the wharf', 'fishing boat creaking 1'):
                check(f'by day: {name} plays', s[name].is_active() and s[name].is_playing())
            check('the bell waits for its interval', s['harbor bell'].is_active() and s['harbor bell'].get_strikes() == 0)
            clock.set_hour(22.5)
            state.update(phase=2, at=time.monotonic() + 7.0)
        elif p == 2:
            s = sounds()
            for name in ('market voices', 'shipyard at work'):
                check(f'at night: {name} falls quiet', not s[name].is_active() and not s[name].is_playing())
            for name in ('tavern voices', 'water at the jetty'):
                check(f'at night: {name} goes on', s[name].is_playing())
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
