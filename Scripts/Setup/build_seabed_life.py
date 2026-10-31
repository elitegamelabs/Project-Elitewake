"""Grow the sea floor's life (world_seabed.py): seagrass meadows and kelp forests swaying in the swell, and corals,
sea fans and sponges in natural colours, round every island and on the seamounts. Safe to run again. Run in the
editor after build_coastal_terrain.py and build_reefs.py, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner, October 17: "dynamic scenery, deeper sand, geography, corals, and aquatic plants" on the bottom of the ocean.
The plants are alive: seagrass and kelp lean and sway back and forth with the swell, each plant at its own phase, the
tips the most, and the kelp's long fronds drift; the corals, fans and sponges stand still and are solid, so a swimmer
bumps into them. Laid as foliage instances, which fade out with distance as the sea's own haze swallows them.

The shapes and colours here are provisional and need the owner visual review defined in CLAUDE.md.
The five glowing major reefs keep their own look (build_reefs.py). Sizes, colours and fade distances are tuning.
Writes Saved/SeabedLifeResult.json.
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
import world_seabed as S  # noqa: E402
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402
from build_reefs import branching, fan, pillar, coral_material  # noqa: E402
from build_coastal_rocks import boulder  # noqa: E402
from build_coastal_flora import Ground  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Seabed'
CORAL_MATERIAL = '/Game/Elitewake/World/Reefs/M_Coral_v1'
# Plants: root and tip colours, and how far the tips sway (cm).
PLANTS = {'Seagrass': ((.02, .06, .015), (.12, .2, .05), 10.0), 'Kelp': ((.06, .045, .012), (.24, .19, .05), 70.0)}
# The natural (not glowing) colours of the corals, fans and sponges.
COLOURS = {'Ochre': (.42, .26, .08), 'Rose': (.55, .17, .17), 'Cream': (.6, .55, .42), 'Olive': (.24, .27, .1),
           'Purple': (.3, .1, .32), 'Yellow': (.6, .45, .06), 'Rust': (.45, .14, .05)}
# Fade start and end per kind (cm).
CULL = {'Seagrass': (3500, 5000), 'Kelp': (9000, 12000), 'Coral': (6000, 8000), 'Fan': (6000, 8000), 'Sponge': (6000, 8000)}
SINK = {'Seagrass': 3.0, 'Kelp': 10.0, 'Coral': 12.0, 'Fan': 8.0, 'Sponge': 8.0}
KELP_HEIGHT = 600.0


def ribbon(b, base, a, tall, lean, width, steps, height):
    """A tapering strip rising from `base` and leaning out toward bearing a; red (tar) is its height over the whole
    plant's (`height`), which is how much it sways."""
    face = a + math.pi / 2
    fx, fy = math.cos(face), math.sin(face)
    prev = None
    for k in range(steps + 1):
        f = k / steps
        out = lean * tall * f * f
        p = (base[0] + out * math.cos(a), base[1] + out * math.sin(a), base[2] + tall * (f - .25 * lean * f * f))
        w = width * (1 - f) ** .6 / 2 + .3
        tar = max(0.0, min(1.0, p[2] / height))
        tone = .3 + .7 * f
        pair = (b.vertex((p[0] - fx * w, p[1] - fy * w, p[2]), tar=tar, tone=tone, uv=(0, f)),
                b.vertex((p[0] + fx * w, p[1] + fy * w, p[2]), tar=tar, tone=tone, uv=(1, f)))
        if prev:
            b.quad(prev[0], prev[1], pair[1], pair[0], (-fy, fx, 0.0))
        prev = pair
    return p


def seagrass(seed):
    """A clump of long, narrow ribbon blades."""
    rng = random.Random(seed)
    b = Builder()
    for _ in range(26):
        a, r = rng.uniform(0, 2 * math.pi), 14 * math.sqrt(rng.random())
        ribbon(b, (r * math.cos(a), r * math.sin(a), -3.0), a + rng.uniform(-.5, .5), rng.uniform(45, 110),
               rng.uniform(.05, .3), rng.uniform(1.0, 1.8), 5, 110.0)
    return b


