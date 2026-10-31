"""Build the raft and the dinghy from the owner's art (Art/Concepts/Boats/2026-10-11/Raft-*, Dinghy-*), their
definitions and built-in steering, and moor both by the coastal dock. Safe to run again.
Run in the editor after build_ship_fittings.py, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

- Raft, about 5 m by 2.5 m: a bed of lashed logs under cross beams and a plank deck, rail logs along the sides,
  rope-wrapped corner posts, a lashed crate for its hold and a stone anchor on a rope coil. It is paddled (owner,
  October 12) and has one Small sail hardpoint forward (owner, October 18: the raft has one functional small-sail
  hardpoint); a fitted sail brings its own short mast and sets on a boom high over the paddler. Its two paddles rest in lashings on the side rails, blades in the water, and
  are part of the raft; taking them up is taking its helm, and forward and back set the stroke.
- Dinghy, about 3.5 m by 1.4 m: a small plank boat with a pointed bow and a rounded transom, ribs, floor boards,
  two thwarts, a short mast, a sea chest for its hold and a grapnel. Steered by a rudder and tiller.

The dinghy carries one Small sail, which sets on its own mast and boom (the mount's look), not as the sloop's jib.
Coordinates are each boat's own, in cm, with the waterline at Z 0; floors stay above the water. Sizes are tuning.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ship_fittings as fittings  # noqa: E402
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402
from ship_hull import plank_tone  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
SHIPS = '/Game/Elitewake/Ships'
ITEMS = '/Game/Elitewake/Items/Ships'
MAP = '/Game/Elitewake/Maps/Test/Lvl_ShipsTest'  # ships and sea life live in the test map (owner, October 14)
UV_TILE = 100.0
T = unreal.EWShipMountType


def rope_ring(b, centre, axis, radius, thickness=2.2, sides=14):
    """A rope loop around a timber: `axis` 0 for a timber along X, 1 along Y, 2 upright."""
    pts = []
    for k in range(sides + 1):
        a = 2 * math.pi * k / sides
        u, v = radius * math.cos(a), radius * math.sin(a)
        p = list(centre)
        p[(axis + 1) % 3] += u
        p[(axis + 2) % 3] += v
        pts.append(tuple(p))
    b.tube(pts, thickness, sides=6, capped=False)


def rope_coil(b, centre, radius, turns=4):
    for k in range(turns):
        rope_ring(b, (centre[0], centre[1], centre[2] + 3 * k), 2, radius - k * 1.5, 2.4)


def bermuda_sail(mast_x, boom_z, head_z, boom_len, furled):
    """A triangular sail on its own mast and boom, in the mount's look frame: origin on the mast at the boom."""
    b = Builder()
    b.tube([(-4, 0, 0), (-boom_len, 0, 0)], lambda k: (5.0, 4.0)[k], sides=8)
    b.box((-5, 0, 0), (10, 18, 10))
    if furled:
        fittings.bundle(b, [(-8 - (boom_len - 20) * k / 12, 0, 8) for k in range(13)], 8.0)
    else:
        luff = head_z - boom_z
        art = fittings.JIB_ART
        fittings.cloth(b, ((-6, 0, 4), (-boom_len + 6, 0, 4), (-6, 0, luff), (-6, 0, luff)),
                       (art['tack'], art['clew'], art['head'], art['head']), belly=18)
    return b


# ---- Raft --------------------------------------------------------------------------------------------------

RAFT_HALF = (250.0, 125.0)
RAFT_DECK = 32.0
RAFT_SPEED = 3 * 51.4444          # cm/s: the raft's base speed, 3 knots (owner, October 18), at a hard stroke or under sail


