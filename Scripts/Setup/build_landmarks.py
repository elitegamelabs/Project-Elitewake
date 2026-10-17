"""Build each island's natural landmark (world_landmarks.py). Safe to run again. Run in the editor after
build_coastal_terrain.py and build_caves.py, and before the dressing scripts, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Sea stacks and spires are lumpy stone columns with ledges where the strata weather out, rising from below the sea
floor or the ground; the Desert's spire is a hoodoo, a column narrowing under a wider cap rock; Winter's carry snow
on every ledge. An arch is a thick, lumpy bow of stone with one foot on the beach and the other in the sea, high
enough to walk under. Standing stones are broken slabs set upright in a ring. A snag is a giant dead tree, its
bleached trunk flaring at the roots and breaking off at the top, with a few bare branches. All in the region's stone
(build_coastal_rocks.py's materials) or the palms' weathered bark, solid to walk against and climb onto. Sizes tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_terrain as T  # noqa: E402
from world_landmarks import LANDMARKS, PILLARS  # noqa: E402
from ship_geometry import save_dynamic_mesh, write_static_mesh  # noqa: E402
from build_coastal_rocks import boulder, lattice  # noqa: E402
from build_caves import STONE, Piece, dynamic  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Landmarks'
ROCKS = '/Game/Elitewake/World/Rocks'
BARK = '/Game/Elitewake/World/Flora/M_PalmBark_v1'
LEVEL_FOLDER = 'World/Landmarks'


def column(seed, height, radius, below, hoodoo=False, sides=22):
    """A standing column of stone from `below` (cm under the ground) to `height`, closed at both ends."""
    noise = lattice(seed)
    rng = random.Random(seed)
    p = Piece()
    lean = (rng.uniform(-.04, .04), rng.uniform(-.04, .04))
    rings, z, step = [], -below, 60.0
    while z < height:
        f = max(0.0, z) / height
        r = radius * (1.15 - .45 * f)
        if hoodoo:
            # A neck under a wider, flat-bottomed cap rock.
            r = radius * (1.1 - .55 * f) if f < .78 else radius * (.95 if f < .93 else .8)
        ledges = .07 * math.sin(z / 140.0 + noise(z / 400, 0, seed) * 3) + .05 * (abs(math.sin(z / 55.0)) - .5)
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            rr = r * (1 + ledges + .2 * noise(math.cos(a) * 1.4, math.sin(a) * 1.4, z / 260) + .07 * noise(math.cos(a) * 4, math.sin(a) * 4, z / 80))
            ring.append(p.add((lean[0] * max(0, z) + rr * math.cos(a), lean[1] * max(0, z) + rr * math.sin(a), z)))
        rings.append(ring)
        z += step
    # A broken, uneven top: two shrinking rings and a point.
    last = rings[-1]
    for shrink, rise in ((.7, 60), (.35, 110)):
        cx = sum(p.verts[v][0] for v in last) / sides
        cy = sum(p.verts[v][1] for v in last) / sides
        ring = [p.add((cx + (p.verts[v][0] - cx) * shrink, cy + (p.verts[v][1] - cy) * shrink,
                       p.verts[v][2] + rise * (1 + .5 * noise(k * .7, seed, 1.0)))) for k, v in enumerate(last)]
        rings.append(ring)
        last = ring
    top = p.add((sum(p.verts[v][0] for v in last) / sides, sum(p.verts[v][1] for v in last) / sides, p.verts[last[0]][2] + 40))
    low = p.add((0.0, 0.0, -below - 20))
    for i in range(len(rings) - 1):
        for k in range(sides):
            a, b, c, d = rings[i][k], rings[i][(k + 1) % sides], rings[i + 1][(k + 1) % sides], rings[i + 1][k]
            p.tris += [(a, b, c), (a, c, d)]
    for k in range(sides):
        p.tris.append((top, rings[-1][k], rings[-1][(k + 1) % sides]))
        p.tris.append((low, rings[0][(k + 1) % sides], rings[0][k]))
    return p.outward()


def arch(seed, a, b, sides=20):
    """A bow of stone from foot a to foot b ((x, y, z) relative to a), each foot sunk well into the ground."""
    noise = lattice(seed)
    p = Piece()
    (ax, ay, az), (bx, by, bz) = a, b
    span = math.hypot(bx - ax, by - ay)
    rise = max(900.0, span * .55)
    sx, sy = -(by - ay) / span, (bx - ax) / span           # across the bow, horizontal
    rings = []
    n = 44
    for i in range(n + 1):
        t = -.1 + 1.2 * i / n
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        z = az + (bz - az) * min(1, max(0, t)) + rise * math.sin(math.pi * t)
        # Direction along the bow, for the cross-section's plane.
        dt = .01
        z2 = az + (bz - az) * min(1, max(0, t + dt)) + rise * math.sin(math.pi * (t + dt))
        tx, ty, tz = (bx - ax) * dt, (by - ay) * dt, z2 - z
        tl = math.sqrt(tx * tx + ty * ty + tz * tz)
        tx, ty, tz = tx / tl, ty / tl, tz / tl
        ux, uy, uz = ty * 0 - tz * sy, tz * sx - tx * 0, tx * sy - ty * sx   # up within the cross-section = t x side
        thick = 1.0 + .45 * (1 - math.sin(math.pi * min(1, max(0, t))))    # thicker at the feet
        ring = []
        for k in range(sides):
            q = 2 * math.pi * k / sides
            r = 1 + .18 * noise(x / 250, y / 250, z / 250 + math.cos(q)) + .06 * noise(x / 70 + math.sin(q), y / 70, z / 70)
            w, h = 380 * thick * r * math.cos(q), 260 * thick * r * math.sin(q)
            ring.append(p.add((x + sx * w + ux * h, y + sy * w + uy * h, z + uz * h)))
        rings.append(ring)
    for i in range(n):
        for k in range(sides):
            a_, b_, c_, d_ = rings[i][k], rings[i][(k + 1) % sides], rings[i + 1][(k + 1) % sides], rings[i + 1][k]
            p.tris += [(a_, b_, c_), (a_, c_, d_)]
    for ring, sign in ((rings[0], -1), (rings[-1], 1)):
        mid = p.add(tuple(sum(p.verts[v][j] for v in ring) / sides for j in range(3)))
        for k in range(sides):
            u, v = ring[k], ring[(k + 1) % sides]
            p.tris.append((mid, u, v) if sign > 0 else (mid, v, u))
    # Winding was chosen by construction; make sure it faces out.
    return p.outward()


def snag(seed, height):
    """A giant dead tree: a flared, slowly twisting trunk broken off at the top, with bare branches."""
    from ship_geometry import Builder
    rng = random.Random(seed)
    b = Builder()
    lean = (rng.uniform(-.06, .06), rng.uniform(-.06, .06))
    trunk = [(lean[0] * z + 30 * math.sin(z / 500), lean[1] * z + 30 * math.cos(z / 650), z)
             for z in [-200.0] + [height * f for f in (0, .08, .2, .4, .6, .8, 1.0)]]
    radii = [150, 150, 115, 95, 80, 62, 45, 32]
    b.tube(trunk, lambda q: radii[q], sides=14, uv_of=lambda q, s: (s / 14 * 2, trunk[q][2] / 300))
    for n in range(rng.randint(5, 7)):
        f = rng.uniform(.35, .85)
        base = trunk[0]
        for (x0, y0, z0), (x1, y1, z1) in zip(trunk, trunk[1:]):
            if z0 <= height * f <= z1:
                w = (height * f - z0) / (z1 - z0)
                base = (x0 + (x1 - x0) * w, y0 + (y1 - y0) * w, height * f)
        a, length = rng.uniform(0, 2 * math.pi), rng.uniform(300, 650) * (1.2 - f * .5)
        up = rng.uniform(.3, .9)
        path = [base]
        for k in range(1, 4):
            g = k / 3
            path.append((base[0] + math.cos(a) * length * g, base[1] + math.sin(a) * length * g,
                         base[2] + length * g * up * (1 - .3 * g) + rng.uniform(-30, 30)))
        r0 = 40 * (1.1 - f * .5)
        b.tube(path, lambda q, r0=r0: r0 * (1.0, .7, .45, .2)[q], sides=8, uv_of=lambda q, s: (s / 8, q * .8))
    return b


def place(actors, mesh, x, y, z, yaw, label, scale=1.0):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
    actor.set_actor_label(label)
    actor.set_folder_path(LEVEL_FOLDER)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.static_mesh_component.set_static_mesh(mesh)
    return actor


def stone_mesh(piece, path, region):
    mesh = dynamic(piece, 0)
    uvs = unreal.GeometryScript_UVs
    uvs.set_num_uv_sets(mesh, 1)
    box = unreal.Transform(unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0), unreal.Vector(4, 4, 4))
    uvs.set_mesh_u_vs_from_box_projection(mesh, 0, box, unreal.GeometryScriptMeshSelection(), 2)
    unreal.GeometryScript_VertexColors.set_mesh_constant_vertex_color(mesh, unreal.LinearColor(0, 0, .6, 1), unreal.GeometryScriptColorFlags(), False)
    split = unreal.GeometryScriptSplitNormalsOptions()
    split.set_editor_property('split_by_opening_angle', True)
    split.set_editor_property('opening_angle_deg', 60.0)
    unreal.GeometryScript_Normals.compute_split_normals(mesh, split, unreal.GeometryScriptCalculateNormalsOptions())
    material = unreal.load_asset(f'{ROCKS}/MI_Rock_{STONE[region][0]}_v1')
    assert material
    return save_dynamic_mesh(mesh, path, [material])


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()).startswith(LEVEL_FOLDER):
            actors.destroy_actor(actor)
    standing = {}
    report = {}
    for key, mark in LANDMARKS.items():
        assert mark, f'{key} has no landmark'
        region, seed = mark.island.region, sum(map(ord, key)) * 13
        name = f'Landmark of {key}'
        tops = []
        if mark.kind in ('stacks', 'spire'):
            for n, (x, y, z, size) in enumerate(mark.parts):
                below = max(400.0, z - T.height(x + 600, y) + 400, 600.0 if mark.kind == 'stacks' else 400.0)
                radius = size * (.17 if mark.kind == 'stacks' else .13)
                hoodoo = mark.kind == 'spire' and region == 'Desert'
                height = size + max(0.0, T.SEA - z)            # a stack's size is how far it stands out of the sea
                mesh = stone_mesh(column(seed + n, height, radius, below, hoodoo), f'{FOLDER}/SM_{key}_{mark.kind}_{n + 1}_v1', region)
                place(actors, mesh, x, y, z, 0, f'{name}: {mark.kind} {n + 1}')
                tops.append(round((z + height) / 100, 1))
        elif mark.kind == 'arch':
            (ax, ay, az, _), (bx, by, bz, _) = mark.parts
            mesh = stone_mesh(arch(seed, (0.0, 0.0, 0.0), (bx - ax, by - ay, bz - az)), f'{FOLDER}/SM_{key}_arch_v1', region)
            place(actors, mesh, ax, ay, az, 0, f'{name}: arch')
        elif mark.kind == 'stones':
            if region not in standing:
                material = unreal.load_asset(f'{ROCKS}/MI_Rock_{STONE[region][0]}_v1')
                standing[region] = [write_static_mesh(boulder(900 + k, (140.0, 75.0, 760.0), cuts=3), f'{FOLDER}/SM_StandingStone_{region}_{k + 1}_v1',
                                                      [material], 120.0) for k in range(3)]
            cx = sum(p[0] for p in mark.parts) / len(mark.parts)
            cy = sum(p[1] for p in mark.parts) / len(mark.parts)
            for n, (x, y, z, scale) in enumerate(mark.parts):
                yaw = math.degrees(math.atan2(y - cy, x - cx)) + 90
                place(actors, standing[region][n % 3], x, y, z - 20, yaw, f'{name}: stone {n + 1}', scale)
        elif mark.kind == 'snag':
            x, y, z, size = mark.parts[0]
            bark = unreal.load_asset(BARK)
            mesh = write_static_mesh(snag(seed, size), f'{FOLDER}/SM_{key}_snag_v1', [bark], 120.0)
            place(actors, mesh, x, y, z, 0, f'{name}: snag')
            tops.append(round((z + size) / 100, 1))
        report[key] = {'kind': mark.kind, 'parts': len(mark.parts), 'tops_m': tops,
                       'at_m': [round(mark.parts[0][0] / 100), round(mark.parts[0][1] / 100)]}
    # The sand and sandstone pillars (world_landmarks.PILLARS): columns in the region's stone, some hoodoos.
    pillars = {}
    for key, mark in PILLARS.items():
        if not mark:
            continue
        region, seed = mark.island.region, sum(map(ord, key)) * 29
        rng = random.Random(seed)
        tops = []
        for n, (x, y, z, size) in enumerate(mark.parts):
            below = max(400.0, z - min(T.height(x + 500 * math.cos(b), y + 500 * math.sin(b)) for b in (0, 1.57, 3.14, 4.71)) + 300)
            mesh = stone_mesh(column(seed + n, size, size * rng.uniform(.12, .18), below, hoodoo=rng.random() < .4),
                              f'{FOLDER}/SM_{key}_pillar_{n + 1}_v1', region)
            place(actors, mesh, x, y, z, rng.uniform(0, 360), f'Pillar of {key} {n + 1}')
            tops.append(round(size / 100, 1))
        pillars[key] = tops
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'LandmarksResult.json').write_text(json.dumps({'success': True, 'landmarks': report, 'pillars_m': pillars}, indent=2))
    unreal.log(f'Landmarks built: {len(report)}')


if __name__ == '__main__':
    main()
