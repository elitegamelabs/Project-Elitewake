"""Bring the owner's land animals onto the islands (owner, October 15, from the owner's photos). Safe to run again.
Run in the editor after build_coastal_flora.py and build_fish.py (for Raw Meat), outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Six animals, each a 3D model built here from lofted bodies and limbs in the colours of the owner's photos:
  - American alligator: long, low and armoured, dark olive-black with ridged scutes, a pale belly, sprawled legs and a
    heavy tail. Aggressive: it goes for a survivor who comes near and bites. It wades into the shallows.
  - Flamingo: salmon-pink, red at the wing, black flight feathers, a long S-necked head with a bent black-tipped bill
    on stilt legs. Wades the shallows.
  - Brown pelican: grey-brown body, cream neck and yellow crown, the long bill and pouch, short dark legs and
    webbed feet.
  - Cottonmouth (water moccasin): a thick dark-banded snake with a cream lip stripe. Aggressive: a bite.
  - Tortoise: a high domed shell of tan scutes with dark seams, scaly grey column legs and a wrinkled neck.
  - Squirrel monkey: olive-grey back, orange forearms and legs, the white face mask and black muzzle, a long
    black-tipped tail.
Each walks with its own gait, made in its material from the stride the game passes it (custom primitive data):
four legs in a diagonal walk, two legs stepping in turn, the snake slithering in waves, tails swaying, birds'
heads bobbing. The rest run off when struck. Killed, an animal drops on its side and Interact harvests it for Raw
Meat. They live on both islands; the aggressive ones start well away from the beach spawn and the dock.

DECIDED (delegated, *tuning*, the owner's fish rule carried over until the owner sets land yields): 6 to 10 Raw
Meat for the alligator and tortoise, 2 to 5 for the smaller animals. Speeds, health, bites, counts, sizes and
colours are tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, cross, material_builder, norm, sub, write_static_mesh  # noqa: E402
from build_coastal_flora import FLORA_FOLDER, Ground, SEA  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/Wildlife/Animals'
LEVEL_FOLDER = 'Coast/Wildlife/Animals'
RAW_MEAT = '/Game/Elitewake/Items/Food/DA_RawMeat'
SPAWN, DOCK = (150.0, 0.0), (4000.0, 900.0)
# The islands: x range, y range.
ISLANDS = {'island': ((-5900.0, 4300.0), (-4200.0, 4000.0)), 'second': ((-17800.0, -12200.0), (-15200.0, -10800.0))}

# Animation parts, carried in each vertex's first UV channel as (part, weight).
BODY, FL, FR, BL, BR, TAIL, HEAD, SNAKE, LEFT, RIGHT = range(10)


# ---- Geometry ----------------------------------------------------------------------------------------------

def tube(b, path, radius, colour, part, weight, sides=16, cap=True, shape=None):
    """A lofted tube along `path`. radius(k) gives a radius or (side, up) half-sizes; colour(q, n, k) an RGB; part
    (number or function of q, k) and weight(q, k) the animation channel; shape(q, n, k) an optional extra push out."""
    rings = []
    count = len(path)
    a = None
    for k, p in enumerate(path):
        t = norm(sub(path[min(k + 1, count - 1)], path[max(k - 1, 0)]))
        if a is None:
            ref = (0, 0, 1) if abs(t[2]) < .9 else (1, 0, 0)
            a = norm(cross(t, ref))
        else:
            along = sum(a[i] * t[i] for i in range(3))
            a = norm(tuple(a[i] - t[i] * along for i in range(3)))
        up = cross(t, a)
        r = radius(k)
        rs, ru = r if isinstance(r, tuple) else (r, r)
        ring = []
        for s in range(sides):
            ang = 2 * math.pi * s / sides
            n = tuple(a[i] * math.cos(ang) + up[i] * math.sin(ang) for i in range(3))
            q = tuple(p[i] + a[i] * math.cos(ang) * rs + up[i] * math.sin(ang) * ru for i in range(3))
            if shape:
                push = shape(q, n, k)
                q = tuple(q[i] + n[i] * push for i in range(3))
            pa = part(q, k) if callable(part) else part
            ring.append(b.vertex(q, *colour(q, n, k), uv=(pa, weight(q, k))))
        rings.append((ring, a, up, t))
    for k in range(count - 1):
        r0, a, up, _ = rings[k]
        r1 = rings[k + 1][0]
        for s in range(sides):
            ang = 2 * math.pi * (s + .5) / sides
            hint = tuple(a[i] * math.cos(ang) + up[i] * math.sin(ang) for i in range(3))
            b.quad(r0[s], r1[s], r1[(s + 1) % sides], r0[(s + 1) % sides], hint)
    if cap:
        for (ring, _, _, t), end, sign in ((rings[0], path[0], -1), (rings[-1], path[-1], 1)):
            first = b.verts[ring[0]]
            c = b.vertex(end, *b.colours[ring[0]], uv=b.uvs[ring[0]])
            for s in range(sides):
                b.tri(c, ring[s], ring[(s + 1) % sides], tuple(t[i] * sign for i in range(3)))
            del first


def stations(points, steps=3):
    """Smooth a list of (x, y, z, side, up) stations into a denser path with radii (Catmull-Rom)."""
    out = []
    for i in range(len(points) - 1):
        p0, p1, p2, p3 = points[max(i - 1, 0)], points[i], points[i + 1], points[min(i + 2, len(points) - 1)]
        for s in range(steps):
            t = s / steps
            out.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(5)))
    out.append(points[-1])
    return [o[:3] for o in out], [(max(o[3], .3), max(o[4], .3)) for o in out]


def body(b, points, colour, part=BODY, weight=None, sides=20, shape=None, steps=3):
    path, radii = stations(points, steps)
    tube(b, path, lambda k: radii[k], lambda q, n, k: colour(q, n), part, weight or (lambda q, k: 0.0), sides, shape=shape)


def ball(b, centre, radii, colour, part=BODY, weight=0.0, sides=14):
    """An ellipsoid: (along x, side, up) half-sizes."""
    cx, cy, cz = centre
    rx, ry, rz = radii
    pts = [(cx + rx * math.cos(math.pi * (1 - k / 8)), cy, cz, ry * math.sin(math.pi * k / 8), rz * math.sin(math.pi * k / 8)) for k in range(9)]
    body(b, pts, colour, part, lambda q, k: weight, sides, steps=1)


def limb(b, joints, r0, r1, colour, part, top_z, sides=10):
    """A leg from the hip down through its joints; its weight grows from 0 at the hip to 1 at the foot. Radii may be
    (side, up) pairs, for a flat foot."""
    path, k = [], len(joints)
    for i in range(k - 1):
        for s in range(3):
            t = s / 3
            path.append(tuple(joints[i][j] * (1 - t) + joints[i + 1][j] * t for j in range(3)))
    path.append(joints[-1])
    n = len(path)
    def radius(i):
        t = i / (n - 1)
        if isinstance(r0, tuple):
            return tuple(r0[j] + (r1[j] - r0[j]) * t for j in range(2))
        return r0 + (r1 - r0) * t
    tube(b, path, radius, lambda q, nn, i: colour(q, nn), part,
         lambda q, i: min(1.0, max(0.0, (top_z - q[2]) / max(top_z, 1.0))), sides)


def mix(a, c, t):
    t = min(1.0, max(0.0, t))
    return tuple(a[i] * (1 - t) + c[i] * t for i in range(3))


def shade(n, top, side, belly):
    """Colour by which way the surface faces: back, flank, belly."""
    return mix(mix(side, top, n[2] * 2.2), belly, -n[2] * 2.2 - .2)


# ---- The animals --------------------------------------------------------------------------------------------

def alligator():
    b = Builder()
    top, side, belly = (.012, .014, .01), (.04, .04, .028), (.4, .36, .24)

    def skin(q, n):
        c = shade(n, top, side, belly)
        if q[0] < -60 and n[2] > -.3 and math.sin(q[0] * .22) > .55:   # pale bands across the tail
            c = mix(c, (.16, .15, .1), .6)
        if q[0] > 95 and abs(n[2]) < .35:                                # the jaw line, pale with teeth showing
            c = mix(c, (.5, .47, .38), .5 if math.sin(q[0] * 1.3) > .3 else .15)
        return c

    def scutes(q, n, k):
        # Rows of raised scutes down the back and two crests along the tail.
        ridge = max(0.0, n[2] - .55) * 2.2
        return ridge * 3.2 * max(0.0, math.sin(q[0] * .55)) * (1.0 if -150 < q[0] < 80 else .3)

    tail = lambda q, k: min(1.0, max(0.0, (-40 - q[0]) / 135))   # noqa: E731
    pts = [(176, 0, 18, 6, 4), (162, 0, 19, 11, 6), (135, 0, 21, 15, 9), (108, 0, 24, 19, 13), (90, 0, 26, 21, 15),
           (70, 0, 28, 26, 18), (40, 0, 30, 36, 22), (0, 0, 31, 40, 24), (-35, 0, 30, 36, 22), (-60, 0, 28, 28, 19),
           (-90, 0, 25, 20, 16), (-120, 0, 21, 13, 12), (-150, 0, 16, 7, 8), (-176, 0, 12, 1.5, 3)]
    path, radii = stations(pts, 4)
    tube(b, path, lambda k: radii[k], lambda q, n, k: skin(q, n),
         lambda q, k: TAIL if q[0] < -40 else BODY, tail, 22, shape=scutes)
    for y in (1, -1):
        ball(b, (112, 10 * y, 33), (5, 4, 4), lambda q, n: (.12, .08, .02) if n[0] > .2 else top)   # eyes on their bumps
        ball(b, (174, 4 * y, 23), (2.2, 1.6, 1.6), lambda q, n: top)                                   # nostrils
    leg = lambda q, n: shade(n, top, side, mix(side, belly, .4))   # noqa: E731
    for x, y, part in ((70, 1, FL), (70, -1, FR), (-30, 1, BL), (-30, -1, BR)):
        reach = 46 if x > 0 else 50
        limb(b, [(x, 22 * y, 26), (x - 4, reach * y, 15), (x + 6, (reach + 2) * y, 3)], 9, 5.5, leg, part, 26)
        limb(b, [(x + 4, (reach + 2) * y, 2.0), (x + 20, (reach + 5) * y, 1.2)], (7.0, 2.2), (4.5, 1.2), leg, part, 26)   # the splayed foot
    return b


def flamingo():
    b = Builder()
    pink, red, black, pale = (.87, .23, .17), (.85, .07, .03), (.015, .015, .015), (.95, .55, .48)

    def plumage(q, n):
        if q[0] < -31:
            return black
        c = mix(pale, pink, .5 + .5 * n[1] ** 2 - .3 * n[2])
        if abs(n[1]) > .55 and -28 < q[0] < 12 and q[2] > 92:     # the folded wing: coverts flushed red
            c = mix(c, red, .55)
        return c

    body(b, [(34, 0, 99, 3, 3), (28, 0, 99, 10, 11), (18, 0, 97, 15, 16), (0, 0, 95, 17, 18), (-18, 0, 95, 15, 15),
             (-32, 0, 97, 9, 8), (-46, 0, 101, 2, 2)], plumage, BODY, sides=22)
    neck = [(24, 0, 104), (31, 0, 116), (27, 0, 128), (20, 0, 139), (23, 0, 150), (31, 0, 155)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in neck], 4)
    tube(b, path, lambda k: 3.6 - 1.0 * k / len(path), lambda q, n, k: mix(pink, pale, .3), HEAD,
         lambda q, k: k / (len(path) - 1), 12)
    ball(b, (35, 0, 156), (6.5, 4.2, 4.6), lambda q, n: mix(pink, pale, .4), HEAD, 1.0)
    bill = [(40, 0, 156), (46, 0, 155), (50, 0, 151), (51, 0, 146)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in bill], 3)
    tube(b, path, lambda k: (2.4 - 1.4 * k / len(path), 2.0 - 1.1 * k / len(path)),
         lambda q, n, k: black if k > len(path) * .45 else (.85, .82, .75), HEAD, lambda q, k: 1.0, 10)
    for y in (1, -1):
        ball(b, (37, 3.6 * y, 158), (1.0, .6, 1.0), lambda q, n: (.7, .6, .1), HEAD, 1.0, 8)
    leg = lambda q, n: (.62, .14, .12)   # noqa: E731
    for y, part in ((1, LEFT), (-1, RIGHT)):
        limb(b, [(2, 6 * y, 92), (2, 5 * y, 80)], 4, 2.2, lambda q, n: pink, part, 92)
        limb(b, [(2, 5 * y, 80), (-3, 5 * y, 44), (2, 5 * y, 3)], 1.7, 1.4, leg, part, 92, 8)
        limb(b, [(1, 5 * y, 1.2), (13, 5 * y, .9)], (3.4, .9), (2.6, .6), leg, part, 92, 8)   # webbed foot
    return b


def pelican():
    b = Builder()
    grey, dark, cream, crown, bill = (.14, .115, .09), (.06, .05, .04), (.78, .74, .62), (.85, .7, .32), (.6, .45, .26)

    def feathers(q, n):
        c = shade(n, mix(grey, (.22, .2, .17), .3), grey, dark)
        if abs(n[1]) > .5 and q[2] > 52:   # silvery wing coverts
            c = mix(c, (.3, .28, .25), .45)
        return c

    body(b, [(32, 0, 62, 4, 4), (25, 0, 62, 14, 14), (10, 0, 58, 20, 22), (-10, 0, 55, 21, 22), (-30, 0, 55, 17, 17),
             (-45, 0, 58, 10, 9), (-60, 0, 61, 2, 3)], feathers, BODY, sides=22)
    neck = [(24, 0, 70), (29, 0, 84), (26, 0, 96), (30, 0, 106)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in neck], 4)
    tube(b, path, lambda k: 6.0 - 1.2 * k / len(path),
         lambda q, n, k: (.16, .08, .05) if n[0] < -.55 else cream, HEAD, lambda q, k: k / (len(path) - 1), 14)
    ball(b, (34, 0, 108), (8, 6, 7), lambda q, n: crown if n[2] > .4 else cream, HEAD, 1.0)
    upper = [(40, 0, 109), (62, 0, 104), (86, 0, 97)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in upper], 4)
    tube(b, path, lambda k: (3.6 - 1.2 * k / len(path), 1.7), lambda q, n, k: mix(bill, (.8, .35, .1), k / len(path) - .4),
         HEAD, lambda q, k: 1.0, 10)
    pouch = [(40, 0, 104), (60, 0, 99), (80, 0, 95)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in pouch], 4)
    tube(b, path, lambda k: (3.2 - 1.4 * k / len(path), 3.8 - 2.6 * k / len(path)), lambda q, n, k: (.1, .12, .1), HEAD, lambda q, k: 1.0, 10)
    for y in (1, -1):
        ball(b, (38, 5.2 * y, 111), (1.4, .8, 1.4), lambda q, n: (.05, .03, .02), HEAD, 1.0, 8)
    leg = lambda q, n: (.045, .045, .045)   # noqa: E731
    for y, part in ((1, LEFT), (-1, RIGHT)):
        limb(b, [(0, 9 * y, 40), (3, 9 * y, 20), (0, 9 * y, 3)], 3.4, 2.6, leg, part, 40)
        limb(b, [(-1, 9 * y, 1.2), (14, 9 * y, .9)], (5.5, .9), (4.0, .6), leg, part, 40, 8)   # webbed foot
    return b


def cottonmouth():
    b = Builder()
    dark, olive, belly, lip = (.025, .02, .014), (.11, .085, .05), (.38, .33, .23), (.5, .45, .32)

    def scales(q, n):
        if n[2] < -.35:
            return belly
        band = .5 + .5 * math.sin(q[0] * .36 + .6 * math.sin(q[0] * .09))
        c = mix(olive, dark, band ** 1.5)
        if q[0] > 47 and -.25 < n[2] < .35 and abs(n[1]) > .5:   # the cream lip stripe
            c = lip
        if q[0] > 47 and n[2] >= .35:
            c = mix(dark, olive, .3)
        return c

    pts = [(64, 0, 3.2, 2.0, 1.6), (60, 0, 3.6, 4.6, 2.6), (53, 0, 4.0, 6.2, 3.3), (47, 0, 4.0, 4.0, 3.4),
           (38, 0, 4.2, 4.4, 4.0), (20, 0, 4.6, 5.0, 4.4), (0, 0, 4.8, 5.2, 4.6), (-20, 0, 4.6, 5.0, 4.4),
           (-38, 0, 4.0, 3.8, 3.4), (-52, 0, 3.0, 2.0, 2.0), (-60, 0, 2.5, .6, .6)]
    path, radii = stations(pts, 5)
    tube(b, path, lambda k: radii[k], lambda q, n, k: scales(q, n), SNAKE, lambda q, k: 1.0, 16)
    for y in (1, -1):
        ball(b, (57, 3.5 * y, 5.0), (1.0, .7, .9), lambda q, n: (.06, .04, .02), SNAKE, 1.0, 8)
    return b


def tortoise():
    b = Builder()
    # Owner, October 20: a darker brown shell, like the photo. (Vertex colours here read brighter than they look:
    # .28 showed as pale cream, so the shell tones sit near a seventh of that.)
    tan, seam, plastron, skin = (.04, .025, .011), (.004, .003, .002), (.09, .07, .035), (.09, .08, .06)

    def plate_at(q):
        # The shell is lofted along X. Give each anatomical band its own count along that axis.
        across = math.atan2(q[1], max(q[2] - 12, .1)) / (math.pi / 2)
        side = 1 if across >= 0 else -1
        a = abs(across)
        if a < .30:
            row, count, centre, half = 0, 5, 0.0, .30
        elif a < .76:
            row, count, centre, half = 1, 4, .53, .23
        elif a < 1.22:
            row, count, centre, half = 2, 11, .99, .23
        else:
            return None
        u = min(count - 1e-6, max(0.0, (q[0] + 40) / 80 * count))
        index = int(u)
        along = (u - index - .5) * 2
        across_local = (a - centre) / half
        radial = min(1.0, math.sqrt((along * along + across_local * across_local) * .5))
        return row, count, index, along, across_local, radial, side

    def shell(q, n):
        if n[2] < -.45:
            return plastron
        plate = plate_at(q)
        if not plate:
            return tan
        row, _, index, along, across_local, radial, side = plate
        # A repeatable but subtle tone shift keeps neighbouring plates distinct.
        rnd = random.Random(row * 1000 + side * 100 + index)
        base = mix(tan, (.075, .048, .02), rnd.uniform(.08, .36))
        rings = .5 + .5 * math.cos(radial * math.pi * 4)
        c = mix(base, mix(base, (.14, .09, .038), .42), rings * .24)
        # Dark seams divide every plate and the three shell bands.
        if abs(along) > .92 or abs(across_local) > .91:
            c = seam
        return c

    def shell_shape(q, n, k):
        flatten = -max(0.0, 12.5 - q[2]) if n[2] < 0 else 0.0
        plate = plate_at(q)
        if not plate or n[2] < .15:
            return flatten
        radial = plate[5]
        # Lift the centre of each scute slightly, leaving the polygonal seam visible around its rim.
        return flatten + 1.1 * max(0.0, 1.0 - radial * radial)

    body(b, [(40, 0, 27, 8, 5), (34, 0, 27, 25, 16), (20, 0, 27, 33, 24), (0, 0, 27, 36, 27), (-20, 0, 27, 33, 24),
             (-34, 0, 27, 25, 16), (-40, 0, 27, 8, 5)], shell, BODY, sides=56, shape=shell_shape, steps=8)
    neck = [(28, 0, 22), (40, 0, 24), (50, 0, 29), (55, 0, 31)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in neck], 3)
    tube(b, path, lambda k: 6.0 - 1.5 * k / len(path), lambda q, n, k: mix(skin, (.2, .17, .12), max(0, n[2])), HEAD,
         lambda q, k: k / (len(path) - 1), 12)
    ball(b, (59, 0, 32), (8, 5.4, 5.6), lambda q, n: mix(skin, (.2, .17, .12), max(0, n[2])), HEAD, 1.0)
    for y in (1, -1):
        ball(b, (63, 3.8 * y, 34), (1.2, .7, 1.1), lambda q, n: (.02, .02, .02), HEAD, 1.0, 8)
    leg = lambda q, n: mix(skin, (.17, .15, .11), .5 + .5 * math.sin(q[2] * 1.4 + q[0]))   # noqa: E731
    for x, y, part in ((22, 1, FL), (22, -1, FR), (-22, 1, BL), (-22, -1, BR)):
        limb(b, [(x, 22 * y, 21), (x + 3, 27 * y, 10), (x + 3, 28 * y, 0)], 8.5 if x > 0 else 9.5, 7.0, leg, part, 21)
    body(b, [(-36, 0, 17, 3, 3), (-42, 0, 14, 1, 1)], lambda q, n: skin, TAIL, lambda q, k: .5, 8, steps=1)
    return b
def squirrel_monkey():
    b = Builder()
    olive, grey, orange, cream, white, black = (.16, .15, .07), (.2, .2, .17), (.6, .3, .04), (.55, .5, .4), (.75, .72, .66), (.03, .03, .03)

    def fur(q, n):
        c = shade(n, olive, mix(olive, grey, .5), cream)
        if q[0] > 6 and n[2] > -.2:
            c = mix(c, (.42, .26, .06), .35)   # an orange cast over the shoulders
        return c

    body(b, [(19, 0, 27, 4, 4), (13, 0, 27, 8, 8), (0, 0, 25, 9.5, 9), (-10, 0, 25, 9, 9), (-17, 0, 26, 6, 6),
             (-20, 0, 27, 2, 2)], fur, BODY, sides=18)

    def face(q, n):
        if n[0] > .86 and n[2] < .25:
            return black                      # the muzzle
        if n[0] > .4 and n[2] < .6:
            return white                      # the mask
        return olive if n[2] > .2 else grey

    ball(b, (25, 0, 34), (8, 7.5, 8), face, HEAD, .35)
    for y in (1, -1):
        ball(b, (31.4, 3.1 * y, 36), (1.1, 1.5, 1.7), lambda q, n: (.05, .03, .02), HEAD, .35, 8)   # eyes
        ball(b, (21, 8.2 * y, 38), (1.8, 1.0, 2.6), lambda q, n: (.7, .55, .5), HEAD, .35, 8)       # ears
    limbs = lambda q, n: black if q[2] < 4 else orange   # noqa: E731
    for x, y, part in ((12, 1, FL), (12, -1, FR), (-12, 1, BL), (-12, -1, BR)):
        foot = 14 if x > 0 else -12
        limb(b, [(x, 6 * y, 22), (x + (2 if x > 0 else -4), 7 * y, 11), (foot, 7 * y, 1)], 3.2 if x > 0 else 3.6, 2.0, limbs, part, 22)
    tail = [(-19, 0, 27), (-30, 0, 20), (-42, 0, 16), (-54, 0, 20), (-61, 0, 28), (-64, 0, 36)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in tail], 4)
    tube(b, path, lambda k: 2.6 - .9 * k / len(path), lambda q, n, k: black if k > len(path) * .72 else mix(grey, olive, .4),
         TAIL, lambda q, k: k / (len(path) - 1), 10)
    return b


def spider():
    """A giant cave spider (about 1.7 m long, over 3 m across its legs; owner, October 28: bigger and properly 3D). A broad hairy abdomen with a
    pale chevron pattern, a ridged armoured cephalothorax, eight glowing red eyes, curved fangs between two palps, and eight jointed legs: a thick
    femur rising to a knee, a long tibia down to the ground, banded dark and tan, with a knuckle at each knee and bristles along them. Its legs
    step in two groups (parts FL and FR): left 1, right 2, left 3, right 4 against the other four. Sizes are tuning."""
    rng = random.Random(8)
    b = Builder()
    dark, brown, tan, pale, black, eye = (.06, .038, .024), (.14, .085, .045), (.36, .22, .09), (.5, .36, .17), (.025, .02, .015), (.85, .04, .03)

    def abdomen(q, n):
        if n[2] > .2:
            chevron = abs(q[1]) * .9 + (q[0] + 52) * .25
            if (chevron % 17) < 4.5 and q[0] < -30:
                return pale if (chevron % 17) < 2.2 else tan
            if abs(q[1]) < 6 and q[0] < -20:
                return (.02, .014, .01)
        return mix(dark, brown, max(0.0, n[2] * .9) + .15 * math.sin(q[0] * .3 + q[1] * .4))

    # the abdomen (broad, hairy) and the cephalothorax in front of it, with a raised ridge and a darker carapace
    body(b, [(-102, 0, 56, 3, 3), (-88, 0, 62, 24, 24), (-62, 0, 66, 41, 40), (-34, 0, 64, 36, 34), (-14, 0, 58, 12, 12)], abdomen, BODY, sides=22)
    carapace = lambda q, n: mix((.1, .065, .04), (.3, .2, .1), max(0.0, n[2]) * (.6 + .4 * math.sin(q[0] * .35)))   # noqa: E731
    body(b, [(-12, 0, 56, 6, 6), (0, 0, 60, 24, 21), (22, 0, 62, 29, 25), (44, 0, 60, 22, 18), (54, 0, 56, 9, 9)], carapace, BODY, sides=20)
    ball(b, (24, 0, 80), (20, 9, 7), lambda q, n: (.1, .065, .04), BODY, 0.0, 12)          # the raised ridge along its back
    # eight eyes in two rows, the middle pair big, glowing red; the fangs and palps
    for y in (1, -1):
        for x, yy, z, r in ((53, 7, 66, 3.6), (50, 15, 63, 2.4), (47, 20, 66, 2.2), (44, 11, 71, 1.9)):
            ball(b, (x, yy * y, z), (r, r, r), lambda q, n: eye, BODY, 0.0, 8)
        limb(b, [(50, 8 * y, 52), (63, 9 * y, 44), (70, 7 * y, 28), (68, 5 * y, 15)], 6.0, 1.2, lambda q, n: mix(tan, black, (60 - q[2]) / 45), BODY, 80, 12)   # a fang
        limb(b, [(46, 17 * y, 50), (58, 24 * y, 46), (66, 26 * y, 33)], 3.0, 1.6, lambda q, n: brown, BODY, 80, 10)                                # a palp
    banded = lambda q, n: tan if int((abs(q[0]) * .6 + abs(q[1]) * .7 + q[2]) // 13) % 4 == 0 else (brown if int((abs(q[0]) + abs(q[1])) // 7) % 2 else dark)   # noqa: E731

    def seg_colour(a, b2):
        """A leg part's colour by how far along it a point lies: dark brown with a few hairy tan rings, and tan at both joints."""
        ax = sub(b2, a)
        length2 = ax[0] ** 2 + ax[1] ** 2 + ax[2] ** 2 or 1.0

        def colour(q, n):
            t = ((q[0] - a[0]) * ax[0] + (q[1] - a[1]) * ax[1] + (q[2] - a[2]) * ax[2]) / length2
            if t < .07 or t > .93:
                return tan
            return mix(black, dark, .5 + .5 * math.sin(t * 38)) if int(t * 9) % 3 else tan if int(t * 40) % 9 == 0 else dark
        return colour

    hair = lambda: rng.choice((black, dark, brown, brown, tan))   # noqa: E731

    def bristles(centre, radii, count, length, part=BODY, sweep=-.55):
        """Fine hair over the body (owner, October 29): many thin short hairs, each leaning back along the body (sweep) like a real spider's setae."""
        for _ in range(count):
            d = norm((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) * .8))
            if d[2] < -.3:
                continue
            base = tuple(centre[c] + d[c] * radii[c] * .95 for c in range(3))
            lean = norm((d[0] + sweep, d[1], d[2] + .15))
            tip = tuple(base[c] + lean[c] * length * rng.uniform(.6, 1.4) for c in range(3))
            colour = hair()
            limb(b, [base, tip], 1.1, .1, lambda q, n, colour=colour: colour, part, 1.0, 4)

    bristles((-62, 0, 64), (42, 40, 39), 520, 12)              # the abdomen is the hairiest
    bristles((22, 0, 62), (29, 25, 21), 170, 8)                # the carapace
    bristles((48, 0, 56), (10, 14, 10), 40, 7, sweep=.3)       # a mat of hair round the mouthparts
    attach = (36.0, 20.0, -4.0, -26.0)
    spread = (38.0, 72.0, 108.0, 144.0)      # each leg's heading in the plan, degrees from the nose
    reach = (160.0, 176.0, 176.0, 160.0)
    for index in range(4):
        for y in (1, -1):
            part = FL if (index + (0 if y > 0 else 1)) % 2 == 0 else FR
            phi = math.radians(spread[index])
            d = (math.cos(phi), y * math.sin(phi))
            x0 = attach[index]
            R = reach[index]

            def at(f, z):
                return (x0 + d[0] * R * f, 14 * y + d[1] * R * f, z)
            # femur up to the knee, tibia down and out, metatarsus nearly upright, a short tarsus whose tip rests on the ground (owner, October 29:
            # realistic legs that touch the ground)
            hip, knee, tib, meta, foot = at(0, 58), at(.3, 114), at(.62, 70), at(.86, 24), at(1.0, 1.4)
            limb(b, [hip, knee], 9.0, 7.0, seg_colour(hip, knee), part, 118, 12)                                       # the thick femur up to the knee
            ball(b, knee, (10, 10, 10), lambda q, n: tan, part, .3, 10)                                                # the knee
            limb(b, [knee, tib], 7.0, 5.0, seg_colour(knee, tib), part, 118, 10)                                       # tibia
            limb(b, [tib, meta], 5.0, 3.6, seg_colour(tib, meta), part, 118, 10)                                       # metatarsus
            limb(b, [meta, foot], 3.6, 2.4, seg_colour(meta, foot), part, 118, 10)                                     # tarsus
            ball(b, foot, (3.4, 3.4, 1.6), lambda q, n: black, part, 1.0, 8)                                           # the foot pad on the ground
            for seg, count in (((hip, knee), 22), ((knee, tib), 36), ((tib, meta), 30), ((meta, foot), 16)):           # hair along each part of the leg
                for k in range(count):
                    u = rng.uniform(.05, .95)
                    base = tuple(seg[0][c] * (1 - u) + seg[1][c] * u for c in range(3))
                    side = norm((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) + .3))
                    along = norm(sub(seg[1], seg[0]))
                    lean = norm(tuple(side[c] + along[c] * .8 for c in range(3)))                       # swept toward the foot
                    tip = tuple(base[c] + lean[c] * rng.uniform(9, 18) for c in range(3))
                    colour = hair()
                    limb(b, [base, tip], 1.5, .1, lambda q, n, colour=colour: colour, part, 118, 4)
    b.colours = [tuple(c ** 2.2 for c in col) for col in b.colours]   # vertex colours are read back as sRGB bytes, so a linear palette must be darkened to show as intended
    return b


