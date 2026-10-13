"""Fill the island's freshwater pond. Safe to run again.
Run in the editor after build_coastal_terrain.py (which carves the basin), outside Play, then build_fish.py:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

The spring's small pool becomes a pond 14 m across: a water surface at the basin's rim in the spring's freshwater
material, a water volume filling the basin so survivors swim in it, and the drinking spot moved to the bank on the
side facing the beach. Bass, catfish and piranhas are placed in it by build_fish.py.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_coastal_flora import MAP, Ground  # noqa: E402
from coastal_layout import POND, POND_DEPTH, POND_RADIUS, POND_SURFACE  # noqa: E402

FOLDER = 'Coast/FreshWater'
SURFACE_LABEL, VOLUME_LABEL, SOURCE_LABEL = 'Freshwater surface', 'Freshwater pond water', 'Freshwater spring - E to drink'
BEACH = (150.0, 0.0)        # the beach spawn, which the drinking spot faces


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    found = {a.get_actor_label(): a for a in actors.get_all_level_actors() if str(a.get_folder_path()) == FOLDER}
    surface, source = found.get(SURFACE_LABEL), found.get(SOURCE_LABEL)
    assert surface and source, f'spring actors missing: {sorted(found)}'
    if VOLUME_LABEL in found:
        actors.destroy_actor(found[VOLUME_LABEL])

    # The surface: the spring's own water, widened to the pond and lying at its rim.
    surface.set_actor_location(unreal.Vector(POND[0], POND[1], POND_SURFACE - 1), False, False)
    surface.set_actor_scale3d(unreal.Vector((POND_RADIUS + 40) / 50, (POND_RADIUS + 40) / 50, .02))
    # Only a look: survivors fall through it into the water, and fish see the basin floor beneath it.
    surface.static_mesh_component.set_collision_profile_name('NoCollision')

    # The water: a volume filling the basin, so survivors and their sense of the water match the surface.
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    mesh = unreal.DynamicMesh()
    unreal.GeometryScript_Primitives.append_cylinder(mesh, unreal.GeometryScriptPrimitiveOptions(), unreal.Transform(),
                                                      POND_RADIUS, POND_DEPTH + 40, 32, 1, True, unreal.GeometryScriptPrimitiveOriginMode.BASE)
    options = unreal.GeometryScriptCreateNewVolumeFromMeshOptions()
    options.set_editor_property('volume_type', unreal.PhysicsVolume)
    at = unreal.Transform(location=unreal.Vector(POND[0], POND[1], POND_SURFACE - POND_DEPTH - 40))
    result = unreal.GeometryScript_NewAssetUtils.create_new_volume_from_mesh(mesh, world, at, 'FreshwaterPond', options)
    volume = next(r for r in result if isinstance(r, unreal.PhysicsVolume))
    volume.set_editor_property('water_volume', True)
    volume.set_editor_property('fluid_friction', .3)
    volume.set_actor_label(VOLUME_LABEL)
    volume.set_folder_path(FOLDER)

    # The drinking spot: on the bank, toward the beach.
    dx, dy = BEACH[0] - POND[0], BEACH[1] - POND[1]
    length = math.hypot(dx, dy)
    x, y = POND[0] + dx / length * (POND_RADIUS + 60), POND[1] + dy / length * (POND_RADIUS + 60)
    ground = Ground()
    source.set_actor_location(unreal.Vector(x, y, ground(x, y) + 10), False, False)

    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'FreshwaterPondResult.json').write_text(json.dumps(
        {'success': True, 'drink_at': [round(x), round(y), round(ground(x, y))], 'centre_floor': round(ground(*POND))}, indent=2))
    unreal.log('Freshwater pond filled')


if __name__ == '__main__':
    main()
