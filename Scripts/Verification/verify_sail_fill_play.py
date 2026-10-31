"""Screenshots of the sloop's sails filled and slack (owner, October 16: sails billow when they catch the wind, go
slack and keep flapping when they don't; CLAUDE.md).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground (EW_PLAY_PLAYERS=1 is enough). Run unattended with
run_play_check.py. Fits out the moored sloop (helm, mainsail, headsail, full sail; she stays anchored), then:
  1. wind across her from port: both sails fill (|fill| over 0.8); photographed from 22 m to starboard, downwind;
  2. wind from dead ahead, along the sails: both go slack (|fill| under 0.2); photographed from the same place;
  3. wind across from starboard: they fill the other way (the mainsail's fill changes sign).
Shots in Saved/Screenshots/SailFill. How the cloth looks is a person's to judge; the numbers are AEWShip::GetSailFill.
Writes Saved/SailFillPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SailFillPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'SailFill')
SHOTS.mkdir(parents=True, exist_ok=True)
world = next(w for w in lib.get_play_worlds())
# Crew dependency (owner, October 18): the helm sets only sails with a hired sailhand, so every ship here is crewed first.
for _s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip):
    _s.crew_every_sail()
pc = unreal.GameplayStatics.get_player_controller(world, 0)
owner = pc.get_controlled_pawn()
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop')
wind = unreal.EWWindSubsystem.get_for_world(world)
folder = '/Game/Elitewake/Items/Testing'
items = [unreal.load_asset(f'{folder}/{n}') for n in ('DA_TestShipHelm', 'DA_TestSailMedium', 'DA_TestSailSmall')]
measured = {}
checks = []
state = {'index': 0, 'begun': False, 'at': 0.0, 'handle': None, 'shot': None}


def fills():
    return {m: round(ship.get_sail_fill(m), 2) for m in ('Mainsail', 'Headsail')}


def camera():
    """22 m off her sunlit side (or forward of it), 4 m up, looking at her sails; held there, the survivor hidden."""
    right = ship.get_actor_right_vector()
    # From whichever side the sun lights.
    sun = next(iter(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.DirectionalLight)), None)
    if sun and (sun.get_actor_forward_vector().x * right.x + sun.get_actor_forward_vector().y * right.y) > 0:
        right = right * -1.0
    right = right + ship.get_actor_forward_vector() * (0.6 if state.get('ahead') else 0.0)
    middle = ship.get_actor_location() + unreal.Vector(0, 0, 800)
    eye = ship.get_actor_location() + right * 2200 + unreal.Vector(0, 0, 400)
    owner.get_component_by_class(unreal.CharacterMovementComponent).set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    owner.set_actor_location(eye, False, True)
    owner.set_actor_hidden_in_game(True)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, middle))


def describe_sails():
    out = {}
    for c in ship.get_components_by_class(unreal.StaticMeshComponent):
        if 'Fitting_' in c.get_name() and ('sail' in c.get_name().lower()):
            mesh = c.get_editor_property('static_mesh')
            origin, extent = c.get_local_bounds()
            centre = ship.get_actor_transform().inverse_transform_location(c.bounds.origin) if hasattr(c, 'bounds') else None
            out[c.get_name()] = {'mesh': mesh.get_name() if mesh else None, 'visible': c.is_visible(),
                                 'materials': [m.get_name() if m else None for m in c.get_materials()],
                                 'local_extent': [round(v) for v in extent.to_tuple()],
                                 'location': [round(v) for v in ship.get_actor_transform().inverse_transform_location(c.get_world_location()).to_tuple()]}
    return out


def fit_out():
    for item in items:
        assert item and owner.get_inventory_component().add_item(item, 1) == 1
    assert lib.fit_out_ship_for_review(ship, owner, 4) == 3


def wind_from(side):
    """Set the wind: 'port' blows toward starboard, 'starboard' toward port, 'ahead' toward the stern."""
    yaw = ship.get_actor_rotation().yaw
    wind.set_wind_yaw(yaw + {'port': 90.0, 'starboard': -90.0, 'ahead': 180.0}[side])


def step(side, test, label):
    def begin():
        wind_from(side)
        state.update(at=time.monotonic(), shot=None)
    def done():
        camera()
        f = fills()
        if time.monotonic() - state['at'] < 3.0:
            return False   # the cloth follows the wind over a second or two
        if state['shot'] is None:
            assert test(f), f'{label}: fills {f}'
            measured[label] = f
            measured.setdefault('sails', describe_sails())
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / (label + ".png")}"')
            state['shot'] = time.monotonic()
            return False
        if not state.get('ahead') and time.monotonic() - state['shot'] > 1.0:
            state['ahead'] = True   # a second shot from forward of the beam
            state['shot'] = time.monotonic() + 1.0
            return False
        if state.get('ahead') and time.monotonic() > state['shot'] and not state.get('ahead_taken'):
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / (label + "_bow.png")}"')
            state['ahead_taken'] = True
            state['shot'] = time.monotonic()
            return False
        if state.get('ahead_taken') and time.monotonic() - state['shot'] > 1.0:
            state.update(ahead=False, ahead_taken=False)
            return True
        return False
    return begin, done


STEPS = [('The sloop is fitted out with full sail', fit_out, lambda: all(ship.get_fitting(m) for m in ('Helm', 'Mainsail', 'Headsail'))),
         ('Wind across from port: both sails fill', *step('port', lambda f: min(abs(v) for v in f.values()) > 0.8, 'filled')),
         ('Wind from ahead, along the sails: both go slack', *step('ahead', lambda f: max(abs(v) for v in f.values()) < 0.2, 'slack')),
         ('Wind across from starboard: they fill the other way',
          *step('starboard', lambda f: abs(f['Mainsail']) > 0.8 and f['Mainsail'] * measured['filled']['Mainsail'] < 0, 'filled_other_way'))]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWPLAYCHECK SailFill success={error is None} error={error}')


def tick(delta):
    description, begin, done = STEPS[state['index']]
    try:
        if not state['begun']:
            begin()
            state.update(begun=True, deadline=time.monotonic() + 20.0)
            return
        if done():
            checks.append(description)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
        elif time.monotonic() > state['deadline']:
            raise TimeoutError(f'{description}: fills {fills()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


unreal.SystemLibrary.execute_console_command(world, 'r.MotionBlurQuality 0')
state['handle'] = unreal.register_slate_post_tick_callback(tick)
