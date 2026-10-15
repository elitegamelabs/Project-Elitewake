"""Grow the coastal map's plant life from the ecology guide's Western Tropical region. Safe to run again.
Run in the editor after build_coastal_terrain.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Veyran Palms: three shapes of feather palm built in the editor, each a ringed, leaning trunk under a crown of
arching fronds (the frond is Art/Flora/Veyran-Palm-Frond-v1.png, drawn by Scripts/Art/make_palm_frond.py) with a
few hanging dry fronds and a cluster of fruit. They stand behind the beaches of the island, the islet and the
second island, singly and in pairs, short and tall, kept clear of the spawn, the dock and the spring.

Maravai (the ecology guide's general tropical lumber tree; owner, October 15: more trees, different sizes and
colours): three shapes of spreading broadleaf hardwood, a stout curving trunk forking into limbs under rounded
clumps of glossy leaves (Art/Flora/Maravai-Leaves-v1.png, drawn by Scripts/Art/make_leaf_cluster.py). They grow
inland and up the hills. Every tree's leaves take their own shade, from blue-green to yellow-green.

Birch (owner, October 14: the Winter region has birch trees, and winter trees carry snow): three shapes of tall,
slender white-barked birch, its bark marked with dark streaks and patches, light branches climbing the upper trunk
under small clumps of yellowing leaves (Art/Flora/Birch-Leaves-v1.png) with snow lying on their upper sides. They
stand over the Winter island, from the beach heads up its slopes.

Spruce (owner, October 14: the Jungle has tall spruce, dense and maze-like): three shapes of tall, narrow spruce,
a straight trunk under whorls of drooping boughs that shorten toward the spire, each bough two crossed cards of
needle sprays (Art/Flora/Spruce-Needles-v1.png).

The five-region world (owner, October 15; world_layout.py): the starter island keeps exactly the palms, Maravai
and plants it had; every other island is dressed for its region (DECIDED, delegated, recipes and densities are
tuning): Plains with groups of Maravai; Desert with palms near its shores; Winter with birches; Jungle with dense
spruce and Maravai between them; Swamp with scattered Maravai (the owner's swamp vegetation is still open). Every
island has fiber plants, fallen sticks and berry bushes to gather by hand (owner: common resources everywhere).

Each tree is harvestable: a hatchet gives Wood and Thatch (the existing test yields; Maravai Timber as its own
item is not made yet), and its trunk is solid.

Under and between them, things to gather by hand with Interact, at the existing test amounts: low fern-like
fiber plants (10 Fiber), piles of fallen sticks near the palms (6 Sticks) and berry bushes hung with berries
(10 berries). Plants can be walked through. All sizes and counts are tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, cross, material_builder, norm, write_static_mesh  # noqa: E402
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Flora'
FLORA_FOLDER = 'Coast/Flora'
ROOT = Path(unreal.Paths.project_dir()).resolve()
FROND_ART = ROOT / 'Art/Flora/Veyran-Palm-Frond-v1.png'
LEAF_ART = ROOT / 'Art/Flora/Maravai-Leaves-v1.png'
BIRCH_ART = ROOT / 'Art/Flora/Birch-Leaves-v1.png'
SPRUCE_ART = ROOT / 'Art/Flora/Spruce-Needles-v1.png'
TIMBER = '/Game/Elitewake/World/Materials/T_Timber_v1'
ITEMS = '/Game/Elitewake/Items/Testing'
WOOD, THATCH = f'{ITEMS}/DA_TestWood', f'{ITEMS}/DA_TestThatch'
# Hand-gathered plants (tuning): item, amount, gathering kind, how many on the island and on the islet.
PLANTS = {'Fiber Plant': ('DA_TestFiber', 10, 'PLANT_FIBER', (18, 5, 8, 4)),
          'Fallen Sticks': ('DA_TestSticks', 6, 'LOOSE_STICKS', (12, 4, 6, 8)),
          'Berry Bush': ('DA_TestAzulBerry', 10, 'BERRIES', (8, 3, 4, 3))}
SEA = -65.0
BARK, FROND = 0, 1
# Palm shapes (tuning): height, lean at the crown, frond count and length.
PALMS = [dict(height=720.0, lean=170.0, fronds=13, frond=380.0, seed=1),
         dict(height=880.0, lean=260.0, fronds=12, frond=420.0, seed=2),
         dict(height=600.0, lean=90.0, fronds=14, frond=340.0, seed=3)]
# Where palms may not stand: (x, y, radius), around the beach spawn, the dock's landing and the spring.
# Maravai shapes (tuning): height, how far the limbs spread, how many limbs.
MARAVAI = [dict(height=900.0, spread=380.0, limbs=6, seed=11), dict(height=1150.0, spread=460.0, limbs=7, seed=12),
           dict(height=700.0, spread=320.0, limbs=5, seed=13)]
KEEP_CLEAR = [(150.0, 0.0, 700.0), (4000.0, 900.0, 700.0), (-1700.0, 1500.0, 1000.0)]
# x range, y range, palms there, Maravai there (tuning): the island, the islet, the second island.
AREAS = [((-5900.0, 4300.0), (-4200.0, 4000.0), 40, 18)]   # the starter island, as it always was
# Birch shapes (tuning): height, how far the branches reach, how many branches; and how many on the Winter island.
BIRCH = [dict(height=1150.0, reach=200.0, branches=9, seed=21), dict(height=1350.0, reach=240.0, branches=10, seed=22),
         dict(height=950.0, reach=170.0, branches=8, seed=23)]
BIRCH_SCALE = (.75, 1.2)
# Spruce shapes (tuning): height, the lowest boughs' reach, how many whorls.
SPRUCE = [dict(height=1800.0, reach=360.0, whorls=16, seed=31), dict(height=2300.0, reach=420.0, whorls=19, seed=32),
          dict(height=1500.0, reach=300.0, whorls=13, seed=33)]
SPRUCE_SCALE = (.8, 1.25)
# Each region's dressing (DECIDED, delegated; tuning): trees per 1,000 m2 of island by kind, whether trees grow in
# groups, and fiber plants, stick piles and berry bushes per 1,000 m2.
RECIPES = {'Plains': dict(trees={'Maravai': 1.0}, groups=True, plants=(0.45, 0.3, 0.22)),
           'Desert': dict(trees={'Veyran Palm': 0.7}, groups=False, plants=(0.2, 0.15, 0.08)),
           'Winter': dict(trees={'Birch': 2.0}, groups=False, plants=(0.15, 0.3, 0.12)),
           'Jungle': dict(trees={'Spruce': 4.5, 'Maravai': 0.8}, groups=False, plants=(0.5, 0.4, 0.25)),
           'Swamp': dict(trees={'Maravai': 0.6}, groups=True, plants=(0.7, 0.3, 0.15))}
MAX_TREES = 380        # per island
PALM_SCALE = (.7, 1.35)
MARAVAI_SCALE = (.75, 1.25)


# ---- Meshes ------------------------------------------------------------------------------------------------

def palm(height, lean, fronds, frond, seed):
    """A palm in its own space: trunk from the origin, leaning toward +X."""
    rng = random.Random(seed)
    b = Builder()
    rings = int(height / 9)

    def axis(t):
        return (lean * t ** 1.6, 0.0, height * t)

    path = [axis(k / rings) for k in range(rings + 1)]

    def radius(k):
        t = k / rings
        flare = 10.0 * max(0.0, 1 - t / 0.08) ** 2       # the trunk swells at its foot
        ring = 1.0 + 0.07 * math.cos(2 * math.pi * (height * t) / 18.0)  # leaf-scar rings
        return (14.5 - 3.5 * t + flare) * ring

    b.slot = BARK
    b.tube(path, radius, sides=14, uv_of=lambda k, s: (s / 14 * 0.7, height * k / rings / 120))
    top = axis(1.0)
    b.tube([top, (top[0], 0, top[2] + 45)], lambda k: (13.0, 9.0)[k], sides=12)   # crownshaft
    # Fruit hanging under the crown.
    for k in range(6):
        a = 2 * math.pi * k / 6 + rng.random()
        c = (top[0] + 16 * math.cos(a), 16 * math.sin(a), top[2] - 6 - 8 * rng.random())
        b.tube([(c[0], c[1], c[2] - 9), (c[0], c[1], c[2] + 9)], lambda q: 6.5, sides=8, iron=0.0)
    b.slot = FROND
    crown = (top[0], 0.0, top[2] + 35)
    for k in range(fronds + 3):
        dry = k >= fronds
        a = 2 * math.pi * k / fronds + rng.uniform(-0.2, 0.2) if not dry else rng.uniform(0, 2 * math.pi)
        rise = math.radians(rng.uniform(25, 55)) if not dry else math.radians(-60)
        length = frond * rng.uniform(0.85, 1.1) * (0.8 if dry else 1.0)
        droop = rng.uniform(0.7, 1.0) if not dry else 0.25
        frond_strip(b, crown, a, rise, length, droop, dry)
    return b


def maravai(height, spread, limbs, seed):
    """A broadleaf tree in its own space: a stout, gently curving trunk forking into limbs that reach out and up,
    each ending in clumps of leaves made of crossed cards, and a clump over the crown."""
    rng = random.Random(seed)
    b = Builder()
    lean = rng.uniform(-.08, .08) * height
    fork = height * .5
    trunk = [(lean * (k / 10) ** 2, 0.0, fork * k / 10) for k in range(11)]
    b.tube(trunk, lambda k: 34.0 - 14.0 * k / 10 + (10.0 if k == 0 else 0.0), sides=12)
    top = trunk[-1]
    clumps = [((top[0], 0.0, height * .9), spread * .8)]
    for n in range(limbs):
        a = 2 * math.pi * n / limbs + rng.uniform(-.3, .3)
        reach, rise = spread * rng.uniform(.75, 1.05), height * rng.uniform(.18, .34)
        start = (top[0], 0.0, fork - rng.uniform(0, height * .08))
        end = (start[0] + reach * math.cos(a), start[1] + reach * math.sin(a), start[2] + rise)
        bend = (start[0] + reach * .45 * math.cos(a), start[1] + reach * .45 * math.sin(a), start[2] + rise * .8)
        path = [tuple(start[i] * (1 - t) ** 2 + 2 * bend[i] * t * (1 - t) + end[i] * t * t for i in range(3)) for t in (k / 6 for k in range(7))]
        b.tube(path, lambda k: 15.0 - 10.0 * k / 6, sides=8)
        clumps.append((end, spread * rng.uniform(.5, .65)))
        clumps.append((path[4], spread * rng.uniform(.4, .55)))
        clumps.append((path[2], spread * rng.uniform(.3, .42)))
    b.slot = 1
    for (cx, cy, cz), size in clumps:
        # Seven cards of leaves at random slants, a little apart, so no clump shows a straight edge or a cross.
        for _ in range(7):
            h = size / 2 * rng.uniform(.6, 1.0)
            a, tilt = rng.uniform(0, 2 * math.pi), rng.uniform(-1.1, 1.1)
            n = (math.cos(a) * math.cos(tilt), math.sin(a) * math.cos(tilt), math.sin(tilt))
            ref = (0, 0, 1) if abs(n[2]) < .9 else (1, 0, 0)
            u = norm(cross(n, ref))
            v = cross(n, u)
            spin = rng.uniform(0, 2 * math.pi)
            u, v = (tuple(u[i] * math.cos(spin) + v[i] * math.sin(spin) for i in range(3)),
                    tuple(v[i] * math.cos(spin) - u[i] * math.sin(spin) for i in range(3)))
            c = (cx + rng.uniform(-.2, .2) * size, cy + rng.uniform(-.2, .2) * size, cz + rng.uniform(-.12, .12) * size)
            corners = [tuple(c[i] + (su * u[i] + sv * v[i]) * h for i in range(3)) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            ids = [b.vertex(p, uv=uv) for p, uv in zip(corners, ((0, 1), (1, 1), (1, 0), (0, 0)))]
            b.quad(*ids, n)
    b.slot = 0
    return b


def birch(height, reach, branches, seed):
    """A birch in its own space: a tall, slender, slightly wandering trunk, light branches rising off its upper
    two thirds, small leaf clumps along and at the ends of them, and a clump at the crown."""
    rng = random.Random(seed)
    b = Builder()
    wander = [(rng.uniform(-14, 14), rng.uniform(-14, 14)) for _ in range(4)]
    def at(t):
        k = min(int(t * 3), 2)
        u = t * 3 - k
        x = wander[k][0] * (1 - u) + wander[k + 1][0] * u
        y = wander[k][1] * (1 - u) + wander[k + 1][1] * u
        return (x * t, y * t, height * t)
    trunk = [at(k / 14) for k in range(15)]
    b.tube(trunk, lambda k: 17.0 - 11.0 * k / 14 + (5.0 if k == 0 else 0.0), sides=12)
    clumps = [(at(1.0), 150.0), (at(.9), 120.0)]
    for n in range(branches):
        t = .38 + .55 * n / max(branches - 1, 1)
        start = at(t)
        a = rng.uniform(0, 2 * math.pi)
        long = reach * rng.uniform(.7, 1.1) * (1.15 - .5 * t)
        rise = long * rng.uniform(.6, 1.1)
        end = (start[0] + long * math.cos(a), start[1] + long * math.sin(a), start[2] + rise)
        mid = tuple((start[i] + end[i]) / 2 + (0, 0, -12)[i] for i in range(3))
        b.tube([start, mid, end], lambda k: 4.5 - 1.6 * k, sides=6)
        clumps.append((end, rng.uniform(85.0, 125.0)))
        clumps.append((mid, rng.uniform(60.0, 90.0)))
    b.slot = 1
    for (cx, cy, cz), size in clumps:
        for _ in range(5):
            h = size / 2 * rng.uniform(.6, 1.0)
            a, tilt = rng.uniform(0, 2 * math.pi), rng.uniform(-1.1, 1.1)
            n = (math.cos(a) * math.cos(tilt), math.sin(a) * math.cos(tilt), math.sin(tilt))
            ref = (0, 0, 1) if abs(n[2]) < .9 else (1, 0, 0)
            u = norm(cross(n, ref))
            v = cross(n, u)
            c = (cx + rng.uniform(-.2, .2) * size, cy + rng.uniform(-.2, .2) * size, cz + rng.uniform(-.12, .12) * size)
            corners = [tuple(c[i] + (su * u[i] + sv * v[i]) * h for i in range(3)) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            ids = [b.vertex(p, uv=uv) for p, uv in zip(corners, ((0, 1), (1, 1), (1, 0), (0, 0)))]
            b.quad(*ids, n)
    b.slot = 0
    return b


def spruce(height, reach, whorls, seed):
    """A spruce in its own space: a straight tapering trunk to a spire, whorls of drooping boughs that shorten
    toward the top, each bough two crossed cards of needle spray (the texture's twig runs left to right)."""
    rng = random.Random(seed)
    b = Builder()
    b.tube([(0, 0, height * k / 12) for k in range(13)], lambda k: 32.0 - 28.0 * k / 12 + (10.0 if k == 0 else 0.0), sides=10)
    b.slot = 1
    for w in range(whorls):
        t = .14 + .84 * w / max(whorls - 1, 1)
        z = height * t
        long = reach * (1 - t) ** 1.05 + 45
        count = 5 if t < .7 else 4
        turn = rng.uniform(0, 2 * math.pi)
        for n in range(count):
            a = turn + 2 * math.pi * n / count + rng.uniform(-.2, .2)
            droop = rng.uniform(.18, .38)
            d = (math.cos(a), math.sin(a), 0.0)
            tip = (d[0] * long, d[1] * long, z - droop * long)
            base = (d[0] * 8, d[1] * 8, z)
            side = (-math.sin(a), math.cos(a), 0.0)
            half = long * .5
            # A flat card (needles seen from above) and one on edge, crossing along the bough.
            for across, hint in ((side, (0.0, 0.0, 1.0)), ((0.0, 0.0, 1.0), side)):
                corners = [tuple(base[i] - across[i] * half * .5 for i in range(3)), tuple(tip[i] - across[i] * half * .3 for i in range(3)),
                           tuple(tip[i] + across[i] * half * .3 for i in range(3)), tuple(base[i] + across[i] * half * .5 for i in range(3))]
                ids = [b.vertex(c, uv=uv) for c, uv in zip(corners, ((0, .82), (1, .62), (1, .38), (0, .18)))]
                b.quad(*ids, hint)
    # The spire.
    for k in range(3):
        a = math.pi * k / 3
        u = (math.cos(a) * 40, math.sin(a) * 40, 0)
        top, low = (0, 0, height * 1.04), (0, 0, height * .9)
        corners = [tuple(low[i] - u[i] for i in range(3)), tuple(low[i] + u[i] for i in range(3)), tuple(top[i] + u[i] * .2 for i in range(3)), tuple(top[i] - u[i] * .2 for i in range(3))]
        ids = [b.vertex(c, uv=uv) for c, uv in zip(corners, ((0, .7), (0, .3), (1, .45), (1, .55)))]
        b.quad(*ids, (-math.sin(a), math.cos(a), 0))
    b.slot = 0
    return b


def birch_bark_material():
    """White birch bark marked with dark horizontal streaks (lenticels) and black patches, in world space."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_BirchBark_v1')
    colour = custom(
        'float3 q = P * float3(.32, .32, 2.6); float3 i = floor(q), f = frac(q);'
        ' float h = frac(sin(dot(i, float3(12.9898, 78.233, 37.719))) * 43758.5453);'
        ' float streak = step(.86, h) * smoothstep(.5, .2, abs(f.z - .5));'
        ' float3 w = P / float3(9.0, 9.0, 16.0); float3 c0 = floor(w), t = frac(w); t = t * t * (3 - 2 * t); float g = 0;'
        ' [unroll] for (int k = 0; k < 8; k++) { float3 o = float3(k & 1, (k >> 1) & 1, (k >> 2) & 1);'
        '  float3 wt = lerp(1 - t, t, o); g += frac(sin(dot(c0 + o, float3(39.3, 11.7, 83.1))) * 43758.5453) * wt.x * wt.y * wt.z; }'
        ' float patch = smoothstep(.72, .8, g);'
        ' float tone = .9 + .1 * frac(sin(dot(floor(P / 4.0), float3(7.1, 3.3, 5.9))) * 43758.5453);'
        ' return lerp(float3(.74, .72, .67) * tone, float3(.04, .04, .04), max(streak * .9, patch * .85));',
        unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P',))
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionWorldPosition), '', colour, 'P')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=0.8), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def frond_strip(b, base, heading, rise, length, droop, dry):
    """One frond: an arching strip along its rachis, folded up a little either side, mapped to the frond art."""
    rows = 14
    ca, sa = math.cos(heading), math.sin(heading)
    side = (-sa, ca, 0.0)
    half = length * 0.24
    tone = 1.0 if dry else 0.0
    grid = []
    uvs = []
    for i in range(rows + 1):
        s = i / rows
        d = length * s * math.cos(rise)
        z = length * (s * math.sin(rise) - droop * s * s * 0.9)
        p = (base[0] + ca * d, base[1] + sa * d, base[2] + z)
        fold = 0.35 * half
        row, uv_row = [], []
        for j, v in ((0, -1.0), (1, 0.0), (2, 1.0)):
            lift = fold if v else 0.0
            row.append((p[0] + side[0] * half * v, p[1] + side[1] * half * v, p[2] + lift))
            uv_row.append((s, 0.5 + 0.5 * v))
        grid.append(row)
        uvs.append(uv_row)
    ids = [[b.vertex(p, tone, 0.0, 0.5, uvs[i][j]) for j, p in enumerate(row)] for i, row in enumerate(grid)]
    for i in range(rows):
        for j in range(2):
            b.quad(ids[i][j], ids[i + 1][j], ids[i + 1][j + 1], ids[i][j + 1], (0, 0, 1))


def fiber_plant(seed):
    """A low clump of fern-like fronds springing from the sand."""
    rng = random.Random(seed)
    b = Builder()
    for k in range(9):
        a = 2 * math.pi * k / 9 + rng.uniform(-0.25, 0.25)
        frond_strip(b, (0.0, 0.0, 2.0), a, math.radians(rng.uniform(45, 70)), rng.uniform(80, 120), rng.uniform(0.6, 0.9), False)
    return b


def stick_pile(seed):
    """A few fallen branches lying crossed on the sand, one forked."""
    rng = random.Random(seed)
    b = Builder()
    for k in range(6):
        a = rng.uniform(0, math.pi)
        length = rng.uniform(70, 130)
        cx, cy = rng.uniform(-25, 25), rng.uniform(-25, 25)
        dx, dy = math.cos(a) * length / 2, math.sin(a) * length / 2
        z = 3.0 + 4.0 * k / 6
        path = [(cx - dx, cy - dy, z), (cx + dx * 0.1, cy + dy * 0.1, z + 2), (cx + dx, cy + dy, z + 1)]
        b.tube(path, lambda q, r=rng.uniform(2.2, 3.4): r * (1.0, 0.85, 0.6)[q], sides=7, uv_of=lambda q, s: (s / 7 * 0.3, q * length / 240))
        if k == 0:  # a fork
            b.tube([path[1], (path[1][0] + dy * 0.5, path[1][1] - dx * 0.5, z + 3)], 1.8, sides=6)
    return b


def berry_bush(seed):
    """A rounded leafy bush with clusters of berries among its leaves."""
    rng = random.Random(seed)
    b = Builder()
    b.slot = 1
    for k in range(14):
        a = 2 * math.pi * k / 14 + rng.uniform(-0.2, 0.2)
        frond_strip(b, (rng.uniform(-10, 10), rng.uniform(-10, 10), 5.0), a, math.radians(rng.uniform(50, 80)),
                    rng.uniform(70, 100), rng.uniform(0.9, 1.2), False)
    b.slot = 2
    for k in range(9):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(25, 45)
        cx, cy, cz = d * math.cos(a), d * math.sin(a), rng.uniform(35, 65)
        for j in range(5):
            bx, by, bz = cx + rng.uniform(-5, 5), cy + rng.uniform(-5, 5), cz + rng.uniform(-5, 4)
            b.tube([(bx, by, bz - 2.2), (bx, by, bz), (bx, by, bz + 2.2)], lambda q: (1.2, 2.6, 1.2)[q], sides=8)
    b.slot = 0
    return b


# ---- Materials ---------------------------------------------------------------------------------------------

def import_texture(name, source):
    path = f'{FOLDER}/{name}'
    task = unreal.AssetImportTask()
    for k, v in {'filename': str(source), 'destination_path': FOLDER, 'destination_name': name,
                 'automated': True, 'replace_existing': True, 'save': True}.items():
        task.set_editor_property(k, v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(path)
    assert isinstance(texture, unreal.Texture2D), path
    return texture


def bark_material():
    """Grey-brown palm bark from the timber texture, darker in the leaf-scar rings' shadow."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_PalmBark_v1')
    wood = node(unreal.MaterialExpressionTextureSample, texture=unreal.load_asset(TIMBER))
    colour = custom('float g = dot(W, float3(0.3, 0.59, 0.11)); return lerp(W * float3(0.9, 0.78, 0.62), g * float3(0.86, 0.8, 0.72), 0.55) * 0.85;',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('W',))
    assert mel.connect_material_expressions(wood, 'RGB', colour, 'W')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=0.9), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def berry_material():
    """Glossy deep blue-violet berries."""
    mel = unreal.MaterialEditingLibrary
    material, node, _ = material_builder(f'{FOLDER}/M_Berry_v1')
    colour = node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(0.08, 0.07, 0.3, 1))
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=0.3), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def frond_material(texture, path=f'{FOLDER}/M_PalmFrond_v1', snow=False):
    """Leaves: the art, cut out by its alpha, lit through from behind; dry fronds turn straw brown. Each tree takes
    its own shade of green, from blue-green to yellow-green, picked by where it stands."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(path)
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    material.set_editor_property('two_sided', True)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    art = node(unreal.MaterialExpressionTextureSample, texture=texture)
    flags = node(unreal.MaterialExpressionVertexColor)
    colour = custom('float h = frac(sin(dot(floor(O.xy / 10.0), float2(12.9898, 78.233))) * 43758.5453);'
                    ' float3 shade = lerp(float3(0.78, 0.98, 0.92), float3(1.2, 1.08, 0.66), h) * lerp(0.85, 1.1, frac(h * 7.31));'
                    ' float3 leaf = A * shade;'
                    ' return lerp(leaf, dot(A, float3(0.3, 0.59, 0.11)) * float3(1.25, 1.0, 0.62), F.r);',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('A', 'F', 'O'))
    through = custom('return C * float3(0.55, 0.7, 0.3);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C',))
    assert mel.connect_material_expressions(art, 'RGB', colour, 'A')
    assert mel.connect_material_expressions(flags, '', colour, 'F')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionObjectPositionWS), '', colour, 'O')
    assert mel.connect_material_expressions(colour, '', through, 'C')
    if snow:
        # Snow lies on the leaves' upper sides (owner: snow on winter trees).
        snowy = custom('float up = saturate((N.z - .15) * 2.2); float n = frac(sin(dot(floor(UV * 18.0), float2(12.9898, 78.233))) * 43758.5453);'
                       ' return lerp(C, float3(.82, .85, .9), up * lerp(.55, .95, n));',
                       unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C', 'N', 'UV'))
        assert mel.connect_material_expressions(colour, '', snowy, 'C')
        assert mel.connect_material_expressions(node(unreal.MaterialExpressionVertexNormalWS), '', snowy, 'N')
        assert mel.connect_material_expressions(node(unreal.MaterialExpressionTextureCoordinate), '', snowy, 'UV')
        colour = snowy
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(through, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    assert mel.connect_material_property(art, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=0.65), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


# ---- Placement ---------------------------------------------------------------------------------------------



class Ground:
    """Ground height anywhere in the world, read from the island meshes as built (made by build_coastal_terrain.py):
    each island's mesh is loaded once and ray-cast straight down, so nothing floats or sinks where the 2-4 m grid's
    triangles cut across a cliff or a channel. Off the islands' meshes it falls back to world_terrain.py."""

    def __init__(self):
        self.meshes = {}

    def mesh(self, key):
        if key not in self.meshes:
            asset = unreal.load_asset(f'/Game/Elitewake/World/Meshes/Islands/SM_Island_{key}_v1')
            mesh = unreal.DynamicMesh()
            if asset:
                unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
                    asset, mesh, unreal.GeometryScriptCopyMeshFromAssetOptions(), unreal.GeometryScriptMeshReadLOD())
                built = unreal.GeometryScript_MeshSpatial.build_bvh_for_mesh(mesh)
                built = built if isinstance(built, tuple) else (built,)
                self.meshes[key] = (mesh, next(v for v in built if isinstance(v, unreal.GeometryScriptDynamicMeshBVH)))
            else:
                self.meshes[key] = None
        return self.meshes[key]

    def __call__(self, x, y):
        best = None
        for i in W.ISLANDS:
            x0, y0, sx, sy, nx, ny = T.GRIDS[i.key]
            if not (x0 <= x <= x0 + sx * nx and y0 <= y <= y0 + sy * ny):
                continue
            found = self.mesh(i.key)
            if not found:
                continue
            mesh, bvh = found
            out = unreal.GeometryScript_MeshSpatial.find_nearest_ray_intersection_with_mesh(
                mesh, bvh, unreal.Vector(x, y, 30000), unreal.Vector(0, 0, -1), unreal.GeometryScriptSpatialQueryOptions())
            hit = next((v for v in (out if isinstance(out, tuple) else (out,)) if isinstance(v, unreal.GeometryScriptRayHitResult)), None)
            if hit and hit.get_editor_property('hit'):
                z = hit.get_editor_property('hit_position').z
                best = z if best is None else max(best, z)
        return best if best is not None else T.built_height(x, y)


