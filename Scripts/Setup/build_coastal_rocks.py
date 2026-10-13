"""Set boulders on the coastal map that give Stone to a pickaxe. Safe to run again.
Run in the editor after build_coastal_flora.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Four boulder shapes built in the editor: a rounded stone, lumpy and flattened, its crevices shaded darker, in a
weathered grey stone material with lichen on its upper faces. Run after build_coastal_flora.py; rocks keep clear of its palms and plants. Rocks sit bedded in the sand, mostly on the
higher ground inland and along the beach heads of the island and the islet, clear of the palms, the spawn, the
dock and the spring. Each is a mining node (the existing test yield: 12 Stone, 3 a strike) and is solid enough to
climb onto.
Sizes and counts are tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402
from build_coastal_flora import FLORA_FOLDER, KEEP_CLEAR, MAP, SEA, Ground  # noqa: E402

FOLDER = '/Game/Elitewake/World/Rocks'
STONE = '/Game/Elitewake/Items/Testing/DA_TestStone'
SHAPES = [dict(seed=1, size=(270.0, 220.0, 170.0)), dict(seed=2, size=(210.0, 180.0, 150.0)),
          dict(seed=3, size=(340.0, 250.0, 190.0)), dict(seed=4, size=(160.0, 150.0, 125.0))]
AREAS = [((-5900.0, 4300.0), (-4200.0, 4000.0), 16), ((7700.0, 11300.0), (1150.0, 4050.0), 5)]


# ---- Shape -------------------------------------------------------------------------------------------------

def lattice(seed):
    rng = random.Random(seed)
    table = [rng.uniform(-1, 1) for _ in range(512)]

    def at(i, j, k):
        return table[(i * 73 + j * 179 + k * 283) % 512]

    def noise(x, y, z):
        """Smooth value noise in about -1..1."""
        i, j, k = math.floor(x), math.floor(y), math.floor(z)
        fx, fy, fz = x - i, y - j, z - k
        sx, sy, sz = (f * f * (3 - 2 * f) for f in (fx, fy, fz))
        value = 0.0
        for di in (0, 1):
            for dj in (0, 1):
                for dk in (0, 1):
                    w = (sx if di else 1 - sx) * (sy if dj else 1 - sy) * (sz if dk else 1 - sz)
                    value += w * at(i + di, j + dj, k + dk)
        return value
    return noise


def icosphere(levels):
    t = (1 + 5 ** 0.5) / 2
    verts = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
             (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    verts = [tuple(c / math.sqrt(sum(v * v for v in p)) for c in p) for p in verts]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
             (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(levels):
        cache, out = {}, []

        def middle(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                m = tuple((verts[a][i] + verts[b][i]) / 2 for i in range(3))
                n = math.sqrt(sum(c * c for c in m))
                verts.append(tuple(c / n for c in m))
                cache[key] = len(verts) - 1
            return cache[key]
        for a, b, c in faces:
            ab, bc, ca = middle(a, b), middle(b, c), middle(c, a)
            out += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = out
    return verts, faces


def boulder(seed, size):
    """A boulder in its own space, its widest part at the origin's height so half of it sinks into the ground."""
    noise = lattice(seed)
    verts, faces = icosphere(4)
    sx, sy, sz = (s / 2 for s in size)
    b = Builder()
    shaped, depth = [], []
    for p in verts:
        # Broad lumps, then sharp ridges (folded noise) so the stone reads fractured rather than smooth.
        bump = (0.22 * noise(p[0] * 1.6 + seed, p[1] * 1.6, p[2] * 1.6)
                + 0.12 * (0.5 - abs(noise(p[0] * 3.2, p[1] * 3.2 + seed, p[2] * 3.2)))
                + 0.05 * noise(p[0] * 8.0 + seed, p[1] * 8.0, p[2] * 8.0))
        r = 1.0 + bump
        z = p[2] * r
        if z < -0.35:  # flatten the buried underside
            z = -0.35 - (z + 0.35) * 0.2
        shaped.append((p[0] * r * sx, p[1] * r * sy, z * sz))
        depth.append(bump)
    for k, p in enumerate(shaped):
        # Crevices (where the surface dips in) read darker, ridges lighter.
        b.vertex(p, 0.0, 0.0, min(1.0, max(0.0, 0.5 + depth[k] * 2.2)))
    for a, c, e in faces:
        centre = tuple((shaped[a][i] + shaped[c][i] + shaped[e][i]) / 3 for i in range(3))
        b.tri(a, c, e, centre)
    return b