def raft_hull():
    b = Builder()
    half_x, half_y = RAFT_HALF
    # Bed of logs, half awash.
    for k in range(8):
        y = -105 + 30 * k
        r = 15 + (k % 3) * 0.8
        trim = 6 * math.sin(k * 2.3)
        b.tube([(-half_x - trim, y, -2), (half_x + trim, y, -2)], r, sides=12)
    # Cross beams, deck planks along the raft, each with its own tone.
    for x in (-190.0, 0.0, 190.0):
        b.box((x, 0, 20), (22, 2 * half_y + 10, 14))
    for k in range(10):
        y = -112 + 24.8 * k
        length = 2 * half_x - 30 + 14 * math.sin(k * 1.7)
        b.box((4 * math.sin(k), y, 29.5), (length, 23, 5))
    # Rail logs: two along each side, one across each end, lashed at intervals.
    for side in (1, -1):
        y = side * (half_y - 7)
        b.tube([(-half_x + 8, y, RAFT_DECK + 12), (half_x - 8, y, RAFT_DECK + 12)], 12.0, sides=12)
        b.tube([(-half_x + 20, y, RAFT_DECK + 33), (half_x - 20, y, RAFT_DECK + 33)], 9.5, sides=12)
        for x in (-180.0, -60.0, 60.0, 180.0):
            rope_ring(b, (x, y, RAFT_DECK + 20), 0, 22.0)
    for end in (1, -1):
        b.tube([(end * (half_x - 7), -half_y + 20, RAFT_DECK + 12), (end * (half_x - 7), half_y - 20, RAFT_DECK + 12)], 11.0, sides=12)
    # Corner posts wrapped in rope.
    for sx in (1, -1):
        for sy in (1, -1):
            c = (sx * (half_x - 14), sy * (half_y - 14))
            b.cylinder((c[0], c[1], RAFT_DECK - 5), 13, 70, sides=12)
            for z in (RAFT_DECK + 18, RAFT_DECK + 45):
                rope_ring(b, (c[0], c[1], z), 2, 15.5)
    # The crate that is the raft's hold, and a stone anchor on a coil of rope.
    crate = (120.0, 60.0)
    b.box((crate[0], crate[1], RAFT_DECK + 22), (70, 55, 44))
    for dx in (-30, 0, 30):
        b.box((crate[0] + dx, crate[1], RAFT_DECK + 22), (5, 57, 46))
    rope_coil(b, (215.0, -85.0, RAFT_DECK + 2), 18.0)
    b.cylinder((195.0, -60.0, RAFT_DECK), 13, 16, sides=7)
    return b


def paddles(mount):
    """In the helm mount's frame: a paddle resting in a rope lashing on each side rail, its blade in the water
    beside the raft, its grip inboard where the paddler kneels."""
    b = Builder()
    loc = lambda p: (p[0] - mount[0], p[1] - mount[1], p[2] - mount[2])
    half_y = RAFT_HALF[1]
    for side in (1, -1):
        grip = (-95.0, side * 55.0, RAFT_DECK + 48)
        rest = (-120.0, side * (half_y - 7), RAFT_DECK + 46)
        throat = (-150.0, side * (half_y + 60), -4.0)
        b.tube([loc(grip), loc(rest), loc(throat)], lambda k: (2.6, 2.8, 3.0)[k], sides=8)
        b.tube([loc((grip[0] + 6, grip[1], grip[2])), loc((grip[0] - 6, grip[1], grip[2]))], 3.6, sides=8)  # T-grip
        # The blade, flattened and broad, continuing the shaft's line down into the water.
        dx, dy, dz = (throat[i] - rest[i] for i in range(3))
        n = (dx * dx + dy * dy + dz * dz) ** 0.5
        tip = (throat[0] + dx / n * 55, throat[1] + dy / n * 55, throat[2] + dz / n * 55)
        b.sweep([loc(throat), loc(tip)], 18.0, 2.5, side=(1, 0, 0))
        rope_ring(b, rest, 0, 6.0, 1.6)
    return b


# ---- Dinghy ------------------------------------------------------------------------------------------------

