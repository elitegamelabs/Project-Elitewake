"""Play: spiders live in every cave and in the swamp (owner, October 16 milestone). One player.
Checks: every island's cave holds its spiders in the chamber; the swamp has spiders; a survivor who walks into the starter cave's
chamber is noticed, chased and bitten (health drops, the spider's action is Chase); the spiders stay in the chamber (the cave roof
and walls hold them); a screenshot of a spider is saved to Saved/Screenshots/Spiders/. Writes Saved/SpidersPlayResult.json."""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
survival = pawn.get_survival_component()
spiders = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal)
           if 'Spider' in str(a.get_editor_property('definition').get_editor_property('display_name'))]
report = {'checks': [], 'total': len(spiders)}
state = {'t0': time.monotonic() + 12, 'phase': 0, 'handle': None}
cave = T.CAVES['Starter']
chamber = cave.world(cave.chamber_u, 0.0)


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


def near(a, x, y, r):
    loc = a.get_actor_location()
    return math.hypot(loc.x - x, loc.y - y) < r


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'SpidersPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Spiders success={error is None} error={error}')


def tick(delta):
    if time.monotonic() < state['t0']:
        return
    try:
        p = state['phase']
        if p == 0:
            for key, c in T.CAVES.items():
                if not c:
                    continue
                cx, cy = c.world(c.chamber_u, 0.0)
                inside = [s for s in spiders if near(s, cx, cy, 700)]
                check(f'spiders in the {key} cave chamber', len(inside) >= 2, count=len(inside))
            swamp = [s for s in spiders if 'swamp' in str(s.get_actor_label()).lower()]
            check('spiders in the swamp', len(swamp) >= 1, count=len(swamp))
            state['start_health'] = survival.get_health()
            ux, uy = cave.world(cave.chamber_u - 450, 0.0)
            ok = False
            for lift in (120, 200, 300):
                ok = pawn.teleport(unreal.Vector(ux, uy, cave.floor + lift), unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(cave.heading)))
                if ok:
                    break
            check('survivor placed in the cave', ok)
            state.update(phase=1, at=now() + 1, until=now() + 40, seen=set())
        elif p == 1:
            local = [s for s in spiders if near(s, chamber[0], chamber[1], 900)]
            for s in local:
                state['seen'].add(str(s.get_action()).upper().split('.')[-1].split(':')[0].strip('<>'))
            report['actions_seen'] = sorted(state['seen'])
            if survival.get_health() < state['start_health'] - 1:
                report['health_lost'] = round(state['start_health'] - survival.get_health(), 1)
                check('a spider chased the survivor', 'CHASE' in state['seen'], seen=sorted(state['seen']))
                # a close-up of the nearest spider
                s = min(local, key=lambda a: unreal.Vector.distance(a.get_actor_location(), pawn.get_actor_location()))
                loc = s.get_actor_location()
                state['shot_spider'] = s
                state.update(phase=2, at=now() + .5)
            elif now() > state['until']:
                raise AssertionError(f'nobody was bitten in 40 s (actions {sorted(state["seen"])})')
        elif p == 2:
            if now() < state['at']:
                return
            check('spiders stay in the chamber', all(near(s, chamber[0], chamber[1], 1100) for s in spiders if near(s, chamber[0], chamber[1], 2500)))
            survival.restore_health(1000.0)
            s = state['shot_spider']
            loc = s.get_actor_location()
            yaw = math.degrees(s.get_actor_rotation().yaw * math.pi / 180) if False else s.get_actor_rotation().yaw
            fwd = unreal.MathLibrary.get_forward_vector(unreal.Rotator(roll=0, pitch=0, yaw=yaw + 35))
            cam = unreal.Vector(loc.x + fwd.x * 170, loc.y + fwd.y * 170, loc.z + 60)
            pawn.teleport(cam, unreal.Rotator())
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, unreal.Vector(loc.x, loc.y, loc.z + 20)))
            state.update(phase=3, at=now() + 1.2)
        elif p == 3:
            if now() < state['at']:
                return
            unreal.SystemLibrary.execute_console_command(world, 'Shot showui filename="' + str(saved / 'Screenshots' / 'Spiders' / 'Spider.png') + '"')
            state.update(phase=4, at=now() + 2)
        elif p == 4:
            if now() < state['at']:
                return
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
