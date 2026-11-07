"""Saltreach Freeport's people and rules (owner, October 30), with a second player (listen server plus one client, EW_PLAY_PLAYERS=2).
The client talks to each named person with a real interaction request (their dialogue window opens on the client's screen) and makes
choices through the window's server request:
  - Marta Vell, provisioner: buys a bundle of round shot; Oskar Brann, resource trader: sells the pack's wood; Lucia Fane, outfitter: buys a hat.
  - Gideon Rusk, recruiter: the roster of named sailors is seen on both sides; signing the first puts their articles in the pack.
  - Bess Harrow, tavern keeper: a rumour, a drink that slakes thirst, and a delivery job paid on handing in raw fish.
  - The notice board: the posted jobs.
  - Elias Thorne, shipwright: sells a weighted small sail, then a raft launched at the slipway with paddles and a small sail; holed, she
    is repaired whole.
  - Captain Ines Calder, harbor master: brings the raft in to a berth, then clears her for departure with the client set aboard.
  - Whoever is talked to faces the client (seen on both sides); a walker on the long pier stops while the client stands in the way,
    and walks on when they step aside.
  - The safe zone: a punch between the two players does nothing inside the town and hurts outside it; Build Mode refuses a spot in
    the town; no hostile creature lives inside it; the client's HUD announces leaving the Freeport and entering it again.
Writes Saved/FreeportMultiplayerPlayResult.json."""
import json
import math
import time
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
port = W.PORTS['Plains']
report = {'checks': [], 'replies': {}}
state = {'phase': 'start', 'at': time.monotonic() + 14, 'handle': None, 'tries': 0, 'queue': []}
ITEMS = '/Game/Elitewake/Items'


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'FreeportMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK FreeportMultiplayer success={error is None} error={error}')


def item(path):
    return unreal.load_asset(f'{ITEMS}/{path}')


def count(path):
    it = item(path)
    return sum(e.quantity for e in state['owner'].get_inventory_component().get_inventory_entries() if e.item_definition == it)


def copper():
    return state['owner'].get_wallet_component().get_copper()


def person(name):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWTownsfolk) if str(a.get_editor_property('npc_name')) == name)


def peer(actor):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWTownsfolk) if a.get_name() == actor.get_name())


def stand_before(npc, dist=200):
    loc, fwd = npc.get_actor_location(), npc.get_actor_forward_vector()
    owner = state['owner']
    owner.teleport(unreal.Vector(loc.x + fwd.x * dist, loc.y + fwd.y * dist, loc.z + 100), unreal.Rotator())
    eye, _ = owner.get_actor_eyes_view_point()
    client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(loc.x, loc.y, loc.z + 120)))


def choose(npc, key):
    if key.startswith('Key'):
        # The window's own keys: the number of a shown choice.
        assert lib.send_verification_ui_key(client, key[3:])
        return
    assert lib.send_verification_dialogue_choice(client, peer(npc), key)


def hud():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWSurvivalWidget, False)
                if w.get_owning_player() == client)


def faces(npc, who):
    to = who.get_actor_location() - npc.get_actor_location()
    yaw = unreal.MathLibrary.make_rot_from_x(unreal.Vector(to.x, to.y, 0)).yaw
    return abs(((npc.get_actor_rotation().yaw - yaw) + 180) % 360 - 180)


def at(a, c, z):
    x, y = port.world(a, c)
    return unreal.Vector(x, y, z)