D_STERN, D_BOW, D_BEAM = -175.0, 175.0, 70.0
D_FLOOR = 8.0
D_SHELL = 2.5
D_MAST = (40.0, 340.0)
D_BOOM_Z = 205.0


def d_half_beam(x):
    if x >= -20:
        return D_BEAM * max(0.0, 1 - ((x + 20) / (D_BOW + 20)) ** 2.2) ** 0.5
    return D_BEAM * (1 - 0.25 * ((-20 - x) / (-20 - D_STERN)) ** 2)


def d_sheer(x):
    if x > 40:
        return 55 + 25 * ((x - 40) / (D_BOW - 40)) ** 2
    if x < -60:
        return 55 + 10 * ((-60 - x) / (-60 - D_STERN)) ** 2
    return 55.0


def d_keel(x):
    if x > 60:
        return -28 + (d_sheer(x) - 6 + 28) * ((x - 60) / (D_BOW - 60)) ** 1.8
    if x < -140:
        return -28 + 15 * (-140 - x) / (-140 - D_STERN)
    return -28.0


def d_section(x, theta):
    n = 2.6 - 1.0 * max(0.0, x - 60) / (D_BOW - 60)
    b, sh, kl = d_half_beam(x), d_sheer(x), d_keel(x)
    s, c = max(math.sin(theta), 0.0), max(math.cos(theta), 0.0)
    return b * s ** (2 / n), sh - (sh - kl) * c ** (2 / n)


def d_normal(x, theta):
    y0, z0 = d_section(x, max(theta - 1e-3, 0.0))
    y1, z1 = d_section(x, min(theta + 1e-3, math.pi / 2))
    ny, nz = z1 - z0, -(y1 - y0)
    length = math.hypot(ny, nz) or 1.0
    return ny / length, nz / length


def d_theta_at(x, z):
    lo, hi = 0.0, math.pi / 2
    for _ in range(36):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if d_section(x, mid)[1] < z else (lo, mid)
    return (lo + hi) / 2


def d_inner_y(x, z):
    t = d_theta_at(x, z)
    return max(d_section(x, t)[0] - D_SHELL * max(d_normal(x, t)[0], 0.3), 0.0)


D_STATIONS = [D_STERN + 10 * i for i in range(int((D_BOW - D_STERN) / 10) + 1)]


