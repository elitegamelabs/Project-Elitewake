"""Ten single first swings after drawing the Pickaxe, with no retry (T5).

Waits through the one-second swing cadence and aims at the boulder's bounds center. The same reachable test
boulder is restored between impacts so its finite resource count does not end the sequence early.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'PickaxeFirstSwingPlayResult.json')
T = '/Game/Elitewake/Items/Testing'
pickaxe, hatchet, stone = (unreal.load_asset(f'{T}/DA_Test{name}') for name in ('WoodenPickaxe', 'WoodenAxe', 'Stone'))
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter)
             if player_id(p) == player_id(pawn))
rocks = sorted(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWMineable),
               key=lambda r: (r.get_actor_location() - unreal.Vector(150, 0, 0)).length())
assert rocks, 'The map has no boulders.'
rock = rocks[0]
distance = 0
state = {'attempt': 0, 'phase': 'equip_hatchet', 'phase_at': time.monotonic(), 'pressed': False,
         'successes': [], 'handle': None, 'before': 0, 'target_label': rock.get_actor_label()}


def held(who):
    return who.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)


def count(who):
    return who.get_inventory_component().get_item_count(stone)


def face_target():
    center, extent = rock.get_actor_bounds(False)
    aim_point = center + unreal.Vector(0, 0, extent.z * .5)
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, aim_point))


def equip(item):
    assert lib.send_verification_equipment_request(client, item, unreal.EWEquipmentSlot.MAIN_HAND)
    state['phase_at'] = time.monotonic()


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'attempts': state['successes'],
                                  'error': error, 'target': state['target_label']}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK PickaxeFirstSwing success={error is None} error={error}')


def tick(delta):
    try:
        phase, now = state['phase'], time.monotonic()
        if state['attempt'] == 10:
            finish()
        elif phase == 'equip_hatchet':
            equip(hatchet)
            state['phase'] = 'wait_hatchet'
        elif phase == 'wait_hatchet':
            if held(owner) == hatchet and held(pawn) == hatchet and now - state['phase_at'] >= .5:
                global rock, distance
                _, extent = rock.get_actor_bounds(False)
                distance = max(extent.x, extent.y) + 55
                state['target_label'] = rock.get_actor_label()
                equip(pickaxe)
                state['phase'] = 'wait_pickaxe'
            elif now - state['phase_at'] > 5:
                raise TimeoutError(f'Could not equip Hatchet for attempt {state["attempt"] + 1}')
        elif phase == 'wait_pickaxe':
            if held(owner) == pickaxe and held(pawn) == pickaxe and now - state['phase_at'] >= .5:
                spot = rock.get_actor_location() + unreal.Vector(-distance, 0, 110)
                for who in (owner, pawn):
                    assert who.teleport(spot, unreal.Rotator()), 'Could not get beside the test boulder'
                    who.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
                face_target()
                state['before'] = count(owner)
                state['phase_at'] = now
                state['phase'] = 'settle'
            elif now - state['phase_at'] > 5:
                raise TimeoutError(f'Could not equip Pickaxe for attempt {state["attempt"] + 1}')
        elif phase == 'settle':
            face_target()
            if now - state['phase_at'] >= 1.0:
                assert lib.send_verification_gameplay_key(client, 'LeftMouseButton'), 'The first swing input was not accepted'
                state['pressed'] = True
                state['phase_at'] = now
                state['phase'] = 'wait_hit'
        elif phase == 'wait_hit':
            if count(owner) > state['before'] and count(pawn) > state['before']:
                state['successes'].append({'attempt': state['attempt'] + 1, 'stone': count(owner) - state['before'],
                                           'target': rock.get_actor_label()})
                # Keep the same confirmed, reachable fixture alive without changing the swing under test.
                rock.set_editor_property('remaining', 12)
                state['attempt'] += 1
                state['phase'] = 'equip_hatchet'
            elif now - state['phase_at'] >= 2.0:
                finish(f'First swing {state["attempt"] + 1} did not mine; held={held(owner)}, client held={held(pawn)}, '
                       f'rock={rock.get_actor_label()}, stone before={state["before"]}, after={count(owner)}')
    except Exception as error:
        finish(f'{error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
