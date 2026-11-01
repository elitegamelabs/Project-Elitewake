"""Build Saltreach Freeport, the starting hub (owner, October 30: an explorable, working Freeport harbor town; ATLAS-inspired in
gameplay only, nothing copied). It replaces the Plains starter Port (build_ports.py and add_port_merchants.py now skip the Plains).
Safe to run again. Run in the editor outside Play, after build_ports.py and add_port_merchants.py:
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -nullrhi -run=pythonscript -script=<this file>

The site is the Plains Port's: a levelled terrace in a bay on the starter island's south-west shore, a low headland on its left
running out to sea as a natural breakwater, the open channel ahead. In the Port's frame (along = out to sea, across = to the right):
  - The harbor: a stone seawall round the terrace and a timber wharf along its front; the long pier running out to deep water with
    three berths; a fishing jetty off the right side with two small-boat berths; mooring bollards, ladders, cargo, nets and pots;
    a channel beacon either side of the harbor mouth and a timber lighthouse on the headland, lit at night.
  - The marketplace: two rows of stalls across the high street (resource trader, provisioner, outfitter, a fish stall and a
    fruit stall), goods on show.
  - The tavern, The Salt Lantern: at the head of the town square, walked into; a bar, shelves of bottles, casks, a hearth,
    tables and stools, lanterns, a veranda with tables, the keeper behind the bar, patrons in and out.
  - The shipyard: a slipway running into the harbor, a shed over a hull in frame on the building cradle, the workshop, timber,
    the shipwright.
  - The crew hiring office by the jetty, the recruiter on its porch; the harbor master's office at the root of the long pier.
  - The town square: a well, the notice board, benches, palms and lamps, boardwalk lanes joining every place.
  - Houses and a warehouse round the edge, palms through the town, townsfolk at work and walking their rounds.
  - The safe zone over town and harbor (AEWSafeZone): no fighting, no building, no hostile creatures.
Names, prices, stock, rumours and jobs are placeholders for the owner. Every size is tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import freeport_pieces as F  # noqa: E402
from ship_geometry import make_timber_material, material_builder, write_static_mesh  # noqa: E402
from build_ports import masonry_material, flat_material  # noqa: E402
from build_coastal_flora import Ground  # noqa: E402
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Freeport'
OUT = 'World/Freeport'
NAME = 'Saltreach Freeport'
LEVEL = T.PORT_LEVEL
SEA = T.SEA
TOWN = LEVEL + 5         # the street's top
DECK = LEVEL + 10        # the piers' and wharf's deck
ITEMS = '/Game/Elitewake/Items'
MANNY = '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple'
QUINN = '/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple'
IDLE = '/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle'
WALK = '/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd'

port = W.PORTS['Plains']
FACING = math.degrees(port.facing)
actors = None
ground = None
report = {'meshes': 0, 'placed': 0, 'lights': 0, 'npcs': [], 'removed': []}


# ---- Materials ------------------------------------------------------------------------------------------------------

NOISE = """
struct Fp {
  float h(float2 c) { return frac(sin(dot(c, float2(12.9898, 78.233))) * 43758.5453); }
  float n(float2 q) { float2 i = floor(q), f = frac(q); f = f * f * (3 - 2 * f);
    return lerp(lerp(h(i), h(i + float2(1,0)), f.x), lerp(h(i + float2(0,1)), h(i + float2(1,1)), f.x), f.y); }
};
Fp t;
"""


def custom_material(path, code, rough=.9):
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(path)
    colour = custom(NOISE + code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'N'))
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionWorldPosition), '', colour, 'P')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionVertexNormalWS), '', colour, 'N')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=rough), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


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


def townsfolk_material():
    """Plain clothes on the engine mannequin, painted by height on the body's rest pose (boots, breeches, a sash, a shirt with
    sleeves, bare hands and head, hair): placeholder townsfolk until the owner's character art."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Townsfolk_v1')
    material.set_editor_property('used_with_skeletal_mesh', True)
    names = ('Skin', 'Shirt', 'Trousers', 'Boots', 'Hair', 'Sash')
    defaults = ((.6, .4, .3), (.7, .66, .55), (.25, .2, .14), (.06, .045, .03), (.08, .05, .03), (.45, .08, .05))
    params = [node(unreal.MaterialExpressionVectorParameter, parameter_name=n, default_value=unreal.LinearColor(*d, 1)) for n, d in zip(names, defaults)]
    code = """
float ax = abs(P.x);
float3 c = Shirt;
if (P.z < 14) c = Boots;
else if (P.z < 90) c = Trousers;
else if (P.z < 100) c = Sash;
if (P.z > 150) c = Skin;
if (ax > 50 && P.z > 55 && P.z < 128) c = Skin;
if (P.z > 168 || (P.z > 158 && P.y < -5)) c = Hair;
float fold = frac(sin(dot(floor(P.xy / 6 + P.z / 9), float2(12.9898, 78.233))) * 43758.5453);
return c * lerp(.92, 1.04, fold);"""
    colour = custom(code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P',) + names)
    # The rest-pose position exists only in the vertex shader: carried to the pixels through an interpolator.
    rest = node(unreal.MaterialExpressionVertexInterpolator)
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionPreSkinnedPosition), '', rest, '')
    assert mel.connect_material_expressions(rest, '', colour, 'P')
    for n, p in zip(names, params):
        assert mel.connect_material_expressions(p, '', colour, n)
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.8), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def make_materials():
    stone = instance(masonry_material(f'{FOLDER}/M_FreeportStone_v1', 'stone'), 'MI_FreeportStone_v1',
                     {'Dark': (.2, .185, .15), 'Light': (.56, .51, .42), 'Snow': 0.0, 'Moss': .3})
    thatch = custom_material(f'{FOLDER}/M_FreeportThatch_v1', """
float2 across = normalize(float2(-N.y, N.x) + 1e-4);
float u = dot(P.xy, across);
float s = t.n(float2(u / 3.0, P.z / 45.0));
float s2 = t.n(float2(u / 13.0, P.z / 120.0 + 5.0));
float3 c = lerp(float3(.16, .12, .06), float3(.46, .37, .19), s * .55 + s2 * .45);
c *= lerp(.68, 1.0, smoothstep(0.0, .3, frac(P.z / 38.0 + s2 * .2)));
return c;""", .95)
    plaster = custom_material(f'{FOLDER}/M_FreeportPlaster_v1', """
float n1 = t.n(P.xy / 60.0 + P.z / 45.0), n2 = t.n(P.yx / 9.0 + P.z / 11.0);
float3 c = lerp(float3(.36, .34, .3), float3(.5, .48, .43), n1);
c = lerp(c, c * .72, smoothstep(.62, .95, n2) * .5);
return c;""", .92)
    street = custom_material(f'{FOLDER}/M_FreeportStreet_v1', """
float n1 = t.n(P.xy / 140.0), n2 = t.n(P.xy / 26.0 + 7.0), n3 = t.n(P.xy / 5.0 + 3.0);
float3 c = lerp(float3(.25, .2, .14), float3(.14, .11, .075), saturate(n1 * 1.4 - .25));
c *= lerp(.84, 1.08, n2);
c = lerp(c, c * .55, step(.86, n3) * .7);
return c;""", .96)
    return {
        'stone': stone, 'thatch': thatch, 'wood': make_timber_material(), 'plaster': plaster, 'street': street,
        'dark': flat_material(f'{FOLDER}/M_FreeportIron_v1', (.02, .019, .018), .6),
        'cloth': flat_material(f'{FOLDER}/M_FreeportCloth1_v1', (.2, .025, .015), .95),
        'cloth2': flat_material(f'{FOLDER}/M_FreeportCloth2_v1', (.3, .16, .025), .95),
        'cloth3': flat_material(f'{FOLDER}/M_FreeportCloth3_v1', (.015, .08, .1), .95),
        'rope': flat_material(f'{FOLDER}/M_FreeportRope_v1', (.3, .23, .13), .97),
        'glow': flat_material(f'{FOLDER}/M_FreeportLantern_v1', (.9, .7, .4), .5, glow=8.0),
        'townsfolk': townsfolk_material(),
    }


