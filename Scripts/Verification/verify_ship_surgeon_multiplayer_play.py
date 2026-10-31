"""The ship's permanent surgeon and the Copper purse, with a second player (listen server plus one client, EW_PLAY_PLAYERS=2).
The client walks up to the surgeon (aboard the brigantine on the coastal map), is wounded, and treats itself through the real
interaction request. Checks: a surgeon stands aboard each ship with a deck below, and the client's world has them too; a new survivor
holds 250 Copper (the placeholder purse) and its own copy of the purse agrees; one treatment costs 15 Copper; the health comes back
gradually (some after 3 s, 25% of the maximum after 12 s, never past it); asking again during the treatment is refused and costs
nothing; with too little Copper the request is refused and nothing changes; a treatment near full health stops at the maximum.
Writes Saved/ShipSurgeonMultiplayerPlayResult.json."""
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
state = {'phase': 0, 'at': time.monotonic() + 14, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def sw():
    return unreal.GameplayStatics.get_time_seconds(server_world)


def surgeons(w):
    return unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWShipSurgeon)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'ShipSurgeonMultiplayerPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ShipSurgeonMultiplayer success={error is None} error={error}')


def stand_before(surgeon_local, survivor, controller):
    """Stand where a first placement worked (found once, then reused: the spot has a clear line to the surgeon) and look at her."""
    loc, fwd = surgeon_local.get_actor_location(), surgeon_local.get_actor_forward_vector()
    if 'spot' not in state:
        for dist in (110, 150, 90, 200):
            for lift in (100, 140, 60):
                spot = unreal.Vector(loc.x + fwd.x * dist, loc.y + fwd.y * dist, loc.z + lift)
                if survivor.teleport(spot, unreal.Rotator()):
                    state['spot'] = spot
                    break
            if 'spot' in state:
                break
    else:
        survivor.teleport(state['spot'], unreal.Rotator())
    report['gap'] = (survivor.get_actor_location() - loc).length()
    eye, _ = survivor.get_actor_eyes_view_point()
    controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(loc.x, loc.y, loc.z + 60)))


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            ships = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
            with_deck = [s for s in ships if s.get_editor_property('definition') and s.get_editor_property('definition').get_editor_property('has_surgeon')]
            check('ships with a deck below have a surgeon aboard', with_deck and all(s.get_surgeon() for s in with_deck), ships=len(with_deck))
            check('the client sees the surgeons too', len(surgeons(client_world)) == len(surgeons(server_world)) >= len(with_deck), server=len(surgeons(server_world)), client=len(surgeons(client_world)))
            owner = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(c) == pid(client.get_controlled_pawn()))
            state['owner'] = owner
            state['surgeon'] = with_deck[0].get_surgeon()
            state['mine'] = next(s for s in surgeons(client_world) if s.get_name() == state['surgeon'].get_name())
            check('a new survivor starts with an empty purse', owner.get_wallet_component().get_copper() == 0, copper=owner.get_wallet_component().get_copper())
            owner.get_wallet_component().set_copper(250)
            state['funded'] = time.monotonic() + 1.0
            owner.get_survival_component().apply_damage(40.0)
            state['health0'] = owner.get_survival_component().get_health()
            state['max'] = owner.get_survival_component().get_max_health()
            stand_before(state['surgeon'], state['owner'], client)
            state.update(phase=1, at=time.monotonic() + 1.5)
        elif p == 1:
            stand_before(state['surgeon'], state['owner'], client)
            state.update(phase=15, at=time.monotonic() + 2.0, tries=0)
        elif p == 15:
            check('the client asks the surgeon', lib.send_verification_interaction_request(client, state['mine']))
            state.update(phase=2, at=time.monotonic() + 1.2, t0=sw())
        elif p == 2:
            owner = state['owner']
            if owner.get_wallet_component().get_copper() == 250 and state['tries'] < 5:          # the aim had not settled: stand and ask again
                state['tries'] += 1
                report['retries'] = state['tries']
                stand_before(state['surgeon'], owner, client)
                state.update(phase=15, at=time.monotonic() + 2.0)
                return
            check('a treatment costs 15 Copper', owner.get_wallet_component().get_copper() == 235, copper=owner.get_wallet_component().get_copper())
            check('the client\'s purse shows it', client.get_controlled_pawn().get_wallet_component().get_copper() == 235)
            check('the surgeon is at work', state['surgeon'].is_treating() and state['mine'].is_treating())
            report['again_refused'] = not state['surgeon'].interact(state['owner'])        # again, mid-treatment
            state.update(phase=3, at=time.monotonic() + 1.0)
        elif p == 3:
            owner = state['owner']
            check('asking again mid-treatment costs nothing', owner.get_wallet_component().get_copper() == 235, copper=owner.get_wallet_component().get_copper())
            state.update(phase=4, at=time.monotonic() + 3.0)
        elif p == 4:
            health = state['owner'].get_survival_component().get_health()
            check('health is coming back gradually', health > state['health0'] + 3 and health < state['health0'] + 25, health0=state['health0'], health=health)
            state.update(phase=5, at=time.monotonic() + 11.0)
        elif p == 5:
            owner = state['owner']
            health = owner.get_survival_component().get_health()
            want = min(state['max'], state['health0'] + .25 * state['max'])
            check('25% of the maximum came back, no more', abs(health - want) < 1.0, health=health, want=want)
            check('the client sees the healed health', abs(client.get_controlled_pawn().get_survival_component().get_health() - health) < 1.5)
            check('the surgeon is idle again', not state['surgeon'].is_treating())
            owner.get_wallet_component().set_copper(10)
            owner.get_survival_component().apply_damage(30.0)
            state['hurt'] = owner.get_survival_component().get_health()
            state.update(phase=6, at=time.monotonic() + 1.2)
        elif p == 6:
            stand_before(state['surgeon'], state['owner'], client)
            state.update(phase=65, at=time.monotonic() + 2.5)
        elif p == 65:
            report['poor_refused'] = not state['surgeon'].interact(state['owner'])
            state.update(phase=7, at=time.monotonic() + 3.0)
        elif p == 7:
            owner = state['owner']
            check('with too little Copper nothing happens', owner.get_wallet_component().get_copper() == 10 and abs(owner.get_survival_component().get_health() - state['hurt']) < .6
                  and not state['surgeon'].is_treating(), copper=owner.get_wallet_component().get_copper())
            owner.get_wallet_component().set_copper(100)
            owner.get_survival_component().restore_health(1000.0)
            owner.get_survival_component().apply_damage(8.0)
            state.update(phase=8, at=time.monotonic() + 1.2)
        elif p == 8:
            stand_before(state['surgeon'], state['owner'], client)
            state.update(phase=85, at=time.monotonic() + 2.5)
        elif p == 85:
            report['near_full_accepted'] = state['surgeon'].interact(state['owner'])
            state.update(phase=9, at=time.monotonic() + 13.0)
        elif p == 9:
            owner = state['owner']
            health = owner.get_survival_component().get_health()
            check('a treatment near full health stops at the maximum', abs(health - state['max']) < .1 and owner.get_wallet_component().get_copper() == 85,
                  health=health, max=state['max'], copper=owner.get_wallet_component().get_copper(), gap=(owner.get_actor_location() - state['surgeon'].get_actor_location()).length(),
                  treating=state['surgeon'].is_treating(), given=state['surgeon'].get_treatments_given(), can=state['surgeon'].can_interact(owner),
                  prompt=str(state['surgeon'].get_interaction_prompt(owner)), hp=owner.get_survival_component().get_health())
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