def quadruped(b, fur, spec):
    """A four-legged body from one spec (sizes in cm): the torso loft, then a leg and flat paw at each corner."""
    path, radii = stations(spec['torso'], 4)
    tube(b, path, lambda k: radii[k], lambda q, n, k: fur(q, n), BODY, lambda q, k: 0.0, 22)
    hip, knee = spec['hip_z'], spec['knee_z']
    for x, y, part in spec['legs']:
        sx = spec['spread'] * y
        bend = spec['bend'] * (1 if x > 0 else -1)
        limb(b, [(x, sx, hip), (x + bend, sx, knee), (x, sx, 1.5)], spec['thigh'], spec['paw'], lambda q, n: fur(q, n), part, hip)
        limb(b, [(x, sx, 1.4), (x + spec['reach'], sx, 1.0)], (spec['paw'] * 1.05, 1.3), (spec['paw'] * .8, 1.0),
             lambda q, n: spec['pad'], part, hip)
    return b


def scaled(b, factor):
    """The same animal, every dimension times factor."""
    b.verts = [tuple(c * factor for c in v) for v in b.verts]
    return b


def bear(fur_c=(.012, .01, .009), belly=(.02, .016, .012), muzzle=(.2, .14, .08)):
    b = Builder()
    fur = lambda q, n: mix(fur_c, belly, max(0.0, -n[2]))   # noqa: E731
    spec = dict(torso=[(88, 0, 58, 22, 24), (70, 0, 70, 30, 34), (40, 0, 74, 36, 38), (0, 0, 70, 36, 36), (-40, 0, 66, 34, 34),
                       (-75, 0, 58, 28, 28), (-92, 0, 52, 10, 10)], hip_z=56, knee_z=30, spread=22, bend=6,
                thigh=14, paw=10, reach=10, pad=(.004, .004, .003), legs=[(58, 1, FL), (58, -1, FR), (-52, 1, BL), (-52, -1, BR)])
    quadruped(b, fur, spec)
    path, _ = stations([(86, 0, 66, 0, 0), (110, 0, 72, 0, 0)], 3)
    tube(b, path, lambda k: 22 - 4 * k / len(path), lambda q, n, k: fur(q, n), HEAD, lambda q, k: .6 + .4 * k / len(path), 14)
    ball(b, (122, 0, 70), (20, 16, 16), lambda q, n: muzzle if n[0] > .5 and n[2] < .6 else fur(q, n), HEAD, 1.0)
    ball(b, (142, 0, 66), (10, 7, 6), lambda q, n: muzzle, HEAD, 1.0, 10)
    ball(b, (151, 0, 67), (2.5, 3.5, 2.5), lambda q, n: (0.0, 0.0, 0.0), HEAD, 1.0, 8)
    for y in (1, -1):
        ball(b, (126, 9 * y, 76), (2.2, 1.2, 1.8), lambda q, n: (.04, .02, .01), HEAD, 1.0, 8)
        ball(b, (110, 12 * y, 86), (4, 5, 6), lambda q, n: fur(q, n), HEAD, 1.0, 10)
    body(b, [(-90, 0, 54, 4, 4), (-100, 0, 52, 3, 3)], lambda q, n: fur(q, n), TAIL, lambda q, k: .5, 8, steps=1)
    return b