def dinghy_hull():
    b = Builder()
    strakes = 6
    span = (math.pi / 2) / strakes
    along = lambda i, j, p: (p[2] / UV_TILE, p[0] / UV_TILE)
    tarred = lambda p: min(1.0, max(0.0, (10 - p[2]) / 25))
    # Lapped planking: each strake's lower edge stands proud of the one below.
    params = []
    for k in range(strakes):
        for f, lap in ((0.0, 1.2), (0.5, 0.6), (0.98, 0.0)):
            params.append((k * span + f * span, lap, k))
    for side in (1, -1):
        rows = []
        for x in D_STATIONS:
            row = []
            for theta, lap, _ in params:
                y, z = d_section(x, theta)
                ny, nz = d_normal(x, theta)
                row.append((x, side * (y + ny * lap), z + nz * lap))
            rows.append(row)
        b.grid(rows, lambda i, j, side=side: (0.3 if D_STATIONS[i] > 100 else 0.0, side * d_normal(D_STATIONS[i], params[j][0])[0],
                                             d_normal(D_STATIONS[i], params[j][0])[1]),
               tar_of=tarred, tone_of=lambda i, j, side=side: plank_tone(params[j][2], side), uv_of=along)
        inner = []
        for x in D_STATIONS:
            t0 = d_theta_at(x, D_FLOOR - 3) if d_keel(x) < D_FLOOR - 3 else 0.0
            row = []
            for k in range(13):
                theta = t0 + (math.pi / 2 - t0) * k / 12
                y, z = d_section(x, theta)
                ny, nz = d_normal(x, theta)
                row.append((x, side * max(y - ny * D_SHELL, 0.0), z - nz * D_SHELL))
            inner.append(row)
        b.grid(inner, lambda i, j, side=side: (0.0, -side, 0.2), uv_of=along)
    # Rounded transom, outside and in.
    tparams = [k / 16 * math.pi / 2 for k in range(17)]
    across = lambda i, j, p: (p[2] / UV_TILE, p[1] / UV_TILE)
    outer = [[(D_STERN, s * d_section(D_STERN, t)[0], d_section(D_STERN, t)[1]) for t in tparams] for s in (-1, 1)]
    b.grid(list(map(list, zip(*outer))), lambda i, j: (-1, 0, 0), tar_of=tarred, uv_of=across)
    t0 = d_theta_at(D_STERN, D_FLOOR - 3)
    ip = [t0 + (math.pi / 2 - t0) * k / 12 for k in range(13)]
    inner = [[(D_STERN + D_SHELL, s * d_inner_y(D_STERN, d_section(D_STERN, t)[1]), d_section(D_STERN, t)[1]) for t in ip] for s in (-1, 1)]
    b.grid(list(map(list, zip(*inner))), lambda i, j: (1, 0, 0), uv_of=across)
    # Gunwale with iron studs, stem post and keel.
    for side in (1, -1):
        path = [(x, side * (d_half_beam(x) - 1), d_sheer(x) + 2.5) for x in D_STATIONS if d_half_beam(x) > 1]
        path.append((D_BOW - 1, 0.0, d_sheer(D_BOW) + 2.5))
        b.sweep(path, 7.0, 5.0, side=(0, 1, 0))
        for x in range(-160, 150, 25):
            b.box((x, side * (d_half_beam(x) + 2.5), d_sheer(x) - 4), (2.5, 2.5, 2.5), iron=1.0)
    b.sweep([(D_STERN + 2, y, d_sheer(D_STERN) + 2.5) for y in (-d_half_beam(D_STERN), d_half_beam(D_STERN))], 7.0, 5.0, side=(1, 0, 0))
    b.sweep([(x, 0.0, d_keel(x) - 3) for x in D_STATIONS if x <= 60], 7.0, 6.0, tar=1.0)
    stem = [(x, 0.0, d_keel(x) - 2) for x in [60 + 10 * k for k in range(12)] if x <= D_BOW]
    stem += [(D_BOW + 4, 0.0, d_sheer(D_BOW) + 10)]
    b.sweep(stem, 8.0, 9.0)
    # Floor, stringers and ribs.
    ys = [-70 + 14 * k for k in range(11)]
    stations = [x for x in D_STATIONS if d_inner_y(x, D_FLOOR) > 8]
    b.grid([[(x, max(-d_inner_y(x, D_FLOOR), min(d_inner_y(x, D_FLOOR), y)), D_FLOOR) for y in ys] for x in stations], lambda i, j: (0, 0, 1))
    for y in (-28.0, 0.0, 28.0):
        b.box((-10, y, D_FLOOR + 1), (260, 13, 2))
    for x in range(-160, 140, 22):
        x = float(x)
        for side in (1, -1):
            path = [(x, side * (d_inner_y(x, z) - 1.5), z) for z in [D_FLOOR + (d_sheer(x) - 3 - D_FLOOR) * k / 6 for k in range(7)]]
            b.sweep(path, 4.0, 3.0, side=(1, 0, 0))
    # Thwarts, the sea chest under the aft one, mast and grapnel.
    for x, z in ((-95.0, 36.0), (40.0, 36.0), (135.0, 42.0)):
        half = d_inner_y(x, z)
        b.box((x, 0, z), (22, 2 * half, 4))
    b.box((-95.0, 0, D_FLOOR + 12), (48, 38, 24))
    mx, mtop = D_MAST
    b.tube([(mx, 0, D_FLOOR), (mx, 0, mtop)], lambda k: (5.5, 4.0)[k], sides=10)
    rope_coil(b, (140.0, 0.0, D_FLOOR + 1), 11.0, 3)
    for a in range(4):
        ang = a * math.pi / 2
        b.tube([(128.0, 0.0, D_FLOOR + 4), (128 + 10 * math.cos(ang), 10 * math.sin(ang), D_FLOOR + 10)], 1.4, sides=6, iron=1.0)
    return b


