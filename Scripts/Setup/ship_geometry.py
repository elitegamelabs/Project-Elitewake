"""Shared geometry for ship scripts: a mesh builder and the writer that turns it into a static mesh asset.

The builder works in a ship's own space, in cm. Each vertex carries colour flags read by the timber material:
R tar, G iron, B plank tone (0.5 neutral). Each triangle carries a material slot.
"""
import math
import unreal

TIMBER_MATERIAL = '/Game/Elitewake/World/Ships/M_ShipTimber_v1'


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a):
    length = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / length, a[1] / length, a[2] / length)


class Builder:
    """Vertices with colour flags and optional fixed UVs; triangles oriented to face a hint direction and
    tagged with the current material slot."""

    def __init__(self):
        self.verts, self.colours, self.uvs, self.tris, self.slots = [], [], [], [], []
        self.alphas = []   # each vertex colour's alpha (1 unless set), apart so colours stay (r, g, b)
        self.slot = 0

    def vertex(self, p, tar=0.0, iron=0.0, tone=0.5, uv=None, alpha=1.0):
        self.verts.append(p)
        self.colours.append((tar, iron, tone))
        self.alphas.append(alpha)
        self.uvs.append(uv)
        return len(self.verts) - 1

    def tri(self, a, b, c, hint):
        n = cross(sub(self.verts[b], self.verts[a]), sub(self.verts[c], self.verts[a]))
        if dot(n, hint) < 0:
            b, c = c, b
        self.tris.append((a, b, c))
        self.slots.append(self.slot)

    def quad(self, a, b, c, d, hint):
        self.tri(a, b, c, hint)
        self.tri(a, c, d, hint)

    def grid(self, rows, hint_of, skip=None, tar_of=None, tone_of=None, uv_of=None, colour_of=None):
        """rows[i][j] points; quads between neighbours face hint_of(i, j). colour_of(i, j), if given, sets each
        vertex's whole colour (r, g, b, a) instead of tar and tone."""
        def make(i, j, p):
            if colour_of:
                r, g, b_, a = colour_of(i, j)
                return self.vertex(p, r, g, b_, uv_of(i, j, p) if uv_of else None, alpha=a)
            return self.vertex(p, tar_of(p) if tar_of else 0.0, 0.0, tone_of(i, j) if tone_of else 0.5,
                               uv_of(i, j, p) if uv_of else None)
        ids = [[make(i, j, p) for j, p in enumerate(row)] for i, row in enumerate(rows)]
        for i in range(len(rows) - 1):
            for j in range(len(rows[i]) - 1):
                if skip and skip(i, j):
                    continue
                self.quad(ids[i][j], ids[i + 1][j], ids[i + 1][j + 1], ids[i][j + 1], hint_of(i, j))
        return ids

    def box(self, centre, size, iron=0.0, tar=0.0):
        cx, cy, cz = centre
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        for axis in range(3):
            for sign in (-1, 1):
                corners = []
                for u in (-1, 1):
                    for v in (-1, 1):
                        p = [0, 0, 0]
                        p[axis] = sign
                        p[(axis + 1) % 3] = u
                        p[(axis + 2) % 3] = v
                        corners.append((cx + p[0] * hx, cy + p[1] * hy, cz + p[2] * hz))
                hint = [0, 0, 0]
                hint[axis] = sign
                ids = [self.vertex(c, tar, iron) for c in corners]
                self.quad(ids[0], ids[1], ids[3], ids[2], tuple(hint))

    def sweep(self, path, width, height, side=(0, 1, 0), iron=0.0, tar=0.0, capped=True, uv_of=None):
        """A rectangular timber (or rope) along a polyline; `side` is the direction of its width."""
        rings = []
        for k, p in enumerate(path):
            t = norm(sub(path[min(k + 1, len(path) - 1)], path[max(k - 1, 0)]))
            up = norm(cross(t, side))
            sd = cross(up, t)
            ring = []
            for su, uu in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                q = (p[0] + sd[0] * su * width / 2 + up[0] * uu * height / 2,
                     p[1] + sd[1] * su * width / 2 + up[1] * uu * height / 2,
                     p[2] + sd[2] * su * width / 2 + up[2] * uu * height / 2)
                ring.append(self.vertex(q, tar, iron, uv=uv_of(k, q) if uv_of else None))
            rings.append((ring, sd, up, t))
        for k in range(len(rings) - 1):
            r0, sd, up, _ = rings[k]
            r1 = rings[k + 1][0]
            for f in range(4):
                g = (f + 1) % 4
                hint = [(-up[0], -up[1], -up[2]), sd, up, (-sd[0], -sd[1], -sd[2])][f]
                self.quad(r0[f], r1[f], r1[g], r0[g], hint)
        if capped:
            for end, sign in ((rings[0], -1), (rings[-1], 1)):
                ring, _, _, t = end
                self.quad(ring[0], ring[1], ring[2], ring[3], (t[0] * sign, t[1] * sign, t[2] * sign))

    def tube(self, path, radius, sides=10, iron=0.0, capped=True, uv_of=None):
        """A round spar or rope along a polyline."""
        rings = []
        for k, p in enumerate(path):
            t = norm(sub(path[min(k + 1, len(path) - 1)], path[max(k - 1, 0)]))
            r = radius(k) if callable(radius) else radius
            ref = (0, 0, 1) if abs(t[2]) < 0.9 else (1, 0, 0)
            a = norm(cross(t, ref))
            b = cross(t, a)
            ring = []
            for s in range(sides + 1):
                ang = 2 * math.pi * s / sides
                q = (p[0] + r * (a[0] * math.cos(ang) + b[0] * math.sin(ang)),
                     p[1] + r * (a[1] * math.cos(ang) + b[1] * math.sin(ang)),
                     p[2] + r * (a[2] * math.cos(ang) + b[2] * math.sin(ang)))
                ring.append(self.vertex(q, 0.0, iron, uv=uv_of(k, s) if uv_of else None))
            rings.append((ring, a, b, t))
        for k in range(len(rings) - 1):
            r0, a, b, _ = rings[k]
            r1 = rings[k + 1][0]
            for s in range(sides):
                ang = 2 * math.pi * (s + 0.5) / sides
                hint = tuple(a[i] * math.cos(ang) + b[i] * math.sin(ang) for i in range(3))
                self.quad(r0[s], r1[s], r1[s + 1], r0[s + 1], hint)
        if capped:
            for (ring, _, _, t), sign in ((rings[0], -1), (rings[-1], 1)):
                centre = self.vertex(path[0] if sign < 0 else path[-1], 0.0, iron)
                for s in range(sides):
                    self.tri(centre, ring[s], ring[s + 1], (t[0] * sign, t[1] * sign, t[2] * sign))

    def cylinder(self, base, radius, height, sides=16, iron=0.0):
        x, y, z = base
        self.tube([(x, y, z), (x, y, z + height)], radius, sides, iron)


