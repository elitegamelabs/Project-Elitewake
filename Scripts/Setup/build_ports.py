"""Build the five regional Ports (owner, October 15: CLAUDE.md).
Safe to run again. Run in the editor after build_coastal_terrain.py (which levels each Port's site), outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

One Port per region on the island world_layout.py picks (DECIDED, delegated: each region's largest island; the
Plains' largest besides the starter), its waterfront facing the world's centre. Each reads as a working coastal Port
in believable stone, never a copy of another:
  - a paved plaza on the levelled site and a stone quay running out over the shallows to deep water, with stairs down
    to the water at its head and bollards along it, and a timber pier beyond;
  - stone buildings round the plaza, of varied width, depth, height and roof, built of coursed masonry (blocks laid in
    courses with mortar joints, each block its own tone, the joints shadowed) with timber doors and shutters;
  - some of them shops or services (a hanging sign and a cloth awning over the door) and the rest plain houses and
    stores; which services they are is the owner's to set (vendors, names and safe-zone bounds stay open);
  - a town wall on the landward side with a gate tower, and a landmark tower by the water that marks the Port from
    the sea (a lantern burns at its top).
Regional character (DECIDED, delegated): Plains grey granite with red tile roofs; Desert warm sandstone, flat roofs
behind parapets; Winter pale granite under steep slate roofs carrying snow; Jungle mossy dark stone with deep
overhanging roofs; Swamp dark stone on raised plinths with shingle roofs. Sizes and counts are tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, make_timber_material, material_builder, write_static_mesh  # noqa: E402
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from build_coastal_flora import Ground  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Ports'
STONE, ROOF, WOOD, DARK, CLOTH = range(5)
LEVEL = T.PORT_LEVEL
STYLES = {
    'Plains': dict(stone=((.16, .155, .145), (.42, .4, .37)), roof=((.32, .09, .05), (.5, .17, .09)), roof_kind='gable',
                   pitch=.55, overhang=40, snow=0.0, cloth=(.55, .1, .08), moss=0.0, plinth=40),
    'Desert': dict(stone=((.33, .23, .13), (.6, .46, .3)), roof=((.45, .36, .25), (.6, .5, .36)), roof_kind='flat',
                   pitch=0.0, overhang=0, snow=0.0, cloth=(.1, .3, .45), moss=0.0, plinth=30),
    'Winter': dict(stone=((.2, .2, .21), (.5, .5, .5)), roof=((.06, .065, .075), (.13, .14, .16)), roof_kind='gable',
                   pitch=1.0, overhang=50, snow=1.0, cloth=(.15, .25, .45), moss=0.0, plinth=40),
    'Jungle': dict(stone=((.09, .1, .08), (.27, .28, .22)), roof=((.12, .09, .05), (.22, .17, .1)), roof_kind='gable',
                   pitch=.7, overhang=110, snow=0.0, cloth=(.45, .32, .06), moss=.7, plinth=50),
    'Swamp': dict(stone=((.07, .07, .07), (.22, .21, .19)), roof=((.1, .08, .06), (.2, .16, .11)), roof_kind='gable',
                  pitch=.65, overhang=60, snow=0.0, cloth=(.25, .35, .15), moss=.5, plinth=120),
}


# ---- Materials ------------------------------------------------------------------------------------------------

MASONRY = """
struct Mason {
  float h(float3 c) { return frac(sin(dot(c, float3(12.9898, 78.233, 37.719))) * 43758.5453); }
  float n(float3 q) { float3 i = floor(q), f = frac(q); f = f * f * (3 - 2 * f);
    return lerp(lerp(lerp(h(i), h(i + float3(1,0,0)), f.x), lerp(h(i + float3(0,1,0)), h(i + float3(1,1,0)), f.x), f.y),
                lerp(lerp(h(i + float3(0,0,1)), h(i + float3(1,0,1)), f.x), lerp(h(i + float3(0,1,1)), h(i + float3(1,1,1)), f.x), f.y), f.z); }
};
Mason m;
// Coursed masonry on whichever face this is: walls run along x or y, paving lies flat.
float3 an = abs(N);
float2 uv = an.z > .7 ? P.xy : (an.x > an.y ? P.yz : P.xz);
float course = an.z > .7 ? 55.0 : 32.0;
float row = floor(uv.y / course);
float shift = m.h(float3(row, 3.1, 0)) * 60.0;
float blen = 48.0 + 34.0 * m.h(float3(row, 7.7, 0));
float col = floor((uv.x + shift) / blen);
float2 f = float2(frac((uv.x + shift) / blen) * blen, frac(uv.y / course) * course);
float joint = min(min(f.x, blen - f.x), min(f.y, course - f.y));
float mortar = 1.0 - smoothstep(1.2, 3.2, joint);
float tone = m.h(float3(row, col, 1.7));
"""


def masonry_material(path, kind):
    """Coursed stone (kind 'stone') or roof tiles (kind 'roof'), coloured by parameters, in world space."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(path)
    material.set_editor_property('tangent_space_normal', False)
    position = node(unreal.MaterialExpressionWorldPosition)
    normal = node(unreal.MaterialExpressionVertexNormalWS)
    params = {n: node(unreal.MaterialExpressionVectorParameter, parameter_name=n, default_value=unreal.LinearColor(*v, 1))
              for n, v in (('Dark', (.16, .15, .14)), ('Light', (.42, .4, .37)))}
    params.update({n: node(unreal.MaterialExpressionScalarParameter, parameter_name=n, default_value=v)
                   for n, v in (('Snow', 0.0), ('Moss', 0.0))})
    if kind == 'stone':
        colour_code = MASONRY + """
float3 c = lerp(Dark, Light, tone) * lerp(.85, 1.1, m.n(P / 7.0));
c = lerp(c, Dark * .55, mortar);
float wet = saturate((-30.0 - P.z) / 120.0);
c *= lerp(1.0, .6, wet);
float moss = Moss * saturate(m.n(P / 60.0) * 2.2 - .7) * saturate(N.z * .5 + .6);
c = lerp(c, float3(.05, .09, .03), moss * .8);
c = lerp(c, float3(.8, .84, .9), Snow * saturate((N.z - .5) * 3.0));
return c;"""
        normal_code = MASONRY + """
// The joints are recessed: lean the surface toward the nearest joint across a narrow band.
float2 g = float2(f.x < blen - f.x ? -1 : 1, f.y < course - f.y ? -1 : 1);
float edge = 1.0 - smoothstep(0.0, 4.0, joint);
float3 tx = an.z > .7 ? float3(1,0,0) : (an.x > an.y ? float3(0,1,0) : float3(1,0,0));
float3 ty = an.z > .7 ? float3(0,1,0) : float3(0,0,1);
float3 lean = (f.x < f.y ? tx * g.x : ty * g.y) * edge * .45;
return normalize(N + lean * (1 - mortar * .5) + (m.n(P / 2.0) - .5) * .12 * (tx + ty));"""
    else:
        colour_code = MASONRY + """
// Roof tiles or slates: overlapping courses, each tile its own tone, the lower edges shadowed.
float3 c = lerp(Dark, Light, tone) * lerp(.85, 1.1, m.n(P / 9.0));
c *= lerp(.55, 1.0, smoothstep(0.0, 6.0, f.y));
c = lerp(c, float3(.82, .85, .9), Snow * saturate((N.z - .25) * 3.0) * saturate(m.n(P / 40.0) * 1.6 + .2));
c = lerp(c, float3(.05, .08, .03), Moss * saturate(m.n(P / 50.0) * 2.0 - .8) * .7);
return c;"""
        normal_code = "return N;"
    colour = custom(colour_code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'N', 'Dark', 'Light', 'Snow', 'Moss'))
    bumped = custom(normal_code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'N'))
    for pin, source in (('P', position), ('N', normal), ('Dark', params['Dark']), ('Light', params['Light']),
                        ('Snow', params['Snow']), ('Moss', params['Moss'])):
        assert mel.connect_material_expressions(source, '', colour, pin), pin
    for pin, source in (('P', position), ('N', normal)):
        assert mel.connect_material_expressions(source, '', bumped, pin), pin
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(bumped, '', unreal.MaterialProperty.MP_NORMAL)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.88), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