# ---- Placement --------------------------------------------------------------------------------------------------------

def slots(m, street=False):
    """Material per builder slot (freeport_pieces: STONE THATCH WOOD DARK CLOTH PLASTER ROPE GLOW CLOTH2 CLOTH3)."""
    return [m['stone'], m['thatch'], m['wood'], m['dark'], m['cloth'], m['street'] if street else m['plaster'],
            m['rope'], m['glow'], m['cloth2'], m['cloth3']]


MESHES = {}


def mesh(key, builder, m, collision=True, street=False):
    if key not in MESHES:
        MESHES[key] = write_static_mesh(builder, f'{FOLDER}/SM_Freeport_{key}_v1', slots(m, street), 120.0, collision=collision, split_angle=35.0)
        report['meshes'] += 1
    return MESHES[key]


def world(a, c):
    return port.world(a, c)


def yaw_to(a, c, ta, tc):
    """The local yaw (degrees) that turns a piece at (a, c) to face (ta, tc)."""
    return math.degrees(math.atan2(tc - c, ta - a))


def snap(yaw):
    return round(yaw / 90.0) * 90.0


def put(m, key, builder_fn, a, c, z, yaw, label, collide=True, scale=1.0, street=False):
    sm = mesh(key, builder_fn(), m, collision=collide, street=street)
    x, y = world(a, c)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator(0, 0, FACING + yaw))
    actor.set_actor_label(f'{NAME}: {label}')
    actor.set_folder_path(OUT)
    comp = actor.static_mesh_component
    comp.set_static_mesh(sm)
    if scale != 1.0:
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if not collide:
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    report['placed'] += 1
    return actor


def ground_z(a, c):
    """The street on the terrace, else the island's ground."""
    if math.hypot(a, c) < 3650:
        return TOWN
    return ground(*world(a, c))


def walk_z(a, c):
    """The deck where (a, c) is on the wharf, the long pier or the jetty; otherwise the ground."""
    on_wharf = 3480 < a < 4420 and -1260 < c < 3460
    on_pier = 4380 < a < 9820 and abs(c - 1800) < 270
    on_jetty = 100 < a < 500 and 3600 < c < 7760
    return DECK if (on_wharf or on_pier or on_jetty) else ground_z(a, c)


def light(a, c, z, intensity=2600.0, radius=1300.0, colour=(255, 178, 105), label='lamp'):
    x, y = world(a, c)
    actor = actors.spawn_actor_from_class(unreal.EWNightLight, unreal.Vector(x, y, z))
    actor.set_actor_label(f'{NAME}: {label} light')
    actor.set_folder_path(OUT)
    lc = actor.get_component_by_class(unreal.PointLightComponent)
    lc.set_editor_property('intensity', intensity)
    lc.set_editor_property('attenuation_radius', radius)
    lc.set_editor_property('light_color', unreal.Color(r=colour[0], g=colour[1], b=colour[2], a=255))
    lc.set_editor_property('cast_shadows', False)
    report['lights'] += 1
    return actor


def lamp(m, a, c, label, lit=True):
    z = ground_z(a, c)
    put(m, 'LanternPost', F.lantern_post, a, c, z, 0, label)
    if lit:
        # The lantern hangs 50 cm out along the post's arm (local +x, along the harbor's axis here).
        light(a + 50, c, z + 240, label=label)


# ---- People -----------------------------------------------------------------------------------------------------------

def clothes(key, skin, shirt, trousers, boots=(.05, .04, .03), hair=(.06, .04, .025), sash=(.4, .08, .05)):
    # Cloth reads twice as light as its value under the game's sun: set darker (tuning).
    dye = lambda c, k=.5: tuple(v * k for v in c)
    return instance(MATS['townsfolk'], f'MI_Townsfolk_{key}_v1', {'Skin': dye(skin, .7), 'Shirt': dye(shirt), 'Trousers': dye(trousers),
                                                                   'Boots': boots, 'Hair': hair, 'Sash': dye(sash)})


