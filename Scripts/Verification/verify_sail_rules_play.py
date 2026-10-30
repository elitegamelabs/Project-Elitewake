"""Play: the owner's sailing rules (October 18, Docs/OwnerDecisions/SAIL_SPEED_WIND_AND_CODEX_PRIORITY_2026-10-18.md, with the delegated
choices). One player, /Game/Elitewake/Maps/Test/Lvl_ShipsTest:
  - each class's base speed: raft 3, dinghy 5, sloop 8, schooner 10, brigantine 12 knots;
  - the sloop under a full standard medium mainsail (with the small headsail full too) heads for 8 knots x 1.50: sails do not stack;
  - with the mainsail at half and the headsail full the better one counts: 8 x 1.30, not the sum;
  - with every sail lowered she stops at once and holds her place;
  - the dinghy under a full weighted small sail heads for 5 x 1.25, and the weighted sail steadies her;
  - the raft, paddled, takes a Small sail at its hardpoint and goes as fast as the better of her sail and her paddles.
Every speed is the class base x the crossing pace (1.6, owner October 30). Speeds are the ship's own target, with the wind's share and the load as they are at the time. Writes Saved/SailRulesPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
KNOT = 51.4444
PACE = 1.6   # AEWShip::CrossingPace (owner, October 30: bring back faster)
ITEMS = '/Game/Elitewake/Items'
report = {'checks': [], 'speeds': {}}
state = {'phase': 'start', 'at': time.monotonic() + 12, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'SailRulesPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SailRules success={error is None} error={error}')


def ship_of(ship_id):
    return next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
                if s.get_editor_property('definition') and str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id)


def item(path):
    return unreal.load_asset(f'{ITEMS}/{path}')


def expect(ship, knots, cap):
    return knots * KNOT * PACE * cap * ship.get_wind_factor() * ship.get_load_speed_factor()


def near(a, b, tol=2.0):
    return abs(a - b) <= tol


def hand(ship, mount, steps):
    """Work one sail by hand at its lines: steps up (+) or down (-)."""
    assert ship.take_lines(pawn, mount), f'lines {mount}'
    for _ in range(abs(steps)):
        ship.step_sail_by_hand(pawn, 1 if steps > 0 else -1)
    ship.leave_lines(pawn)


def board(ship):
    x = ship.get_actor_location()
    pawn.teleport(unreal.Vector(x.x, x.y, x.z + 300), unreal.Rotator())


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 'start':
            for ship_id, knots in (('Raft', 3), ('Dinghy', 5), ('Sloop', 8), ('Schooner', 10), ('Brigantine', 12)):
                top = ship_of(ship_id).get_editor_property('definition').get_editor_property('top_speed')
                check(f'{ship_id}: base speed {knots} knots', near(top, knots * KNOT, .5), top=top)
            sloop = ship_of('Sloop')
            for mount, path in (('Helm', 'Testing/DA_TestShipHelm'), ('Mainsail', 'Testing/DA_TestSailMedium'), ('Headsail', 'Testing/DA_TestSailSmall')):
                if not sloop.get_fitting(mount):
                    sloop.verification_install_fitting(mount, item(path))
            sloop.crew_every_sail()
            board(sloop)
            state.update(sloop=sloop, phase='sloop', at=time.monotonic() + 1.0)
        elif p == 'sloop':
            sloop = state['sloop']
            hand(sloop, 'Mainsail', 4)
            hand(sloop, 'Headsail', 4)
            target = sloop.compute_target_speed()
            want = expect(sloop, 8, 1.50)
            report['speeds']['sloop, medium and small full'] = target
            check('medium and small full: 8 knots x 1.50, the better sail, not the sum', near(target, want), target=target, want=want)
            check('a standard sail does not steady her', not sloop.is_weighted_sail_drawing())
            hand(sloop, 'Mainsail', -2)
            target = sloop.compute_target_speed()
            want = expect(sloop, 8, max(.5 * 1.50, 1.30))
            report['speeds']['sloop, medium half and small full'] = target
            check('medium at half and small full: the better counts (8 x 1.30)', near(target, want), target=target, want=want)
            check('her anchor comes up', sloop.set_anchored(pawn, False))
            state.update(phase='under_way', at=time.monotonic() + 4.0)
        elif p == 'under_way':
            sloop = state['sloop']
            check('she gets under way', sloop.get_speed() > 50, speed=sloop.get_speed())
            hand(sloop, 'Mainsail', -2)
            hand(sloop, 'Headsail', -4)
            state.update(phase='stopped', at=time.monotonic() + .3)
        elif p == 'stopped':
            sloop = state['sloop']
            check('every sail down: she stops at once', sloop.get_speed() == 0, speed=sloop.get_speed())
            state.update(phase='held', at=time.monotonic() + 2.5, held_at=sloop.get_actor_location())
        elif p == 'held':
            sloop, at = state['sloop'], state['held_at']
            moved = unreal.Vector(sloop.get_actor_location().x - at.x, sloop.get_actor_location().y - at.y, 0).length()
            check('and holds her place, no drift', moved < 1, moved=moved)
            sloop.set_anchored(pawn, True)
            dinghy = ship_of('Dinghy')
            check('the dinghy takes a weighted small sail', dinghy.verification_install_fitting('Sail', item('Ships/DA_SailSmallWeighted')))
            dinghy.crew_every_sail()
            board(dinghy)
            state.update(dinghy=dinghy, phase='dinghy', at=time.monotonic() + 1.0)
        elif p == 'dinghy':
            dinghy = state['dinghy']
            hand(dinghy, 'Sail', 4)
            target = dinghy.compute_target_speed()
            want = expect(dinghy, 5, 1.25)
            report['speeds']['dinghy, weighted small full'] = target
            check('a full weighted small sail: 5 knots x 1.25', near(target, want), target=target, want=want)
            check('a drawing weighted sail steadies her', dinghy.is_weighted_sail_drawing())
            raft = ship_of('Raft')
            check('the raft takes a Small sail at its hardpoint', raft.verification_install_fitting('Sail', item('Testing/DA_TestSailSmall')))
            board(raft)
            state.update(raft=raft, phase='raft', at=time.monotonic() + 1.0)
        elif p == 'raft':
            raft = state['raft']
            check('the survivor takes the paddles', raft.take_helm(pawn))
            for _ in range(4):
                raft.step_sails(pawn, 1)
            paddling = raft.compute_target_speed()
            want = 3 * KNOT * PACE * raft.get_load_speed_factor()
            report['speeds']['raft, hard stroke, sail down'] = paddling
            check('a hard stroke with the sail down: 3 knots', near(paddling, want), target=paddling, want=want)
            raft.leave_helm(pawn, True)
            hand(raft, 'Sail', 4)
            under_sail = raft.compute_target_speed()
            report['speeds']['raft, small sail full'] = under_sail
            report['raft_wind_share'] = raft.get_wind_factor()
            check('with her sail set she goes as fast as the better of sail and paddles',
                  near(under_sail, max(paddling, expect(raft, 3, 1.30))), under_sail=under_sail, sail=expect(raft, 3, 1.30))
            finish()
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
