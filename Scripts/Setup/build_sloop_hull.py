"""Build the sloop's hull mesh in Unreal from the owner's concept art (Art/Concepts/Boats/2026-10-11/Sloop-*).
Safe to run again. Run in the editor, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

A bare hull in weathered oak: planked sides with seams and two wales, a tarred bottom, a deep curved bow with a
tall stem post, a modest rounded stern, low bulwarks with a rail and posts, and one gunport each side. A flat deck
has a cargo hatch with a coaming and stairs down into a cramped hold of ribs, floorboards, deck beams and a post.
Boarding ladders on both sides and a capstan near the bow are part of the hull. Masts, sails, the helm and
cannons are fittings and are not built here.

Coordinates are the ship's own, in cm: X forward to the bow, Y to starboard, Z up, the waterline at Z 0. The hold
floor sits above the waves so the sea neither shows nor counts as swimmable inside. All sizes are tuning.
"""
import json
import math
from pathlib import Path
import unreal

MESH = '/Game/Elitewake/World/Ships/SM_SloopHull_v2'
MATERIAL = '/Game/Elitewake/World/Ships/M_ShipTimber_v1'
DEFINITION = '/Game/Elitewake/Ships/DA_Ship_Sloop'
MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'

STERN_X, BOW_X = -520.0, 540.0
BEAM = 185.0            # half-beam at its widest
KEEL_Z = -110.0
DECK_Z = 250.0          # deck top
DECK_THICK = 8.0
FLOOR_Z = 30.0          # hold floor top, above the swell
SHELL = 9.0             # planking thickness
HATCH = (-220.0, 20.0, 50.0)   # hatch opening: aft x, forward x, half-width
GUNPORT = (-60.0, 48.0, 268.0, 306.0)  # centre x, width, bottom z, top z
LADDER_X = -100.0
CAPSTAN = (380.0, -60.0)
UV_TILE = 120.0         # one timber texture repeat, in cm
STRAKES = 11


# ---- Hull lines --------------------------------------------------------------------------------------------

def half_beam(x):
    if x >= -40:
        return BEAM * max(0.0, 1 - ((x + 40) / (BOW_X + 40)) ** 2.2) ** 0.5
    return BEAM * (1 - 0.35 * ((-40 - x) / (-40 - STERN_X)) ** 2.2)


def sheer(x):
    """Top of the bulwark: low amidships, sweeping up to a high bow and a raised stern."""
    if x > 60:
        return 315 + 115 * ((x - 60) / (BOW_X - 60)) ** 2
    if x < -200:
        return 315 + 50 * ((-200 - x) / (-200 - STERN_X)) ** 2
    return 315.0


def keel(x):
    """Bottom of the hull: flat amidships, sweeping up into the stem at the bow and a little at the stern."""
    if x > 80:
        return KEEL_Z + (sheer(x) - 12 - KEEL_Z) * ((x - 80) / (BOW_X - 80)) ** 1.7
    if x < -430:
        return KEEL_Z + 70 * ((-430 - x) / (-430 - STERN_X)) ** 1.5
    return KEEL_Z


def fullness(x):
    """Superellipse exponent of the sections: full amidships, sharp at the bow."""
    if x > 150:
        return 2.8 - 1.2 * (x - 150) / (BOW_X - 150)
    if x < -300:
        return 2.8 - 0.5 * (-300 - x) / (-300 - STERN_X)
    return 2.8


def section_point(x, theta):
    """Outer hull at station x; theta runs from the keel (0) to the sheer (pi/2). Returns (y, z), starboard."""
    b, sh, kl, n = half_beam(x), sheer(x), keel(x), fullness(x)
    s, c = max(math.sin(theta), 0.0), max(math.cos(theta), 0.0)
    return b * s ** (2 / n), sh - (sh - kl) * c ** (2 / n)


def section_normal(x, theta):
    h = 1e-3
    y0, z0 = section_point(x, max(theta - h, 0.0))
    y1, z1 = section_point(x, min(theta + h, math.pi / 2))
    ty, tz = y1 - y0, z1 - z0
    ny, nz = tz, -ty
    length = math.hypot(ny, nz) or 1.0
    return ny / length, nz / length


