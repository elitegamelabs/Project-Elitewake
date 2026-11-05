"""Build one cave on every island of the five-region world. Safe to run again. Run in the editor after
build_coastal_terrain.py (whose ground is notched under each cave) and before the dressing scripts, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner, October 14 (WORLD_STRUCTURE_OWNER_DECISIONS): one cave system per island, the entrances placed differently:
in inland hills, in cliff faces and in coastal rock formations; Winter's partway up the mountains. world_terrain.py
chooses each island's site (CAVES). Each cave is one rock formation in its region's stone: a mouth in a rock face,
a passage about 4.5 m wide and 4.5 m high that swings to one side and back, and a chamber about 12 m across at its
end, with a flat rock floor throughout. The formation is solid to walk on and against (its collision is the mesh
itself), sits over ground notched below its floor, and its inside is stone without the Winter snow. Caves are dark:
bring a torch. Cave contents (gem deposits, treasure sites, chests, Giant Spiders) are not built yet. Sizes tuning.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_terrain as T  # noqa: E402
from ship_geometry import save_dynamic_mesh  # noqa: E402
from build_coastal_rocks import lattice  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Caves'
ROCKS = '/Game/Elitewake/World/Rocks'
LEVEL_FOLDER = 'World/Caves'
# Region stone outside, and inside (no snow in a cave), from build_coastal_rocks.py's stones.
STONE = {'Plains': ('Granite', 'Granite'), 'Desert': ('Sandstone', 'Sandstone'), 'Winter': ('GraniteSnow', 'Granite'),
         'Jungle': ('Basalt', 'Basalt'), 'Swamp': ('Basalt', 'Basalt')}
STEP = 100.0          # the formation's surface grid, cm
FACE = 750.0          # the rock face's height over the mouth, cm (tuning)
CROWN = 300.0         # how much higher the formation stands over the chamber


class Piece:
    """A closed triangle mesh: vertices relative to the cave's mouth at floor level, triangles counter-clockwise
    about their outward normal."""

    def __init__(self):
        self.verts, self.tris = [], []

    def add(self, p):
        self.verts.append(p)
        return len(self.verts) - 1

    def volume(self):
        total = 0.0
        for a, b, c in self.tris:
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = self.verts[a], self.verts[b], self.verts[c]
            total += ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)
        return total / 6.0

    def outward(self):
        if self.volume() < 0:
            self.tris = [(a, c, b) for a, b, c in self.tris]
        assert self.volume() > 0
        return self


def formation(cave, noise):
    """The rock formation, solid: its top follows the island's ground a little above it and rises into a rock face
    over the mouth and a crown over the chamber; its sides go down past the notched ground to a flat bottom."""
    p = Piece()
    nu, nv = max(8, int(cave.depth / STEP) + 1), max(8, int(2 * cave.half / STEP) + 1)
    back0 = cave.chamber_u + cave.chamber[0]

    def width(u):
        if u <= back0:
            return cave.half
        f = (u - back0) / (cave.depth - back0)
        return cave.half * math.sqrt(max(.15, 1 - f * f))

    top, flat, lowest = [], [], cave.floor
    for i in range(nu):
        u = cave.depth * i / (nu - 1)
        rise = min(1.0, u / cave.chamber_u)
        rise = rise * rise * (3 - 2 * rise)
        height = cave.face + cave.crown * rise
        if u > back0:
            taper = max(0.0, 1 - (u - back0) / (cave.depth - back0)) ** .6
            # Keep a rock wall around the landward portal rather than tapering its roof to ground.
            height *= .6 + .4 * taper if cave.island.key in ('Plains3', 'Desert3') else taper
        row, frow = [], []
        for j in range(nv):
            t = -1 + 2 * j / (nv - 1)
            x, y = cave.world(u, t * width(u))
            ground = T.height_raw(x, y)
            lowest = min(lowest, ground)
            lat = math.sqrt(max(0.0, 1 - t * t))
            # Broad bulges and knobs, never cutting down far enough to thin the roof.
            lumps = noise(x / 900, y / 900, .3) * 260 + noise(x / 300, y / 300, 2.7) * 90 + noise(x / 110, y / 110, 4.1) * 25
            z = max(cave.floor + height * lat, ground + 40 + 150 * lat) + max(lumps, -50.0) * (.35 + .65 * lat)
            row.append(p.add((x - cave.mx, y - cave.my, z - cave.floor)))
            frow.append((x - cave.mx, y - cave.my))
        top.append(row)
        flat.append(frow)
    bottom_z = lowest - 400 - cave.floor
    bottom = [[p.add((x, y, bottom_z)) for x, y in frow] for frow in flat]
    for i in range(nu - 1):
        for j in range(nv - 1):
            a, b, c, d = top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]
            p.tris += [(a, b, c), (a, c, d)]
            a, b, c, d = bottom[i][j], bottom[i + 1][j], bottom[i + 1][j + 1], bottom[i][j + 1]
            p.tris += [(a, c, b), (a, d, c)]
    # The sides: the boundary counter-clockwise from above, bulging out a little and roughened between top and bottom.
    ring = [(i, 0) for i in range(nu)] + [(nu - 1, j) for j in range(1, nv)] + \
           [(i, nv - 1) for i in range(nu - 2, -1, -1)] + [(0, j) for j in range(nv - 2, 0, -1)]
    c, s = math.cos(cave.heading), math.sin(cave.heading)
    levels = 5
    columns = []
    for i, j in ring:
        ou = -1.0 if i == 0 else (1.0 if i == nu - 1 else 0.0)
        ov = -1.0 if j == 0 else (1.0 if j == nv - 1 else 0.0)
        length = math.hypot(ou, ov)
        ox, oy = (ou * c - ov * s) / length, (ou * s + ov * c) / length
        x, y, z = p.verts[top[i][j]]
        column = [top[i][j]]
        for k in range(1, levels):
            f = k / levels
            wz = z + (bottom_z - z) * f
            push = 70 * math.sin(math.pi * f) + 55 * noise((x + cave.mx) / 160, (y + cave.my) / 160, wz / 160 + 7.7)
            column.append(p.add((x + ox * push, y + oy * push, wz)))
        column.append(bottom[i][j])
        columns.append(column)
    for n in range(len(columns)):
        pc, qc = columns[n], columns[(n + 1) % len(columns)]
        for k in range(levels):
            p.tris += [(pc[k], pc[k + 1], qc[k + 1]), (pc[k], qc[k + 1], qc[k])]
    return p.outward()


def passage(cave, noise, sides=22):
    """The passage as a solid to cut away: rings across the way in, flaring at the mouth, from outside the face to
    inside the chamber."""
    p = Piece()
    hw, hh, cz = cave.tunnel
    lumps = T.SEA_NOISE[0] if cave.kind == 'sea' else .14
    rings, u = [], -400.0
    end = cave.length + cave.chamber[0] * .6
    while True:
        flare = 1.0 + .3 * max(0.0, 1 - u / 350.0)
        vc = cave.centre_v(u)
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            bx, by = cave.world(u, vc + hw * math.cos(a))
            bz = cz + hh * math.sin(a)
            r = flare * (1 + lumps * noise(bx / 230, by / 230, bz / 230 + 2.2))
            x, y = cave.world(u, vc + hw * math.cos(a) * r)
            ring.append(p.add((x - cave.mx, y - cave.my, cz + hh * math.sin(a) * r)))
        rings.append(ring)
        if u >= end:
            break
        u = min(end, u + 60.0)
    for i in range(len(rings) - 1):
        for k in range(sides):
            a, b, c, d = rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % sides], rings[i][(k + 1) % sides]
            p.tris += [(a, c, b), (a, d, c)]
    for ring, sign in ((rings[0], -1), (rings[-1], 1)):
        mid = [sum(p.verts[v][n] for v in ring) / sides for n in range(3)]
        z = p.add(tuple(mid))
        for k in range(sides):
            a, b = ring[k], ring[(k + 1) % sides]
            p.tris.append((z, a, b) if sign > 0 else (z, b, a))
    return p.outward()


def chamber(cave, noise, rows=16, sides=28):
    """The chamber as a solid to cut away: a lumpy dome, wider than high."""
    p = Piece()
    cu, cv, cz = cave.chamber
    centre_u, centre_z = cave.chamber_u, cave.chamber_z
    lumps = T.SEA_NOISE[1] if cave.kind == 'sea' else .16

    def point(theta, phi):
        u, v, z = cu * math.sin(theta) * math.cos(phi), cv * math.sin(theta) * math.sin(phi), cz * math.cos(theta)
        bx, by = cave.world(centre_u + u, v)
        r = 1 + lumps * noise(bx / 300, by / 300, (centre_z + z) / 300 + 5.5)
        x, y = cave.world(centre_u + u * r, v * r)
        return p.add((x - cave.mx, y - cave.my, centre_z + z * r))

    top, low = point(0.0, 0.0), point(math.pi, 0.0)
    rings = [[point(math.pi * i / rows, 2 * math.pi * k / sides) for k in range(sides)] for i in range(1, rows)]
    for i in range(len(rings) - 1):
        for k in range(sides):
            a, b, c, d = rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % sides], rings[i][(k + 1) % sides]
            p.tris += [(a, b, c), (a, c, d)]
    for k in range(sides):
        p.tris.append((top, rings[0][k], rings[0][(k + 1) % sides]))
        p.tris.append((low, rings[-1][(k + 1) % sides], rings[-1][k]))
    return p.outward()


def exit_frames(cave):
    """Along the walk out (world_terrain.Cave.exit_path): (u, v, surface, nu, nv, outward) with (nu, nv) the walk's
    right-hand normal in the cave's frame."""
    pts = cave.exit_path()
    out = []
    for i, (u, v, z, o) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        out.append((u, v, z, (b[1] - a[1]) / length, -(b[0] - a[0]) / length, o))
    return out


