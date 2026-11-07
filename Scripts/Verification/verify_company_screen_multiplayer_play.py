"""The live Company screen and ship sharing (October 30), with a second player (listen server plus one client, EW_PLAY_PLAYERS=2).
Needs /Game/Elitewake/Maps/Test/Lvl_ShipsTest (the schooner).
  - the host claims the schooner (takes her helm); the client is not her shipmate;
  - the host opens the menu's Company section and creates a Company there, then invites the client from the screen's list;
  - the client opens their Company section, sees the invitation and accepts it with Enter on the Invitations page (a real key);
  - both screens list two members (the host Leader, the client Member);
  - the host's screen changes the ship policy to Personal Shared: the client becomes the schooner's shipmate and takes her helm;
  - the client leaves through the screen (Leave, then Right and Enter on the confirmation: real keys) and is kept off her again.
Saves Saved/Screenshots/Menus/company_live_host.png and company_live_client.png. Writes Saved/CompanyScreenMultiplayerPlayResult.json."""
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
shots = saved / 'Screenshots' / 'Menus'
shots.mkdir(parents=True, exist_ok=True)


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def name(p):
    return p.get_editor_property('PlayerState').get_player_name()


def menu(pc, world):
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWInventoryWidget, False)
                if w.get_owning_player() == pc and w.is_in_viewport())


def screen(pc, world):
    return menu(pc, world).get_company_panel()


def key(pc, k):
    assert lib.send_verification_ui_key(pc, k), k


def shot(world, file):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{shots / file}"')


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    for pc in (host, client):
        pc.set_inventory_open(False)
    report.update(success=error is None, error=error)
    (saved / 'CompanyScreenMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK CompanyScreenMultiplayer success={error is None} error={error}')


def wait(phase, seconds=1.5):
    state.update(phase=phase, at=time.monotonic() + seconds)


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        ship, mate = state.get('ship'), state.get('mate')
        if p == 'start':
            ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
                        if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Schooner')
            mate = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            state.update(ship=ship, mate=mate)
            if not ship.get_fitting('Helm'):
                ship.verification_install_fitting('Helm', unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestShipHelm'))
            check('the host claims the schooner', ship.take_helm(host.get_controlled_pawn()) and ship.get_owner_name() == name(host))
            ship.leave_helm(host.get_controlled_pawn(), True)
            check('the client is not her shipmate', not ship.is_shipmate(mate))
            host.set_inventory_open(True)
            client.set_inventory_open(True)
            wait('open', 1.5)
        elif p == 'open':
            menu(host, server_world).open_section(2)
            menu(client, client_world).open_section(2)
            wait('create', 1.5)
        elif p == 'create':
            hs = screen(host, server_world)
            check('outside a Company the host\'s screen offers to make one', not hs.is_in_company() and hs.get_member_count() == 0)
            hs.create_company('Saltwind')
            wait('invite', 2.0)
        elif p == 'invite':
            hs = screen(host, server_world)
            check('the host\'s screen shows the new Company with its Leader', hs.is_in_company() and hs.get_company_name() == 'Saltwind'
                  and hs.get_member_count() == 1 and hs.get_viewer_rank() == 2, status=hs.get_status_text())
            hs.set_sub_tab(1)
            hs.invite_player(name(client))
            wait('accept', 2.0)
        elif p == 'accept':
            cs = screen(client, client_world)
            check('the client\'s screen shows the invitation', cs.get_incoming_invitation() == 'Saltwind', seen=cs.get_incoming_invitation())
            cs.set_sub_tab(1)
            key(client, 'Enter')
            wait('joined', 2.5)
        elif p == 'joined':
            hs, cs = screen(host, server_world), screen(client, client_world)
            check('both screens list two members', hs.get_member_count() == 2 and cs.get_member_count() == 2,
                  host=hs.get_member_count(), client=cs.get_member_count(), status=cs.get_status_text())
            check('the client is a Member, the host the Leader', cs.get_viewer_rank() == 0 and hs.get_viewer_rank() == 2)
            check('with Personal ships the client is still kept off her', not ship.is_shipmate(mate))
            hs.set_sub_tab(0)
            hs.cycle_ship_policy()
            wait('shared', 2.5)
        elif p == 'shared':
            hs, cs = screen(host, server_world), screen(client, client_world)
            check('the policy is Personal Shared on both screens', hs.get_ship_policy() == 1 and cs.get_ship_policy() == 1)
            check('and the client is her shipmate and takes her helm', ship.is_shipmate(mate) and ship.take_helm(mate))
            ship.leave_helm(mate, True)
            shot(server_world, 'company_live_host.png')
            shot(client_world, 'company_live_client.png')
            cs.do_action(5)
            check('leaving asks first', cs.is_confirm_open())
            key(client, 'Right')
            key(client, 'Enter')
            wait('left', 2.5)
        elif p == 'left':
            hs, cs = screen(host, server_world), screen(client, client_world)
            check('the client has left (both screens)', not cs.is_in_company() and hs.get_member_count() == 1, status=cs.get_status_text())
            check('and is kept off her again', not ship.is_shipmate(mate))
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