def theta_at(x, z):
    """Section parameter where the outer hull reaches height z (clamped)."""
    lo, hi = 0.0, math.pi / 2
    for _ in range(40):
        mid = (lo + hi) / 2
        if section_point(x, mid)[1] < z:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def inner_y(x, z):
    """Inside face of the planking at height z, starboard."""
    t = theta_at(x, z)
    y, _ = section_point(x, t)
    ny, _ = section_normal(x, t)
    return max(y - SHELL * max(ny, 0.3), 0.0)


# ---- Mesh accumulator ------------------------------------------------------------------------------------------

def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Builder:
    """Vertices with colour flags (R tar, G iron, B plank tone, 0.5 neutral) and optional fixed UVs; triangles
    oriented to face a hint direction."""

    def __init__(self):
        self.verts, self.colours, self.uvs, self.tris = [], [], [], []

    def vertex(self, p, tar=0.0, iron=0.0, tone=0.5, uv=None):
        self.verts.append(p)
        self.colours.append((tar, iron, tone))
        self.uvs.append(uv)
        return len(self.verts) - 1

    def tri(self, a, b, c, hint):
        n = cross(sub(self.verts[b], self.verts[a]), sub(self.verts[c], self.verts[a]))
        if dot(n, hint) < 0:
            b, c = c, b
        self.tris.append((a, b, c))

    def quad(self, a, b, c, d, hint):
        self.tri(a, b, c, hint)
        self.tri(a, c, d, hint)

    def grid(self, rows, hint_of, skip=None, tar_of=None, tone_of=None, uv_of=None):
        """rows[i][j] points; quads between neighbours face hint_of(i, j)."""
        ids = [[self.vertex(p, tar_of(p) if tar_of else 0.0, 0.0, tone_of(i, j) if tone_of else 0.5,
                            uv_of(p) if uv_of else None)
                for j, p in enumerate(row)] for i, row in enumerate(rows)]
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

    def sweep(self, path, width, height, side=(0, 1, 0), iron=0.0, tar=0.0, capped=True):
        """A rectangular timber along a polyline; `side` is the direction of its width."""
        rings = []
        for k, p in enumerate(path):
            a = path[max(k - 1, 0)]
            b = path[min(k + 1, len(path) - 1)]
            t = sub(b, a)
            length = math.sqrt(dot(t, t)) or 1.0
            t = (t[0] / length, t[1] / length, t[2] / length)
            up = cross(t, side)
            ul = math.sqrt(dot(up, up)) or 1.0
            up = (up[0] / ul, up[1] / ul, up[2] / ul)
            sd = cross(up, t)
            ring = []
            for su, uu in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                q = (p[0] + sd[0] * su * width / 2 + up[0] * uu * height / 2,
                     p[1] + sd[1] * su * width / 2 + up[1] * uu * height / 2,
                     p[2] + sd[2] * su * width / 2 + up[2] * uu * height / 2)
                ring.append(self.vertex(q, tar, iron))
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

    def cylinder(self, base, radius, height, sides=16, iron=0.0):
        x, y, z = base
        ring0, ring1 = [], []
        for k in range(sides + 1):
            a = 2 * math.pi * k / sides
            ring0.append(self.vertex((x + radius * math.cos(a), y + radius * math.sin(a), z), 0.0, iron))
            ring1.append(self.vertex((x + radius * math.cos(a), y + radius * math.sin(a), z + height), 0.0, iron))
        for k in range(sides):
            a = 2 * math.pi * (k + 0.5) / sides
            self.quad(ring0[k], ring0[k + 1], ring1[k + 1], ring1[k], (math.cos(a), math.sin(a), 0))
        top = self.vertex((x, y, z + height), 0.0, iron)
        bottom = self.vertex((x, y, z), 0.0, iron)
        for k in range(sides):
            self.tri(top, ring1[k], ring1[k + 1], (0, 0, 1))
            self.tri(bottom, ring0[k], ring0[k + 1], (0, 0, -1))


