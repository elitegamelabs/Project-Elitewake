"""Crystals, obsidian and coal (owner, October 18 rules: CLAUDE.md; the owner asked again
on October 28). Safe to run again. Run in the editor outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Makes: the items (Ruby, Sapphire, Emerald, Obsidian, Coal), faceted crystal clusters (hexagonal prisms with pointed tips growing from a rock
base, three shapes), a jagged black obsidian cluster, a lump of coal; a glossy glowing gem material (so crystals read in a dark cave), a dull
coal material; and places mineable nodes (AEWMineable, from the existing mining system):
  - every island's cave: ruby, sapphire, emerald and obsidian nodes growing out of the chamber walls (found by ray casts from the middle of the chamber);
  - Winter: emerald deposits on the mountainsides and coal ore on the mountainsides, not only the summits (coal is nowhere else).
Mining: a Metal pickaxe or better; a node holds 4 to 8 (drawn each time) and comes back 60 minutes after it is emptied.
Counts, sizes and colours are tuning."""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, cross, dot, material_builder, norm, sub, write_static_mesh  # noqa: E402
from build_coastal_flora import MAP, SEA, Ground  # noqa: E402
from build_coastal_rocks import lattice  # noqa: E402
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

FOLDER = '/Game/Elitewake/World/Crystals'
ITEM_FOLDER = '/Game/Elitewake/Items/Resources'
LEVEL_FOLDER = 'Coast/Resources/Crystals'
CAVE_NODES = ('Ruby', 'Ruby', 'Sapphire', 'Sapphire', 'Emerald', 'Emerald', 'Obsidian', 'Obsidian')      # per cave (tuning)
CAVE_DECOR = 30                                                                                             # decorative clusters per cave (tuning)
WINTER_EMERALD, WINTER_COAL = 8, 14                                                                         # per winter island (tuning)
# colour (linear), glow, roughness
GEMS = {'Ruby': ((.5, .01, .02), .5, .1), 'Sapphire': ((.015, .09, .6), .45, .1), 'Emerald': ((.015, .45, .1), .4, .1),
        'Obsidian': ((.018, .016, .028), .0, .04)}
ITEMS = {'Ruby': 'A deep red crystal from a cave wall.', 'Sapphire': 'A blue crystal from a cave wall.',
         'Emerald': 'A green crystal from a cave wall or a mountainside.', 'Obsidian': 'Black volcanic glass, sharp and glossy.',
         'Coal': 'Black ore that burns.'}


def frame(axis):
    ref = (0, 0, 1) if abs(axis[2]) < .9 else (1, 0, 0)
    u = norm(cross(axis, ref))
    return u, cross(axis, u)


def at(base, *terms):
    return tuple(base[i] + sum(c * v[i] for c, v in terms) for i in range(3))


def crystal(b, base, axis, radius, length, rng, sides=6):
    """One prism with a pointed tip, growing from `base` along `axis` (the local +x of the node)."""
    u, v = frame(axis)
    twist = rng.uniform(0, math.pi)

    def ring(h, r, k):
        a = twist + 2 * math.pi * k / sides
        return at(base, (h, axis), (r * math.cos(a), u), (r * math.sin(a), v))
    tone = rng.uniform(.25, .95)
    low = [b.vertex(ring(-radius * .6, radius, k), tone=tone) for k in range(sides)]
    mid = [b.vertex(ring(length * .78, radius * .9, k), tone=tone) for k in range(sides)]
    tip = b.vertex(at(base, (length + radius * 1.5, axis)), tone=min(1.0, tone + .25))
    for k in range(sides):
        j = (k + 1) % sides
        mean = norm(tuple(sum(b.verts[i][c] for i in (low[k], low[j])) / 2 - base[c] for c in range(3)))
        b.quad(low[k], low[j], mid[j], mid[k], mean)
        b.tri(mid[k], mid[j], tip, tuple(mean[c] + axis[c] * .6 for c in range(3)))


def lump(b, centre, radii, rng, rough=.22, rows=10, cols=14, slot=0):
    """A lumpy flattened ball, its lumps from a few random bumps."""
    bumps = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(.4, 1)) for _ in range(6)]
    b.slot = slot
    grid = []
    for i in range(rows + 1):
        phi = math.pi * i / rows
        row = []
        for j in range(cols + 1):
            th = 2 * math.pi * (j % cols) / cols
            d = (math.sin(phi) * math.cos(th), math.sin(phi) * math.sin(th), math.cos(phi))
            r = 1 + rough * sum(w * max(0, dot(d, norm((x, y, z)))) ** 2 for x, y, z, w in bumps) - rough * .5
            row.append(tuple(centre[c] + d[c] * radii[c] * r for c in range(3)))
        grid.append(row)
    b.grid(grid, lambda i, j: norm(sub(grid[i][j], centre)), tone_of=lambda i, j: .4 + .3 * math.sin(i * 1.7 + j * .9))