# Each talk: (person, distance in front, the steps once the window is open). A step is (key or None, check function or None).
def talks():
    shot0 = {}
    return [
        ('Marta Vell', 230, [
            (None, lambda: check('Marta knows who she is talking to, on both sides, and faces them',
                                 person('Marta Vell').get_talking_with() == state['owner'] and peer(person('Marta Vell')).get_talking_with() == client.get_controlled_pawn()
                                 and faces(person('Marta Vell'), state['owner']) < 30, yaw_off=faces(person('Marta Vell'), state['owner']))),
            ('Buy0', lambda: check('Marta sells a bundle of five round shot for 50 Copper', count('Testing/DA_TestRoundShot') == 5 and copper() == 1150,
                                   shot=count('Testing/DA_TestRoundShot'), copper=copper()))]),
        ('Oskar Brann', 230, [
            (None, lambda: state['owner'].get_inventory_component().add_item(item('Testing/DA_TestWood'), 10)),
            ('SellAll', lambda: check('Oskar buys the wood', count('Testing/DA_TestWood') == 0 and copper() == 1150 + 10 * item('Testing/DA_TestWood').get_editor_property('sell_value_copper'),
                                      copper=copper()))]),
        ('Lucia Fane', 230, [
            (None, lambda: shot0.update(c=copper())),
            ('KeyOne', lambda: check('pressing 1 in the window buys the first hat', count('Testing/DA_TestHat') == 1 and copper() == shot0['c'] - 80, copper=copper()))]),
        ('Gideon Rusk', 220, [
            (None, lambda: check('the recruiter has a roster, seen by the client too', len(person('Gideon Rusk').get_roster()) == 6
                                 and len(peer(person('Gideon Rusk')).get_roster()) == 6, roster=[r.name for r in person('Gideon Rusk').get_roster()])),
            (None, lambda: shot0.update(r=person('Gideon Rusk').get_roster()[0], c=copper())),
            ('Hire0', lambda: check('signing the first sailor gives their articles for their fee',
                                    count('Crew/DA_GunnerArticles' if shot0['r'].gunner else 'Crew/DA_SailhandArticles') == 1 and copper() == shot0['c'] - shot0['r'].fee
                                    and len(person('Gideon Rusk').get_roster()) == 5, sailor=shot0['r'].name, copper=copper()))]),
        ('Bess Harrow', 200, [
            ('Rumor', lambda: check('Bess tells a rumour', len(str(client.get_last_dialogue_reply())) > 20, reply=client.get_last_dialogue_reply())),
            (None, lambda: (state['owner'].get_survival_component().set_hydration(40.0), shot0.update(c=copper()))),
            ('Drink', lambda: check('a drink slakes thirst for 5 Copper', state['owner'].get_survival_component().get_hydration() >= 69.0 and copper() == shot0['c'] - 5,
                                    hydration=state['owner'].get_survival_component().get_hydration())),
            (None, lambda: (state['owner'].get_inventory_component().add_item(item('Food/DA_RawFish'), 5), shot0.update(c=copper()))),
            ('Job0', lambda: check('the fish job pays on handing in five raw fish', count('Food/DA_RawFish') == 0 and copper() == shot0['c'] + 45, copper=copper()))]),
        ('notice board', 170, [
            ('Jobs', lambda: check('the notice board lists the jobs', 'Raw Fish' in str(client.get_last_dialogue_reply()) or 'Fish' in str(client.get_last_dialogue_reply()),
                                   reply=client.get_last_dialogue_reply()))]),
        ('Elias Thorne', 220, [
            (None, lambda: shot0.update(ships=len(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)), c=copper())),
            ('Buy3', lambda: check('Elias sells a weighted small sail for 180 Copper', count('Ships/DA_SailSmallWeighted') == 1 and copper() == shot0['c'] - 180,
                                   copper=copper())),
            (None, lambda: shot0.update(c=copper())),
            ('Ship0', lambda: check('Elias launches a raft at the slipway for her price (60 Copper since November 1)',
                                    len(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)) == shot0['ships'] + 1
                                    and copper() == shot0['c'] - person('Elias Thorne').get_editor_property('ships_for_sale')[0].get_editor_property('price_copper'),
                                    copper=copper(), reply=client.get_last_dialogue_reply())),
            (None, lambda: hole_the_raft()),
            ('Repair', lambda: check('Elias repairs the holed raft', state['raft'].get_hull_health() >= state['raft'].get_max_hull_health() - .01
                                     and state['raft'].get_hole_count() == 0, health=state['raft'].get_hull_health(), reply=client.get_last_dialogue_reply()))]),
        ('Captain Ines Calder', 220, [
            ('Berth', lambda: check('the harbor master brings the raft in to a berth', person('Captain Ines Calder').find_berth_of(state['raft']) >= 0,
                                    reply=client.get_last_dialogue_reply())),
            ('Depart', lambda: check('clearing her for departure tows her to the harbor mouth with the client aboard',
                                     (state['raft'].get_actor_location() - person('Captain Ines Calder').get_editor_property('departure_lane').translation).length() < 200
                                     and state['raft'].is_aboard(state['owner']), at=state['raft'].get_actor_location(), reply=client.get_last_dialogue_reply()))]),
    ]