TILLER_TURN = -35.0   # degrees the rudder swings with the helm hard to starboard (tuning)


def rudder_post():
    """Where the dinghy's rudder hangs and swings: on the transom's centre line."""
    return (D_STERN - 6, 0.0, 0.0)


def gudgeons(mount):
    """In the helm mount's frame: the iron pintle fittings on the transom that the rudder hangs from."""
    b = Builder()
    post = rudder_post()
    for z in (5.0, 35.0):
        b.box((post[0] - mount[0] + 2, -mount[1], z - mount[2]), (6, 8, 4), iron=1.0)
    return b


def tiller():
    """Around the rudder post: the rudder blade and the tiller reaching forward, which swing together."""
    b = Builder()
    post = rudder_post()
    loc = lambda p: (p[0] - post[0], p[1] - post[1], p[2] - post[2])
    b.box(loc((D_STERN - 6, 0, 10)), (4, 30, 80))
    b.tube([loc((D_STERN - 6, 0, d_sheer(D_STERN) + 6)), loc((D_STERN + 60, 0, d_sheer(D_STERN) + 4))], lambda k: (2.6, 2.0)[k], sides=8)
    return b


# ---- Assets ------------------------------------------------------------------------------------------------

def data_asset(folder, name, cls):
    asset = unreal.load_asset(f'{folder}/{name}')
    if asset:
        return asset
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', cls)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    assert asset, name
    return asset


def built_in_helm(name, item_id, display, mesh, turning=None):
    """`turning` is (mesh, pivot location in the helm's frame, rotator at full starboard rudder), if part of it
    turns with the rudder."""
    item = data_asset(ITEMS, name, unreal.EWItemDefinition)
    turning_mesh, pivot, turn = turning or (None, (0, 0, 0), unreal.Rotator())
    for k, v in {'item_id': item_id, 'display_name': display, 'category': unreal.EWItemCategory.MISCELLANEOUS,
                 'max_stack_size': 1, 'unit_weight': 0.0, 'fitting_mount_type': T.HELM, 'fitting_mesh': mesh,
                 'fitting_turning_mesh': turning_mesh, 'fitting_turning_pivot': unreal.Transform(location=unreal.Vector(*pivot)),
                 'fitting_turn_at_full': turn,
                 'description': 'Part of the hull: steers the boat and is never removed.'}.items():
        item.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    return item


def mount(mount_id, kind, location, sail=unreal.EWSailSize.NONE, look=None):
    m = unreal.EWShipMount()
    m.set_editor_property('mount_id', mount_id)
    m.set_editor_property('type', kind)
    m.set_editor_property('sail_size', sail)
    m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(*location)))
    if look:
        mesh, furled, offset = look
        m.set_editor_property('fitted_mesh', mesh)
        m.set_editor_property('fitted_furled_mesh', furled)
        m.set_editor_property('fitted_mesh_transform', unreal.Transform(location=unreal.Vector(*offset)))
    return m


def definition(name, values, helm_item):
    d = data_asset(SHIPS, name, unreal.EWShipDefinition)
    for k, v in values.items():
        if v is None:
            # Clearing a mesh only sticks with a change notice (the raft once had rigging, from when it had a mast).
            d.modify()
            d.set_editor_property(k, None, unreal.PropertyAccessChangeNotifyMode.ALWAYS)
        else:
            d.set_editor_property(k, v)
    built = unreal.EWInstalledFitting()
    built.set_editor_property('mount_id', 'Helm')
    built.set_editor_property('item', helm_item)
    d.set_editor_property('built_in_fittings', [built])
    assert unreal.EditorAssetLibrary.save_loaded_asset(d, False)
    return d