def uv_for(p, n):
    """Local triplanar mapping chosen so planks and deck boards run fore and aft."""
    ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
    if ay >= ax and ay >= az:
        return (p[2] / UV_TILE, p[0] / UV_TILE)
    if az >= ax:
        return (p[1] / UV_TILE, p[0] / UV_TILE)
    return (p[1] / UV_TILE, p[2] / UV_TILE)


# ---- Parts -------------------------------------------------------------------------------------------------

STATIONS = [STERN_X + 20 * i for i in range(int((BOW_X - STERN_X) / 20) + 1)]


def strake_params():
    """Section samples with seam grooves between strakes and two raised wales: (theta, outward offset, strake)."""
    out = []
    span = (math.pi / 2) / STRAKES
    wales = {7, 9}
    for k in range(STRAKES):
        lift = 4.0 if k in wales else 0.0
        below = 4.0 if (k - 1) in wales else 0.0
        t0 = k * span
        if k > 0:
            out.append((t0, min(lift, below) - 2.0, k))  # seam groove
        for f in (0.1, 0.37, 0.63, 0.9):
            out.append((t0 + f * span, lift, k))
    out.append((math.pi / 2, 0.0, STRAKES - 1))
    return out


def plank_tone(*seed):
    """A steady pseudo-random 0..1 per plank, so neighbouring planks differ a little in colour."""
    v = math.sin(sum((k + 1) * 12.9898 * s for k, s in enumerate(seed)) + 0.5) * 43758.5453
    return v - math.floor(v)


def tarred(p):
    """The lower planking is tarred dark, showing well above the waterline as in the art."""
    return min(1.0, max(0.0, (75 - p[2]) / 40))


def along_hull(p):
    """Planking UVs: grain runs fore and aft wherever the hull curves."""
    return (p[2] / UV_TILE, p[0] / UV_TILE)


def in_gunport(x, z):
    cx, w, z0, z1 = GUNPORT
    return abs(x - cx) < w / 2 and z0 < z < z1


def outer_shell(b):
    params = strake_params()
    for side in (1, -1):
        rows = []
        for x in STATIONS:
            row = []
            for theta, lift, _ in params:
                y, z = section_point(x, theta)
                ny, nz = section_normal(x, theta)
                row.append((x, side * (y + ny * lift), z + nz * lift))
            rows.append(row)

        def hint(i, j, side=side):
            x = STATIONS[i]
            ny, nz = section_normal(x, params[j][0])
            return (0.3 if x > 300 else 0.0, side * ny, nz)

        def skip(i, j):
            x = (STATIONS[i] + STATIONS[i + 1]) / 2
            z = (rows[i][j][2] + rows[i][j + 1][2]) / 2
            return in_gunport(x, z)

        b.grid(rows, hint, skip, tar_of=tarred, tone_of=lambda i, j, side=side: plank_tone(params[j][2], side),
               uv_of=along_hull)


def inner_shell(b):
    for side in (1, -1):
        rows = []
        for x in STATIONS:
            t0 = theta_at(x, FLOOR_Z - 4) if keel(x) < FLOOR_Z - 4 else 0.0
            row = []
            for k in range(25):
                theta = t0 + (math.pi / 2 - t0) * k / 24
                y, z = section_point(x, theta)
                ny, nz = section_normal(x, theta)
                row.append((x, side * max(y - ny * SHELL, 0.0), z - nz * SHELL))
            rows.append(row)

        def hint(i, j, side=side):
            return (0.0, -side, 0.2)

        def skip(i, j):
            x = (STATIONS[i] + STATIONS[i + 1]) / 2
            z = (rows[i][j][2] + rows[i][j + 1][2]) / 2
            return in_gunport(x, z)

        b.grid(rows, hint, skip, uv_of=along_hull)


