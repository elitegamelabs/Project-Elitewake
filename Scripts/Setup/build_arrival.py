"""Build the Plains arrival (CLAUDE.md Phase 1, slice 1; arrival_layout.py has the places and why). Safe to run again.
Run in the editor outside Play (it also clears the grass off the track and spring; build_grass.py leaves them bare when regrown):
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -run=pythonscript -script=<this file>

  - The PlayerStart moves to the south-shore beach and faces west-north-west toward Saltreach.
  - A worn track, 4.5 m wide, runs from it across the sand and round the flooded hollows to Saltreach's east edge: a thin,
    collision-free skin laid 4 cm over the island mesh (walking stays on the island), its edges ragged and dithered out.
  - Four oaks (harvestable, like every other oak) stand on the rise to the forward left.
  - A small spring below them: a ring of rough limestone round a pool of the pond's fresh water, with a drinking spot.
  - Owner, October 31: the piranhas leave the starter pond (the bass and catfish stay). There is no other fresh water yet
    for them, so they are taken out of the map; their definition stays for a Jungle river later.
Nothing else moves: the old beach, its dock, the pond and the moored sloop stay where they were.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arrival_layout as A  # noqa: E402
import world_terrain as T  # noqa: E402
from build_coastal_flora import MAP, Ground, WOOD, THATCH  # noqa: E402
from coastal_layout import POND, POND_RADIUS  # noqa: E402
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

FOLDER = 'World/Arrival'
ASSETS = '/Game/Elitewake/World/Arrival'
OAK_MESHES = '/Game/Elitewake/World/Flora/SM_Oak_{}'
TRACK_MATERIAL, STONE_MATERIAL = f'{ASSETS}/M_ArrivalTrack_v1', f'{ASSETS}/M_SpringStone_v1'
SEGMENT = 4000.0          # cm of track per mesh, so distant stretches cull on their own
LIFT = 4.0                # cm the track floats over the island mesh between its samples

# A small hash noise both materials share (world-space, no textures).
NOISE = """
struct N { float h(float2 p) { return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }
  float n(float2 p) { float2 i = floor(p), f = frac(p); f = f * f * (3.0 - 2.0 * f);
    return lerp(lerp(h(i), h(i + float2(1, 0)), f.x), lerp(h(i + float2(0, 1)), h(i + float2(1, 1)), f.x), f.y); } } m;