def spots(ground):
    """Palm positions behind the beaches: above the wet sand, below the hills, apart from each other."""
    rng = random.Random(11)
    chosen = []
    for (x0, x1), (y0, y1), count, _ in AREAS:
        placed, tries = 0, 0
        while placed < count and tries < 4000:
            tries += 1
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            z = ground(x, y)
            if z is None or not (SEA + 60 < z < 70):
                continue
            if any(math.hypot(x - cx, y - cy) < r for cx, cy, r in KEEP_CLEAR):
                continue
            if any(math.hypot(x - px, y - py) < 450 for px, py, _ in chosen):
                continue
            chosen.append((x, y, z))
            placed += 1
            # Palms often grow in pairs.
            if rng.random() < 0.35 and placed < count:
                a = rng.uniform(0, 2 * math.pi)
                px, py = x + 220 * math.cos(a), y + 220 * math.sin(a)
                pz = ground(px, py)
                if pz is not None and SEA + 60 < pz < 70:
                    chosen.append((px, py, pz))
                    placed += 1
    return chosen


def inland_spots(ground, palms):
    """Maravai positions inland and up the hills, apart from each other and from the palms."""
    rng = random.Random(17)
    chosen = []
    for (x0, x1), (y0, y1), _, count in AREAS:
        placed, tries = 0, 0
        while placed < count and tries < 6000:
            tries += 1
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            z = ground(x, y)
            if z is None or not (40 < z < 650):
                continue
            if any(math.hypot(x - cx, y - cy) < r + 200 for cx, cy, r in KEEP_CLEAR):
                continue
            if any(math.hypot(x - px, y - py) < 450 for px, py in palms) or any(math.hypot(x - px, y - py) < 750 for px, py, _ in chosen):
                continue
            chosen.append((x, y, z))
            placed += 1
    return chosen


