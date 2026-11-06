"""Set rocks on the coastal map that give Stone to a pickaxe. Safe to run again.
Run in the editor after build_coastal_flora.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner, October 15: more rock, in different sizes and colours, and no more low-poly look. Eight shapes built in
the editor at a fine resolution and smooth-shaded: rounded boulders, flat slabs, broken angular blocks and tall
outcrops, their lumps from layered noise and their broken faces from fracture planes. Four stones, one material
with four looks: grey granite, warm sandstone, dark basalt and pale coral limestone. Every stone is finished in
the shader with grain at several scales, a network of cracks and fine bumps that catch the light, darker
crevices, salt-darkened where the sea wets it, and lichen on the faces that look up.

Rocks sit bedded in the ground on every island of the five-region world (the starter island's as before), from knee-high stones to outcrops
taller than a survivor, clear of the trees, the spawn, the dock and the spring. Each is a mining node (the
existing test yield: 12 Stone, 3 a strike) and is solid enough to climb onto. Sizes, colours and counts are tuning.
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
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from world_landmarks import near_landmark  # noqa: E402

FOLDER = '/Game/Elitewake/World/Rocks'
STONE = '/Game/Elitewake/Items/Testing/DA_TestStone'
# Shapes (tuning): size in cm at scale 1, and how many fracture planes cut it (more reads more broken).
SHAPES = [dict(seed=1, size=(270.0, 220.0, 170.0), cuts=1), dict(seed=2, size=(210.0, 180.0, 150.0), cuts=2),
          dict(seed=3, size=(340.0, 250.0, 190.0), cuts=3), dict(seed=4, size=(160.0, 150.0, 125.0), cuts=0),
          dict(seed=5, size=(380.0, 300.0, 110.0), cuts=2),     # a flat slab
          dict(seed=6, size=(230.0, 200.0, 330.0), cuts=5),     # a tall outcrop
          dict(seed=7, size=(300.0, 170.0, 200.0), cuts=4),     # a broken block
          dict(seed=8, size=(120.0, 100.0, 80.0), cuts=1)]      # a stone
# Stones (tuning): dark and light tones, lichen, banding and its spacing in cm, bump strength.
STONES = {'Granite': dict(dark=(.07, .068, .064), light=(.27, .26, .245), lichen=.6, strata=0.0, spacing=12.0, bump=5.0),
          'Sandstone': dict(dark=(.19, .12, .065), light=(.5, .36, .21), lichen=.25, strata=.55, spacing=9.0, bump=4.0),
          'Basalt': dict(dark=(.022, .022, .025), light=(.1, .095, .09), lichen=.35, strata=.12, spacing=20.0, bump=6.0),
          'Limestone': dict(dark=(.28, .27, .23), light=(.64, .61, .53), lichen=.3, strata=.3, spacing=18.0, bump=4.5),
          # Winter: the same stone, snow lying on top (owner: stone keeps one style; winter adds snow on top).
          'GraniteSnow': dict(dark=(.07, .068, .064), light=(.27, .26, .245), lichen=.1, strata=0.0, spacing=12.0, bump=5.0, snow=1.0),
          'BasaltSnow': dict(dark=(.022, .022, .025), light=(.1, .095, .09), lichen=.05, strata=.12, spacing=20.0, bump=6.0, snow=1.0)}
# Where rocks go: x range, y range, how many, and the scale range there (tuning).
AREAS = [((-5900.0, 4300.0), (-4200.0, 4000.0), 34, (.45, 1.6))]        # the starter island, as it always was
# The five-region world (owner, October 15; world_layout.py): every other island gets rocks by its region
# (DECIDED, delegated; tuning): per 1,000 m2, the scale range, and the stones it shows. Stone keeps one style the world
# over; winter adds snow on top (owner).
ROCK_RECIPES = {'Plains': (0.45, (.5, 2.0), ['Granite'] * 3 + ['Limestone'] * 2),
                'Desert': (0.45, (.5, 2.2), ['Sandstone'] * 4 + ['Limestone']),
                'Winter': (0.7, (.6, 2.6), ['GraniteSnow'] * 3 + ['BasaltSnow']),
                'Jungle': (0.35, (.5, 2.0), ['Basalt'] * 2 + ['Granite'] * 2),
                'Swamp': (0.15, (.4, 1.2), ['Basalt', 'Granite'])}
MAX_ROCKS = 220        # per island (the bigger islands of October 15 night; tuning)


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


def boulder(seed, size, cuts=0):
    """A rock in its own space, its widest part at the origin's height so half of it sinks into the ground. Lumps
    come from noise at three scales; each fracture plane shears off a side into a flat broken face."""
    noise = lattice(seed)
    rng = random.Random(seed * 101)
    planes = []
    for _ in range(cuts):
        a, up = rng.uniform(0, 2 * math.pi), rng.uniform(-.25, .75)
        n = (math.cos(a) * math.sqrt(1 - up * up), math.sin(a) * math.sqrt(1 - up * up), up)
        planes.append((n, rng.uniform(.55, .8)))
    verts, faces = icosphere(5)
    sx, sy, sz = (s / 2 for s in size)
    b = Builder()
    shaped, depth = [], []
    for p in verts:
        # Broad lumps, then sharp ridges (folded noise) so the stone reads fractured rather than smooth.
        bump = (0.22 * noise(p[0] * 1.6 + seed, p[1] * 1.6, p[2] * 1.6)
                + 0.12 * (0.5 - abs(noise(p[0] * 3.2, p[1] * 3.2 + seed, p[2] * 3.2)))
                + 0.05 * noise(p[0] * 8.0 + seed, p[1] * 8.0, p[2] * 8.0))
        r = 1.0 + bump
        q = [p[0] * r, p[1] * r, p[2] * r]
        for n, d in planes:
            over = q[0] * n[0] + q[1] * n[1] + q[2] * n[2] - d
            if over > 0:
                for i in range(3):
                    q[i] -= n[i] * over * .92
                bump -= over * .5     # broken faces read a shade darker toward their middles
        p, r = q, 1.0
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


NOISE = """
struct Stone {
  float h(float3 c) { c = frac(c * 0.3183099 + 0.1) * 17.0; return frac(c.x * c.y * c.z * (c.x + c.y + c.z)); }
  float n(float3 q) {
    float3 i = floor(q), f = frac(q); f = f * f * (3 - 2 * f);
    return lerp(lerp(lerp(h(i), h(i + float3(1, 0, 0)), f.x), lerp(h(i + float3(0, 1, 0)), h(i + float3(1, 1, 0)), f.x), f.y),
                lerp(lerp(h(i + float3(0, 0, 1)), h(i + float3(1, 0, 1)), f.x), lerp(h(i + float3(0, 1, 1)), h(i + float3(1, 1, 1)), f.x), f.y), f.z);
  }
  float fbm(float3 q) { float a = .5, s = 0; for (int k = 0; k < 5; k++) { s += a * n(q); q = q * 2.03 + 17.1; a *= .5; } return s; }
  float crack(float3 q) {
    float3 w = float3(n(q * .43 + 3.1), n(q * .43 + 8.7), n(q * .43 + 1.9)) * 1.6;
    return pow(saturate(1 - abs(n(q + w) * 2 - 1)), 70) * saturate(n(q * .21 + 9.7) * 3.2 - 1.5);
  }
  float cracks(float3 p) { return crack(p / 34.0) * .9 + crack(p / 11.0 + 5.3) * .45; }
  float height(float3 p) { return fbm(p / 16.0) + fbm(p / 3.5) * .3 - cracks(p) * .7; }
};
Stone r;
"""


def rock_material():
    """One stone material with parameters for each look (see STONES). Colour and surface detail are worked out in
    world space, so they never stretch or tile across a rock, at any scale."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_CoastalRock_v2')
    material.set_editor_property('tangent_space_normal', False)
    position = node(unreal.MaterialExpressionWorldPosition)
    normal = node(unreal.MaterialExpressionVertexNormalWS)
    flags = node(unreal.MaterialExpressionVertexColor)
    vectors = {name: node(unreal.MaterialExpressionVectorParameter, parameter_name=name, default_value=unreal.LinearColor(*value, 1))
               for name, value in (('Dark', (.07, .068, .064)), ('Light', (.27, .26, .245)), ('LichenColour', (.28, .3, .15)))}
    scalars = {name: node(unreal.MaterialExpressionScalarParameter, parameter_name=name, default_value=value)
               for name, value in (('Lichen', .5), ('Strata', 0.0), ('Spacing', 12.0), ('Bump', 5.0), ('Snow', 0.0))}
    colour = custom(NOISE + """
float big = r.fbm(P / 90.0), mid = r.fbm(P / 13.0), fine = r.n(P / 1.3);
float3 c = lerp(Dark, Light, saturate(big * 1.5 - .25));
c *= lerp(.78, 1.18, mid) * lerp(.9, 1.08, fine);
float band = sin(P.z / Spacing + big * 7.0) * .5 + .5;
c = lerp(c, c * lerp(.7, 1.15, r.n(float3(0, 0, P.z / Spacing))), band * Strata);
c *= 1 - saturate(r.cracks(P)) * .55;
c *= lerp(.94, 1.04, r.n(P / .45));
c *= lerp(.4, 1.12, F.b);
float up = saturate((N.z - .45) * 3);
float lichen = up * saturate(r.fbm(P / 22.0) * 2.6 - 1.05) * Lichen;
c = lerp(c, LichenColour * lerp(.7, 1.2, mid), lichen);
c *= lerp(1.0, .55, saturate((-35.0 - P.z) / 70.0));
float lying = saturate((N.z - .3) * 2.6) * saturate(r.fbm(P / 30.0) * 2.0 - .2) * Snow;
c = lerp(c, float3(.8, .84, .9) * lerp(.92, 1.04, fine), lying);
return c;""", unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'N', 'F', 'Dark', 'Light', 'LichenColour', 'Lichen', 'Strata', 'Spacing', 'Snow'))
    bumped = custom(NOISE + """
float e = .5, h0 = r.height(P);
float3 g = float3(r.height(P + float3(e, 0, 0)) - h0, r.height(P + float3(0, e, 0)) - h0, r.height(P + float3(0, 0, e)) - h0) / e;
g -= N * dot(g, N);
return normalize(N - g * Bump);""", unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'N', 'Bump'))
    rough = custom(NOISE + 'return lerp(.95, .72, F.b) - r.cracks(P) * .1 - saturate((-35.0 - P.z) / 70.0) * .4;',
                   unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('P', 'F'))
    for target, pins in ((colour, ('P', 'N', 'F', 'Dark', 'Light', 'LichenColour', 'Lichen', 'Strata', 'Spacing', 'Snow')),
                         (bumped, ('P', 'N', 'Bump')), (rough, ('P', 'F'))):
        for pin in pins:
            source = {'P': position, 'N': normal, 'F': flags}.get(pin) or vectors.get(pin) or scalars.get(pin)
            assert mel.connect_material_expressions(source, '', target, pin), pin
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(bumped, '', unreal.MaterialProperty.MP_NORMAL)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    looks = {}
    for name, stone in STONES.items():
        path = f'{FOLDER}/MI_Rock_{name}_v1'
        mi = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            f'MI_Rock_{name}_v1', FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, material)
        mel.set_material_instance_vector_parameter_value(mi, 'Dark', unreal.LinearColor(*stone['dark'], 1))
        mel.set_material_instance_vector_parameter_value(mi, 'Light', unreal.LinearColor(*stone['light'], 1))
        for param, key in (('Lichen', 'lichen'), ('Strata', 'strata'), ('Spacing', 'spacing'), ('Bump', 'bump'), ('Snow', 'snow')):
            mel.set_material_instance_scalar_parameter_value(mi, param, stone.get(key, 0.0))
        mel.update_material_instance(mi)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
        looks[name] = mi
    return material, looks