def transom(b):
    x = STERN_X
    params = [k / 30 * math.pi / 2 for k in range(31)]
    outer = [[(x, -section_point(x, t)[0], section_point(x, t)[1]) for t in params],
             [(x, section_point(x, t)[0], section_point(x, t)[1]) for t in params]]
    across = lambda p: (p[2] / UV_TILE, p[1] / UV_TILE)  # transom planks run athwartships
    b.grid(list(map(list, zip(*outer))), lambda i, j: (-1, 0, 0), tar_of=tarred, uv_of=across)
    xi = x + SHELL
    t0 = theta_at(x, FLOOR_Z - 4)
    inner_params = [t0 + (math.pi / 2 - t0) * k / 20 for k in range(21)]
    inner = [[(xi, -inner_y(x, section_point(x, t)[1]), section_point(x, t)[1]) for t in inner_params],
             [(xi, inner_y(x, section_point(x, t)[1]), section_point(x, t)[1]) for t in inner_params]]
    b.grid(list(map(list, zip(*inner))), lambda i, j: (1, 0, 0), uv_of=across)


def rail_and_keel(b):
    for side in (1, -1):
        path = [(x, side * (half_beam(x) - SHELL / 2), sheer(x) + 4.5) for x in STATIONS if half_beam(x) > 2]
        path.append((BOW_X - 2, 0.0, sheer(BOW_X) + 4.5))
        b.sweep(path, 16.0, 9.0, side=(0, 1, 0))
    stern_path = [(STERN_X + 4, y, sheer(STERN_X) + 4.5) for y in (-half_beam(STERN_X), half_beam(STERN_X))]
    b.sweep(stern_path, 16.0, 9.0, side=(1, 0, 0))
    # Keel along the bottom, then the stem rising out of it and standing proud above the bow.
    keel_path = [(x, 0.0, keel(x) - 6) for x in STATIONS if x <= 80]
    b.sweep(keel_path, 18.0, 14.0, tar=1.0)
    stem = [(x, 0.0, keel(x) - 4) for x in [80 + 20 * k for k in range(24)] if x <= BOW_X]
    stem += [(BOW_X + 12, 0.0, sheer(BOW_X) + 30), (BOW_X + 20, 0.0, sheer(BOW_X) + 60), (BOW_X + 14, 0.0, sheer(BOW_X) + 75)]
    b.sweep(stem, 20.0, 22.0)
    # Iron straps binding the stem.
    for k, x in enumerate((330, 430, 500)):
        z = keel(x) - 4
        b.box((x + 10, 0.0, z + 4), (8, 26, 26), iron=1.0)


def deck(b):
    hatch_aft, hatch_fwd, hatch_half = HATCH
    ys = [-200 + 25 * k for k in range(17)]
    stations = [x for x in STATIONS if x >= STERN_X + SHELL and inner_y(x, DECK_Z) > 8]
    stations[0] = STERN_X + SHELL

    def rows_at(z):
        return [[(x, max(-inner_y(x, z), min(inner_y(x, z), y)), z) for y in ys] for x in stations]

    def skip(i, j):
        x = (stations[i] + stations[i + 1]) / 2
        y = (ys[j] + ys[j + 1]) / 2
        return hatch_aft < x < hatch_fwd and abs(y) < hatch_half

    top = rows_at(DECK_Z)
    for j in range(len(ys) - 1):
        board = [[row[j], row[j + 1]] for row in top]
        b.grid(board, lambda i, _, j=j: (0, 0, 1), lambda i, _, j=j: skip(i, j), tone_of=lambda i, _, j=j: plank_tone(j, 7))
    b.grid(rows_at(DECK_Z - DECK_THICK), lambda i, j: (0, 0, -1), skip)
    # Hatch coaming, and the hatch's own cut sides.
    length, width = hatch_fwd - hatch_aft, 2 * hatch_half
    mid = (hatch_aft + hatch_fwd) / 2
    for y in (-hatch_half - 5, hatch_half + 5):
        b.box((mid, y, DECK_Z + 2), (length + 20, 10, 22))
    for x in (hatch_aft - 5, hatch_fwd + 5):
        b.box((x, 0.0, DECK_Z + 2), (10, width, 22))