def kelp(seed):
    """One to three stalks rising toward the light, fronds all the way up."""
    rng = random.Random(seed)
    b = Builder()
    for _ in range(rng.choice((1, 2, 2, 3))):
        sx, sy = rng.uniform(-30, 30), rng.uniform(-30, 30)
        tall = KELP_HEIGHT * rng.uniform(.75, 1.0)
        a0 = rng.uniform(0, math.pi)
        for twist in (0.0, math.pi / 2):
            ribbon(b, (sx, sy, -10.0), a0 + twist, tall, .04, 3.0, 12, KELP_HEIGHT)
        z = 50.0
        while z < tall - 30:
            a = rng.uniform(0, 2 * math.pi)
            ribbon(b, (sx, sy, z), a, rng.uniform(70, 125), rng.uniform(.45, .8), rng.uniform(10, 16), 4, KELP_HEIGHT)
            z += rng.uniform(28, 45)
    return b


def barrel_sponge(seed):
    rng = random.Random(seed)
    b = Builder()
    r = rng.uniform(24, 32)
    b.tube([(0, 0, -10), (0, 0, 15), (0, 0, 45), (0, 0, 70)], lambda q: r * (.8, 1.05, 1.0, .9)[q], sides=14)
    return b


def tube_sponges(seed):
    rng = random.Random(seed)
    b = Builder()
    for _ in range(rng.randint(4, 7)):
        x, y, h, r = rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(40, 95), rng.uniform(5, 8)
        b.tube([(x, y, -8), (x + rng.uniform(-5, 5), y + rng.uniform(-5, 5), h * .55), (x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), h)],
               lambda q, r=r: r * (1.0, .95, 1.1)[q], sides=8)
    return b


