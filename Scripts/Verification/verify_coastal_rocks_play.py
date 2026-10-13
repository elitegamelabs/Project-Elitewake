"""Client acceptance for the coastal boulders: they sit in the ground, a client mines Stone from one with the
starter pickaxe through Left Mouse, and they are solid.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the boulders from
Scripts/Setup/build_coastal_rocks.py and the test starter kit. Run unattended with run_play_check.py.

  1. At least 15 boulders sit on the island and islet, each bedded in the ground with Stone to give.
  2. The client equips the starter kit's wooden pickaxe and strikes the boulder nearest the spawn with Left Mouse:
     it gains 3 Stone, and the boulder has that much less, on server and client.
  3. The client walks straight into the boulder and is stopped at its face or climbs over it, never through it.
Writes Saved/CoastalRocksPlayResult.json.
"""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'CoastalRocksPlayResult.json')
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
rocks = [t for t in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWMineable)
         if t.get_actor_label().startswith('Boulder')]
folder = '/Game/Elitewake/Items/Testing'
pickaxe, stone = (unreal.load_asset(f'{folder}/DA_Test{n}') for n in ('WoodenPickaxe', 'Stone'))
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'input': None}


def peer(actor):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWMineable) if a.get_name() == actor.get_name())


def counts(character):
    return character.get_inventory_component().get_item_count(stone)


def rooted():
    assert len(rocks) >= 15, f'only {len(rocks)} boulders'
    bad = []
    for t in rocks:
        base = t.get_actor_location()
        hit = unreal.SystemLibrary.line_trace_single(server_world, base + unreal.Vector(0, 0, 20), base - unreal.Vector(0, 0, 200),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [t], unreal.DrawDebugTrace.NONE, True)
        gap = (base.z + 20 - hit.to_tuple()[4].z) if hit else None
        if gap is None or gap > 60 or t.get_editor_property('remaining') <= 0:
            bad.append((t.get_actor_label(), gap))
    assert not bad, f'boulders floating or empty: {bad[:5]}'
    state['memo']['rocks'] = len(rocks)


def nearest():
    spawn = unreal.Vector(150, 0, 0)
    return min(rocks, key=lambda t: (t.get_actor_location() - spawn).length())


def reach():
    """How far from the nearest boulder's centre its face is, from its bounds."""
    _, extent = nearest().get_actor_bounds(False)
    return max(extent.x, extent.y)


def equip():
    assert lib.send_verification_equipment_request(client, pickaxe, unreal.EWEquipmentSlot.MAIN_HAND)


def equipped():
    return owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) == pickaxe


def approach(distance):
    """Stand `distance` from the boulder's centre on the side toward the spawn, facing it, and settle."""
    tree = nearest()
    base = tree.get_actor_location()
    away = unreal.Vector(150 - base.x, -base.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = base + away * distance + unreal.Vector(0, 0, 110)
    look = unreal.MathLibrary.find_look_at_rotation(spot + unreal.Vector(0, 0, 60), base + unreal.Vector(0, 0, 20))
    for p in (owner, pawn):
        assert p.teleport(spot, unreal.Rotator(roll=0, pitch=0, yaw=look.yaw)), 'no room beside the boulder'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    client.set_control_rotation(look)
    owner.get_controller().set_control_rotation(look)
    state['memo'].update(tree=tree, look=look, t=time.monotonic())


def settle_then(action):
    def done():
        if time.monotonic() - state['memo']['t'] < 0.8:
            return False
        action()
        return True
    return done


def strike():
    m = state['memo']
    m['before'] = counts(owner)
    m['pool'] = m['tree'].get_editor_property('remaining')
    assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def mined():
    m = state['memo']
    rock, want = m['tree'], m['before'] + 3
    if counts(owner) != want or counts(pawn) != want:
        return False
    return rock.get_editor_property('remaining') == m['pool'] - 3 and peer(rock).get_editor_property('remaining') == m['pool'] - 3


def walk_in():
    approach(reach() + 140)
    look = state['memo']['look']
    m = state['memo']
    m.update(start_z=owner.get_actor_location().z, nearest=1e9, rise=0.0)
    base = m['tree'].get_actor_location()

    def push():
        client.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=look.yaw))
        pawn.do_move(0, 1)
        here = owner.get_actor_location()
        m['nearest'] = min(m['nearest'], math.hypot(here.x - base.x, here.y - base.y))
        m['rise'] = max(m['rise'], here.z - m['start_z'])
    state['input'] = push


def stopped():
    """The boulder is solid: a walker into it is either stopped at its face or climbs up over it, never through."""
    m = state['memo']
    if time.monotonic() - m['t'] < 2.5:
        return False
    state['input'] = None
    m['closest'], m['climbed'] = round(m['nearest']), round(m['rise'])
    assert m['nearest'] >= 0.5 * reach() or m['rise'] >= 25, f"passed {m['nearest']:.0f} cm from the centre without rising ({m['rise']:.0f} cm)"
    return True


STEPS = [
    ('At least 15 boulders sit bedded in the island and islet, with Stone to give', lambda: None, lambda: rooted() or True, 3),
    ('Client equips the starter wooden pickaxe', equip, equipped, 6),
    ('', lambda: approach(reach() + 55), settle_then(strike), 4),
    ('Client strikes the nearest boulder with Left Mouse: +3 Stone, and the boulder gives that up, on server and client', lambda: None, mined, 5),
    ('Client walks into the boulder and is stopped by it or climbs over it, never through it', walk_in, stopped, 6),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    m = state['memo']
    RESULT.write_text(json.dumps({'success': error is None, 'checks': [c for c in checks if c], 'error': error,
                                  'rocks': m.get('rocks'), 'closest_to_centre': m.get('closest'), 'climbed_cm': m.get('climbed'),
                                  'tree': m['tree'].get_actor_label() if m.get('tree') else None}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK CoastalRocks success={error is None} error={error}')


def tick(delta):
    if state['input']:
        state['input']()
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
