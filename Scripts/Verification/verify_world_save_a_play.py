"""Play, first half of the world-state save round trip (M7 persistence, October 30). One player, the coastal map. Changes the map's
own resources the way play does, then saves (single-player Save Game, slot WorldSaveTest) and writes what it expects back to
Saved/WorldSaveExpected.json for verify_world_save_b_play, which loads it in a fresh Play session:
  - a tree is knocked over (left lying, as an elephant leaves one);
  - another is cut down to nothing (it falls, fades and is gone);
  - a hand gatherable (fibre, sticks or berries) is picked clean through a real interaction request (gone);
  - a ruby deposit in the starter island's cave is mined with a metal pickaxe through real swings (partly mined);
  - the survivor's pack (seven wood, two hide) is dropped in a death bag at the cave mouth, as a death leaves it.
Writes Saved/WorldSaveAPlayResult.json."""
import json
import math
import time
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
cave = T.CAVES['Starter']
metal = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestMetalPickaxe')
report = {'checks': []}
state = {'phase': 'start', 'at': time.monotonic() + 12, 'handle': None, 'strikes': 0, 'tries': 0}
expected = {}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'WorldSaveAPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK WorldSaveA success={error is None} error={error}')


def startup(cls):
    # Everything of these kinds in a fresh map is placed in it (not spawned in play).
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, cls))


def near(actors, to, n):
    return sorted(actors, key=lambda a: (a.get_actor_location() - to).length())[:n]


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 'start':
            here = pawn.get_actor_location()
            trees = [t for t in near(startup(unreal.EWHarvestTree), here, 12) if not t.is_felled()]
            check('trees stand near the start', len(trees) >= 2)
            lying, gone = trees[0], trees[1]
            check('one tree is knocked over', lying.fell(unreal.Vector(1, 0, 0)))
            check('another is cut down', gone.cut_down(None))
            expected['lying_tree'] = lying.get_name()
            expected['gone_tree'] = gone.get_name()
            plants = near(startup(unreal.EWHandGatherable), here, 6)
            check('a hand gatherable grows near the start', plants)
            state['plant'] = plants[0]
            expected['gone_plant'] = plants[0].get_name()
            loc = plants[0].get_actor_location()
            pawn.teleport(unreal.Vector(loc.x + 120, loc.y, loc.z + 100), unreal.Rotator())
            state.update(phase='pick', at=time.monotonic() + 1.5)
        elif p == 'pick':
            loc = state['plant'].get_actor_location()
            eye, _ = pawn.get_actor_eyes_view_point()
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, loc))
            lib.send_verification_interaction_request(pc, state['plant'])
            state.update(phase='picked', at=time.monotonic() + 2.0)
        elif p == 'picked':
            if not unreal.SystemLibrary.is_valid(state['plant']) or state['plant'].is_actor_being_destroyed():
                state.update(phase='to_rock', at=time.monotonic() + .2)
                return
            # Some plants take more than one gathering: go again.
            state['tries'] += 1
            check('the plant can be picked clean', state['tries'] < 8)
            state.update(phase='pick', at=time.monotonic() + .5)
        elif p == 'to_rock':
            # A ruby deposit in the starter cave, as verify_crystals_play mines one; the cave's spiders would bite the miner.
            rocks = [r for r in startup(unreal.EWMineable) if str(r.get_actor_label()).startswith('Ruby Node') and 'Starter cave' in str(r.get_actor_label())]
            check('a ruby deposit lies in the starter cave', rocks)
            for animal in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal):
                animal.destroy_actor()
            rock = rocks[0]
            state['rock'] = rock
            expected['rock'] = rock.get_name()
            state['rock_start'] = rock.get_editor_property('remaining')
            pawn.get_inventory_component().add_item(metal, 1)
            check('metal pickaxe equipped', lib.send_verification_equipment_request(pc, metal, unreal.EWEquipmentSlot.MAIN_HAND))
            face(rock)
            state.update(phase='mine', at=time.monotonic() + 2.0)
        elif p == 'mine':
            rock = state['rock']
            if rock.get_editor_property('remaining') == state['rock_start'] and state['strikes'] < 6:
                face(rock)
                lib.send_verification_attack(pc, rock)
                state['strikes'] += 1
                state['at'] = time.monotonic() + 1.8
                return
            left = rock.get_editor_property('remaining')
            check('the deposit is partly mined', 0 < left < state['rock_start'], left=left, start=state['rock_start'])
            expected['rock_left'] = left
            state.update(phase='wait_gone', at=time.monotonic() + 1.0)
        elif p == 'wait_gone':
            gone = [t for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHarvestTree) if t.get_name() == expected['gone_tree']]
            if gone and state['tries'] < 60:
                state['tries'] += 1
                state['at'] = time.monotonic() + .5
                return
            check('the cut tree has gone', not gone)
            lying = next(t for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHarvestTree) if t.get_name() == expected['lying_tree'])
            check('the knocked-over tree lies on the ground', lying.is_felled())
            rot = lying.get_actor_rotation()
            expected['lying_pitch_roll'] = [rot.pitch, rot.roll]
            expected['lying_at'] = [lying.get_actor_location().x, lying.get_actor_location().y, lying.get_actor_location().z]
            mx, my = cave.world(-1400, 0.0)
            pawn.teleport(unreal.Vector(mx, my, cave.floor + 200), unreal.Rotator())
            state.update(phase='bag', at=time.monotonic() + 1.5)
        elif p == 'bag':
            pack = pawn.get_inventory_component()
            for e in list(pack.get_inventory_entries()):
                pack.remove_item(e.item_definition, e.quantity)
            pack.add_item(unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood'), 7)
            pack.add_item(unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHide'), 2)
            at = pawn.get_actor_location()
            bag = unreal.EWDeathBag.drop_inventory_of(pawn, unreal.Vector(at.x + 150, at.y, at.z - 80))
            check('the pack drops into a death bag', bag is not None and pack.get_used_slot_count() == 0)
            expected['bag_at'] = [bag.get_actor_location().x, bag.get_actor_location().y, bag.get_actor_location().z]
            expected['bag'] = sorted([str(e.item_definition.get_name()), e.quantity] for e in bag.get_contents().get_inventory_entries())
            state.update(bag=bag, phase='save', at=time.monotonic() + 1.0)
        elif p == 'save':
            expected['bag_life'] = state['bag'].get_life_span()
            check('the game saves', unreal.EWSurvivorSave.save_survivor(pawn, 'WorldSaveTest'))
            (saved / 'WorldSaveExpected.json').write_text(json.dumps(expected, indent=2))
            report['expected'] = expected
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


def face(n, distance=150.0):
    """Stand in front of a deposit (out along its +x) and look at it."""
    loc, fwd = n.get_actor_location(), n.get_actor_forward_vector()
    for lift in (110, 160, 220):
        spot = unreal.Vector(loc.x + fwd.x * distance, loc.y + fwd.y * distance, cave.floor + lift)
        if pawn.teleport(spot, unreal.Rotator()):
            break
    eye, _ = pawn.get_actor_eyes_view_point()
    aim = unreal.Vector(loc.x + fwd.x * 35, loc.y + fwd.y * 35, loc.z + fwd.z * 35)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, aim))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