def cluster(seed, count, big=1.0):
    """A node: a rock base and crystals growing out along +x (out of the wall)."""
    rng = random.Random(seed)
    b = Builder()
    # A chunky gem cluster (owner, October 28: "more cluster like and less pokey ball", like Ark): a broad rock base, one fat tall
    # crystal, a ring of thick medium ones tightly around it, and low stubby ones at the foot. Thick (radius to length about 1:4),
    # mostly parallel, not radiating spikes.
    lump(b, (-16, 0, 0), (30, 70, 62), rng, rough=.28, rows=8, cols=12, slot=0)
    b.slot = 1
    crystal(b, (0, 0, 0), norm((1, rng.uniform(-.08, .08), rng.uniform(-.08, .08))), 22 * big, 100 * big, rng)
    for k in range(count):
        a = 2 * math.pi * k / count + rng.uniform(-.3, .3)
        lean = rng.uniform(.18, .42)
        axis = norm((1 - lean * .4, lean * math.cos(a), lean * math.sin(a)))
        reach = rng.uniform(26, 38)
        crystal(b, (-6, reach * math.cos(a), reach * math.sin(a)), axis, rng.uniform(14, 19) * big, rng.uniform(60, 100) * big, rng)
    for k in range(count + 2):
        a = 2 * math.pi * (k + .5) / (count + 2) + rng.uniform(-.25, .25)
        lean = rng.uniform(.5, .8)
        axis = norm((1 - lean * .5, lean * math.cos(a), lean * math.sin(a)))
        reach = rng.uniform(46, 62)
        crystal(b, (-10, reach * math.cos(a), reach * math.sin(a)), axis, rng.uniform(8, 12) * big, rng.uniform(26, 48) * big, rng)
    return b


def obsidian(seed):
    rng = random.Random(seed)
    b = Builder()
    lump(b, (-14, 0, 0), (36, 48, 40), rng, rough=.34, rows=8, cols=12, slot=0)
    b.slot = 1
    for k in range(7):
        a = 2 * math.pi * k / 7 + rng.uniform(-.4, .4)
        lean = rng.uniform(.2, .8) if k else 0.0
        axis = norm((1 - lean * .4, lean * math.cos(a), lean * math.sin(a)))
        reach = rng.uniform(8, 28) if k else 0.0
        crystal(b, (-4, reach * math.cos(a), reach * math.sin(a)), axis, rng.uniform(6, 13), rng.uniform(30, 90), rng, sides=4)
    return b


def coal(seed):
    rng = random.Random(seed)
    b = Builder()
    for centre, radii in (((0, 0, 20), (48, 40, 36)), ((38, 20, 12), (30, 26, 24)), ((-30, -26, 10), (28, 30, 22)), ((10, -38, 8), (22, 22, 16))):
        lump(b, centre, radii, rng, rough=.3, rows=8, cols=12, slot=0)
    return b


