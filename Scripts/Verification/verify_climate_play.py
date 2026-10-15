"""Client acceptance for the regions and their climate (owner's five regions and climate rules, October 14).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after
Scripts/Setup/build_coastal_terrain.py and build_regions.py. Run unattended with run_play_check.py.

  1. On the beach the survivor is in the Desert: hot and humid on both machines, the HUD's climate line says so with
     its humidity; bare-skinned, the body stays at 37 C and does not overheat (owner: clothing causes overheating).
  2. The Desert's humidity reaches 100 m offshore and fades into the open sea's; past that is the Open Sea.
  3. Walking onto the Winter island: the region's name crosses the screen, the line reads WINTER -12 C, a Cold
     notice shows and the body cools, on the client.
  4. Cooled past 35 C the survivor is Freezing: the notice shows and health falls, on server and client.
  5. Back in the Desert the body warms again and the Freezing notice clears.
Writes Saved/ClimatePlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ClimatePlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
BEACH = unreal.Vector(150, 0, 150)
WINTER = unreal.Vector(1800, 15800, 400)
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def hud():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWSurvivalWidget, False)
                if w.get_owning_player() == client)


def survival(who):
    return who.get_survival_component()


def notices(who):
    return {str(n.get_editor_property('id')) for n in survival(who).get_debuff_notices()}


def go(spot):
    def begin():
        for p in (owner, pawn):
            assert p.teleport(spot, unreal.Rotator())
        state['memo']['t'] = time.monotonic()
    return begin


def in_desert():
    if time.monotonic() - state['memo']['t'] < 2.0:
        return False
    for who in (owner, pawn):
        c = survival(who).get_climate()
        if c.region != unreal.EWRegion.DESERT:
            return False
        assert abs(survival(who).get_felt_temperature() - 34) < .5 and abs(c.humidity - 75) < .5, (survival(who).get_felt_temperature(), c.humidity)
    line = str(hud().get_displayed_climate())
    assert line.startswith('DESERT') and 'Humidity 75%' in line, line
    assert abs(survival(owner).get_body_temperature() - 37) < .05 and abs(survival(owner).get_target_body_temperature() - 37) < .05
    assert not ({'Overheating', 'Warming'} & notices(pawn)), notices(pawn)
    state['memo']['desert_line'] = line
    return True


def offshore():
    sample = lambda x, y: unreal.EWClimateRegion.sample_climate(server_world, unreal.Vector(x, y, 0))   # noqa: E731
    # South of the island: its oval (with 15 m of shallows) ends near y = -5900; 50 m out, then 150 m out.
    near, far = sample(-800, -11000), sample(-800, -26000)
    assert near.region == unreal.EWRegion.DESERT and 60 < near.humidity < 75, (near.region, near.humidity)
    assert far.region == unreal.EWRegion.OPEN_SEA and abs(far.humidity - 60) < .5 and abs(far.air_temperature - 22) < .5, (far.region, far.humidity)
    state['memo'].update(humidity_50m_out=round(near.humidity, 1), open_sea=f'{far.air_temperature:.0f} C {far.humidity:.0f}%')
    return True


def in_winter():
    m = state['memo']
    if time.monotonic() - m['t'] < 1.5:
        return False
    c = survival(pawn).get_climate()
    if c.region != unreal.EWRegion.WINTER or survival(owner).get_climate().region != unreal.EWRegion.WINTER:
        return False
    line = str(hud().get_displayed_climate())
    assert line.startswith('WINTER') and '-12' in line, line
    banner = str(hud().get_displayed_region_banner())
    assert banner == 'Winter', f'banner {banner!r}'
    if 'Cold' not in notices(pawn):
        return False
    m.update(winter_line=line, body_on_arrival=round(survival(pawn).get_body_temperature(), 2), t=time.monotonic())
    return True


def cooling():
    m = state['memo']
    if time.monotonic() - m['t'] < 4.0:
        return False
    body = survival(pawn).get_body_temperature()
    assert body < m['body_on_arrival'] - .1, f'not cooling: {body}'
    assert survival(owner).get_target_body_temperature() < 35, survival(owner).get_target_body_temperature()
    m['body_after_4s'] = round(body, 2)
    # Hurry on to the edge of freezing rather than wait out the cooling.
    survival(owner).set_body_temperature(35.2)
    m['health_before'] = survival(owner).get_health()
    return True


def freezing():
    m = state['memo']
    if not (survival(owner).is_freezing() and 'Freezing' in notices(pawn)):
        return False
    if survival(owner).get_health() >= m['health_before'] - .5 or survival(pawn).get_health() >= m['health_before'] - .5:
        return False
    m['health_freezing'] = round(survival(pawn).get_health(), 1)
    return True


def warmed():
    m = state['memo']
    if time.monotonic() - m['t'] < 1.0:
        return False
    if survival(pawn).get_climate().region != unreal.EWRegion.DESERT or 'Freezing' in notices(pawn):
        return False
    if survival(owner).get_body_temperature() <= 35.2:
        return False
    m['body_warming'] = round(survival(owner).get_body_temperature(), 2)
    return True


STEPS = [
    ('On the beach: Desert, 34 C and 75% humidity on both machines and the HUD; bare skin stays at 37 C', go(BEACH), in_desert, 6),
    ("The Desert's humidity reaches out 100 m and fades; beyond is the Open Sea", lambda: None, offshore, 2),
    ('On the Winter island: the banner, WINTER -12 C, a Cold notice, on the client', go(WINTER), in_winter, 6),
    ('There the body cools', lambda: None, cooling, 8),
    ('Past 35 C: Freezing, and health falls on server and client', lambda: None, freezing, 8),
    ('Back in the Desert the body warms and Freezing clears', go(BEACH), warmed, 10),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k != 't'}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Climate success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; body {survival(owner).get_body_temperature():.2f}, '
                               f'notices {notices(pawn)}, line {hud().get_displayed_climate()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
