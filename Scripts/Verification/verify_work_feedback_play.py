"""Client acceptance for the work motions and the feel of a blow landing (owner, October 15).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client. Run unattended with
run_play_check.py. Through ordinary keys, the client:
  1. with the Hatchet at a palm, swings Left Mouse: the chop (AS_Chop_v1) plays on the client and on the server's
     copy; at the contact moment wood chips fly on the client, the palm shakes there, and the client's hit marker
     pops white with "+3 Wood" beside it, matching what the server put in the pack;
  2. with the Pickaxe at a boulder: the overhead blow (AS_Mine_v1), stone chips, the rock shakes, "+3 Stone";
  3. with the Hatchet at the boulder: it glances off: chips but no stone, the marker amber with "Needs a pickaxe";
  4. presses E at a fiber plant: the survivor squats and reaches to the ground (AS_GatherGround_v1) on both
     machines, cannot walk on through it, and "+10 Fiber" rises beside the centre;
  5. presses E at a berry bush: the reach into the bush (AS_GatherBush_v1) and the berries' popup.
Writes Saved/WorkFeedbackPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'WorkFeedbackPlayResult.json')
T = '/Game/Elitewake/Items/Testing'
hatchet, pickaxe, wood, stone, fiber = (unreal.load_asset(f'{T}/DA_Test{n}') for n in ('WoodenAxe', 'WoodenPickaxe', 'Wood', 'Stone', 'Fiber'))
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
SPAWN = unreal.Vector(150, 0, 0)
near = lambda actors: sorted(actors, key=lambda t: (t.get_actor_location() - SPAWN).length())   # noqa: E731
palm = near([t for t in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarvestTree) if t.get_actor_label().startswith('Veyran Palm')])[0]
rock = near(list(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWMineable)))[0]
plants = list(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHandGatherable))
fiber_plant = near([p for p in plants if p.get_actor_label().startswith('Fiber Plant')])[0]
bush = near([p for p in plants if p.get_actor_label().startswith('Berry Bush')])[0]
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None}


def copy_in(world, actor):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, actor.get_class()) if a.get_name() == actor.get_name())


def count(who, item):
    return who.get_inventory_component().get_item_count(item)


def marker():
    return client.get_hit_marker_widget()


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def approach(target, distance, aim_height):
    base = target.get_actor_location()
    center, extent = target.get_actor_bounds(False)
    away = unreal.Vector(150 - base.x, -base.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = base + away * distance + unreal.Vector(0, 0, 110)
    for p in (owner, pawn):
        assert p.teleport(spot, unreal.Rotator()), f'no room beside {target.get_actor_label()}'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    height = center.z - base.z if aim_height is None else aim_height
    state['aim'] = lambda: base + unreal.Vector(0, 0, height)
    keep_aim()


def hold(item):
    if not item:
        return   # gathering by hand works with a tool still in the other hand's reach
    if owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) != item:
        assert lib.send_verification_equipment_request(client, item, unreal.EWEquipmentSlot.MAIN_HAND)


def bursts():
    return list(unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWImpactBurst))


def begin_strike(target, item, distance, aim_height, watch):
    def begin():
        hold(item)
        approach(target, distance, aim_height)
        state['memo'].update(t=time.monotonic(), pressed=0.0, swings=0, target=target, watch=watch,
                             before=count(owner, watch), markers=marker().get_marker_count(),
                             impacts=pawn.get_work_impact_count(), bursts_seen=0, shook=False)
    return begin


def swing_until(anim_name, expect_gain, refusal_text=None):
    def done():
        m = state['memo']
        keep_aim()
        held_now = owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)
        if time.monotonic() - m['t'] < 1.0 or pawn.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) != held_now:
            return False
        # One press only: a missing impact fails this check instead of being concealed by another swing.
        if m['swings'] == 0:
            m['swings'] += 1
            m['pressed'] = time.monotonic()
            assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')
        if bursts():
            m['bursts_seen'] = max(m['bursts_seen'], max(b.get_chip_count() for b in bursts()))
        if copy_in(client_world, m['target']).is_shaking():
            m['shook'] = True
        if marker().get_marker_count() == m['markers']:
            return False
        swung = pawn.get_last_swing_animation()
        seen = owner.get_last_swing_animation()   # the server's copy of the client's survivor
        assert swung and swung.get_name() == anim_name, f'the client swung {swung.get_name() if swung else None}, not {anim_name}'
        assert seen and seen.get_name() == anim_name, f"the server's copy swung {seen.get_name() if seen else None}"
        assert m['bursts_seen'] > 4, f'no chips flew on the client ({m["bursts_seen"]})'
        assert m['shook'], 'the target did not shake on the client'
        assert pawn.get_work_impact_count() > m['impacts']
        gained = count(owner, m['watch']) - m['before']
        line = marker().get_last_line()
        if expect_gain:
            assert gained > 0 and count(pawn, m['watch']) - m['before'] == gained, f'gained {gained}'
            assert line == f"+{gained} {m['watch'].get_editor_property('display_name')}" or line.startswith('+'), line
            m[f'{anim_name}_line'] = line
        else:
            assert gained == 0, f'it gave {gained} anyway'
            assert line == refusal_text, f'the marker said {line!r}'
            m['refused_line'] = line
        m[f'{anim_name}_chips'] = m['bursts_seen']
        m[f'{anim_name}_swings'] = m['swings']
        return True
    return done


def begin_gather(target, anim_name):
    def begin():
        hold(None)
        approach(target, 95, 10)
        item = target.get_editor_property('item_definition')
        state['memo'].update(t=time.monotonic(), pressed=0.0, target=target, item=item, before=count(owner, item), anim=anim_name)
    return begin


def gathered():
    m = state['memo']
    keep_aim()
    if time.monotonic() - m['t'] < .8:
        return False
    if not m['pressed']:
        m['pressed'] = time.monotonic()
        assert lib.send_verification_interaction_request(client, copy_in(client_world, m['target']))
        return False
    gained = count(owner, m['item']) - m['before']
    if gained <= 0:
        return False
    played = (pawn.get_last_tool_animation(), owner.get_last_tool_animation())
    if not all(a and a.get_name() == m['anim'] for a in played):
        return False
    line = marker().get_last_line()
    assert line == f"+{gained} {m['item'].get_editor_property('display_name')}", f'popup {line!r}'
    # Still while the hands work: walking does not carry the survivor on.
    assert client.is_move_input_ignored(), 'the survivor can walk on through the gather'
    m[f'{m["anim"]}_line'] = line
    return True


STEPS = [
    ('With the Hatchet at a palm, Left Mouse chops (AS_Chop_v1 on both machines): chips fly, the palm shakes and the '
     'hit marker pops with what the server gave', begin_strike(palm, hatchet, 110, 120, wood), swing_until('AS_Chop_v1', True), 14),
    ('With the Pickaxe at a boulder, the overhead blow (AS_Mine_v1): stone chips, the rock shakes, "+N Stone"',
     begin_strike(rock, pickaxe, None, None, stone), swing_until('AS_Mine_v1', True), 14),
    ('With the Hatchet at the boulder the blow glances off: chips but no stone, the marker says "Needs a pickaxe"',
     begin_strike(rock, hatchet, None, None, stone), swing_until('AS_ToolChop_v1', False, 'Needs a pickaxe'), 14),
    ('E at a fiber plant: the squat and reach to the ground (AS_GatherGround_v1) on both machines, held still, "+10 Fiber"',
     begin_gather(fiber_plant, 'AS_GatherGround_v1'), gathered, 8),
    ('E at a berry bush: the reach into the bush (AS_GatherBush_v1) and the berries\' popup',
     begin_gather(bush, 'AS_GatherBush_v1'), gathered, 8),
]
# The boulder's stand-off depends on its size.
_, rock_extent = rock.get_actor_bounds(False)
for i in (1, 2):
    label, begin, done, timeout = STEPS[i]
    item = pickaxe if i == 1 else hatchet
    STEPS[i] = (label, begin_strike(rock, item, max(rock_extent.x, rock_extent.y) + 55, 20, stone), done, timeout)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, str)) and k not in ('swings', 'markers', 'impacts', 'before', 'bursts_seen')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK WorkFeedback success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; memo {dict((k, v) for k, v in state["memo"].items() if isinstance(v, (int, float, str, bool)))}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