def rock_material():
    """Weathered dark grey stone: mottled at two scales by world-space noise, darkened in the shape's crevices,
    with pale salt and lichen on top."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_CoastalRock_v1')
    position = node(unreal.MaterialExpressionWorldPosition)
    normal = node(unreal.MaterialExpressionVertexNormalWS)
    flags = node(unreal.MaterialExpressionVertexColor)
    colour = custom(
        'float n = 0, fine = 0;'
        ' [unroll] for (int s = 0; s < 2; s++) {'
        '  float3 q = P / (s == 0 ? 45.0 : 7.0); float3 i = floor(q); float3 f = frac(q); f = f * f * (3 - 2 * f); float v = 0;'
        '  [unroll] for (int k = 0; k < 8; k++) { float3 o = float3(k & 1, (k >> 1) & 1, (k >> 2) & 1);'
        '   float3 c = frac((i + o) * 0.3183099 + 0.1) * 17.0; float r = frac(c.x * c.y * c.z * (c.x + c.y + c.z));'
        '   float3 w = lerp(1 - f, f, o); v += r * w.x * w.y * w.z; }'
        '  if (s == 0) n = v; else fine = v; }'
        ' float3 stone = lerp(float3(0.085, 0.082, 0.076), float3(0.23, 0.215, 0.195), n) * lerp(0.75, 1.2, fine);'
        ' stone *= lerp(0.35, 1.2, F.b);'
        ' float top = saturate((N.z - 0.5) * 3);'
        ' float lichen = top * saturate(n * 2.2 - 1.0);'
        ' stone = lerp(stone, float3(0.36, 0.34, 0.3), top * saturate(fine * 1.6 - 0.9) * 0.6);'
        ' return lerp(stone, float3(0.3, 0.32, 0.17), lichen * 0.6);',
        unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'N', 'F'))
    rough = custom('return lerp(0.92, 0.75, F.b);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('F',))
    for source, pin in ((position, 'P'), (normal, 'N'), (flags, 'F')):
        assert mel.connect_material_expressions(source, '', colour, pin)
    assert mel.connect_material_expressions(flags, '', rough, 'F')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def spots(ground, avoid):
    rng = random.Random(23)
    chosen = []
    for (x0, x1), (y0, y1), count in AREAS:
        placed, tries = 0, 0
        while placed < count and tries < 6000:
            tries += 1
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            z = ground(x, y)
            if z is None or not (SEA + 75 < z < 320):
                continue
            if any(math.hypot(x - cx, y - cy) < r for cx, cy, r in KEEP_CLEAR):
                continue
            if any(math.hypot(x - px, y - py) < 300 for px, py in avoid) or any(math.hypot(x - px, y - py) < 600 for px, py, _ in chosen):
                continue
            chosen.append((x, y, z))
            placed += 1
    return chosen


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    material = rock_material()
    meshes = [write_static_mesh(boulder(**shape), f'{FOLDER}/SM_CoastalBoulder_{k + 1}', [material], 120.0) for k, shape in enumerate(SHAPES)]
    stone = unreal.load_asset(STONE)
    assert stone
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()) == FLORA_FOLDER and actor.get_actor_label().startswith('Boulder'):
            actors.destroy_actor(actor)
    # Keep clear of the palms and plants already growing there.
    plants = [(a.get_actor_location().x, a.get_actor_location().y) for a in actors.get_all_level_actors()
              if str(a.get_folder_path()) == FLORA_FOLDER and not a.get_actor_label().startswith('Boulder')]
    rng = random.Random(9)
    placed = []
    for k, (x, y, z) in enumerate(spots(Ground(), plants)):
        shape = SHAPES[k % len(SHAPES)]
        scale = rng.uniform(0.85, 1.2)
        lift = 0.08 * shape['size'][2] * scale  # proud of the sand, yet bedded in on slopes too
        rock = actors.spawn_actor_from_class(unreal.EWMineable, unreal.Vector(x, y, z + lift),
                                             unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
        rock.set_actor_label(f'Boulder {k + 1:02d}')
        rock.set_folder_path(FLORA_FOLDER)
        mesh = rock.get_editor_property('mesh')
        mesh.set_static_mesh(meshes[k % len(meshes)])
        mesh.set_relative_scale3d(unreal.Vector(scale, scale, scale))
        rock.set_editor_property('resource', stone)
        # The rock itself is solid, so survivors can climb onto it as well as walk around it.
        mesh.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        for channel in (unreal.CollisionChannel.ECC_PAWN, unreal.CollisionChannel.ECC_CAMERA, unreal.CollisionChannel.ECC_WORLD_DYNAMIC):
            mesh.set_collision_response_to_channel(channel, unreal.CollisionResponseType.ECR_BLOCK)
        placed.append([round(x), round(y), round(z)])
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'CoastalRocksResult.json').write_text(json.dumps({'success': True, 'rocks': len(placed), 'positions': placed}, indent=2))
    unreal.log(f'Coastal rocks: {len(placed)}')


if __name__ == '__main__':
    main()