SKIN = [(.6, .41, .3), (.42, .27, .17), (.22, .13, .08), (.68, .5, .4), (.12, .07, .045), (.5, .33, .22)]


def person(cls, key, a, c, yaw, name, role, greeting='', talk=(), body='m', look=None, stroll=(), z=None):
    x, y = world(a, c)
    zz = walk_z(a, c) if z is None else z
    actor = actors.spawn_actor_from_class(cls, unreal.Vector(x, y, zz), unreal.Rotator(0, 0, FACING + yaw))
    actor.set_actor_label(f'{NAME}: {name}')
    actor.set_folder_path(OUT)
    actor.set_editor_property('npc_name', unreal.Text(name))
    actor.set_editor_property('role_title', unreal.Text(role))
    if greeting:
        actor.set_editor_property('greeting', unreal.Text(greeting))
    actor.set_editor_property('small_talk', [unreal.Text(s) for s in talk])
    if body:
        actor.set_editor_property('figure_mesh', unreal.load_asset(MANNY if body == 'm' else QUINN))
        actor.set_editor_property('figure_material', look)
        actor.set_editor_property('idle_anim', unreal.load_asset(IDLE))
        actor.set_editor_property('walk_anim', unreal.load_asset(WALK))
    if stroll:
        points = []
        for pa, pc in stroll:
            px, py = world(pa, pc)
            pz = walk_z(pa, pc)
            points.append(unreal.Vector(px, py, pz))
        actor.set_editor_property('stroll_points', points)
    report['npcs'].append({'name': name, 'role': role, 'class': cls.__name__, 'at': [round(a), round(c)]})
    return actor


def goods(path, bundle, price, stock):
    line = unreal.EWMerchantGoods()
    item = unreal.load_asset(f'{ITEMS}/{path}')
    assert item, path
    line.set_editor_property('item', item)
    line.set_editor_property('bundle', bundle)
    line.set_editor_property('price_copper', price)
    line.set_editor_property('max_stock', stock)
    return line


def transform(a, c, z, yaw):
    x, y = world(a, c)
    return unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(0, 0, FACING + yaw), unreal.Vector(1, 1, 1))


# ---- The town ---------------------------------------------------------------------------------------------------------

def clear_site():
    """The old Plains Port (its stone plaza, quay, houses, wall and tower, its merchant and crew masters), anything left from an
    earlier run, and plants, rocks and gatherables standing where the town is built."""
    plains_labels = ('Port Merchant Plains', 'Port Crew Master Plains', 'Port Gunnery Master Plains')
    loose = tuple(c for c in (getattr(unreal, n, None) for n in ('EWHarvestTree', 'EWHandGatherable', 'EWResourceNode', 'EWMineable')) if c)
    cx, cy = port.cx, port.cy
    lx, ly = world(5600, -4200)
    for actor in actors.get_all_level_actors():
        folder = str(actor.get_folder_path())
        label = actor.get_actor_label()
        drop = folder.startswith('World/Ports/Plains') or folder.startswith(OUT) or label in plains_labels
        if not drop and isinstance(actor, loose):
            p = actor.get_actor_location()
            a, c = port.local(p.x, p.y)
            drop = math.hypot(p.x - cx, p.y - cy) < 4700 or math.hypot(p.x - lx, p.y - ly) < 700 or (a > 2500 and -3600 < c < 8000 and a < 12000 and p.z < SEA + 300)
        if drop:
            report['removed'].append(label)
            actors.destroy_actor(actor)


def build_ground(m):
    put(m, 'Ground', lambda: F.ground_disc(3700, 1500), 0, 0, TOWN, 0, 'streets and seawall', street=True)
    # Boardwalk lanes: high street from the tavern to the wharf, the market lane across it, and paths to the jetty, the
    # houses and the shipyard. Each a little higher than the last so crossings do not flicker.
    lanes = [((-1500, -200), (3550, -200), 420), ((2000, -1200), (2000, 1500), 360), ((300, 300), (350, 3550), 300),
             ((-1100, 300), (-2300, 2200), 260), ((-200, -700), (1300, -2300), 280), ((2600, 0), (3550, 1500), 300)]
    for k, ((a0, c0), (a1, c1), width) in enumerate(lanes):
        length = math.hypot(a1 - a0, c1 - c0)
        put(m, f'Lane{k + 1}', lambda: F.boardwalk(length, width, k), (a0 + a1) / 2, (c0 + c1) / 2, TOWN + k * .8,
            math.degrees(math.atan2(c1 - c0, a1 - a0)), f'boardwalk {k + 1}')


