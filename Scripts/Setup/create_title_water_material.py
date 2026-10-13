"""Build the UI material that moves sampled title-screen pixels only inside the water mask.

Run in the Unreal Editor after importing the owner title image and water mask.
"""
import unreal

DEST = '/Game/Elitewake/UI/Title'
IMAGE = f'{DEST}/T_ElitewakeStarterScreen_20261013'
MASK = f'{DEST}/T_TitleWaterMask_20261013'
MATERIAL = f'{DEST}/M_TitleScreenWater_20261013'

image = unreal.load_asset(IMAGE)
mask = unreal.load_asset(MASK)
if not image or not mask:
    raise RuntimeError('Import the starter image and water mask before creating the material')

assets = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
material = unreal.load_asset(MATERIAL)
if material:
    mel.delete_all_material_expressions(material)
else:
    material = assets.create_asset('M_TitleScreenWater_20261013', DEST, unreal.Material, unreal.MaterialFactoryNew())
material.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)


def node(cls, **properties):
    expression = mel.create_material_expression(material, cls)
    for name, value in properties.items():
        expression.set_editor_property(name, value)
    return expression


def connect(source, target, input_name, output=''):
    available = mel.get_material_expression_input_names(target)
    assert input_name in available, (target.get_name(), input_name, available)
    assert mel.connect_material_expressions(source, output, target, input_name), (target.get_name(), input_name)


def constant(value):
    return node(unreal.MaterialExpressionConstant, r=float(value))


def custom_vector2():
    expression = node(unreal.MaterialExpressionCustom,
        code='''
float foreground = smoothstep(0.56, 0.95, UV.y);
float shore = (1.0 - smoothstep(0.20, 0.57, UV.x)) * foreground;
float surge = pow(0.5 + 0.5 * sin(T * 1.45 - UV.y * 13.0), 4.0);
float2 swell = float2(sin(UV.y * 65.0 + T * 1.25), cos(UV.x * 42.0 - T * 0.9));
float2 detail = float2(sin(UV.x * 135.0 + UV.y * 90.0 - T * 2.7), sin(UV.y * 115.0 + T * 2.2));
float2 offset = swell * lerp(0.0005, 0.0020, foreground) + detail * foreground * 0.00045;
offset += float2(-0.0020, -0.0035) * shore * surge;
// The two waterfalls flow downward; the mask keeps their surrounding cliffs still.
float falls = (1.0 - smoothstep(0.17, 0.19, UV.x)) * (1.0 - smoothstep(0.53, 0.58, UV.y));
offset.y -= falls * (0.0020 + 0.0010 * sin(T * 3.0 + UV.y * 75.0));
return clamp(UV + offset, 0.001, 0.999);
''',
        output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    pins = []
    for name in ('UV', 'T'):
        pin = unreal.CustomInput()
        pin.set_editor_property('input_name', name)
        pins.append(pin)
    expression.set_editor_property('inputs', pins)
    return expression


uv = node(unreal.MaterialExpressionTextureCoordinate)
clock = node(unreal.MaterialExpressionTime)
displaced_uv = custom_vector2()
connect(uv, displaced_uv, 'UV')
connect(clock, displaced_uv, 'T')

original = node(unreal.MaterialExpressionTextureSampleParameter2D, texture=image, parameter_name='TitleImage')
moving = node(unreal.MaterialExpressionTextureSampleParameter2D, texture=image, parameter_name='TitleImage')
mask_sample = node(unreal.MaterialExpressionTextureSampleParameter2D, texture=mask, parameter_name='WaterMask')
connect(uv, original, 'UVs')
connect(displaced_uv, moving, 'UVs')
connect(uv, mask_sample, 'UVs')

# The generated mask uses near-black for scenery and white for water. Threshold it so
# anti-aliased silhouettes around the boat and trees stay completely still.
threshold = node(unreal.MaterialExpressionCustom,
    code='return M > 0.5 ? 1.0 : 0.0;',
    output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT1)
mask_pin = unreal.CustomInput()
mask_pin.set_editor_property('input_name', 'M')
threshold.set_editor_property('inputs', [mask_pin])
connect(mask_sample, threshold, 'M', 'R')

# Reject displaced samples that cross onto a rock, dock, boat or survivor.
moving_mask = node(unreal.MaterialExpressionTextureSampleParameter2D, texture=mask, parameter_name='WaterMask')
connect(displaced_uv, moving_mask, 'UVs')
safe_mask = node(unreal.MaterialExpressionMultiply)
connect(threshold, safe_mask, 'A')
connect(moving_mask, safe_mask, 'B', 'R')

foam = node(unreal.MaterialExpressionCustom, code='''
float shore = (1.0 - smoothstep(0.20, 0.57, UV.x)) * smoothstep(0.56, 0.93, UV.y);
float impact = pow(0.5 + 0.5 * sin(T * 1.45 - UV.y * 13.0), 4.0);
float brightFoam = smoothstep(0.48, 0.85, min(C.r, min(C.g, C.b)));
return saturate(C + brightFoam * shore * impact * float3(0.10, 0.115, 0.12));
''', output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3)
foam_pins = []
for name in ('C', 'UV', 'T'):
    pin = unreal.CustomInput()
    pin.set_editor_property('input_name', name)
    foam_pins.append(pin)
foam.set_editor_property('inputs', foam_pins)
connect(moving, foam, 'C', 'RGB')
connect(uv, foam, 'UV')
connect(clock, foam, 'T')

blend = node(unreal.MaterialExpressionLinearInterpolate)
connect(original, blend, 'A', 'RGB')
connect(foam, blend, 'B')
connect(safe_mask, blend, 'Alpha')
assert mel.connect_material_property(blend, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(material)
assert unreal.EditorAssetLibrary.save_loaded_asset(material)
unreal.log(f'EW_TITLE_WATER created {MATERIAL}; only white mask pixels are UV-animated')
