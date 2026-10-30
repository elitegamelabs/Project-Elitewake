"""Geometry for the Freeport (build_freeport.py): every piece is built in its own space, x forward out of its front, y across,
z up from the ground it stands on, in cm. Pieces carry material slots (below) that the build script maps to materials, and the
timber's vertex colours (tar darkens, tone varies board by board; ship_geometry.make_timber_material). Sizes are tuning."""
import math
import random

from ship_geometry import Builder

STONE, THATCH, WOOD, DARK, CLOTH, PLASTER, ROPE, GLOW, CLOTH2, CLOTH3 = range(10)


def boards(b, rng, centre, size, axis, gap=2.0, plank=22.0, tar=0.0):
    """Planks laid side by side across a rectangle: `axis` is the direction the planks run (0 x, 1 y); each its own tone."""
    cx, cy, cz = centre
    sx, sy, sz = size
    across = sy if axis == 0 else sx
    n = max(1, int(across / plank))
    w = across / n
    for k in range(n):
        o = -across / 2 + w * (k + .5)
        tone = rng.uniform(.25, .85)
        p = (cx, cy + o, cz) if axis == 0 else (cx + o, cy, cz)
        s = (sx, w - gap, sz) if axis == 0 else (w - gap, sy, sz)
        start = len(b.verts)
        b.box(p, s, tar=tar)
        for v in range(start, len(b.verts)):
            r, g, _ = b.colours[v]
            b.colours[v] = (r, g, tone)


def post(b, x, y, z0, z1, r=11.0, sides=8, tar=0.0):
    start = len(b.verts)
    b.tube([(x, y, z0), (x, y, z1)], r, sides=sides)
    if tar:
        for v in range(start, len(b.verts)):
            _, g, t = b.colours[v]
            b.colours[v] = (tar, g, t)


def gable(b, w, d, z, pitch, overhang, slot, tar=0.0, thick=10.0):
    """A pitched roof over a w (x) by d (y) footprint, ridge along y; gives its rise. Thick enough to read from below."""
    hx, hy = w / 2 + overhang, d / 2 + overhang
    rise = (w / 2) * pitch
    drop = overhang * pitch
    b.slot = slot
    for side in (-1, 1):
        eave = (side * hx, z - drop)
        ridge = (0.0, z + rise)
        for off, hint_up in ((0.0, 1), (-thick, -1)):
            ids = [b.vertex((eave[0], -hy, eave[1] + off), tar), b.vertex((eave[0], hy, eave[1] + off), tar),
                   b.vertex((ridge[0], hy, ridge[1] + off), tar), b.vertex((ridge[0], -hy, ridge[1] + off), tar)]
            b.quad(*ids, (side * pitch * hint_up, 0, hint_up))
        # The eave's edge.
        ids = [b.vertex((eave[0], -hy, eave[1]), tar), b.vertex((eave[0], hy, eave[1]), tar),
               b.vertex((eave[0], hy, eave[1] - thick), tar), b.vertex((eave[0], -hy, eave[1] - thick), tar)]
        b.quad(*ids, (side, 0, 0))
    # The gable ends, closed in timber.
    b.slot = WOOD
    for side in (-1, 1):
        ids = [b.vertex((w / 2, side * d / 2, z), tar * .5), b.vertex((-w / 2, side * d / 2, z), tar * .5),
               b.vertex((0, side * d / 2, z + rise), tar * .5)]
        b.tri(*ids, (0, side, 0))
    # A ridge beam.
    b.box((0, 0, z + rise + 4), (16, d + 2 * overhang + 10, 14), tar=.3)
    return rise


def window(b, x, y, z, w, h, facing, shutters=True, rng=None):
    """A dark opening with a frame and a pair of open shutters, on a wall facing (nx, ny)."""
    nx, ny = facing
    along = (0, 1) if nx else (1, 0)
    b.slot = DARK
    b.box((x + nx * 3, y + ny * 3, z), (6 if nx else w, w if nx else 6, h))
    b.slot = WOOD
    for off in (-1, 1):
        b.box((x + nx * 6 + along[0] * off * (w / 2 + 5), y + ny * 6 + along[1] * off * (w / 2 + 5), z), (10 if nx else 10, 10 if nx else 10, h + 14))
    b.box((x + nx * 7, y + ny * 7, z - h / 2 - 6), (14 if nx else w + 24, w + 24 if nx else 14, 8))
    b.box((x + nx * 7, y + ny * 7, z + h / 2 + 6), (12 if nx else w + 30, w + 30 if nx else 12, 10))
    if shutters:
        for off in (-1, 1):
            # Swung open, flat to the wall beside the opening.
            cx = x + nx * 9 + along[0] * off * (w * .75 + 8)
            cy = y + ny * 9 + along[1] * off * (w * .75 + 8)
            start = len(b.verts)
            b.box((cx, cy, z), (5 if nx else w / 2, w / 2 if nx else 5, h))
            tone = (rng or random).uniform(.3, .8)
            for v in range(start, len(b.verts)):
                r, g, _ = b.colours[v]
                b.colours[v] = (.15, g, tone)


def house(w, d, storeys, seed, roof='thatch', plaster=False, porch=False, sign=False):
    """A waterfront house or shop: a stone footing, a timber frame with plank (or whitewashed) walls, shuttered windows,
    a plank door up two steps, a steep thatch or shingle roof with deep eaves. Front (door) faces +x."""
    rng = random.Random(seed)
    b = Builder()
    plinth = 55.0
    storey = 300.0
    height = storeys * storey
    b.slot = STONE
    b.box((0, 0, plinth / 2 - 50), (w + 24, d + 24, plinth + 100))
    # Walls: a solid core, then the frame and boards proud of it.
    b.slot = PLASTER if plaster else WOOD
    b.box((0, 0, plinth + height / 2), (w - 8, d - 8, height))
    b.slot = WOOD
    if not plaster:
        for fx, fy, sx, sy, axis in ((w / 2, 0, 4, d - 20, 1), (-w / 2, 0, 4, d - 20, 1), (0, d / 2, w - 20, 4, 0), (0, -d / 2, w - 20, 4, 0)):
            # Weatherboards: horizontal planks lapped up the wall.
            for k in range(int(height / 24)):
                z = plinth + 12 + k * 24
                tone = rng.uniform(.3, .85)
                start = len(b.verts)
                b.box((fx, fy, z), (sx, sy, 22))
                for v in range(start, len(b.verts)):
                    r, g, _ = b.colours[v]
                    b.colours[v] = (r, g, tone)
    # Corner posts, sill and plate beams, a beam at each floor.
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((sx * w / 2, sy * d / 2, plinth + height / 2), (20, 20, height + 10))
    for k in range(storeys + 1):
        z = plinth + k * storey
        b.box((0, d / 2 + 2, z), (w + 6, 14, 16), tar=.2)
        b.box((0, -d / 2 - 2, z), (w + 6, 14, 16), tar=.2)
        b.box((w / 2 + 2, 0, z), (14, d + 6, 16), tar=.2)
        b.box((-w / 2 - 2, 0, z), (14, d + 6, 16), tar=.2)
    # Windows on every side, a door in the front.
    for k in range(storeys):
        z = plinth + k * storey + 160
        across = max(1, int(d / 240))
        for j in range(across):
            y = -d / 2 + d * (j + .5) / across
            if k == 0 and abs(y) < 90:
                continue
            window(b, w / 2 + 2, y, z, 70, 90, (1, 0), rng=rng)
            if rng.random() < .7:
                window(b, -w / 2 - 2, y, z, 70, 90, (-1, 0), rng=rng)
        along = max(1, int(w / 260))
        for j in range(along):
            x = -w / 2 + w * (j + .5) / along
            window(b, x, d / 2 + 2, z, 60, 80, (0, 1), rng=rng)
            window(b, x, -d / 2 - 2, z, 60, 80, (0, -1), rng=rng)
    b.slot = DARK
    b.box((w / 2 + 3, 0, plinth + 110), (6, 110, 220))
    b.slot = WOOD
    boards(b, rng, (w / 2 + 7, 0, plinth + 108), (4, 100, 214), 0, plank=20)
    b.box((w / 2 + 9, 0, plinth + 226), (12, 140, 14))
    b.slot = STONE
    b.box((w / 2 + 40, 0, plinth - 15), (60, 160, 30))
    b.box((w / 2 + 80, 0, plinth - 40), (50, 170, 30))
    top = plinth + height
    if roof == 'thatch':
        gable(b, w, d, top, 1.05, 60, THATCH, thick=22)
    else:
        gable(b, w, d, top, .8, 45, WOOD, tar=.75)
    if porch:
        # A lean-to porch on posts across the front, plank floor, a bench.
        b.slot = WOOD
        depth = 200
        boards(b, rng, (w / 2 + depth / 2, 0, plinth - 6), (depth, d - 40, 8), 0)
        for y in (-d / 2 + 40, d / 2 - 40):
            post(b, w / 2 + depth - 15, y, plinth - 60, plinth + 260, 9)
        b.box((w / 2 + depth - 15, 0, plinth + 262), (18, d - 40, 16), tar=.2)
        b.slot = THATCH if roof == 'thatch' else WOOD
        lo, hi = plinth + 255, plinth + 300
        ids = [b.vertex((w / 2, -d / 2 + 20, hi), .75 if roof != 'thatch' else 0), b.vertex((w / 2, d / 2 - 20, hi), .75 if roof != 'thatch' else 0),
               b.vertex((w / 2 + depth + 30, d / 2 - 20, lo), .75 if roof != 'thatch' else 0), b.vertex((w / 2 + depth + 30, -d / 2 + 20, lo), .75 if roof != 'thatch' else 0)]
        b.quad(*ids, (.2, 0, 1))
        ids2 = [b.vertex((w / 2, -d / 2 + 20, hi - 8)), b.vertex((w / 2, d / 2 - 20, hi - 8)),
                b.vertex((w / 2 + depth + 30, d / 2 - 20, lo - 8)), b.vertex((w / 2 + depth + 30, -d / 2 + 20, lo - 8))]
        b.quad(*ids2, (-.2, 0, -1))
        b.slot = WOOD
        b.box((w / 2 + 30, d / 2 - 140, plinth + 25), (40, 160, 8))
        for y in (d / 2 - 200, d / 2 - 80):
            b.box((w / 2 + 30, y, plinth + 10), (36, 8, 30))
    if sign:
        b.slot = WOOD
        b.box((w / 2 + 70, 110, plinth + 300), (140, 8, 8), tar=.4)
        b.slot = CLOTH
        b.box((w / 2 + 110, 110, plinth + 255), (80, 6, 55))
    return b