def build_harbor(m):
    # The wharf along the terrace's front (laid along +across), the long pier to deep water, the fishing jetty off the right.
    def depth(a, c):
        return DECK - ground(*world(a, c))
    put(m, 'Wharf', lambda: F.pier(4700, 900, (depth(3950, -1200), depth(3950, 3500)), 11, ladders=((1400, 1), (3600, 1))),
        3950, -1250, DECK, 90, 'wharf')
    put(m, 'LongPier', lambda: F.pier(5400, 520, (depth(4400, 1800), depth(9800, 1800)), 12, ladders=((1500, 1), (3800, 1), (4600, -1))),
        4400, 1800, DECK, 0, 'long pier')
    put(m, 'Jetty', lambda: F.pier(4100, 360, (depth(300, 3650), depth(300, 7700)), 13, ladders=((1700, 1), (3300, 1))),
        300, 3650, DECK, 90, 'fishing jetty')
    # Mooring posts standing in the water off the berths, for the lines.
    for a, c in ((5200, 3300), (7600, 3700), (9000, 3700), (8600, 300), (1400, 5000), (1400, 7400)):
        put(m, 'MooringPost', F.mooring_post, a, c, DECK - 20, 0, 'mooring post')
    # Channel beacons either side of the harbor mouth and the lighthouse on the headland.
    for k, (a, c) in enumerate(((10800, -2000), (10800, 4400))):
        put(m, 'Beacon', F.beacon, a, c, SEA, 0, f'channel beacon {k + 1}')
        light(a, c, SEA + 930, 9000.0, 3500.0, label=f'channel beacon {k + 1}')
    lz = ground_z(5600, -4200)
    put(m, 'Lighthouse', F.lighthouse, 5600, -4200, lz, 0, 'lighthouse')
    light(5600, -4200, lz + 1500 + 300, 6000.0, 5000.0, label='lighthouse')
    # Cargo, coils, pots and nets along the waterfront.
    for k, (a, c, z) in enumerate(((4150, -700, DECK), (4200, 700, DECK), (4150, 2900, DECK), (6000, 1960, DECK), (8700, 1960, DECK),
                                   (2900, 1100, TOWN), (2850, -1100, TOWN))):
        put(m, f'Cargo{k % 4}', lambda: F.cargo_pile(k % 4), a, c, z, random.Random(k).uniform(0, 360), f'cargo {k + 1}')
    for k, (a, c) in enumerate(((4300, 1960), (7200, 1950), (9500, 1650), (420, 5600), (4300, -400))):
        put(m, 'RopeCoil', F.rope_coil, a, c, DECK, k * 70, f'rope coil {k + 1}')
    for k, (a, c) in enumerate(((400, 4500), (400, 6900))):
        put(m, f'Pots{k}', lambda: F.lobster_pots(k), a, c, DECK, k * 40, f'lobster pots {k + 1}')
    put(m, 'NetRack', F.net_rack, -500, 3300, TOWN, 90, 'net rack 1')
    put(m, 'NetRack', F.net_rack, 900, 3520, TOWN, 80, 'net rack 2')
    # Boats: two rowboats lying off the jetty, two fishing boats at anchor in the bay.
    for k, (a, c, yaw, kind) in enumerate(((-260, 5100, 92, 'row'), (-280, 6300, 86, 'row'), (2900, 6700, 30, 'fish'), (6600, 5600, -20, 'fish'))):
        if kind == 'row':
            put(m, 'Rowboat', lambda: F.rowboat(420, 140, 55, 1), a, c, SEA - 18, yaw, f'rowboat {k + 1}')
        else:
            put(m, 'FishingBoat', lambda: F.rowboat(780, 250, 95, 2, mast=True), a, c, SEA - 30, yaw, f'fishing boat {k + 1}')
    # Lamps along the waterfront and piers.
    for k, (a, c) in enumerate(((3620, -900), (3620, 900), (3620, 2700), (9600, 2050), (6600, 2050), (420, 7600))):
        z = walk_z(a, c)
        put(m, 'LanternPost', F.lantern_post, a, c, z, 0, f'waterfront lamp {k + 1}')
        light(a + 50, c, z + 240, label=f'waterfront lamp {k + 1}')
    # Benches along the high street, facing it.
    for k, (a, c, yaw) in enumerate(((2650, -650, 90), (2650, 950, -90))):
        put(m, 'Bench', F.bench, a, c, TOWN, yaw, f'high street bench {k + 1}')


def build_town(m):
    # The tavern at the head of the square, facing down the high street to the harbor.
    put(m, 'Tavern', lambda: F.tavern(7), -2500, -200, TOWN, 0, 'The Salt Lantern (tavern)')
    for lx, ly, lz in ((150, -300, 380 - 105), (150, 300, 380 - 105), (-200, 0, 380 - 105)):
        light(-2500 + lx, -200 + ly, TOWN + 44 + lz - 40, 1800.0, 900.0, label='tavern lantern')
    light(-2500 - 650 + 200, -200 - 750 + 100, TOWN + 80, 2200.0, 700.0, colour=(255, 120, 50), label='tavern hearth')
    light(-2500 + 650 + 300 + 110, -200 - 750 + 30, TOWN + 320, 1200.0, 600.0, label='tavern sign')
    # The square: the well, the notice board, benches, lamps.
    put(m, 'Well', F.well, -600, -900, TOWN, 0, 'well')
    put(m, 'NoticeBoard', F.notice_board, -400, 520, TOWN, yaw_to(-400, 520, -600, -200), 'notice board')
    for k, (a, c, yaw) in enumerate(((-1100, -1300, 60), (-100, -1250, 120), (-1550, 700, -60))):
        put(m, 'Bench', F.bench, a, c, TOWN, yaw, f'square bench {k + 1}')
    for k, (a, c) in enumerate(((-1300, -600), (200, 400), (1200, -500), (-900, 1600))):
        lamp(m, a, c, f'street lamp {k + 1}')
    # The market: two rows of stalls facing each other across the market lane.
    stalls = {}
    for key, a, c, yaw, kinds in (('Resources', 1650, -800, 0, ('resources',)), ('Fish', 1650, 500, 0, ('fish',)),
                                  ('Provisions', 2350, -800, 180, ('crates', 'fruit')), ('Outfitter', 2350, 500, 180, ('cloth',)),
                                  ('Fruit', 2350, 1350, 180, ('fruit',))):
        put(m, f'Stall{key}', lambda: F.stall(len(stalls) + 3, goods=kinds), a, c, TOWN, yaw, f'market stall: {key.lower()}')
        stalls[key] = (a, c, yaw)
    for k, (a, c) in enumerate(((1700, -1500), (2300, 1900), (1650, 1350))):
        put(m, f'Cargo{k % 4}', lambda: F.cargo_pile(k % 4), a, c, TOWN, k * 50, f'market goods {k + 1}')
    # Houses, the warehouse, the hiring office and the harbor master's office round the edge.
    buildings = [('HouseA', -1900, 2400, 750, 900, 2, 'thatch', False, False), ('HouseB', -3000, 1350, 650, 800, 1, 'thatch', True, False),
                 ('HouseC', -1500, -2650, 700, 950, 2, 'shingle', False, False), ('HouseD', -2950, -1750, 600, 750, 1, 'thatch', True, False),
                 ('Warehouse', 1250, 2950, 900, 1300, 1, 'shingle', False, False), ('HiringOffice', -250, 2750, 650, 850, 1, 'thatch', False, True),
                 ('HarborOffice', 2650, 2650, 700, 800, 2, 'shingle', True, True), ('Workshop', 500, -3000, 800, 1000, 1, 'shingle', False, True)]
    placed = {}
    for key, a, c, w, d, storeys, roof, plaster, porch in buildings:
        target = (2000, 0) if key == 'HarborOffice' else (-600, -200)
        yaw = snap(yaw_to(a, c, *target))
        put(m, key, lambda: F.house(w, d, storeys, len(placed) + 21, roof=roof, plaster=plaster, porch=porch, sign=porch), a, c, ground_z(a, c), yaw,
            key.replace('House', 'house ').replace('Office', ' office').lower())
        placed[key] = (a, c, yaw, w)
    put(m, 'Flagpole', F.flagpole, 2650 + 520, 2650 + 300, TOWN, 0, 'harbor flag')
    put(m, 'Flagpole', F.flagpole, -150, -700, TOWN, 0, 'square flag')
    return stalls, placed


