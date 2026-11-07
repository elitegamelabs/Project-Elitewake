"""Set the saved prototype ocean's maximum depth, preserving its surface and art."""
import json
from pathlib import Path
import unreal
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

OCEAN_MAX_DEPTH_METERS = 1500.0  # owner, October 22: the ocean at most 1,500 m deep (was 2,000 m)

def apply_depth(volume, bed, surface_z):
    depth = OCEAN_MAX_DEPTH_METERS * 100.0  # Unreal centimeters.
    center, extent = volume.get_actor_bounds(False)
    assert extent.z > 0, 'Ocean brush has no vertical extent'
    scale = volume.get_actor_scale3d()
    volume.set_actor_scale3d(unreal.Vector(scale.x, scale.y, scale.z * depth / (2 * extent.z)))
    center, extent = volume.get_actor_bounds(False)
    delta = unreal.Vector(-center.x, -center.y, surface_z - depth / 2 - center.z)
    volume.set_actor_location(volume.get_actor_location() + delta, False, False)
    # Keep the existing seabed thickness; its upper face is exactly the maximum depth below water.
    center, extent = bed.get_actor_bounds(False)
    assert extent.z > 0, 'Seabed has no thickness'
    bed.set_actor_location(bed.get_actor_location() + unreal.Vector(0, 0,
        surface_z - depth - (center.z + extent.z)), False, False)
    center, extent = volume.get_actor_bounds(False)
    bed_center, bed_extent = bed.get_actor_bounds(False)
    assert abs(center.z + extent.z - surface_z) < .1
    assert abs(center.z - extent.z - (surface_z-depth)) < .1
    assert abs(bed_center.z + bed_extent.z - (surface_z-depth)) < .1
    return {'maximum_depth_meters':OCEAN_MAX_DEPTH_METERS, 'water_surface_z_cm':surface_z,
            'water_bottom_z_cm':center.z-extent.z, 'seabed_top_z_cm':bed_center.z+bed_extent.z}

def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(), 'Save current map first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_name() == 'Lvl_CoastalPlayground', 'Open the coastal map first'
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    volume = next(a for a in actors if a.get_actor_label() == 'Coastal ocean swimming volume')
    bed = next(a for a in actors if a.get_actor_label() == 'Coastal seabed')
    sea = next(a for a in actors if a.get_actor_label().startswith('Coastal sea surface'))
    result = apply_depth(volume, bed, sea.get_actor_location().z)
    assert world_map.save_map()
    result.update(success=True, limits='Prototype flat deep seabed; regional bathymetry remains unbuilt')
    Path(unreal.Paths.project_saved_dir(), 'CoastalOceanDepthResult.json').write_text(json.dumps(result,indent=2))
    unreal.log(f'Saved coastal maximum ocean depth: {OCEAN_MAX_DEPTH_METERS:.0f} meters')

if __name__ == '__main__':
    main()
