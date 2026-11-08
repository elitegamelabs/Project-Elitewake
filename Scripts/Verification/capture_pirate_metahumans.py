"""Play capture: the two pirate MetaHumans (build_pirate_metahumans.py) standing on the title map's dock, full length and
faces close, for the owner's first look. One player in the editor on Lvl_Title:
    Scripts/Verification/run_play_check_once.ps1 -Check capture_pirate_metahumans.py -Result PirateCaptureResult.json -Players 1 -Map /Game/Elitewake/Maps/Lvl_Title
Screenshots in Saved/Screenshots/Pirates. Visual review pending.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
SHOTS = saved / 'Screenshots' / 'Pirates'
SHOTS.mkdir(parents=True, exist_ok=True)
BUILD = '/Game/Elitewake/Characters/Survivors'
report = {'shots': []}
state = {'phase': 'spawn', 'at': time.monotonic() + 3.0, 'h': None, 'view': 0}
VIEWS = [('Both', (330.0, 0.0, 120.0), (0.0, 0.0, 100.0)), ('MaleFace', (75.0, -45.0, 168.0), (0.0, -45.0, 166.0)),
         ('FemaleFace', (72.0, 45.0, 157.0), (0.0, 45.0, 155.0))]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    (saved / 'PirateCaptureResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK PirateCapture success={error is None} error={error}')


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        world = lib.get_play_worlds()[0]
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        if state['phase'] == 'spawn':
            spot = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.TargetPoint) if 'PreviewSpot' in [str(t) for t in a.tags])
            base = spot.get_actor_location()
            state['base'] = base
            for name, y in (('MH_PirateMale', -45.0), ('MH_PirateFemale', 45.0)):
                path = f'{BUILD}/{name}/{name}/BP_{name}'
                cls = unreal.load_class(None, f'{path}.BP_{name}_C')
                if not cls:
                    asset = unreal.load_asset(path)
                    report[name + '_asset'] = str(asset.get_class().get_name()) if asset else None
                    cls = asset.generated_class() if asset and hasattr(asset, 'generated_class') else None
                actor = lib.spawn_verification_actor(world, cls, base + unreal.Vector(0, y, 0), unreal.Rotator(0, 0, 0))
                report[name] = {'class': str(cls), 'spawned': actor is not None}
            title = pc.get_title_widget()
            if title:
                title.set_visibility(unreal.SlateVisibility.COLLAPSED)
            state.update(phase='view', at=time.monotonic() + 6.0)
        elif state['phase'] == 'view':
            name, eye, target = VIEWS[state['view']]
            base = state['base']
            at = base + unreal.Vector(*eye)
            look = unreal.MathLibrary.find_look_at_rotation(at, base + unreal.Vector(*target))
            lib.spawn_verification_camera(pc, at, look, 40.0 if name == 'Both' else 30.0)
            state.update(phase='shot', at=time.monotonic() + 2.5, name=name)
        elif state['phase'] == 'shot':
            unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{SHOTS / (state["name"] + ".png")}"')
            report['shots'].append(state['name'])
            state['view'] += 1
            state.update(phase='view' if state['view'] < len(VIEWS) else 'done', at=time.monotonic() + 2.0)
        else:
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