def lion():
    b = Builder()
    tawny, belly, mane, tuft = (.28, .16, .06), (.45, .34, .2), (.1, .045, .018), (.03, .02, .012)
    fur = lambda q, n: mix(tawny, belly, max(0.0, -n[2] * 1.4))   # noqa: E731
    spec = dict(torso=[(70, 0, 66, 20, 26), (52, 0, 82, 26, 32), (20, 0, 84, 28, 34), (-20, 0, 78, 24, 28), (-55, 0, 74, 22, 25),
                       (-78, 0, 72, 10, 12)], hip_z=64, knee_z=34, spread=14, bend=7, thigh=11, paw=8, reach=11,
                pad=(.12, .08, .04), legs=[(48, 1, FL), (48, -1, FR), (-52, 1, BL), (-52, -1, BR)])
    quadruped(b, fur, spec)
    path, _ = stations([(66, 0, 76, 0, 0), (88, 0, 90, 0, 0)], 3)
    tube(b, path, lambda k: 17 - 3 * k / len(path), lambda q, n, k: mane if n[0] < .6 else fur(q, n), HEAD, lambda q, k: .6 + .4 * k / len(path), 14)
    ball(b, (84, 0, 90), (26, 25, 26), lambda q, n: mane, HEAD, 1.0, 16)   # the mane
    ball(b, (102, 0, 88), (13, 11, 11), lambda q, n: fur(q, n), HEAD, 1.0)
    ball(b, (114, 0, 85), (7, 6, 5), lambda q, n: (.5, .38, .26), HEAD, 1.0, 10)
    ball(b, (120, 0, 87), (2, 3, 2), lambda q, n: (.02, .01, .01), HEAD, 1.0, 8)
    for y in (1, -1):
        ball(b, (108, 8 * y, 92), (2, 1.2, 1.5), lambda q, n: (.5, .32, .05), HEAD, 1.0, 8)
        ball(b, (92, 14 * y, 106), (4, 3, 5), lambda q, n: fur(q, n), HEAD, 1.0, 8)
    tail = [(-76, 0, 72), (-100, 0, 64), (-122, 0, 52), (-136, 0, 42)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in tail], 4)
    tube(b, path, lambda k: 3.2 + (3.0 if k > len(path) * .85 else 0), lambda q, n, k: tuft if k > len(path) * .85 else fur(q, n), TAIL,
         lambda q, k: k / (len(path) - 1), 10)
    return b