ROOF_SHADE = .6   # roofs face the sun; their tones are set darker than they read (tuning)


def instance(parent, name, values):
    mel = unreal.MaterialEditingLibrary
    path = f'{FOLDER}/{name}'
    mi = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, parent)
    for k, v in values.items():
        if isinstance(v, tuple):
            mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*v, 1))
        else:
            mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
    mel.update_material_instance(mi)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi


def flat_material(path, colour, rough=.8, glow=0.0):
    mel = unreal.MaterialEditingLibrary
    material, node, _ = material_builder(path)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(*colour, 1)), '',
                                         unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=rough), '', unreal.MaterialProperty.MP_ROUGHNESS)
    if glow:
        assert mel.connect_material_property(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(1.0 * glow, .7 * glow, .3 * glow, 1)), '',
                                             unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


# ---- Pieces (each in its own space: x forward out of the front, z up from the ground) ------------------------------

def gable_roof(b, w, d, z, pitch, overhang):
    """A pitched roof over a w (along x... front to back is x) by d box: the ridge runs across the front (along y)."""
    hx, hy = w / 2 + overhang, d / 2 + overhang
    rise = (w / 2 + overhang) * pitch
    b.slot = ROOF
    front_l, front_r, back_l, back_r = (hx, -hy, z), (hx, hy, z), (-hx, -hy, z), (-hx, hy, z)
    ridge_l, ridge_r = (0, -hy, z + rise), (0, hy, z + rise)
    ids = [b.vertex(p) for p in (front_l, front_r, ridge_r, ridge_l)]
    b.quad(*ids, (1, 0, 1))
    ids = [b.vertex(p) for p in (back_r, back_l, ridge_l, ridge_r)]
    b.quad(*ids, (-1, 0, 1))
    b.slot = STONE
    # Gable ends in stone.
    for side in (-1, 1):
        y = side * (d / 2)
        ids = [b.vertex(p) for p in ((w / 2, y, z), (-w / 2, y, z), (0, y, z + w / 2 * pitch))]
        b.tri(*ids, (0, side, 0))
    return rise


