"""Build the highlight a placeable is drawn in before it is placed. Safe to run again. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner, October 17: placeable items show a blue highlight where they can be placed, red where they cannot, and look
normal once placed (UEWPlacementPreviewComponent sets the colour). A see-through glow, brighter at its silhouette's
edges so the shape reads against anything behind it, unlit so it shows the same by day and night. Amounts tuning.
"""
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import material_builder  # noqa: E402

PATH = '/Game/Elitewake/UI/M_PlacementGhost_v1'


def main():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(PATH)
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('two_sided', True)
    colour = node(unreal.MaterialExpressionVectorParameter, parameter_name='Colour', default_value=unreal.LinearColor(.12, .45, 1.0, 1.0))
    edge = node(unreal.MaterialExpressionFresnel, exponent=2.5, base_reflect_fraction=0.0)
    glow = custom('return C * (0.6 + E * 3.0);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C', 'E'))
    seen = custom('return saturate(0.22 + E * 0.6);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('E',))
    assert mel.connect_material_expressions(colour, '', glow, 'C')
    assert mel.connect_material_expressions(edge, '', glow, 'E')
    assert mel.connect_material_expressions(edge, '', seen, 'E')
    assert mel.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert mel.connect_material_property(seen, '', unreal.MaterialProperty.MP_OPACITY)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.log('Placement ghost built')


if __name__ == '__main__':
    main()
