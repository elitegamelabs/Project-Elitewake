"""Hired gunners and the volley (owner, October 18: Port NPCs assigned to any deck's cannons fire only on the player's shot, only when
ready), with a second player (listen server plus one client, EW_PLAY_PLAYERS=2). Needs /Game/Elitewake/Maps/Test/Lvl_ShipsTest (the schooner).
On the schooner, four starboard hull cannons and one port cannon are fitted for the check and round shot is put in the hold. The
client is given Gunner Articles (hiring is checked in verify_sail_crew_multiplayer_play) and signs a gunner on at a starboard cannon (a real interaction request); three more gunners are signed on
directly. Hired gunners load from the hold and open their ports. The client mans the first starboard cannon and fires: the three
starboard gunners that bear fire with it, the port-side gunner holds fire, and they reload from the hold (sponge, powder, shot,
ram); both screens see the cannons recoil. Target lock: a ship is set straight out from the broadside, the client marks it with Right
Mouse (a real key event), lays their own cannon 25 degrees away and fires: the gunners lay on the marked ship and fire at her. Writes
Saved/GunnerVolleyMultiplayerPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 14, 'handle': None, 'tries': 0}
CANNON = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestCannon')
SHOT = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestRoundShot')
POWDER = unreal.load_asset('/Game/Elitewake/Items/Ships/DA_Gunpowder')   # a powder charge with each round shot (November 7)
ARTICLES = unreal.load_asset('/Game/Elitewake/Items/Crew/DA_GunnerArticles')
LOWER = 20.0


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'GunnerVolleyMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK GunnerVolleyMultiplayer success={error is None} error={error}')


def count(inv, item):
    return sum(e.quantity for e in inv.get_inventory_entries() if e.item_definition == item)


def shots(world):
    return len(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWCannonBall))


def behind(mount):
    """Stand behind a cannon on the lower deck and look at it."""
    ship, owner = state['ship'], state['owner']
    m = state['mounts'][mount]
    xf = m.get_editor_property('transform')
    back = xf.transform_location(unreal.Vector(-140, 0, 0))
    world = ship.get_actor_transform()
    owner.teleport(world.transform_location(unreal.Vector(back.x, back.y, LOWER + 98)), unreal.Rotator())
    eye, _ = owner.get_actor_eyes_view_point()
    client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, ship.get_mount_world_transform(mount).translation))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        ship, peer, owner = state.get('ship'), state.get('peer'), state.get('owner')
        if p == 0:
            report['ships'] = [(s.get_name(), str(s.get_editor_property('definition').get_editor_property('ship_id')) if s.get_editor_property('definition') else None) for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)]
            ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
                        if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Schooner')
            peer = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if s.get_name() == ship.get_name())
            owner = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            mounts = {str(m.get_editor_property('mount_id')): m for m in ship.get_editor_property('definition').get_editor_property('mounts')
                      if m.get_editor_property('type') == unreal.EWShipMountType.CANNON and str(m.get_editor_property('parent_mount')) == 'None'}
            star = sorted(n for n in mounts if n.startswith('Starboard'))[:4]
            port = sorted(n for n in mounts if n.startswith('Port'))[:1]
            state.update(ship=ship, peer=peer, owner=owner, mounts=mounts, star=star, port=port)
            # Broadside to open sea: turned in place to head south, her starboard guns look east, clear of the dock and the other ships.
            ship.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=-90), True)
            for n in star + port:
                if not ship.get_fitting(n):
                    ship.verification_install_fitting(n, CANNON)
            check('four starboard and one port cannon fitted', len(star) == 4 and len(port) == 1 and all(ship.get_fitting(n) == CANNON for n in star + port), star=star, port=port)
            ship.get_cargo().add_item(SHOT, 12)
            ship.get_cargo().add_item(POWDER, 12)
            state['hold0'] = count(ship.get_cargo(), SHOT)
            check('round shot in the hold', state['hold0'] >= 12, hold=state['hold0'])
            # Hiring at a Port gunnery master is checked on the coastal map (verify_sail_crew_multiplayer_play); here the articles are given.
            owner.get_inventory_component().add_item(ARTICLES, 1)
            behind(state['star'][1])
            state.update(phase=2, at=time.monotonic() + 2.0)
        elif p == 2:
            report['cannon_prompt'] = str(ship.get_interaction_prompt(owner))
            check('the client asks at the cannon', lib.send_verification_interaction_request(client, peer))
            state.update(phase=3, at=time.monotonic() + 4.0)
        elif p == 3:
            mount = state['star'][1]
            if not ship.is_cannon_crewed(mount) and state['tries'] < 5:
                state['tries'] += 1
                report['retries'] = state['tries']
                behind(mount)
                state.update(phase=2, at=time.monotonic() + 2.0)
                return
            check('the gunner is signed on and the articles used', ship.is_cannon_crewed(mount) and count(owner.get_inventory_component(), ARTICLES) == 0,
                  prompt=ship.get_interaction_prompt(owner))
            check('the client sees the hired gunner', peer.is_cannon_crewed(mount))
            for n in state['star'][2:] + state['port']:
                check(f'a gunner signs on at {n}', ship.sign_on_gunner(n))
            check('the survivor did not man the cannon', ship.get_cannon_gunner(mount) is None)
            state.update(phase=4, at=time.monotonic() + 7.0)
        elif p == 4:
            hired = state['star'][1:] + state['port']
            loaded = [ship.is_cannon_loaded(n) for n in hired]
            check('hired gunners load from the hold', all(loaded) and count(ship.get_cargo(), SHOT) == state['hold0'] - len(hired),
                  loaded=loaded, hold=count(ship.get_cargo(), SHOT))
            check('their ports are open', all(ship.get_gunport_opening(n) > .99 for n in hired))
            first = state['star'][0]
            owner.get_inventory_component().add_item(SHOT, 2)
            owner.get_inventory_component().add_item(POWDER, 2)
            behind(first)
            check('the client mans the first starboard cannon', ship.man_cannon(owner, first))
            ship.set_gunport_open(owner, True)
            ship.aim_cannon(owner, 0.0, 0.0)
            state.update(phase=5, at=time.monotonic() + 7.0)
        elif p == 5:
            first = state['star'][0]
            check('the survivor cannon is loaded and run out', ship.is_cannon_loaded(first) and ship.get_gunport_opening(first) > .99)
            state['shots0'] = shots(server_world)
            check('the client fires', ship.fire_cannon(owner))
            report['volley'] = ship.get_last_volley()
            report['after'] = {n: [ship.is_cannon_loaded(n), str(ship.get_cannon_aim(n)), str(ship.get_cannon_muzzle_world(n).translation), ship.get_gunport_opening(n)] for n in state['star'] + state['port']}
            check('the three starboard gunners fire with it', ship.get_last_volley() == 3 and not any(ship.is_cannon_loaded(n) for n in state['star']),
                  volley=ship.get_last_volley())
            check('the port-side gunner holds fire (it cannot bear)', ship.is_cannon_loaded(state['port'][0]))
            check('four round shot fly', shots(server_world) - state['shots0'] >= 4, shots=shots(server_world) - state['shots0'])
            state.update(phase=6, at=time.monotonic() + .5)
        elif p == 6:
            check('the client sees the shot', shots(client_world) >= 1, client=shots(client_world))
            recoil = [peer.get_cannon_recoil(n) for n in state['star']]
            report['recoil_client'] = recoil
            check('the client sees the cannons thrown back by their shots', all(r > 10 for r in recoil), recoil=recoil)
            steps = [str(ship.get_cannon_load_step(n)) for n in state['star'][1:]]
            check('the gunners start reloading at the first step, sponging out', steps == ['Swab'] * 3, steps=steps)
            check('the client sees the step', str(peer.get_cannon_load_step(state['star'][1])) == 'Swab')
            state.update(phase=65, at=time.monotonic() + 2.0)
        elif p == 65:
            check('the cannons have run out again', all(peer.get_cannon_recoil(n) == 0 for n in state['star']))
            steps = [str(ship.get_cannon_load_step(n)) for n in state['star'][1:]]
            report['steps_later'] = steps
            check('then the powder goes in', all(st in ('Powder', 'Shot') for st in steps), steps=steps)
            state.update(phase=7, at=time.monotonic() + 4.0)
        elif p == 7:
            check('the hired gunners reload from the hold', all(ship.is_cannon_loaded(n) for n in state['star'][1:]), hold=count(ship.get_cargo(), SHOT))
            # A target 35 m straight out from the first starboard cannon.
            first = state['star'][0]
            muzzle = ship.get_cannon_muzzle_world(first)
            out = unreal.MathLibrary.get_forward_vector(muzzle.rotation.rotator())
            spot = unreal.Vector(muzzle.translation.x + out.x * 3500, muzzle.translation.y + out.y * 3500, -65)
            target = lib.spawn_verification_ship(server_world, unreal.load_asset('/Game/Elitewake/Ships/DA_Ship_Sloop'), spot,
                                                 unreal.Rotator(0, 0, ship.get_actor_rotation().yaw))
            check('a target ship lies off the broadside', target is not None)
            state['target'] = target
            owner.get_inventory_component().add_item(SHOT, 2)
            owner.get_inventory_component().add_item(POWDER, 2)
            behind(first)
            state.update(phase=75, at=time.monotonic() + 1.5)
        elif p == 75:
            first = state['star'][0]
            report['man_again_prompt'] = str(ship.get_interaction_prompt(owner))
            check('the client is at the first cannon', ship.get_cannon_gunner(first) == owner or ship.man_cannon(owner, first))
            # Laid on her: the client looks at her side (a gunner's view lays the cannon).
            aim_at = state['target'].get_actor_location()
            muzzle = ship.get_cannon_muzzle_world(first).translation
            client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(muzzle, unreal.Vector(aim_at.x, aim_at.y, aim_at.z + 60)))
            state.update(phase=8, at=time.monotonic() + 6.5)
        elif p == 8:
            check('the client marks the ship with Right Mouse', lib.send_verification_gameplay_key(client, 'RightMouseButton'))
            state.update(phase=9, at=time.monotonic() + 1.0)
        elif p == 9:
            first = state['star'][0]
            m = ship.get_cannon_muzzle_world(first)
            fwd = unreal.MathLibrary.get_forward_vector(m.rotation.rotator())
            end = unreal.Vector(m.translation.x + fwd.x * 20000, m.translation.y + fwd.y * 20000, m.translation.z + fwd.z * 20000)
            hit = unreal.SystemLibrary.line_trace_single_for_objects(server_world, m.translation, end,
                [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2], False, [ship], unreal.DrawDebugTrace.NONE, True)
            t = hit.to_tuple() if hit else None
            report['mark_diag'] = {'aim': str(ship.get_cannon_aim(first)), 'hit': str(t[9].get_name()) if t and t[9] else None,
                                   'target': state['target'].get_name(), 'target_at': str(state['target'].get_actor_location()), 'muzzle': str(m.translation)}
            check('she is the marked target, on both screens', ship.get_marked_ship() == state['target'] and peer.get_marked_ship() is not None)
            report['target_prompt'] = str(ship.get_interaction_prompt(state['owner']))
            # The client's own cannon is laid well away from her: they look 25 degrees aft of her.
            rot = client.get_control_rotation()
            client.set_control_rotation(unreal.Rotator(roll=0, pitch=rot.pitch, yaw=rot.yaw - 25))
            state.update(phase=10, at=time.monotonic() + 1.5)
        elif p == 10:
            first = state['star'][0]
            check('the survivor cannon is loaded again', ship.is_cannon_loaded(first))
            check('the client fires', ship.fire_cannon(state['owner']))
            report['locked_volley'] = ship.get_last_volley()
            aims = {n: ship.get_cannon_aim(n).yaw for n in state['star'][1:]}
            report['locked_aims'] = {k: round(v, 1) for k, v in aims.items()}
            check('the gunners fire at the marked ship, not where the client is laid', ship.get_last_volley() == 3
                  and all(abs(a) < 12 for a in aims.values()), volley=ship.get_last_volley(), aims=aims, own=ship.get_cannon_aim(first).yaw)
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