def hold(b):
    hatch_aft, hatch_fwd, hatch_half = HATCH
    ys = [-150 + 25 * k for k in range(13)]
    stations = [x for x in STATIONS if x >= STERN_X + SHELL and inner_y(x, FLOOR_Z) > 20]
    rows = [[(x, max(-inner_y(x, FLOOR_Z), min(inner_y(x, FLOOR_Z), y)), FLOOR_Z) for y in ys] for x in stations]
    b.grid(rows, lambda i, j: (0, 0, 1))
    # Deck beams, framing the hatch; the hold keeps 2 m of headroom beneath them.
    for x in (-460, -370, -290, hatch_aft - 8, hatch_fwd + 8, 110, 200, 290, 380):
        half = inner_y(x, DECK_Z - DECK_THICK)
        if half > 10:
            b.box((x, 0.0, DECK_Z - DECK_THICK - 5), (14, 2 * half, 10))
    # Ribs following the planking, from the floor to the underside of the deck, and posts in the bulwark above it.
    for x in range(-460, 420, 60):
        x = float(x)
        for side in (1, -1):
            path = []
            for k in range(13):
                z = FLOOR_Z + (DECK_Z - DECK_THICK - 10 - FLOOR_Z) * k / 12
                path.append((x, side * (inner_y(x, z) - 4), z))
            b.sweep(path, 9.0, 8.0, side=(1, 0, 0))
    for x in range(-460, 470, 90):
        x = float(x)
        if abs(x - GUNPORT[0]) < 40:
            continue
        for side in (1, -1):
            path = [(x, side * (inner_y(x, min(z, sheer(x))) - 5), z) for z in (DECK_Z, (DECK_Z + sheer(x)) / 2, sheer(x) + 12)]
            b.sweep(path, 10.0, 10.0, side=(1, 0, 0))
    # A post under the mast step, and stairs down from the hatch.
    b.box((90, 0.0, (FLOOR_Z + DECK_Z - DECK_THICK - 10) / 2), (16, 16, DECK_Z - DECK_THICK - 10 - FLOOR_Z))
    steps = 10
    rise = (DECK_Z - FLOOR_Z) / steps
    run = (hatch_fwd - hatch_aft - 10) / steps
    for k in range(steps - 1):
        top = DECK_Z - rise * (k + 1)
        x0 = hatch_aft + 5 + run * k
        b.box((x0 + run / 2, 0.0, (FLOOR_Z + top) / 2), (run, 84, top - FLOOR_Z))


def studs(b):
    """Iron nail heads where each strake crosses a frame."""
    span = (math.pi / 2) / STRAKES
    for x in range(-460, 420, 60):
        x = float(x)
        for k in range(STRAKES):
            theta = (k + 0.5) * span
            y, z = section_point(x, theta)
            if in_gunport(x, z) or half_beam(x) < 10:
                continue
            ny, nz = section_normal(x, theta)
            for side in (1, -1):
                b.box((x, side * (y + ny * 1.5), z + nz * 1.5), (3.5, 3.5, 3.5), iron=1.0)


def gunports(b):
    cx, w, z0, z1 = GUNPORT
    for side in (1, -1):
        y_out = half_beam(cx) + 2
        y_in = inner_y(cx, (z0 + z1) / 2) - 2
        yc, depth = side * (y_out + y_in) / 2, y_out - y_in + 4
        b.box((cx, yc, z0 - 4), (w + 16, depth, 8))
        b.box((cx, yc, z1 + 4), (w + 16, depth, 8))
        b.box((cx - w / 2 - 4, yc, (z0 + z1) / 2), (8, depth, z1 - z0))
        b.box((cx + w / 2 + 4, yc, (z0 + z1) / 2), (8, depth, z1 - z0))


def ladders(b):
    for side in (1, -1):
        def out(x, z):
            t = theta_at(x, z)
            y, _ = section_point(x, t)
            return side * (y + 9)
        zs = [-40 + 20 * k for k in range(int((sheer(LADDER_X) + 10 + 40) / 20) + 1)]
        for dx in (-22, 22):
            x = LADDER_X + dx
            b.sweep([(x, out(x, z), z) for z in zs], 5.0, 6.0, side=(1, 0, 0))
        for z in range(-30, int(sheer(LADDER_X)), 30):
            y = out(LADDER_X, z) + side * 1
            b.sweep([(LADDER_X - 24, y, z), (LADDER_X + 24, y, z)], 4.0, 4.0, side=(0, 1, 0))


