"""World directions, evidence captures (CLAUDE.md Phase 2, first slice; section 9.4): pictures to review, plus measured bearings.
Run through run_play_check.py on /Game/Elitewake/Maps/Lvl_CoastalPlayground with EW_PLAY_PLAYERS=1, EW_PLAY_WINDOW=1920x1080,
EW_PLAY_STARTER_KIT=0, EW_PLAY_RESULT=WorldDirectionsCaptures.json. Writes Saved/Screenshots/WorldDirections/*.png, 70-degree view.

North is world +Y and east -X (Source/EW/World/EWNorth.h): Winter north, Swamp south, Desert east, Jungle west.
  01-04 the gameplay camera on the Plains island's high ground facing each other island, late morning (HUD: the compass);
  05 the map screen at full extent: Winter at the top, Swamp at the bottom, Desert right, Jungle left (HUD);
  06 sunrise: the gameplay camera facing east at 06:30 (HUD).
For each, the compass heading and the island's measured bearing are written to the result; 'success' only means the pictures were taken.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'WorldDirections'
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
clock = unreal.EWDayNightSubsystem.get_for_world(world)
report = {'shots': [], 'facing': {}, 'notes': []}
EXPECTED = {'Winter': 0.0, 'Desert': 90.0, 'Swamp': 180.0, 'Jungle': 270.0}
# The Plains island's highest feature: a clear view over the sea in every direction.
_starter = W.island('Starter')
_top = max(_starter.features, key=lambda f: f[3])          # features are offsets from the island's centre
LOOKOUT = (_starter.cx + _top[0], _starter.cy + _top[1])


def shot(name, ui):
    unreal.SystemLibrary.execute_console_command(world, f'Shot {"showui " if ui else ""}filename="{shots / (name + ".png")}"')
    report['shots'].append(name + '.png')
    return 1.5


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 20000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else 0.0


def bearing(dx, dy):
    """Clockwise from north (+Y), east -X."""
    return (math.degrees(math.atan2(dy, dx)) - 90.0) % 360.0


def hour(h):
    clock.set_hour(h)
    report['notes'].append(f'hour {h}')
    return 4.0


def face(region):
    def go():
        x, y = LOOKOUT[0], LOOKOUT[1]
        pawn.set_actor_location(unreal.Vector(x, y, ground(x, y) + 120), False, True)
        pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
        target = next(i for i in W.ISLANDS if i.region == region)
        yaw = math.degrees(math.atan2(target.cy - y, target.cx - x))
        pc.set_control_rotation(unreal.Rotator(0.0, -2.0, yaw))
        report['facing'][region] = {'island_bearing': round(bearing(target.cx - x, target.cy - y), 1),
                                    'expected': EXPECTED[region], 'yaw': round(yaw, 1)}
        return 4.0
    return go


def heading(region):
    def read():
        compass = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWCompassWidget, False) if w.is_in_viewport())
        report['facing'][region]['compass_heading'] = round(compass.get_heading(), 1)
        return .5
    return read


def open_map():
    pc.set_map_open(True)
    return 4.0


def close_map():
    pc.set_map_open(False)
    return 1.5


def sunrise():
    x, y = LOOKOUT[0], LOOKOUT[1]
    pawn.set_actor_location(unreal.Vector(x, y, ground(x, y) + 120), False, True)
    pc.set_control_rotation(unreal.Rotator(0.0, 4.0, 180.0))     # east: -X
    return 4.0


steps = [lambda: unreal.SystemLibrary.execute_console_command(world, 'DisableAllScreenMessages'), lambda: hour(10.5)]
for n, region in enumerate(('Winter', 'Desert', 'Swamp', 'Jungle'), 1):
    steps += [face(region), heading(region), (lambda n=n, r=region: shot(f'0{n}_facing_{r.lower()}', True))]
steps += [open_map, lambda: shot('05_map_full_extent', True), close_map,
          lambda: hour(6.5), sunrise, lambda: shot('06_sunrise_east', True), lambda: hour(10.5)]
state = {'i': 0, 'at': time.monotonic() + 1.0, 'h': None}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error, map_open=pc.is_map_open())
    (saved / 'WorldDirectionsCaptures.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWDIRECTIONSCAPTURE success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(steps):
            finish()
            return
        wait = steps[state['i']]()
        state['i'] += 1
        state['at'] = time.monotonic() + (wait if isinstance(wait, float) else .5)
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
