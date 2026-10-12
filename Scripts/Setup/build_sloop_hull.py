"""Build the sloop's hull mesh in Unreal from the owner's concept art (Art/Concepts/Boats/2026-10-11/Sloop-*).
Safe to run again. Run in the editor, outside Play, with no unsaved maps:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

A bare hull in weathered oak: planked sides with seams and two wales, a tarred bottom, a deep curved bow with a
tall stem post, a modest rounded stern, low bulwarks with a rail and posts, and one gunport each side. A flat deck
has a cargo hatch with a coaming and stairs down into a cramped hold of ribs, floorboards, deck beams and a post.
Boarding ladders on both sides, a capstan near the bow, the mast and bowsprit are part of the hull, and the
standing rigging (shrouds and forestay) is a separate mesh drawn without collision. Sails, the helm and cannons
are fittings, built by build_ship_fittings.py, which reads the rig's positions from here.

Coordinates are the ship's own, in cm: X forward to the bow, Y to starboard, Z up, the waterline at Z 0. The hold
floor sits above the waves so the sea neither shows nor counts as swimmable inside. All sizes are tuning.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402

MESH = '/Game/Elitewake/World/Ships/SM_SloopHull_v2'
RIGGING = '/Game/Elitewake/World/Ships/SM_SloopRigging_v1'
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
# Rig: one mast with a gaff mainsail and a jib on the forestay out to the bowsprit.
MAST_X, MAST_TOP = 90.0, 1300.0
BOOM_Z = 460.0                       # boom height, above the heads of crew on deck
STAY_TOP = (MAST_X + 8, 0.0, MAST_TOP - 30)
STAY_BOW = (775.0, 0.0, 468.0)       # bowsprit end


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


def along_hull(i, j, p):
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
    across = lambda i, j, p: (p[2] / UV_TILE, p[1] / UV_TILE)  # transom planks run athwartships
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
    # Stairs down from the hatch; the mast stands in the hold forward of them.
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


def mast_and_bowsprit(b):
    """The mast steps on the hold floor and rises through the deck; the bowsprit reaches out over the bow."""
    b.tube([(MAST_X, 0.0, FLOOR_Z), (MAST_X, 0.0, DECK_Z), (MAST_X, 0.0, MAST_TOP)],
           lambda k: (15.0, 15.0, 10.0)[k], sides=14)
    b.box((MAST_X, 0.0, MAST_TOP + 6), (26, 26, 12))                       # masthead cap
    b.tube([(MAST_X, 0.0, DECK_Z), (MAST_X, 0.0, DECK_Z + 12)], 19.0, sides=14, iron=1.0)  # mast coat
    b.tube([(470.0, 0.0, sheer(470) - 25), STAY_BOW[:2] + (STAY_BOW[2] + 2,)], lambda k: (11.0, 7.0)[k], sides=12)


def rigging():
    """Standing rigging: a forestay to the bowsprit and two shrouds a side, as tarred rope."""
    r = Builder()
    r.tube([STAY_TOP, STAY_BOW], 1.8, sides=6)
    for side in (1, -1):
        for x in (MAST_X - 30, MAST_X + 30):
            r.tube([(MAST_X, side * 11, MAST_TOP - 90), (x, side * (half_beam(x) + 1), sheer(x) + 3)], 1.6, sides=6)
    for k in range(len(r.colours)):
        r.colours[k] = (1.0, 0.0, 0.5)
    return r


def capstan(b):
    x, y = CAPSTAN
    b.cylinder((x, y, DECK_Z), 26, 6)
    b.cylinder((x, y, DECK_Z + 6), 19, 52)
    b.cylinder((x, y, DECK_Z + 58), 27, 9)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        b.box((x + 19 * math.cos(a), y + 19 * math.sin(a), DECK_Z + 32), (6, 6, 40), iron=1.0)


# ---- Assets ------------------------------------------------------------------------------------------------

def mount(mount_id, kind, location, yaw=0.0, sail=unreal.EWSailSize.NONE):
    m = unreal.EWShipMount()
    m.set_editor_property('mount_id', mount_id)
    m.set_editor_property('type', kind)
    m.set_editor_property('sail_size', sail)
    m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(*location), rotation=unreal.Rotator(0, 0, yaw)))
    return m


def update_definition(hull, rig):
    definition = unreal.load_asset(DEFINITION)
    assert definition, DEFINITION
    deck_y = lambda x: inner_y(x, DECK_Z)
    t = unreal.EWShipMountType
    values = {
        'hull_mesh': hull,
        'rigging_mesh': rig,
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
    mast_and_bowsprit(b)
    timber = make_timber_material()
    hull = write_static_mesh(b, MESH, [timber], UV_TILE)
    rig = write_static_mesh(rigging(), RIGGING, [timber], UV_TILE, collision=False)
    report = {'vertices': len(b.verts), 'triangles': len(b.tris), 'definition': update_definition(hull, rig)}
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


if __name__ == '__main__':
    main()