def tavern(seed):
    """The tavern: a broad two-storey timber hall on a stone footing, walked into through its front door. Inside a plank floor,
    a bar across the back with shelves of bottles and casks behind it, a stone hearth, tables with stools, benches, a gallery
    beam with hanging lanterns; outside a deep veranda with tables and the hanging sign. Front faces +x. Interior 1300 x 1500."""
    rng = random.Random(seed)
    b = Builder()
    W, D = 1300.0, 1500.0
    plinth = 40.0
    H = 380.0          # the hall's ceiling
    H2 = 300.0         # the upper storey (outside only)
    t = 22.0           # wall thickness
    # Footing and floor.
    b.slot = STONE
    b.box((0, 0, plinth / 2 - 60), (W + 40, D + 40, plinth + 120))
    b.slot = WOOD
    boards(b, rng, (0, 0, plinth + 2), (W - 2 * t, D - 2 * t, 4), 0, plank=24)
    floor = plinth + 4
    # Walls with a door in the front and windows; each wall in pieces round its openings.
    door_w, door_h = 220.0, 260.0
    win_w, win_h, win_z = 120.0, 120.0, floor + 120

    def wall_x(x, nx):
        """A wall across the front or back (along y), with its openings."""
        openings = [(-D / 2 + 260, win_w, win_z, win_h), (D / 2 - 260, win_w, win_z, win_h)]
        if nx > 0:
            openings.append((0.0, door_w, floor, door_h))
        else:
            openings.append((0.0, win_w, win_z, win_h))
        edges = sorted(openings)
        y = -D / 2
        b.slot = WOOD
        for oy, ow, oz, oh in edges:
            b.box((x, (y + oy - ow / 2) / 2, (floor + H) / 2 - 2), (t, oy - ow / 2 - y, H - floor + 4 + plinth))
            # Below and above the opening.
            if oz > floor + 1:
                b.box((x, oy, (floor + oz) / 2), (t, ow, oz - floor))
            b.box((x, oy, (oz + oh + H + 20) / 2), (t, ow, H + 20 - (oz + oh)))
            y = oy + ow / 2
        b.box((x, (y + D / 2) / 2, (floor + H) / 2 - 2), (t, D / 2 - y, H - floor + 4 + plinth))
        for oy, ow, oz, oh in openings:
            if oz > floor + 1:
                window(b, x + nx * 8, oy, oz + oh / 2, ow, oh, (nx, 0), rng=rng)

    def wall_y(y, ny):
        openings = [(-W / 2 + 330, win_w, win_z, win_h), (W / 2 - 330, win_w, win_z, win_h)]
        x = -W / 2
        b.slot = WOOD
        for ox, ow, oz, oh in openings:
            b.box(((x + ox - ow / 2) / 2, y, (floor + H) / 2 - 2), (ox - ow / 2 - x, t, H - floor + 4 + plinth))
            b.box((ox, y, (floor + oz) / 2), (ow, t, oz - floor))
            b.box((ox, y, (oz + oh + H + 20) / 2), (ow, t, H + 20 - (oz + oh)))
            x = ox + ow / 2
        b.box(((x + W / 2) / 2, y, (floor + H) / 2 - 2), (W / 2 - x, t, H - floor + 4 + plinth))
        for ox, ow, oz, oh in openings:
            window(b, ox, y + ny * 8, oz + oh / 2, ow, oh, (0, ny), rng=rng)

    wall_x(W / 2, 1)
    wall_x(-W / 2, -1)
    wall_y(D / 2, 1)
    wall_y(-D / 2, -1)
    # Weatherboards over the outside of the walls, the frame, the door.
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((sx * W / 2, sy * D / 2, (H + H2 + plinth) / 2), (30, 30, H + H2 + 20), tar=.2)
    for z in (floor, H, H + H2):
        for sy in (-1, 1):
            b.box((0, sy * (D / 2 + 4), z), (W + 10, 16, 18), tar=.25)
        for sx in (-1, 1):
            b.box((sx * (W / 2 + 4), 0, z), (16, D + 10, 18), tar=.25)
    b.box((W / 2 + 10, 0, floor + door_h + 10), (18, door_w + 40, 20), tar=.3)
    for off in (-1, 1):
        b.box((W / 2 + 10, off * (door_w / 2 + 8), floor + door_h / 2), (18, 16, door_h))
    # The door stands open, swung in against the wall.
    b.slot = WOOD
    boards(b, rng, (W / 2 - door_w / 2 - 20, -door_w / 2 - 8, floor + door_h / 2), (door_w - 10, 6, door_h - 6), 1, plank=20)
    # Upper storey: whitewashed, a little overhanging, its windows shuttered.
    b.slot = PLASTER
    b.box((0, 0, H + H2 / 2 + 6), (W + 30, D + 30, H2))
    for y in (-D / 2 + 260, -D / 2 + 620, D / 2 - 620, D / 2 - 260):
        window(b, W / 2 + 17, y, H + 150, 90, 100, (1, 0), rng=rng)
        window(b, -W / 2 - 17, y, H + 150, 90, 100, (-1, 0), rng=rng)
    # Ceiling of the hall, beams under it.
    b.slot = WOOD
    boards(b, rng, (0, 0, H - 4), (W - 2 * t, D - 2 * t, 8), 1, plank=26)
    for x in range(-int(W / 2) + 160, int(W / 2), 260):
        b.box((x, 0, H - 20), (24, D - 2 * t, 28), tar=.35)
    # Roof.
    gable(b, W + 30, D + 30, H + H2 + 6, .9, 70, THATCH, thick=26)
    # A chimney at the hearth's side.
    b.slot = STONE
    b.box((-W / 2 + 200, -D / 2 + 20, floor + 200), (220, 90, 400))
    b.box((-W / 2 + 200, -D / 2 - 30, H + H2 + 300), (110, 110, 1000))
    b.slot = DARK
    b.box((-W / 2 + 200, -D / 2 + 66, floor + 70), (110, 6, 110))
    b.slot = GLOW
    b.box((-W / 2 + 200, -D / 2 + 60, floor + 25), (80, 20, 22))
    # The bar across the back, shelves and casks behind it.
    b.slot = WOOD
    bx = -W / 2 + 230
    boards(b, rng, (bx, 0, floor + 55), (60, 760, 110), 0, plank=20, tar=.2)
    b.box((bx + 8, 0, floor + 114), (90, 800, 10), tar=.45)
    for z in (floor + 140, floor + 200, floor + 260):
        b.box((-W / 2 + t + 25, 0, z), (40, 700, 6))
        b.slot = CLOTH2
        for k in range(14):
            y = -320 + k * 48 + rng.uniform(-6, 6)
            b.cylinder((-W / 2 + t + 25, y, z + 3), 6, 26 + rng.uniform(-4, 6), sides=6)
        b.slot = WOOD
    for k, y in enumerate((-460, -360, 360, 460)):
        barrel_into(b, (-W / 2 + t + 50, y, floor), 38, 90, lying=k % 2 == 0)
    # Tables with stools and benches.
    for tx, ty in ((150, -450), (150, 0), (150, 450), (-150, -500), (-150, 500), (420, -300), (420, 300)):
        table_into(b, rng, (tx, ty, floor), 4)
    # Lanterns hanging from the beams (the build places lights at their spots).
    for lx, ly in ((150, -300), (150, 300), (-200, 0)):
        b.slot = ROPE
        b.box((lx, ly, H - 50), (2, 2, 60))
        lantern_into(b, (lx, ly, H - 105))
    # The veranda: a plank deck on posts across the front with its own roof, two tables, the sign.
    depth = 300.0
    b.slot = WOOD
    boards(b, rng, (W / 2 + depth / 2, 0, plinth - 4), (depth, D, 8), 0, plank=22)
    for y in (-D / 2 + 30, -D / 4, D / 4, D / 2 - 30):
        post(b, W / 2 + depth - 15, y, plinth - 60, H + 40, 11)
    b.box((W / 2 + depth - 15, 0, H + 40), (22, D + 20, 22), tar=.2)
    b.slot = THATCH
    ids = [b.vertex((W / 2, -D / 2 - 30, H + 90)), b.vertex((W / 2, D / 2 + 30, H + 90)),
           b.vertex((W / 2 + depth + 50, D / 2 + 30, H + 20)), b.vertex((W / 2 + depth + 50, -D / 2 - 30, H + 20))]
    b.quad(*ids, (.25, 0, 1))
    ids = [b.vertex((W / 2, -D / 2 - 30, H + 72)), b.vertex((W / 2, D / 2 + 30, H + 72)),
           b.vertex((W / 2 + depth + 50, D / 2 + 30, H + 2)), b.vertex((W / 2 + depth + 50, -D / 2 - 30, H + 2))]
    b.quad(*ids, (-.25, 0, -1))
    for ty in (-520, 520):
        table_into(b, rng, (W / 2 + 150, ty, plinth), 2)
    # The sign: a lantern-shaped board on a bracket at the veranda's corner.
    b.slot = WOOD
    b.box((W / 2 + depth + 60, -D / 2 + 30, H - 20), (160, 10, 10), tar=.4)
    b.box((W / 2 + depth + 110, -D / 2 + 30, H - 85), (110, 8, 110))
    b.slot = GLOW
    b.box((W / 2 + depth + 110, -D / 2 + 25, H - 85), (40, 4, 60))
    b.slot = WOOD
    b.box((W / 2 + depth + 110, -D / 2 + 35, H - 85), (40, 4, 60))
    return b


def barrel_into(b, base, r, h, lying=False, tar=0.0):
    """A cask: bulged staves and two dark iron hoops. Standing on base, or lying along x."""
    x, y, z = base
    prof = [(0, .86), (.18, .97), (.5, 1.0), (.82, .97), (1, .86)]
    if lying:
        path = [(x - h / 2 + f * h, y, z + r) for f, _ in prof]
    else:
        path = [(x, y, z + f * h) for f, _ in prof]
    b.slot = WOOD
    b.tube(path, lambda k: r * prof[k][1], sides=12)
    b.slot = DARK
    for f in (.14, .86):
        rr = r * (.94 if f < .5 else .94) + 1.5
        p0 = (x - h / 2 + f * h, y, z + r) if lying else (x, y, z + f * h)
        p1 = (p0[0] + 5, p0[1], p0[2]) if lying else (p0[0], p0[1], p0[2] + 5)
        b.tube([p0, p1], rr, sides=12, capped=False)


def table_into(b, rng, base, seats):
    x, y, z = base
    b.slot = WOOD
    boards(b, rng, (x, y, z + 76), (100, 160, 6), 0, plank=20)
    for sx in (-40, 40):
        for sy in (-65, 65):
            b.box((x + sx, y + sy, z + 37), (8, 8, 74))
    for k in range(seats):
        a = k * 2 * math.pi / seats + .4
        sx, sy = x + math.cos(a) * 95, y + math.sin(a) * 110
        b.cylinder((sx, sy, z), 4, 44, sides=5)
        b.cylinder((sx, sy, z + 42), 17, 5, sides=10)


def lantern_into(b, base):
    """A ship's lantern: an iron frame round a glowing glass."""
    x, y, z = base
    b.slot = GLOW
    b.box((x, y, z), (16, 16, 24))
    b.slot = DARK
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((x + sx * 9, y + sy * 9, z), (3, 3, 28))
    b.box((x, y, z + 15), (22, 22, 4))
    b.box((x, y, z - 14), (20, 20, 4))
    b.box((x, y, z + 21), (8, 8, 8))


def lantern_post(height=300):
    b = Builder()
    b.slot = WOOD
    post(b, 0, 0, -40, height, 9, tar=.4)
    b.box((25, 0, height - 10), (60, 8, 8), tar=.4)
    b.slot = ROPE
    b.box((50, 0, height - 30), (2, 2, 30))
    lantern_into(b, (50, 0, height - 60))
    return b


def barrel(seed=0):
    b = Builder()
    barrel_into(b, (0, 0, 0), 32, 82)
    return b


def crate(w=70, d=60, h=55, seed=0):
    rng = random.Random(seed)
    b = Builder()
    b.slot = WOOD
    b.box((0, 0, h / 2), (w - 6, d - 6, h - 6))
    for z in (4, h - 4):
        for sy in (-1, 1):
            b.box((0, sy * d / 2, z), (w, 6, 8), tar=.15)
        for sx in (-1, 1):
            b.box((sx * w / 2, 0, z), (6, d, 8), tar=.15)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((sx * w / 2, sy * d / 2, h / 2), (8, 8, h), tar=.15)
    # Diagonal braces on two faces.
    for sy in (-1, 1):
        b.sweep([(-w / 2 + 6, sy * (d / 2 + 2), 6), (w / 2 - 6, sy * (d / 2 + 2), h - 6)], 7, 3, side=(1, 0, 0))
    return b


def rope_coil(r=28, turns=4):
    b = Builder()
    b.slot = ROPE
    path = []
    for k in range(turns * 16 + 1):
        a = k * 2 * math.pi / 16
        rr = r - (k / 16) * 3.5
        path.append((rr * math.cos(a), rr * math.sin(a), 3 + (k / (turns * 16)) * 10))
    b.tube(path, 3.2, sides=6)
    return b


