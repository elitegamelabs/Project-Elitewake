"""Client acceptance for the coastal palms: they stand on the ground, a client fells wood from one with the
starter axe through Left Mouse, and their trunks are solid.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the palms from
Scripts/Setup/build_coastal_flora.py and the test starter kit. Run unattended with run_play_check.py.

  1. At least 25 palms stand on the island and islet, each rooted in the ground with Wood and Thatch to give.
  2. The client equips the starter kit's wooden axe and strikes the palm nearest the spawn with Left Mouse:
     it gains 3 Wood and 1 Thatch, and the palm has that much less, on server and client.
  3. The client walks straight into the palm's trunk and is stopped by it.
Writes Saved/CoastalPalmsPlayResult.json.
"""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'CoastalPalmsPlayResult.json')
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
palms = [t for t in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarvestTree)
         if t.get_actor_label().startswith('Veyran Palm')]
folder = '/Game/Elitewake/Items/Testing'
axe, wood, thatch = (unreal.load_asset(f'{folder}/DA_Test{n}') for n in ('WoodenAxe', 'Wood', 'Thatch'))
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'input': None}


def peer(actor):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWHarvestTree) if a.get_name() == actor.get_name())


def counts(character):
    inv = character.get_inventory_component()
    return inv.get_item_count(wood), inv.get_item_count(thatch)


def rooted():
    assert len(palms) >= 25, f'only {len(palms)} palms'
    bad = []
    for t in palms:
        base = t.get_actor_location()
        hit = unreal.SystemLibrary.line_trace_single(server_world, base + unreal.Vector(0, 0, 60), base - unreal.Vector(0, 0, 200),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [t], unreal.DrawDebugTrace.NONE, True)
        gap = (base.z + 60 - hit.to_tuple()[4].z) if hit else None
        if gap is None or gap > 90 or t.get_editor_property('wood_remaining') <= 0 or t.get_editor_property('blocker_radius') <= 0:
            bad.append((t.get_actor_label(), gap))
    assert not bad, f'palms not rooted or empty: {bad[:5]}'
    state['memo']['palms'] = len(palms)


def nearest():
    spawn = unreal.Vector(150, 0, 0)
    return min(palms, key=lambda t: (t.get_actor_location() - spawn).length())


def equip():
    assert lib.send_verification_equipment_request(client, axe, unreal.EWEquipmentSlot.MAIN_HAND)


def equipped():
    return owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) == axe


def approach(distance):
    """Stand `distance` from the palm's trunk on the side toward the spawn, facing it, and settle."""
    tree = nearest()
    base = tree.get_actor_location()
    away = unreal.Vector(150 - base.x, -base.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = base + away * distance + unreal.Vector(0, 0, 110)
    look = unreal.MathLibrary.find_look_at_rotation(spot + unreal.Vector(0, 0, 60), base + unreal.Vector(0, 0, 120))
    for p in (owner, pawn):
        assert p.teleport(spot, unreal.Rotator(roll=0, pitch=0, yaw=look.yaw)), 'no room beside the palm'
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
    m['pool'] = (m['tree'].get_editor_property('wood_remaining'), m['tree'].get_editor_property('thatch_remaining'))
    assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def felled():
    m = state['memo']
    tree, (w0, t0) = m['tree'], m['before']
    want = (w0 + 3, t0 + 1)
    if counts(owner) != want or counts(pawn) != want:
        return False
    pool = (tree.get_editor_property('wood_remaining'), tree.get_editor_property('thatch_remaining'))
    seen = (peer(tree).get_editor_property('wood_remaining'), peer(tree).get_editor_property('thatch_remaining'))
    if pool != (m['pool'][0] - 3, m['pool'][1] - 1) or seen != pool:
        return False
    return True


def walk_in():
    approach(150)
    look = state['memo']['look']
    state['input'] = lambda: (client.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=look.yaw)), pawn.do_move(0, 1))


def stopped():
    m = state['memo']
    if time.monotonic() - m['t'] < 1.8:
        return False
    state['input'] = None
    base = m['tree'].get_actor_location()
    gap = min(math.hypot(p.get_actor_location().x - base.x, p.get_actor_location().y - base.y) for p in (owner, pawn))
    m['closest'] = round(gap)
    radius = m['tree'].get_editor_property('blocker_radius')
    assert gap >= radius + 25, f'walked to {gap:.0f} cm of the trunk axis; the trunk is {radius:.0f} cm'
    return True


STEPS = [
    ('At least 25 palms stand rooted on the island and islet, with Wood and Thatch to give', lambda: None, lambda: rooted() or True, 3),
    ('Client equips the starter wooden axe', equip, equipped, 6),
    ('', lambda: approach(110), settle_then(strike), 4),
    ('Client strikes the nearest palm with Left Mouse: +3 Wood, +1 Thatch, and the palm gives that up, on server and client', lambda: None, felled, 5),
    ('Client walks into the palm and its trunk stops it', walk_in, stopped, 5),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    m = state['memo']
    RESULT.write_text(json.dumps({'success': error is None, 'checks': [c for c in checks if c], 'error': error,
                                  'palms': m.get('palms'), 'closest_to_trunk': m.get('closest'),
                                  'tree': m['tree'].get_actor_label() if m.get('tree') else None}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK CoastalPalms success={error is None} error={error}')


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