def build_shipyard(m):
    yz = ground_z(2200, -2700)
    put(m, 'ShipShed', lambda: F.ship_shed(2200, 1150, 820), 2200, -2700, yz, 0, 'ship shed')
    put(m, 'ShipFrame', F.ship_frame, 2200, -2700, yz, 0, 'hull in frame')
    put(m, 'Slipway', lambda: F.slipway(3600, 380), 3300, -1500, TOWN, 0, 'slipway')
    for k, (a, c) in enumerate(((900, -3500), (3300, -3300))):
        put(m, f'Cargo{(k + 2) % 4}', lambda: F.cargo_pile((k + 2) % 4), a, c, ground_z(a, c), k * 90, f'shipyard stores {k + 1}')
    lamp(m, 3000, -2200, 'shipyard lamp')


def build_palms(m):
    meshes = [unreal.load_asset(f'/Game/Elitewake/World/Flora/SM_VeyranPalm_{k}') for k in (1, 2, 3)]
    rng = random.Random(91)
    spots = [(-1150, -950), (-80, 650), (-1350, 300), (250, -1000), (-3450, 500), (-2100, 3300), (-3500, -900), (1100, -1500),
             (3600, -2900), (4600, -3600), (700, 3600), (-1000, -3300), (1700, 2350), (-3300, 2200), (-2600, 3000), (-700, 2000)]
    for k, (a, c) in enumerate(spots):
        x, y = world(a, c)
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, ground_z(a, c) - 10), unreal.Rotator(0, 0, rng.uniform(0, 360)))
        actor.set_actor_label(f'{NAME}: palm {k + 1}')
        actor.set_folder_path(OUT)
        actor.static_mesh_component.set_static_mesh(meshes[k % 3])
        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        s = rng.uniform(.8, 1.15)
        actor.set_actor_scale3d(unreal.Vector(s, s, s))
        report['placed'] += 1


