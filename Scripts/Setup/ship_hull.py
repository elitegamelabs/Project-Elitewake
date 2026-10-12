"""A planked, double-ended wooden hull drawn from a handful of lines, shared by the ship hull scripts.

Coordinates are the ship's own, in cm: X forward to the bow, Y to starboard, Z up, the waterline at Z 0.
`Hull` holds the lines (beam, sheer, keel and fullness along the length) and draws the parts every hull has:
planking with seams and wales, the inner skin, rail, keel and end posts, decks, ribs, beams, gunports, studs,
ladders, a capstan, masts and standing rigging. Each ship script sets the lines and places the parts.
"""
import math
from dataclasses import dataclass, field
from typing import Optional



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
    gunports: list = field(default_factory=list)  # (centre x, width, bottom z, top z)
    quarterdeck: Optional[tuple] = None           # (front x, rise): a raised aft deck

    # ---- Lines -------------------------------------------------------------------------------------------

    def half_beam(self, x):
        return self.beam * max(0.0, 1 - (abs(x) / self.bow_x) ** self.beam_power) ** 0.5

    def quarterdeck_lift(self, x):
        """How far the raised aft deck lifts the sheer at x, easing up over 80 cm to full height just aft of its front."""
        if not self.quarterdeck:
            return 0.0
        front, rise = self.quarterdeck
        # The raised deck keeps the bulwark's height above it, until the sweep up to the stern catches up.
        return max(0.0, self.sheer_mid + rise - self.end_sheer(x)) * smoothstep((front + 60 - x) / 80)

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
        if ax > self.keel_flat:
            return self.keel_z + (self.end_sheer(x) - 12 - self.keel_z) * ((ax - self.keel_flat) / (self.bow_x - self.keel_flat)) ** self.keel_power
        return self.keel_z

    def fullness(self, x):
        """Superellipse exponent of the sections: full amidships, sharp at both ends."""
        ax = abs(x)
        if ax > self.full_len:
            return self.full_mid - (self.full_mid - self.full_end) * (ax - self.full_len) / (self.bow_x - self.full_len)
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
        return any(abs(x - cx) < w / 2 and z0 < z < z1 for cx, w, z0, z1 in self.gunports)

    def near_gunport(self, x, margin, z0, z1):
        """Whether a timber at x spanning z0..z1 would cross a gunport opening."""
        return any(abs(x - cx) < w / 2 + margin and lo < z1 and hi > z0 for cx, w, lo, hi in self.gunports)

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
        for cx, w, z0, z1 in self.gunports:
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

    def capstan(self, b, x, y, z):
        b.cylinder((x, y, z), 26, 6)
        b.cylinder((x, y, z + 6), 19, 52)
        b.cylinder((x, y, z + 58), 27, 9)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            b.box((x + 19 * math.cos(a), y + 19 * math.sin(a), z + 32), (6, 6, 40), iron=1.0)

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

    def shrouds(self, r, mast_x, top_z, xs, radius=1.6, spread=11.0):
        """Shrouds from just below a masthead down to the rail at each x, on both sides."""
        for side in (1, -1):
            for x in xs:
                r.tube([(mast_x, side * spread, top_z), (x, side * (self.half_beam(x) + 1), self.sheer(x) + 3)], radius, sides=6)


def tar_rope(r):
    """Colour every vertex of a rigging builder as tarred rope."""
    for k in range(len(r.colours)):
        r.colours[k] = (1.0, 0.0, 0.5)
    return r