def house(w, d, storeys, style, shop, seed):
    """A stone building, front (with the door) facing +x. w along x (depth from the front), d across."""
    rng = random.Random(seed)
    b = Builder()
    height = storeys * 330
    plinth = style['plinth']
    b.slot = STONE
    b.box((0, 0, plinth / 2 - 60), (w + 30, d + 30, plinth + 120))       # the plinth, into the ground
    b.box((0, 0, plinth + height / 2), (w, d, height))
    # Quoins and a string course give the masonry some depth.
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((sx * (w / 2 + 4), sy * (d / 2 + 4), plinth + height / 2), (18, 18, height))
    for k in range(1, storeys):
        b.box((0, 0, plinth + k * 330), (w + 16, d + 16, 16))
    top = plinth + height
    if style['roof_kind'] == 'flat':
        b.slot = STONE
        for sx, sy, lx, ly in ((0, d / 2, w, 24), (0, -d / 2, w, 24), (w / 2, 0, 24, d), (-w / 2, 0, 24, d)):
            b.box((sx, sy, top + 45), (lx + 24, ly, 90))
        b.slot = ROOF
        b.box((0, 0, top + 6), (w - 20, d - 20, 12))
    else:
        rise = gable_roof(b, w, d, top, style['pitch'], style['overhang'])
        if rng.random() < .6:
            b.slot = STONE
            cy = rng.uniform(-d / 3, d / 3)
            b.box((-w / 4, cy, top + rise * .7), (70, 70, rise * 1.1))
    # Openings: dark recesses with timber frames; a door on the front.
    def opening(x, y, z, ow, oh, facing):
        nx, ny = facing
        b.slot = DARK
        b.box((x + nx * 2, y + ny * 2, z), ((6 if nx else ow), (6 if ny else ow), oh))
        b.slot = WOOD
        for off in (-1, 1):   # jambs
            b.box((x + nx * 5 + (0 if nx else off * ow / 2), y + ny * 5 + (off * ow / 2 if nx else 0), z), (10 if nx else 12, 12 if nx else 10, oh + 10))
        b.box((x + nx * 5, y + ny * 5, z + oh / 2 + 6), ((10 if nx else ow + 20), (ow + 20 if nx else 10), 12))   # lintel
    for k in range(storeys):
        z = plinth + k * 330 + 170
        across = max(1, int(d / 260))
        for j in range(across):
            y = -d / 2 + d * (j + .5) / across
            if k == 0 and j == across // 2:
                continue
            opening(w / 2, y, z, 90, 120, (1, 0))
            opening(-w / 2, y, z, 90, 120, (-1, 0))
        along = max(1, int(w / 300))
        for j in range(along):
            x = -w / 2 + w * (j + .5) / along
            opening(x, d / 2, z, 80, 110, (0, 1))
            opening(x, -d / 2, z, 80, 110, (0, -1))
    # The door, and steps up to it.
    b.slot = WOOD
    b.box((w / 2 + 4, 0, plinth + 125), (8, 120, 250))
    b.slot = STONE
    for k in range(max(1, int(plinth / 30))):
        b.box((w / 2 + 30 + 35 * k, 0, plinth - 30 * k - 15), (36, 170, 30))
    if shop:
        # A cloth awning over the door and a hanging sign on a bracket.
        b.slot = CLOTH
        ids = [b.vertex(p) for p in ((w / 2, -110, plinth + 300), (w / 2, 110, plinth + 300), (w / 2 + 150, 110, plinth + 250), (w / 2 + 150, -110, plinth + 250))]
        b.quad(*ids, (0, 0, 1))
        ids = [b.vertex(p) for p in ((w / 2, 110, plinth + 300), (w / 2, -110, plinth + 300), (w / 2 + 150, -110, plinth + 250), (w / 2 + 150, 110, plinth + 250))]
        b.quad(*ids, (0, 0, -1))
        b.slot = WOOD
        b.box((w / 2 + 60, 150, plinth + 330), (120, 8, 8))
        b.box((w / 2 + 100, 150, plinth + 285), (70, 6, 50))
    return b


