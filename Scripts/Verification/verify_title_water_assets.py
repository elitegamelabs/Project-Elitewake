"""Verify the imported title textures and water-only UI material from Unreal Editor."""
import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
saved = Path(unreal.Paths.project_saved_dir())
paths = {
    'title': '/Game/Elitewake/UI/Title/T_ElitewakeStarterScreen_20261013',
    'mask': '/Game/Elitewake/UI/Title/T_TitleWaterMask_20261013',
    'prompt': '/Game/Elitewake/UI/Title/T_PressAnyKeyToStart_20261013_v2',
    'material': '/Game/Elitewake/UI/Title/M_TitleScreenWater_20261013',
}
assets = {name: unreal.load_asset(path) for name, path in paths.items()}
assert all(assets.values()), {name: bool(value) for name, value in assets.items()}
material = assets['material']
expressions = material.get_editor_property('expressions')
custom = [e.get_editor_property('code') for e in expressions
          if isinstance(e, unreal.MaterialExpressionCustom)]
parameters = [e.get_editor_property('parameter_name') for e in expressions
              if isinstance(e, unreal.MaterialExpressionTextureSampleParameter2D)]
assert material.get_editor_property('material_domain') == unreal.MaterialDomain.MD_UI
assert any('sin(UV.y' in code and 'T *' in code for code in custom), custom
assert any('M > 0.5' in code for code in custom), custom
assert {'TitleImage', 'WaterMask'}.issubset(set(parameters)), parameters
result = {
    'success': True,
    'assets': {key: value.get_path_name() for key, value in assets.items()},
    'material_domain': str(material.get_editor_property('material_domain')),
    'expression_count': len(expressions),
    'parameters': parameters,
    'custom_nodes': custom,
}
(saved / 'TitleWaterAssetCheck.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
unreal.log(f"EW_TITLE_ASSETCHECK success expressions={len(expressions)}")
