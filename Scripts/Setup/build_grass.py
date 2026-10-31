"""Grow grass you can see as plants on the grassy islands. Safe to run again. Run in the editor after
build_coastal_terrain.py and build_caves.py, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner, October 15 (STARTER_ISLAND_CENTRAL_PLAINS_DIRECTION, REGIONAL_WORLD_AND_3D_ASSET_REQUIREMENTS): the Central
Plains are grassland. Until now the grass was only painted on the ground. This adds clumps of real blades, each a
tapered, curved strip, darker at the root and lighter and yellower at the tip, swaying in the wind, laid as foliage
instances wherever the ground is grassed (world_terrain.cover) and not steep: thick on the Plains islands (the
starter island's included), thinner under the Jungle's trees. Kept off the beach, the spring, the Ports and the
caves. Grass has no collision and fades out past about 65 m (the painted ground carries on beyond). DECIDED (delegated): heights 35-70 cm and densities are
tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from world_landmarks import near_landmark  # noqa: E402
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Grass'
# Per region: clumps per square metre where the ground is fully grassed, and the clump scale range (tuning).
DENSITY = {'Plains': (7.0, (.8, 1.35)), 'Jungle': (1.4, (.8, 2.0))}      # Plains 2.5 on the old islands; the five-island Plains island is mostly open ground and needs about 7 to stay at least 1.5 times as thick as the Jungle
# The Jungle's understory (owner, October 16, BIOME_TERRAIN_FOLIAGE_AND_GLOBAL_SUN: dense bushes, grass of varying
# heights, understory plants and flowers, layered, with navigable paths and performance-aware density): ferns, leafy
# bushes and flowering plants among its grass, per square metre, with their scale ranges (tuning). None of it blocks.
UNDERSTORY = {'Jungle': (('Fern', .15, (.8, 1.35)), ('Bush', .06, (.8, 1.45)), ('Flowers', .04, (.85, 1.25)))}
CLUMPS = 4
CULL = (4500.0, 6500.0)       # fade start and end, cm


def clump(seed):
    """About forty blades from one root, leaning out and curling over at the tips."""
    rng = random.Random(seed)
    b = Builder()
    for _ in range(40):
        a = rng.uniform(0, 2 * math.pi)
        r0 = 22 * math.sqrt(rng.random())
        x0, y0 = r0 * math.cos(a), r0 * math.sin(a)
        tall = rng.uniform(35, 70)
        lean = rng.uniform(.15, .55)
        width = rng.uniform(1.6, 2.6)
        face = a + rng.uniform(-.6, .6) + math.pi / 2
        fx, fy = math.cos(face), math.sin(face)
        steps = 4
        prev = None
        for k in range(steps + 1):
            f = k / steps
            out = lean * tall * f * f
            p = (x0 + out * math.cos(a), y0 + out * math.sin(a), -3 + tall * (f - .25 * lean * f * f))
            w = width * (1 - f) ** .8 / 2
            tone = .35 + .65 * f
            if k < steps:
                pair = (b.vertex((p[0] - fx * w, p[1] - fy * w, p[2]), tar=f, tone=tone, uv=(0, f)),
                        b.vertex((p[0] + fx * w, p[1] + fy * w, p[2]), tar=f, tone=tone, uv=(1, f)))
            else:
                tip = b.vertex(p, tar=1.0, tone=1.0, uv=(.5, 1))
            normal = (-fy, fx, 0.0)
            if prev and k < steps:
                b.quad(prev[0], prev[1], pair[1], pair[0], normal)
            elif prev:
                b.tri(prev[0], prev[1], tip, normal)
            if k < steps:
                prev = pair
    return b


def blade(b, x0, y0, z0, a, tall, lean, width, steps=4, petal=0.0, hue=0.0):
    """One tapered, curving strip from (x0, y0, z0) leaning out toward a: a grass blade, a fern frond or a leaf.
    Red (tar) is how far up it the point is (the material's sway and shading); a petal sets green (iron) and blue
    (its colour)."""
    face = a + math.pi / 2
    fx, fy = math.cos(face), math.sin(face)
    prev = None
    for k in range(steps + 1):
        f = k / steps
        out = lean * tall * f * f
        p = (x0 + out * math.cos(a), y0 + out * math.sin(a), z0 + tall * (f - .25 * lean * f * f))
        w = width * (1 - f) ** .8 / 2
        tone = hue if petal else .35 + .65 * f
        if k < steps:
            pair = (b.vertex((p[0] - fx * w, p[1] - fy * w, p[2]), tar=f, iron=petal, tone=tone, uv=(0, f)),
                    b.vertex((p[0] + fx * w, p[1] + fy * w, p[2]), tar=f, iron=petal, tone=tone, uv=(1, f)))
        else:
            tip = b.vertex(p, tar=1.0, iron=petal, tone=tone if petal else 1.0, uv=(.5, 1))
        normal = (-fy, fx, 0.0)
        if prev and k < steps:
            b.quad(prev[0], prev[1], pair[1], pair[0], normal)
        elif prev:
            b.tri(prev[0], prev[1], tip, normal)
        if k < steps:
            prev = pair
    return p


def fern(seed):
    """A dozen broad fronds arching out and over from one crown, 0.5-1 m long."""
    rng = random.Random(seed)
    b = Builder()
    for n in range(12):
        a = 2 * math.pi * n / 12 + rng.uniform(-.25, .25)
        blade(b, 0, 0, -3, a, rng.uniform(55, 95), rng.uniform(.75, 1.05), rng.uniform(11, 17), steps=6)
    return b


def bush(seed):
    """A leafy shrub about a metre high: short broad leaves over a rounded dome."""
    rng = random.Random(seed)
    b = Builder()
    for _ in range(80):
        a, up = rng.uniform(0, 2 * math.pi), rng.uniform(.1, 1.0)
        r = 55 * math.sqrt(1 - up * up) * rng.uniform(.6, 1.0)
        blade(b, r * math.cos(a), r * math.sin(a), 10 + 80 * up, a + rng.uniform(-.5, .5), rng.uniform(22, 34),
              rng.uniform(.3, .6), rng.uniform(7, 11), steps=3)
    return b


def flowers(seed):
    """A clump of slender stems, each topped by a flower of four petals, all of one colour (blue picks it)."""
    rng = random.Random(seed)
    b = Builder()
    hue = (seed % 4 + .5) / 4
    for _ in range(9):
        a = rng.uniform(0, 2 * math.pi)
        r0 = 14 * math.sqrt(rng.random())
        top = blade(b, r0 * math.cos(a), r0 * math.sin(a), -3, a, rng.uniform(35, 65), rng.uniform(.05, .2), 1.4, steps=3)
        for k in range(4):
            pa = a + k * math.pi / 2 + rng.uniform(-.2, .2)
            blade(b, top[0], top[1], top[2] - 2, pa, 6.0, 2.2, 5.0, steps=2, petal=1.0, hue=hue)
    return b


def understory_material():
    """The grass's material with flowers: green (iron) marks petals, blue picks their colour (red, yellow, white,
    purple); the rest shades and sways as grass."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Understory_v1')
    material.set_editor_property('two_sided', True)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    flags = node(unreal.MaterialExpressionVertexColor)
    origin = node(unreal.MaterialExpressionObjectPositionWS)
    colour = custom('float h = frac(sin(dot(floor(O.xy / 37.0), float2(12.9898, 78.233))) * 43758.5453);'
                    ' float3 root = float3(.018, .04, .01), tip = lerp(float3(.07, .13, .03), float3(.1, .15, .04), h);'
                    ' float3 leaf = lerp(root, tip, saturate(F.r * 1.1)) * lerp(.8, 1.15, frac(h * 5.3));'
                    ' float3 petal = F.b < .25 ? float3(.62, .05, .07) : F.b < .5 ? float3(.85, .62, .05) : F.b < .75 ? float3(.8, .78, .72) : float3(.36, .1, .52);'
                    ' return lerp(leaf, petal, saturate(F.g));',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('F', 'O'))
    through = custom('return C * float3(.6, .75, .35);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C',))
    sway = custom('float bend = F.r * F.r;'
                  ' float gust = sin(T * 1.7 + P.x / 310.0 + P.y / 470.0) * .6 + sin(T * 3.1 + P.y / 130.0) * .25;'
                  ' return float3(.8, .6, 0) * bend * gust * 6.0 + float3(0, 0, -abs(gust) * bend * 1.5);',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('F', 'T', 'P'))
    assert mel.connect_material_expressions(flags, '', colour, 'F')
    assert mel.connect_material_expressions(origin, '', colour, 'O')
    assert mel.connect_material_expressions(colour, '', through, 'C')
    assert mel.connect_material_expressions(flags, '', sway, 'F')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTime), '', sway, 'T')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionWorldPosition), '', sway, 'P')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(through, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.7), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(sway, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def grass_material():
    """Two-sided foliage: dark green at the root to a lighter, drier green at the tip, each clump its own shade;
    the tips sway with the wind, the roots stay put."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Grass_v1')
    material.set_editor_property('two_sided', True)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    flags = node(unreal.MaterialExpressionVertexColor)
    origin = node(unreal.MaterialExpressionObjectPositionWS)
    colour = custom('float h = frac(sin(dot(floor(O.xy / 37.0), float2(12.9898, 78.233))) * 43758.5453);'
                    ' float3 root = float3(.025, .05, .012), tip = lerp(float3(.11, .15, .035), float3(.17, .16, .05), h);'
                    ' return lerp(root, tip, saturate(F.r * 1.1)) * lerp(.8, 1.15, frac(h * 5.3));',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('F', 'O'))
    through = custom('return C * float3(.6, .75, .35);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C',))
    sway = custom('float bend = F.r * F.r;'
                  ' float gust = sin(T * 1.7 + P.x / 310.0 + P.y / 470.0) * .6 + sin(T * 3.1 + P.y / 130.0) * .25;'
                  ' return float3(.8, .6, 0) * bend * gust * 9.0 + float3(0, 0, -abs(gust) * bend * 2.0);',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('F', 'T', 'P'))
    assert mel.connect_material_expressions(flags, '', colour, 'F')
    assert mel.connect_material_expressions(origin, '', colour, 'O')
    assert mel.connect_material_expressions(colour, '', through, 'C')
    assert mel.connect_material_expressions(flags, '', sway, 'F')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTime), '', sway, 'T')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionWorldPosition), '', sway, 'P')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(through, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.7), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(sway, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def foliage_type(name, mesh):
    path = f'{FOLDER}/{name}'
    kind = unreal.load_asset(path)
    if not kind:
        kind = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, unreal.FoliageType_InstancedStaticMesh, None)
    kind.set_editor_property('mesh', mesh)
    kind.set_editor_property('cull_distance', unreal.Int32Interval(int(CULL[0]), int(CULL[1])))
    kind.set_editor_property('cast_shadow', False)
    body = kind.get_editor_property('body_instance')
    body.set_editor_property('collision_enabled', unreal.CollisionEnabled.NO_COLLISION)
    kind.set_editor_property('body_instance', body)
    assert unreal.EditorAssetLibrary.save_loaded_asset(kind)
    return kind


def patchy(x, y):
    """0-1: meadows, thinner patches and bare spots, at two scales."""
    a = math.sin(x / 1300 + 1.7 * math.sin(y / 2100)) * math.sin(y / 1100 + 1.3 * math.sin(x / 1700))
    b = math.sin(x / 290 + y / 410) * math.sin(y / 330 - x / 520)
    return min(1.0, max(0.0, .65 + .5 * a + .25 * b))


def spots(island, rng, density=None, scales=None):
    if density is None:
        density, scales = DENSITY[island.region]
    reach = island.reach()
    area = math.pi * island.rx * island.ry / 1e4
    out = []
    for _ in range(int(area * density * 1.4)):
        x, y = island.cx + rng.uniform(-reach, reach), island.cy + rng.uniform(-reach, reach)
        if island.distance(x, y) > -1300:
            continue                                            # the beach and the grass's edge
        z = T.built_height(x, y)
        g = T.cover(x, y, z)[1]
        if rng.random() > g * patchy(x, y):
            continue
        if W.near_port(x, y, 300) or T.near_cave(x, y, 0) or near_landmark(x, y, 0):
            continue
        if island.key == 'Starter' and math.hypot(x - T.POND[0], y - T.POND[1]) < T.POND_RADIUS + 250:
            continue
        # Not on steep ground (bare earth there, as the terrain paints it).
        e = 150.0
        slope = math.hypot(T.built_height(x + e, y) - T.built_height(x - e, y), T.built_height(x, y + e) - T.built_height(x, y - e)) / (2 * e)
        if slope > .75 or z < T.SEA + 40:
            continue
        s = rng.uniform(*scales)
        out.append(unreal.Transform(unreal.Vector(x, y, z - 2), unreal.Rotator(rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(0, 360)),
                                    unreal.Vector(s, s, s * rng.uniform(.85, 1.15))))
    return out


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert level.load_level(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    material = grass_material()
    kinds = []
    for k in range(CLUMPS):
        mesh = write_static_mesh(clump(400 + k), f'{FOLDER}/SM_GrassClump_{k + 1}_v1', [material], 50.0, collision=False, split_angle=180.0)
        # No simple shapes and complex traces use the simple ones: nothing, not even a precise trace, meets grass.
        setup = mesh.get_editor_property('body_setup')
        if setup:
            setup.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
            assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        kinds.append(foliage_type(f'FT_GrassClump_{k + 1}_v1', mesh))
    for kind in kinds:
        unreal.InstancedFoliageActor.remove_all_instances(world, kind)
    report, total = {}, 0
    for island in W.ISLANDS:
        if island.region not in DENSITY:
            continue
        rng = random.Random(sum(map(ord, island.key)) * 6151)
        placed = spots(island, rng)
        for k, kind in enumerate(kinds):
            share = placed[k::CLUMPS]
            if share:
                unreal.InstancedFoliageActor.add_instances(world, kind, share)
        report[island.key] = len(placed)
        total += len(placed)
    # The Jungle's understory: three looks of each plant, laid like the grass.
    under = understory_material()
    makers = {'Fern': fern, 'Bush': bush, 'Flowers': flowers}
    under_report = {}
    for region, plants in UNDERSTORY.items():
        for name, density, scales in plants:
            looks = []
            for k in range(3 if name != 'Flowers' else 4):
                mesh = write_static_mesh(makers[name](700 + 10 * len(name) + k), f'{FOLDER}/SM_{name}_{k + 1}_v1', [under], 50.0,
                                         collision=False, split_angle=180.0)
                setup = mesh.get_editor_property('body_setup')
                if setup:
                    setup.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
                    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
                looks.append(foliage_type(f'FT_{name}_{k + 1}_v1', mesh))
            for kind in looks:
                unreal.InstancedFoliageActor.remove_all_instances(world, kind)
            for island in W.ISLANDS:
                if island.region != region:
                    continue
                rng = random.Random(sum(map(ord, island.key + name)) * 7919)
                placed = spots(island, rng, density, scales)
                for k, kind in enumerate(looks):
                    share = placed[k::len(looks)]
                    if share:
                        unreal.InstancedFoliageActor.add_instances(world, kind, share)
                under_report.setdefault(name, {})[island.key] = len(placed)
                total += len(placed)
    report['understory'] = under_report
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
        for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = comp.get_editor_property('static_mesh')
            if mesh and any(k in mesh.get_name() for k in ('SM_GrassClump', 'SM_Fern', 'SM_Bush', 'SM_Flowers')):
                comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'GrassResult.json').write_text(json.dumps({'success': True, 'clumps': report, 'total': total}, indent=2))
    unreal.log(f'Grass clumps: {total}')


if __name__ == '__main__':
    main()
