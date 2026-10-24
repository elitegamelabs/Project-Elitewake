"""Debug: frames per second of a one-player Play session at the start, and the grass instance count. Writes Saved/DebugFps.json. EW_PLAY_PLAYERS=1."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
state = {'start': time.monotonic() + 8, 'frames': 0, 'handle': None}


def tick(delta):
    if time.monotonic() < state['start']:
        return
    state['frames'] += 1
    if time.monotonic() - state['start'] > 15:
        unreal.unregister_slate_post_tick_callback(state['handle'])
        total = 0
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
            for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
                mesh = comp.get_editor_property('static_mesh')
                if mesh and 'SM_GrassClump' in mesh.get_name():
                    total += comp.get_instance_count()
        Path(unreal.Paths.project_saved_dir(), 'DebugFps.json').write_text(json.dumps({'fps': state['frames'] / 15.0, 'grass_clumps': total}))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