def at(cave, frame, lateral, z):
    """A point `lateral` cm to the walk's right of a frame, at world height z, relative to the cave's mouth."""
    u, v, _, nu, nv, _ = frame
    x, y = cave.world(u + nu * lateral, v + nv * lateral)
    return x - cave.mx, y - cave.my, z - cave.floor


def inland_exit_tunnel(cave, sides=20):
    """Bore the walk out through the rock: from the berth chamber's rear on the straight exits, and the whole way on
    Jungle3's spiral, which runs along and then through the chamber's wall."""
    p = Piece()
    frames = exit_frames(cave)
    if cave.island.key not in cave.SPIRAL:
        frames = [f for f in frames if f[0] >= cave.chamber_u + .4 * cave.chamber[0]]
    rings = []
    for frame in frames:
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            ring.append(p.add(at(cave, frame, 350.0 * math.cos(a), frame[2] + 235.0 + 325.0 * math.sin(a))))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(sides):
            a, b = rings[i][k], rings[i][(k + 1) % sides]
            c, d = rings[i + 1][k], rings[i + 1][(k + 1) % sides]
            p.tris += [(a, c, b), (b, c, d)]
    for ring, sign in ((rings[0], -1), (rings[-1], 1)):
        centre = p.add(tuple(sum(p.verts[v][n] for v in ring) / sides for n in range(3)))
        for k in range(sides):
            a, b = ring[k], ring[(k + 1) % sides]
            p.tris.append((centre, b, a) if sign > 0 else (centre, a, b))   # wound to match the sides
    return p.outward()


