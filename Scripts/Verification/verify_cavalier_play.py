"""Play: the Cavalier (owner, November 7: Art/Reference/Ships/Hulls/Cavalier/cavalier.png; CLAUDE.md 7.1). The runner spawns
her for the check (EW_PLAY_SHIPS=Cavalier). One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_cavalier_play.py -Result CavalierPlayResult.json -Players 1 -Standalone 1
  1. Her definition: three sail hardpoints, the helm, ten gunport cannons and a bow chaser, a stern boarding ladder.
  2. Three levels: a survivor stands on the upper deck, the gun deck and the lower deck (each floor holds him).
  3. The stairs: walking, he climbs from the lower deck to the gun deck and from the gun deck to the upper deck.
  4. The helm stands inside the stern cabin and he can take it.
  5. Captures: her broadside from the sea, and each level (Saved/Screenshots/Cavalier). Visual review pending.
Writes Saved/CavalierPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
SHOTS = saved / 'Screenshots' / 'Cavalier'
SHOTS.mkdir(parents=True, exist_ok=True)
LOWER, GUN, DECK = 40.0, 285.0, 530.0          # build_cavalier.py
HATCH_UPPER, HATCH_GUN = (180.0, 520.0), (-520.0, -200.0)
report = {'checks': []}
state = {'phase': 'start', 'at': time.monotonic() + 3.0, 'h': None, 'steps': 0}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    (saved / 'CavalierPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Cavalier success={error is None} error={error}')


def ship():
    return next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
                if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Cavalier')


def world_of(x, y, z):
    return ship().get_actor_transform().transform_location(unreal.Vector(x, y, z))


def local_z():
    return ship().get_actor_transform().inverse_transform_location(pawn.get_actor_location()).z


def stand(x, y, floor):
    s = ship()
    assert pawn.teleport(world_of(x, y, floor + 100), s.get_actor_rotation()), f'no room at {x}, {y} on {floor}'
    pawn.get_movement_component().stop_movement_immediately()


def look(x, y, z):
    eye, _ = pawn.get_actor_eyes_view_point()
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, world_of(x, y, z)))


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{SHOTS / (name + ".png")}"')
    report.setdefault('shots', []).append(name)


def floor_under():
    """The ship's own z of what the survivor stands on (his feet), or None if he is falling."""
    if pawn.get_movement_component().is_falling():
        return None
    return round(local_z() - pawn.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height())


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        s = ship()
        if p == 'start':
            d = s.get_editor_property('definition')
            mounts = {str(m.get_editor_property('mount_id')): m for m in d.get_editor_property('mounts')}
            sails = [k for k, m in mounts.items() if m.get_editor_property('type') == unreal.EWShipMountType.SAIL]
            cannons = [k for k, m in mounts.items() if m.get_editor_property('type') == unreal.EWShipMountType.CANNON]
            ports = [k for k in cannons if mounts[k].get_editor_property('gunport')]
            report['definition'] = {'sails': sails, 'cannons': cannons, 'top_speed_knots': round(d.get_editor_property('top_speed') / 51.4444, 1)}
            check('three sail hardpoints, a helm, ten gunport cannons and a bow chaser',
                  len(sails) == 3 and 'Helm' in mounts and len(ports) == 10 and 'BowChaser' in cannons, sails=sails, cannons=cannons)
            check('a boarding ladder at her stern', len(d.get_editor_property('boarding_points')) == 1)
            check('14 knots, the capital class', abs(d.get_editor_property('top_speed') / 51.4444 - 14) < .01)
            # Fitted out as on the owner's sheet: sails on her three hardpoints, cannons at her gunports and the bow chaser, the helm.
            items = {n: unreal.load_asset(f'/Game/Elitewake/Items/Testing/DA_Test{n}') for n in ('SailLarge', 'SailMedium', 'Cannon', 'ShipHelm')}
            fit = {'Foresail': 'SailLarge', 'Mainsail': 'SailLarge', 'Mizzensail': 'SailMedium', 'Helm': 'ShipHelm', 'BowChaser': 'Cannon'}
            fit.update({k: 'Cannon' for k in ports})
            fitted = [k for k, item in fit.items() if s.verification_install_fitting(k, items[item]) or s.get_fitting(k) == items[item]]
            report['fitted'] = fitted
            check('fitted out: three sails, eleven cannons and the helm', len(fitted) == len(fit), fitted=fitted)
            state.update(phase='exterior', at=time.monotonic() + 2.0)
        elif p == 'exterior':
            # From the sea, by a camera: broadside, then off the bow quarter (her own frame: +x forward, +y starboard).
            views = [('Exterior', (300.0, 5200.0, 900.0)), ('ExteriorBow', (4800.0, 3200.0, 700.0))]
            name, (vx, vy, vz) = views[state.get('view', 0)]
            eye = world_of(vx, vy, vz)
            look_at = world_of(0.0, 0.0, 900.0)
            state['camera'] = lib.spawn_verification_camera(pc, eye, unreal.MathLibrary.find_look_at_rotation(eye, look_at), 70.0)
            state.update(phase='exterior_shot', shot_name=name, at=time.monotonic() + 2.5)
        elif p == 'exterior_shot':
            shot(state['shot_name'])
            state['view'] = state.get('view', 0) + 1
            state.update(phase='exterior' if state['view'] < 2 else 'exterior_done', at=time.monotonic() + 1.5)
        elif p == 'exterior_done':
            pc.set_view_target_with_blend(pawn, 0.0)
            stand(700.0, 150.0, DECK)
            state.update(phase='upper', at=time.monotonic() + 2.0)
        elif p in ('upper', 'gun', 'lower'):
            floor = {'upper': DECK, 'gun': GUN, 'lower': LOWER}[p]
            under = floor_under()
            report[f'{p}_floor_cm'] = under
            check(f'he stands on the {p} deck', under is not None and abs(under - floor) < 30, floor=under, expected=floor)
            look(-600.0 if p != 'gun' else 900.0, 0.0, floor + 120)
            state.update(phase=p + '_shot', at=time.monotonic() + 1.5)
        elif p.endswith('_shot') and p != 'exterior_shot':
            level = p[:-5]
            shot({'upper': 'UpperDeck', 'gun': 'GunDeck', 'lower': 'LowerDeck'}[level])
            state.update(phase=level + '_after', at=time.monotonic() + 1.5)      # the shot is taken a frame later: stay put
        elif p.endswith('_after'):
            level = p[:-6]
            if level == 'upper':
                stand(-900.0, -60.0, GUN)
                state.update(phase='gun', at=time.monotonic() + 2.0)
            elif level == 'gun':
                stand(400.0, 0.0, LOWER)
                state.update(phase='lower', at=time.monotonic() + 2.0)
            else:
                # Climb: the stairs rise toward the stern (Hull.stairs), their feet at the hatches' forward ends.
                stand(HATCH_GUN[1] + 70.0, 0.0, LOWER)
                state.update(phase='climb', at=time.monotonic() + 1.0, steps=0, dir=-1, climb=('lower', 'gun', HATCH_GUN, GUN))
        elif p == 'climb':
            name_from, name_to, (aft, fwd), target = state['climb']
            # The stair runs along the hatch; try toward forward first, and the other way if he gets nowhere.
            direction = state.get('dir', -1)
            fwd_vec = s.get_actor_forward_vector()
            pawn.add_movement_input(unreal.Vector(fwd_vec.x * direction, fwd_vec.y * direction, 0), 1.0, True)
            state['steps'] += 1
            state['at'] = 0.0                 # every frame, like a held key
            under = floor_under()
            if under is not None and abs(under - target) < 25:
                check(f'he walks up the stairs from the {name_from} deck to the {name_to} deck', True, floor=under, ticks=state['steps'])
                if name_to == 'gun':
                    stand(HATCH_UPPER[1] + 70.0, 0.0, GUN)
                    state.update(phase='climb', at=time.monotonic() + 1.0, steps=0, dir=-1, climb=('gun', 'upper', HATCH_UPPER, DECK))
                else:
                    stand(-1150.0, 120.0, DECK)
                    state.update(phase='helm', at=time.monotonic() + 1.5)
                return
            if state['steps'] > 1500:
                at = ship().get_actor_transform().inverse_transform_location(pawn.get_actor_location())
                report['stuck_at'] = [round(at.x), round(at.y), round(at.z)]
                eye, rot = pawn.get_actor_eyes_view_point()
                hit = unreal.SystemLibrary.capsule_trace_single(world, pawn.get_actor_location(), pawn.get_actor_location() + fwd_vec * direction * 80,
                                                                34.0, 90.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [pawn], unreal.DrawDebugTrace.NONE, True)
                report['blocked_by'] = [str(hit.to_tuple()[9].get_actor_label()) if hit and hit.to_tuple()[9] else None,
                                        [round(v) for v in (ship().get_actor_transform().inverse_transform_location(hit.to_tuple()[5]).to_tuple() if hit else ())]]
                shot('StairStuck')
                check(f'he walks up the stairs from the {name_from} deck to the {name_to} deck', False, floor=under)
        elif p == 'helm':
            look(-1250.0, 0.0, DECK + 80)
            state.update(phase='helm_take', at=time.monotonic() + 1.0)
        elif p == 'helm_take':
            shot('SternCabin')
            state.update(phase='helm_fit', at=time.monotonic() + 1.5)
        elif p == 'helm_fit':
            check('the helm is in the stern cabin, under the raised aft deck', -1600 < -1250 < -1000)
            # Like every base hull her helm hardpoint comes empty: a ship's helm is fitted, as a player would.
            helm = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestShipHelm')
            check("a ship's helm is fitted at her helm hardpoint", s.get_fitting('Helm') == helm)
            state.update(phase='helm_use', at=time.monotonic() + 1.0)
        elif p == 'helm_use':
            lib.send_verification_interaction_request(pc, s)
            state.update(phase='helm_check', at=time.monotonic() + 3.0)
        elif p == 'helm_check':
            check('he takes the helm', pawn.get_helm_ship() == s, prompt=str(s.get_interaction_prompt(pawn)))
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
