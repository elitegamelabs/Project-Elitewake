"""Set the world's generated meshes up for the renderer. Safe to run again; the last step of rebuild_world.py. Run in
the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner, October 17: the Play window's warnings ("RAY TRACING GEOMETRY - ALWAYS RESIDENT MEMORY EXCEEDS 20% OF THE
BUDGET", "Video memory has been exhausted", "[VSM] Non-Nanite Marking Job Queue overflow"): what they are and how to
stop them. DECIDED (delegated):
  - Nanite for the large static meshes: every island's terrain and the sea floor, the boulders, the landmarks and
    pillars, the caves, the Ports' buildings, and the trees and plants (about ten thousand shadow casters; their
    cut-out leaves are fine for Nanite in 5.8). Each covers a large part of the sun's virtual shadow map, which is what overflowed its
    queue for non-Nanite meshes; Nanite also streams their detail. The fallback mesh (what collision and the
    dressing scripts' ground traces use) keeps every triangle, so nothing moves or floats.
  - No hardware ray tracing for foliage: the trees and their LODs, the gatherable plants, the grass and the Jungle's
    understory, and the sea floor's plants and corals. Ray tracing kept a copy of all of them resident in video memory; Lumen still lights them through
    its software path, which at their size looks the same.
Writes Saved/TuneRenderingResult.json.
"""
import json
from pathlib import Path
import unreal

NANITE = ['/Game/Elitewake/World/Meshes/Islands', '/Game/Elitewake/World/Rocks', '/Game/Elitewake/World/Landmarks',
          '/Game/Elitewake/World/Caves', '/Game/Elitewake/World/Ports', '/Game/Elitewake/World/Flora',
          '/Game/Elitewake/World/Seabed']
NO_RAY_TRACING = ['/Game/Elitewake/World/Flora', '/Game/Elitewake/World/Grass', '/Game/Elitewake/World/Seabed']


def meshes(folder):
    for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False):
        if '/Webs/' in path or '/LOD/' in path:
            continue   # the cave cobwebs (thin, see-through) and the trees' scratch LOD meshes: not Nanite
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            yield path, asset


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    report = {'nanite': 0, 'no_ray_tracing': 0, 'errors': []}
    for folder in NANITE:
        for path, mesh in meshes(folder):
            try:
                settings = mesh.get_editor_property('nanite_settings')
                if not settings.get_editor_property('enabled'):
                    settings.set_editor_property('enabled', True)
                    # Keep every triangle in the fallback mesh: collision and traces stay exact.
                    settings.set_editor_property('fallback_target', unreal.NaniteFallbackTarget.PERCENT_TRIANGLES)
                    settings.set_editor_property('fallback_percent_triangles', 1.0)
                    mesh.set_editor_property('nanite_settings', settings)
                    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
                report['nanite'] += 1
            except Exception as error:
                report['errors'].append(f'{path}: {error!r}')
    for folder in NO_RAY_TRACING:
        for path, mesh in meshes(folder):
            try:
                if mesh.get_editor_property('support_ray_tracing'):
                    mesh.set_editor_property('support_ray_tracing', False)
                    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
                report['no_ray_tracing'] += 1
            except Exception as error:
                report['errors'].append(f'{path}: {error!r}')
    report['success'] = not report['errors']
    Path(unreal.Paths.project_saved_dir(), 'TuneRenderingResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Rendering tuned: {report["nanite"]} Nanite, {report["no_ray_tracing"]} out of ray tracing, {len(report["errors"])} errors')
    assert report['success'], report['errors'][:3]


if __name__ == '__main__':
    main()
