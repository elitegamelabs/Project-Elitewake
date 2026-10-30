"""Play: ships are saved (M7 persistence, October 30). One player, the coastal map. Twice, once through the single-player Save Game
(UEWSurvivorSave) and once through the server's world save (UEWBuildSave):
  - a raft is launched in play off the Freeport's slipway, fitted out, given cargo and holed by a round shot; the map's own sloop is
    towed to a new spot off the long pier, given cargo and a crewed mainsail set to half
  - the game is saved;
  - everything changes: the raft is broken up, the sloop towed elsewhere, her hold emptied and her crew gone;
  - the save is loaded: a raft lies where she was with her fittings, cargo and hole, and the sloop is back where she was with her hold
    and her crewed half-set mainsail.
The test slots are deleted afterwards. Writes Saved/ShipSavePlayResult.json."""
import json
import time
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
port = W.PORTS['Plains']
report = {'checks': [], 'rounds': []}
state = {'phase': 'setup', 'at': time.monotonic() + 12, 'handle': None, 'round': 0}
ITEMS = '/Game/Elitewake/Items'
WOOD = unreal.load_asset(f'{ITEMS}/Testing/DA_TestWood')
SHOT = unreal.load_asset(f'{ITEMS}/Testing/DA_TestRoundShot')
ROUNDS = ['survivor', 'server']
SLOTS = {'survivor': 'ShipSaveTest', 'server': 'ShipSaveTestServer'}


