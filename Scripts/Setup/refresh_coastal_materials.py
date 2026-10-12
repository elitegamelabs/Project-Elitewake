"""Weather the coastal dock and deepen the ocean's colour. Safe to run again.
Run in the editor after build_coastal_terrain.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

- Dock: a weathered timber material for every dock plank, the landing and the posts. The owner's timber texture is
  bleached toward silver-grey with its grain darkened, projected from the world so long planks never stretch it,
  and varied a little from plank to plank. Posts darken where the sea wets them and carry green weed at the
  waterline.
- Ocean: deeper, darker water out at sea; the shallows over the sand stay clear. Colour values are tuning.
"""
import json
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import material_builder  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
DOCK_MATERIAL = '/Game/Elitewake/World/Materials/M_DockTimberWeathered_v1'
TIMBER = '/Game/Elitewake/World/Materials/T_Timber_v1'
OCEAN = '/Game/Elitewake/World/Water/MI_CoastalOcean_v1'
SEA_Z = -65.0
# Ocean colour (tuning), chosen from side-by-side Play captures: what deep water scatters back (RGB, A strength),
# the surface's own albedo, and how fast each colour is absorbed (RGB, A scale), so red and green fade with depth.
OCEAN_COLOURS = {
    'Scattering': unreal.LinearColor(0.02, 0.08, 0.12, 0.25),
    'Water Albedo': unreal.LinearColor(0.3, 0.35, 0.4, 0.5),
    'Absorption': unreal.LinearColor(30, 120, 300, 8),
}


def set_vector_parameters(instance, values):
    """Override vector parameters by writing the instance's own list: the usual setter refuses the Water plugin's
    ocean colours although the parent exposes them."""
    entries = [e for e in instance.get_editor_property('vector_parameter_values')
               if str(e.get_editor_property('parameter_info').get_editor_property('name')) not in values]
    for name, colour in values.items():
        info = unreal.MaterialParameterInfo()
        info.set_editor_property('name', name)
        entry = unreal.VectorParameterValue()
        entry.set_editor_property('parameter_info', info)
        entry.set_editor_property('parameter_value', colour)
        entries.append(entry)
    instance.set_editor_property('vector_parameter_values', entries)
    unreal.MaterialEditingLibrary.update_material_instance(instance)


def dock_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(DOCK_MATERIAL)
    texture = unreal.load_asset(TIMBER)
    position = node(unreal.MaterialExpressionWorldPosition)
    normal = node(unreal.MaterialExpressionVertexNormalWS)
    origin = node(unreal.MaterialExpressionObjectPositionWS)
    # Three projections, chosen by the face's normal: grain runs along deck planks (Y) and up the posts (Z).
    projections = {
        'Top': 'return P.xy / 150;',
        'Side': 'return (P.z < 0 ? P.yz : P.zy) / 150;',
        'End': 'return P.xz / 150;',
    }
    samples = {}
    for name, code in projections.items():
        uv = custom(code, unreal.CustomMaterialOutputType.CMOT_FLOAT2, ('P',))
        assert mel.connect_material_expressions(position, '', uv, 'P')
        sample = node(unreal.MaterialExpressionTextureSample, texture=texture)
        assert mel.connect_material_expressions(uv, '', sample, 'UVs')
        samples[name] = sample
    colour = custom(
        'float3 n = abs(N);'
        ' float3 w = n.z > 0.7 ? Top : (n.x >= n.y ? Side : End);'
        # A steady random tone per plank or post.
        ' float r = frac(sin(dot(O.xy, float2(12.9898, 78.233))) * 43758.5453);'
        ' float grey = dot(w, float3(0.3, 0.59, 0.11));'
        ' float3 bleached = lerp(w * float3(1.0, 0.86, 0.7), grey * float3(1.02, 1.0, 0.95), 0.7);'
        ' float3 c = pow(saturate(bleached * 1.1), 1.3) * lerp(0.78, 1.08, r);'
        # Wet below the deck toward the sea, with weed in a band at the waterline.
        ' float wet = saturate((Sea + 60 - P.z) / 60);'
        ' float weed = saturate(1 - abs(P.z - Sea) / 35) * 0.8;'
        ' c = lerp(c, c * 0.45, wet);'
        ' return lerp(c, float3(0.07, 0.11, 0.05), weed);',
        unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('N', 'O', 'P', 'Top', 'Side', 'End', 'Sea'))
    rough = custom('return lerp(0.88, 0.45, saturate((Sea + 60 - P.z) / 60));', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('P', 'Sea'))
    sea = node(unreal.MaterialExpressionConstant, r=SEA_Z)
    for source, pin in ((normal, 'N'), (origin, 'O'), (position, 'P'), (sea, 'Sea')):
        assert mel.connect_material_expressions(source, '', colour, pin)
    for name, sample in samples.items():
        assert mel.connect_material_expressions(sample, 'RGB', colour, name)
    for source, pin in ((position, 'P'), (sea, 'Sea')):
        assert mel.connect_material_expressions(source, '', rough, pin)
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    report = {}
    material = dock_material()
    ocean = unreal.load_asset(OCEAN)
    assert ocean, 'Run build_coastal_terrain.py first'
    set_vector_parameters(ocean, OCEAN_COLOURS)
    assert unreal.EditorAssetLibrary.save_loaded_asset(ocean)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    dock = [a for a in actors.get_all_level_actors()
            if isinstance(a, unreal.StaticMeshActor) and str(a.get_folder_path()) == 'Coast/Dock']
    assert dock, 'no dock actors in Coast/Dock'
    for actor in dock:
        actor.static_mesh_component.set_material(0, material)
    report['dock_actors'] = len(dock)
    assert level.save_current_level()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'CoastalMaterialsResult.json').write_text(json.dumps(report, indent=2))
    unreal.log('Coastal materials refreshed')


if __name__ == '__main__':
    main()
