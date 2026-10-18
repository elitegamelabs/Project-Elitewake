"""Build the plain white flag: its cloth, the material that makes it fly and wear, and its test item. Safe to run again.
Run in the editor, outside Play, before the hull scripts (they fly it at their staffs):
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner, October 17: a crafted flag is plain clean white, with no emblem or skin options yet (future skins must not
change its durability); flags flutter in the wind, and weather, fray and tear progressively only when damaged in
combat, never from storms; they are not repaired, and destroyed fabric disappears while the pole remains.

The flag streams out from its staff along +X (AEWShip::ShowFlags turns it downwind of the wind felt aboard) and ripples
in a wave running out to the fly, faster and fuller in a stronger wind (custom primitive data 1), drooping when the
wind is light. Its wear (custom primitive data 0, AEWShip::GetFlagWear) greys and stains the cloth, frays the fly end
ragged and opens holes, more of each as it wears. A test item until the owner sets the recipe (open question 1).
Sizes, colours and amounts are tuning.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships/Flags'
ITEMS = '/Game/Elitewake/Items/Testing'
FLY, DROP = 150.0, 100.0      # the flag's length out from the staff and its depth, cm
STAFF_GAP = 4.0               # its hoist stands this far off the staff's axis


def flag_cloth(cols=16, rows=10):
    """A flat sheet hanging from its head at the origin, out along +X and down -Z. Red is how far out to the fly
    (how far it ripples), green how far down."""
    b = Builder()
    grid = [[b.vertex((STAFF_GAP + FLY * i / cols, 0.0, -DROP * j / rows), tar=i / cols, iron=j / rows, tone=.5, uv=(i / cols, j / rows))
             for i in range(cols + 1)] for j in range(rows + 1)]
    for j in range(rows):
        for i in range(cols):
            b.quad(grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i], (0.0, 1.0, 0.0))
    return b


def flag_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Flag_v1')
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    material.set_editor_property('two_sided', True)
    wear = node(unreal.MaterialExpressionScalarParameter, parameter_name='Wear', default_value=0.0,
                use_custom_primitive_data=True, primitive_data_index=0)
    flutter = node(unreal.MaterialExpressionScalarParameter, parameter_name='Flutter', default_value=0.8,
                   use_custom_primitive_data=True, primitive_data_index=1)
    flags = node(unreal.MaterialExpressionVertexColor)
    uv = node(unreal.MaterialExpressionTextureCoordinate)
    time = node(unreal.MaterialExpressionTime)
    noise = ('float h(float2 c) { return frac(sin(dot(c, float2(12.9898, 78.233))) * 43758.5453); }'
             ' float n2(float2 q) { float2 i = floor(q), f = frac(q); f = f * f * (3 - 2 * f);'
             ' return lerp(lerp(h(i), h(i + float2(1, 0)), f.x), lerp(h(i + float2(0, 1)), h(i + float2(1, 1)), f.x), f.y); }')
    # Clean white cloth with a fine weave; wear greys it toward powder-smoke grime, stained in blotches.
    colour = custom('struct G { ' + noise + ' }; G g;'
                    ' float weave = .94 + .06 * sin(U.x * 900.0) * sin(U.y * 600.0);'
                    ' float3 c = float3(.84, .83, .8) * weave;'
                    ' float stain = saturate(g.n2(U * float2(6, 4)) * 1.4 - .3) * W;'
                    ' c = lerp(c, float3(.5, .46, .4), saturate(W * .55 + stain * .6));'
                    ' return lerp(c, float3(.12, .1, .08), saturate((W - .5) * stain * 1.5));',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('U', 'W'))
    # Wear opens holes and frays the fly end ragged; none at all on a new flag.
    mask = custom('struct G { ' + noise + ' }; G g;'
                  ' if (W <= 0.001) return 1.0;'
                  ' float holes = g.n2(U * float2(7, 5)) * .75 + g.n2(U * float2(23, 17)) * .25;'
                  ' float cut = step(holes, W * .45 - .05);'
                  ' float ragged = U.x - (1.0 - W * .4 * (.55 + .9 * g.n2(float2(U.y * 14.0, 3.0))));'
                  ' float slit = step(.985 - W * .05, frac(U.y * 6.0 + g.n2(U * 9.0) * .4)) * step(1.0 - W * .7, U.x);'
                  ' return 1.0 - saturate(cut + step(0.0, ragged) + slit);',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('U', 'W'))
    # A wave running out from the staff to the fly, fuller toward the fly; in a light wind the cloth droops.
    wave = custom('float s = V.r, t = V.g;'
                  ' float run = sin(s * 8.0 - T * (5.0 + 7.0 * F) + t * 1.2) * (.65 + .35 * sin(T * 1.9 + s * 2.5));'
                  ' float droop = saturate(1.0 - F) * s * s * 45.0;'
                  ' return float3(-abs(run) * s * 6.0, run * s * (5.0 + 12.0 * F), -droop);',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('V', 'T', 'F'))
    to_world = node(unreal.MaterialExpressionTransform,
                    transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
                    transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    for a, b, pin in ((uv, colour, 'U'), (wear, colour, 'W'), (uv, mask, 'U'), (wear, mask, 'W'),
                      (flags, wave, 'V'), (time, wave, 'T'), (flutter, wave, 'F')):
        assert mel.connect_material_expressions(a, '', b, pin), pin
    assert mel.connect_material_expressions(wave, '', to_world, '')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(mask, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    assert mel.connect_material_property(to_world, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.85), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    mesh = write_static_mesh(flag_cloth(), f'{FOLDER}/SM_FlagWhite_v1', [flag_material()], FLY, collision=False, split_angle=180.0)
    path = f'{ITEMS}/DA_TestFlagWhite'
    item = unreal.load_asset(path)
    if not item:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
        item = unreal.AssetToolsHelpers.get_asset_tools().create_asset('DA_TestFlagWhite', ITEMS, unreal.EWItemDefinition, factory)
    item.set_editor_property('item_id', 'Test.FlagWhite')
    item.set_editor_property('display_name', 'Plain White Flag')
    item.set_editor_property('category', unreal.EWItemCategory.MISCELLANEOUS)
    item.set_editor_property('max_stack_size', 5)
    item.set_editor_property('unit_weight', 1.0)
    item.set_editor_property('fitting_mount_type', unreal.EWShipMountType.FLAG)
    item.set_editor_property('fitting_mesh', mesh)
    item.set_editor_property('fitting_mesh_transform', unreal.Transform())
    item.set_editor_property('description', 'A plain clean white flag for a ship\'s staff. Test fixture: weight is tuning; recipe and cost pending.')
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    Path(unreal.Paths.project_saved_dir(), 'FlagsResult.json').write_text(json.dumps({'success': True, 'mesh': mesh.get_path_name(), 'item': path}, indent=2))
    unreal.log('Flag built')


if __name__ == '__main__':
    main()