def inland_exit_ramp(cave):
    """Colliding 4.5 m wide walk to existing island ground: a causeway (Plains3), a deck on piers (Desert3), or a
    ledge cut from the chamber wall with its rock sloping back into the wall beneath it (Jungle3)."""
    p = Piece()
    frames = exit_frames(cave)
    spiral = cave.island.key in cave.SPIRAL

    def strip(chosen, left, right, top_of, bottom_of, bottom_right=None):
        """A solid strip between `left` and `right` of the walk; `bottom_right` sets the lower outer edge apart."""
        sections = []
        for f in chosen:
            low_right = bottom_right or (lambda z: (right, bottom_of(z)))
            lr, lz = low_right(f[2])
            section = [p.add(at(cave, f, left * f[5], top_of(f[2]))), p.add(at(cave, f, right * f[5], top_of(f[2]))),
                       p.add(at(cave, f, left * f[5], bottom_of(f[2]))), p.add(at(cave, f, lr * f[5], lz))]
            sections.append(section)
        for a, b in zip(sections, sections[1:]):
            p.tris += [(a[0], b[0], b[1]), (a[0], b[1], a[1]),
                       (a[2], b[3], b[2]), (a[2], a[3], b[3]),
                       (a[0], a[2], b[2]), (a[0], b[2], b[0]),
                       (a[1], b[1], b[3]), (a[1], b[3], a[3])]
        for a, sign in ((sections[0], -1), (sections[-1], 1)):
            p.tris += ([(a[0], a[1], a[3]), (a[0], a[3], a[2])] if sign < 0 else
                       [(a[0], a[3], a[1]), (a[0], a[2], a[3])])

    if spiral:
        # The ledge: its outer side runs 10 m back into the wall, falling 15 m, so from the water it reads as rock.
        strip(frames, -225, 225, lambda z: z, lambda z: z - 150, lambda z: (1225, z - 1500))
    else:
        bottom = (lambda z: z - 60) if cave.island.key == 'Desert3' else (lambda z: cave.floor - 40)
        strip(frames, -225, 225, lambda z: z, bottom)
    # Low stone parapets keep walkers away from the drop (on a spiral, its inner side only). The first 6 m and last
    # 7 m stay open so a crew can step from the boat and onto shore.
    travelled, along = 0.0, [0.0]
    for a, b in zip(frames, frames[1:]):
        travelled += math.hypot(b[0] - a[0], b[1] - a[1])
        along.append(travelled)
    guarded = [f for f, d in zip(frames, along) if 600.0 <= d <= travelled - 700.0]
    for left, right in ((-225, -195),) if spiral else ((-225, -195), (195, 225)):
        strip(guarded, left, right, lambda z: z + 95, lambda z: z)
    return p.outward()


