"""Creates /Game/Elitewake/UI/Map/M_MapCapture_v1, the UI material that shows the world map's top-down capture (owner, October 22). The scene capture writes albedo with an
alpha of 0, which a plain image would draw as nothing; this material shows the colour at full opacity and lets the map brighten it. Run in the editor:
    UnrealEditor-Cmd.exe EW.uproject -ExecutePythonScript=<this file>"""
import unreal

FOLDER = '/Game/Elitewake/UI/Map'
NAME = 'M_MapCapture_v1'
path = f'{FOLDER}/{NAME}'
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)
mel = unreal.MaterialEditingLibrary
material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
assert material
material.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)

sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
sample.set_editor_property('parameter_name', 'Map')
sample.set_editor_property('texture', unreal.load_asset('/Engine/EngineResources/DefaultTexture'))
bright = mel.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -700, 260)
bright.set_editor_property('parameter_name', 'Brightness')
bright.set_editor_property('default_value', 2.6)
multiply = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -380, 80)
mel.connect_material_expressions(sample, 'RGB', multiply, 'A')
mel.connect_material_expressions(bright, '', multiply, 'B')
mel.connect_material_property(multiply, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
opaque = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -380, 320)
opaque.set_editor_property('r', 1.0)
mel.connect_material_property(opaque, '', unreal.MaterialProperty.MP_OPACITY)
mel.recompile_material(material)
assert unreal.EditorAssetLibrary.save_loaded_asset(material)
unreal.log('Map capture material created')
unreal.SystemLibrary.quit_editor()
