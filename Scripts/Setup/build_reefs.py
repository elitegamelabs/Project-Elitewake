"""Grow the five major reefs (world_reefs.py). Safe to run again. Run in the editor after build_coastal_terrain.py,
outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Canonical world rule: one reef per island, glowing day and night. Four corals are built here: branching staghorn coral,
lumpy brain-like mounds, upright sea fans and clusters of pillar coral; in five glows (cyan, magenta, lime, amber,
violet) whose light breathes slowly, bright enough to find a reef from the surface at night but not to light the
sea. Each coral stands on the sea floor (the island mesh, ray-cast) and stays at least 80 cm under the surface. Corals
are solid, so a swimmer bumps into them rather than through. Colours, glow strength and sizes are tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_terrain as T  # noqa: E402
from world_reefs import REEFS  # noqa: E402
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402
from build_coastal_rocks import boulder  # noqa: E402
from build_coastal_flora import Ground  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Reefs'
LEVEL_FOLDER = 'World/Reefs'
GLOWS = {'Cyan': ((.02, .35, .4), (.1, 1.0, 1.2)), 'Magenta': ((.4, .03, .25), (1.2, .1, .8)),
         'Lime': ((.2, .4, .03), (.6, 1.2, .1)), 'Amber': ((.45, .2, .02), (1.3, .55, .05)),
         'Violet': ((.15, .05, .4), (.45, .15, 1.2))}
GLOW = 2.5            # emissive strength (tuning)
HEIGHT = {'branching': 130.0, 'mound': 70.0, 'fan': 140.0, 'pillar': 160.0}   # at scale 1, cm


def branching(seed):
    """Staghorn: a few trunks that fork twice, tapering to blunt tips."""
    rng = random.Random(seed)
    b = Builder()

    def grow(base, direction, length, radius, depth):
        end = tuple(base[i] + direction[i] * length for i in range(3))
        mid = tuple((base[i] + end[i]) / 2 + rng.uniform(-6, 6) for i in range(3))
        b.tube([base, mid, end], lambda q: radius * (1.0, .85, .7)[q], sides=7)
        if depth < 2:
            for _ in range(2):
                a, up = rng.uniform(0, 2 * math.pi), rng.uniform(.5, .9)
                d = (math.cos(a) * math.sqrt(1 - up * up), math.sin(a) * math.sqrt(1 - up * up), up)
                grow(end, d, length * rng.uniform(.6, .8), radius * .7, depth + 1)
    for _ in range(4):
        a, up = rng.uniform(0, 2 * math.pi), rng.uniform(.55, .85)
        grow((rng.uniform(-10, 10), rng.uniform(-10, 10), -10), (math.cos(a) * math.sqrt(1 - up * up), math.sin(a) * math.sqrt(1 - up * up), up),
             rng.uniform(45, 60), 7.0, 0)
    return b


def fan(seed):
    """A sea fan: a thin, round-topped lattice of branches in one upright plane."""
    rng = random.Random(seed)
    b = Builder()
    for k in range(9):
        a = math.radians(-60 + 120 * k / 8 + rng.uniform(-5, 5))
        length = rng.uniform(100, 140)
        pts = [(0.0, 0.0, -10.0)]
        for f in (.33, .66, 1.0):
            pts.append((math.sin(a) * length * f + rng.uniform(-6, 6), rng.uniform(-3, 3), math.cos(a) * length * f))
        b.tube(pts, lambda q: (5.0, 3.5, 2.5, 1.5)[q], sides=5)
    for z in (40, 75, 105):
        ring = [(math.sin(math.radians(a)) * z * 1.1, 0.0, math.cos(math.radians(a)) * z) for a in range(-60, 61, 15)]
        b.tube(ring, 1.4, sides=4)
    return b


def pillar(seed):
    """Pillar coral: a clump of upright, round-topped columns."""
    rng = random.Random(seed)
    b = Builder()
    for _ in range(7):
        x, y = rng.uniform(-35, 35), rng.uniform(-35, 35)
        h, r = rng.uniform(70, 160), rng.uniform(7, 13)
        b.tube([(x, y, -10), (x + rng.uniform(-4, 4), y + rng.uniform(-4, 4), h * .5), (x, y, h)], lambda q, r=r: r * (1.1, 1.0, .85)[q], sides=9)
    return b


def coral_material():
    """Its colour, and a glow of the same hue that slowly breathes, each coral at its own pace."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Coral_v1')
    base = node(unreal.MaterialExpressionVectorParameter, parameter_name='Colour', default_value=unreal.LinearColor(.1, .3, .3, 1))
    glow = node(unreal.MaterialExpressionVectorParameter, parameter_name='Glow', default_value=unreal.LinearColor(.1, 1, 1, 1))
    strength = node(unreal.MaterialExpressionScalarParameter, parameter_name='Strength', default_value=GLOW)
    shade = custom('float n = frac(sin(dot(floor(P / 9.0), float3(12.9898, 78.233, 37.719))) * 43758.5453);'
                   ' return C * lerp(.75, 1.15, n);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C', 'P'))
    breathe = custom('float h = frac(sin(dot(O.xy, float2(12.9898, 78.233))) * 43758.5453);'
                     ' return G * S * (.65 + .35 * sin(T * (.6 + .5 * h) + h * 6.283));',
                     unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('G', 'S', 'T', 'O'))
    position = node(unreal.MaterialExpressionWorldPosition)
    assert mel.connect_material_expressions(base, '', shade, 'C')
    assert mel.connect_material_expressions(position, '', shade, 'P')
    assert mel.connect_material_expressions(glow, '', breathe, 'G')
    assert mel.connect_material_expressions(strength, '', breathe, 'S')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTime), '', breathe, 'T')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionObjectPositionWS), '', breathe, 'O')
    assert mel.connect_material_property(shade, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(breathe, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.55), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def instances(parent):
    mel = unreal.MaterialEditingLibrary
    assets = unreal.AssetToolsHelpers.get_asset_tools()
    out = []
    for name, (colour, glow) in GLOWS.items():
        path = f'{FOLDER}/MI_Coral_{name}_v1'
        mi = unreal.load_asset(path) or assets.create_asset(f'MI_Coral_{name}_v1', FOLDER, unreal.MaterialInstanceConstant,
                                                            unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, parent)
        mel.set_material_instance_vector_parameter_value(mi, 'Colour', unreal.LinearColor(*colour, 1))
        mel.set_material_instance_vector_parameter_value(mi, 'Glow', unreal.LinearColor(*glow, 1))
        assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
        out.append(mi)
    return out


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()).startswith(LEVEL_FOLDER):
            actors.destroy_actor(actor)
    glows = instances(coral_material())
    first = glows[0]
    shapes = {'branching': [write_static_mesh(branching(10 + k), f'{FOLDER}/SM_CoralBranching_{k + 1}_v1', [first], 60.0) for k in range(3)],
              'mound': [write_static_mesh(boulder(40 + k, (150.0, 140.0, 140.0), cuts=0), f'{FOLDER}/SM_CoralMound_{k + 1}_v1', [first], 60.0) for k in range(2)],
              'fan': [write_static_mesh(fan(60 + k), f'{FOLDER}/SM_CoralFan_{k + 1}_v1', [first], 60.0) for k in range(2)],
              'pillar': [write_static_mesh(pillar(80 + k), f'{FOLDER}/SM_CoralPillar_{k + 1}_v1', [first], 60.0) for k in range(2)]}
    ground = Ground()
    report = {}
    for reef in REEFS:
        made, depths = 0, []
        for n, (x, y, kind, scale, yaw, glow) in enumerate(reef.corals):
            z = ground(x, y)
            if z is None or z > T.SEA - 150:
                continue
            # Never breaking the surface: at least 80 cm of water over the top.
            scale = min(scale, (T.SEA - 80 - z) / HEIGHT[kind])
            if scale < .4:
                continue
            actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z - 8), unreal.Rotator(0, 0, yaw))
            actor.set_actor_label(f'Reef {reef.key}: {kind} {n + 1}')
            actor.set_folder_path(f'{LEVEL_FOLDER}/{reef.key}')
            actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            comp = actor.static_mesh_component
            comp.set_static_mesh(shapes[kind][n % len(shapes[kind])])
            comp.set_material(0, glows[glow])
            made += 1
            depths.append(round((T.SEA - z) / 100, 1))
        report[reef.key] = {'island': reef.island.key, 'centre_m': [round(reef.cx / 100), round(reef.cy / 100)], 'corals': made,
                            'depth_m': [min(depths), max(depths)] if depths else None}
    assert world_map.save_map()
    Path(unreal.Paths.project_saved_dir(), 'ReefsResult.json').write_text(json.dumps({'success': True, 'reefs': report}, indent=2))
    unreal.log(f'Reefs built: {len(report)}')


if __name__ == '__main__':
    main()