def crystal_material():
    """Glossy, glowing faceted gem: a tint (per-gem instance), brighter along facets by position, an emissive glow so it shows in a cave."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Crystal_v1')
    pos = node(unreal.MaterialExpressionWorldPosition)
    vc = node(unreal.MaterialExpressionVertexColor)
    tint = node(unreal.MaterialExpressionVectorParameter, parameter_name='Tint', default_value=unreal.LinearColor(.1, .3, .8, 1))
    glow = node(unreal.MaterialExpressionScalarParameter, parameter_name='Glow', default_value=1.5)
    rough = node(unreal.MaterialExpressionScalarParameter, parameter_name='Rough', default_value=.1)
    spec = node(unreal.MaterialExpressionConstant, r=.9)
    pins = ('P', 'V', 'Tint', 'Glow')
    base = custom('float n = sin(P.x * .11 + P.y * .07) * sin(P.z * .13 - P.x * .05) * .5 + .5;'
                  ' return Tint.rgb * (.35 + .9 * V.b) * (.7 + .3 * n);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'V', 'Tint'))
    emit = custom('float n = sin(P.x * .09 - P.z * .08) * sin(P.y * .12 + P.z * .06) * .5 + .5;'
                  ' return Tint.rgb * Tint.rgb * Glow * (.4 + .9 * V.b) * (.6 + .4 * n);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, pins)
    sources = {'P': pos, 'V': vc, 'Tint': tint, 'Glow': glow}
    for target, names in ((base, ('P', 'V', 'Tint')), (emit, pins)):
        for name in names:
            assert mel.connect_material_expressions(sources[name], '', target, name), name
    assert mel.connect_material_property(base, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(emit, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(spec, '', unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def rock_material(path, dark, light, rough, sparkle):
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(path)
    pos = node(unreal.MaterialExpressionWorldPosition)
    vc = node(unreal.MaterialExpressionVertexColor)
    code = ('float n = sin(P.x * .31 + P.y * .17) * sin(P.z * .29 - P.x * .13) * .5 + .5;'
            ' float g = sin(P.x * 1.7 + P.z * 1.3) * sin(P.y * 1.9 - P.z * 1.1);'
            ' float3 c = lerp(float3(%f, %f, %f), float3(%f, %f, %f), saturate(n * .8 + V.b * .4));'
            ' return c * (1 + %f * saturate(g * 3 - 2));' % (dark + light + (sparkle,)))
    base = custom(code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'V'))
    assert mel.connect_material_expressions(pos, '', base, 'P') and mel.connect_material_expressions(vc, '', base, 'V')
    assert mel.connect_material_property(base, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=rough), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def instance(name, parent, **params):
    mel = unreal.MaterialEditingLibrary
    path = f'{FOLDER}/{name}'
    mi = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, parent)
    for k, v in params.items():
        if isinstance(v, tuple):
            mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*v, 1))
        else:
            mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
    mel.update_material_instance(mi)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi


def item(key):
    path = f'{ITEM_FOLDER}/DA_{key}'
    asset = unreal.load_asset(path)
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(f'DA_{key}', ITEM_FOLDER, unreal.EWItemDefinition, factory)
    for k, v in {'item_id': key, 'display_name': key, 'description': ITEMS[key], 'category': unreal.EWItemCategory.RESOURCE,
                 'max_stack_size': 50, 'unit_weight': .4}.items():
        asset.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    gem = crystal_material()
    stone = rock_material(f'{FOLDER}/M_CrystalRock_v1', (.03, .028, .026), (.13, .12, .11), .85, .5)
    coal_material = rock_material(f'{FOLDER}/M_Coal_v1', (.006, .006, .007), (.045, .045, .05), .55, 2.0)
    looks = {name: instance(f'MI_{name}_v1', gem, Tint=c, Glow=g, Rough=r) for name, (c, g, r) in GEMS.items()}
    items = {key: item(key) for key in ITEMS}
    meshes = {'Crystal': [write_static_mesh(cluster(s, c, big), f'{FOLDER}/SM_CrystalCluster{n}_v1', [stone, gem], 100.0)
                          for n, (s, c, big) in enumerate(((11, 6, 1.0), (23, 5, 1.2), (37, 7, .9)), 1)],
              'Obsidian': [write_static_mesh(obsidian(5), f'{FOLDER}/SM_ObsidianCluster_v1', [stone, gem], 100.0)],
              'Coal': [write_static_mesh(coal(3), f'{FOLDER}/SM_CoalOre_v1', [coal_material], 100.0)]}
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()) == LEVEL_FOLDER:
            actors.destroy_actor(actor)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ground = Ground()
    rng = random.Random(1018)
    placed = []

    def trace(a, b_):
        res = unreal.SystemLibrary.line_trace_single(world, a, b_, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if not res:
            return None
        t = res.to_tuple()
        return t[4], t[7]

    def spawn(kind, where, point, normal, mesh_set):
        mesh_asset = rng.choice(mesh_set)
        # +x of the mesh points out of the surface; embedded a little so the base is bedded in.
        rot = unreal.MathLibrary.make_rot_from_x(unreal.Vector(normal.x, normal.y, normal.z))
        rot.roll = rng.uniform(0, 360)
        loc = unreal.Vector(point.x - normal.x * 8, point.y - normal.y * 8, point.z - normal.z * 8)
        node = actors.spawn_actor_from_class(unreal.EWMineable, loc, rot)
        node.set_actor_label(f'{kind} Node {where} {len(placed) + 1}')
        node.set_folder_path(LEVEL_FOLDER)
        mesh = node.get_editor_property('mesh')
        mesh.set_static_mesh(mesh_asset)
        if kind in looks:
            mesh.set_material(1, looks[kind])
        scale = rng.uniform(1.8, 2.4)                      # much larger (owner, October 28)
        mesh.set_relative_scale3d(unreal.Vector(scale, scale, scale))
        node.set_editor_property('resource', items[kind])
        node.set_editor_property('minimum_pickaxe_tier', unreal.EWPickaxeTier.METAL)
        node.set_editor_property('respawn_when_depleted', True)
        node.set_editor_property('respawn_seconds', 3600.0)
        node.set_editor_property('randomize_stock', True)
        node.set_editor_property('minimum_stock', 4)
        node.set_editor_property('maximum_stock', 8)
        node.set_editor_property('per_strike', 2)
        mesh.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        placed.append([kind, where, round(point.x), round(point.y), round(point.z)])

    # Caves: points on the chamber's own lumpy wall (the same formula build_caves.py cuts it with), oriented out of the wall into the chamber.
    for key, cave in T.CAVES.items():
        if not cave or cave.kind == 'sea':
            continue
        noise = lattice(sum(map(ord, cave.island.key)) * 31)
        cu, cv, cz = cave.chamber

        def wall(theta, phi):
            """World position of the chamber wall at ellipsoid angles (theta from the roof, phi round the chamber)."""
            u, v, z = cu * math.sin(theta) * math.cos(phi), cv * math.sin(theta) * math.sin(phi), cz * math.cos(theta)
            bx, by = cave.world(cave.chamber_u + u, v)
            r = 1 + .16 * noise(bx / 300, by / 300, (cave.chamber_z + z) / 300 + 5.5)
            x, y = cave.world(cave.chamber_u + u * r, v * r)
            return unreal.Vector(x, y, cave.floor + cave.chamber_z + z * r)

        kinds = list(CAVE_NODES)
        rng.shuffle(kinds)
        for k, kind in enumerate(kinds):
            # round the back and sides of the chamber (phi 0 is straight in, away from the way in), low enough to reach from the floor
            phi = math.radians(-105 + 210 * k / (len(kinds) - 1) + rng.uniform(-6, 6))
            theta = math.acos(rng.uniform(-.3, .07))      # a point 60 to 230 cm above the floor
            point = wall(theta, phi)
            dt = .02
            tu = wall(theta + dt, phi) - point
            tv = wall(theta, phi + dt) - point
            n = unreal.Vector(tu.y * tv.z - tu.z * tv.y, tu.z * tv.x - tu.x * tv.z, tu.x * tv.y - tu.y * tv.x)
            length = math.sqrt(n.x ** 2 + n.y ** 2 + n.z ** 2) or 1
            n = unreal.Vector(n.x / length, n.y / length, n.z / length)
            inward = unreal.Vector(*cave.world(cave.chamber_u, 0.0), cave.floor + cave.chamber_z) - point
            if n.x * inward.x + n.y * inward.y + n.z * inward.z < 0:
                n = unreal.Vector(-n.x, -n.y, -n.z)          # the normal points into the chamber
            spawn(kind, f'{key} cave', point, n, meshes['Obsidian'] if kind == 'Obsidian' else meshes['Crystal'])

        # Decoration (owner, October 28: crystals throughout every cave): many more clusters, not mineable, over the roof, walls and
        # floor edges, in all four colours, with a few coloured lights so the cave glows. Solid to nothing: they cannot snag a survivor.
        palette = ['Ruby', 'Sapphire', 'Emerald']
        made = 0
        for attempt in range(400):
            if made >= CAVE_DECOR:
                break
            phi = math.radians(rng.uniform(-165, 165))
            theta = math.acos(rng.uniform(-.8, 1.0))                 # from the roof (1.0) down to a hand above the floor (-.8)
            point = wall(theta, phi)
            dt = .02
            tu, tv = wall(theta + dt, phi) - point, wall(theta, phi + dt) - point
            n = unreal.Vector(tu.y * tv.z - tu.z * tv.y, tu.z * tv.x - tu.x * tv.z, tu.x * tv.y - tu.y * tv.x)
            length = math.sqrt(n.x ** 2 + n.y ** 2 + n.z ** 2) or 1
            n = unreal.Vector(n.x / length, n.y / length, n.z / length)
            inward = unreal.Vector(*cave.world(cave.chamber_u, 0.0), cave.floor + cave.chamber_z) - point
            if n.x * inward.x + n.y * inward.y + n.z * inward.z < 0:
                n = unreal.Vector(-n.x, -n.y, -n.z)
            if any(math.hypot(point.x - p_[2], point.y - p_[3]) < 170 and abs(point.z - p_[4]) < 170 for p_ in placed):
                continue                                              # not on top of a mineable node or another cluster
            kind = rng.choice(palette)
            rot = unreal.MathLibrary.make_rot_from_x(n)
            rot.roll = rng.uniform(0, 360)
            decor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(point.x - n.x * 8, point.y - n.y * 8, point.z - n.z * 8), rot)
            decor.set_actor_label(f'Crystal Decor {key} cave {made + 1}')
            decor.set_folder_path(LEVEL_FOLDER)
            comp = decor.static_mesh_component
            comp.set_static_mesh(rng.choice(meshes['Crystal']))
            comp.set_material(1, looks[kind])
            size = rng.uniform(1.2, 2.4)
            comp.set_relative_scale3d(unreal.Vector(size, size, size))
            comp.set_collision_profile_name('NoCollision')
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            placed.append(['Decor', f'{key} cave', round(point.x), round(point.y), round(point.z)])
            if made % 7 == 0 and (kind != 'Sapphire' or made % 14 == 0):
                light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(point.x + n.x * 90, point.y + n.y * 90, point.z + n.z * 90))
                light.set_actor_label(f'Crystal Light {key} cave {made + 1}')
                light.set_folder_path(LEVEL_FOLDER)
                lc = light.get_component_by_class(unreal.PointLightComponent)
                lc.set_editor_property('intensity', 450.0)
                lc.set_editor_property('attenuation_radius', 650.0)
                lc.set_editor_property('light_color', unreal.Color(*{'Ruby': (255, 40, 60), 'Sapphire': (60, 110, 255), 'Emerald': (40, 255, 110)}[kind], 255))
                lc.set_editor_property('cast_shadows', False)
            made += 1

    # Winter mountains: exposed deposits on the slopes, high and low, not only the peaks.
    for island in W.ISLANDS:
        if island.region != 'Winter':
            continue
        reach = island.reach()
        tries = 0
        samples = []
        while len(samples) < 600 and tries < 20000:
            tries += 1
            x, y = island.cx + rng.uniform(-reach, reach), island.cy + rng.uniform(-reach, reach)
            if island.distance(x, y) > -500 or T.near_cave(x, y, 700) or T.near_climb(x, y):
                continue
            z = ground(x, y)
            gx, gy = ground(x + 60, y), ground(x, y + 60)
            if z is None or gx is None or gy is None:
                continue
            samples.append((x, y, z, math.hypot(gx - z, gy - z) / 60.0))
        top = max(s[2] for s in samples)
        mountain = [s for s in samples if s[2] > SEA + .22 * (top - SEA) and s[3] > .25]       # slopes well up the mountains
        rng.shuffle(mountain)
        used = []
        for kind, count in (('Emerald', WINTER_EMERALD), ('Coal', WINTER_COAL)):
            made = 0
            for x, y, z, slope in mountain:
                if made >= count:
                    break
                if any(math.hypot(x - ux, y - uy) < 450 for ux, uy in used):
                    continue
                hit = trace(unreal.Vector(x, y, z + 400), unreal.Vector(x, y, z - 400))
                if not hit:
                    continue
                n = hit[1]
                up = unreal.Vector(n.x * .5, n.y * .5, n.z * .5 + .5)       # lean toward vertical so it sits up out of the slope
                length = math.sqrt(up.x ** 2 + up.y ** 2 + up.z ** 2) or 1
                spawn(kind, f'{island.key} mountain', hit[0], unreal.Vector(up.x / length, up.y / length, up.z / length),
                      meshes['Coal'] if kind == 'Coal' else meshes['Crystal'])
                used.append((x, y))
                made += 1
            if made < count:
                unreal.log_warning(f'{island.key}: only {made}/{count} {kind}')
    assert level.save_current_level()
    counts = {}
    for p in placed:
        label = f'{p[0]}/{p[1].split()[-1]}'
        counts[label] = counts.get(label, 0) + 1
    Path(unreal.Paths.project_saved_dir(), 'CrystalsResult.json').write_text(json.dumps(
        {'success': True, 'nodes': len(placed), 'counts': counts, 'placed': placed}, indent=2))
    unreal.log(f'Crystal nodes: {len(placed)}')


if __name__ == '__main__':
    main()
