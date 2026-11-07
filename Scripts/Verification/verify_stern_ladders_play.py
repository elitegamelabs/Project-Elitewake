"""Acceptance for the stern boarding ladders (owner, October 16: the boarding ladder directly at the horizontal centre of
the stern, on the ship's centreline, on every ship that has one).

Needs Play in /Game/Elitewake/Maps/Test/Lvl_ShipsTest (EW_PLAY_PLAYERS=1 is enough). Run unattended with
run_play_check.py. For the sloop, schooner and brigantine:
  1. the ship has exactly one ladder, and its foot and head lie on the centreline (within 1 cm), aft of the stern post;
  2. its foot is above the rudder's head and its head at the stern's rail;
  3. a screenshot from 14 m astern and 4.5 m up, looking at the ladder (Saved/Screenshots/SternLadders), for a person to
     judge the alignment.
Boarding itself is covered by verify_ladder_play, verify_ship_deck_play, verify_first_voyage_play,
verify_schooner_play and verify_brigantine_play. Writes Saved/SternLaddersPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SternLaddersPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'SternLadders')
SHOTS.mkdir(parents=True, exist_ok=True)
SHIPS = ('DA_Ship_Sloop', 'DA_Ship_Schooner', 'DA_Ship_Brigantine')

world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
ships = {}
for ship in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip):
    name = ship.get_editor_property('definition').get_name()
    if name in SHIPS and name not in ships:
        ships[name] = ship
measured = {}
state = {'queue': list(SHIPS), 'phase': 'check', 'at': 0.0, 'handle': None}


def check(name):
    ship = ships.get(name)
    assert ship, f'no {name} in the map'
    definition = ship.get_editor_property('definition')
    points = list(definition.get_editor_property('boarding_points'))
    tops = list(definition.get_editor_property('ladder_tops'))
    assert len(points) == 1 and len(tops) == 1, f'{name}: {len(points)} ladders, {len(tops)} heads'
    foot, head = points[0], tops[0]
    assert abs(foot.y) < 1 and abs(head.y) < 1, f'{name}: ladder off the centreline ({foot.y}, {head.y})'
    assert foot.x < 0 and head.x < foot.x, f'{name}: ladder not at the stern ({foot.x}, {head.x})'
    assert head.z > definition.get_editor_property('deck_height'), f'{name}: ladder head {head.z} below the deck'
    world_foot = ship.get_boarding_point_world(0)
    local = ship.get_actor_transform().inverse_transform_location(world_foot)
    assert abs(local.y) < 1, f'{name}: world ladder off the centreline by {local.y:.1f} cm'
    measured[name] = {'foot': [round(foot.x), round(foot.z)], 'head': [round(head.x), round(head.z)]}
    return ship, world_foot


def shoot(ship, foot):
    back = ship.get_actor_forward_vector() * -1.0
    eye = foot + back * 1400 + unreal.Vector(0, 0, 450)
    pawn.set_actor_location(eye, False, True)
    pawn.set_actor_hidden_in_game(True)   # the third-person camera looks past the survivor
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, foot + unreal.Vector(0, 0, 150)))


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': list(measured), 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWPLAYCHECK SternLadders success={error is None} error={error}')


def tick(delta):
    try:
        if not state['queue']:
            return finish()
        name = state['queue'][0]
        now = time.monotonic()
        if state['phase'] == 'check':
            state['ship'] = check(name)
            shoot(*state['ship'])
            state.update(phase='shot', at=now)
        elif state['phase'] == 'shot' and now - state['at'] < 0.6:
            shoot(*state['ship'])   # held up there until the frame is taken, before it falls
        elif state['phase'] == 'shot':
            unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (name + ".png")}"')
            state.update(phase='wait', at=now)
        elif state['phase'] == 'wait' and now - state['at'] > 1.0:
            state['queue'].pop(0)
            state['phase'] = 'check'
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