# ---- Unreal ---------------------------------------------------------------------------------------------------

def dynamic(piece, material_id):
    geo, lists = unreal.GeometryScript_MeshEdits, unreal.GeometryScript_List
    mesh = unreal.DynamicMesh()
    geo.add_vertices_to_mesh(mesh, lists.convert_array_to_vector_list([unreal.Vector(*v) for v in piece.verts]))
    # Counter-clockwise about the outward normal here; Unreal's front faces wind the other way.
    geo.add_triangles_to_mesh(mesh, lists.convert_array_to_triangle_list([unreal.IntVector(a, c, b) for a, b, c in piece.tris]))
    unreal.GeometryScript_Materials.enable_material_i_ds(mesh)
    unreal.GeometryScript_Materials.set_all_triangle_material_i_ds(
        mesh, lists.convert_array_to_index_list([material_id] * len(piece.tris)))
    return mesh


def boolean(target, tool, operation):
    options = unreal.GeometryScriptMeshBooleanOptions()
    options.set_editor_property('fill_holes', True)
    return unreal.GeometryScript_MeshBooleans.apply_mesh_boolean(target, unreal.Transform(), tool, unreal.Transform(), operation, options)


def bounds(mesh):
    box = unreal.GeometryScript_MeshQueries.get_mesh_bounding_box(mesh)
    return box.get_editor_property('min'), box.get_editor_property('max')


def hollow(cave, noise):
    """The passage and chamber joined, cut flat at the floor so the cave keeps a rock floor."""
    for flip in (False, True):
        tool = dynamic(passage(cave, noise), 1)
        boolean(tool, dynamic(chamber(cave, noise), 1), unreal.GeometryScriptBooleanOperation.UNION)
        if T.W.SEA_CAVERN_ACCESS.get(cave.island.key):
            boolean(tool, dynamic(inland_exit_tunnel(cave), 1), unreal.GeometryScriptBooleanOperation.UNION)
        options = unreal.GeometryScriptMeshPlaneCutOptions()
        options.set_editor_property('fill_holes', True)
        options.set_editor_property('flip_cut_side', flip)
        unreal.GeometryScript_MeshBooleans.apply_mesh_plane_cut(tool, unreal.Transform(), options)
        low, high = bounds(tool)
        if low.z > -2 and high.z > 300:
            return tool
    raise RuntimeError(f'could not cut the {cave.island.key} cave flat at its floor ({low.z:.0f}..{high.z:.0f})')


def cave_mesh(cave):
    noise = lattice(sum(map(ord, cave.island.key)) * 31)
    mesh = dynamic(formation(cave, noise), 0)
    boolean(mesh, hollow(cave, noise), unreal.GeometryScriptBooleanOperation.SUBTRACT)
    uvs = unreal.GeometryScript_UVs
    uvs.set_num_uv_sets(mesh, 1)
    box = unreal.Transform(unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0), unreal.Vector(4, 4, 4))
    uvs.set_mesh_u_vs_from_box_projection(mesh, 0, box, unreal.GeometryScriptMeshSelection(), 2)
    unreal.GeometryScript_VertexColors.set_mesh_constant_vertex_color(
        mesh, unreal.LinearColor(0, 0, .6, 1), unreal.GeometryScriptColorFlags(), False)
    split = unreal.GeometryScriptSplitNormalsOptions()
    split.set_editor_property('split_by_opening_angle', True)
    split.set_editor_property('opening_angle_deg', 50.0)
    unreal.GeometryScript_Normals.compute_split_normals(mesh, split, unreal.GeometryScriptCalculateNormalsOptions())
    outer, inner = STONE[cave.island.region]
    materials = [unreal.load_asset(f'{ROCKS}/MI_Rock_{outer}_v1'), unreal.load_asset(f'{ROCKS}/MI_Rock_{inner}_v1')]
    assert all(materials), materials
    asset = save_dynamic_mesh(mesh, f'{FOLDER}/SM_Cave_{cave.island.key}_v1', materials)
    return asset, unreal.GeometryScript_MeshQueries.get_num_triangle_i_ds(mesh)