def rename_if_present(folder, old, new):
    """Rename one of this script's own assets, so references follow and nothing is left behind."""
    library = unreal.EditorAssetLibrary
    if library.does_asset_exist(f'{folder}/{old}') and not library.does_asset_exist(f'{folder}/{new}'):
        assert library.rename_asset(f'{folder}/{old}', f'{folder}/{new}'), old


def raft_mast(height):
    """A raft sail assembly's short mast (owner, October 18: the mast belongs to the removable sail), from a socket on the deck."""
    b = Builder()
    b.tube([(0, 0, -30), (0, 0, height)], lambda k: (7.0, 5.0)[k], sides=10)
    b.box((0, 0, -24), (26, 26, 12))
    return b


def build_raft(timber, sail_mi):
    hull = write_static_mesh(raft_hull(), f'{FOLDER}/SM_RaftHull_v1', [timber], UV_TILE)
    helm_at = (-140.0, 0.0, RAFT_DECK + 50)
    # The raft was first steered by an oar; its paddles take that item's and mesh's place.
    rename_if_present(FOLDER, 'SM_RaftSteeringOar_v1', 'SM_RaftPaddles_v1')
    rename_if_present(ITEMS, 'DA_RaftSteeringOar', 'DA_RaftPaddles')
    paddle_mesh = write_static_mesh(paddles(helm_at), f'{FOLDER}/SM_RaftPaddles_v1', [timber], UV_TILE, collision=False)
    helm = built_in_helm('DA_RaftPaddles', 'Ship.RaftPaddles', 'Paddles', paddle_mesh)
    hx, hy = RAFT_HALF
    return definition('DA_Ship_Raft', {
        'ship_id': 'Raft', 'display_name': 'Raft', 'hull_mesh': hull, 'rigging_mesh': None, 'paddled': True,
        'hull_extent': unreal.Vector(hx + 5, hy + 5, 40), 'hull_draft': 17.0,
        'deck_height': RAFT_DECK, 'hold_floor_height': RAFT_DECK,
        'anchor_point': unreal.Vector(205, -75, RAFT_DECK + 30), 'cargo_hatch_point': unreal.Vector(120, 60, RAFT_DECK + 30),
        'boarding_points': [unreal.Vector(0, s * (hy + 30), -10) for s in (-1, 1)],
        'hull_health': 200.0, 'cargo_slots': 8, 'weight_capacity': 400.0, 'top_speed': RAFT_SPEED, 'turn_rate': 25.0, 'crew_capacity': 2,
        'mounts': [mount('Helm', T.HELM, helm_at), raft_sail_mount(timber, sail_mi)],
    }, helm)


def raft_sail_mount(timber, sail_mi):
    """The raft's one Small sail hardpoint, forward of the paddler: a triangular sail on its own mast and a boom high over his head."""
    sail_at = (70.0, 0.0, RAFT_DECK + 30)
    boom_z, head_z = RAFT_DECK + 190, RAFT_DECK + 420
    sail_args = (0.0, boom_z, head_z, 150)
    sail = write_static_mesh(bermuda_sail(*sail_args, False), f'{FOLDER}/SM_RaftSail_v1', [timber, sail_mi], UV_TILE, collision=False)
    furled = write_static_mesh(bermuda_sail(*sail_args, True), f'{FOLDER}/SM_RaftSailFurled_v1', [timber, sail_mi], UV_TILE, collision=False)
    mast = write_static_mesh(raft_mast(head_z - sail_at[2] + 10), f'{FOLDER}/SM_RaftMast_v1', [timber], UV_TILE, collision=False)
    m = mount('Sail', T.SAIL, sail_at, unreal.EWSailSize.SMALL, (sail, furled, (0, 0, boom_z - sail_at[2])))
    m.set_editor_property('mast_mesh', mast)
    return m


