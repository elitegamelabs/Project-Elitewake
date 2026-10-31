"""Play: how Saltreach Freeport looks (owner, October 30). One player. The survivor is set at a run of viewpoints (the approach from
the harbor mouth, the lighthouse gallery over the harbor, the high street and market, the square and the tavern, the tavern's hall,
the shipyard, the long pier, the fishing jetty and the hiring office, the townsfolk close up) by day, then the square at night, and
a screenshot is taken at each. Saves Saved/Screenshots/FreeportLook/*.png and Saved/FreeportLookPlayResult.json; how it looks is
judged by looking at the shots."""
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
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
port = W.PORTS['Plains']
TOWN = T.PORT_LEVEL + 5
report = {'checks': [], 'shots': []}
state = {'t0': time.monotonic() + 12, 'i': 0, 'step': 0, 'at': 0.0, 'handle': None}
# name, survivor (along, across, z above the street), look at (along, across, z above the street), hour
VIEWS = [
    ('01_approach_from_sea', (13500, 1800, -120), (1500, 0, 400), 11.0),
    ('02_over_harbor_from_headland', (6400, -5200, 1700), (2200, 1200, -200), 11.0),
    ('03_harbor_from_long_pier_end', (9500, 1800, 10), (2000, 0, 500), 15.0),
    ('04_high_street_to_harbor', (-1200, -200, 0), (4000, 300, 150), 11.0),
    ('05_market', (2000, -1500, 0), (2000, 1200, 120), 11.0),
    ('06_square_and_tavern', (300, 900, 0), (-2400, -300, 300), 11.0),
    ('07_tavern_hall', (-2050, 200, 44), (-3000, -300, 140), 11.0),
    ('08_shipyard', (3400, -900, 0), (2000, -2800, 200), 11.0),
    ('09_jetty_and_hiring_office', (1200, 1800, 0), (-200, 3400, 150), 11.0),
    ('10_provisioner_close', (2000, -700, 0), (2390, -800, 160), 11.0),
    ('11_square_at_night', (600, 1100, 0), (-2400, -300, 250), 22.5),
    ('12_harbor_at_night', (9500, 1800, 10), (2000, 0, 400), 22.5),
]


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def at(a, c, dz):
    x, y = port.world(a, c)
    return unreal.Vector(x, y, TOWN + dz)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'FreeportLookPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK FreeportLook success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['t0'] or time.monotonic() < state['at']:
        return
    try:
        if state['i'] == 0 and state['step'] == 0:
            folk = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWTownsfolk)
            report['townsfolk'] = len(folk)
            check('the Freeport has its people', len(folk) >= 15, found=len(folk))
            # Hostile creatures nearby would chase the survivor round the viewpoints outside the town; none should be inside it.
            zone = unreal.EWSafeZone.find_at(world, at(0, 0, 0))
            check('the town lies in the safe zone', zone is not None)
        if state['i'] >= len(VIEWS):
            finish()
            return
        name, (a, c, dz), (ta, tc, tz), hour = VIEWS[state['i']]
        if state['step'] == 0:
            unreal.EWDayNightSubsystem.get_for_world(world).set_hour(hour)
            # A camera at the viewpoint (the survivor waits nearby on the ground so the place around is streamed and lit).
            eye, target = at(a, c, dz + 170), at(ta, tc, tz)
            if state.get('cam'):
                state['cam'].destroy_actor()
            state['cam'] = lib.spawn_verification_camera(pc, eye, unreal.MathLibrary.find_look_at_rotation(eye, target), 75.0)
            state.update(step=1, at=time.monotonic() + 3.0)
        elif state['step'] == 1:
            state.update(step=2, at=time.monotonic() + .5)
        else:
            path = saved / 'Screenshots' / 'FreeportLook' / f'{name}.png'
            unreal.SystemLibrary.execute_console_command(world, f'Shot filename="{path}"')
            report['shots'].append(name)
            state.update(i=state['i'] + 1, step=0, at=time.monotonic() + 1.0)
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
