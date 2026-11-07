"""A planked, double-ended wooden hull drawn from a handful of lines, shared by the ship hull scripts.

Coordinates are the ship's own, in cm: X forward to the bow, Y to starboard, Z up, the waterline at Z 0.
`Hull` holds the lines (beam, sheer, keel and fullness along the length) and draws the parts every hull has:
planking with seams and wales, the inner skin, rail, keel and end posts, decks, ribs, beams, gunports, studs,
ladders, a capstan, masts and standing rigging. Each ship script sets the lines and places the parts.
"""
import math
from dataclasses import dataclass, field
from typing import Optional
from ship_geometry import WINDOW_GLASS



def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def plank_tone(*seed):
    """A steady pseudo-random 0..1 per plank, so neighbouring planks differ a little in colour."""
    v = math.sin(sum((k + 1) * 12.9898 * s for k, s in enumerate(seed)) + 0.5) * 43758.5453
    return v - math.floor(v)


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


@dataclass
class Hull:
    stern_x: float
    bow_x: float
    beam: float                 # half-beam at the widest
    keel_z: float
    deck_z: float               # main deck top
    floor_z: float              # lowest floor inside, above the swell
    sheer_mid: float            # top of the bulwark amidships
    sheer_rise: float           # how far the sheer sweeps up at the ends
    sheer_flat: float = 60.0    # half-length of the level sheer amidships
    keel_flat: float = 120.0    # half-length of the flat keel
    keel_power: float = 1.7
    beam_power: float = 2.4     # higher keeps the beam further toward the ends
    stern_power: Optional[float] = None   # the same aft of amidships, if the stern is fuller than the bow
    stern_keel_power: Optional[float] = None   # keel_power aft: higher keeps the bottom low further aft
    stern_full_len: Optional[float] = None     # full_len aft: full sections further aft
    full_mid: float = 2.8       # section superellipse exponent amidships ...
    full_end: float = 1.6       # ... and at the ends
    full_len: float = 200.0     # half-length of full sections
    deck_thick: float = 8.0
    shell: float = 9.0          # planking thickness
    strakes: int = 11
    wales: tuple = (7, 9)
    tar_line: float = 75.0      # tar reaches this high above the waterline
    uv_tile: float = 120.0
    station_step: float = 20.0
    # (centre x, width, bottom z, top z[, kind]): kind 'square' (default, framed), 'round' (a framed circular port,
    # owner, October 17: the brigantine's) or 'gap' (an opening for a railing module, no frame).
    gunports: list = field(default_factory=list)
    quarterdeck: Optional[tuple] = None           # (front x, rise): a raised aft deck
    forecastle: Optional[tuple] = None            # (back x, rise): a raised deck at the bow

    # ---- Lines -------------------------------------------------------------------------------------------

    def half_beam(self, x):
        if x < 0 and self.stern_power:
            return self.beam * max(0.0, 1 - (abs(x) / abs(self.stern_x)) ** self.stern_power) ** 0.5
        return self.beam * max(0.0, 1 - (abs(x) / self.bow_x) ** self.beam_power) ** 0.5

    def quarterdeck_lift(self, x):
        """How far the raised decks lift the sheer at x, easing up over 80 cm to full height just inside their edge."""
        lift = 0.0
        # Each raised deck keeps the bulwark's height above it, until the sweep up to the end catches up.
        if self.quarterdeck:
            front, rise = self.quarterdeck
            lift += max(0.0, self.sheer_mid + rise - self.end_sheer(x)) * smoothstep((front + 60 - x) / 80)
        if self.forecastle:
            back, rise = self.forecastle
            lift += max(0.0, self.sheer_mid + rise - self.end_sheer(x)) * smoothstep((x - back + 60) / 80)
        return lift

    def sheer(self, x):
        """Top of the bulwark: low amidships, sweeping up alike to the bow and the stern."""
        flat = self.sheer_flat
        return (self.sheer_mid + self.sheer_rise * max(0.0, (abs(x) - flat) / (self.bow_x - flat)) ** 2
                + self.quarterdeck_lift(x))

    def end_sheer(self, x):
        """The sheer without the raised aft deck, which the keel's sweep follows."""
        flat = self.sheer_flat
        return self.sheer_mid + self.sheer_rise * max(0.0, (abs(x) - flat) / (self.bow_x - flat)) ** 2

    def keel(self, x):
        """Bottom of the hull: flat amidships, sweeping up alike into the stem and the sternpost."""
        ax = abs(x)
        power = self.stern_keel_power if x < 0 and self.stern_keel_power else self.keel_power
        if ax > self.keel_flat:
            return self.keel_z + (self.end_sheer(x) - 12 - self.keel_z) * ((ax - self.keel_flat) / (self.bow_x - self.keel_flat)) ** power
        return self.keel_z

    def fullness(self, x):
        """Superellipse exponent of the sections: full amidships, sharp at both ends."""
        ax = abs(x)
        full_len = self.stern_full_len if x < 0 and self.stern_full_len else self.full_len
        if ax > full_len:
            return self.full_mid - (self.full_mid - self.full_end) * (ax - full_len) / (self.bow_x - full_len)
        return self.full_mid

    def section_point(self, x, theta):
        """Outer hull at station x; theta runs from the keel (0) to the sheer (pi/2). Returns (y, z), starboard."""
        b, sh, kl, n = self.half_beam(x), self.sheer(x), self.keel(x), self.fullness(x)
        s, c = max(math.sin(theta), 0.0), max(math.cos(theta), 0.0)
        return b * s ** (2 / n), sh - (sh - kl) * c ** (2 / n)

    def section_normal(self, x, theta):
        h = 1e-3
        y0, z0 = self.section_point(x, max(theta - h, 0.0))
        y1, z1 = self.section_point(x, min(theta + h, math.pi / 2))
        ty, tz = y1 - y0, z1 - z0
        ny, nz = tz, -ty
        length = math.hypot(ny, nz) or 1.0
        return ny / length, nz / length

    def theta_at(self, x, z):
        """Section parameter where the outer hull reaches height z (clamped)."""
        lo, hi = 0.0, math.pi / 2
        for _ in range(40):
            mid = (lo + hi) / 2
            if self.section_point(x, mid)[1] < z:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def inner_y(self, x, z):
        """Inside face of the planking at height z, starboard."""
        t = self.theta_at(x, z)
        y, _ = self.section_point(x, t)
        ny, _ = self.section_normal(x, t)
        return max(y - self.shell * max(ny, 0.3), 0.0)

    def deck_at(self, x):
        """Height of the deck underfoot at x: the main deck, or the raised aft deck over it."""
        if self.quarterdeck and x <= self.quarterdeck[0]:
            return self.deck_z + self.quarterdeck[1]
        if self.forecastle and x >= self.forecastle[0]:
            return self.deck_z + self.forecastle[1]
        return self.deck_z

    @property
    def stations(self):
        step = self.station_step
        return [self.stern_x + step * i for i in range(int((self.bow_x - self.stern_x) / step) + 1)]

    def strake_params(self):
        """Section samples with seam grooves between strakes and raised wales: (theta, outward offset, strake)."""
        out = []
        span = (math.pi / 2) / self.strakes
        for k in range(self.strakes):
            lift = 4.0 if k in self.wales else 0.0
            below = 4.0 if (k - 1) in self.wales else 0.0
            t0 = k * span
            if k > 0:
                out.append((t0, min(lift, below) - 2.0, k))  # seam groove
            for f in (0.1, 0.37, 0.63, 0.9):
                out.append((t0 + f * span, lift, k))
        out.append((math.pi / 2, 0.0, self.strakes - 1))
        return out

    def tarred(self, p):
        """The lower planking is tarred dark, showing well above the waterline as in the art."""
        return min(1.0, max(0.0, (self.tar_line - p[2]) / 40))

    def along_hull(self, i, j, p):
        """Planking UVs: grain runs fore and aft wherever the hull curves."""
        return (p[2] / self.uv_tile, p[0] / self.uv_tile)

    def in_gunport(self, x, z):
        for port in self.gunports:
            cx, w, z0, z1 = port[:4]
            if len(port) > 4 and port[4] == 'round':
                if ((x - cx) / (w / 2)) ** 2 + ((z - (z0 + z1) / 2) / ((z1 - z0) / 2)) ** 2 < 1:
                    return True
            elif abs(x - cx) < w / 2 and z0 < z < z1:
                return True
        return False

    def near_gunport(self, x, margin, z0, z1):
        """Whether a timber at x spanning z0..z1 would cross a gunport opening."""
        return any(abs(x - p[0]) < p[1] / 2 + margin and p[2] < z1 and p[3] > z0 for p in self.gunports)

    # ---- Planking ----------------------------------------------------------------------------------------

    def outer_shell(self, b):
        params = self.strake_params()
        stations = self.stations
        bow_third = 0.43 * self.bow_x
        for side in (1, -1):
            rows = []
            for x in stations:
                row = []
                for theta, lift, _ in params:
                    y, z = self.section_point(x, theta)
                    ny, nz = self.section_normal(x, theta)
                    row.append((x, side * (y + ny * lift), z + nz * lift))
                rows.append(row)

            def hint(i, j, side=side):
                x = stations[i]
                ny, nz = self.section_normal(x, params[j][0])
                return (math.copysign(0.3, x) if abs(x) > bow_third else 0.0, side * ny, nz)

            def skip(i, j, rows=rows):
                x = (stations[i] + stations[i + 1]) / 2
                z = (rows[i][j][2] + rows[i][j + 1][2]) / 2
                return self.in_gunport(x, z)

            b.grid(rows, hint, skip, tar_of=self.tarred,
                   tone_of=lambda i, j, side=side: plank_tone(params[j][2], side), uv_of=self.along_hull)

    def inner_shell(self, b):
        stations = self.stations
        for side in (1, -1):
            rows = []
            for x in stations:
                t0 = self.theta_at(x, self.floor_z - 4) if self.keel(x) < self.floor_z - 4 else 0.0
                row = []
                for k in range(25):
                    theta = t0 + (math.pi / 2 - t0) * k / 24
                    y, z = self.section_point(x, theta)
                    ny, nz = self.section_normal(x, theta)
                    row.append((x, side * max(y - ny * self.shell, 0.0), z - nz * self.shell))
                rows.append(row)

            def skip(i, j, rows=rows):
                x = (stations[i] + stations[i + 1]) / 2
                z = (rows[i][j][2] + rows[i][j + 1][2]) / 2
                return self.in_gunport(x, z)

            b.grid(rows, lambda i, j, side=side: (0.0, -side, 0.2), skip, uv_of=self.along_hull)

    def rail_and_keel(self, b, straps=(450, 560, 640), keel_size=(18.0, 14.0), post_size=(20.0, 22.0)):
        stations = self.stations
        for side in (1, -1):
            path = [(self.stern_x + 2, 0.0, self.sheer(self.stern_x) + 4.5)]
            path += [(x, side * (self.half_beam(x) - self.shell / 2), self.sheer(x) + 4.5) for x in stations if self.half_beam(x) > 2]
            path.append((self.bow_x - 2, 0.0, self.sheer(self.bow_x) + 4.5))
            b.sweep(path, 16.0, 9.0, side=(0, 1, 0))
        # Keel along the bottom, rising into a stem at the bow and a matching sternpost.
        keel_path = [(x, 0.0, self.keel(x) - 6) for x in stations if abs(x) <= self.keel_flat]
        b.sweep(keel_path, *keel_size, tar=1.0)
        for end in (1, -1):
            top = self.sheer(end * self.bow_x)
            post = [(end * x, 0.0, self.keel(end * x) - 4) for x in [self.keel_flat + 20 * k for k in range(int(self.bow_x / 20) + 1)]
                    if x <= self.bow_x]
            post += [(end * (self.bow_x + 10), 0.0, top), (end * (self.bow_x + 12), 0.0, top + 8)]
            b.sweep(post, *post_size, side=(0, 1, 0))
            for x in straps:  # iron straps binding the post
                b.box((end * (x + 10), 0.0, self.keel(end * x)), (8, 26, 26), iron=1.0)

    # ---- Decks -------------------------------------------------------------------------------------------

    def deck(self, b, z, hatches=(), x_range=None, underside=True, tone_seed=7, board_inset=50.0):
        """A planked deck at z, cut to the hull, with each hatch (aft x, forward x, half-width) left open and
        given a coaming on top. A margin plank each side, cut to the planking, closes the deck against the hull."""
        ys = [-(self.beam - board_inset) + 25 * k for k in range(int(2 * (self.beam - board_inset) / 25) + 1)]
        ys = [-self.beam] + ys + [self.beam]
        stations = [x for x in self.stations if self.inner_y(x, z) > 8 and (not x_range or x_range[0] <= x <= x_range[1])]

        def rows_at(zz):
            return [[(x, max(-self.inner_y(x, zz), min(self.inner_y(x, zz), y)), zz) for y in ys] for x in stations]

        def skip(i, j):
            x = (stations[i] + stations[i + 1]) / 2
            y = (ys[j] + ys[j + 1]) / 2
            return any(aft < x < fwd and abs(y) < half for aft, fwd, half in hatches)

        top = rows_at(z)
        for j in range(len(ys) - 1):
            board = [[row[j], row[j + 1]] for row in top]
            b.grid(board, lambda i, _, j=j: (0, 0, 1), lambda i, _, j=j: skip(i, j), tone_of=lambda i, _, j=j: plank_tone(j, tone_seed))
        if underside:
            b.grid(rows_at(z - self.deck_thick), lambda i, j: (0, 0, -1), skip)
        for aft, fwd, half in hatches:
            length, width, mid = fwd - aft, 2 * half, (aft + fwd) / 2
            for y in (-half - 5, half + 5):
                b.box((mid, y, z + 2), (length + 20, 10, 22))
            for x in (aft - 5, fwd + 5):
                b.box((x, 0.0, z + 2), (10, width, 22))

    def floor(self, b, z, inset=100.0):
        """Floorboards at z, reaching the planking on both sides."""
        ys = [-(self.beam - inset) + 25 * k for k in range(int(2 * (self.beam - inset) / 25) + 1)]
        ys = [-self.beam] + ys + [self.beam]
        stations = [x for x in self.stations if self.inner_y(x, z) > 20]
        rows = [[(x, max(-self.inner_y(x, z), min(self.inner_y(x, z), y)), z) for y in ys] for x in stations]
        b.grid(rows, lambda i, j: (0, 0, 1))

    def beams(self, b, xs, z):
        """Deck beams under a deck whose top is at z."""
        for x in xs:
            half = self.inner_y(x, z - self.deck_thick)
            if half > 10:
                b.box((x, 0.0, z - self.deck_thick - 5), (14, 2 * half, 10))

    def ribs(self, b, xs, z0, z1):
        """Frames following the planking from z0 up to z1, clear of the gunports."""
        for x in xs:
            x = float(x)
            if self.inner_y(x, z0) < 20 or self.near_gunport(x, 8, z0, z1):
                continue
            for side in (1, -1):
                path = []
                for k in range(13):
                    z = z0 + (z1 - z0) * k / 12
                    path.append((x, side * (self.inner_y(x, z) - 4), z))
                b.sweep(path, 9.0, 8.0, side=(1, 0, 0))

    def bulwark_posts(self, b, xs):
        """Posts inside the bulwark from the deck underfoot to just above the rail."""
        for x in xs:
            x = float(x)
            base = self.deck_at(x)
            if self.near_gunport(x, 16, base, self.sheer(x)):
                continue
            for side in (1, -1):
                path = [(x, side * (self.inner_y(x, min(z, self.sheer(x))) - 5), z)
                        for z in (base, (base + self.sheer(x)) / 2, self.sheer(x) + 12)]
                b.sweep(path, 10.0, 10.0, side=(1, 0, 0))

    def stairs(self, b, x0, x1, z_top, z_bottom, steps, width=84.0, y=0.0):
        """A flight rising from z_bottom at x1 to z_top at x0 (x0 < x1 climbs toward the stern)."""
        rise = (z_top - z_bottom) / steps
        run = (x1 - x0) / steps
        for k in range(steps - 1):
            top = z_top - rise * (k + 1)
            xa = x0 + run * k
            b.box((xa + run / 2, y, (z_bottom + top) / 2), (abs(run), width, top - z_bottom))

    def bulkhead(self, b, x, z0, z1, openings=(), thick=8.0, plank=20.0):
        """A bulkhead of horizontal planks across the hull at x from z0 to z1, each cut to the planking, with
        framed openings (y0, y1, z0, z1) left clear."""
        n = max(1, round((z1 - z0) / plank))
        for k in range(n):
            za, zb = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
            zm = (za + zb) / 2
            half = self.inner_y(x, zm) + 2
            edges = [-half] + [y for o in sorted(openings) if o[2] < zm < o[3] for y in o[:2]] + [half]
            for ya, yb in zip(edges[0::2], edges[1::2]):
                if yb - ya > 1:
                    b.box((x, (ya + yb) / 2, zm), (thick, yb - ya, zb - za - 0.6))
        for y0, y1, oz0, oz1 in openings:
            for y in (y0 - 5, y1 + 5):
                b.box((x, y, (oz0 + oz1) / 2), (thick + 6, 10, oz1 - oz0))
            b.box((x, (y0 + y1) / 2, oz1 + 5), (thick + 6, y1 - y0 + 20, 10))

    def raised_deck(self, b, edge, rise, facing, x_range, beams=(), skylight=None, door=(90.0, 205.0),
                    side_lights=(), side_light=(40.0, 400.0, 450.0), steps=11, tone_seed=11):
        """A raised deck over the main deck with a room under it: its deck (with an optional skylight grating),
        beams, a front wall facing the main deck (`facing` +1 forward, -1 aft) with a doorway between two windows,
        glazed lights in the hull sides, stairs up each side against the bulwark, and a breast rail."""
        top = self.deck_z + rise
        self.deck(b, top, [skylight] if skylight else [], x_range=x_range, tone_seed=tone_seed)
        self.beams(b, beams, top)
        if skylight:
            aft, fwd, half = skylight
            for y in (-half / 2, 0.0, half / 2):
                b.box(((aft + fwd) / 2, y, top + 10), (fwd - aft + 10, 5, 6))
        door_w, door_h = door
        windows = [(y - 20.0, y + 20.0, self.deck_z + 95, self.deck_z + 140) for y in (-130.0, 130.0)]
        self.bulkhead(b, edge, self.deck_z, top, openings=[(-door_w / 2, door_w / 2, self.deck_z, self.deck_z + door_h)] + windows)
        # The cut-outs above must be closed panes, not open passages into the cabin. Slot 3 is
        # The dedicated window pane is also a box in complex hull collision.
        old_slot = b.slot
        b.slot = WINDOW_GLASS
        for y0, y1, z0, z1 in windows:
            b.box((edge + 2.0 * facing, (y0 + y1) / 2, (z0 + z1) / 2),
                  (4.0, y1 - y0, z1 - z0))
        b.slot = old_slot
        b.box((edge + 2 * facing, 0.0, top - 6), (16, 2 * self.inner_y(edge, top), 12))
        w, z0, z1 = side_light
        for x in side_lights:
            for side in (1, -1):
                y_out, y_in = self.half_beam(x), self.inner_y(x, (z0 + z1) / 2)
                yc, depth = side * (y_out + y_in) / 2, y_out - y_in + 2
                b.slot = WINDOW_GLASS
                b.box((x, yc, (z0 + z1) / 2), (4, depth, z1 - z0))
                b.slot = old_slot
                for z in (z0 + 2, z1 - 2):
                    b.box((x, yc, z), (w + 8, depth + 2, 4))
                for dx in (-w / 2 - 2, w / 2 + 2):
                    b.box((x + dx, yc, (z0 + z1) / 2), (4, depth + 2, z1 - z0))
        stair_y = self.inner_y(edge, self.deck_z) - 55
        for side in (1, -1):
            self.stairs(b, edge, edge + 25 * steps * facing, top, self.deck_z, steps, width=70.0, y=side * stair_y)
        rail_y = stair_y - 40
        for k in range(7):
            y = -rail_y + 2 * rail_y * k / 6
            b.box((edge + 4 * facing, y, top + 45), (8, 8, 90))
        b.sweep([(edge + 4 * facing, -rail_y - 4, top + 92), (edge + 4 * facing, rail_y + 4, top + 92)], 10.0, 8.0, side=(1, 0, 0))

    # ---- Trim (owner's ship design sheet, October 18) ---------------------------------------------------

    def balustrade(self, b, x0, x1, skip=(), height=34.0, step=26.0):
        """Turned balusters with brass caps standing on the bulwark's rail from x0 to x1 both sides, under a top rail;
        none over the open stretches in `skip` [(x_from, x_to)]."""
        def open_at(x):
            return any(a <= x <= c for a, c in skip)
        for side in (1, -1):
            run = []
            x = x0
            while x <= x1 + 1e-6:
                if open_at(x) or self.half_beam(x) < 40:
                    if len(run) > 1:
                        b.sweep([(px, py, pz + height + 4) for px, py, pz in run], 9.0, 7.0, side=(0, 0, 1))
                    run = []
                else:
                    y, z = side * (self.half_beam(x) - 6), self.sheer(x) + 6
                    b.tube([(x, y, z), (x, y, z + height * .5), (x, y, z + height)], lambda k: (3.2, 4.4, 3.0)[k], sides=8)
                    b.alpha = .5
                    b.tube([(x, y, z + height - 1), (x, y, z + height + 3)], 3.6, sides=8)
                    b.alpha = 1.0
                    run.append((x, y, z))
                x += step
            if len(run) > 1:
                b.sweep([(px, py, pz + height + 4) for px, py, pz in run], 9.0, 7.0, side=(0, 0, 1))

    def brass_band(self, b, below_sheer=38.0, x_pad=40.0):
        """A brass strip along each side a little under the sheer, standing just proud of the planking."""
        b.alpha = .5
        for side in (1, -1):
            path = []
            for x in self.stations:
                if x < self.stern_x + x_pad or x > self.bow_x - x_pad:
                    continue
                z = self.sheer(x) - below_sheer
                t = self.theta_at(x, z)
                y, zz = self.section_point(x, t)
                ny, nz = self.section_normal(x, t)
                path.append((x, side * (y + ny * 2.5), zz + nz * 2.5))
            b.sweep(path, 3.0, 5.0, side=(0, side, 0))
        b.alpha = 1.0

    def stair_rails(self, b, edge, rise, facing, steps=11, run=25.0, height=88.0):
        """Fixed safety railings along the inner edge of both staircases up to a raised deck (owner, October 18: fixed,
        non-editable rails along the stairs and round the raised aft deck, apart from the modular outer railings):
        posts a stride apart and a sloped top rail from the stair's foot to its head, brass-capped, with the same
        geometry `raised_deck` builds its stairs on."""
        top = self.deck_z + rise
        stair_y = self.inner_y(edge, self.deck_z) - 55
        foot_x, head_x = edge + run * steps * facing, edge
        for side in (1, -1):
            y = side * (stair_y - 35 - 4)
            posts = max(3, steps // 2)
            path = []
            for k in range(posts + 1):
                f = k / posts
                x = foot_x + (head_x - foot_x) * f
                z = self.deck_z + (top - self.deck_z) * f
                b.tube([(x, y, z), (x, y, z + height * .5), (x, y, z + height)], lambda q: (3.2, 4.2, 3.0)[q], sides=8)
                b.alpha = .5
                b.tube([(x, y, z + height - 1), (x, y, z + height + 3)], 3.6, sides=8)
                b.alpha = 1.0
                path.append((x, y, z + height + 4))
            b.sweep(path, 8.0, 6.0, side=(0, 1, 0))

    def sail_socket(self, b, x, y, deck_z, radius=26.0):
        """An empty sail hardpoint (owner, October 18: base hulls carry no permanent masts; each sail location keeps a
        clearly identified socket for a removable sail assembly): an iron base plate bolted to the deck, a collar with a
        brass band, a brass locking pin. The assembly's mast stands in it."""
        b.box((x, y, deck_z + 3), (2 * radius + 26, 2 * radius + 26, 6), iron=1.0)
        for dx in (-1, 1):
            for dy in (-1, 1):
                b.tube([(x + dx * (radius + 8), y + dy * (radius + 8), deck_z + 5), (x + dx * (radius + 8), y + dy * (radius + 8), deck_z + 9)], 3.2, sides=6, iron=1.0)
        b.cylinder((x, y, deck_z + 6), radius, 28.0, sides=18, iron=1.0)
        b.alpha = .5
        b.cylinder((x, y, deck_z + 26), radius + 2.0, 6.0, sides=18)       # the brass band at the collar's lip
        b.tube([(x + radius + 2, y - 8, deck_z + 18), (x + radius + 14, y - 8, deck_z + 18)], 3.0, sides=6)   # the locking pin
        b.alpha = 1.0

    # ---- Fittings in the hull ----------------------------------------------------------------------------

    def studs(self, b, xs):
        """Iron nail heads where each strake crosses a frame."""
        span = (math.pi / 2) / self.strakes
        for x in xs:
            x = float(x)
            for k in range(self.strakes):
                theta = (k + 0.5) * span
                y, z = self.section_point(x, theta)
                if self.in_gunport(x, z) or self.half_beam(x) < 10:
                    continue
                ny, nz = self.section_normal(x, theta)
                for side in (1, -1):
                    b.box((x, side * (y + ny * 1.5), z + nz * 1.5), (3.5, 3.5, 3.5), iron=1.0)

    def gunport_frames(self, b):
        for port in self.gunports:
            cx, w, z0, z1 = port[:4]
            kind = port[4] if len(port) > 4 else 'square'
            if kind == 'gap':
                continue
            if kind == 'round':
                # A thick ring of timber round the port, in twelve segments.
                zc, r = (z0 + z1) / 2, w / 2 + 5
                for side in (1, -1):
                    y_out = self.half_beam(cx) + 2
                    y_in = self.inner_y(cx, zc) - 2
                    yc, depth = side * (y_out + y_in) / 2, y_out - y_in + 4
                    for k in range(12):
                        a = 2 * math.pi * (k + .5) / 12
                        b.box((cx + r * math.cos(a), yc, zc + r * math.sin(a)), (11 if abs(math.sin(a)) > .5 else 9, depth, 11 if abs(math.cos(a)) > .5 else 9))
                continue
            for side in (1, -1):
                y_out = self.half_beam(cx) + 2
                y_in = self.inner_y(cx, (z0 + z1) / 2) - 2
                yc, depth = side * (y_out + y_in) / 2, y_out - y_in + 4
                b.box((cx, yc, z0 - 4), (w + 16, depth, 8))
                b.box((cx, yc, z1 + 4), (w + 16, depth, 8))
                b.box((cx - w / 2 - 4, yc, (z0 + z1) / 2), (8, depth, z1 - z0))
                b.box((cx + w / 2 + 4, yc, (z0 + z1) / 2), (8, depth, z1 - z0))

    def ladders(self, b, ladder_x):
        for side in (1, -1):
            def out(x, z, side=side):
                t = self.theta_at(x, z)
                y, _ = self.section_point(x, t)
                return side * (y + 9)
            top = self.sheer(ladder_x)
            zs = [-40 + 20 * k for k in range(int((top + 10 + 40) / 20) + 1)]
            for dx in (-22, 22):
                x = ladder_x + dx
                b.sweep([(x, out(x, z), z) for z in zs], 5.0, 6.0, side=(1, 0, 0))
            for z in range(-30, int(top), 30):
                y = out(ladder_x, z) + side * 1
                b.sweep([(ladder_x - 24, y, z), (ladder_x + 24, y, z)], 4.0, 4.0, side=(0, 1, 0))

    def stern_ladder_line(self, z_foot, stand_off=16.0):
        """The boarding ladder centred on the stern (owner, October 16): a straight ladder on the centreline from just
        above the rudder's head (z_foot) to the top of the stern post, standing off the raked post on brackets so no
        rung meets it. Returns the rung line's foot and head, (x, 0, z) each, in the ship's space."""
        z_head = next(z for z in range(int(z_foot), 2000, 5) if z >= self.sheer(self.stern_post_x(z)) - 5)
        foot, head = self.stern_post_x(z_foot) - stand_off, self.stern_post_x(z_head) - stand_off
        # The post bulges aft of a straight line between its ends: move the whole line aft until it clears it.
        bulge = max(foot + (head - foot) * (z - z_foot) / (z_head - z_foot) - (self.stern_post_x(z) - stand_off)
                    for z in range(int(z_foot), z_head + 1, 5))
        foot, head = foot - max(0.0, bulge), head - max(0.0, bulge)
        return (foot, 0.0, float(z_foot)), (head, 0.0, float(z_head))

    def stern_ladder(self, b, line):
        """Draw a stern ladder along line (from stern_ladder_line): two rails, rungs every 30 cm and iron-strapped
        brackets back to the post."""
        (xf, _, zf), (xh, _, zh) = line
        at = lambda z: xf + (xh - xf) * (z - zf) / (zh - zf)
        for y in (-22.0, 22.0):
            b.sweep([(at(z), y, z) for z in (zf - 10, (zf + zh) / 2, zh + 25)], 5.0, 6.0, side=(0, 1, 0))
        z = zf + 10
        while z < zh:
            b.sweep([(at(z), -24.0, z), (at(z), 24.0, z)], 4.0, 4.0, side=(1, 0, 0))
            z += 30
        for k in range(1, 4):
            z = zf + (zh - zf) * k / 4
            post = self.stern_post_x(z)
            length = post - at(z)
            if length > 4:
                for y in (-22.0, 22.0):
                    b.box((at(z) + length / 2, y, z), (length + 4, 6, 6), iron=1.0)

    CAPSTAN_TOP = 80.0      # the barrel's top above the deck, where the drumhead sits

    def capstan(self, b, x, y, z):
        """A capstan's fixed base and barrel; its head turns on top (capstan_head)."""
        b.cylinder((x, y, z), 26, 6)
        b.cylinder((x, y, z + 6), 19, self.CAPSTAN_TOP - 6)

    @classmethod
    def capstan_head(cls, b):
        """The part of a capstan that turns, about the middle of its base on the deck: iron whelps up the barrel,
        the drumhead and four bars to push it round by."""
        top = cls.CAPSTAN_TOP
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            b.box((19 * math.cos(a), 19 * math.sin(a), (12 + top - 6) / 2), (6, 6, top - 18), iron=1.0)
        b.cylinder((0, 0, top), 27, 10)
        for k in range(4):
            c, s = math.cos(k * math.pi / 2), math.sin(k * math.pi / 2)
            b.tube([(20 * c, 20 * s, top + 5), (85 * c, 85 * s, top + 5)], 2.6, sides=8)

    def mast(self, b, x, top, radius=15.0, top_radius=10.0, coat_z=None):
        """A mast stepped on the floor, rising through the deck at coat_z to its cap."""
        coat_z = self.deck_at(x) if coat_z is None else coat_z
        b.tube([(x, 0.0, self.floor_z), (x, 0.0, coat_z), (x, 0.0, top)],
               lambda k: (radius, radius, top_radius)[k], sides=14)
        b.box((x, 0.0, top + 6), (2.6 * top_radius, 2.6 * top_radius, 12))       # masthead cap
        b.tube([(x, 0.0, coat_z), (x, 0.0, coat_z + 12)], radius + 4, sides=14, iron=1.0)  # mast coat

    def bowsprit(self, b, heel, end, radius=(11.0, 7.0)):
        b.tube([heel, end], lambda k: radius[k], sides=12)
        b.tube([lerp3(heel, end, 0.97), end], radius[1] + 1.5, sides=12, iron=1.0)  # iron band where stays meet

    # ---- Rig ironwork, rudder and anchors ----------------------------------------------------------------

    CHANNEL_DROP = 25.0     # channels sit this far below the rail
    DEADEYE_OUT = 20.0      # deadeyes stand this far outboard of the hull's widest point

    def deadeye_top(self, x, side):
        """Where a shroud ends: on top of its deadeye, on the channel outboard of the rail."""
        return (x, side * (self.half_beam(x) + self.DEADEYE_OUT), self.sheer(x) - self.CHANNEL_DROP + 24)

    def channels(self, b, xs):
        """A channel (a ledge on the hull side) for a mast's shrouds, a deadeye for each, and the iron chainplate
        that carries it down the planking, on both sides."""
        xm = sum(xs) / len(xs)
        z = self.sheer(xm) - self.CHANNEL_DROP
        for side in (1, -1):
            out = self.half_beam(xm)
            b.box((xm, side * (out + 12), z), (max(xs) - min(xs) + 70, 30, 8))
            for x in xs:
                y = side * (self.half_beam(x) + self.DEADEYE_OUT)
                b.tube([(x, y - 3.5, z + 13), (x, y + 3.5, z + 13)], 9.0, sides=12)      # deadeye
                b.tube([(x, y - 4.5, z + 13), (x, y + 4.5, z + 13)], 9.6, sides=12, iron=1.0, capped=False)  # its iron strop
                low = z - 70
                t = self.theta_at(x, low)
                hull_y, _ = self.section_point(x, t)
                b.sweep([(x, y, z + 4), (x, side * (hull_y + 2), low)], 4.0, 1.5, side=(1, 0, 0), iron=1.0)  # chainplate

    def shrouds(self, r, mast_x, top_z, xs, radius=1.6, spread=11.0, ratlines=True):
        """Shrouds from just below a masthead down to their deadeyes, on both sides, with ratlines (the rope rungs
        crew climb by) across them every 38 cm."""
        for side in (1, -1):
            lines = []
            for x in xs:
                end = self.deadeye_top(x, side)
                r.tube([(mast_x, side * spread, top_z), end], radius, sides=6)
                lines.append(((mast_x, side * spread, top_z), end))
            if not ratlines or len(lines) < 2:
                continue
            low = max(line[1][2] for line in lines) + 45
            z = low
            while z < top_z - 120:
                pts = [lerp3(a, e, (top_z - z) / (top_z - e[2])) for a, e in lines]
                for p0, p1 in zip(pts, pts[1:]):
                    r.tube([p0, p1], 0.7, sides=4, capped=False)
                z += 38.0

    def stern_post_x(self, z):
        """Where the curve of the stern meets height z, on the keel's centreline."""
        lo, hi = self.stern_x, -self.keel_flat
        for _ in range(40):
            mid = (lo + hi) / 2
            if self.keel(mid) > z:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def rudder(self, b, z_low, z_high, chord_low, chord_high, thick):
        """A straight, raked rudder hung on the curve of the stern by iron pintles: its leading edge runs between
        the stern's points at z_low and z_high, and the blade reaches aft of it, tarred below the waterline."""
        a = (self.stern_post_x(z_low), z_low)
        e = (self.stern_post_x(z_high), z_high)
        rows = 8
        lead = [(a[0] + (e[0] - a[0]) * k / rows, a[1] + (e[1] - a[1]) * k / rows) for k in range(rows + 1)]
        chord = [chord_low + (chord_high - chord_low) * k / rows for k in range(rows + 1)]
        tar = lambda p: 1.0 if p[2] < 20 else 0.0
        for side in (1, -1):
            face = [[(x, side * thick / 2, z), (x - c, side * thick / 2, z)] for (x, z), c in zip(lead, chord)]
            b.grid(face, lambda i, j, side=side: (0, side, 0), tar_of=tar)
        edge = lambda pts: [[(x, -thick / 2, z), (x, thick / 2, z)] for x, z in pts]
        b.grid(edge([(x - c, z) for (x, z), c in zip(lead, chord)]), lambda i, j: (-1, 0, 0), tar_of=tar)   # trailing edge
        b.grid(edge(lead), lambda i, j: (1, 0, 0), tar_of=tar)                                              # leading edge
        for (x, z), c, sign in ((lead[0], chord[0], -1), (lead[-1], chord[-1], 1)):                          # foot and head
            b.grid([[(x, -thick / 2, z), (x, thick / 2, z)], [(x - c, -thick / 2, z), (x - c, thick / 2, z)]],
                   lambda i, j, sign=sign: (0, 0, sign), tar_of=tar)
        for k in (1, 4, 7):  # pintle straps wrapping the post
            x, z = lead[k]
            b.box((x + 6, 0.0, z), (26, thick + 8, 7), iron=1.0)

    def cathead_and_anchor(self, b, x, side, size):
        """A cathead beam jutting from the bow's rail with an anchor catted beneath it, clear of the water."""
        inner, outer = self.half_beam(x) - 30, self.half_beam(x) + 50 * size
        z = self.sheer(x) - 8
        b.sweep([(x, side * inner, z), (x, side * outer, z + 6)], 16.0 * size, 16.0 * size, side=(1, 0, 0))
        b.box((x, side * (outer - 3), z + 6), (18 * size, 6, 18 * size), iron=1.0)
        y = side * (outer - 8)
        top, length = z - 18, 120.0 * size
        crown = top - length
        b.tube([(x, y, top + 10), (x, y, top)], 7.0 * size, sides=10, iron=1.0, capped=False)  # ring
        b.tube([(x, y, top), (x, y, crown)], 4.5 * size, sides=8, iron=1.0)                       # shank
        b.sweep([(x, y - 45 * size, top - 12), (x, y + 45 * size, top - 12)], 9 * size, 9 * size, side=(1, 0, 0))  # wooden stock
        for sign in (1, -1):  # arms curving up from the crown to the flukes
            arm = [(x + sign * 40 * size * math.sin(a), y, crown + 40 * size * (1 - math.cos(a))) for a in (0.0, 0.5, 1.0, 1.35)]
            b.tube(arm, 4.0 * size, sides=8, iron=1.0)
            fx, _, fz = arm[-1]
            b.box((fx - sign * 4 * size, y, fz - 6 * size), (16 * size, 3, 22 * size), iron=1.0)

    def pin_rail(self, b, x, length=110.0):
        """A pin rail inside the bulwark at a mast, with belaying pins, on both sides."""
        base = self.deck_at(x)
        z = base + 75
        for side in (1, -1):
            y = side * (self.inner_y(x, z) - 9)
            b.box((x, y, z), (length, 11, 6))
            for k in range(6):
                px = x - length / 2 + 12 + (length - 24) * k / 5
                b.tube([(px, y, z + 13), (px, y, z - 12)], lambda q: (1.8, 1.4)[q], sides=6)


def tar_rope(r):
    """Colour every vertex of a rigging builder as tarred rope."""
    for k in range(len(r.colours)):
        r.colours[k] = (1.0, 0.0, 0.5)
    return r