def triplanar_uv(p, n, tile):
    """Local triplanar mapping chosen so planks and boards run fore and aft."""
    ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
    if ay >= ax and ay >= az:
        return (p[2] / tile, p[0] / tile)
    if az >= ax:
        return (p[1] / tile, p[0] / tile)
    return (p[1] / tile, p[2] / tile)


def material_builder(path, parent=unreal.Material):
    """Create (or empty) a material and return it with node helpers."""
    assets = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    folder, name = path.rsplit('/', 1)
    material = unreal.load_asset(path) or assets.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(material)

    def node(cls, **props):
        n = mel.create_material_expression(material, cls)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def custom(code, kind, inputs):
        n = node(unreal.MaterialExpressionCustom, code=code, output_type=kind)
        pins = []
        for name_ in inputs:
            pin = unreal.CustomInput()
            pin.set_editor_property('input_name', name_)
            pins.append(pin)
        n.set_editor_property('inputs', pins)
        return n

    return material, node, custom


def make_timber_material():
    """Weathered oak from the dock's timber texture, warmed toward the art; vertex colours add tar, iron and
    a per-plank tone."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(TIMBER_MATERIAL)
    timber = node(unreal.MaterialExpressionTextureSample, texture=unreal.load_asset('/Game/Elitewake/World/Materials/T_Timber_v1'))
    flags = node(unreal.MaterialExpressionVertexColor)
    colour = custom('float3 oak = Wood * float3(0.98, 0.7, 0.44);'
                    ' float3 tarred = Wood * float3(0.2, 0.16, 0.13);'
                    ' float3 c = lerp(oak, tarred, Flags.r) * lerp(0.72, 1.15, Flags.b);'
                    ' return lerp(c, float3(0.05, 0.05, 0.055), Flags.g);',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('Wood', 'Flags'))
    rough = custom('return lerp(lerp(0.82, 0.62, Flags.r), 0.45, Flags.g);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('Flags',))
    metal = custom('return Flags.g * 0.85;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('Flags',))
    assert mel.connect_material_expressions(timber, 'RGB', colour, 'Wood')
    for n in (colour, rough, metal):
        assert mel.connect_material_expressions(flags, '', n, 'Flags')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(metal, '', unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def write_static_mesh(b, path, materials, uv_tile, collision=True, split_angle=40.0):
    """Write the builder into a static mesh asset, in place if it exists so references keep working.
    `materials` lists one material per slot; fixed vertex UVs win over the triplanar fallback. Normals are split
    (a hard edge) where faces meet at more than `split_angle` degrees."""
    geo = unreal.GeometryScript_MeshEdits
    lists = unreal.GeometryScript_List
    mesh = unreal.DynamicMesh()
    geo.add_vertices_to_mesh(mesh, lists.convert_array_to_vector_list([unreal.Vector(*p) for p in b.verts]))
    # The builder winds triangles counter-clockwise about their outward normal; Unreal's front faces wind the other way.
    geo.add_triangles_to_mesh(mesh, lists.convert_array_to_triangle_list([unreal.IntVector(a, c, d) for a, d, c in b.tris]))
    uvs = unreal.GeometryScript_UVs
    uvs.set_num_uv_sets(mesh, 1)
    for tid, (a, d, c) in enumerate(b.tris):  # a fresh mesh numbers triangles in the order they were added
        n = cross(sub(b.verts[c], b.verts[a]), sub(b.verts[d], b.verts[a]))
        corner = unreal.GeometryScriptUVTriangle()
        fixed = all(b.uvs[v] is not None for v in (a, c, d))
        for name, v in (('uv0', a), ('uv1', c), ('uv2', d)):
            corner.set_editor_property(name, unreal.Vector2D(*(b.uvs[v] if fixed else triplanar_uv(b.verts[v], n, uv_tile))))
        uvs.set_mesh_triangle_u_vs(mesh, 0, tid, corner)
    unreal.GeometryScript_VertexColors.set_mesh_per_vertex_colors(
        mesh, lists.convert_array_to_color_list([unreal.LinearColor(r, g, t, a) for (r, g, t), a in
                                                 zip(b.colours, b.alphas + [1.0] * (len(b.colours) - len(b.alphas)))]))
    if len(materials) > 1:
        unreal.GeometryScript_Materials.enable_material_i_ds(mesh)
        unreal.GeometryScript_Materials.set_all_triangle_material_i_ds(mesh, lists.convert_array_to_index_list(b.slots))
    split = unreal.GeometryScriptSplitNormalsOptions()
    split.set_editor_property('split_by_opening_angle', True)
    split.set_editor_property('opening_angle_deg', split_angle)
    unreal.GeometryScript_Normals.compute_split_normals(mesh, split, unreal.GeometryScriptCalculateNormalsOptions())
    return save_dynamic_mesh(mesh, path, materials, collision)


def save_dynamic_mesh(mesh, path, materials, collision=True):
    """Write a finished dynamic mesh (normals already set) into a static mesh asset, in place if it exists."""
    asset = unreal.load_asset(path)
    if asset:
        options = unreal.GeometryScriptCopyMeshToAssetOptions()
        options.set_editor_property('enable_recompute_normals', False)
        options.set_editor_property('enable_recompute_tangents', True)
        options.set_editor_property('replace_materials', True)
        options.set_editor_property('new_materials', materials)
        _, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(mesh, asset, options, unreal.GeometryScriptMeshWriteLOD())
        assert outcome == unreal.GeometryScriptOutcomePins.SUCCESS, outcome
    else:
        create = unreal.GeometryScriptCreateNewStaticMeshAssetOptions(enable_collision=collision,
                                                                      enable_recompute_normals=False, enable_recompute_tangents=True)
        asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(mesh, path, create)
        assert asset, outcome
        for slot, material in enumerate(materials):
            asset.set_material(slot, material)
    if collision:
        asset.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset
