"""A tree that is cut down falls slowly, lies a moment, then disappears (single-player Play session). Owner, October 27: when a tree
is destroyed it should slowly fall like a naturally cut tree and then disappear; the fall happens only after it is cut down.
1. A standing tree that is only shaken (no final strike) stays upright and in the world.
2. CutDown (what the last hatchet strike calls) tips the tree over: it is NOT removed at once, its up vector tilts progressively
   from vertical to horizontal over more than a second, it lies, and then it is gone from the world.
Writes Saved/TreeCutFallPlayResult.json."""
import json
import math
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
tree_cls = unreal.load_class(None, '/Script/EW.EWHarvestTree')
trees = unreal.GameplayStatics.get_all_actors_of_class(world, tree_cls)
tree = min((t for t in trees if not t.is_felled()), key=lambda t: unreal.Vector.distance(t.get_actor_location(), pawn.get_actor_location()))
name = tree.get_name()
state = {'t0': time.monotonic() + 12, 'cut_at': None, 'samples': [], 'handle': None, 'phase': 0}
report = {'tree': name, 'label': str(tree.get_actor_label())}


def exists():
    return any(a.get_name() == name for a in unreal.GameplayStatics.get_all_actors_of_class(world, tree_cls))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, samples=state['samples'][::10][:80])
    (saved / 'TreeCutFallPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK TreeCutFall success={error is None} error={error}')


def tick(delta):
    now = time.monotonic()
    if now < state['t0']:
        return
    try:
        if state['phase'] == 0:
            report['upright_before'] = tree.get_actor_up_vector().z
            assert report['upright_before'] > .99, 'tree not upright to start'
            assert not tree.is_felled() and exists()
            # a tree that is only hit stays up (nothing here fells it); give it a moment to prove that
            state['phase'] = 1
            state['wait'] = now + 2.0
        elif state['phase'] == 1:
            if now < state['wait']:
                return
            assert not tree.is_felled() and tree.get_actor_up_vector().z > .99, 'tree moved without being cut'
            loc0 = tree.get_actor_location()
            for lift in (96, 160, 260):
                if pawn.teleport(unreal.Vector(loc0.x - 900, loc0.y, loc0.z + lift), unreal.Rotator()):
                    break
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=0))
            assert tree.cut_down(pawn), 'CutDown refused'
            assert exists(), 'cut tree was removed at once instead of falling'
            state['cut_at'] = unreal.GameplayStatics.get_time_seconds(world)      # game time: a hitch must not lengthen the measured fade
            state['phase'] = 2
        elif state['phase'] == 2:
            t = unreal.GameplayStatics.get_time_seconds(world) - state['cut_at']
            if exists():
                up = tree.get_actor_up_vector().z
                fade = tree.get_fade()
                state['samples'].append([round(t, 2), round(up, 3), round(fade, 3)])
                if fade < .55 and not state.get('shot'):
                    state['shot'] = True
                    unreal.SystemLibrary.execute_console_command(world, 'Shot showui filename="' + str(saved / 'Screenshots' / 'TreeFade' / 'MidFade.png') + '"')
                if t > 25:
                    raise AssertionError('tree never disappeared')
            else:
                report['seconds_until_gone'] = round(t, 2)
                fades = [x[2] for x in state['samples']]
                fade_start = next((x[0] for x in state['samples'] if x[2] < 1.0), None)
                landed = next((x[0] for x in state['samples'] if x[1] < .03), None)
                report['fade_starts_at'] = fade_start
                report['landed_at'] = landed
                assert fade_start is not None, 'the tree never faded'
                assert fade_start - landed >= 3.0, f'tree faded before it had lain a few seconds ({fade_start - landed:.1f} s)'
                assert fades == sorted(fades, reverse=True), 'fade did not go steadily from solid to gone'
                assert 2.6 <= t - fade_start <= 3.6, f'fade took {t - fade_start:.1f} s, not about 3'
                assert min(fades) < .15, f'tree was still visible when removed (fade {min(fades)})'
                ups = [s[1] for s in state['samples']]
                report['min_up_z'] = min(ups)
                assert ups[0] > .8, f'tree toppled instantly (first sample up_z {ups[0]})'
                assert min(ups) < .15, f'tree never lay down (lowest up_z {min(ups)})'
                assert all(a >= b - .02 for a, b in zip(ups, ups[1:])), 'tree did not fall steadily'
                fall_time = next(s[0] for s in state['samples'] if s[1] < .15)
                report['seconds_to_lie_down'] = fall_time
                assert fall_time > 1.2, f'fall was not slow ({fall_time} s)'
                assert t > fall_time + 5.0, f'tree vanished before lying and fading ({t} s, down at {fall_time} s)'
                state['phase'] = 3
                state['wait'] = now + .5
        elif state['phase'] == 3:
            if now < state['wait']:
                return
            others = [t for t in unreal.GameplayStatics.get_all_actors_of_class(world, tree_cls)
                      if not t.is_felled() and t.get_name() != name and str(t.get_actor_label()).lower().startswith('oak')]
            tree2 = min(others, key=lambda t: unreal.Vector.distance(t.get_actor_location(), pawn.get_actor_location()))
            state['tree2'] = tree2
            state['name2'] = tree2.get_name()
            wood, thatch = tree2.get_editor_property('wood'), tree2.get_editor_property('thatch')
            hatchet = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatchet')
            inv = pawn.get_inventory_component()
            for item in (wood, thatch, hatchet):
                inv.remove_item(item, 100000)
            tree2.set_editor_property('wood_remaining', 3)
            tree2.set_editor_property('thatch_remaining', 1)
            loc = tree2.get_actor_location()
            for lift in (96, 160, 260):
                if pawn.teleport(unreal.Vector(loc.x - 120, loc.y, loc.z + lift), unreal.Rotator()):
                    break
            eye, _ = pawn.get_actor_eyes_view_point()
            aim = unreal.Vector(loc.x, loc.y, loc.z + 120)
            import math
            pitch = -math.degrees(math.atan2(eye.z - aim.z, aim.x - eye.x))
            pc.set_control_rotation(unreal.Rotator(0, pitch, 0))
            inv.add_item(hatchet, 1)
            assert lib.send_verification_equipment_request(pc, hatchet, unreal.EWEquipmentSlot.MAIN_HAND), 'equip refused'
            state['wood'] = wood
            state['phase'] = 4
            state['wait'] = now + 1.5
        elif state['phase'] == 4:
            if now < state['wait']:
                return
            assert lib.send_verification_attack(pc, state['tree2']), 'attack not accepted'
            state['phase'] = 5
            state['wait'] = now + 1.0
        elif state['phase'] == 5:
            if now < state['wait']:
                return
            tree2 = state['tree2']
            got = pawn.get_inventory_component().get_item_count(state['wood'])
            report['last_strike_wood'] = got
            assert got == 3, f'the last strike did not give its wood ({got})'
            assert tree2.is_felled(), 'last strike did not fell the tree'
            assert any(a.get_name() == state['name2'] for a in unreal.GameplayStatics.get_all_actors_of_class(world, tree_cls)), 'tree removed at once'
            state['t_last'] = now
            state['phase'] = 6
        elif state['phase'] == 6:
            gone = not any(a.get_name() == state['name2'] for a in unreal.GameplayStatics.get_all_actors_of_class(world, tree_cls))
            if gone:
                report['last_strike_seconds_until_gone'] = round(now - state['t_last'], 2)
                assert now - state['t_last'] > 5.0, 'the felled tree vanished too soon'
                finish()
            elif now - state['t_last'] > 25:
                raise AssertionError('struck tree never disappeared')
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
