"""Write versioned ship hull meshes and update only their hull-mesh references.

Unlike the full ship builders, this helper does not load or save a map, move ships, or alter mounts/moorings.
It creates new mesh paths rather than replacing the existing locked hull assets, then updates each definition's
`hull_mesh` reference (the Schooner/Brigantine window panes and the Sloop's visual surgeon-table prop).
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
import build_sloop_hull as sloop  # noqa: E402
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
    window_glass = unreal.load_asset(f'{FOLDER}/M_ShipWindowGlass_v1')
    if not window_glass:
        window_glass = window_material()
    hull_materials.append(window_glass)
    specs = (
            ('Schooner', schooner, 'SM_SchoonerHull_Windowed_v1', '/Game/Elitewake/Ships/DA_Ship_Schooner'),
            ('Brigantine', brigantine, 'SM_BrigantineHull_Windowed_v1', '/Game/Elitewake/Ships/DA_Ship_Brigantine'),
            ('Sloop', sloop, 'SM_SloopHull_Surgeon_v1', '/Game/Elitewake/Ships/DA_Ship_Sloop'))
    results = {}
    meshes = {}
    for ship, builder, asset_name, definition_path in specs:
        mesh_builder = builder.hull_mesh()
        asset = write_static_mesh(mesh_builder, f'{FOLDER}/{asset_name}', hull_materials, builder.UV_TILE)
        meshes[ship] = (asset, definition_path)
        results[ship] = {
            'asset': asset.get_path_name(),
            'definition': definition_path,
            'vertices': len(mesh_builder.verts),
            'triangles': len(mesh_builder.tris),
            'window_glass_triangles': sum(1 for slot in mesh_builder.slots if slot == 3),
            'complex_collision': str(asset.get_editor_property('body_setup').get_editor_property('collision_trace_flag')),
        }
        if ship != 'Sloop':
            assert results[ship]['window_glass_triangles'] > 0, f'{ship} has no glass-slot triangles'
    # Record generated meshes even if a shared ship definition is still locked by another process.
    result_path = Path(unreal.Paths.project_saved_dir(), 'SealedShipWindowsBuildResult.json')
    result_path.write_text(json.dumps({'success': False, 'meshes_built': results,
                                       'definitions_updated': [], 'blocked_definition': None}, indent=2))
    for ship, _, _, definition_path in specs:
        asset, _ = meshes[ship]
        definition = unreal.load_asset(definition_path)
        assert definition, definition_path
        definition.set_editor_property('hull_mesh', asset)
        if not unreal.EditorAssetLibrary.save_loaded_asset(definition):
            mesh_order = list(meshes)
            partial = {'success': False, 'meshes_built': results,
                       'definitions_updated': mesh_order[:mesh_order.index(ship)],
                       'blocked_definition': definition_path}
            result_path.write_text(json.dumps(partial, indent=2))
            raise RuntimeError(f'Cannot update {definition_path}; versioned meshes were generated and saved.')
    result_path.write_text(json.dumps({'success': True, 'meshes_built': results,
                                       'definitions_updated': [name for name, _, _, _ in specs]}, indent=2))
    unreal.log('Versioned sealed-window/treatment-prop hull meshes written; no map or mooring changed')


if __name__ == '__main__':
    main()
