"""Client acceptance for the island's freshwater pond.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after
build_freshwater_pond.py and build_fish.py. Run unattended with run_play_check.py.

  1. Bass and catfish live in the pond on server and client: under its surface, within its banks. No piranhas
     (owner, October 31: they left the starter pond).
  2. A survivor who wades into the middle swims, on server and client.
  3. Nothing in the pond bites: health holds for 8 s on both.
  4. Out on the bank, the survivor walks again and no fish is after them.
Writes Saved/FreshwaterPondPlayResult.json.
"""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'FreshwaterPondPlayResult.json')
POND, RADIUS, SURFACE = (-1700.0, 1500.0), 700.0, 5.0
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
FRESH = ('Bass', 'Catfish', 'Piranha')
STOCK = ('Bass', 'Catfish')


def kind(f):
    return str(f.get_editor_property('definition').get_editor_property('display_name'))


def pond_fish(world):
    return [f for f in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWFish) if kind(f) in FRESH]


checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def mode(who):
    return who.get_component_by_class(unreal.CharacterMovementComponent).movement_mode


def place(x, y, z):
    for p in (owner, pawn):
        p.set_actor_location(unreal.Vector(x, y, z), False, True)


def stocked():
    server, seen = pond_fish(server_world), pond_fish(client_world)
    kinds = sorted({kind(f) for f in server})
    assert kinds == sorted(STOCK), f'pond holds {kinds}'
    assert len(seen) == len(server), f'client sees {len(seen)} of {len(server)}'
    for f in server:
        at = f.get_actor_location()
        assert math.hypot(at.x - POND[0], at.y - POND[1]) < RADIUS and at.z < SURFACE, f'{kind(f)} out of the pond at {at}'
    state['memo']['fish'] = len(server)
    return True


def wade_in():
    place(POND[0], POND[1], SURFACE - 60)
    state['memo']['health_before'] = owner.get_survival_component().get_health()
    state['memo']['waded_at'] = time.monotonic()


def swimming():
    return mode(owner) == unreal.MovementMode.MOVE_SWIMMING and mode(pawn) == unreal.MovementMode.MOVE_SWIMMING


def unharmed():
    before = state['memo']['health_before']
    for who in (owner, pawn):
        assert who.get_survival_component().get_health() >= before, 'bitten in the starter pond'
    assert not any(f.get_quarry() == owner for f in pond_fish(server_world)), 'a fish is hunting the swimmer'
    return time.monotonic() - state['memo']['waded_at'] >= 8.0


def climb_out():
    place(-1110.0, 1021.0, 120.0)
    owner.get_survival_component().restore_health(100)


def ashore():
    if mode(owner) == unreal.MovementMode.MOVE_SWIMMING:
        return False
    return not any(f.get_quarry() == owner for f in pond_fish(server_world))


STEPS = [
    ('Bass and catfish (no piranhas) live in the pond, under its surface and within its banks, on server and client', lambda: None, stocked, 5),
    ('A survivor in the middle of the pond swims, on server and client', wade_in, swimming, 5),
    ('Nothing in the pond bites the swimmer: health holds for 8 s on server and client', lambda: None, unharmed, 15),
    ('On the bank the survivor walks again and no fish is after them', climb_out, ashore, 6),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': state['memo']}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK FreshwaterPond success={error is None} error={error}')


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
            hunting = sum(1 for f in pond_fish(server_world) if f.get_quarry() == owner)
            raise TimeoutError(f'not done within {timeout} s; survivor {mode(owner)}, health '
                               f'{owner.get_survival_component().get_health():.0f}, fish hunting {hunting}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