def quay(length, width, deep):
    """A stone quay from the site's edge out over the water (x out to sea), its top at the site's level, its walls down
    to the sea floor; stairs down to the water at its head; bollards along both sides."""
    b = Builder()
    b.slot = STONE
    top = 0.0
    b.box((length / 2, 0, (top + deep) / 2), (length, width, top - deep))
    b.box((length / 2, 0, top + 30), (length, width + 40, 60 - 1))   # coping course
    for side in (-1, 1):
        for k in range(1, int(length / 800) + 1):
            b.cylinder((k * 800 - 400, side * (width / 2 - 40), top + 60), 18, 70, 10)
    # Stairs down to the water, along the head's left side.
    steps = 14
    for k in range(steps):
        b.box((length - 300 + 30 * k, -width / 2 - 90, top - 20 - 22 * k), (60, 180, 44))
    return b


def pier(length):
    """A timber pier on posts (x out to sea), deck at the quay's level."""
    b = Builder()
    b.slot = WOOD
    for k in range(int(length / 25)):
        b.box((k * 25 + 12, 0, 20), (22, 320, 8))
    for side in (-1, 1):
        b.box((length / 2, side * 150, 8), (length, 18, 16))
        for k in range(0, int(length / 300) + 1):
            b.box((k * 300 + 10, side * 150, -400), (26, 26, 860))
    return b


def wall_segment(length, height):
    """A length of town wall (along x), crenellated."""
    b = Builder()
    b.slot = STONE
    b.box((0, 0, height / 2 - 60), (length, 120, height + 120))
    merlons = int(length / 140)
    for k in range(merlons):
        if k % 2 == 0:
            b.box((-length / 2 + 70 + k * 140, 35, height + 45), (120, 50, 90))
    b.box((0, -10, height - 10), (length, 100, 20))
    return b


def gate_tower(style):
    """A square gate tower with an arched passage through it (along x)."""
    b = Builder()
    b.slot = STONE
    h = 900
    for side in (-1, 1):
        b.box((0, side * 260, h / 2 - 60), (520, 220, h + 120))
    b.box((0, 0, 560 + (h - 560) / 2), (520, 300, h - 560))
    for k in range(5):   # the arch, stepped
        b.box((0, 0, 400 + k * 32), (520, 300 - k * 50, 34))
    b.box((0, 0, h + 50), (580, 760, 100))
    if style['roof_kind'] == 'gable':
        gable_roof(b, 580, 760, h + 100, style['pitch'] * .8, 40)
    b.slot = WOOD
    b.box((-200, 0, 200), (16, 300, 400))   # the gate, open inward
    return b