def build_people(stalls, placed, ship_class):
    global MATS
    tavern_floor = TOWN + 44

    def at(stall, x):
        a, c, yaw = stalls[stall]
        r = math.radians(yaw)
        return a + x * math.cos(r), c + x * math.sin(r), yaw

    # Merchants inside their stalls.
    a, c, yaw = at('Resources', -40)
    trader = person(unreal.EWMerchant, 'Trader', a, c, yaw, 'Oskar Brann', 'Resource Trader',
                    'Timber, stone, fibre, hide and ore, bought and sold by the bundle. What do you need, or what have you brought?',
                    ('Wood fetches more after a storm.', 'Ore from the hills is worth carrying. Ore from a wreck is worth more.'),
                    'm', clothes('Trader', SKIN[1], (.32, .22, .12), (.18, .14, .1), sash=(.2, .12, .05)))
    trader.set_editor_property('goods', [goods('Testing/DA_TestWood', 10, 30, 8), goods('Testing/DA_TestStone', 10, 30, 8),
                                         goods('Testing/DA_TestFiber', 10, 15, 8), goods('Testing/DA_TestThatch', 10, 15, 8),
                                         goods('Testing/DA_TestHide', 2, 25, 5), goods('Testing/DA_TestOre', 2, 40, 5)])
    a, c, yaw = at('Provisions', -40)
    provisioner = person(unreal.EWMerchant, 'Provisioner', a, c, yaw, 'Marta Vell', 'Provisioner',
                         'Shot, kits, food and water for the crossing. Nobody sails from Saltreach hungry if they can pay.',
                         ('Salt the fish before you sail, or eat it first.', 'A repair kit has saved more ships than prayer.'),
                         'f', clothes('Provisioner', SKIN[0], (.6, .55, .45), (.3, .16, .1), sash=(.1, .25, .28)))
    provisioner.set_editor_property('goods', [goods('Testing/DA_TestRoundShot', 5, 50, 6), goods('Testing/DA_TestRepairKit', 1, 60, 4),
                                              goods('Food/DA_CookedFish', 1, 15, 8), goods('Food/DA_MedicinalHerb', 1, 25, 5),
                                              goods('Testing/DA_TestHideWaterFlask', 1, 15, 3)])
    a, c, yaw = at('Outfitter', -40)
    outfitter = person(unreal.EWMerchant, 'Outfitter', a, c, yaw, 'Lucia Fane', 'Outfitter',
                       'Hats, colours and finery for a captain who wants to be remembered. Have a look.',
                       ('A good hat is half a captain.', 'White colours on a mast mean you want to talk. Mostly.'),
                       'f', clothes('Outfitter', SKIN[2], (.42, .07, .05), (.08, .07, .09), hair=(.02, .015, .01), sash=(.55, .34, .07)))
    outfitter.set_editor_property('goods', [goods('Testing/DA_TestHat', 1, 80, 3), goods('Testing/DA_TestHatAlternate', 1, 95, 3),
                                            goods('Testing/DA_TestFlagWhite', 1, 60, 2)])
    for merchant in (trader, provisioner, outfitter):
        merchant.set_editor_property('build_stall', False)
        merchant.set_editor_property('restock_seconds', 300.0)
    # The crew recruiter on the hiring office's porch.
    a, c, yaw, w = placed['HiringOffice']
    r = math.radians(yaw)
    recruiter = person(unreal.EWCrewMaster, 'Recruiter', a + (w / 2 + 130) * math.cos(r), c + (w / 2 + 130) * math.sin(r), yaw,
                       'Gideon Rusk', 'Crew Recruiter',
                       'Sailors and gunners looking for a berth. Pick who you like; their articles go aboard with you.',
                       ('Pay your crew and they stay. Mostly.', 'A gunner is worth two hands on the lines, when it comes to it.'),
                       'm', clothes('Recruiter', SKIN[4], (.12, .15, .25), (.2, .17, .12), sash=(.55, .34, .07)))
    recruiter.set_editor_property('articles', unreal.load_asset(f'{ITEMS}/Crew/DA_SailhandArticles'))
    recruiter.set_editor_property('gunner_articles', unreal.load_asset(f'{ITEMS}/Crew/DA_GunnerArticles'))
    recruiter.set_editor_property('hire_cost', 100)
    recruiter.set_editor_property('gunner_hire_cost', 150)
    recruiter.set_editor_property('build_stall', False)
    # The harbor master on her office porch.
    a, c, yaw, w = placed['HarborOffice']
    r = math.radians(yaw)
    master = person(unreal.EWHarborMaster, 'HarborMaster', a + (w / 2 + 130) * math.cos(r), c + (w / 2 + 130) * math.sin(r), yaw,
                    'Captain Ines Calder', 'Harbor Master',
                    'Welcome to Saltreach. Free port, free trade, no quarrels inside the beacons. Need a berth, or clearing out?',
                    ('Mind the headland on the way in; the rocks run out further than they look.',),
                    'f', clothes('HarborMaster', SKIN[3], (.08, .1, .2), (.08, .1, .2), hair=(.2, .2, .2), sash=(.6, .5, .2)))
    berths = []
    for name, a2, c2, yaw2, length in (('the long pier, east berth', 5900, 2650, 0, 2600), ('the long pier, outer east berth', 8300, 3000, 0, 4200),
                                       ('the long pier, west berth', 8500, 950, 0, 2600), ('the fishing jetty, inner berth', 950, 5300, 90, 1000),
                                       ('the fishing jetty, outer berth', 950, 7000, 90, 1000)):
        berth = unreal.EWBerth()
        berth.set_editor_property('where', transform(a2, c2, SEA, yaw2))
        berth.set_editor_property('max_length', float(length))
        berth.set_editor_property('name', unreal.Text(name))
        berths.append(berth)
    master.set_editor_property('berths', berths)
    master.set_editor_property('departure_lane', transform(12500, 1200, SEA, 0))
    master.set_editor_property('approach_radius', 40000.0)
    # The shipwright at the head of the slipway.
    wright = person(unreal.EWShipwright, 'Shipwright', 3000, -2050, yaw_to(3000, -2050, -600, -200), 'Elias Thorne', 'Master Shipwright',
                    'Hulls built, sold and mended. Choose one and she goes down the ways today; bring a holed ship alongside and I will make her sound.',
                    ('Oak for the frames, pine for the planks, pitch for everything.', 'Never trust a ship that does not creak.'),
                    'm', clothes('Shipwright', SKIN[5], (.5, .45, .34), (.22, .17, .11), hair=(.35, .3, .26), sash=(.3, .2, .1)))
    sales = []
    for ship, price, fit in (('Raft', 60, ('Ships/DA_RaftPaddles', 'Testing/DA_TestSailSmall')),
                             ('Dinghy', 400, ('Ships/DA_DinghyTiller', 'Testing/DA_TestSailSmall')),
                             ('Sloop', 2500, ('Testing/DA_TestShipHelm', 'Testing/DA_TestSailMedium', 'Testing/DA_TestSailSmall'))):
        definition = unreal.load_asset(f'/Game/Elitewake/Ships/DA_Ship_{ship}')
        sale = unreal.EWShipForSale()
        sale.set_editor_property('definition', definition)
        sale.set_editor_property('price_copper', price)
        mounts, items, used = [], [], set()
        for path in fit:
            item = unreal.load_asset(f'{ITEMS}/{path}')
            kind = item.get_editor_property('fitting_mount_type')
            mount = next((mm for mm in definition.get_editor_property('mounts')
                          if mm.get_editor_property('type') == kind and str(mm.get_editor_property('mount_id')) not in used
                          and str(mm.get_editor_property('parent_mount')) == 'None'), None)
            if mount:
                used.add(str(mount.get_editor_property('mount_id')))
                mounts.append(mount.get_editor_property('mount_id'))
                items.append(item)
        sale.set_editor_property('fitted_mounts', mounts)
        sale.set_editor_property('fitted_items', items)
        sales.append(sale)
        report.setdefault('ships_for_sale', []).append({ship: [str(x) for x in mounts]})
    wright.set_editor_property('ships_for_sale', sales)
    # His fittings: the six sail assemblies (owner, October 18: standard and weighted, small to large) and cannons. Prices are tuning.
    wright.set_editor_property('goods', [goods('Testing/DA_TestSailSmall', 1, 150, 3), goods('Testing/DA_TestSailMedium', 1, 300, 2),
                                         goods('Testing/DA_TestSailLarge', 1, 500, 2), goods('Ships/DA_SailSmallWeighted', 1, 180, 3),
                                         goods('Ships/DA_SailMediumWeighted', 1, 350, 2), goods('Ships/DA_SailLargeWeighted', 1, 600, 2),
                                         goods('Testing/DA_TestCannon', 1, 250, 4)])
    wright.set_editor_property('build_stall', False)
    wright.set_editor_property('buys_pack', False)
    wright.set_editor_property('restock_seconds', 600.0)
    wright.set_editor_property('ship_class', ship_class)
    wright.set_editor_property('launch_point', transform(7500, -1500, SEA, 0))
    # The tavern keeper behind the bar.
    keeper = person(unreal.EWTavernKeeper, 'Keeper', -2500 - 520, -200, 0, 'Bess Harrow', 'Keeper of the Salt Lantern',
                    'Sit, drink, listen. Half of what is said in here is lies, and the other half is worth money.',
                    ('The stew is fish. It is always fish.',), 'f',
                    clothes('Keeper', SKIN[0], (.55, .5, .42), (.28, .12, .08), hair=(.3, .12, .05), sash=(.42, .07, .05)), z=tavern_floor)
    keeper.set_editor_property('rumors', [unreal.Text(s) for s in (
        'The caves on the Plains islands glitter with gemstones, they say, for anyone with a pick and a lamp.',
        'Something with too many legs nests in the deep caves. Look for the webs and turn back if you are wise.',
        'Winter will kill a sailor in a shirt. Furs first, then the birch woods.',
        'The Desert islands pay in stone and ore for anyone who can stand the heat.',
        'A hired gunner fires when you fire, and not before. Keep them loaded and pointed the same way you are.',
        'The swamp channels are shallow; take the dinghy, not the sloop.',
        'Elias at the yard will mend a holed hull, if you can get her back into the harbor.')])
    contracts = []
    for path, qty, reward, story in (('Food/DA_RawFish', 5, 45, 'The cook is short of fish for the pot.'),
                                     ('Testing/DA_TestWood', 20, 70, 'Benches to mend after last night.'),
                                     ('Testing/DA_TestHide', 3, 45, 'The cobbler needs hides.'),
                                     ('Food/DA_MedicinalHerb', 2, 35, 'For the surgeon\'s chest.'),
                                     ('Resources/DA_Coal', 5, 50, 'The smith\'s forge is cold.')):
        job = unreal.EWDeliveryContract()
        job.set_editor_property('item', unreal.load_asset(f'{ITEMS}/{path}'))
        job.set_editor_property('quantity', qty)
        job.set_editor_property('reward_copper', reward)
        job.set_editor_property('story', unreal.Text(story))
        contracts.append(job)
    keeper.set_editor_property('contracts', contracts)
    # The notice board in the square.
    board = person(unreal.EWNoticeBoard, 'Board', -400 + 40, 520 - 60, yaw_to(-400, 520, -600, -200), 'notice board', '', body=None)
    board.set_editor_property('directions', unreal.Text(
        'SALTREACH FREEPORT. A free port: no fighting, no building, no beasts within the beacons.\n'
        '- The Salt Lantern, tavern (Bess Harrow): rumours, jobs, a drink. Head of the square.\n'
        '- The market, down the high street: Oskar Brann (resources), Marta Vell (provisions), Lucia Fane (outfitter).\n'
        '- The shipyard, past the market on the left: Elias Thorne, ships built, sold and mended.\n'
        '- The hiring office by the fishing jetty: Gideon Rusk, sailors and gunners.\n'
        '- The harbor office at the long pier: Captain Ines Calder, berths and departures.'))
    # Townsfolk: at work and walking their rounds.
    folk = [
        ('Pell', 'dock worker', 'm', (.55, .5, .42), (.2, .16, .1), [(4500, 1650), (9300, 1650)], ('Mind your feet; the planks are wet.',)),
        ('Hask', 'dock worker', 'm', (.25, .3, .35), (.22, .2, .16), [(3450, -1000), (3450, 2600), (3150, 2600), (3150, -1000)], ('Cargo does not lift itself.',)),
        ('Ondine', 'fisher', 'f', (.2, .3, .25), (.25, .2, .15), [(180, 3900), (180, 7400)], ('The bream run on the ebb.',)),
        ('Wat', 'townsman', 'm', (.45, .2, .12), (.2, .18, .15), [(-1200, -500), (-1200, 300), (-300, 300), (-300, -500)], ('Fine day for it.',)),
        ('Rosa', 'townswoman', 'f', (.6, .55, .3), (.25, .2, .2), [(2000, -1100), (2000, 1400)], ('Lucia has new hats in.',)),
        ('Abe', 'shipwright\'s hand', 'm', (.4, .35, .25), (.2, .16, .1), [(1300, -2200), (3000, -2200), (3000, -3150), (1300, -3150)], ('The frames want pitch before the rain.',)),
        ('Corrie', 'watchwoman', 'f', (.15, .15, .2), (.12, .12, .14), [(-1200, 1100), (-1200, -1700), (-400, -2300), (700, -1600), (700, 1100)], ('Keep the peace and it keeps you.',)),
    ]
    for k, (name, role, body, shirt, trousers, route, talk) in enumerate(folk):
        a, c = route[0]
        person(unreal.EWTownsfolk, f'Folk{k}', a, c, 0, name, role, '', talk, body,
               clothes(f'Folk{k}', SKIN[k % len(SKIN)], shirt, trousers, hair=SKIN[(k + 3) % len(SKIN)] if k % 3 == 0 else (.05, .035, .02)),
               stroll=route)
    # People who stand: patrons at the tavern, a sailor on the wharf.
    for k, (name, role, body, a, c, yaw, z, talk) in enumerate((
            ('Silas', 'patron', 'm', -2500 + 150 + 80, -200 - 450, 180, tavern_floor, ('Buy me a drink and I will tell you about the Winter run.',)),
            ('Nan', 'patron', 'f', -2500 + 150 - 85, -200 + 450, 0, tavern_floor, ('I am waiting for a ship. I am always waiting for a ship.',)),
            ('Ibbie', 'patron', 'f', -2500 + 650 + 160, -200 - 430, 90, TOWN, ('Have you met Gideon? He will find you a crew.',)),
            ('Mack', 'sailor', 'm', 4100, 1500, 0, DECK, ('She is a fine sloop, that one at the pier.',)))):
        person(unreal.EWTownsfolk, f'Stand{k}', a, c, yaw, name, role, '', talk, body,
               clothes(f'Stand{k}', SKIN[(k + 2) % len(SKIN)], ((.5, .2, .1), (.6, .55, .4), (.1, .3, .3), (.3, .3, .32))[k], (.2, .16, .12)), z=z)


