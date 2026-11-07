"""Build the foam wake drawn behind a moving ship. Safe to run again.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

SM_ShipWake_v1 is a flat ribbon on the water, made for the sloop: its narrow end at the stern, widening to three
beams behind it over two ship lengths. AEWShip scales it to each hull and lies it on the sea surface. Its material
draws churned water close behind the stern and the two broken foam lines that spread from it, drifting backward
and fading along the wake, and as strong as the scalar Foam says (0 at rest, 1 at top speed). Sizes are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
LENGTH, STERN_WIDTH, TAIL_WIDTH = 2800.0, 220.0, 760.0   # cm, for the sloop
ROWS, COLUMNS = 24, 8


def trail_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_WakeTrail_v1')
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property('two_sided', True)
    uv = node(unreal.MaterialExpressionTextureCoordinate)
    wp = node(unreal.MaterialExpressionWorldPosition)
    time = node(unreal.MaterialExpressionTime)
    fade = node(unreal.MaterialExpressionPerInstanceCustomData, data_index=0)
    foam = custom("""float2 p = WP.xy / 85.0; float n = 0; float a = .55;
for (int i = 0; i < 4; i++) { n += a * (sin(p.x * 1.7 + sin(p.y * 1.3 + T * .35)) * cos(p.y * 1.9 + sin(p.x * 1.1 - T * .25)) * .5 + .5); p = p * 2.03 + 1.7; a *= .5; }
float across = 1.0 - abs(UV.y * 2.0 - 1.0);
float edge = smoothstep(0.0, .45, across) * smoothstep(0.0, .25, UV.x) * smoothstep(1.0, .75, UV.x);
return saturate((n - .42) * 2.4) * edge * saturate(F) * .85;""", unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('UV', 'WP', 'T', 'F'))
    for src, pin in ((uv, 'UV'), (wp, 'WP'), (time, 'T'), (fade, 'F')):
        assert mel.connect_material_expressions(src, '', foam, pin)
    colour = node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.86, .92, .95, 1))
    rough = node(unreal.MaterialExpressionConstant, r=.7)
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(foam, '', unreal.MaterialProperty.MP_OPACITY)
    material.set_editor_property('used_with_instanced_static_meshes', True)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def wake_mesh():
    b = Builder()
    rows = []
    for i in range(ROWS + 1):
        t = i / ROWS
        half = (STERN_WIDTH + (TAIL_WIDTH - STERN_WIDTH) * t ** .8) * .5
        rows.append([(-LENGTH * t, half * (2 * j / COLUMNS - 1), 0.0) for j in range(COLUMNS + 1)])
    b.grid(rows, lambda i, j: (0, 0, 1), uv_of=lambda i, j, p: (i / ROWS, j / COLUMNS))
    return b


def wake_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_ShipWake_v1')
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property('two_sided', True)
    foam = custom(
        'float along = UV.x;\n'
        'float across = abs(UV.y * 2 - 1);\n'
        '// broken, drifting foam: two layers of crossed ripples\n'
        'float n1 = sin(along * 53 - T * 5 + across * 17) * sin(across * 31 - along * 23 + T * 2);\n'
        'float n2 = sin(along * 131 - T * 7 + across * 71) * sin(across * 97 + along * 67);\n'
        'float noise = saturate(.5 + .35 * n1 + .25 * n2);\n'
        '// two foam lines spreading from the stern, and churned water close behind it\n'
        'float arms = smoothstep(.62, .84, across) * (1 - smoothstep(.86, 1, across));\n'
        'float middle = (1 - smoothstep(0, .45, across)) * (1 - smoothstep(0, .55, along));\n'
        'float shape = max(arms * (.55 + .45 * noise), middle * noise);\n'
        'float fade = smoothstep(0, .05, along) * (1 - along) * (1 - along);\n'
        'return saturate(shape * noise * fade * Foam * .9);',
        unreal.CustomMaterialOutputType.CMOT_FLOAT1, ['UV', 'T', 'Foam'])
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTextureCoordinate), '', foam, 'UV')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTime), '', foam, 'T')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionScalarParameter, parameter_name='Foam', default_value=0.0), '', foam, 'Foam')
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.92, .95, .97, 1)), '',
                                         unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.8), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(foam, '', unreal.MaterialProperty.MP_OPACITY)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    material = wake_material()
    mesh = write_static_mesh(wake_mesh(), f'{FOLDER}/SM_ShipWake_v1', [material], 100.0, collision=False)
    trail = trail_material()
    Path(unreal.Paths.project_saved_dir(), 'ShipWakeResult.json').write_text(json.dumps(
        {'success': True, 'mesh': mesh.get_path_name(), 'trail_material': trail.get_path_name()}))
    unreal.log('Ship wake built')


if __name__ == '__main__':
    main()
