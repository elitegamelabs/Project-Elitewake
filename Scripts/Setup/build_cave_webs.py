"""Cobwebs in the caves (owner, October 15 night: webs you can walk through that fall apart, only for show).
Safe to run again; run after build_caves.py whenever the caves move:
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>

Builds the web (SM_Cobweb_v1: spokes and a sagging spiral, 2 m across, facing +X, its middle at the origin), the
strands a torn web falls in (SM_CobwebShred_v1), their pale translucent material, and DA_CaveWebs: where each web
hangs, from the caves' own layout (world_terrain.CAVES). The map is not touched: AEWCobweb's subsystem hangs the
webs on every machine when play begins. DECIDED (delegated, tuning): two webs across each cave's passage, which a
survivor walking in tears; three in the chamber's upper corners, out of reach, left whole.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_terrain as T  # noqa: E402
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/World/Caves/Webs'
MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
RADIUS = 100.0       # the web mesh's radius at scale 1, cm
STRAND = 0.45        # a strand's width at scale 1, cm


def strand(b, p0, p1, tone):
    """A thread from p0 to p1 in the web's plane (y, z), a flat ribbon facing +X."""
    dy, dz = p1[1] - p0[1], p1[2] - p0[2]
    length = math.hypot(dy, dz) or 1.0
    ny, nz = -dz / length * STRAND / 2, dy / length * STRAND / 2
    ids = [b.vertex((p[0], p[1] + sy * ny, p[2] + sy * nz), tone=tone) for p, sy in ((p0, -1), (p0, 1), (p1, 1), (p1, -1))]
    b.quad(*ids, (1.0, 0.0, 0.0))


def web_mesh(seed=7):
    rng = random.Random(seed)
    b = Builder()
    spokes = 14
    angles = [2 * math.pi * k / spokes + rng.uniform(-.12, .12) for k in range(spokes)]
    reach = [RADIUS * rng.uniform(.92, 1.08) for _ in range(spokes)]
    point = lambda k, r: (0.0, r * math.cos(angles[k]), r * math.sin(angles[k]))   # noqa: E731
    for k in range(spokes):
        strand(b, (0.0, 0.0, 0.0), point(k, reach[k] * 1.12), rng.uniform(.6, 1.0))   # anchors run past the spiral
    rings = 9
    for ring in range(1, rings + 1):
        f = (ring / rings) ** .85
        for k in range(spokes):
            if rng.random() < .08:
                continue   # an old web has gaps
            k2 = (k + 1) % spokes
            a, c = point(k, reach[k] * f), point(k2, reach[k2] * f)
            sag = .9   # each thread between spokes sags toward the middle
            mid = (0.0, (a[1] + c[1]) / 2 * sag, (a[2] + c[2]) / 2 * sag)
            tone = rng.uniform(.55, 1.0)
            strand(b, a, mid, tone)
            strand(b, mid, c, tone)
    return b


def shred_mesh(seed=11):
    """A few loose threads hanging from a short broken edge, about 40 cm long."""
    rng = random.Random(seed)
    b = Builder()
    for k in range(5):
        y = rng.uniform(-15, 15)
        points = [(0.0, y, 0.0)]
        for n in range(1, 6):
            points.append((0.0, y + rng.uniform(-3, 3) + n * rng.uniform(-1.5, 1.5), -n * rng.uniform(5, 9)))
        for p0, p1 in zip(points, points[1:]):
            strand(b, p0, p1, rng.uniform(.6, 1.0))
    return b


def web_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Cobweb_v1')
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property('two_sided', True)
    flags = node(unreal.MaterialExpressionVertexColor)
    colour = custom('return lerp(0.5, 0.9, Flags.b) * float3(0.93, 0.93, 0.9);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('Flags',))
    glow = custom('return lerp(0.5, 0.9, Flags.b) * float3(0.035, 0.035, 0.035);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('Flags',))
    opacity = node(unreal.MaterialExpressionConstant, r=0.55)
    rough = node(unreal.MaterialExpressionConstant, r=0.6)
    for n in (colour, glow):
        assert mel.connect_material_expressions(flags, '', n, 'Flags')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert mel.connect_material_property(opacity, '', unreal.MaterialProperty.MP_OPACITY)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def placements():
    """(x, y, z, yaw, pitch, scale y, scale z, where) for every web in every cave."""
    webs = []
    for key, cave in T.CAVES.items():
        # Across the passage, wall to wall and floor to above head height: walking in tears them.
        for f in (.35, .75):
            u = cave.length * f
            v = cave.centre_v(u)
            x, y = cave.world(u, v)
            slope = cave.bend * math.pi / cave.length * math.cos(math.pi * f)
            yaw = math.degrees(cave.heading + math.atan2(slope, 1.0))
            webs.append((x, y, cave.floor + 175.0, yaw, 0.0, (T.TUNNEL[0] - 20) / RADIUS, 1.6, f'{key} passage'))
        # High in the chamber's back corners, leaning into the rock, facing the way in.
        cu, cv, cz = cave.chamber
        for side in (-.5, 0.0, .5):
            u, v = cave.chamber_u + .72 * cu, side * cv
            x, y = cave.world(u, v)
            q = math.hypot(.72, side)
            top = cave.chamber_z + cz * math.sqrt(max(0.0, 1 - q * q))
            mx, my = cave.world(cave.chamber_u, 0.0)
            yaw = math.degrees(math.atan2(my - y, mx - x))
            webs.append((x, y, cave.floor + top - 90.0, yaw, -35.0, .85, .85, f'{key} chamber'))
    return webs


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    material = web_material()
    write_static_mesh(web_mesh(), f'{FOLDER}/SM_Cobweb_v1', [material], 100.0, collision=False)
    write_static_mesh(shred_mesh(), f'{FOLDER}/SM_CobwebShred_v1', [material], 100.0, collision=False)
    path = f'{FOLDER}/DA_CaveWebs'
    data = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'DA_CaveWebs', FOLDER, unreal.EWCaveWebSet, unreal.DataAssetFactory())
    webs = placements()
    data.set_editor_property('map', unreal.load_asset(MAP))
    data.set_editor_property('webs', [unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=pitch, yaw=yaw),
                                                       unreal.Vector(1.0, sy, sz)) for x, y, z, yaw, pitch, sy, sz, _ in webs])
    assert unreal.EditorAssetLibrary.save_loaded_asset(data)
    Path(unreal.Paths.project_saved_dir(), 'CaveWebsResult.json').write_text(json.dumps(
        {'success': True, 'caves': len(T.CAVES), 'webs': len(webs),
         'where': [{'cave': w, 'at': [round(x), round(y), round(z)]} for x, y, z, _, _, _, _, w in webs]}, indent=2))
    unreal.log(f'Cave webs: {len(webs)} in {len(T.CAVES)} caves')


if __name__ == '__main__':
    main()