def capstan(b):
    x, y = CAPSTAN
    b.cylinder((x, y, DECK_Z), 26, 6)
    b.cylinder((x, y, DECK_Z + 6), 19, 52)
    b.cylinder((x, y, DECK_Z + 58), 27, 9)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        b.box((x + 19 * math.cos(a), y + 19 * math.sin(a), DECK_Z + 32), (6, 6, 40), iron=1.0)


# ---- Assets ------------------------------------------------------------------------------------------------

def make_material():
    assets = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    material = unreal.load_asset(MATERIAL) or assets.create_asset(MATERIAL.rsplit('/', 1)[1], MATERIAL.rsplit('/', 1)[0],
                                                                  unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(material)

    def node(cls, **props):
        n = mel.create_material_expression(material, cls)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def custom(code, kind, inputs):
        n = node(unreal.MaterialExpressionCustom, code=code, output_type=kind)
        pins = []
        for name in inputs:
            pin = unreal.CustomInput()
            pin.set_editor_property('input_name', name)
            pins.append(pin)
        n.set_editor_property('inputs', pins)
        return n

    timber = node(unreal.MaterialExpressionTextureSample, texture=unreal.load_asset('/Game/Elitewake/World/Materials/T_Timber_v1'))
    tint = node(unreal.MaterialExpressionVertexColor)
    # Warm the grey driftwood toward the oak in the art; tar darkens the bottom; iron reads as dark metal.
    colour = custom('float3 oak = Wood * float3(0.98, 0.7, 0.44);'
                    ' float3 tarred = Wood * float3(0.2, 0.16, 0.13);'
                    ' float3 c = lerp(oak, tarred, Flags.r) * lerp(0.72, 1.15, Flags.b);'
                    ' return lerp(c, float3(0.05, 0.05, 0.055), Flags.g);',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('Wood', 'Flags'))
    rough = custom('return lerp(lerp(0.82, 0.62, Flags.r), 0.45, Flags.g);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('Flags',))
    metal = custom('return Flags.g * 0.85;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('Flags',))
    assert mel.connect_material_expressions(timber, 'RGB', colour, 'Wood')
    for n in (colour, rough, metal):
        assert mel.connect_material_expressions(tint, '', n, 'Flags')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(metal, '', unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def make_mesh(b, material):
    geo = unreal.GeometryScript_MeshEdits
    lists = unreal.GeometryScript_List
    mesh = unreal.DynamicMesh()
    geo.add_vertices_to_mesh(mesh, lists.convert_array_to_vector_list([unreal.Vector(*p) for p in b.verts]))
    # The builder winds triangles counter-clockwise about their outward normal; Unreal's front faces wind the other way.
    triangles = lists.convert_array_to_triangle_list([unreal.IntVector(a, c, d) for a, d, c in b.tris])
    geo.add_triangles_to_mesh(mesh, triangles)
    tri_ids = range(len(b.tris))  # a fresh mesh numbers its triangles in the order they were added
    uvs = unreal.GeometryScript_UVs
    uvs.set_num_uv_sets(mesh, 1)
    for tid, (a, d, c) in zip(tri_ids, b.tris):
        n = cross(sub(b.verts[c], b.verts[a]), sub(b.verts[d], b.verts[a]))
        corner = unreal.GeometryScriptUVTriangle()
        fixed = all(b.uvs[v] is not None for v in (a, c, d))
        for name, v in (('uv0', a), ('uv1', c), ('uv2', d)):
            corner.set_editor_property(name, unreal.Vector2D(*(b.uvs[v] if fixed else uv_for(b.verts[v], n))))
        uvs.set_mesh_triangle_u_vs(mesh, 0, tid, corner)
    colours = lists.convert_array_to_color_list([unreal.LinearColor(r, g, t, 1) for r, g, t in b.colours])
    unreal.GeometryScript_VertexColors.set_mesh_per_vertex_colors(mesh, colours)
    split = unreal.GeometryScriptSplitNormalsOptions()
    split.set_editor_property('split_by_opening_angle', True)
    split.set_editor_property('opening_angle_deg', 40.0)
    unreal.GeometryScript_Normals.compute_split_normals(mesh, split, unreal.GeometryScriptCalculateNormalsOptions())
    hull = unreal.load_asset(MESH)
    if hull:
        # Rebuilt in place: the sloop definition and placed ships keep pointing at the same asset.
        options = unreal.GeometryScriptCopyMeshToAssetOptions()
        options.set_editor_property('enable_recompute_normals', False)
        options.set_editor_property('enable_recompute_tangents', True)
        _, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(
            mesh, hull, options, unreal.GeometryScriptMeshWriteLOD())
        assert outcome == unreal.GeometryScriptOutcomePins.SUCCESS, outcome
    else:
        hull, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
            mesh, MESH, unreal.GeometryScriptCreateNewStaticMeshAssetOptions(enable_collision=True,
            enable_recompute_normals=False, enable_recompute_tangents=True))
        assert hull, outcome
    hull.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    hull.set_material(0, material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(hull)
    return hull


def mount(mount_id, kind, location, yaw=0.0, sail=unreal.EWSailSize.NONE):
    m = unreal.EWShipMount()
    m.set_editor_property('mount_id', mount_id)
    m.set_editor_property('type', kind)
    m.set_editor_property('sail_size', sail)
    m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(*location), rotation=unreal.Rotator(0, 0, yaw)))
    return m


def update_definition(hull):
    definition = unreal.load_asset(DEFINITION)
    assert definition, DEFINITION
    deck_y = lambda x: inner_y(x, DECK_Z)
    t = unreal.EWShipMountType
    values = {
        'hull_mesh': hull,
        'hull_mesh_transform': unreal.Transform(),
        'hull_extent': unreal.Vector(BOW_X - 10, BEAM + 5, -KEEL_Z + 5),
        'hull_draft': -KEEL_Z,
        'deck_height': DECK_Z,
        'hold_floor_height': FLOOR_Z,
        'anchor_point': unreal.Vector(CAPSTAN[0], CAPSTAN[1], DECK_Z + 40),
        'cargo_hatch_point': unreal.Vector((HATCH[0] + HATCH[1]) / 2, 0, DECK_Z + 5),
        'boarding_points': [unreal.Vector(LADDER_X, side * (half_beam(LADDER_X) + 30), 60) for side in (-1, 1)],
        'mounts': [
            mount('Helm', t.HELM, (-430, 0, DECK_Z + 50)),
            mount('Mainsail', t.SAIL, (90, 0, DECK_Z + 50), sail=unreal.EWSailSize.MEDIUM),
            mount('Headsail', t.SAIL, (420, 0, DECK_Z + 50), sail=unreal.EWSailSize.SMALL),
            mount('PortCannon', t.CANNON, (GUNPORT[0], -(deck_y(GUNPORT[0]) - 45), DECK_Z + 40), yaw=-90),
            mount('StarboardCannon', t.CANNON, (GUNPORT[0], deck_y(GUNPORT[0]) - 45, DECK_Z + 40), yaw=90),
        ],
    }
    for k, v in values.items():
        definition.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
    return {k: str(v) for k, v in values.items() if k != 'mounts'}


def main():
    lib = unreal.EWEditorVerificationLibrary
    assert not lib.get_play_worlds(), 'Stop Play first'
    b = Builder()
    outer_shell(b)
    inner_shell(b)
    transom(b)
    rail_and_keel(b)
    deck(b)
    hold(b)
    gunports(b)
    studs(b)
    ladders(b)
    capstan(b)
    hull = make_mesh(b, make_material())
    report = {'vertices': len(b.verts), 'triangles': len(b.tris), 'definition': update_definition(hull)}
    # The sloop floats with its waterline (local Z 0) on the sea's surface.
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert level.load_level(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for ship in [a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip)]:
        p = ship.get_actor_location()
        ship.set_actor_location(unreal.Vector(p.x, 1650, -65), False, False)  # moored clear of the dock
        ship.set_actor_label('Sloop')
    assert level.save_current_level()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'SloopHullResult.json').write_text(json.dumps(report, indent=2))
    unreal.log('Sloop hull built')


main()
