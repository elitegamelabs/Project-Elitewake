"""Acceptance for the placement highlight (owner, October 17: placeable items show a blue highlight where they can be
placed, red where they cannot, and look normal once placed).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground with one player (EW_PLAY_PLAYERS=1: the preview shows on
the player's own screen, which is the one screenshots capture), with the moored sloop bare. Run unattended with
run_play_check.py. Standing on her deck, the survivor (test fittings granted in Play only):
  1. carrying a Medium sail, looks at the mainsail mount (Medium): a blue glowing sail shows there;
  2. looks at the headsail mount (Small): the Medium sail would not fit, so it shows red;
  3. carrying a cannon, looks at a cannon place behind the plain railing (no cannon railing fitted): red;
  4. installs the Medium sail at the mainsail mount: it stands there as itself, the highlight gone.
Screenshots of each in Saved/Screenshots/Placement. Writes Saved/PlacementPreviewPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'PlacementPreviewPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Placement')
SHOTS.mkdir(parents=True, exist_ok=True)
world = next(w for w in lib.get_play_worlds())
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
preview = pc.get_placement_preview()
ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
            if str(s.get_editor_property('definition').get_editor_property('ship_id')) == 'Sloop')
T = '/Game/Elitewake/Items/Testing'
sail, cannon = unreal.load_asset(f'{T}/DA_TestSailMedium'), unreal.load_asset(f'{T}/DA_TestCannon')
checks, measured = [], {}
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'at': 0.0, 'mount': None, 'shot': None}


def stand_and_look(mount, back=140):
    """On deck aft of the mount (or inboard for a side mount), looking at it."""
    at = ship.get_mount_world_transform(mount).translation
    local = ship.get_actor_transform().inverse_transform_location(at)
    spot = ship.get_actor_transform().transform_location(unreal.Vector(local.x - back if abs(local.y) < 100 else local.x + 60,
                                                                      local.y * .3, ship.get_deck_height() + 98))
    pawn.teleport(spot, ship.get_actor_rotation())
    pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    eye = pawn.get_actor_location() + unreal.Vector(0, 0, pawn.get_editor_property('base_eye_height'))
    target = at
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, target))


def look(mount, back=140):
    def begin():
        state.update(mount=mount, at=time.monotonic(), shot=None)
        stand_and_look(mount, back)
    return begin


def shows(colour_ok, label, item):
    def done():
        stand_and_look(state['mount'])
        if time.monotonic() - state['at'] < 1.0:
            return False
        if state['shot'] is None:
            assert preview.is_showing(), f'no preview at {state["mount"]} (aimed: {ship.find_aimed_mount(pawn)})'
            assert str(preview.get_preview_mount()) == state['mount'], preview.get_preview_mount()
            assert preview.get_preview_item() == item, preview.get_preview_item()
            assert preview.is_placeable() == colour_ok, f'placeable {preview.is_placeable()} at {state["mount"]}'
            measured[label] = {'mount': state['mount'], 'placeable': preview.is_placeable()}
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / (label + ".png")}"')
            state['shot'] = time.monotonic()
            return False
        return time.monotonic() - state['shot'] > 1.0
    return done


def grant():
    assert not ship.get_installed_fittings(), 'the sloop must start bare'
    inv = pawn.get_inventory_component()
    assert inv.add_item(sail, 1) == 1 and inv.add_item(cannon, 1) == 1
    # A first shot to throw away: the first one in a session can catch the editor's own viewport.
    unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / "warmup.png"}"')


def install():
    stand_and_look('Mainsail')
    state.update(at=time.monotonic(), shot=None, mount='Mainsail')
    assert lib.send_verification_interaction_request(pc, ship), 'the install request was refused'


def installed():
    stand_and_look('Mainsail')
    if ship.get_fitting('Mainsail') != sail:
        return False
    if time.monotonic() - state['at'] < 1.0:
        return False
    # Carrying no more Medium sails, the mount shows the sail as itself: no highlight there.
    assert not (preview.is_showing() and str(preview.get_preview_mount()) == 'Mainsail'), 'the highlight stays on the placed sail'
    sail_visual = next((c for c in ship.get_components_by_class(unreal.StaticMeshComponent) if 'Fitting_Mainsail' in c.get_name()), None)
    assert sail_visual and sail_visual.is_visible(), 'the placed sail is not drawn'
    names = [m.get_name() if m else '' for m in sail_visual.get_materials()]
    assert not any('Ghost' in n for n in names), f'the placed sail is drawn in the highlight: {names}'
    if state['shot'] is None:
        unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{SHOTS / "placed.png"}"')
        state['shot'] = time.monotonic()
        return False
    measured['placed'] = names
    return time.monotonic() - state['shot'] > 1.0


STEPS = [
    ('A Medium sail and a cannon granted in Play only; the sloop is bare', grant, lambda: time.sleep(0) or True, 2),
    ('Looking at the mainsail mount with a Medium sail: a blue highlight there', look('Mainsail'), shows(True, 'blue_mainsail', sail), 8),
    ('Looking at the headsail mount (Small): the Medium sail shows red', look('Headsail'), shows(False, 'red_headsail', sail), 8),
    ('Looking at a cannon place behind the plain railing: the cannon shows red', look('StarboardCannon1'), shows(False, 'red_cannon', cannon), 8),
    ('Installing the sail: it stands there as itself, the highlight gone', install, installed, 10),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': measured,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
    unreal.log(f'EWPLAYCHECK PlacementPreview success={error is None} error={error}')


def tick(delta):
    description, begin, done, timeout = STEPS[state['index']]
    try:
        if not state['begun']:
            begin()
            state.update(begun=True, deadline=time.monotonic() + timeout)
            return
        if done():
            checks.append(description)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
        elif time.monotonic() > state['deadline']:
            raise TimeoutError(f'not done within {timeout} s; preview showing {preview.is_showing()} at {preview.get_preview_mount()}, aimed {ship.find_aimed_mount(pawn)}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


unreal.SystemLibrary.execute_console_command(world, 'r.MotionBlurQuality 0')
state['handle'] = unreal.register_slate_post_tick_callback(tick)