def check(label, ok, **values):
    report['checks'].append({'label': f'[{ROUNDS[state["round"]]}] {label}', 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    for slot in SLOTS.values():
        if unreal.GameplayStatics.does_save_game_exist(slot, 0):
            unreal.GameplayStatics.delete_game_in_slot(slot, 0)
    report.update(success=error is None, error=error)
    (saved / 'ShipSavePlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ShipSave success={error is None} error={error}')


def ships():
    return [s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip) if not s.is_sinking()]


def sid(s):
    return str(s.get_editor_property('definition').get_editor_property('ship_id'))


def count(ship, item):
    return sum(e.quantity for e in ship.get_cargo().get_inventory_entries() if e.item_definition == item)


def spot(a, c, yaw):
    x, y = port.world(a, c)
    return unreal.Transform(unreal.Vector(x, y, T.SEA), unreal.Rotator(0, 0, unreal.MathLibrary.radians_to_degrees(port.facing) + yaw), unreal.Vector(1, 1, 1))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 'setup':
            sloop = next(s for s in ships() if sid(s) == 'Sloop')
            state['sloop_name'] = sloop.get_name()
            for mount, item in (('Helm', 'DA_TestShipHelm'), ('Mainsail', 'DA_TestSailMedium')):
                if not sloop.get_fitting(mount):
                    sloop.verification_install_fitting(mount, unreal.load_asset(f'{ITEMS}/Testing/{item}'))
            check('the sloop tows to a spot off the long pier', sloop.tow_to(spot(6000, 4200, 15)))
            sloop.get_cargo().add_item(WOOD, 7)
            check('a sailhand signs on at her mainsail', sloop.sign_on_sailhand('Mainsail'))
            raft_def = unreal.load_asset('/Game/Elitewake/Ships/DA_Ship_Raft')
            x, y = port.world(7500, -1500)
            raft = lib.spawn_verification_ship(world, raft_def, unreal.Vector(x, y, T.SEA), unreal.Rotator(0, 0, unreal.MathLibrary.radians_to_degrees(port.facing)))
            raft.verification_install_fitting('Helm', unreal.load_asset(f'{ITEMS}/Ships/DA_RaftPaddles'))
            raft.get_cargo().add_item(SHOT, 3)
            loc = raft.get_actor_location()
            raft.take_round_shot(unreal.Vector(loc.x, loc.y, loc.z + 30), unreal.Vector(0, 0, 1), None)
            state.update(raft=raft, sloop=sloop, phase='sail', at=time.monotonic() + 1.0)
        elif p == 'sail':
            sloop = state['sloop']
            # The helm sets the crewed mainsail to half.
            x = sloop.get_actor_location()
            pawn.teleport(unreal.Vector(x.x, x.y, x.z + 400), unreal.Rotator())
            state.update(phase='helm', at=time.monotonic() + 1.0)
        elif p == 'helm':
            sloop, raft = state['sloop'], state['raft']
            check('the survivor takes the helm', sloop.take_helm(pawn))
            check('the helm sets the crewed mainsail to half', sloop.step_sails(pawn, 1) and sloop.step_sails(pawn, 1))
            sloop.leave_helm(pawn, True)
            check('the mainsail is set half', sloop.get_mount_sail_state('Mainsail') == unreal.EWSailState.HALF)
            state['want'] = {
                'sloop_at': sloop.get_actor_location(), 'sloop_yaw': sloop.get_actor_rotation().yaw,
                'raft_at': raft.get_actor_location(), 'raft_health': raft.get_hull_health(), 'ships': len(ships())}
            # Stand ashore on the Freeport's high street to save.
            sx, sy = port.world(0, -200)
            pawn.teleport(unreal.Vector(sx, sy, T.PORT_LEVEL + 120), unreal.Rotator())
            state.update(phase='save', at=time.monotonic() + 1.5)
        elif p == 'save':
            slot = SLOTS[ROUNDS[state['round']]]
            # Under half sail at anchor she drifts on her chain: what is expected back is where she is as the save is made.
            sloop, raft = state['sloop'], state['raft']
            state['want'].update(sloop_at=sloop.get_actor_location(), sloop_yaw=sloop.get_actor_rotation().yaw,
                                 raft_at=raft.get_actor_location(), raft_health=raft.get_hull_health(), ships=len(ships()))
            ok = unreal.EWSurvivorSave.save_survivor(pawn, slot) if ROUNDS[state['round']] == 'survivor' else unreal.EWBuildSave.save_world(world, slot)
            check('the game saves', ok)
            sloop, raft = state['sloop'], state['raft']
            # Everything changes.
            raft.destroy_actor()
            sloop.tow_to(spot(2500, 7000, -40))
            sloop.get_cargo().remove_item(WOOD, 7)
            state.update(phase='load', at=time.monotonic() + 1.5)
        elif p == 'load':
            check('the raft is gone and the sloop moved before loading', len(ships()) == state['want']['ships'] - 1)
            slot = SLOTS[ROUNDS[state['round']]]
            if ROUNDS[state['round']] == 'survivor':
                check('the save loads', unreal.EWSurvivorSave.load_save(slot).apply_to(pawn))
            else:
                unreal.EWBuildSave.restore_world(world, slot)
            state['loaded_sloop_at'] = next(s for s in ships() if s.get_name() == state['sloop_name']).get_actor_location()
            state.update(phase='verify', at=time.monotonic() + 1.0)
        elif p == 'verify':
            want = state['want']
            sloop = next(s for s in ships() if s.get_name() == state['sloop_name'])
            raft = next((s for s in ships() if sid(s) == 'Raft'), None)
            check('as many ships as were saved', len(ships()) == want['ships'], found=len(ships()))
            # Checked as soon as the load is done (she may drift on afterwards under her half-set sail).
            check('the sloop is back where she was saved', (state['loaded_sloop_at'] - want['sloop_at']).length() < 30
                  and abs(((sloop.get_actor_rotation().yaw - want['sloop_yaw']) + 180) % 360 - 180) < 1, at=sloop.get_actor_location())
            check('her hold is back', count(sloop, WOOD) == 7)
            check('her mainsail is crewed and set half again', sloop.is_sail_crewed('Mainsail') and sloop.get_mount_sail_state('Mainsail') == unreal.EWSailState.HALF)
            check('a raft lies where she was', raft is not None and (raft.get_actor_location() - want['raft_at']).length() < 30)
            check('with her paddles, her round shot and her hole', raft.get_fitting('Helm') is not None and count(raft, SHOT) == 3
                  and raft.get_hole_count() == 1 and abs(raft.get_hull_health() - want['raft_health']) < .1, holes=raft.get_hole_count())
            check('she is at anchor', raft.is_anchored())
            report['rounds'].append(ROUNDS[state['round']])
            state['round'] += 1
            if state['round'] == len(ROUNDS):
                finish()
                return
            state.update(raft=raft, sloop=sloop, phase='helm_again', at=time.monotonic() + .5)
        elif p == 'helm_again':
            # The second round starts from the loaded state: set the same scene again and save it the other way.
            state.update(phase='save', at=time.monotonic() + .5)
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