def boar():
    """Wild boar (Phase 1 slice 4, the Plains' modest threat, CLAUDE.md 5.2): about 140 cm nose to rump and 85 cm at the
    shoulder, deep and narrow in the chest, the shoulders higher than the rump, short legs on small dark hooves, a long
    wedge head ending in a flat snout disc with short pale tusks, upright ears and a thin tail. Grizzled grey-brown
    bristle, darker along the back and legs."""
    b = Builder()
    back, flank, dark, disc, tusk = (.022, .017, .012), (.06, .046, .032), (.012, .009, .007), (.09, .062, .05), (.5, .45, .34)
    fur = lambda q, n: mix(back, flank, min(1.0, max(0.0, .5 - n[2] * .8)))   # noqa: E731
    # The body: deepest and highest at the shoulders, falling away to a smaller rump.
    spec = dict(torso=[(60, 0, 62, 15, 22), (40, 0, 64, 19, 28), (12, 0, 61, 19, 25), (-20, 0, 57, 17, 21), (-46, 0, 54, 14, 17),
                       (-60, 0, 52, 8, 9)], hip_z=44, knee_z=22, spread=10, bend=5, thigh=6, paw=3.5, reach=4,
                pad=dark, legs=[(40, 1, FL), (40, -1, FR), (-44, 1, BL), (-44, -1, BR)])
    quadruped(b, fur, spec)
    # The head: one long wedge from the deep neck down to the snout, narrower than it is tall.
    body(b, [(52, 0, 66, 16, 22), (70, 0, 60, 12, 17), (84, 0, 51, 8, 10.5), (96, 0, 46.5, 6, 6.5), (100, 0, 46, 5.8, 5.4)],
         lambda q, n: fur(q, n), HEAD, lambda q, k: 1.0, 16)
    ball(b, (101, 0, 46), (1.8, 6.0, 5.4), lambda q, n: disc if n[0] > .4 else dark, HEAD, 1.0, 12)      # the snout disc
    # The bristle crest along the spine, darker, highest over the shoulders.
    body(b, [(52, 0, 86, 2.0, 4.0), (30, 0, 92, 2.5, 5.0), (0, 0, 87, 2.0, 3.5), (-25, 0, 79, 1.5, 2.0)], lambda q, n: dark, BODY,
         lambda q, k: 0.0, 8)
    for y in (1, -1):
        ball(b, (102.5, 2.2 * y, 46.5), (1.0, 1.0, 1.4), lambda q, n: (.01, .008, .006), HEAD, 1.0, 8)   # nostrils
        ball(b, (92, 6.2 * y, 44), (3.5, 1.0, 1.0), lambda q, n: tusk, HEAD, 1.0, 8)                       # tusks, curving up
        ball(b, (94.5, 6.8 * y, 47), (1.0, .9, 2.5), lambda q, n: tusk, HEAD, 1.0, 8)
        ball(b, (76, 9.5 * y, 61), (1.6, 1.0, 1.4), lambda q, n: (.005, .004, .003), HEAD, 1.0, 8)        # eyes
        ball(b, (64, 8.5 * y, 77), (2.5, 3.0, 6.5), lambda q, n: dark, HEAD, 1.0, 10)                      # ears
    body(b, [(-58, 0, 54, 2.2, 2.2), (-70, 0, 46, 1.6, 1.6), (-76, 0, 38, 2.6, 2.6)], lambda q, n: dark, TAIL, lambda q, k: .5, 8, steps=1)
    return b