def net_rack(seed=0):
    """Fishing nets hung to dry over a rail on two posts, sagging, with cork floats along the head rope."""
    rng = random.Random(seed)
    b = Builder()
    b.slot = WOOD
    L = 360
    for y in (-L / 2, L / 2):
        post(b, 0, y, -30, 210, 7)
    b.box((0, 0, 205), (8, L + 30, 8))
    b.slot = ROPE
    rows = []
    for i in range(9):
        row = []
        for j in range(13):
            y = -L / 2 + 10 + (L - 20) * j / 12
            sag = math.sin(math.pi * j / 12) * (18 + i * 2)
            drop = i * 20
            row.append((4 + (i % 2) * 3, y, 200 - drop - sag * (i / 8)))
        rows.append(row)
    for i in range(len(rows)):
        b.sweep(rows[i], 1.5, 1.5, side=(1, 0, 0), capped=False)
    for j in range(13):
        b.sweep([rows[i][j] for i in range(len(rows))], 1.5, 1.5, side=(0, 1, 0), capped=False)
    b.slot = CLOTH3
    for j in range(0, 13, 2):
        x, y, z = rows[0][j]
        b.box((x + 5, y, z - 4), (8, 12, 6))
    return b


def bollard():
    b = Builder()
    b.slot = DARK
    b.tube([(0, 0, -10), (0, 0, 40), (0, 0, 52)], lambda k: (16, 13, 18)[k], sides=12)
    return b


def mooring_post(h=140):
    b = Builder()
    b.slot = WOOD
    post(b, 0, 0, -900, h, 14, sides=10, tar=.5)
    b.slot = ROPE
    b.tube([(0, 0, h - 40), (0, 0, h - 25)], 15.5, sides=10)
    return b


def pier(length, width, depth, seed, ladders=()):
    """A timber pier (x out to sea): planks across on stringers, bents of piles every 3 m driven down to the bottom (depth cm
    below the deck, given at both ends as (near, far)), cross-braced; a rubbing strake and bollards along both edges."""
    rng = random.Random(seed)
    b = Builder()
    b.slot = WOOD
    n = int(length / 24)
    for k in range(n):
        x = k * 24 + 12
        tone = rng.uniform(.25, .9)
        start = len(b.verts)
        jitter = rng.uniform(-4, 4)
        b.box((x, jitter, -4), (22, width + rng.uniform(-6, 6), 8))
        for v in range(start, len(b.verts)):
            r, g, _ = b.colours[v]
            b.colours[v] = (r, g, tone)
    for y in (-width / 2 + 20, 0, width / 2 - 20):
        b.box((length / 2, y, -18), (length, 14, 22), tar=.3)
    near, far = depth
    for k in range(int(length / 300) + 1):
        x = k * 300 + 10
        d = near + (far - near) * x / length
        for y in (-width / 2 + 10, width / 2 - 10):
            post(b, x, y, -d - 60, 10, 13, sides=8, tar=.55)
        b.box((x, 0, -45), (16, width, 16), tar=.4)
        b.sweep([(x, -width / 2 + 10, -50), (x, width / 2 - 10, -min(d, 260))], 8, 8, side=(1, 0, 0))
    for y in (-width / 2 - 4, width / 2 + 4):
        b.box((length / 2, y, -10), (length, 10, 18), tar=.4)
    for k in range(int(length / 600)):
        x = k * 600 + 300
        for y in (-width / 2 + 25, width / 2 - 25):
            b.slot = DARK
            b.tube([(x, y, 0), (x, y, 36), (x, y, 46)], lambda i: (13, 11, 15)[i], sides=10)
    b.slot = WOOD
    for lx, side in ladders:
        y = side * (width / 2 + 8)
        for off in (-25, 25):
            b.box((lx + off, y, -110), (6, 6, 230), tar=.4)
        for k in range(8):
            b.box((lx, y, -20 - k * 28), (50, 6, 5), tar=.4)
    return b


def ground_disc(radius, depth):
    """The town's ground over the levelled site: a flat top (the packed sand of the streets) and a stone seawall round its edge
    down to the sea floor, where the site meets the water."""
    b = Builder()
    b.slot = PLASTER
    centre = b.vertex((0, 0, 0))
    ring = [b.vertex((radius * math.cos(2 * math.pi * k / 64), radius * math.sin(2 * math.pi * k / 64), 0)) for k in range(64)]
    for k in range(64):
        b.tri(centre, ring[k], ring[(k + 1) % 64], (0, 0, 1))
    b.slot = STONE
    b.tube([(0, 0, -depth), (0, 0, -1)], radius + 2, sides=64, capped=False)
    # A coping course along the top of the wall.
    b.tube([(0, 0, -14), (0, 0, 2)], radius + 14, sides=64, capped=False)
    return b


def boardwalk(length, width, seed):
    """A plank walk laid on the street (x along it), its boards across, two runners under."""
    rng = random.Random(seed)
    b = Builder()
    b.slot = WOOD
    for k in range(int(length / 26)):
        x = -length / 2 + k * 26 + 13
        tone = rng.uniform(.25, .9)
        start = len(b.verts)
        b.box((x + rng.uniform(-1.5, 1.5), rng.uniform(-3, 3), 3), (24, width + rng.uniform(-5, 5), 5))
        for v in range(start, len(b.verts)):
            r, g, _ = b.colours[v]
            b.colours[v] = (r, g, tone)
    return b