def hole_the_raft():
    ships = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
    launch = person('Elias Thorne').get_editor_property('launch_point').translation
    raft = min(ships, key=lambda s: (s.get_actor_location() - launch).length())
    state['raft'] = raft
    check('the new raft lies at the slipway', (raft.get_actor_location() - launch).length() < 300 and str(raft.get_editor_property('definition').get_editor_property('ship_id')) == 'Raft')
    check('she is fitted out, paddles and a small sail', bool(raft.get_fitting('Helm')) and bool(raft.get_fitting('Sail')))
    loc = raft.get_actor_location()
    raft.take_round_shot(unreal.Vector(loc.x, loc.y, loc.z + 30), unreal.Vector(0, 0, 1), None)
    check('a round shot holes her', raft.get_hole_count() == 1 and raft.get_hull_health() < raft.get_max_hull_health())


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 'start':
            owner = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            state['owner'] = owner
            state['other'] = host.get_controlled_pawn()
            owner.get_wallet_component().set_copper(1200)
            names = [str(a.get_editor_property('npc_name')) for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWTownsfolk) if str(a.get_editor_property('npc_name'))]
            report['people'] = names
            for name in ('Marta Vell', 'Oskar Brann', 'Lucia Fane', 'Gideon Rusk', 'Bess Harrow', 'Elias Thorne', 'Captain Ines Calder', 'notice board'):
                check(f'{name} is in the Freeport', name in names)
            state['queue'] = talks()
            state.update(phase='next', at=time.monotonic() + .5)
        elif p == 'next':
            if not state['queue']:
                state.update(phase='walker', at=time.monotonic() + .5, tries=0)
                return
            name, dist, steps = state['queue'].pop(0)
            state.update(npc=person(name), dist=dist, steps=steps, tries=0)
            if client.is_dialogue_open():
                # Leave as a player does: Escape in the window.
                lib.send_verification_ui_key(client, 'Escape')
                check('Escape closes the window', not client.is_dialogue_open())
            stand_before(state['npc'], dist)
            state.update(phase='ask', at=time.monotonic() + 1.5)
        elif p == 'ask':
            report.setdefault('prompts', {})[str(state['npc'].get_editor_property('npc_name'))] = str(state['npc'].get_interaction_prompt(state['owner']))
            check(f'the client talks to {state["npc"].get_editor_property("npc_name")}', lib.send_verification_interaction_request(client, peer(state['npc'])))
            state.update(phase='opened', at=time.monotonic() + 1.5)
        elif p == 'opened':
            if not (client.is_dialogue_open() and client.get_dialogue_speaker() == peer(state['npc'])):
                if state['tries'] < 5:
                    state['tries'] += 1
                    stand_before(state['npc'], state['dist'])
                    state.update(phase='ask', at=time.monotonic() + 1.5)
                    return
                check(f'the window opens for {state["npc"].get_editor_property("npc_name")}', False, open=client.is_dialogue_open())
            widget = client.get_dialogue_widget()
            report.setdefault('windows', {})[str(state['npc'].get_editor_property('npc_name'))] = {
                'line': str(widget.get_shown_line()), 'options': widget.get_shown_option_count()}
            state.update(phase='step', at=time.monotonic() + .3)
        elif p == 'step':
            if not state['steps']:
                state.update(phase='next', at=time.monotonic() + .3)
                return
            key, after = state['steps'][0]
            if key and not state.get('sent'):
                report.setdefault('distances', {})[f'{state["npc"].get_editor_property("npc_name")}: {key}'] = [
                    round((state['owner'].get_actor_location() - state['npc'].get_actor_location()).length()),
                    str(state['owner'].get_actor_location()), str(state['npc'].get_actor_location())]
                choose(state['npc'], key)
                state.update(sent=True, at=time.monotonic() + 1.5)
                return
            state['steps'].pop(0)
            state['sent'] = False
            if key:
                report['replies'][f'{state["npc"].get_editor_property("npc_name")}: {key}'] = str(client.get_last_dialogue_reply())
            if after:
                after()
            state['at'] = time.monotonic() + .3
        elif p == 'walker':
            if client.is_dialogue_open():
                lib.send_verification_ui_key(client, 'Escape')
            pell = person('Pell')
            state['pell'] = pell
            if not pell.is_walking() and state['tries'] < 60:
                state['tries'] += 1
                state['at'] = time.monotonic() + .5
                return
            check('Pell walks his round on the long pier', pell.is_walking())
            loc, fwd = pell.get_actor_location(), pell.get_actor_forward_vector()
            state['owner'].teleport(unreal.Vector(loc.x + fwd.x * 110, loc.y + fwd.y * 110, loc.z + 100), unreal.Rotator())
            state.update(phase='walker_blocked', at=time.monotonic() + 2.5, pell_at=None)
        elif p == 'walker_blocked':
            pell = state['pell']
            if state['pell_at'] is None:
                state.update(pell_at=pell.get_actor_location(), at=time.monotonic() + 1.5)
                return
            moved = (pell.get_actor_location() - state['pell_at']).length()
            check('a survivor in the way stops him (no walking through them)', pell.is_held() and not pell.is_walking() and moved < 5, moved=moved,
                  gap=(pell.get_actor_location() - state['owner'].get_actor_location()).length())
            check('the client sees him stopped', peer(pell).is_held())
            x, y = port.world(2000, 0)
            state['owner'].teleport(unreal.Vector(x, y, T.PORT_LEVEL + 110), unreal.Rotator())
            state.update(phase='walker_free', at=time.monotonic() + 3.0, pell_at=pell.get_actor_location())
        elif p == 'walker_free':
            pell = state['pell']
            moved = (pell.get_actor_location() - state['pell_at']).length()
            check('with the way clear he walks on', not pell.is_held() and moved > 100, moved=moved)
            check('the client sees him walk on', not peer(pell).is_held() and (peer(pell).get_actor_location() - pell.get_actor_location()).length() < 60,
                  apart=(peer(pell).get_actor_location() - pell.get_actor_location()).length())
            state.update(phase='safe', at=time.monotonic() + .5)
        elif p == 'safe':
            if client.is_dialogue_open():
                lib.send_verification_ui_key(client, 'Escape')
            owner, other = state['owner'], state['other']
            # Face to face in the square: the client swings at the host.
            spot = at(-600, 600, T.PORT_LEVEL + 110)
            other.teleport(spot, unreal.Rotator())
            owner.teleport(unreal.Vector(spot.x + 90, spot.y, spot.z), unreal.Rotator())
            state.update(phase='punch_in', at=time.monotonic() + 1.0)
        elif p == 'punch_in':
            eye, _ = state['owner'].get_actor_eyes_view_point()
            client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['other'].get_actor_location()))
            state['hp0'] = state['other'].get_survival_component().get_health()
            lib.send_verification_attack(client, None)
            state.update(phase='punched_in', at=time.monotonic() + 1.2)
        elif p == 'punched_in':
            check('inside the Freeport a punch does nothing', state['other'].get_survival_component().get_health() >= state['hp0'],
                  before=state['hp0'], after=state['other'].get_survival_component().get_health())
            # The same, out on the island's far side (well beyond the safe zone).
            x, y = port.world(-12000, 0)
            spot = unreal.Vector(x, y, 20000)
            ground = unreal.SystemLibrary.line_trace_single(server_world, spot, unreal.Vector(x, y, -5000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
                                                          list(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWForest)),   # the ground, not a treetop (forests, November 6)
                                                          unreal.DrawDebugTrace.NONE, True)
            z = ground.to_tuple()[4].z + 110 if ground else T.PORT_LEVEL + 400
            check('the control spot is outside every safe zone', unreal.EWSafeZone.find_at(server_world, unreal.Vector(x, y, z)) is None)
            state['other'].teleport(unreal.Vector(x, y, z), unreal.Rotator())
            state['owner'].teleport(unreal.Vector(x + 90, y, z), unreal.Rotator())
            state.update(phase='punch_out', at=time.monotonic() + 1.5)
        elif p == 'punch_out':
            eye, _ = state['owner'].get_actor_eyes_view_point()
            client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['other'].get_actor_location()))
            state['hp1'] = state['other'].get_survival_component().get_health()
            lib.send_verification_attack(client, None)
            state.update(phase='punched_out', at=time.monotonic() + 1.2)
        elif p == 'punched_out':
            check('outside it the punch lands', state['other'].get_survival_component().get_health() < state['hp1'],
                  before=state['hp1'], after=state['other'].get_survival_component().get_health())
            x, y = port.world(-600, 600)
            why = unreal.BuildZones.check_point(server_world, x, y) if hasattr(unreal, 'BuildZones') else unreal.EWBuildZones.check_point(server_world, x, y)
            report['build_refusal'] = why
            check('Build Mode refuses a spot in the town', 'free port' in why, why=why)
            hostile = [a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWAnimal)
                       if a.get_editor_property('definition') and a.get_editor_property('definition').get_editor_property('aggressive')
                       and unreal.EWSafeZone.keeps_hostiles_out(server_world, a.get_actor_location())]
            check('no hostile creature lives inside the Freeport', not hostile, found=[a.get_name() for a in hostile])
            report['leave_banner'] = str(hud().get_displayed_zone_banner())
            check('the HUD tells the client they have left the Freeport', 'Leaving Saltreach Freeport' in report['leave_banner'], banner=report['leave_banner'])
            state['owner'].teleport(at(-600, 1200, T.PORT_LEVEL + 110), unreal.Rotator())
            state.update(phase='back_in', at=time.monotonic() + 2.0)
        elif p == 'back_in':
            report['enter_banner'] = str(hud().get_displayed_zone_banner())
            check('and that they are back in it, with its rules', 'Saltreach Freeport' in report['enter_banner'] and 'no fighting' in report['enter_banner'],
                  banner=report['enter_banner'])
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