def giant_crocodile(top=(.03, .028, .016), side=(.07, .06, .03), belly=(.42, .38, .24)):
    b = Builder()

    def skin(q, n):
        c = shade(n, top, side, belly)
        if q[0] < -100 and n[2] > -.3 and math.sin(q[0] * .14) > .5:
            c = mix(c, (.015, .014, .01), .6)
        if q[0] > 150 and abs(n[2]) < .35:
            c = mix(c, (.55, .5, .38), .5 if math.sin(q[0] * .9) > .3 else .15)
        return c

    def scutes(q, n, k):
        ridge = max(0.0, n[2] - .55) * 2.2
        return ridge * 4.5 * max(0.0, math.sin(q[0] * .35)) * (1.0 if -260 < q[0] < 150 else .3)

    tail = lambda q, k: min(1.0, max(0.0, (-60 - q[0]) / 240))   # noqa: E731
    pts = [(300, 0, 26, 8, 6), (280, 0, 28, 15, 9), (240, 0, 30, 24, 15), (190, 0, 34, 30, 20), (150, 0, 38, 36, 24),
           (100, 0, 42, 48, 32), (40, 0, 44, 58, 36), (-30, 0, 44, 62, 38), (-90, 0, 42, 54, 34), (-150, 0, 38, 40, 28),
           (-210, 0, 32, 26, 22), (-270, 0, 24, 14, 15), (-330, 0, 16, 7, 9), (-380, 0, 12, 1.5, 3)]
    path, radii = stations(pts, 4)
    tube(b, path, lambda k: radii[k], lambda q, n, k: skin(q, n), lambda q, k: TAIL if q[0] < -60 else BODY, tail, 24, shape=scutes)
    for y in (1, -1):
        ball(b, (176, 17 * y, 56), (7, 6, 6), lambda q, n: (.14, .1, .02) if n[0] > .2 else top)
        ball(b, (296, 6 * y, 33), (3, 2.4, 2.4), lambda q, n: top)
    leg = lambda q, n: shade(n, top, side, mix(side, belly, .4))   # noqa: E731
    for x, y, part in ((100, 1, FL), (100, -1, FR), (-60, 1, BL), (-60, -1, BR)):
        reach = 62 if x > 0 else 68
        limb(b, [(x, 34 * y, 36), (x - 6, reach * y, 22), (x + 8, (reach + 3) * y, 4)], 15, 9, leg, part, 36)
        limb(b, [(x + 6, (reach + 3) * y, 3), (x + 32, (reach + 8) * y, 2)], (11, 3), (7, 2), leg, part, 36)
    return b


def elephant():
    b = Builder()
    hide, dark, ivory = (.07, .062, .052), (.045, .04, .034), (.55, .5, .38)
    fur = lambda q, n: mix(hide, dark, max(0.0, -n[2]) * .8)   # noqa: E731
    spec = dict(torso=[(150, 0, 190, 60, 60), (120, 0, 205, 80, 78), (60, 0, 215, 92, 88), (0, 0, 212, 94, 88),
                       (-70, 0, 205, 90, 84), (-130, 0, 195, 76, 76), (-160, 0, 185, 36, 36)],
                hip_z=175, knee_z=95, spread=52, bend=6, thigh=30, paw=24, reach=6, pad=(.09, .08, .07),
                legs=[(100, 1, FL), (100, -1, FR), (-105, 1, BL), (-105, -1, BR)])
    quadruped(b, fur, spec)
    path, _ = stations([(140, 0, 200, 0, 0), (175, 0, 204, 0, 0)], 3)
    tube(b, path, lambda k: 52 - 8 * k / len(path), lambda q, n, k: fur(q, n), HEAD, lambda q, k: .5 + .5 * k / len(path), 16)
    ball(b, (188, 0, 205), (46, 40, 50), lambda q, n: fur(q, n), HEAD, 1.0, 18)
    trunk = [(222, 0, 185), (238, 0, 150), (244, 0, 110), (240, 0, 70), (252, 0, 36), (266, 0, 40)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in trunk], 4)
    tube(b, path, lambda k: 22 - 12 * k / len(path), lambda q, n, k: fur(q, n), HEAD, lambda q, k: .7 + .3 * k / len(path), 14)
    for y in (1, -1):
        ball(b, (212, 38 * y, 210), (2.5, 2, 3), lambda q, n: (.02, .015, .01), HEAD, 1.0, 8)
        ball(b, (160, 66 * y, 225), (6, 42, 50), lambda q, n: fur(q, n), HEAD, 1.0, 14)   # the fan ears
        tusk = [(226, 24 * y, 170), (254, 28 * y, 142), (284, 26 * y, 144), (306, 22 * y, 162)]
        tp, _ = stations([(x, yy, z, 0, 0) for x, yy, z in tusk], 3)
        tube(b, tp, lambda k: 7 - 5.5 * k / len(tp), lambda q, n, k: ivory, HEAD, lambda q, k: 1.0, 10)
    tail = [(-158, 0, 190), (-170, 0, 140), (-168, 0, 90)]
    path, _ = stations([(x, y, z, 0, 0) for x, y, z in tail], 4)
    tube(b, path, lambda k: 4.0 + (4 if k > len(path) * .85 else 0), lambda q, n, k: dark, TAIL, lambda q, k: k / (len(path) - 1), 8)
    return b


# ---- Wildlife for every island (November 6) -------------------------------------------------------------------
# Placeholders in the same lofted style as the animals above, so every island carries its planned wildlife; realistic,
# rigged replacements arrive in Phase 5 (CLAUDE.md 5.6). Sizes are adults of the real species.

def cervid(b, coat, belly, neck, spec):
    """A deer-family body: a deep chest on long slender legs and small hooves, the neck carried up and forward, a narrow
    head with a dark muzzle, upright ears and a short pale-backed tail. spec: (length scale, shoulder height, girth)."""
    k, h, g = spec
    fur = lambda q, n: mix(neck if q[0] > 42 * k else coat, belly, max(0.0, -n[2] * 1.5))   # noqa: E731
    quadruped(b, fur, dict(torso=[(58 * k, 0, h * .92, 13 * g, 18 * g), (42 * k, 0, h * .98, 17 * g, 22 * g),
                                  (10 * k, 0, h * .95, 17 * g, 21 * g), (-25 * k, 0, h * .94, 16 * g, 19 * g),
                                  (-52 * k, 0, h * .93, 14 * g, 16 * g), (-62 * k, 0, h * .9, 7 * g, 8 * g)],
                           hip_z=h * .86, knee_z=h * .45, spread=9 * g, bend=4 * k, thigh=6 * g, paw=2.6 * g, reach=3 * k,
                           pad=(.02, .016, .012), legs=[(42 * k, 1, FL), (42 * k, -1, FR), (-46 * k, 1, BL), (-46 * k, -1, BR)]))
    path, _ = stations([(56 * k, 0, h * .98, 0, 0), (70 * k, 0, h * 1.18, 0, 0), (78 * k, 0, h * 1.36, 0, 0)], 3)
    tube(b, path, lambda j: (11 - 4 * j / len(path)) * g, lambda q, n, j: fur(q, n), HEAD,
         lambda q, j: .5 + .5 * j / len(path), 14)
    body(b, [(74 * k, 0, h * 1.42, 7 * g, 8 * g), (86 * k, 0, h * 1.38, 6 * g, 6.5 * g), (100 * k, 0, h * 1.3, 3.5 * g, 4 * g),
             (104 * k, 0, h * 1.28, 2.6 * g, 3 * g)], lambda q, n: (.03, .025, .02) if q[0] > 97 * k else fur(q, n), HEAD,
         lambda q, j: 1.0, 14)
    for y in (1, -1):
        ball(b, (86 * k, 5.5 * g * y, h * 1.43), (1.6, 1.0, 1.4), lambda q, n: (.01, .008, .006), HEAD, 1.0, 8)
        ball(b, (74 * k, 7 * g * y, h * 1.5), (2.2, 4.5, 7), lambda q, n: fur(q, n), HEAD, 1.0, 10)
    ball(b, (-62 * k, 0, h * .9), (4 * k, 4 * g, 6 * g), lambda q, n: (.5, .47, .42) if n[0] < 0 else coat, TAIL, .5, 10)
    return b


