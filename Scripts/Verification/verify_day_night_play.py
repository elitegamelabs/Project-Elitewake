"""Client acceptance for day and night (owner: 90 real minutes of day, 90 of night). Needs Play in
/Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after setup_day_night.py. Run
unattended with run_play_check.py.

  1. The clock runs on server and client, the same hour on both, starting in the morning (08:00).
  2. It turns at one game hour per 450 real seconds (12 hours of day in 90 minutes), on both.
  3. Set to noon on the server, the client's sun stands 65 degrees up in the south and shines; no moon.
  4. Set to midnight, the client's sun is below the horizon and dark, and the moon is up.
  5. A client cannot set the clock.
Writes Saved/DayNightPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'DayNightPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
server_time = unreal.EWDayNightSubsystem.get_for_world(server_world)
client_time = unreal.EWDayNightSubsystem.get_for_world(client_world)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def lights(world):
    found = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.DirectionalLight)
    sun = next(a for a in found if 'EWSun' in [str(t) for t in a.tags])
    moon = next((a for a in found if 'EWMoon' in [str(t) for t in a.tags]), None)
    others = [f'{a.get_name()} pitch {a.get_actor_rotation().pitch:.0f}' for a in found if a not in (sun, moon)]
    assert not others, f'other directional lights would light the night: {others}'
    return sun, moon


def gap(a, b):
    d = abs(a - b) % 24
    return min(d, 24 - d)


def running():
    counts = {name: (len(unreal.GameplayStatics.get_all_actors_of_class(server_world, cls)), len(unreal.GameplayStatics.get_all_actors_of_class(client_world, cls)))
              for name, cls in (('clock', unreal.EWSkyClock), ('wind', unreal.EWWindState))}
    if not counts['clock'][1]:
        return False                                  # wait for it to arrive
    state['memo'].update(clock_server_client=str(counts))
    s, c = server_time.get_hour(), client_time.get_hour()
    assert gap(s, c) < .02, f'server {s:.3f} h, client {c:.3f} h'
    assert 8.0 <= s < 9.0, f'the world began at {s:.2f} h, not in the morning'
    state['memo'].update(start_hour=round(s, 3))
    return True


def begin_rate():
    state['memo'].update(t=time.monotonic(), h=server_time.get_hour(), hc=client_time.get_hour())


def rate():
    m = state['memo']
    if time.monotonic() - m['t'] < 6.0:
        return False
    seconds = time.monotonic() - m['t']
    per_hour = seconds / max(1e-6, server_time.get_hour() - m['h'])
    per_hour_client = seconds / max(1e-6, client_time.get_hour() - m['hc'])
    assert 380 < per_hour < 520 and 380 < per_hour_client < 520, (per_hour, per_hour_client)
    m.update(real_seconds_per_hour=round(per_hour), client_real_seconds_per_hour=round(per_hour_client))
    return True


def set_to(hour):
    def begin():
        server_time.set_hour(hour)
        state['memo']['t'] = time.monotonic()
    return begin


def noon():
    if gap(client_time.get_hour(), 12.0) > .02 or time.monotonic() - state['memo']['t'] < 1.0:
        return False
    sun, moon = lights(client_world)
    r = sun.get_actor_rotation()
    assert abs(r.pitch + 65) < 2 and abs(unreal.MathLibrary.normalize_axis(r.yaw - 90)) < 3, f'noon sun at pitch {r.pitch:.1f}, yaw {r.yaw:.1f}'
    assert sun.light_component.intensity > 1, sun.light_component.intensity
    assert moon is None or not moon.light_component.is_visible(), 'the moon is out at noon'
    state['memo'].update(noon_sun_pitch=round(r.pitch, 1), noon_sun_yaw=round(r.yaw, 1))
    return True


def midnight():
    if gap(client_time.get_hour(), 0.0) > .02 or time.monotonic() - state['memo']['t'] < 1.0:
        return False
    sun, moon = lights(client_world)
    r = sun.get_actor_rotation()
    assert r.pitch > 55, f'the midnight sun points {r.pitch:.1f} degrees (it should be under the horizon, shining up)'
    assert sun.light_component.intensity < .01, sun.light_component.intensity
    assert moon and moon.light_component.is_visible(), 'no moon at midnight'
    mr = moon.get_actor_rotation()
    assert mr.pitch < -55, f'the moon shines at pitch {mr.pitch:.1f}'
    state['memo'].update(midnight_moon_pitch=round(mr.pitch, 1))
    return True


def client_cannot():
    client_time.set_hour(15.0)
    time.sleep(.2)
    assert gap(server_time.get_hour(), 0.0) < .05, server_time.get_hour()
    return True


STEPS = [
    ('The clock runs on server and client, the same hour, starting in the morning', lambda: None, running, 6),
    ('It turns at one game hour per 450 real seconds on both', begin_rate, rate, 12),
    ("Noon set on the server: the client's sun stands 65 degrees up in the south, shining, no moon", set_to(12.0), noon, 6),
    ("Midnight: the client's sun is under the horizon and dark, and the moon is up", set_to(0.0), midnight, 6),
    ('A client cannot set the clock', lambda: None, client_cannot, 3),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    server_time.set_hour(8.0)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t', 'h', 'hc')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK DayNight success={error is None} error={error}')


def tick(delta):
    description, begin, done, timeout = STEPS[state['index']]
    try:
        if not state['begun']:
            begin()
            state.update(begun=True, deadline=time.monotonic() + timeout)
            return
        if done():
            checks.append(description)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
        elif time.monotonic() > state['deadline']:
            counts = {name: (len(unreal.GameplayStatics.get_all_actors_of_class(server_world, cls)), len(unreal.GameplayStatics.get_all_actors_of_class(client_world, cls)))
                      for name, cls in (('clock', unreal.EWSkyClock), ('wind', unreal.EWWindState))}
            raise TimeoutError(f'not done within {timeout} s; server {server_time.get_hour():.3f} h, client {client_time.get_hour():.3f} h; actors {counts}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
