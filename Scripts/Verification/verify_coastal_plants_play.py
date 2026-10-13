"""Client acceptance for the coast's hand-gathered plants: fiber plants, fallen sticks and berry bushes.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the plants from
Scripts/Setup/build_coastal_flora.py. Run unattended with run_play_check.py.

For the fiber plant, stick pile and berry bush nearest the spawn, the client stands beside it, looks at it and
presses E, as a player does: it gains the plant's whole amount (10 Fiber, 6 Sticks, 10 berries), and the plant is
gone, on server and client. Writes Saved/CoastalPlantsPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'CoastalPlantsPlayResult.json')
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
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}
KINDS = {'Fiber Plant': 10, 'Fallen Sticks': 6, 'Berry Bush': 10}


def plants(world, label):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHandGatherable) if a.get_actor_label().startswith(label)]


def alive(world, name):
    return any(a.get_name() == name for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHandGatherable))


def count(character, item):
    return character.get_inventory_component().get_item_count(item)


def census():
    found = {label: len(plants(server_world, label)) for label in KINDS}
    assert all(n >= 8 for n in found.values()), f'too few plants: {found}'
    state['memo']['plants'] = found


def go(label):
    def begin():
        spawn = unreal.Vector(150, 0, 0)
        plant = min(plants(server_world, label), key=lambda a: (a.get_actor_location() - spawn).length())
        item = plant.get_editor_property('item_definition')
        base = plant.get_actor_location()
        away = unreal.Vector(150 - base.x, -base.y, 0)
        away = away * (1.0 / max(away.length(), 1.0))
        spot = base + away * 110 + unreal.Vector(0, 0, 100)
        look = unreal.MathLibrary.find_look_at_rotation(spot + unreal.Vector(0, 0, 60), base + unreal.Vector(0, 0, 30))
        for p in (owner, pawn):
            assert p.teleport(spot, unreal.Rotator(roll=0, pitch=0, yaw=look.yaw)), f'no room beside {plant.get_actor_label()}'
            p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
        client.set_control_rotation(look)
        owner.get_controller().set_control_rotation(look)
        state['memo'].update(plant=plant.get_name(), label=plant.get_actor_label(), item=item, before=count(owner, item),
                             t=time.monotonic(), pressed=False)
    return begin


def gathered(amount):
    def done():
        m = state['memo']
        if not m['pressed']:
            if time.monotonic() - m['t'] < 0.8:
                return False
            assert lib.send_verification_gameplay_key(client, 'E')
            m['pressed'] = True
            return False
        want = m['before'] + amount
        if count(owner, m['item']) != want or count(pawn, m['item']) != want:
            return False
        return not alive(server_world, m['plant']) and not alive(client_world, m['plant'])
    return done


STEPS = [('Fiber plants, stick piles and berry bushes grow on the island and islet', lambda: None, lambda: census() or True, 3)]
for label, amount in KINDS.items():
    STEPS.append((f'Client presses E at the nearest {label.lower()}: +{amount}, and it is gone, on server and client', go(label), gathered(amount), 6))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    m = state['memo']
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error,
                                  'plants': m.get('plants'), 'last': m.get('label')}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK CoastalPlants success={error is None} error={error}')


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