def antlers(b, head_x, head_z, size):
    """A pair of swept-back branching antlers (both sexes carry them in caribou)."""
    tone = lambda q, n, j: (.2, .16, .11)   # noqa: E731
    for y in (1, -1):
        beam = [(head_x, 4 * y, head_z), (head_x - 6 * size, 14 * y * size, head_z + 22 * size),
                (head_x - 4 * size, 20 * y * size, head_z + 48 * size), (head_x + 8 * size, 16 * y * size, head_z + 66 * size),
                (head_x + 20 * size, 10 * y * size, head_z + 70 * size)]
        path, _ = stations([(x, yy, z, 0, 0) for x, yy, z in beam], 3)
        tube(b, path, lambda j: 2.4 - 1.4 * j / len(path), tone, HEAD, lambda q, j: 1.0, 8)
        for i in (1, 2, 3):
            bx, by, bz = beam[i]
            path, _ = stations([(bx, by, bz, 0, 0), (bx + 12 * size, by * .9, bz + 10 * size, 0, 0)], 2)
            tube(b, path, lambda j: 1.4 - .6 * j / len(path), tone, HEAD, lambda q, j: 1.0, 6)
        path, _ = stations([(head_x + 2, 5 * y, head_z + 6, 0, 0), (head_x + 14 * size, 6 * y, head_z + 14 * size, 0, 0)], 2)
        tube(b, path, lambda j: (2.6, 1.2), tone, HEAD, lambda q, j: 1.0, 6)    # the brow tine over the face


def deer():
    """Red deer hind (Plains): about 190 cm long, 110 cm at the shoulder, red-brown with a paler belly."""
    return cervid(Builder(), (.2, .1, .045), (.42, .34, .24), (.17, .09, .04), (1.0, 110.0, 1.0))


def caribou():
    """Caribou (Winter): about 210 cm long, 120 cm at the shoulder, dark brown with a creamy neck and tall swept antlers."""
    b = cervid(Builder(), (.11, .08, .055), (.5, .47, .4), (.48, .45, .38), (1.1, 120.0, 1.15))
    antlers(b, 78 * 1.1, 120 * 1.5, 1.0)
    return b


def wolf():
    """Grey wolf (Plains' deep wood, Winter): about 150 cm nose to rump, 80 cm at the shoulder, grizzled grey with a pale
    belly, a long muzzle, upright ears and a bushy tail."""
    b = Builder()
    back, side, belly = (.09, .085, .075), (.2, .18, .15), (.5, .47, .4)
    fur = lambda q, n: mix(mix(side, back, max(0.0, n[2]) * 1.4), belly, max(0.0, -n[2] * 1.6))   # noqa: E731
    quadruped(b, fur, dict(torso=[(50, 0, 62, 11, 15), (36, 0, 65, 14, 19), (5, 0, 62, 13, 16), (-25, 0, 60, 12, 14),
                                  (-46, 0, 60, 11, 13), (-55, 0, 60, 6, 7)],
                           hip_z=56, knee_z=28, spread=8, bend=5, thigh=5.5, paw=3.4, reach=6, pad=(.03, .028, .025),
                           legs=[(36, 1, FL), (36, -1, FR), (-42, 1, BL), (-42, -1, BR)]))
    path, _ = stations([(48, 0, 66, 0, 0), (62, 0, 74, 0, 0)], 3)
    tube(b, path, lambda j: 11 - 2 * j / len(path), lambda q, n, j: fur(q, n), HEAD, lambda q, j: .6 + .4 * j / len(path), 14)
    ball(b, (68, 0, 76), (11, 9, 9), lambda q, n: fur(q, n), HEAD, 1.0)
    body(b, [(74, 0, 74, 6, 6), (86, 0, 71, 4.2, 4.4), (96, 0, 69, 2.6, 3)], lambda q, n: belly if n[2] < 0 else fur(q, n),
         HEAD, lambda q, j: 1.0, 12, steps=2)
    ball(b, (97, 0, 69.5), (1.8, 2.2, 1.8), lambda q, n: (.01, .01, .01), HEAD, 1.0, 8)
    for y in (1, -1):
        ball(b, (78, 5 * y, 79), (1.5, 1.0, 1.0), lambda q, n: (.3, .22, .05), HEAD, 1.0, 8)
        ball(b, (65, 6 * y, 88), (2.0, 3.0, 6.0), lambda q, n: back, HEAD, 1.0, 10)
    body(b, [(-54, 0, 60, 4, 4), (-66, 0, 52, 6, 6), (-78, 0, 42, 6, 6), (-86, 0, 34, 3, 3)],
         lambda q, n: back if q[0] < -82 else fur(q, n), TAIL, lambda q, j: .6, 10, steps=2)
    return b


def hare():
    """Brown hare (Plains, Winter): about 55 cm long, long black-tipped ears, long hind feet and a white scut."""
    b = Builder()
    coat, belly = (.18, .13, .08), (.45, .4, .32)
    fur = lambda q, n: mix(coat, belly, max(0.0, -n[2] * 1.5))   # noqa: E731
    body(b, [(20, 0, 22, 5, 6), (14, 0, 22, 8, 9), (0, 0, 21, 9, 10), (-12, 0, 21, 9, 10), (-20, 0, 19, 5, 6)], fur, BODY)
    for x, y, part, foot in ((12, 1, FL, 1), (12, -1, FR, 1), (-12, 1, BL, 9), (-12, -1, BR, 9)):
        limb(b, [(x, 5 * y, 18), (x + 2, 5 * y, 8), (x, 5 * y, 1)], 2.6 if x > 0 else 4.2, 1.4, fur, part, 18)
        limb(b, [(x, 5 * y, .8), (x + foot + 2, 5 * y, .6)], (1.8, .8), (1.4, .6), fur, part, 18)
    ball(b, (25, 0, 26), (6.5, 4.5, 5), fur, HEAD, 1.0)
    for y in (1, -1):
        ball(b, (27, 3.6 * y, 28), (1.2, .7, 1.1), lambda q, n: (.02, .015, .01), HEAD, 1.0, 8)
        path, _ = stations([(21, 2.2 * y, 30, 0, 0), (18, 3.0 * y, 38, 0, 0), (15, 3.6 * y, 46, 0, 0)], 3)
        tube(b, path, lambda j: (2.0, .7), lambda q, n, j: (.02, .02, .02) if q[2] > 43 else coat, HEAD, lambda q, j: 1.0, 8)
    ball(b, (-21, 0, 21), (3, 3, 3), lambda q, n: (.7, .68, .64), TAIL, .5, 8)
    return b


def snake():
    """A blotched brown snake about 130 cm long: the snake of the Swamp, Desert and Jungle islands."""
    b = Builder()
    sand, brown, belly = (.3, .22, .12), (.09, .05, .025), (.45, .4, .3)

    def scales(q, n):
        if n[2] < -.35:
            return belly
        blot = .5 + .5 * math.sin(q[0] * .5)
        return mix(sand, brown, (blot ** 3) * (1.0 if abs(n[1]) < .8 else .4))

    pts = [(64, 0, 3.0, 2.4, 1.6), (59, 0, 3.4, 4.0, 2.6), (53, 0, 3.8, 4.2, 3.0), (47, 0, 3.8, 3.4, 3.0),
           (30, 0, 4.0, 4.0, 3.6), (0, 0, 4.4, 4.6, 4.0), (-25, 0, 4.0, 4.2, 3.6), (-45, 0, 3.0, 2.6, 2.4), (-62, 0, 2.2, .5, .5)]
    path, radii = stations(pts, 5)
    tube(b, path, lambda j: radii[j], lambda q, n, j: scales(q, n), SNAKE, lambda q, j: 1.0, 16)
    for y in (1, -1):
        ball(b, (57, 3.2 * y, 4.6), (1.0, .7, .9), lambda q, n: (.05, .03, .01), SNAKE, 1.0, 8)
    return b


def polar_bear():
    """Polar bear (Winter's ice): the black bear's build a quarter larger, creamy white with a black nose."""
    return scaled(bear(fur_c=(.62, .6, .52), belly=(.5, .48, .4), muzzle=(.6, .58, .5)), 1.25)


def crocodile():
    """Crocodile (the Swamp's edges): the giant crocodile's build at about 440 cm, a greyer olive."""
    return scaled(giant_crocodile(top=(.05, .05, .03), side=(.11, .1, .06), belly=(.45, .42, .3)), .65)