def plant_material():
    """Two-sided foliage, root to tip colour, swaying with the swell: back and forth, a slower drift across it, each
    plant at its own phase and the tips the most."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_SeabedPlant_v1')
    material.set_editor_property('two_sided', True)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    root = node(unreal.MaterialExpressionVectorParameter, parameter_name='Root', default_value=unreal.LinearColor(.02, .06, .015, 1))
    tip = node(unreal.MaterialExpressionVectorParameter, parameter_name='Tip', default_value=unreal.LinearColor(.12, .2, .05, 1))
    amount = node(unreal.MaterialExpressionScalarParameter, parameter_name='Sway', default_value=10.0)
    flags = node(unreal.MaterialExpressionVertexColor)
    origin = node(unreal.MaterialExpressionObjectPositionWS)
    colour = custom('float h = frac(sin(dot(floor(O.xy / 53.0), float2(12.9898, 78.233))) * 43758.5453);'
                    ' return lerp(R, U, saturate(F.r * 1.2 + F.b * .2)) * lerp(.8, 1.15, h);',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('R', 'U', 'F', 'O'))
    through = custom('return C * float3(.7, .8, .4);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C',))
    sway = custom('float bend = pow(saturate(F.r), 1.5);'
                  ' float ph = O.x / 730.0 + O.y / 910.0;'
                  ' float surge = sin(T * .75 + ph + P.z / 450.0) * .8 + sin(T * 1.9 + ph * 2.3) * .2;'
                  ' float drift = sin(T * .37 + ph * 1.7 + P.z / 300.0);'
                  ' return float3(.85 * surge, .55 * drift, -abs(surge) * .15) * bend * S;',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('F', 'T', 'P', 'O', 'S'))
    for a, b, pin in ((root, colour, 'R'), (tip, colour, 'U'), (flags, colour, 'F'), (origin, colour, 'O'), (colour, through, 'C'),
                      (flags, sway, 'F'), (node(unreal.MaterialExpressionTime), sway, 'T'),
                      (node(unreal.MaterialExpressionWorldPosition), sway, 'P'), (origin, sway, 'O'), (amount, sway, 'S')):
        assert mel.connect_material_expressions(a, '', b, pin), pin
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(through, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.6), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(sway, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def instance(parent, name, vectors=(), scalars=()):
    mel = unreal.MaterialEditingLibrary
    path = f'{FOLDER}/{name}'
    mi = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, parent)
    for key, value in vectors:
        mel.set_material_instance_vector_parameter_value(mi, key, unreal.LinearColor(*value, 1))
    for key, value in scalars:
        mel.set_material_instance_scalar_parameter_value(mi, key, value)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi


def plant_mesh(b, path, material):
    mesh = write_static_mesh(b, path, [material], 50.0, collision=False, split_angle=180.0)
    setup = mesh.get_editor_property('body_setup')
    if setup:
        # Nothing, not even a precise trace, meets a plant.
        setup.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return mesh


def foliage_type(name, mesh, kind):
    path = f'{FOLDER}/{name}'
    ft = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FOLDER, unreal.FoliageType_InstancedStaticMesh, None)
    ft.set_editor_property('mesh', mesh)
    ft.set_editor_property('cull_distance', unreal.Int32Interval(*CULL[kind]))
    ft.set_editor_property('cast_shadow', kind in ('Coral', 'Sponge', 'Kelp'))
    body = ft.get_editor_property('body_instance')
    try:
        body.set_editor_property('collision_profile_name', 'NoCollision' if kind in ('Seagrass', 'Kelp') else 'BlockAll')
    except Exception:
        pass   # not exposed in every version: the components are set after laying (main)
    # Corals, fans and sponges are solid to a swimmer; plants are not.
    body.set_editor_property('collision_enabled', unreal.CollisionEnabled.NO_COLLISION if kind in ('Seagrass', 'Kelp')
                             else unreal.CollisionEnabled.QUERY_ONLY)
    ft.set_editor_property('body_instance', body)
    assert unreal.EditorAssetLibrary.save_loaded_asset(ft)
    return ft


class MeshGround:
    """A built ground mesh, ray-cast straight down (a seamount's own mesh, off the islands' meshes)."""

    def __init__(self, path):
        asset = unreal.load_asset(path)
        self.mesh = unreal.DynamicMesh()
        unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
            asset, self.mesh, unreal.GeometryScriptCopyMeshFromAssetOptions(), unreal.GeometryScriptMeshReadLOD())
        built = unreal.GeometryScript_MeshSpatial.build_bvh_for_mesh(self.mesh)
        built = built if isinstance(built, tuple) else (built,)
        self.bvh = next(v for v in built if isinstance(v, unreal.GeometryScriptDynamicMeshBVH))

    def __call__(self, x, y):
        out = unreal.GeometryScript_MeshSpatial.find_nearest_ray_intersection_with_mesh(
            self.mesh, self.bvh, unreal.Vector(x, y, 1000), unreal.Vector(0, 0, -1), unreal.GeometryScriptSpatialQueryOptions())
        hit = next((v for v in (out if isinstance(out, tuple) else (out,)) if isinstance(v, unreal.GeometryScriptRayHitResult)), None)
        return hit.get_editor_property('hit_position').z if hit and hit.get_editor_property('hit') else None


def transforms(spots, kind, rng):
    out = []
    for x, y, z, scale, yaw in spots:
        tilt = 3 if kind == 'Kelp' else 8
        out.append(unreal.Transform(unreal.Vector(x, y, z - SINK[kind] * scale),
                                    unreal.Rotator(rng.uniform(-tilt, tilt), rng.uniform(-tilt, tilt), yaw),
                                    unreal.Vector(scale, scale, scale * (1.0 if kind == 'Kelp' else rng.uniform(.85, 1.15)))))
    return out


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert level.load_level(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    plant = plant_material()
    looks = {k: instance(plant, f'MI_{k}_v1', (('Root', root), ('Tip', tip)), (('Sway', sway),)) for k, (root, tip, sway) in PLANTS.items()}
    coral = unreal.load_asset(CORAL_MATERIAL) or coral_material()
    tints = {name: instance(coral, f'MI_SeabedCoral_{name}_v1', (('Colour', c), ('Glow', (0, 0, 0))), (('Strength', 0.0),))
             for name, c in COLOURS.items()}
    shapes = {
        'Seagrass': [plant_mesh(seagrass(500 + k), f'{FOLDER}/SM_Seagrass_{k + 1}_v1', looks['Seagrass']) for k in range(3)],
        'Kelp': [plant_mesh(kelp(520 + k), f'{FOLDER}/SM_Kelp_{k + 1}_v1', looks['Kelp']) for k in range(3)],
        'Coral': [write_static_mesh(branching(540 + k), f'{FOLDER}/SM_SeabedCoralBranching_{k + 1}_v1', [tints[c]], 60.0)
                  for k, c in enumerate(('Ochre', 'Rose', 'Cream'))] +
                 [write_static_mesh(boulder(550 + k, (150.0, 140.0, 140.0), cuts=0), f'{FOLDER}/SM_SeabedCoralMound_{k + 1}_v1', [tints[c]], 60.0)
                  for k, c in enumerate(('Olive', 'Ochre'))] +
                 [write_static_mesh(pillar(560 + k), f'{FOLDER}/SM_SeabedCoralPillar_{k + 1}_v1', [tints[c]], 60.0)
                  for k, c in enumerate(('Cream', 'Rose'))],
        'Fan': [write_static_mesh(fan(570 + k), f'{FOLDER}/SM_SeaFan_{k + 1}_v1', [tints[c]], 60.0)
                for k, c in enumerate(('Purple', 'Rose', 'Yellow'))],
        'Sponge': [write_static_mesh(barrel_sponge(580 + k), f'{FOLDER}/SM_BarrelSponge_{k + 1}_v1', [tints[c]], 60.0)
                   for k, c in enumerate(('Rust', 'Ochre'))] +
                  [write_static_mesh(tube_sponges(590 + k), f'{FOLDER}/SM_TubeSponge_{k + 1}_v1', [tints[c]], 60.0)
                   for k, c in enumerate(('Yellow', 'Purple'))],
    }
    kinds = {kind: [foliage_type(f'FT_Seabed_{kind}_{k + 1}_v1', mesh, kind) for k, mesh in enumerate(meshes)]
             for kind, meshes in shapes.items()}
    for fts in kinds.values():
        for ft in fts:
            unreal.InstancedFoliageActor.remove_all_instances(world, ft)

    def lay(kind, spots, rng):
        placed = transforms(spots, kind, rng)
        rng.shuffle(placed)
        fts = kinds[kind]
        for k, ft in enumerate(fts):
            share = placed[k::len(fts)]
            if share:
                unreal.InstancedFoliageActor.add_instances(world, ft, share)
        return len(placed)

    ground = Ground()
    report = {'islands': {}, 'seamounts': [], 'totals': {}}
    for island in W.ISLANDS:
        rng = random.Random(sum(map(ord, island.key)) * 31)
        counts = {kind: lay(kind, spots, rng) for kind, spots in S.island_life(island, ground).items()}
        report['islands'][island.key] = counts
        for kind, n in counts.items():
            report['totals'][kind] = report['totals'].get(kind, 0) + n
    for n, (mx, my, top, radius) in enumerate(T.SEAMOUNT_SITES):
        region, life = S.seamount_life(n, MeshGround(f'/Game/Elitewake/World/Meshes/Islands/SM_Seamount_{n + 1}_v1'))
        rng = random.Random(77 + n)
        counts = {kind: lay(kind, spots, rng) for kind, spots in life.items()}
        report['seamounts'].append({'centre_m': [round(mx / 100), round(my / 100)], 'top_depth_m': round(top / 100, 1),
                                    'region': region, 'life': counts})
        for kind, c in counts.items():
            report['totals'][kind] = report['totals'].get(kind, 0) + c
    # Foliage keeps its own collision setting per component (the type's profile wins over its enabled flag): plants
    # have none; corals, fans and sponges block, for queries only (a swimmer's sweep and a trace), with no physics.
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
        for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = comp.get_editor_property('static_mesh')
            name = mesh.get_name() if mesh else ''
            if any(k in name for k in ('SM_Seagrass', 'SM_Kelp')):
                comp.set_collision_profile_name('NoCollision')
                comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            elif any(k in name for k in ('SM_SeabedCoral', 'SM_SeaFan', 'SM_BarrelSponge', 'SM_TubeSponge')):
                comp.set_collision_profile_name('BlockAll')
                comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
                report.setdefault('solid_components', 0)
                report['solid_components'] += 1
    assert level.save_current_level()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'SeabedLifeResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Seabed life: {report["totals"]}')


if __name__ == '__main__':
    main()
