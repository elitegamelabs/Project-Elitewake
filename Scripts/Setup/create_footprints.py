"""Build the footprint decal material (owner, October 26: black footprints that fade on firm ground and stay, six at a time, in
snow, mud and sand). Safe to run again. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
The print itself is drawn in the material (a sole, an arch and a heel as smooth ovals), so there is no texture to import. The
material is a translucent deferred decal with two parameters the game sets per print: Tint (the colour) and Opacity (the fade).
UEWFootprintComponent (Source/EW/World) spawns the decals. The shape's top is the toe; the decal's Z axis points the way the
survivor is walking."""
import unreal

DEST = '/Game/Elitewake/World/Footprints'
NAME = 'M_Footprint_v1'

unreal.EditorAssetLibrary.make_directory(DEST)
mel = unreal.MaterialEditingLibrary
material = unreal.load_asset(f'{DEST}/{NAME}')
if material:
    mel.delete_all_material_expressions(material)
else:
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, DEST, unreal.Material, unreal.MaterialFactoryNew())
material.set_editor_property('material_domain', unreal.MaterialDomain.MD_DEFERRED_DECAL)
material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)


def node(cls, **properties):
    expression = mel.create_material_expression(material, cls)
    for key, value in properties.items():
        expression.set_editor_property(key, value)
    return expression


uv = node(unreal.MaterialExpressionTextureCoordinate)
shape = node(unreal.MaterialExpressionCustom, output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT1, code='''
float2 p = (UV - 0.5) * 2.0;
p.y = -p.y;                                   // up the print is the toe
p.x *= 1.0;
float fore = 1.0 - length((p - float2(0.0, 0.42)) / float2(0.46, 0.52));
float arch = 1.0 - length((p - float2(0.0, -0.05)) / float2(0.30, 0.34));
float heel = 1.0 - length((p - float2(0.0, -0.58)) / float2(0.34, 0.30));
float d = max(max(fore, arch), heel);
return smoothstep(0.0, 0.12, d);
''')
pin = unreal.CustomInput()
pin.set_editor_property('input_name', 'UV')
shape.set_editor_property('inputs', [pin])
assert mel.connect_material_expressions(uv, '', shape, 'UV')
opacity = node(unreal.MaterialExpressionScalarParameter, parameter_name='Opacity', default_value=1.0)
strength = node(unreal.MaterialExpressionConstant, r=.8)
times = node(unreal.MaterialExpressionMultiply)
assert mel.connect_material_expressions(shape, '', times, 'A')
assert mel.connect_material_expressions(opacity, '', times, 'B')
final = node(unreal.MaterialExpressionMultiply)
assert mel.connect_material_expressions(times, '', final, 'A')
assert mel.connect_material_expressions(strength, '', final, 'B')
tint = node(unreal.MaterialExpressionVectorParameter, parameter_name='Tint', default_value=unreal.LinearColor(0, 0, 0, 1))
assert mel.connect_material_property(tint, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
assert mel.connect_material_property(final, '', unreal.MaterialProperty.MP_OPACITY)
mel.recompile_material(material)
assert unreal.EditorAssetLibrary.save_loaded_asset(material)
unreal.log(f'Footprint material built: {DEST}/{NAME}')
