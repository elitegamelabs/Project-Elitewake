"""Sail control and crew dependency (owner, October 18), with a second player (listen server plus one client, EW_PLAY_PLAYERS=2).
On the sloop (helm, mainsail and headsail fitted for the check): the client hires a sailhand from a Port crew master (100 Copper,
Sailhand Articles); with no sailhand aboard the helm cannot set sail; at the mainsail lines the client signs the hand on (a real
interaction request); the helm then sets only the crewed mainsail; at the headsail lines the client works that sail by hand to full;
walking away lets go of the lines; the client sees every sail setting. Writes Saved/SailCrewMultiplayerPlayResult.json."""
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
TESTING = '/Game/Elitewake/Items/Testing'
ARTICLES = unreal.load_asset('/Game/Elitewake/Items/Crew/DA_SailhandArticles')
FURLED, HALF, FULL = unreal.EWSailState.FURLED, unreal.EWSailState.HALF, unreal.EWSailState.FULL


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'SailCrewMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SailCrewMultiplayer success={error is None} error={error}')


def articles(owner):
    return sum(e.quantity for e in owner.get_inventory_component().get_inventory_entries() if e.item_definition == ARTICLES)


def at_lines(mount, back=110):
    """Stand on deck aft of a sail's lines and look at the pin rail."""
    ship, owner = state['ship'], state['owner']
    lines = ship.get_lines_local(mount)
    xf = ship.get_actor_transform()
    owner.teleport(xf.transform_location(unreal.Vector(lines.x - back, lines.y, lines.z + 100)), unreal.Rotator())
    eye, _ = owner.get_actor_eyes_view_point()
    client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, xf.transform_location(unreal.Vector(lines.x, lines.y, lines.z + 85))))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        ship, peer, owner = state.get('ship'), state.get('peer'), state.get('owner')
        if p == 0:
            ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
                        if s.get_editor_property('definition') and 'Sloop' in s.get_editor_property('definition').get_name())
            peer = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if s.get_name() == ship.get_name())
            owner = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            state.update(ship=ship, peer=peer, owner=owner)
            for mount, item in (('Helm', 'DA_TestShipHelm'), ('Mainsail', 'DA_TestSailMedium'), ('Headsail', 'DA_TestSailSmall')):
                if not ship.get_fitting(mount):
                    ship.verification_install_fitting(mount, unreal.load_asset(f'{TESTING}/{item}'))
            check('the sloop has her helm and both sails', all(ship.get_fitting(m) for m in ('Helm', 'Mainsail', 'Headsail')))
            check('no sailhand aboard yet', ship.get_crewed_sail_count() == 0)
            # The regional Ports' crew masters (Saltreach Freeport's named recruiter is checked in verify_freeport_multiplayer_play).
            masters = [m for m in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCrewMaster)
                       if m.get_editor_property('crew_role') == 'sailhand' and not str(m.get_editor_property('npc_name'))]
            check('a crew master waits at each of the four regional Ports', len(masters) == 4, found=len(masters))
            master = masters[0]
            owner.teleport(master.get_actor_location() + master.get_actor_forward_vector() * 150 + unreal.Vector(0, 0, 100), unreal.Rotator())
            owner.get_wallet_component().set_copper(250)
            state.update(phase=1, at=time.monotonic() + 1.5, master=master)
        elif p == 1:
            report['hire_prompt'] = str(state['master'].get_interaction_prompt(owner))
            check('the crew master hires a sailhand', state['master'].interact(owner))
            check('the fee is 100 Copper', owner.get_wallet_component().get_copper() == 150, copper=owner.get_wallet_component().get_copper())
            check('the Sailhand Articles are in the pack', articles(owner) == 1)
            gunnery = [m for m in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCrewMaster) if m.get_editor_property('crew_role') == 'gunner']
            check('a gunnery master waits at each of the four regional Ports', len(gunnery) == 4, found=len(gunnery))
            owner.teleport(gunnery[0].get_actor_location() + gunnery[0].get_actor_forward_vector() * 150 + unreal.Vector(0, 0, 100), unreal.Rotator())
            report['gunner_prompt'] = str(gunnery[0].get_interaction_prompt(owner))
            gunner_articles = unreal.load_asset('/Game/Elitewake/Items/Crew/DA_GunnerArticles')
            owner.get_wallet_component().set_copper(150)
            check('the gunnery master hires a gunner for 150 Copper', gunnery[0].interact(owner) and owner.get_wallet_component().get_copper() == 0
                  and sum(e.quantity for e in owner.get_inventory_component().get_inventory_entries() if e.item_definition == gunner_articles) == 1)
            owner.teleport(state['master'].get_actor_location() + state['master'].get_actor_forward_vector() * 150 + unreal.Vector(0, 0, 100), unreal.Rotator())
            owner.get_wallet_component().set_copper(50)
            check('too little Copper hires nobody', not state['master'].interact(owner) and articles(owner) == 1 and owner.get_wallet_component().get_copper() == 50)
            at_lines('Helm', 0)
            state.update(phase=2, at=time.monotonic() + 1.5)
        elif p == 2:
            check('the client takes the helm', ship.take_helm(owner), why=ship.get_interaction_prompt(owner))
            check('with no sailhand the helm cannot set sail', not ship.step_sails(owner, 1) and ship.get_mount_sail_state('Mainsail') == FURLED)
            check('the client leaves the helm', ship.leave_helm(owner, True))
            at_lines('Mainsail')
            state.update(phase=3, at=time.monotonic() + 2.0)
        elif p == 3:
            report['lines_prompt'] = str(ship.get_interaction_prompt(owner))
            check('the client signs on the sailhand at the mainsail lines', lib.send_verification_interaction_request(client, peer))
            state.update(phase=4, at=time.monotonic() + 1.5)
        elif p == 4:
            if not ship.is_sail_crewed('Mainsail') and state['tries'] < 5:
                state['tries'] += 1
                report['retries'] = state['tries']
                at_lines('Mainsail')
                state.update(phase=3, at=time.monotonic() + 2.0)
                return
            check('the mainsail has a sailhand and the articles are used', ship.is_sail_crewed('Mainsail') and articles(owner) == 0 and not ship.is_sail_crewed('Headsail'))
            check('the client sees the sailhand', peer.is_sail_crewed('Mainsail'))
            at_lines('Helm', 0)
            state.update(phase=5, at=time.monotonic() + 1.0)
        elif p == 5:
            check('the client takes the helm again', ship.take_helm(owner))
            check('the helm sets half sail', ship.step_sails(owner, 1) and ship.step_sails(owner, 1))
            check('the crewed mainsail follows the helm, the headsail does not', ship.get_mount_sail_state('Mainsail') == HALF and ship.get_mount_sail_state('Headsail') == FURLED,
                  main=ship.get_mount_sail_state('Mainsail'), head=ship.get_mount_sail_state('Headsail'))
            check('the sail set is the mainsail share only', abs(ship.get_sail_fraction() - (2 * .5) / 3) < .01, fraction=ship.get_sail_fraction())
            ship.leave_helm(owner, True)
            state['tries'] = 0
            at_lines('Headsail')
            state.update(phase=6, at=time.monotonic() + 2.0)
        elif p == 6:
            check('the client takes the headsail lines', lib.send_verification_interaction_request(client, peer))
            state.update(phase=7, at=time.monotonic() + 1.5)
        elif p == 7:
            if owner.get_lines_ship() != ship and state['tries'] < 5:
                state['tries'] += 1
                report['line_retries'] = state['tries']
                at_lines('Headsail')
                state.update(phase=6, at=time.monotonic() + 2.0)
                return
            check('the survivor works the headsail lines', owner.get_lines_ship() == ship and ship.get_lines_worker('Headsail') == owner)
            check('the client knows it is at the lines', client.get_controlled_pawn().get_lines_ship() == peer)
            steps = [ship.step_sail_by_hand(owner, 1) for _ in range(5)]
            check('by hand the headsail goes up a step at a time to full', steps == [True, True, True, True, False] and ship.get_mount_sail_state('Headsail') == FULL, steps=steps)
            check('the mainsail keeps the helm setting', ship.get_mount_sail_state('Mainsail') == HALF)
            state.update(phase=8, at=time.monotonic() + 1.5)
        elif p == 8:
            check('the client sees both sail settings', peer.get_mount_sail_state('Headsail') == FULL and peer.get_mount_sail_state('Mainsail') == HALF)
            owner.teleport(owner.get_actor_location() + ship.get_actor_forward_vector() * -700, unreal.Rotator())
            state.update(phase=9, at=time.monotonic() + 1.5)
        elif p == 9:
            check('walking away lets go of the lines', owner.get_lines_ship() is None and ship.get_lines_worker('Headsail') is None,
                  gap=(owner.get_actor_location() - ship.get_actor_location()).length())
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