"""


def track_material():
    """Trampled ground: pale packed sand on the beach (vertex red 0) into worn brown loam on the grass (red 1), broken up in
    world space; vertex alpha fades the ragged edges out through a dither."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(TRACK_MATERIAL)
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    material.set_editor_property('dithered_lod_transition', False)
    position = node(unreal.MaterialExpressionWorldPosition)
    flags = node(unreal.MaterialExpressionVertexColor)
    colour = custom(NOISE + """
float big = m.n(P.xy / 260.0), fine = m.n(P.xy / 23.0);
float3 sand = float3(.58, .49, .33), loam = float3(.15, .10, .06), grit = float3(.36, .30, .21);
float3 c = lerp(sand, lerp(loam, grit, big * .55), saturate(V.r));
return c * lerp(.86, 1.08, fine);""", unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'V'))
    rough = custom('return .92;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ())
    # The vertex colour's main pin carries only red, green and blue; its alpha comes on its own pin.
    mask = custom(NOISE + 'return Edge - (m.n(P.xy / 41.0) * .7 + m.n(P.xy / 11.0) * .3) + .5;',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('P', 'Edge'))
    assert mel.connect_material_expressions(position, '', colour, 'P')
    assert mel.connect_material_expressions(flags, '', colour, 'V')
    assert mel.connect_material_expressions(position, '', mask, 'P')
    assert mel.connect_material_expressions(flags, 'A', mask, 'Edge')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(mask, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def stone_material():
    """Weathered grey limestone (CLAUDE.md #B8AA8E), darker and greener low down where the spring keeps it wet."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(STONE_MATERIAL)
    position = node(unreal.MaterialExpressionWorldPosition)
    flags = node(unreal.MaterialExpressionVertexColor)
    colour = custom(NOISE + """
float3 c = float3(.47, .40, .28) * lerp(.7, 1.1, m.n(P.xy / 11.0 + P.z / 13.0));
float wet = saturate(1.0 - V.b * 2.0);
return lerp(c, c * float3(.42, .46, .36), wet);""", unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'V'))
    rough = custom('return lerp(.55, .9, saturate(V.b * 2.0));', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('V',))
    assert mel.connect_material_expressions(position, '', colour, 'P')
    assert mel.connect_material_expressions(flags, '', colour, 'V')
    assert mel.connect_material_expressions(flags, '', rough, 'V')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def track_segments():
    """The track's samples cut into SEGMENT-long pieces that share their end samples."""
    samples = track_samples()
    per = int(SEGMENT / 100)
    return [samples[k:k + per + 1] for k in range(0, len(samples) - 1, per)]


def track_samples():
    """The smoothed centre line resampled every metre."""
    pts = A.smoothed_route()
    at = [0.0]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        at.append(at[-1] + math.hypot(bx - ax, by - ay))
    samples, k = [], 0
    for step in range(int(at[-1] // 100) + 1):
        d = step * 100.0
        while at[k + 1] < d:
            k += 1
        f = (d - at[k]) / ((at[k + 1] - at[k]) or 1.0)
        samples.append((pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f))
    if at[-1] - (len(samples) - 1) * 100.0 > 20:
        samples.append(pts[-1])
    return samples


def track_mesh(samples, ground, rng, origin):
    """One piece of track, in space relative to `origin`: five rows across, edges wandering by up to 40 cm."""
    b = Builder()
    across = (-1.0, -.55, 0.0, .55, 1.0)
    rows = []
    for k, (x, y) in enumerate(samples):
        a = samples[max(k - 1, 0)]
        c = samples[min(k + 1, len(samples) - 1)]
        dx, dy = c[0] - a[0], c[1] - a[1]
        run = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / run, dx / run
        half = A.ROUTE_WIDTH / 2
        wobble = (rng.uniform(-40, 30), rng.uniform(-40, 30))
        row = []
        for j, s in enumerate(across):
            w = s * half + (wobble[0] if j == 0 else wobble[1] if j == 4 else 0.0) * (-1 if j == 0 else 1)
            px, py = x + nx * w, y + ny * w
            z = ground(px, py) + LIFT
            # Red: 0 on the beach's sand, 1 on the grass (the terrain turns to soil about 1 m above the waterline).
            earth = min(1.0, max(0.0, (z - (T.SEA + 100)) / 80.0))
            edge = 0.0 if j in (0, 4) else 1.0
            row.append(b.vertex((px - origin[0], py - origin[1], z - origin[2]), earth, 0.0, .5, alpha=edge))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(len(across) - 1):
            b.quad(r0[j], r0[j + 1], r1[j + 1], r1[j], (0, 0, 1))
    return b


def spring_meshes(ground, rng):
    """The spring's stones (one mesh, a ring of 11 rough boulders, wetter at their feet) and its pool's surface disc."""
    x0, y0 = A.SPRING
    # The pool lies level with the ring's highest ground, so the slope never shows through it; the stones stand taller than
    # the water all round, a closed ring, so its edge is hidden on the low side too.
    rim = A.SPRING_RADIUS + 12
    water_z = max(ground(x0 + rim * math.cos(a), y0 + rim * math.sin(a)) for a in [k * math.pi / 8 for k in range(16)]) + 4.0
    stones = Builder()
    count, sides = 15, 8
    shape = ((0.0, .85, 0.0), (.35, 1.0, .25), (.75, .74, .65), (1.0, .32, 1.0))   # (height share, girth, dryness)
    for k in range(count):
        a = 2 * math.pi * k / count + rng.uniform(-.08, .08)
        r = A.SPRING_RADIUS + rng.uniform(5, 20)
        cx, cy = r * math.cos(a), r * math.sin(a)
        size = rng.uniform(30, 42)
        base = ground(x0 + cx, y0 + cy) - water_z - 10
        height = max(size * rng.uniform(.6, .9), -base + 8)          # at least 8 cm proud of the water
        radii = [size * rng.uniform(.8, 1.15) for _ in range(sides)]
        rings = []
        for share, girth, dry in shape:
            rings.append([stones.vertex((cx + radii[j] * girth * math.cos(2 * math.pi * j / sides),
                                         cy + radii[j] * girth * math.sin(2 * math.pi * j / sides), base + height * share), 0, 0, dry)
                          for j in range(sides)])
        top = stones.vertex((cx, cy, base + height * 1.04), 0, 0, 1.0)
        for j in range(sides):
            n = (j + 1) % sides
            out = (math.cos(2 * math.pi * (j + .5) / sides), math.sin(2 * math.pi * (j + .5) / sides), 0.0)
            for lower, upper in zip(rings, rings[1:]):
                stones.quad(lower[j], lower[n], upper[n], upper[j], (out[0], out[1], .3))
            stones.tri(rings[-1][j], rings[-1][n], top, (out[0], out[1], 2.0))
    water = Builder()
    centre = water.vertex((0, 0, 0))
    rim = [water.vertex(((A.SPRING_RADIUS + 12) * math.cos(t), (A.SPRING_RADIUS + 12) * math.sin(t), 0))
           for t in [2 * math.pi * k / 24 for k in range(24)]]
    for k in range(24):
        water.tri(centre, rim[k], rim[(k + 1) % 24], (0, 0, 1))
    return stones, water, water_z


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    report = {'removed': [], 'placed': []}
    everything = actors.get_all_level_actors()
    for actor in everything:
        if str(actor.get_folder_path()).startswith(FOLDER):
            report['removed'].append(actor.get_actor_label())
            actors.destroy_actor(actor)
    ground = Ground()
    rng = random.Random(3101)

    # The spawn.
    start = next(a for a in everything if isinstance(a, unreal.PlayerStart))
    sz = ground(*A.SPAWN)
    start.set_actor_location_and_rotation(unreal.Vector(A.SPAWN[0], A.SPAWN[1], sz + A.STAND_HEIGHT),
                                          unreal.Rotator(roll=0, pitch=0, yaw=A.SPAWN_YAW), False, False)
    start.set_actor_label('Plains arrival spawn')
    start.set_editor_property('player_start_tag', 'Arrival')   # turns on the arrival prompts (UEWArrivalComponent)
    report['spawn'] = [A.SPAWN[0], A.SPAWN[1], round(sz + A.STAND_HEIGHT), A.SPAWN_YAW]

    # The track.
    material = track_material()
    for k, samples in enumerate(track_segments()):
        ox, oy = samples[0]
        origin = (ox, oy, ground(ox, oy))
        mesh = write_static_mesh(track_mesh(samples, ground, rng, origin), f'{ASSETS}/SM_ArrivalTrack_{k + 1:02d}_v1', [material],
                                 200.0, collision=False, split_angle=180.0)
        piece = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*origin))
        piece.static_mesh_component.set_static_mesh(mesh)
        piece.static_mesh_component.set_collision_profile_name('NoCollision')
        piece.static_mesh_component.set_editor_property('cast_shadow', False)
        piece.set_actor_label(f'Arrival track {k + 1:02d}')
        piece.set_folder_path(FOLDER)
        report['placed'].append(piece.get_actor_label())

    # The oaks.
    wood, thatch = unreal.load_asset(WOOD), unreal.load_asset(THATCH)
    assert wood and thatch
    for k, (x, y, scale) in enumerate(A.OAKS):
        tree = actors.spawn_actor_from_class(unreal.EWHarvestTree, unreal.Vector(x, y, ground(x, y) - 12),
                                             unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
        tree.set_actor_label(f'Arrival oak {k + 1}')
        tree.set_folder_path(FOLDER)
        oak = unreal.load_asset(OAK_MESHES.format((k + 1) % 3 + 1))
        assert oak, k
        tree.get_editor_property('mesh').set_static_mesh(oak)
        tree.get_editor_property('mesh').set_relative_scale3d(unreal.Vector(scale, scale, scale))
        for prop, value in {'wood': wood, 'thatch': thatch, 'blocker_radius': 52.0, 'blocker_half_height': 220.0}.items():
            tree.set_editor_property(prop, value)
        report['placed'].append(tree.get_actor_label())

    # The spring.
    pond_surface = next(a for a in everything if a.get_actor_label() == 'Freshwater surface')
    fresh = pond_surface.static_mesh_component.get_material(0)
    stones, water, water_z = spring_meshes(ground, rng)
    x0, y0 = A.SPRING
    for name, builder, materials, collide in (('SpringStones', stones, [stone_material()], True), ('SpringWater', water, [fresh], False)):
        mesh = write_static_mesh(builder, f'{ASSETS}/SM_{name}_v1', materials, 60.0, collision=collide)
        piece = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x0, y0, water_z))
        piece.static_mesh_component.set_static_mesh(mesh)
        if not collide:
            piece.static_mesh_component.set_collision_profile_name('NoCollision')
        piece.set_actor_label(f'Arrival spring {"stones" if collide else "water"}')
        piece.set_folder_path(FOLDER)
        report['placed'].append(piece.get_actor_label())
    # The drinking spot covers the pool, so a survivor at its edge looking in finds it.
    drink = actors.spawn_actor_from_class(unreal.EWWaterSource, unreal.Vector(x0, y0, water_z + 2))
    drink.set_actor_scale3d(unreal.Vector(A.SPRING_RADIUS / 50, A.SPRING_RADIUS / 50, 1))
    drink.set_actor_label('Arrival spring - E to drink')
    drink.set_folder_path(FOLDER)
    report['placed'].append(drink.get_actor_label())
    report['spring_water_z'] = round(water_z)

    # The starter pond keeps its bass and catfish; its piranhas go (owner, October 31).
    for actor in everything:
        if isinstance(actor, unreal.EWFish) and actor.get_actor_label().startswith('Piranha'):
            p = actor.get_actor_location()
            if math.hypot(p.x - POND[0], p.y - POND[1]) < POND_RADIUS + 200:
                report['removed'].append(actor.get_actor_label())
                actors.destroy_actor(actor)

    # Grass off the track and the spring (build_grass.py leaves them bare too, when the whole island is regrown).
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    circles = [unreal.Vector(x, y, A.ROUTE_WIDTH / 2 + 40) for x, y in track_samples()[::2]]
    circles.append(unreal.Vector(A.SPRING[0], A.SPRING[1], A.SPRING_RADIUS + 90))
    report['grass_cleared'] = unreal.EWWorldEditorLibrary.remove_foliage_in_circles(world, circles, 'SM_GrassClump')

    assert world_map.save_map()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'ArrivalResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Arrival built: {len(report["placed"])} placed')


if __name__ == '__main__':
    main()