def build_dinghy(timber, sail_mi):
    hull = write_static_mesh(dinghy_hull(), f'{FOLDER}/SM_DinghyHull_v1', [timber], UV_TILE)
    helm_at = (-110.0, 0.0, D_FLOOR + 40)
    fittings = write_static_mesh(gudgeons(helm_at), f'{FOLDER}/SM_DinghyRudderFittings_v1', [timber], UV_TILE, collision=False)
    rudder = write_static_mesh(tiller(), f'{FOLDER}/SM_DinghyTiller_v1', [timber], UV_TILE, collision=False)
    post = rudder_post()
    sail_at = (D_MAST[0], 0.0, D_FLOOR + 60)
    sail_args = (D_MAST[0], D_BOOM_Z, D_MAST[1] - 10, 170)
    sail = write_static_mesh(bermuda_sail(*sail_args, False), f'{FOLDER}/SM_DinghySail_v1', [timber, sail_mi], UV_TILE, collision=False)
    furled = write_static_mesh(bermuda_sail(*sail_args, True), f'{FOLDER}/SM_DinghySailFurled_v1', [timber, sail_mi], UV_TILE, collision=False)
    helm = built_in_helm('DA_DinghyTiller', 'Ship.DinghyTiller', 'Tiller', fittings,
                         turning=(rudder, (post[0] - helm_at[0], post[1] - helm_at[1], post[2] - helm_at[2]),
                                  unreal.Rotator(roll=0, pitch=0, yaw=TILLER_TURN)))
    return definition('DA_Ship_Dinghy', {
        'ship_id': 'Dinghy', 'display_name': 'Dinghy', 'hull_mesh': hull,
        'hull_extent': unreal.Vector(D_BOW + 5, D_BEAM + 5, 35), 'hull_draft': 28.0,
        'deck_height': D_FLOOR, 'hold_floor_height': D_FLOOR,
        'anchor_point': unreal.Vector(135, 0, D_FLOOR + 25), 'cargo_hatch_point': unreal.Vector(-95, 0, D_FLOOR + 22),
        'boarding_points': [unreal.Vector(-20, s * (D_BEAM + 35), -10) for s in (-1, 1)],
        'hull_health': 300.0, 'cargo_slots': 6, 'weight_capacity': 250.0, 'top_speed': 5 * 51.4444, 'turn_rate': 45.0, 'crew_capacity': 2,
        'cannot_sink': True,   # design reference: ordinary damage cannot sink the dinghy
        'mounts': [mount('Helm', T.HELM, helm_at),
                   mount('Sail', T.SAIL, sail_at, unreal.EWSailSize.SMALL, (sail, furled, (0, 0, D_BOOM_Z - sail_at[2])))],
    }, helm)


def moor(definitions):
    """Raft and dinghy wait side by side on the beach side of the dock, bows out to sea so neither runs into the
    other, clear of the swimming checks' lane along Y 0."""
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    # Side by side off the dock with room between them (the dinghy by the dock at Y 650, the raft 3 m deep out).
    for label, d, where in (('Raft', definitions[0], (5300, 60, -65)), ('Dinghy', definitions[1], (5300, 480, -65))):
        ship = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWShip) and a.get_editor_property('definition') == d), None)
        if not ship:
            ship = actors.spawn_actor_from_class(unreal.EWShip, unreal.Vector(*where))
            ship.set_actor_label(label)
        ship.set_editor_property('definition', d)
        ship.set_actor_location(unreal.Vector(*where), False, False)
    assert level.save_current_level()


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = make_timber_material()
    sail_mi = unreal.load_asset(f'{FOLDER}/MI_SailSmall_v1')
    assert sail_mi, 'Run build_ship_fittings.py first'
    definitions = (build_raft(timber, sail_mi), build_dinghy(timber, sail_mi))
    moor(definitions)
    Path(unreal.Paths.project_saved_dir(), 'SmallCraftResult.json').write_text(json.dumps({'success': True}))
    unreal.log('Raft and dinghy built')


if __name__ == '__main__':
    main()