# Name, display, builder, size (length, height), stride, gait (0 four legs, 1 two legs, 2 snake), animation
# (swing, lift, bob, tail sway, nod, snake amplitude, wave), surface (scales, scale size, fur, mottle, roughness),
# Neutral kinds: never start a fight, but defend themselves when struck instead of fleeing (UEWAnimalDefinition::bDefendsItself).
DEFENDERS = ('Elephant',)
# behaviour (aggressive, walk, run, turn, roam, wade, notice, damage, interval, reach, attack name, health), yield
# (fewest, most), and where it lives (habitat, count on the island, count on the second island).
ANIMALS = {
    'Alligator': dict(display='American Alligator', build=alligator, size=(352, 50), stride=75, gait=0,
                      anim=(15, 5, .6, 6, 0, 0, 1), surface=(.3, 3.2, 0, .25, .55),
                      behave=(True, 70, 320, 70, 900, 45, 650, 20, 1.8, 70, 'bite', 250), yield_=(6, 10), live=('water', 1, 1)),
    'Flamingo': dict(display='Flamingo', build=flamingo, size=(90, 160), stride=55, gait=1,
                     anim=(13, 7, 1.2, 0, 3, 0, 1), surface=(0, 1, .25, .12, .8),
                     behave=(False, 55, 380, 160, 700, 25, 0, 0, 1, 0, '', 40), yield_=(2, 5), live=('beach', 3, 2)),
    'Pelican': dict(display='Brown Pelican', build=pelican, size=(146, 112), stride=40, gait=1,
                    anim=(9, 5, 1.6, 0, 2, 0, 1), surface=(0, 1, .3, .12, .8),
                    behave=(False, 45, 300, 160, 600, 10, 0, 0, 1, 0, '', 45), yield_=(2, 5), live=('beach', 2, 2)),
    'Cottonmouth': dict(display='Cottonmouth', build=cottonmouth, size=(124, 10), stride=45, gait=2,
                        anim=(0, 0, 0, 0, 0, 7, 45), surface=(.35, 1.3, 0, .15, .45),
                        behave=(True, 35, 180, 90, 500, 0, 320, 12, 2.0, 45, 'bite', 30), yield_=(2, 5), live=('inland', 2, 1)),
    'Tortoise': dict(display='Tortoise', build=tortoise, size=(118, 62), stride=26, gait=0,
                     anim=(6, 3, .3, 0, 1.5, 0, 1), surface=(.3, 1.6, 0, .2, .7),
                     behave=(False, 14, 32, 40, 400, 0, 0, 0, 1, 0, '', 150), yield_=(6, 10), live=('inland', 2, 1)),
    'Bear': dict(display='Black Bear', build=bear, size=(190, 100), stride=90, gait=0,
                 anim=(16, 5, 1.2, 3, 2, 0, 1), surface=(0, 1, .55, .12, .9),
                 behave=(True, 80, 520, 90, 1100, 0, 700, 24, 1.6, 90, 'swipe', 350), yield_=(8, 12), live=('inland', 0, 0)),
    'Lion': dict(display='Lion', build=lion, size=(260, 110), stride=95, gait=0,
                 anim=(17, 6, 1.0, 5, 1.5, 0, 1), surface=(0, 1, .4, .14, .85),
                 behave=(True, 90, 700, 110, 1200, 0, 800, 20, 1.4, 85, 'bite', 300), yield_=(8, 12), live=('inland', 0, 0)),
    # The Plains' modest threat (Phase 1 slice 4): it charges only a survivor who comes within 6 m, gives up past about 10 m,
    # and a sprinting survivor (750 cm/s) outruns it; 8 a gore every 1.6 s. Placed by build_plains_threat.py, not place().
    'Boar': dict(display='Wild Boar', build=boar, size=(140, 85), stride=55, gait=0,
                 anim=(15, 5, 1.2, 4, 2, 0, 1), surface=(0, 1, .7, .15, .9),
                 behave=(True, 70, 520, 130, 900, 0, 600, 8, 1.6, 60, 'gore', 80), yield_=(3, 5), live=('plains', 0, 0)),
    'GiantCrocodile': dict(display='Giant Crocodile', build=giant_crocodile, size=(680, 90), stride=150, gait=0,
                           anim=(24, 7, .8, 9, 0, 0, 1), surface=(.3, 5.0, 0, .25, .55),
                           behave=(True, 80, 420, 60, 1200, 90, 900, 45, 2.2, 150, 'bite', 900), yield_=(14, 20), live=('water', 0, 0)),
    'Elephant': dict(display='Elephant', build=elephant, size=(430, 290), stride=170, gait=0,
                     anim=(26, 7, 1.5, 6, 5, 0, 1), surface=(0, 1, .25, .18, .9),
                     # Neutral (owner, November 1): never starts a fight; struck, it defends itself with its tusks (tuning: 30 every 2 s).
                     behave=(False, 70, 380, 45, 1500, 0, 0, 30, 2.0, 120, 'tusk', 1500), yield_=(20, 30), live=('inland', 0, 0)),
    'Spider': dict(display='Cave Spider', build=spider, size=(180, 120), stride=60, gait=3,
                   anim=(26, 22, 1.2, 0, 0, 0, 1), surface=(0, 1, .6, .3, .75),
                   behave=(True, 130, 430, 200, 450, 0, 800, 18, 1.2, 90, 'bite', 90), yield_=(2, 5), live=('cave', 0, 0)),
    'SquirrelMonkey': dict(display='Squirrel Monkey', build=squirrel_monkey, size=(64, 44), stride=30, gait=0,
                           anim=(7, 4, .8, 4, 1, 0, 1), surface=(0, 1, .35, .12, .85),
                           behave=(False, 90, 480, 220, 900, 0, 0, 0, 1, 0, '', 35), yield_=(2, 5), live=('trees', 3, 3)),
    # November 6: wildlife for every island (placed by place_animals.py from wildlife_distribution.py). All tuning.
    'Deer': dict(display='Red Deer', build=deer, size=(175, 170), stride=85, gait=0,
                 anim=(16, 6, 1.4, 2, 2, 0, 1), surface=(0, 1, .4, .12, .85),
                 behave=(False, 80, 800, 180, 1200, 0, 0, 0, 1, 0, '', 90), yield_=(5, 8), live=('world', 0, 0)),
    'Caribou': dict(display='Caribou', build=caribou, size=(190, 190), stride=95, gait=0,
                    anim=(17, 6, 1.3, 2, 2, 0, 1), surface=(0, 1, .5, .12, .9),
                    behave=(False, 75, 700, 150, 1400, 30, 0, 0, 1, 0, '', 140), yield_=(8, 12), live=('world', 0, 0)),
    # A pack hunter: it goes for a survivor within 9 m; a sprinting survivor (750 cm/s) just outruns it.
    'Wolf': dict(display='Grey Wolf', build=wolf, size=(185, 95), stride=70, gait=0,
                 anim=(15, 6, 1.2, 5, 2, 0, 1), surface=(0, 1, .6, .14, .9),
                 behave=(True, 85, 680, 150, 1100, 0, 900, 14, 1.3, 70, 'bite', 120), yield_=(3, 5), live=('world', 0, 0)),
    'Hare': dict(display='Hare', build=hare, size=(55, 46), stride=30, gait=0,
                 anim=(10, 7, 2.0, 0, 1, 0, 1), surface=(0, 1, .5, .1, .9),
                 behave=(False, 60, 650, 260, 600, 0, 0, 0, 1, 0, '', 20), yield_=(1, 2), live=('world', 0, 0)),
    'Snake': dict(display='Snake', build=snake, size=(126, 10), stride=45, gait=2,
                  anim=(0, 0, 0, 0, 0, 7, 45), surface=(.35, 1.3, 0, .15, .45),
                  behave=(True, 35, 180, 90, 500, 0, 300, 10, 2.0, 45, 'bite', 30), yield_=(1, 3), live=('world', 0, 0)),
    'PolarBear': dict(display='Polar Bear', build=polar_bear, size=(300, 140), stride=110, gait=0,
                      anim=(16, 5, 1.2, 3, 2, 0, 1), surface=(0, 1, .6, .08, .9),
                      behave=(True, 85, 560, 90, 1300, 60, 800, 30, 1.6, 110, 'swipe', 450), yield_=(10, 14), live=('world', 0, 0)),
    'Crocodile': dict(display='Crocodile', build=crocodile, size=(440, 60), stride=100, gait=0,
                      anim=(20, 6, .7, 8, 0, 0, 1), surface=(.3, 4.0, 0, .25, .55),
                      behave=(True, 75, 380, 60, 1000, 80, 750, 30, 2.0, 110, 'bite', 450), yield_=(8, 12), live=('world', 0, 0)),
}
# The species added on November 6: add_wildlife_species.py builds only these, so the others keep their generated models.
NEW_SPECIES = ('Deer', 'Caribou', 'Wolf', 'Hare', 'Snake', 'PolarBear', 'Crocodile')


# ---- Material -----------------------------------------------------------------------------------------------

NOISE = """
struct Fur {
  float h(float3 c) { c = frac(c * 0.3183099 + 0.1) * 17.0; return frac(c.x * c.y * c.z * (c.x + c.y + c.z)); }
  float n(float3 q) {
    float3 i = floor(q), f = frac(q); f = f * f * (3 - 2 * f);
    return lerp(lerp(lerp(h(i), h(i + float3(1, 0, 0)), f.x), lerp(h(i + float3(0, 1, 0)), h(i + float3(1, 1, 0)), f.x), f.y),
                lerp(lerp(h(i + float3(0, 0, 1)), h(i + float3(1, 0, 1)), f.x), lerp(h(i + float3(0, 1, 1)), h(i + float3(1, 1, 1)), f.x), f.y), f.z);
  }
};
Fur r;
"""
WALK = """
float part = UV.x, w = UV.y;
float alive = 1 - Dead, moving = Amount * alive;
float3 o = 0;
float lp = -1;
if (Gait < .5) {
  if (abs(part - 1) < .5 || abs(part - 4) < .5) lp = 0;
  if (abs(part - 2) < .5 || abs(part - 3) < .5) lp = 3.14159;
} else if (Gait < 1.5) {
  if (abs(part - 8) < .5) lp = 0;
  if (abs(part - 9) < .5) lp = 3.14159;
}
if (Gait > 2.5) {
  // a spider's alternating-tetrapod crawl (owner, October 29): the two leg groups step in turn, each leg a little behind the one in front
  // (a wave along the body), the foot sweeping forward while lifted and pushing back while planted, with a sideways scuttle
  float side = P.y >= 0 ? 1 : -1;
  float lag = (P.x - 10) * -.012;
  float s = Phase + lag + (abs(part - 1) < .5 ? 0 : 3.14159);
  if (abs(part - 1) < .5 || abs(part - 2) < .5) {
    float step = sin(s), up = max(0, cos(s));
    o.x += step * Swing * w * moving;
    o.y += side * (up - .35) * Swing * .45 * w * moving;
    o.z += up * Lift * w * moving;
  }
  lp = -1;
}
if (lp >= 0) { float s = Phase + lp; o.x += sin(s) * Swing * w * moving; o.z += max(0, cos(s)) * Lift * w * moving; }
bool trunk = part < .5 || abs(part - 5) < .5 || abs(part - 6) < .5;
if (trunk) o.z += (abs(sin(Phase)) - .5) * Bob * moving + sin(T * 2.1) * .35 * alive;
if (abs(part - 5) < .5) o.y += sin(T * 1.7 + w * 2.0 + Phase) * TailSway * w * alive;
if (abs(part - 6) < .5) o.x += sin(Phase * (Gait > .5 ? 2.0 : 1.0)) * Nod * w * moving + sin(T * .9) * Nod * .25 * w * alive;
if (abs(part - 7) < .5) {
  float env = saturate((HeadX - P.x) / 22.0);
  o.y += sin(6.2832 * P.x / Wave + Phase + T * .7 * (1 - Amount)) * SnakeAmp * env * (.3 + .7 * Amount) * alive;
}
return o;
"""
SKIN = NOISE + """
float3 c = V;
float m = r.n(P / 5.0) * .6 + r.n(P / 1.4) * .4;
c *= lerp(1 - Mottle, 1 + Mottle, m);
float3 q = P / max(ScaleSize, .1); float3 f = frac(q) - .5;
float edge = saturate((max(abs(f.x), max(abs(f.y), abs(f.z))) - .36) * 7);
c *= lerp(1, lerp(.8, 1.12, r.h(floor(q))) * (1 - edge * .45), Scales);
c *= lerp(1, lerp(.8, 1.14, r.n(P * float3(.12, 1.7, 1.7))), FurAmt);
return c;
"""