def stall(seed, width=320, depth=240, goods=('crates',)):
    """A market stall: four posts, a plank counter across the front, a cloth awning sloping to the customer, shelves at the back
    and goods on show (front +x; the stallholder stands inside, the customer outside)."""
    rng = random.Random(seed)
    b = Builder()
    b.slot = WOOD
    for sx, h in ((-1, 250), (1, 220)):
        for sy in (-1, 1):
            post(b, sx * depth / 2, sy * width / 2, -20, h, 7)
    boards(b, rng, (depth / 2 - 20, 0, 92), (50, width - 20, 6), 0, plank=20)
    boards(b, rng, (depth / 2 - 20, 0, 46), (6, width - 30, 88), 0, plank=20, tar=.1)
    b.box((-depth / 2 + 25, 0, 110), (40, width - 20, 5))
    b.box((-depth / 2 + 25, 0, 160), (40, width - 20, 5))
    b.slot = CLOTH
    for off, hint in ((0, 1), (-2, -1)):
        ids = [b.vertex((-depth / 2 - 15, -width / 2 - 15, 252 + off)), b.vertex((-depth / 2 - 15, width / 2 + 15, 252 + off)),
               b.vertex((depth / 2 + 60, width / 2 + 15, 205 + off)), b.vertex((depth / 2 + 60, -width / 2 - 15, 205 + off))]
        b.quad(*ids, (.2 * hint, 0, hint))
    # A scalloped valance along the awning's front edge.
    for k in range(10):
        y = -width / 2 - 15 + (width + 30) * (k + .5) / 10
        b.box((depth / 2 + 60, y, 198), (2, (width + 30) / 10 - 8, 12))
    for kind in goods:
        for k in range(4):
            y = -width / 2 + 45 + (width - 90) * k / 3
            x = depth / 2 - 20
            if kind == 'fruit':
                b.slot = WOOD
                b.cylinder((x, y, 95), 22, 12, sides=10)
                b.slot = CLOTH2 if k % 2 else CLOTH3
                for j in range(6):
                    a = j * 1.05
                    b.tube([(x + math.cos(a) * 10, y + math.sin(a) * 10, 108), (x + math.cos(a) * 10, y + math.sin(a) * 10, 116)],
                           lambda i: (5, 6)[i], sides=6)
            elif kind == 'fish':
                b.slot = WOOD
                b.box((x, y, 100), (44, 60, 14))
                b.slot = DARK
                for j in range(3):
                    b.tube([(x - 15, y - 20 + j * 20, 110), (x + 15, y - 20 + j * 20, 110)], lambda i: (5, 3)[i], sides=6)
            elif kind == 'cloth':
                b.slot = (CLOTH, CLOTH2, CLOTH3, CLOTH)[k]
                b.tube([(x, y - 20, 104), (x, y + 20, 104)], 9, sides=8)
                b.slot = (CLOTH2, CLOTH3, CLOTH, CLOTH2)[k]
                b.tube([(-depth / 2 + 25, y - 18, 120), (-depth / 2 + 25, y + 18, 120)], 8, sides=8)
                # Hats on pegs.
                b.slot = DARK
                b.tube([(-depth / 2 + 25, y, 172), (-depth / 2 + 25, y, 176), (-depth / 2 + 25, y, 190)], lambda i: (20, 11, 9)[i], sides=10)
            elif kind == 'resources':
                b.slot = WOOD
                for j in range(3):
                    b.tube([(x - 20, y - 15 + j * 15, 104), (x + 20, y - 15 + j * 15, 104)], 6, sides=6)
                b.slot = STONE
                b.box((-depth / 2 + 25, y, 122), (30, 30, 20))
                b.slot = ROPE
                b.tube([(-depth / 2 + 25, y, 168), (-depth / 2 + 25, y, 180)], 13, sides=8)
            else:
                b.slot = WOOD
                b.box((x, y, 112), (34, 36, 34))
                b.slot = CLOTH2
                b.cylinder((-depth / 2 + 25, y, 112), 10, 22, sides=8)
    return b


def notice_board():
    b = Builder()
    b.slot = WOOD
    for y in (-90, 90):
        post(b, 0, y, -30, 230, 8, tar=.3)
    b.box((0, 0, 160), (8, 200, 120))
    b.box((0, 0, 232), (60, 230, 8), tar=.6)
    b.slot = PLASTER
    for k, (y, z, w, h) in enumerate(((-60, 175, 45, 55), (-5, 160, 40, 60), (50, 180, 50, 45), (20, 125, 60, 30), (-55, 125, 35, 30))):
        b.box((5, y, z), (2, w, h))
    return b


def well():
    b = Builder()
    b.slot = STONE
    b.tube([(0, 0, -100), (0, 0, 75)], 95, sides=16, capped=False)
    b.tube([(0, 0, -100), (0, 0, 75)], 75, sides=16, capped=False)
    b.tube([(0, 0, 68), (0, 0, 80)], 100, sides=16)
    b.slot = DARK
    b.cylinder((0, 0, -20), 74, 2, sides=16)
    b.slot = WOOD
    for y in (-85, 85):
        post(b, 0, y, 70, 240, 7)
    b.box((0, 0, 230), (10, 190, 10))
    gable(b, 120, 190, 245, .7, 25, WOOD, tar=.7, thick=6)
    b.slot = ROPE
    b.box((0, 0, 180), (2, 2, 100))
    barrel_into(b, (0, 0, 110), 14, 26)
    return b


def bench(length=180):
    b = Builder()
    b.slot = WOOD
    b.box((0, 0, 44), (36, length, 6))
    for y in (-length / 2 + 20, length / 2 - 20):
        b.box((0, y, 21), (30, 8, 42))
    return b


