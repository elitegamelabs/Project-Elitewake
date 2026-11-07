"""Client acceptance for swimming directions (owner, October 16: only forward and backward propel a swimmer; left and
right add no sideways movement, alone or with forward or back; see CLAUDE.md). Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one
client. Run unattended with run_play_check.py. Through the client's own keys, swimming in open water east of the
starter island, facing east:
  1. D alone: the survivor stays where they are (under 0.5 m of drift in 2 s, on both machines).
  2. W + D: they swim forward, east, with almost no sideways drift (under 5% of the way gone).
  3. S: they swim backward, west.
  4. On land again, D still steps sideways (strafing is unchanged).
Writes Saved/SwimDirectionsPlayResult.json.
"""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SwimDirectionsPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
pawn = client.get_controlled_pawn()


def player_id(p):
    s = p.get_editor_property('PlayerState')
    return json.loads(unreal.ToolsetLibrary.get_object_properties(s, ['PlayerId']))['PlayerId'] if s else None


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter)
             if player_id(p) is not None and player_id(p) == player_id(pawn))
WATER = unreal.Vector(9000, -300, -120)     # open water east of the starter island, deep enough to swim
LAND = unreal.Vector(150, 0, 200)           # the beach spawn
EAST = unreal.Rotator(0, 0, 0)
checks, measured = [], {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def keys(*held):
    for k in ('W', 'A', 'S', 'D'):
        lib.send_verification_gameplay_key_state(client, k, k in held)


def put(at):
    for p in (owner, pawn):
        assert p.teleport(at, EAST), f'no room at {at}'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    for c in (client, owner.get_controller()):
        c.set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=0))


def trial(where, held, judge, settle=2.0, hold=2.0):
    def begin():
        keys()
        put(where)
        state['memo'] = {'t': time.monotonic(), 'pressed': False}

    def done():
        m = state['memo']
        now = time.monotonic()
        if not m['pressed']:
            if now - m['t'] < settle:
                return False
            m.update(pressed=True, t=now, client_from=pawn.get_actor_location(), server_from=owner.get_actor_location())
            keys(*held)
            return False
        if now - m['t'] < hold:
            return False
        keys()
        for name, who, start in (('client', pawn, m['client_from']), ('server', owner, m['server_from'])):
            d = who.get_actor_location() - start
            judge(name, d.x, d.y, who)
        return True
    return begin, done


def swimming(who):
    return who.get_component_by_class(unreal.CharacterMovementComponent).is_swimming()


def still(name, dx, dy, who):
    assert swimming(who), f'the {name} survivor is not swimming'
    assert math.hypot(dx, dy) < 50, f'{name}: D alone moved the swimmer {dx:.0f}, {dy:.0f} cm'
    measured[f'D_alone_{name}_cm'] = round(math.hypot(dx, dy))


def forward_only(name, dx, dy, who):
    assert swimming(who), f'the {name} survivor is not swimming'
    assert dx > 200, f'{name}: W+D went only {dx:.0f} cm forward'
    assert abs(dy) < .05 * dx, f'{name}: W+D drifted {dy:.0f} cm sideways over {dx:.0f} cm forward'
    measured[f'W_D_{name}'] = {'forward_cm': round(dx), 'sideways_cm': round(dy)}


def backward(name, dx, dy, who):
    assert swimming(who), f'the {name} survivor is not swimming'
    assert dx < -100 and abs(dy) < 50, f'{name}: S moved {dx:.0f}, {dy:.0f} cm'
    measured[f'S_{name}_cm'] = round(dx)


def strafes(name, dx, dy, who):
    assert not swimming(who), f'the {name} survivor is swimming on the beach'
    assert dy > 200, f'{name}: D on land moved only {dy:.0f} cm sideways'
    measured[f'D_on_land_{name}_cm'] = round(dy)


STEPS = [('D alone in the water: the swimmer stays put', *trial(WATER, ('D',), still), 10),
         ('W + D in the water: forward only, no sideways drift', *trial(WATER, ('W', 'D'), forward_only), 10),
         ('S in the water: backward', *trial(WATER, ('S',), backward), 10),
         ('D on land: strafing is unchanged', *trial(LAND, ('D',), strafes), 10)]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    keys()
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK SwimDirections success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