def exit_ramp_mesh(cave):
    mesh = dynamic(inland_exit_ramp(cave), 0)
    uvs = unreal.GeometryScript_UVs
    uvs.set_num_uv_sets(mesh, 1)
    box = unreal.Transform(unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0), unreal.Vector(4, 4, 4))
    uvs.set_mesh_u_vs_from_box_projection(mesh, 0, box, unreal.GeometryScriptMeshSelection(), 2)
    unreal.GeometryScript_Normals.compute_split_normals(mesh, unreal.GeometryScriptSplitNormalsOptions(),
                                                        unreal.GeometryScriptCalculateNormalsOptions())
    stone = STONE[cave.island.region][1]
    material = unreal.load_asset(f'{ROCKS}/MI_Rock_{stone}_v1')
    assert material
    return save_dynamic_mesh(mesh, f'{FOLDER}/SM_Cave_{cave.island.key}_ExitRamp_v1', [material])


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()).startswith(LEVEL_FOLDER):
            actors.destroy_actor(actor)
    report = {}
    for key, cave in T.CAVES.items():
        assert cave, f'{key} has no cave site'
        mesh, tris = cave_mesh(cave)
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(cave.mx, cave.my, cave.floor), unreal.Rotator())
        actor.set_actor_label(f'Cave of {key}: rock')
        actor.set_folder_path(LEVEL_FOLDER)
        actor.static_mesh_component.set_static_mesh(mesh)
        if T.W.SEA_CAVERN_ACCESS.get(key):
            ramp = actors.spawn_actor_from_class(unreal.StaticMeshActor,
                                                 unreal.Vector(cave.mx, cave.my, cave.floor), unreal.Rotator())
            ramp.set_actor_label(f'Cave of {key}: {"shore bridge" if key == "Desert3" else "inland exit ramp"}')
            ramp.set_folder_path(LEVEL_FOLDER)
            ramp.static_mesh_component.set_static_mesh(exit_ramp_mesh(cave))
            if key == 'Desert3':
                block = unreal.load_asset('/Engine/BasicShapes/Cube')
                stone = unreal.load_asset(f'{ROCKS}/MI_Rock_{STONE[cave.island.region][1]}_v1')
                assert block and stone
                path = [f for f in cave.exit_path() if f[0] <= cave.depth]
                for n in range(7):
                    u, lateral, surface, _ = path[round(n * (len(path) - 1) / 6)]
                    for side in (-180.0, 180.0):
                        x, y = cave.world(u, lateral + side)
                        bottom, top = cave.floor - 40.0, surface - 60.0
                        support = actors.spawn_actor_from_class(
                            unreal.StaticMeshActor, unreal.Vector(x, y, (bottom + top) / 2), unreal.Rotator())
                        support.set_actor_label(f'Cave of {key}: bridge support {n}-{int(side)}')
                        support.set_folder_path(LEVEL_FOLDER)
                        support.static_mesh_component.set_static_mesh(block)
                        support.static_mesh_component.set_material(0, stone)
                        support.set_actor_scale3d(unreal.Vector(.7, .7, (top - bottom) / 100.0))
        report[key] = {'kind': cave.kind, 'region': cave.island.region, 'mouth_cm': [round(cave.mx), round(cave.my)],
                       'floor_cm': round(cave.floor), 'heading_deg': round(math.degrees(cave.heading)),
                       'scale': cave.scale, 'entrance_width_cm': round(2 * cave.tunnel[0]),
                       'water_depth_cm': round(T.SEA - cave.floor) if cave.kind == 'sea' else 0,
                       'triangles': tris, 'access': T.W.SEA_CAVERN_ACCESS.get(key)}
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'CavesResult.json').write_text(json.dumps({'success': True, 'caves': report}, indent=2))
    unreal.log(f'Caves built: {len(report)}')


if __name__ == '__main__':
    main()