def landmark(style, seed):
    """The Port's landmark tower by the water: a tall round stone tower with a gallery and a lantern room."""
    b = Builder()
    b.slot = STONE
    h = 1800 + random.Random(seed).uniform(0, 400)
    b.tube([(0, 0, -80), (0, 0, h * .5), (0, 0, h)], lambda k: (360, 300, 260)[k], sides=20)
    b.box((0, 0, h + 30), (680, 680, 60))
    for k in range(12):
        a = 2 * math.pi * k / 12
        b.box((310 * math.cos(a), 310 * math.sin(a), h + 110), (40, 40, 100))
    b.slot = DARK
    b.tube([(0, 0, h + 60), (0, 0, h + 300)], 170, sides=12)
    b.slot = ROOF
    b.tube([(0, 0, h + 300), (0, 0, h + 520)], lambda k: (230, 10)[k], sides=12)
    return b


def lantern():
    b = Builder()
    b.slot = 0
    b.tube([(0, 0, 0), (0, 0, 180)], 120, sides=12)
    return b


# ---- Placement --------------------------------------------------------------------------------------------------

def place(actors, mesh, x, y, z, yaw, label, folder, collide=True):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
    actor.set_actor_label(label)
    actor.set_folder_path(folder)
    comp = actor.static_mesh_component
    comp.set_static_mesh(mesh)
    if not collide:
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return actor