def steep(ground, x, y):
    """True on ground too steep for a tree to stand (more than about 40 degrees over 3 m)."""
    gx = ground(x + 150, y) - ground(x - 150, y)
    gy = ground(x, y + 150) - ground(x, y - 150)
    return math.hypot(gx, gy) > 250


def dress_islands(actors, ground, kinds, wood, thatch):
    """Trees on every island but the starter, by its region's recipe. Returns the trees (x, y) and a summary."""
    trees, summary = [], {}
    for island in W.ISLANDS:
        if island.key == 'Starter':
            continue
        recipe = RECIPES[island.region]
        rng = random.Random(sum(map(ord, island.key)) * 104729)
        area = math.pi * island.rx * island.ry / 1e4 / 1000.0      # thousands of m2
        reach = island.reach()
        here = []
        for kind, density in recipe['trees'].items():
            wanted = min(MAX_TREES, int(round(density * area)))
            meshes, scales, radius, half, sink = kinds[kind]
            spacing = 450.0 if kind == 'Spruce' else 650.0
            centres = [(island.cx + rng.uniform(-reach, reach) * .7, island.cy + rng.uniform(-reach, reach) * .7) for _ in range(max(1, wanted // 5))]
            made, tries = 0, 0
            while made < wanted and tries < wanted * 60 + 200:
                tries += 1
                if recipe['groups']:
                    gx, gy = rng.choice(centres)
                    a, d = rng.uniform(0, 2 * math.pi), abs(rng.gauss(0, 1100))
                    x, y = gx + d * math.cos(a), gy + d * math.sin(a)
                else:
                    x, y = island.cx + rng.uniform(-reach, reach), island.cy + rng.uniform(-reach, reach)
                inland = -island.distance(x, y)
                # Palms keep to the shore's sand; other trees stand back from the beach.
                if kind == 'Veyran Palm' and not (300 < inland < 3500):
                    continue
                if kind != 'Veyran Palm' and inland < 700:
                    continue
                z = ground(x, y)
                if z < SEA + 60 or steep(ground, x, y):
                    continue
                if any(math.hypot(x - px, y - py) < spacing for px, py in here):
                    continue
                tree = actors.spawn_actor_from_class(unreal.EWHarvestTree, unreal.Vector(x, y, z - sink),
                                                     unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
                made += 1
                tree.set_actor_label(f'{kind} {island.key} {made:03d}')
                tree.set_folder_path(FLORA_FOLDER)
                mesh = tree.get_editor_property('mesh')
                mesh.set_static_mesh(rng.choice(meshes))
                mesh.set_relative_scale3d(unreal.Vector(*[rng.uniform(*scales)] * 3))
                for prop, value in {'wood': wood, 'thatch': thatch, 'blocker_radius': radius, 'blocker_half_height': half}.items():
                    tree.set_editor_property(prop, value)
                here.append((x, y))
            summary.setdefault(island.key, {})[kind] = made
        trees += here
    return trees, summary


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    frond_art = import_texture('T_PalmFrond_v1', FROND_ART)
    materials = [bark_material(), frond_material(frond_art)]
    meshes = [write_static_mesh(palm(**shape), f'{FOLDER}/SM_VeyranPalm_{k + 1}', materials, 120.0)
              for k, shape in enumerate(PALMS)]
    wood, thatch = unreal.load_asset(WOOD), unreal.load_asset(THATCH)
    assert wood and thatch
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    # Replace this script's earlier palms and plants.
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()) == FLORA_FOLDER and actor.get_actor_label().startswith(('Veyran Palm', 'Maravai', 'Birch', 'Spruce', *PLANTS)):
            actors.destroy_actor(actor)
    rng = random.Random(5)
    placed = []
    ground = Ground()
    for k, (x, y, z) in enumerate(spots(ground)):
        tree = actors.spawn_actor_from_class(unreal.EWHarvestTree, unreal.Vector(x, y, z - 8),
                                             unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
        tree.set_actor_label(f'Veyran Palm {k + 1:02d}')
        tree.set_folder_path(FLORA_FOLDER)
        mesh = tree.get_editor_property('mesh')
        mesh.set_static_mesh(meshes[k % len(meshes)])
        mesh.set_relative_scale3d(unreal.Vector(*[rng.uniform(*PALM_SCALE)] * 3))
        for prop, value in {'wood': wood, 'thatch': thatch, 'blocker_radius': 26.0, 'blocker_half_height': 160.0}.items():
            tree.set_editor_property(prop, value)
        placed.append([round(x), round(y), round(z)])
    leaf_material = frond_material(import_texture('T_MaravaiLeaves_v1', LEAF_ART), f'{FOLDER}/M_MaravaiLeaves_v1')
    broadleaf = [write_static_mesh(maravai(**shape), f'{FOLDER}/SM_Maravai_{k + 1}', [materials[BARK], leaf_material], 120.0)
                 for k, shape in enumerate(MARAVAI)]
    hardwoods = []
    for k, (x, y, z) in enumerate(inland_spots(ground, [(p[0], p[1]) for p in placed])):
        tree = actors.spawn_actor_from_class(unreal.EWHarvestTree, unreal.Vector(x, y, z - 12),
                                             unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
        tree.set_actor_label(f'Maravai {k + 1:02d}')
        tree.set_folder_path(FLORA_FOLDER)
        mesh = tree.get_editor_property('mesh')
        mesh.set_static_mesh(broadleaf[k % len(broadleaf)])
        mesh.set_relative_scale3d(unreal.Vector(*[rng.uniform(*MARAVAI_SCALE)] * 3))
        for prop, value in {'wood': wood, 'thatch': thatch, 'blocker_radius': 38.0, 'blocker_half_height': 220.0}.items():
            tree.set_editor_property(prop, value)
        hardwoods.append([round(x), round(y), round(z)])
    birch_leaves = frond_material(import_texture('T_BirchLeaves_v1', BIRCH_ART), f'{FOLDER}/M_BirchLeaves_v1', snow=True)
    birches = [write_static_mesh(birch(**shape), f'{FOLDER}/SM_Birch_{k + 1}', [birch_bark_material(), birch_leaves], 120.0)
               for k, shape in enumerate(BIRCH)]
    needles = frond_material(import_texture('T_SpruceNeedles_v1', SPRUCE_ART), f'{FOLDER}/M_SpruceNeedles_v1')
    spruces = [write_static_mesh(spruce(**shape), f'{FOLDER}/SM_Spruce_{k + 1}', [materials[BARK], needles], 120.0)
               for k, shape in enumerate(SPRUCE)]
    kinds = {'Veyran Palm': (meshes, PALM_SCALE, 26.0, 160.0, 8), 'Maravai': (broadleaf, MARAVAI_SCALE, 38.0, 220.0, 12),
             'Birch': (birches, BIRCH_SCALE, 20.0, 220.0, 10), 'Spruce': (spruces, SPRUCE_SCALE, 30.0, 260.0, 12)}
    whites, dressed = dress_islands(actors, ground, kinds, wood, thatch)
    plants = place_plants(actors, ground, [(p[0], p[1]) for p in placed + hardwoods], materials, whites)
    assert level.save_current_level()
    report = {'success': True, 'starter_palms': len(placed), 'starter_maravai': len(hardwoods), 'islands': dressed,
              'positions': placed, 'maravai_positions': hardwoods, 'plants': plants}
    Path(unreal.Paths.project_saved_dir(), 'CoastalFloraResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Coastal flora: {len(placed)} palms')


def place_plants(actors, ground, palms, materials, island_trees=()):
    """Fiber plants and berry bushes in the open sand behind the beach; stick piles under the palms. Then the same
    on every other island, by its region's recipe, sticks under its trees."""
    berry = berry_material()
    looks = {'Fiber Plant': [write_static_mesh(fiber_plant(k), f'{FOLDER}/SM_FiberPlant_{k + 1}', [materials[FROND]], 120.0) for k in range(3)],
             'Fallen Sticks': [write_static_mesh(stick_pile(k), f'{FOLDER}/SM_FallenSticks_{k + 1}', [materials[BARK]], 120.0) for k in range(3)],
             'Berry Bush': [write_static_mesh(berry_bush(k), f'{FOLDER}/SM_BerryBush_{k + 1}', [materials[BARK], materials[FROND], berry], 120.0)
                            for k in range(2)]}
    rng = random.Random(31)
    taken = list(palms)
    counts = {}
    for label, (item_name, amount, kind, per_area) in PLANTS.items():
        item = unreal.load_asset(f'{ITEMS}/{item_name}')
        assert item, item_name
        n = 0
        for (area, count) in zip(AREAS, per_area):
            (x0, x1), (y0, y1), _, _ = area
            placed, tries = 0, 0
            while placed < count and tries < 5000:
                tries += 1
                if label == 'Fallen Sticks':
                    px, py = rng.choice(palms)
                    a, d = rng.uniform(0, 2 * math.pi), rng.uniform(150, 400)
                    x, y = px + d * math.cos(a), py + d * math.sin(a)
                    if not (x0 <= x <= x1 and y0 <= y <= y1):
                        continue
                else:
                    x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
                z = ground(x, y)
                if z is None or not (SEA + 70 < z < 160):
                    continue
                if any(math.hypot(x - cx, y - cy) < r for cx, cy, r in KEEP_CLEAR):
                    continue
                if any(math.hypot(x - tx, y - ty) < 140 for tx, ty in taken):
                    continue
                plant = actors.spawn_actor_from_class(unreal.EWHandGatherable, unreal.Vector(x, y, z - 2),
                                                      unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
                n += 1
                plant.set_actor_label(f'{label} {n:02d}')
                plant.set_folder_path(FLORA_FOLDER)
                mesh = plant.get_editor_property('mesh')
                mesh.set_static_mesh(rng.choice(looks[label]))
                mesh.set_relative_scale3d(unreal.Vector(*[rng.uniform(0.85, 1.15)] * 3))
                for prop, value in {'item_definition': item, 'quantity': amount,
                                    'gathering_kind': getattr(unreal.EWHandGatheringKind, kind)}.items():
                    plant.set_editor_property(prop, value)
                taken.append((x, y))
                placed += 1
        # Every other island.
        for island in W.ISLANDS:
            if island.key == 'Starter':
                continue
            per = RECIPES[island.region]['plants'][list(PLANTS).index(label)]
            wanted = int(round(per * math.pi * island.rx * island.ry / 1e7))
            near = [(tx, ty) for tx, ty in island_trees if island.distance(tx, ty) < 0]
            reach = island.reach()
            placed, tries = 0, 0
            while placed < wanted and tries < wanted * 50 + 100:
                tries += 1
                if label == 'Fallen Sticks' and near:
                    px, py = rng.choice(near)
                    a, d = rng.uniform(0, 2 * math.pi), rng.uniform(150, 400)
                    x, y = px + d * math.cos(a), py + d * math.sin(a)
                else:
                    x, y = island.cx + rng.uniform(-reach, reach), island.cy + rng.uniform(-reach, reach)
                if island.distance(x, y) > -400:
                    continue
                z = ground(x, y)
                if z < SEA + 70 or steep(ground, x, y):
                    continue
                if any(math.hypot(x - tx, y - ty) < 140 for tx, ty in near):
                    continue
                plant = actors.spawn_actor_from_class(unreal.EWHandGatherable, unreal.Vector(x, y, z - 2),
                                                      unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
                n += 1
                plant.set_actor_label(f'{label} {n:03d}')
                plant.set_folder_path(FLORA_FOLDER)
                mesh = plant.get_editor_property('mesh')
                mesh.set_static_mesh(rng.choice(looks[label]))
                mesh.set_relative_scale3d(unreal.Vector(*[rng.uniform(0.85, 1.15)] * 3))
                for prop, value in {'item_definition': item, 'quantity': amount,
                                    'gathering_kind': getattr(unreal.EWHandGatheringKind, kind)}.items():
                    plant.set_editor_property(prop, value)
                placed += 1
        counts[label] = n
    return counts


if __name__ == '__main__':
    main()