def town_attenuation(name, inner, falloff):
    path = f'{FOLDER}/{name}'
    asset = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FOLDER, unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    settings = asset.get_editor_property('attenuation')
    settings.set_editor_property('attenuation_shape', unreal.AttenuationShape.SPHERE)
    settings.set_editor_property('attenuation_shape_extents', unreal.Vector(inner, 0, 0))
    settings.set_editor_property('falloff_distance', falloff)
    settings.set_editor_property('distance_algorithm', unreal.AttenuationDistanceModel.NATURAL_SOUND)
    asset.set_editor_property('attenuation', settings)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def build_sounds():
    """The town heard: voices in the tavern (always) and the market (by day), the yard at work by day, water at the piles, hulls and
    rigging creaking off the piers, and the harbor bell struck every few minutes (AEWTownSound; levels are tuning)."""
    near = town_attenuation('SA_Town_v1', 300.0, 2200.0)
    wide = town_attenuation('SA_TownWide_v1', 1200.0, 5000.0)
    far = unreal.load_asset('/Game/Elitewake/Audio/SA_Far_v1')
    audio = '/Game/Elitewake/Audio'
    H = unreal.EWTownSoundHours
    spots = [('tavern voices', 'Town/S_AmbTavernMurmur_v1', -2500, -200, TOWN + 200, H.ALWAYS, 1.0, near, (0, 0)),
             ('market voices', 'Town/S_AmbMarketMurmur_v1', 2000, 200, TOWN + 170, H.DAY, .8, wide, (0, 0)),
             ('shipyard at work', 'Town/S_AmbShipyardWork_v1', 2200, -2700, TOWN + 150, H.DAY, .9, wide, (0, 0)),
             ('water at the wharf', 'Town/S_AmbPierLapping_v1', 3950, 1000, DECK - 150, H.ALWAYS, .6, near, (0, 0)),
             ('water at the long pier', 'Town/S_AmbPierLapping_v1', 7000, 1800, DECK - 150, H.ALWAYS, .6, near, (0, 0)),
             ('water at the jetty', 'Town/S_AmbPierLapping_v1', 300, 5600, DECK - 150, H.ALWAYS, .6, near, (0, 0)),
             ('fishing boat creaking 1', 'Ships/S_AmbHullCreak_v2', 2900, 6700, SEA + 80, H.ALWAYS, .7, near, (0, 0)),
             ('fishing boat creaking 2', 'Ships/S_AmbHullCreak_v2', 6600, 5600, SEA + 80, H.ALWAYS, .7, near, (0, 0)),
             ('rigging at the pier head', 'Ships/S_AmbRigging_v2', 9500, 2300, DECK + 300, H.ALWAYS, .5, near, (0, 0)),
             ('harbor bell', 'Town/S_HarborBell_v1', 3170, 2950, TOWN + 600, H.ALWAYS, .8, far, (120.0, 240.0))]
    for label, path, a, c, z, hours, volume, attenuation, interval in spots:
        sound = unreal.load_asset(f'{audio}/{path}')
        assert sound, path
        x, y = world(a, c)
        actor = actors.spawn_actor_from_class(unreal.EWTownSound, unreal.Vector(x, y, z), unreal.Rotator(0, 0, 0))
        actor.set_actor_label(f'{NAME}: sound, {label}')
        actor.set_folder_path(OUT)
        actor.set_editor_property('sound', sound)
        actor.set_editor_property('attenuation', attenuation)
        actor.set_editor_property('hours', hours)
        actor.set_editor_property('volume', volume)
        actor.set_editor_property('interval', unreal.Vector2D(*interval))
        report.setdefault('sounds', []).append(label)