def spots(ground, avoid):
    rng = random.Random(23)
    chosen = []
    for (x0, x1), (y0, y1), count, scales in AREAS:
        placed, tries = 0, 0
        while placed < count and tries < 6000:
            tries += 1
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            z = ground(x, y)
            if z is None or not (SEA + 75 < z < 1300):
                continue
            if any(math.hypot(x - cx, y - cy) < r for cx, cy, r in KEEP_CLEAR) or T.near_cave(x, y) or T.near_climb(x, y) or near_landmark(x, y):
                continue
            if any(math.hypot(x - px, y - py) < 300 for px, py in avoid) or any(math.hypot(x - px, y - py) < 450 for px, py, _, _ in chosen):
                continue
            chosen.append((x, y, z, rng.uniform(*scales)))
            placed += 1
    return chosen


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    _, looks = rock_material()
    bodies = [boulder(**shape) for shape in SHAPES]
    meshes = [write_static_mesh(body, f'{FOLDER}/SM_CoastalBoulder_{k + 1}', [looks['Granite']], 120.0, split_angle=75.0)
              for k, body in enumerate(bodies)]
    # Each shape's lowest and highest point: fracture planes can shear the underside, so bed rocks by their real base.
    spans = [(min(p[2] for p in body.verts), max(p[2] for p in body.verts)) for body in bodies]
    stone = unreal.load_asset(STONE)
    assert stone
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()) == FLORA_FOLDER and actor.get_actor_label().startswith('Boulder'):
            actors.destroy_actor(actor)
    # Keep clear of the trees and plants already growing there.
    plants = [(a.get_actor_location().x, a.get_actor_location().y) for a in actors.get_all_level_actors()
              if str(a.get_folder_path()) == FLORA_FOLDER and not a.get_actor_label().startswith('Boulder')]
    ground = Ground()
    rng = random.Random(9)
    # Mostly grey granite, then sandstone, some dark basalt and pale limestone.
    mix = ['Granite'] * 4 + ['Sandstone'] * 3 + ['Basalt'] * 2 + ['Limestone'] * 2
    wanted = [(x, y, z, scale, k % len(SHAPES), rng.choice(mix)) for k, (x, y, z, scale) in enumerate(spots(ground, plants))]
    # Every other island, by its region.
    for island in W.ISLANDS:
        density, scales, looks_here = ROCK_RECIPES[island.region]
        want = min(MAX_ROCKS, int(round(density * math.pi * island.rx * island.ry / 1e7)))
        irng = random.Random(sum(map(ord, island.key)) * 7907)
        reach, here, tries = island.reach(), [], 0
        close = [(px, py) for px, py in plants if abs(px - island.cx) < reach + 600 and abs(py - island.cy) < reach + 600]
        while len(here) < want and tries < want * 60 + 100:
            tries += 1
            x, y = island.cx + irng.uniform(-reach, reach), island.cy + irng.uniform(-reach, reach)
            if island.distance(x, y) > -300 or W.near_port(x, y) or T.near_cave(x, y) or T.near_climb(x, y) or near_landmark(x, y):
                continue
            if island.key == 'Starter' and island.old.distance(x, y) < 1500:
                continue   # the starter's old ground keeps exactly the rocks it always had
            z = ground(x, y)
            if z < SEA + 60 or any(math.hypot(x - px, y - py) < 300 for px, py in close):
                continue
            if any(math.hypot(x - px, y - py) < 500 for px, py in here):
                continue
            here.append((x, y))
            wanted.append((x, y, z, irng.uniform(*scales), irng.randrange(len(SHAPES)), irng.choice(looks_here)))
    placed = []
    for k, (x, y, z, scale, shape_index, look) in enumerate(wanted):
        low, high = spans[shape_index]
        # On a slope, bed it lower, halfway to the lowest ground under its footprint, so its downhill side is not left proud.
        reach = .35 * max(SHAPES[shape_index]['size'][:2]) * scale
        under = [ground(x + dx * reach, y + dy * reach) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        tall = scale * rng.uniform(.85, 1.1)
        # ...but never more than 40% of its height, or on a mountainside the rock would sink out of sight.
        z = max((z + min([z] + [g for g in under if g is not None])) / 2, z - .4 * tall * (high - low))
        lift = tall * (-low - .12 * (high - low))  # the base sunk an eighth of the rock's height, bedded in on slopes too
        rock = actors.spawn_actor_from_class(unreal.EWMineable, unreal.Vector(x, y, z + lift),
                                             unreal.Rotator(roll=rng.uniform(-6, 6), pitch=rng.uniform(-6, 6), yaw=rng.uniform(0, 360)))
        rock.set_actor_label(f'Boulder {k + 1:02d}')
        rock.set_folder_path(FLORA_FOLDER)
        mesh = rock.get_editor_property('mesh')
        mesh.set_static_mesh(meshes[shape_index])
        mesh.set_material(0, looks[look])
        stretch = rng.uniform(.85, 1.15)
        mesh.set_relative_scale3d(unreal.Vector(scale * stretch, scale / stretch, tall))
        rock.set_editor_property('resource', stone)
        # The rock itself is solid, so survivors can climb onto it as well as walk around it.
        mesh.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        for channel in (unreal.CollisionChannel.ECC_PAWN, unreal.CollisionChannel.ECC_CAMERA, unreal.CollisionChannel.ECC_WORLD_DYNAMIC):
            mesh.set_collision_response_to_channel(channel, unreal.CollisionResponseType.ECR_BLOCK)
        placed.append([round(x), round(y), round(z), round(scale, 2), shape_index + 1, look])
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'CoastalRocksResult.json').write_text(json.dumps(
        {'success': True, 'rocks': len(placed), 'looks': {n: sum(1 for p in placed if p[5] == n) for n in STONES},
         'positions': placed}, indent=2))
    unreal.log(f'Coastal rocks: {len(placed)}')


if __name__ == '__main__':
    main()