def build_port(actors, port, style, mats, ground):
    rng = random.Random(sum(map(ord, port.region)) * 271)
    folder = f'World/Ports/{port.region}'
    facing = math.degrees(port.facing)
    name = f'Port of the {port.region}'
    made = {'buildings': 0, 'shops': 0}
    slots = [mats['stone'], mats['roof'], mats['wood'], mats['dark'], mats['cloth']]

    def mesh(key, builder):
        path = f'{FOLDER}/SM_{port.region}_{key}_v1'
        return write_static_mesh(builder, path, slots, 120.0, split_angle=30.0)

    # The plaza: one paved slab over the site.
    paving = Builder()
    paving.slot = STONE
    # Down past the sea floor, so where the site meets the water it stands as a solid seawall, not a floating slab.
    paving.tube([(0, 0, -1500), (0, 0, 0)], W.PORT_PAD - 400, sides=40)
    place(actors, mesh('Plaza', paving), port.cx, port.cy, LEVEL + 4, facing, f'{name}: plaza', folder)
    # The quay from the site's seaward edge out over the shallows, and a timber pier beyond it.
    shore_along = W.PORT_INLAND
    q_len = 4200.0
    floor = min(ground(*port.world(shore_along + q_len * f, 0)) for f in (.5, 1.0))
    qx, qy = port.world(shore_along - 600, 0)
    place(actors, mesh('Quay', quay(q_len + 600, 900, floor - LEVEL - 200)), qx, qy, LEVEL, facing, f'{name}: quay', folder)
    px, py = port.world(shore_along + q_len, 0)
    place(actors, mesh('Pier', pier(2200)), px, py, LEVEL, facing, f'{name}: pier', folder)
    # Buildings round the plaza, fronts facing its middle; the shops nearest the waterfront.
    plots = []
    for k in range(9):
        a = math.radians(62 + 236 * k / 8 + rng.uniform(-6, 6))       # round the landward side, leaving the sea open
        r = rng.uniform(1900, 2600)
        plots.append((a, r))
    plots.sort(key=lambda p: -math.cos(p[0]))     # nearest the water first
    for k, (a, r) in enumerate(plots):
        along, across = r * math.cos(a), r * math.sin(a)
        w, d = rng.uniform(600, 900), rng.uniform(700, 1300)
        storeys = rng.choice((1, 2, 2, 3)) if port.region != 'Swamp' else rng.choice((1, 2))
        shop = k < 4
        house_mesh = mesh(f'House{k + 1}', house(w, d, storeys, style, shop, sum(map(ord, port.region)) + k))
        x, y = port.world(along, across)
        # Face the plaza's middle.
        yaw = math.degrees(math.atan2(port.cy - y, port.cx - x))
        place(actors, house_mesh, x, y, LEVEL, yaw, f'{name}: {"shop" if shop else "house"} {k + 1}', folder)
        made['buildings'] += 1
        made['shops'] += int(shop)
    # The town wall on the landward side with its gate tower.
    wall_mesh = mesh('Wall', wall_segment(1100, 450))
    for k in range(-4, 5):
        if k == 0:
            continue
        a = math.radians(180 + k * 17)
        along, across = (W.PORT_PAD - 150) * math.cos(a), (W.PORT_PAD - 150) * math.sin(a)
        x, y = port.world(along, across)
        z = max(LEVEL, ground(x, y))
        place(actors, wall_mesh, x, y, min(z, LEVEL + 150), facing + math.degrees(a) + 90, f'{name}: wall {k + 5}', folder)
    gx, gy = port.world(-(W.PORT_PAD - 150), 0)
    place(actors, mesh('Gate', gate_tower(style)), gx, gy, LEVEL, facing, f'{name}: gate tower', folder)
    # The landmark tower at the waterfront's corner, its lantern lit.
    lx, ly = port.world(shore_along - 500, 2600)
    tower = landmark(style, sum(map(ord, port.region)))
    place(actors, mesh('Tower', tower), lx, ly, LEVEL, facing, f'{name}: landmark tower', folder)
    top = max(v[2] for v in tower.verts)
    lamp = place(actors, mats['lantern_mesh'], lx, ly, LEVEL + top - 450, 0, f'{name}: lantern', folder, collide=False)
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(lx, ly, LEVEL + top - 350))
    light.set_actor_label(f'{name}: lantern light')
    light.set_folder_path(folder)
    lc = light.get_component_by_class(unreal.PointLightComponent)
    lc.set_editor_property('intensity', 8000.0)
    lc.set_editor_property('attenuation_radius', 4000.0)
    lc.set_editor_property('light_color', unreal.Color(255, 190, 120, 255))
    return made


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    stone_parent = masonry_material(f'{FOLDER}/M_PortStone_v1', 'stone')
    roof_parent = masonry_material(f'{FOLDER}/M_PortRoof_v1', 'roof')
    timber = make_timber_material()
    dark = flat_material(f'{FOLDER}/M_PortDark_v1', (.012, .011, .01), .9)
    lantern_mat = flat_material(f'{FOLDER}/M_PortLantern_v1', (.9, .7, .4), .5, glow=30.0)
    lantern_mesh = write_static_mesh(lantern(), f'{FOLDER}/SM_PortLantern_v1', [lantern_mat], 120.0, collision=False)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()).startswith('World/Ports') and not str(actor.get_folder_path()).startswith('World/Ports/Plains'):
            actors.destroy_actor(actor)
    ground = Ground()
    report = {}
    for region, port in W.PORTS.items():
        if region == 'Plains':
            continue   # Saltreach Freeport stands on the Plains Port's site (owner, October 30; build_freeport.py)
        style = STYLES[region]
        mats = {'stone': instance(stone_parent, f'MI_PortStone_{region}_v1', {'Dark': style['stone'][0], 'Light': style['stone'][1],
                                                                               'Snow': style['snow'], 'Moss': style['moss']}),
                'roof': instance(roof_parent, f'MI_PortRoof_{region}_v1', {'Dark': tuple(c * ROOF_SHADE for c in style['roof'][0]),
                                                                            'Light': tuple(c * ROOF_SHADE for c in style['roof'][1]),
                                                                            'Snow': style['snow'], 'Moss': style['moss']}),
                'wood': timber, 'dark': dark,
                'cloth': flat_material(f'{FOLDER}/M_PortCloth_{region}_v1', style['cloth'], .9),
                'lantern_mesh': lantern_mesh}
        made = build_port(actors, port, style, mats, ground)
        report[region] = {'island': port.island.key, 'facing_deg': round(math.degrees(port.facing)),
                          'site_m': [round(port.cx / 100), round(port.cy / 100)], **made}
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'PortsResult.json').write_text(json.dumps({'success': True, 'ports': report}, indent=2))
    unreal.log('Ports built')


if __name__ == '__main__':
    main()
