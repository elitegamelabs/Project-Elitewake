"""Regenerate only the schooner and brigantine hull meshes after window-sealing changes.

Unlike the full ship builders, this helper does not load or save a map, move ships, or update ship definitions.
Run inside Unreal Editor outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_brigantine as brigantine  # noqa: E402
import build_schooner as schooner  # noqa: E402
from ship_geometry import write_static_mesh  # noqa: E402
from ship_interior import window_material  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    # Reuse the project's existing material assets without recompiling/saving them. The owner/another
    # local process may have those shared materials open while this bounded mesh refresh runs.
    hull_materials = [unreal.load_asset(f'{FOLDER}/{name}') for name in
                      ('M_ShipTimber_v1', 'M_ShipFabric_v1', 'M_LanternGlass_v1')]
    assert all(hull_materials), 'Build the existing ship hull/interior materials first.'
    hull_materials.append(window_material())
    results = {}
    for ship, builder, asset_name in (
            ('Schooner', schooner, 'SM_SchoonerHull_v1'),
            ('Brigantine', brigantine, 'SM_BrigantineHull_v1')):
        mesh_builder = builder.hull_mesh()
        asset = write_static_mesh(mesh_builder, f'{FOLDER}/{asset_name}', hull_materials, builder.UV_TILE)
        results[ship] = {
            'asset': asset.get_path_name(),
            'vertices': len(mesh_builder.verts),
            'triangles': len(mesh_builder.tris),
            'window_glass_triangles': sum(1 for slot in mesh_builder.slots if slot == 3),
            'complex_collision': str(asset.get_editor_property('body_setup').get_editor_property('collision_trace_flag')),
        }
        assert results[ship]['window_glass_triangles'] > 0, f'{ship} has no glass-slot triangles'
    Path(unreal.Paths.project_saved_dir(), 'SealedShipWindowsBuildResult.json').write_text(
        json.dumps({'success': True, 'ships': results}, indent=2))
    unreal.log('Schooner and brigantine sealed-window meshes rebuilt without changing maps or definitions')


if __name__ == '__main__':
    main()
