"""Client acceptance for winter snow (owner: winter snow; snow-covered wild berries). Needs Play in
/Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after build_snowfall.py and
build_coastal_flora.py. Run unattended with run_play_check.py.

  1. Every Winter fiber plant and berry bush carries snow (the snowy frond material), on server and client; no
     plant elsewhere does.
  2. On open ground on a Winter island, snow falls round the client's survivor, on the client only (the server does
     not draw it for someone else's survivor, and the host's own survivor in the Plains has none).
  3. Inside a Winter cave the snow stops; back outside it falls again.
  4. Back on the starter island (Plains), no snow.
Writes Saved/SnowPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SnowPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()
host_pawn = host.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}
SNOWY = 'M_PalmFrondSnow_v1'


def snowing(character):
    comp = character.get_component_by_class(unreal.EWSnowfallComponent)
    return bool(comp and comp.is_snowing())


def plants_dressed():
    counts = {'winter': 0, 'snowy_elsewhere': 0}
    for world in (server_world, client_world):
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHandGatherable):
            label = a.get_actor_label()
            if not label.startswith(('Fiber Plant', 'Berry Bush')):
                continue
            p = a.get_actor_location()
            region = W.region_of(p.x, p.y)
            mesh = a.get_editor_property('mesh')
            names = [m.get_name() if m else '' for m in mesh.get_materials()]
            if region == 'Winter':
                assert SNOWY in names, f'{label} on a Winter island has no snow ({names})'
                counts['winter'] += 1
            elif SNOWY in names:
                counts['snowy_elsewhere'] += 1
    assert counts['winter'] >= 10 and not counts['snowy_elsewhere'], counts
    state['memo'].update(snowy_winter_plants=counts['winter'] // 2)
    return True


def open_ground():
    """A flat, open spot on Winter1, away from trees, rocks and the cave."""
    i = W.island('Winter1')
    best = None
    for k in range(200):
        a, r = k * 2.39996, (k / 200) ** .5 * i.reach() * .6
        x, y = i.cx + r * math.cos(a), i.cy + r * math.sin(a)
        if i.distance(x, y) > -1500 or T.near_cave(x, y, 1500):
            continue
        z = T.height(x, y)
        if best is None or abs(z - 600) < abs(best[2] - 600):
            best = (x, y, z)
    return best


def go(x, y, z):
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(x, y, z), unreal.Rotator()), f'no room at ({x:.0f}, {y:.0f}, {z:.0f})'
    state['memo']['t'] = time.monotonic()


def to_winter():
    x, y, z = open_ground()
    go(x, y, z + 150)


def falls():
    if time.monotonic() - state['memo']['t'] < 2.5:
        return False
    climate = pawn.get_survival_component().get_climate()
    assert climate.region == unreal.EWRegion.WINTER, f'the client is in {climate.region}'
    assert snowing(pawn), 'no snow round the client in the Winter region'
    assert not snowing(owner), 'the server draws snow for the client\'s survivor'
    assert not snowing(host_pawn), 'the host survivor in the Plains has snow'
    return True


def into_cave():
    c = T.CAVES['Winter3']
    x, y = c.world(c.chamber_u, 0)
    go(x, y, c.floor + 120)


def stops():
    if time.monotonic() - state['memo']['t'] < 2.5:
        return False
    assert pawn.get_survival_component().get_climate().region == unreal.EWRegion.WINTER
    assert not snowing(pawn), 'it snows inside the cave'
    return True


def out_of_cave():
    c = T.CAVES['Winter3']
    x, y = c.world(-900, 0)
    go(x, y, T.height(x, y) + 150)


def to_plains():
    go(150, 0, T.height(150, 0) + 150)


def none_here():
    if time.monotonic() - state['memo']['t'] < 2.5:
        return False
    assert not snowing(pawn), 'snow on the starter island'
    return True


STEPS = [
    ('Every Winter fiber plant and berry bush carries snow, on server and client; no plant elsewhere does', lambda: None, plants_dressed, 6),
    ('Snow falls round the client on open Winter ground, drawn only by the client', to_winter, falls, 12),
    ('Inside a Winter cave the snow stops', into_cave, stops, 10),
    ('Back outside, it falls again', out_of_cave, falls, 10),
    ('On the starter island, no snow', to_plains, none_here, 10),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k != 't'}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Snow success={error is None} error={error}')


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
            p = pawn.get_actor_location()
            raise TimeoutError(f'not done within {timeout} s; survivor at ({p.x:.0f}, {p.y:.0f}, {p.z:.0f})')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