def rowboat(length=420, beam=140, depth=55, seed=0, mast=False):
    """A clinker rowboat: two skins (outside and in) lofted through stations, a gunwale, three thwarts, oars; with mast, a
    small fishing boat's stepped mast and a furled sail. x forward."""
    b = Builder()
    b.slot = WOOD
    stations = 11
    pts = 9

    def section(f, inset):
        # Fuller amidships, fine at the bow (f=1) and fuller transom aft (f=0).
        width = beam / 2 * (math.sin(math.pi * min(1.0, f * 1.15)) ** .7 if f > .5 else .55 + .45 * math.sin(math.pi * (f * .9 + .05)))
        width = max(4.0, width - inset)
        sheer = depth + 18 * (2 * f - 1) ** 2
        floor = (-6 if f > .15 else 0) + inset
        row = []
        for j in range(pts):
            a = math.pi * j / (pts - 1)
            y = -math.cos(a) * width
            z = sheer - (sheer - floor) * math.sin(a) ** .6
            row.append(((f - .5) * length, y, z))
        return row
    outer = [section(i / (stations - 1), 0) for i in range(stations)]
    inner = [section(i / (stations - 1), 4) for i in range(stations)]
    b.grid(outer, lambda i, j: (0, outer[i][j][1], -1), tone_of=lambda i, j: .35 + .5 * ((j // 2) % 2))
    b.grid(inner, lambda i, j: (0, -inner[i][j][1], 1), tone_of=lambda i, j: .5)
    # Gunwales along the top, a transom aft.
    for side in (0, pts - 1):
        b.sweep([outer[i][side] for i in range(stations)], 6, 6, side=(0, 0, 1), tar=.3)
    b.box((-length / 2 + 2, 0, depth / 2), (6, beam * .55, depth))
    for k, fx in enumerate((-.25, .05, .3)):
        b.box((fx * length, 0, depth - 12), (22, beam * .8, 5))
    b.sweep([(-60, -30, depth + 4), (150, 20, depth + 6)], 5, 3, side=(0, 0, 1))
    b.sweep([(-60, 30, depth + 4), (150, -20, depth + 6)], 5, 3, side=(0, 0, 1))
    if mast:
        b.tube([(.18 * length, 0, 0), (.18 * length, 0, length * .9)], 6, sides=8)
        b.tube([(.18 * length - 10, 0, length * .3), (-.4 * length, 0, length * .12)], 4, sides=6)
        b.slot = CLOTH3
        b.tube([(.18 * length - 10, 0, length * .32), (-.38 * length, 0, length * .15)], 11, sides=8)
    return b


def ship_frame(length=1600, beam=420, depth=330):
    """A hull in frame on the building cradle: keel on blocks, stem and sternpost, ribs at every station, a few strakes of
    planking started low on one side, ribbands holding the ribs, and scaffold poles with planks round her."""
    b = Builder()
    b.slot = WOOD
    b.box((0, 0, 70), (length, 30, 40), tar=.3)
    for k in range(7):
        b.box((-length / 2 + 120 + k * (length - 240) / 6, 0, 25), (60, 120, 50), tar=.2)
    b.sweep([(length / 2 - 20, 0, 70), (length / 2 + 80, 0, 200), (length / 2 + 140, 0, depth + 140)], 24, 24, side=(0, 1, 0))
    b.sweep([(-length / 2, 0, 70), (-length / 2 - 30, 0, depth + 110)], 24, 24, side=(0, 1, 0))
    frames = 15
    for i in range(frames):
        f = i / (frames - 1)
        half = beam / 2 * (math.sin(math.pi * (f * .92 + .04)) ** .55)
        x = -length / 2 + 60 + (length - 140) * f
        for side in (-1, 1):
            path = []
            for j in range(8):
                a = math.pi / 2 * j / 7
                y = side * half * math.sin(a) ** .7
                z = 90 + (depth + 20 * (2 * f - 1) ** 2) * (1 - math.cos(a))
                path.append((x, y, z))
            b.sweep(path, 14, 18, side=(1, 0, 0))
    for side in (-1, 1):
        for level in (.45, .8):
            path = []
            for i in range(frames):
                f = i / (frames - 1)
                half = beam / 2 * (math.sin(math.pi * (f * .92 + .04)) ** .55)
                a = math.acos(1 - level)
                path.append((-length / 2 + 60 + (length - 140) * f, side * (half * math.sin(a) ** .7 + 9), 90 + (depth + 20 * (2 * f - 1) ** 2) * level))
            b.sweep(path, 6, 12, side=(0, 0, 1), tar=.2)
    # Planking started on the near side: three strakes low down.
    for s in range(3):
        level = .12 + s * .09
        path = []
        for i in range(2, frames - 3):
            f = i / (frames - 1)
            half = beam / 2 * (math.sin(math.pi * (f * .92 + .04)) ** .55)
            a = math.acos(1 - level)
            path.append((-length / 2 + 60 + (length - 140) * f, -(half * math.sin(a) ** .7 + 10), 90 + (depth + 20 * (2 * f - 1) ** 2) * level))
        b.sweep(path, 5, 30, side=(0, 0, 1))
    # Scaffold: poles either side, two plank walks.
    for side in (-1, 1):
        for k in range(5):
            x = -length / 2 + 100 + k * (length - 200) / 4
            post(b, x, side * (beam / 2 + 90), 0, depth + 200, 6, tar=.2)
        for z in (180, 330):
            boards(b, random.Random(int(z) + side), (0, side * (beam / 2 + 90), z), (length - 160, 60, 5), 1, plank=24)
    return b


def ship_shed(length, width, height):
    """An open shed over the slipway's head: posts, tie-beams, a long shingled roof; open on every side."""
    b = Builder()
    b.slot = WOOD
    bays = 5
    for k in range(bays + 1):
        x = -length / 2 + k * length / bays
        for y in (-width / 2, width / 2):
            post(b, x, y, -60, height, 16, sides=8, tar=.3)
        b.box((x, 0, height - 10), (24, width + 30, 28), tar=.3)
        b.sweep([(x, -width / 2, height - 160), (x, -width / 4, height - 18)], 12, 12, side=(1, 0, 0))
        b.sweep([(x, width / 2, height - 160), (x, width / 4, height - 18)], 12, 12, side=(1, 0, 0))
    for y in (-width / 2, width / 2):
        b.box((0, y, height + 5), (length + 30, 24, 24), tar=.3)
    # The roof runs along the shed (ridge along x).
    rise = width / 2 * .55
    b.slot = WOOD
    for side in (-1, 1):
        for off, hint in ((0, 1), (-10, -1)):
            ids = [b.vertex((-length / 2 - 60, side * (width / 2 + 70), height - 35 + off), .7), b.vertex((length / 2 + 60, side * (width / 2 + 70), height - 35 + off), .7),
                   b.vertex((length / 2 + 60, 0, height + rise + off), .7), b.vertex((-length / 2 - 60, 0, height + rise + off), .7)]
            b.quad(*ids, (0, side * .55 * hint, hint))
    return b


def slipway(length, drop, width=520):
    """The slipway: ground ways (two timber rails) on sleepers, running down from the yard into the water (x down the slip)."""
    b = Builder()
    b.slot = WOOD
    for k in range(int(length / 120) + 1):
        x = k * 120
        z = -drop * x / length
        b.box((x, 0, z - 10), (30, width, 20), tar=.5)
        post(b, x, -width / 2 + 30, z - 400, z - 10, 12, tar=.6)
        post(b, x, width / 2 - 30, z - 400, z - 10, 12, tar=.6)
    for y in (-width / 4, width / 4):
        b.sweep([(0, y, 8), (length, y, 8 - drop)], 34, 22, side=(0, 1, 0), tar=.45)
    return b


def lighthouse(height=1500):
    """A timber watch tower on a stone base: four splayed legs braced in tiers, a gallery, a lantern room, a pointed cap."""
    b = Builder()
    b.slot = STONE
    b.box((0, 0, 60), (520, 520, 240))
    b.slot = WOOD
    top = height
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.sweep([(sx * 230, sy * 230, 180), (sx * 120, sy * 120, top)], 26, 26, side=(1, 0, 0), tar=.4)
    for z in (500, 850, 1200):
        f = (z - 180) / (top - 180)
        h = 230 - 110 * f
        for sx, sy, lx, ly in ((0, -1, 2 * h, 14), (0, 1, 2 * h, 14), (-1, 0, 14, 2 * h), (1, 0, 14, 2 * h)):
            b.box((sx * h, sy * h, z), (lx + 20, ly + 20, 16), tar=.4)
    b.box((0, 0, top), (380, 380, 20))
    for k in range(16):
        a = 2 * math.pi * k / 16
        post(b, 175 * math.cos(a), 175 * math.sin(a), top, top + 100, 4)
    b.tube([(0, 0, top + 95), (0, 0, top + 105)], 182, sides=16, capped=False)
    b.slot = GLOW
    b.tube([(0, 0, top + 20), (0, 0, top + 200)], 95, sides=8)
    b.slot = DARK
    for k in range(8):
        a = 2 * math.pi * k / 8
        b.box((100 * math.cos(a), 100 * math.sin(a), top + 110), (8, 8, 190))
    b.slot = WOOD
    b.tube([(0, 0, top + 200), (0, 0, top + 215), (0, 0, top + 380)], lambda k: (140, 140, 6)[k], sides=8)
    b.tube([(0, 0, top + 380), (0, 0, top + 520)], 4, sides=6)
    # A ladder up one leg's side.
    for k in range(int((top - 200) / 35)):
        z = 200 + k * 35
        b.box((0, -240 + (z - 180) / (top - 180) * 110, z), (60, 6, 5))
    return b


def beacon(height=900):
    """A channel marker: a tarred pile standing out of the water with a lantern basket on top."""
    b = Builder()
    b.slot = WOOD
    post(b, 0, 0, -2200, height, 22, sides=10, tar=.7)
    for k in range(3):
        b.slot = CLOTH if k % 2 == 0 else PLASTER
        b.tube([(0, 0, height - 300 + k * 60), (0, 0, height - 240 + k * 60)], 24, sides=10)
    b.slot = DARK
    b.tube([(0, 0, height), (0, 0, height + 60)], 40, sides=8, capped=False)
    b.slot = GLOW
    b.tube([(0, 0, height + 5), (0, 0, height + 40)], 26, sides=8)
    return b


def flagpole(height=900):
    b = Builder()
    b.slot = WOOD
    b.tube([(0, 0, -50), (0, 0, height)], lambda k: (12, 6)[k], sides=10)
    b.slot = CLOTH
    ids = [b.vertex((0, 0, height - 20)), b.vertex((0, 0, height - 130)), b.vertex((0, 220, height - 90)), b.vertex((0, 240, height - 50))]
    b.quad(*ids, (1, 0, 0))
    ids = [b.vertex((-1, 0, height - 20)), b.vertex((-1, 0, height - 130)), b.vertex((-1, 220, height - 90)), b.vertex((-1, 240, height - 50))]
    b.quad(*ids, (-1, 0, 0))
    return b


def cargo_pile(seed):
    """Crates, casks and a coil of rope as they come off a ship."""
    rng = random.Random(seed)
    b = Builder()
    for k in range(rng.randint(3, 5)):
        x, y = rng.uniform(-90, 90), rng.uniform(-70, 70)
        w, d, h = rng.uniform(55, 80), rng.uniform(50, 70), rng.uniform(45, 65)
        b.slot = WOOD
        b.box((x, y, h / 2), (w, d, h))
        b.box((x, y, h - 3), (w + 4, 8, 6), tar=.2)
        if rng.random() < .5:
            b.box((x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), h + h * .45), (w * .8, d * .8, h * .9))
    for k in range(rng.randint(2, 3)):
        barrel_into(b, (rng.uniform(-120, 120), rng.choice((-110, 110)) + rng.uniform(-15, 15), 0), 30, 78, lying=rng.random() < .3)
    b.slot = ROPE
    path = []
    cx, cy = rng.uniform(-60, 60), rng.choice((-130, 130))
    for k in range(3 * 16 + 1):
        a = k * 2 * math.pi / 16
        rr = 26 - (k / 16) * 3
        path.append((cx + rr * math.cos(a), cy + rr * math.sin(a), 3 + k * .25))
    b.tube(path, 3, sides=6)
    return b


def lobster_pots(seed):
    rng = random.Random(seed)
    b = Builder()
    for k in range(5):
        x, y, z = rng.uniform(-60, 60), rng.uniform(-60, 60), 0
        if k > 2:
            z = 45
        b.slot = WOOD
        for j in range(5):
            a = math.pi * j / 4
            b.sweep([(x - 30, y + 22 * math.cos(a), z + 22 * math.sin(a) + 2), (x + 30, y + 22 * math.cos(a), z + 22 * math.sin(a) + 2)], 3, 3, side=(0, 0, 1))
        b.slot = ROPE
        for fx in (-28, 0, 28):
            b.tube([(x + fx, y - 22, z + 2), (x + fx, y, z + 24), (x + fx, y + 22, z + 2)], 1.5, sides=5)
        b.slot = DARK
        b.box((x, y, z + 1), (60, 44, 2))
    return b