def build_safe_zone():
    x, y = world(4000, 600)
    zone = actors.spawn_actor_from_class(unreal.EWSafeZone, unreal.Vector(x, y, LEVEL), unreal.Rotator(0, 0, 0))
    zone.set_actor_label(f'{NAME}: safe zone')
    zone.set_folder_path(OUT)
    zone.set_editor_property('zone_name', unreal.Text(NAME))
    zone.set_editor_property('radius', 9500.0)
    report['safe_zone'] = {'centre': [round(x), round(y)], 'radius_m': 95}


def main():
    global actors, ground, MATS
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    ground = Ground()
    MATS = make_materials()
    clear_site()
    ships = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip)]
    assert ships, 'no ship on the map to take the class from'
    ship_class = ships[0].get_class()
    report['ships_on_map'] = {s.get_actor_label(): [round(v) for v in port.local(s.get_actor_location().x, s.get_actor_location().y)] for s in ships}
    build_ground(MATS)
    build_harbor(MATS)
    stalls, placed = build_town(MATS)
    build_shipyard(MATS)
    build_palms(MATS)
    build_people(stalls, placed, ship_class)
    build_sounds()
    build_safe_zone()
    assert level.save_current_level()
    report['success'] = True
    report['site'] = {'centre': [round(port.cx), round(port.cy)], 'facing_deg': round(FACING)}
    Path(unreal.Paths.project_saved_dir(), 'FreeportResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Freeport built: {report["placed"]} pieces, {report["lights"]} lights, {len(report["npcs"])} people')


if __name__ == '__main__':
    main()
