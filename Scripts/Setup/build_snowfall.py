"""Make the falling snow's flake field and material (used by Source/EW/World/EWSnowfall.*). Safe to run again. Run
in the editor outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Twelve thousand small flakes scattered through a 30 x 30 x 15 m box (about one in every cubic metre). Each flake's corners sit together at its centre
and carry its place in the box in their vertex colour; the material opens them into a soft disc facing the camera
and moves the whole flake: down at about a metre a second, drifting
with a slow sway, each at its own pace, and wrapped round the box's centre (the camera) so the snow is always
there however far the survivor walks. Lit like everything else, so the snow dims at night. Sizes and speeds tuning.
"""
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/World/Weather'
BOX = (3000.0, 3000.0, 1500.0)
FLAKES = 12000
SIZE = 3.0          # half a flake's width, cm


def field():
    """Every flake is four corners at its centre; the material spreads them into a small disc facing the camera."""
    rng = random.Random(1201)
    b = Builder()
    for _ in range(FLAKES):
        c = [rng.random() for _ in range(3)]
        centre = tuple((c[k] - .5) * BOX[k] for k in range(3))
        # A hair apart (not one point), or the mesh build would throw the triangles away as degenerate.
        ids = [b.vertex((centre[0] + .1 * (u - .5), centre[1] + .1 * (v - .5), centre[2]), tar=c[0], iron=c[1], tone=c[2], uv=(u, v))
               for u, v in ((0, 0), (1, 0), (1, 1), (0, 1))]
        b.tris += [(ids[0], ids[1], ids[2]), (ids[0], ids[2], ids[3])]
        b.slots += [0, 0]
    return b


def snow_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Snowfall_v1')
    material.set_editor_property('two_sided', True)
    # Translucent: soft flakes, and no motion smear when a flake wraps round from the bottom of the box to the top.
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    flags = node(unreal.MaterialExpressionVertexColor)
    fall = custom('float3 B = float3(3000, 3000, 1500);'
                  ' float3 old = O + (C - .5) * B;'
                  ' float h = frac(sin(dot(C, float3(12.9898, 78.233, 37.719))) * 43758.5453);'
                  ' float3 w = C * B + float3(sin(T * .7 + h * 6.283) * 60 + T * 40, cos(T * .5 + h * 6.283) * 60 + T * 15, -T * (90 + 60 * h));'
                  ' float3 base = O - .5 * B;'
                  ' return base + frac((w - base) / B) * B - old;',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C', 'O', 'T'))
    assert mel.connect_material_expressions(flags, '', fall, 'C')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionObjectPositionWS), '', fall, 'O')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTime), '', fall, 'T')
    # Spread the corners into a disc facing the camera.
    uv = node(unreal.MaterialExpressionTextureCoordinate)
    axes = []
    for axis in ((1, 0, 0), (0, 1, 0)):
        to_world = node(unreal.MaterialExpressionTransform, transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_VIEW,
                        transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
        assert mel.connect_material_expressions(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(*axis, 1)), '', to_world, '')
        axes.append(to_world)
    spread = custom(f'return F + ((UV.x - .5) * R + (UV.y - .5) * U) * {2 * SIZE:.1f};', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('F', 'UV', 'R', 'U'))
    assert mel.connect_material_expressions(fall, '', spread, 'F')
    assert mel.connect_material_expressions(uv, '', spread, 'UV')
    assert mel.connect_material_expressions(axes[0], '', spread, 'R')
    assert mel.connect_material_expressions(axes[1], '', spread, 'U')
    soft = custom('return saturate(1 - length(UV - .5) * 2) * .95;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('UV',))
    assert mel.connect_material_expressions(uv, '', soft, 'UV')
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.92, .94, .97, 1)), '',
                                         unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.85), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(soft, '', unreal.MaterialProperty.MP_OPACITY)
    assert mel.connect_material_property(spread, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def main():
    material = snow_material()
    write_static_mesh(field(), f'{FOLDER}/SM_Snowfall_v1', [material], 10.0, collision=False, split_angle=180.0)
    unreal.log('Snowfall built')


if __name__ == '__main__':
    main()
