"""Phase 0 baseline truth captures (CLAUDE.md section 12): pictures to look at, not pass/fail and not an art pass.
Run through run_play_check.py with EW_PLAY_WINDOW=1920x1080 and EW_CAPTURE_SET set to one of:
  title    map Lvl_Title, EW_PLAY_STANDALONE=1, EW_PLAY_PLAYERS=1: the title screen with its UI;
  world    map Lvl_CoastalPlayground, EW_PLAY_PLAYERS=1: Plains spawn in daylight (the gameplay camera, with the HUD), then from a
           fixed 70-degree camera with no UI: Saltreach from the sea in daylight, each island from about 1 km offshore, and the
           Saltreach market at night;
  players  map Lvl_CoastalPlayground, EW_PLAY_PLAYERS=2: the client's survivor standing in front of the host, from the host's view.
Writes Saved/Screenshots/Phase0Baseline/<set>/*.png and Saved/Phase0Baseline_<set>.json."""
import json
import math
import os
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W
import world_terrain as T

lib = unreal.EWEditorVerificationLibrary
SET = os.environ.get('EW_CAPTURE_SET', 'world')
saved = Path(unreal.Paths.project_saved_dir())
shots = saved / 'Screenshots' / 'Phase0Baseline' / SET
shots.mkdir(parents=True, exist_ok=True)
for old in shots.glob('*.png'):
    old.unlink()
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
report = {'set': SET, 'shots': [], 'notes': []}
state = {'steps': [], 'i': 0, 'at': time.monotonic() + 4.0, 'handle': None}
EYE = T.SEA + 400.0            # ship-eye height, cm
DAY, NIGHT = 10.5, 22.0        # late morning; night


def shot(world, name, ui):
    unreal.SystemLibrary.execute_console_command(world, f'Shot {"showui " if ui else ""}filename="{shots / (name + ".png")}"')
    report['shots'].append(name + '.png')


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / f'Phase0Baseline_{SET}.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPHASE0 {SET} success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(state['steps']):
            finish()
            return
        wait = state['steps'][state['i']]()
        state['i'] += 1
        state['at'] = time.monotonic() + (wait or 0.5)
    except Exception as error:
        import traceback
        report['trace'] = traceback.format_exc()
        finish(repr(error))


def title_steps():
    world = worlds[0]
    return [lambda: shot(world, '01_title_screen', True)]


def world_steps():
    world, pc = worlds[0], pcs[0]
    pawn = pc.get_controlled_pawn()
    clock = unreal.EWDayNightSubsystem.get_for_world(world)
    cam = {}

    def set_hour(hour):
        clock.set_hour(hour)
        report['notes'].append(f'hour set to {hour}')
        return 4.0                      # let exposure settle

    def make_camera():
        cam['actor'] = lib.spawn_verification_camera(pc, pawn.get_actor_location(), pawn.get_actor_rotation(), 70.0)

    def place(x, y, z, yaw, pitch=-1.0):
        # The survivor waits a few metres behind the camera so the world streams in around it.
        back = math.radians(yaw)
        pawn.teleport(unreal.Vector(x - 600 * math.cos(back), y - 600 * math.sin(back), max(z, T.SEA + 300)), unreal.Rotator(0, 0, yaw))
        cam['actor'].set_actor_location_and_rotation(unreal.Vector(x, y, z), unreal.Rotator(0, pitch, yaw), False, False)
        pc.set_view_target_with_blend(cam['actor'], 0.0)
        return 5.0

    steps = [lambda: set_hour(DAY), lambda: shot(world, '01_plains_spawn_day', True), make_camera]
    port = W.PORTS['Plains']
    sx, sy = port.shore
    out = 100000.0                      # 1 km
    steps += [lambda: place(sx + out * math.cos(port.facing), sy + out * math.sin(port.facing), EYE, math.degrees(port.facing) + 180),
              lambda: shot(world, '02_saltreach_sea_approach_day', False)]
    for n, isle in enumerate(W.ISLANDS):
        ang = math.atan2(-isle.cy, -isle.cx) if (abs(isle.cx) > 5000 or abs(isle.cy) > 5000) else 0.0
        r = isle.radius(ang) + out
        x, y = isle.cx + r * math.cos(ang), isle.cy + r * math.sin(ang)
        steps += [lambda x=x, y=y, a=ang: place(x, y, EYE, math.degrees(a + math.pi)),
                  lambda k=isle.key, reg=isle.region, n=n: shot(world, f'{3 + n:02d}_island_{reg.lower()}_{k.lower()}_1km_day', False)]
    # The market lane: between the two rows of stalls (along 1650 and 2350 cm), looking down the lane.
    mx, my = port.world(2000.0, -1800.0)
    steps += [lambda: set_hour(NIGHT), lambda: place(mx, my, T.PORT_LEVEL + 175.0, math.degrees(port.facing) + 90, -4.0),
              lambda: shot(world, f'{3 + len(W.ISLANDS):02d}_saltreach_market_night', False),
              lambda: pc.set_view_target_with_blend(pawn, 0.0)]
    return steps


def players_steps():
    server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
    host = next(c for c in pcs if c.has_authority())
    client = next(c for c in pcs if not c.has_authority())

    def pid(p):
        return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']

    def face():
        unreal.EWDayNightSubsystem.get_for_world(server_world).set_hour(DAY)
        h = host.get_controlled_pawn()
        mate = next(c for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter)
                    if pid(c) == pid(client.get_controlled_pawn()))
        loc, yaw = h.get_actor_location(), host.get_control_rotation().yaw
        f = math.radians(yaw)
        # Ahead and to the right, so the host's own survivor does not hide the client's from the host's camera.
        r = f + math.pi / 2
        mate.teleport(unreal.Vector(loc.x + 500 * math.cos(f) + 220 * math.cos(r), loc.y + 500 * math.sin(f) + 220 * math.sin(r), loc.z + 50),
                      unreal.Rotator(0, 0, yaw + 200))
        host.set_control_rotation(unreal.Rotator(0, -6, yaw + 12))       # (roll, pitch, yaw)
        report['notes'].append(f'host PlayerId {pid(host.get_controlled_pawn())}, client PlayerId {pid(client.get_controlled_pawn())}')
        return 4.0

    # (Shot from the client's world captures the editor viewport, not the client's window, so only the host's view is taken.)
    return [face, lambda: shot(server_world, '01_two_players_host_view', True)]


state['steps'] = {'title': title_steps, 'world': world_steps, 'players': players_steps}[SET]()
state['handle'] = unreal.register_slate_post_tick_callback(tick)
