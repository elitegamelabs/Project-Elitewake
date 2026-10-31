"""Ship ownership (M7, DECIDED delegated October 30), with a second player (listen server plus one client, EW_PLAY_PLAYERS=2). Needs
/Game/Elitewake/Maps/Test/Lvl_ShipsTest (the schooner).
  - the schooner starts unclaimed; the host takes her helm and she becomes the host's (both screens show the owner's name);
  - the client is not her shipmate: cannot take the helm or work the anchor;
  - host and client form a Company: with its ship policy Personal the client is still kept off; with Personal Shared the client is a
    shipmate on both screens and takes the helm;
  - the client leaves the Company and is kept off again;
  - given to the client she is the client's, and the host is kept off; set free she is anyone's again.
Writes Saved/ShipOwnerMultiplayerPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
report = {'checks': []}
state = {'phase': 'start', 'at': time.monotonic() + 14, 'handle': None}
A = unreal.EWCompanyAction
P = unreal.EWCompanyOwnership


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def name(p):
    return p.get_editor_property('PlayerState').get_player_name()


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'ShipOwnerMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ShipOwnerMultiplayer success={error is None} error={error}')


def wait(phase, seconds=1.5):
    state.update(phase=phase, at=time.monotonic() + seconds)


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        ship, peer = state.get('ship'), state.get('peer')
        captain, mate = state.get('captain'), state.get('mate')
        if p == 'start':
            ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
                        if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Schooner')
            peer = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if s.get_name() == ship.get_name())
            captain = host.get_controlled_pawn()
            mate = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            state.update(ship=ship, peer=peer, captain=captain, mate=mate, remote=mate.get_controller())
            check('the schooner starts unclaimed, open to anyone', not ship.is_owned() and ship.is_shipmate(mate) and ship.is_shipmate(captain))
            if not ship.get_fitting('Helm'):
                ship.verification_install_fitting('Helm', unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestShipHelm'))
            check('the schooner has a helm', ship.get_fitting('Helm') is not None)
            check('the host takes her helm', ship.take_helm(captain))
            check('and she is the host\'s', ship.is_owned() and ship.get_owner_name() == name(host), owner=ship.get_owner_name(), host=name(host))
            check('the host leaves the helm', ship.leave_helm(captain, True))
            wait('locked')
        elif p == 'locked':
            check('the client sees whose ship she is', peer.is_owned() and peer.get_owner_name() == name(host), seen=peer.get_owner_name())
            check('the client is not her shipmate (server and client agree)',
                  not ship.is_shipmate(mate) and not peer.is_shipmate(client.get_controlled_pawn()))
            check('the client cannot take her helm', not ship.take_helm(mate) and ship.get_helmsman() is None)
            anchored = ship.is_anchored()
            check('nor work her anchor', not ship.set_anchored(mate, not anchored) and ship.is_anchored() == anchored)
            check('the host still can', ship.is_shipmate(captain))
            assert lib.send_verification_company_command(host, A.CREATE, 'Saltwind', -1)
            wait('invite', 2.0)
        elif p == 'invite':
            check('the host made a Company', host.get_company_component().get_company().name == 'Saltwind')
            assert lib.send_verification_company_command(host, A.INVITE, '', pid(client))
            wait('accept', 2.0)
        elif p == 'accept':
            assert lib.send_verification_company_command(client, A.ACCEPT_INVITE, '', -1)
            wait('personal', 2.5)
        elif p == 'personal':
            members = len(host.get_company_component().get_company().members)
            check('the client joined it', members == 2, members=members)
            check('with the ship policy Personal she is still only the host\'s',
                  not ship.is_shipmate(mate) and not ship.take_helm(mate))
            assert lib.send_verification_company_policy(host, 0, P.PERSONAL_SHARED)
            wait('shared', 2.5)
        elif p == 'shared':
            check('shared with the Company, the client is her shipmate (both screens)',
                  ship.is_shipmate(mate) and peer.is_shipmate(client.get_controlled_pawn()))
            check('and takes her helm', ship.take_helm(mate) and ship.get_helmsman() == mate)
            check('she stays the host\'s', ship.get_owner_name() == name(host))
            check('the client leaves the helm', ship.leave_helm(mate, True))
            assert lib.send_verification_company_command(client, A.LEAVE, '', -1)
            wait('left', 2.5)
        elif p == 'left':
            check('out of the Company, the client is kept off again', not ship.is_shipmate(mate) and not ship.take_helm(mate))
            ship.set_ship_owner(state['remote'])
            wait('given')
        elif p == 'given':
            check('given to the client she is theirs', ship.get_owner_name() == name(client) and peer.get_owner_name() == name(client),
                  owner=ship.get_owner_name())
            check('and the host is kept off', not ship.is_shipmate(captain) and ship.is_shipmate(mate))
            ship.set_ship_owner(None)
            wait('free')
        elif p == 'free':
            check('set free she is anyone\'s again', not ship.is_owned() and not peer.is_owned() and ship.is_shipmate(captain)
                  and ship.is_shipmate(mate))
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
