"""Grow the coastal map's plant life from the ecology guide's Western Tropical region. Safe to run again.
Run in the editor after build_coastal_terrain.py, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Veyran Palms: three shapes of feather palm built in the editor, each a ringed, leaning trunk under a crown of
arching fronds (the frond is Art/Flora/Veyran-Palm-Frond-v1.png, drawn by Scripts/Art/make_palm_frond.py) with a
few hanging dry fronds and a cluster of fruit. About thirty stand behind the beaches of the island and the islet,
singly and in pairs, kept clear of the spawn, the dock and the spring. Each is a harvestable tree: a hatchet
gives Wood and Thatch (the existing test yields), and its trunk is solid.

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
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Flora'
FLORA_FOLDER = 'Coast/Flora'
ROOT = Path(unreal.Paths.project_dir()).resolve()
FROND_ART = ROOT / 'Art/Flora/Veyran-Palm-Frond-v1.png'
TIMBER = '/Game/Elitewake/World/Materials/T_Timber_v1'
ITEMS = '/Game/Elitewake/Items/Testing'
WOOD, THATCH = f'{ITEMS}/DA_TestWood', f'{ITEMS}/DA_TestThatch'
# Hand-gathered plants (tuning): item, amount, gathering kind, how many on the island and on the islet.
PLANTS = {'Fiber Plant': ('DA_TestFiber', 10, 'PLANT_FIBER', (18, 5)),
          'Fallen Sticks': ('DA_TestSticks', 6, 'LOOSE_STICKS', (12, 4)),
          'Berry Bush': ('DA_TestAzulBerry', 10, 'BERRIES', (8, 3))}
SEA = -65.0
BARK, FROND = 0, 1
# Palm shapes (tuning): height, lean at the crown, frond count and length.
PALMS = [dict(height=720.0, lean=170.0, fronds=13, frond=380.0, seed=1),
         dict(height=880.0, lean=260.0, fronds=12, frond=420.0, seed=2),
         dict(height=600.0, lean=90.0, fronds=14, frond=340.0, seed=3)]
# Where palms may not stand: (x, y, radius), around the beach spawn, the dock's landing and the spring.
KEEP_CLEAR = [(150.0, 0.0, 700.0), (4000.0, 900.0, 700.0), (-1700.0, 1500.0, 1000.0)]
AREAS = [((-5900.0, 4300.0), (-4200.0, 4000.0), 24), ((7700.0, 11300.0), (1150.0, 4050.0), 7)]  # x range, y range, count


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


def frond_material(texture):
    """Leaves: the frond art, cut out by its alpha, lit through from behind; dry fronds turn straw brown."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_PalmFrond_v1')
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    material.set_editor_property('two_sided', True)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    art = node(unreal.MaterialExpressionTextureSample, texture=texture)
    flags = node(unreal.MaterialExpressionVertexColor)
    colour = custom('return lerp(A, dot(A, float3(0.3, 0.59, 0.11)) * float3(1.25, 1.0, 0.62), F.r);',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('A', 'F'))
    through = custom('return C * float3(0.55, 0.7, 0.3);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('C',))
    assert mel.connect_material_expressions(art, 'RGB', colour, 'A')
    assert mel.connect_material_expressions(flags, '', colour, 'F')
    assert mel.connect_material_expressions(colour, '', through, 'C')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(through, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    assert mel.connect_material_property(art, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=0.65), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


# ---- Placement ---------------------------------------------------------------------------------------------

TERRAIN_MESH = '/Game/Elitewake/World/Meshes/SM_CoastalTerrain_v1'


class Ground:
    """Heights of the coastal terrain mesh (a regular grid, placed at the origin), looked up by position."""

    def __init__(self):
        mesh = unreal.DynamicMesh()
        _, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
            unreal.load_asset(TERRAIN_MESH), mesh, unreal.GeometryScriptCopyMeshFromAssetOptions(), unreal.GeometryScriptMeshReadLOD())
        assert outcome == unreal.GeometryScriptOutcomePins.SUCCESS, outcome
        points = unreal.GeometryScript_List.convert_vector_list_to_array(
            unreal.GeometryScript_MeshQueries.get_all_vertex_positions(mesh, False)[1])
        xs = sorted({round(p.x) for p in points})
        self.origin, self.step = xs[0], xs[1] - xs[0]
        self.heights = {(round((p.x - self.origin) / self.step), round((p.y - self.origin) / self.step)): p.z for p in points}

    def __call__(self, x, y):
        """Bilinear height at (x, y), or None off the terrain."""
        fx, fy = (x - self.origin) / self.step, (y - self.origin) / self.step
        ix, iy = math.floor(fx), math.floor(fy)
        corners = [self.heights.get((ix + dx, iy + dy)) for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
        if any(c is None for c in corners):
            return None
        tx, ty = fx - ix, fy - iy
        return (corners[0] * (1 - tx) + corners[1] * tx) * (1 - ty) + (corners[2] * (1 - tx) + corners[3] * tx) * ty


def spots(ground):
    """Palm positions behind the beaches: above the wet sand, below the hills, apart from each other."""
    rng = random.Random(11)
    chosen = []
    for (x0, x1), (y0, y1), count in AREAS:
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
        if str(actor.get_folder_path()) == FLORA_FOLDER and actor.get_actor_label().startswith(('Veyran Palm', *PLANTS)):
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
        mesh.set_relative_scale3d(unreal.Vector(*[rng.uniform(0.9, 1.12)] * 3))
        for prop, value in {'wood': wood, 'thatch': thatch, 'blocker_radius': 26.0, 'blocker_half_height': 160.0}.items():
            tree.set_editor_property(prop, value)
        placed.append([round(x), round(y), round(z)])
    plants = place_plants(actors, ground, [(p[0], p[1]) for p in placed], materials)
    assert level.save_current_level()
    report = {'success': True, 'palms': len(placed), 'positions': placed, 'plants': plants}
    Path(unreal.Paths.project_saved_dir(), 'CoastalFloraResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Coastal flora: {len(placed)} palms')


def place_plants(actors, ground, palms, materials):
    """Fiber plants and berry bushes in the open sand behind the beach; stick piles under the palms."""
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
            (x0, x1), (y0, y1), _ = area
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
        counts[label] = n
    return counts


if __name__ == '__main__':
    main()