def animal_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Animal_v1')
    world = node(unreal.MaterialExpressionWorldPosition)
    local = node(unreal.MaterialExpressionTransformPosition,
                 transform_source_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,
                 transform_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    assert mel.connect_material_expressions(world, '', local, '')
    params = {}
    for name, default in (('Gait', 0.0), ('Swing', 10.0), ('Lift', 5.0), ('Bob', 1.0), ('TailSway', 0.0), ('Nod', 0.0),
                          ('SnakeAmp', 0.0), ('Wave', 40.0), ('HeadX', 60.0), ('Scales', 0.0), ('ScaleSize', 2.0),
                          ('FurAmt', 0.0), ('Mottle', .15), ('Rough', .7)):
        params[name] = node(unreal.MaterialExpressionScalarParameter, parameter_name=name, default_value=default)
    for index, name in enumerate(('Phase', 'Amount', 'Dead')):
        params[name] = node(unreal.MaterialExpressionScalarParameter, parameter_name=name, default_value=0.0,
                            use_custom_primitive_data=True, primitive_data_index=index)
    params['T'] = node(unreal.MaterialExpressionTime)
    params['UV'] = node(unreal.MaterialExpressionTextureCoordinate)
    params['P'] = local
    params['V'] = node(unreal.MaterialExpressionVertexColor)
    walk_pins = ('P', 'UV', 'T', 'Phase', 'Amount', 'Dead', 'Gait', 'Swing', 'Lift', 'Bob', 'TailSway', 'Nod', 'SnakeAmp', 'Wave', 'HeadX')
    walk = custom(WALK, unreal.CustomMaterialOutputType.CMOT_FLOAT3, walk_pins)
    skin_pins = ('P', 'V', 'Scales', 'ScaleSize', 'FurAmt', 'Mottle')
    skin = custom(SKIN, unreal.CustomMaterialOutputType.CMOT_FLOAT3, skin_pins)
    for target, pins in ((walk, walk_pins), (skin, skin_pins)):
        for pin in pins:
            assert mel.connect_material_expressions(params[pin], '', target, pin), pin
    to_world = node(unreal.MaterialExpressionTransform,
                    transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
                    transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    assert mel.connect_material_expressions(walk, '', to_world, '')
    assert mel.connect_material_property(to_world, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    assert mel.connect_material_property(skin, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(params['Rough'], '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


# ---- Assets -------------------------------------------------------------------------------------------------

def data_asset(name, cls):
    asset = unreal.load_asset(f'{FOLDER}/{name}')
    if asset:
        return asset
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', cls)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, cls, factory)
    assert asset, name
    return asset


def build_definitions(meat, only=None):
    """Every animal's material instance, model and definition; only those named in `only` when given, keeping the shared
    material as it is and the other animals' models (some are generated: apply_generated_animals.py)."""
    mel = unreal.MaterialEditingLibrary
    base = (only and unreal.load_asset(f'{FOLDER}/M_Animal_v1')) or animal_material()
    defs = {}
    for name, a in ANIMALS.items():
        if only and name not in only:
            continue
        mi = unreal.load_asset(f'{FOLDER}/MI_{name}_v1') or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            f'MI_{name}_v1', FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, base)
        swing, lift, bob, sway, nod, snake, wave = a['anim']
        scales, scale_size, fur, mottle, rough = a['surface']
        head = max(v[0] for v in a['build']().verts) if a['gait'] == 2 else 60.0
        for param, value in (('Gait', a['gait']), ('Swing', swing), ('Lift', lift), ('Bob', bob), ('TailSway', sway), ('Nod', nod),
                             ('SnakeAmp', snake), ('Wave', wave), ('HeadX', head), ('Scales', scales), ('ScaleSize', scale_size),
                             ('FurAmt', fur), ('Mottle', mottle), ('Rough', rough)):
            mel.set_material_instance_scalar_parameter_value(mi, param, float(value))
        mel.update_material_instance(mi)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
        mesh = write_static_mesh(a['build'](), f'{FOLDER}/SM_{name}_v1', [mi], 100.0, collision=False, split_angle=70.0)
        definition = data_asset(f'DA_Animal_{name}', unreal.EWAnimalDefinition)
        aggressive, walk, run, turn, roam, wade, notice, damage, interval, reach, attack, health = a['behave']
        for k, v in {'display_name': a['display'], 'mesh': mesh, 'size': unreal.Vector2D(*a['size']),
                     'stride_length': float(a['stride']), 'aggressive': aggressive, 'walk_speed': float(walk),
                     'run_speed': float(run), 'turn_rate': float(turn), 'roam_radius': float(roam), 'wade_depth': float(wade),
                     'notice_range': float(notice), 'attack_damage': float(damage), 'attack_interval': float(interval),
                     'attack_reach': float(reach), 'attack_name': attack, 'max_health': float(health), 'yield': meat,
                     'defends_itself': name in DEFENDERS, 'pushes_trees': name == 'Elephant', 'rideable': name == 'Spider', 'ride_seat_height': 100.0, 'ride_seat_forward': -30.0, 'yield_min': a['yield_'][0], 'yield_max': a['yield_'][1], 'respawn_seconds': 300.0}.items():
            definition.set_editor_property(k, v)
        assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
        defs[name] = definition
    return defs


# ---- Placement ----------------------------------------------------------------------------------------------

def habitat_ok(kind, x, y, z, ground, trees):
    if z is None:
        return False
    if kind == 'beach':
        return SEA + 15 < z < 55
    if kind == 'water':   # the shore, near the sea or the pond
        near_water = any((ground(x + dx, y + dy) or 0) < SEA + 5 for dx, dy in ((500, 0), (-500, 0), (0, 500), (0, -500)))
        near_pond = 900 < math.hypot(x + 1700, y - 1500) < 1300
        return SEA + 15 < z < 90 and (near_water or near_pond)
    if kind == 'trees':
        return 20 < z < 600 and any(math.hypot(x - tx, y - ty) < 350 for tx, ty in trees)
    return 30 < z < 600   # inland


def place(actors, defs, ground, trees):
    rng = random.Random(41)
    taken, placed = [], []
    for name, a in ANIMALS.items():
        kind, *counts = a['live']
        if kind in ('cave', 'plains', 'world'):
            continue      # cave and swamp spiders: add_spiders.py; the Plains boars: build_plains_threat.py
        aggressive = a['behave'][0]
        radius = max(a['size'][1] * .5, a['size'][0] * .3, 15.0)
        for island, count in zip(ISLANDS, counts):
            (x0, x1), (y0, y1) = ISLANDS[island]
            n, tries = 0, 0
            while n < count and tries < 20000:
                tries += 1
                x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
                z = ground(x, y)
                if not habitat_ok(kind, x, y, z, ground, trees):
                    continue
                if min(math.hypot(x - px, y - py) for px, py in (SPAWN, DOCK)) < (2600 if aggressive else 700):
                    continue
                if any(math.hypot(x - px, y - py) < 400 for px, py in taken):
                    continue
                animal = actors.spawn_actor_from_class(unreal.EWAnimal, unreal.Vector(x, y, z + radius),
                                                       unreal.Rotator(0, 0, rng.uniform(-180, 180)))
                n += 1
                animal.set_actor_label(f'{a["display"]} {len([p for p in placed if p[0] == name]) + 1}')
                animal.set_folder_path(LEVEL_FOLDER)
                animal.set_editor_property('definition', defs[name])
                animal.set_editor_property('surface_z', SEA)
                taken.append((x, y))
                placed.append((name, island, round(x), round(y), round(z)))
    return placed


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    meat = unreal.load_asset(RAW_MEAT)
    assert meat, 'Run build_fish.py first (it makes Raw Meat).'
    defs = build_definitions(meat)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWAnimal):
            actors.destroy_actor(actor)
    trees = [(t.get_actor_location().x, t.get_actor_location().y) for t in actors.get_all_level_actors()
             if str(t.get_folder_path()) == FLORA_FOLDER and t.get_actor_label().startswith('Maravai')]
    placed = place(actors, defs, Ground(), trees)
    assert world_map.save_map()
    Path(unreal.Paths.project_saved_dir(), 'AnimalsResult.json').write_text(json.dumps({
        'success': True, 'animals': len(placed),
        'by_kind': {n: sum(1 for p in placed if p[0] == n) for n in ANIMALS},
        'by_island': {i: sum(1 for p in placed if p[1] == i) for i in ISLANDS}, 'placed': placed}, indent=2))
    unreal.log(f'Animals: {len(placed)}')


if __name__ == '__main__':
    main()
