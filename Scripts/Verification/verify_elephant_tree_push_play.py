"""Play: an elephant pushes a standing tree over, the tree stays down, and a hatchet still yields wood from it (owner, October 16:
tropical elephants push down trees; felled trees persist and yield wood). One player.
An elephant is stood 4.3 m from the nearest tree, facing it (re-stood if it wanders off, since this tests the push, not the roaming).
Checks: the tree is knocked over by the elephant alone; it is still in the world, not fading, with its full wood after the time a
player-felled tree would have faded away; one real hatchet strike (equipped, attack input) puts wood in the inventory.
Writes Saved/ElephantTreePushPlayResult.json."""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
tree_cls = unreal.load_class(None, '/Script/EW.EWHarvestTree')
elephants = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal)
             if 'Elephant' in str(a.get_editor_property('definition').get_editor_property('display_name'))]
assert elephants, 'no elephants in the map'
elephant = elephants[0]
assert elephant.get_editor_property('definition').get_editor_property('pushes_trees'), 'the elephant definition does not push trees'
trees = [t for t in unreal.GameplayStatics.get_all_actors_of_class(world, tree_cls) if not t.is_felled()]
home = elephant.get_actor_location()
tree = min(trees, key=lambda t: math.hypot(t.get_actor_location().x - home.x, t.get_actor_location().y - home.y))
tree_name = tree.get_name()
wood = tree.get_editor_property('wood')
hatchet = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatchet')
inventory = pawn.get_inventory_component()
report = {'tree': tree_name, 'tree_label': str(tree.get_actor_label()), 'checks': []}
state = {'t0': time.monotonic() + 12, 'phase': 0, 'handle': None}


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


def exists():
    return any(a.get_name() == tree_name for a in unreal.GameplayStatics.get_all_actors_of_class(world, tree_cls))


def stand_elephant():
    t = tree.get_actor_location()
    ang = math.radians(state.get('side', 0))
    x, y = t.x - math.cos(ang) * 430, t.y - math.sin(ang) * 430
    elephant.set_actor_location_and_rotation(unreal.Vector(x, y, t.z + 40), unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(ang)), False, True)
    pawn.teleport(unreal.Vector(t.x + 900, t.y + 900, t.z + 400), unreal.Rotator())


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    unreal.SystemLibrary.execute_console_command(world, 'slomo 1')
    report.update(success=error is None, error=error)
    Path(unreal.Paths.project_saved_dir(), 'ElephantTreePushPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ElephantTreePush success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['t0']:
        return
    try:
        p = state['phase']
        if p == 0:
            check('tree standing to start', not tree.is_felled() and exists())
            inventory.remove_item(wood, 100000)
            stand_elephant()
            unreal.SystemLibrary.execute_console_command(world, 'slomo 3')
            state.update(phase=1, start=now(), restood=now())
        elif p == 1:
            if tree.is_felled():
                report['felled_after_game_seconds'] = round(now() - state['start'], 1)
                state.update(phase=2, felled_at=now())
                unreal.SystemLibrary.execute_console_command(world, 'slomo 1')
                return
            if now() - state['restood'] > 4:      # it wandered off: put it back facing the tree
                state['restood'] = now()
                state['side'] = state.get('side', 0) + 70
                stand_elephant()
            if now() - state['start'] > 240:
                raise AssertionError('the elephant never knocked the tree over')
        elif p == 2:
            if now() - state['felled_at'] < 14:      # RemoveDelay 4 s + FadeSeconds 3 s for a player-felled tree: this one must outlast that
                return
            check('felled tree still lies there after the usual fade time', exists() and not tree.is_fading(), fade=tree.get_fade())
            check('felled tree still has its wood', tree.get_editor_property('wood_remaining') == 12, wood=tree.get_editor_property('wood_remaining'))
            loc = tree.get_actor_location()
            up = tree.get_actor_up_vector()      # a lying tree's up vector runs along the trunk, away from its base
            yaw = math.degrees(math.atan2(up.y, up.x))
            for lift in (96, 160, 260):      # at the trunk's base, facing along it
                if pawn.teleport(unreal.Vector(loc.x - up.x * 70, loc.y - up.y * 70, loc.z + lift), unreal.Rotator(roll=0, pitch=0, yaw=yaw)):
                    break
            eye, _ = pawn.get_actor_eyes_view_point()
            aim = unreal.Vector(loc.x + up.x * 70, loc.y + up.y * 70, loc.z + up.z * 70)
            pitch = -math.degrees(math.atan2(eye.z - aim.z, math.hypot(aim.x - eye.x, aim.y - eye.y)))
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
            inventory.add_item(hatchet, 1)
            check('hatchet equipped', lib.send_verification_equipment_request(pc, hatchet, unreal.EWEquipmentSlot.MAIN_HAND))
            state.update(phase=3, at=now() + 2.5)
        elif p == 3:
            if now() < state['at']:
                return
            eye, rot = pawn.get_actor_eyes_view_point()
            res = unreal.SystemLibrary.line_trace_single(world, eye, eye + unreal.MathLibrary.get_forward_vector(rot) * 400, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
            report.setdefault('traces', []).append([str(eye), str(rot), str(tree.get_actor_location()), str(tree.get_actor_rotation()), res.to_tuple()[9].get_name() if res else 'no hit'])
            check('attack input accepted', lib.send_verification_attack(pc, tree))
            state.update(phase=4, at=now() + 2.0)
        elif p == 4:
            if now() < state['at']:
                return
            got = inventory.get_item_count(wood)
            report['wood_after_one_strike'] = got
            if got == 0 and not state.get('retried'):
                state.update(retried=True, phase=3, at=now())
                return
            check('one strike on the felled tree gives wood', got >= 3, wood=got)
            check('the tree stock went down', tree.get_editor_property('wood_remaining') == 12 - got, left=tree.get_editor_property('wood_remaining'))
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
