"""Draws the aged explorer's-journal paper (owner, October 22): warm cream and tan with paper grain and fibres, soft stains and foxing spots, creases, and
edges browned and worn. Pure Python (no libraries); writes Art/UI/Journal/JournalParchment.png, 768 x 1024, an original texture made for this game.
    python Scripts/Art/make_journal_parchment.py
Imported to /Game/Elitewake/UI/Journal/T_JournalParchment by Scripts/Setup/import_journal_parchment.py."""
import math
import random
import struct
import zlib
from pathlib import Path

W, H = 768, 1024
random.seed(1022)
OUT = Path(__file__).resolve().parents[2] / 'Art' / 'UI' / 'Journal' / 'JournalParchment.png'


def lattice(size_x, size_y, seed):
    rng = random.Random(seed)
    return [[rng.random() for _ in range(size_x + 2)] for _ in range(size_y + 2)]


def smooth(t):
    return t * t * (3 - 2 * t)


def value_noise(grid, cells_x, cells_y, x, y):
    gx, gy = x / W * cells_x, y / H * cells_y
    ix, iy = int(gx), int(gy)
    fx, fy = smooth(gx - ix), smooth(gy - iy)
    a, b = grid[iy][ix], grid[iy][ix + 1]
    c, d = grid[iy + 1][ix], grid[iy + 1][ix + 1]
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


octaves = [(3, 3, 11, .45), (8, 10, 12, .28), (24, 32, 13, .17), (96, 128, 14, .10)]
grids = [(cx, cy, lattice(cx, cy, seed), amp) for cx, cy, seed, amp in octaves]
stain_grid = lattice(4, 5, 99)
stain_fine = lattice(11, 14, 98)

base = [(226, 205, 160), (206, 178, 126)]     # light and dark paper
pix = [[0.0] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        n = sum(amp * value_noise(g, cx, cy, x, y) for cx, cy, g, amp in grids)    # 0..~1
        pix[y][x] = n

# Fibres: short faint strokes lying every way.
fibre = [[0.0] * W for _ in range(H)]
for _ in range(2600):
    x, y = random.random() * W, random.random() * H
    a = random.random() * math.tau
    length = random.randint(6, 26)
    shade = random.choice((-1, 1)) * random.uniform(.03, .08)
    for i in range(length):
        px, py = int(x + math.cos(a) * i), int(y + math.sin(a) * i)
        if 0 <= px < W and 0 <= py < H:
            fibre[py][px] += shade
        a += random.uniform(-.12, .12)

# Foxing: little rust-brown spots, each with a soft halo.
spots = [(random.random() * W, random.random() * H, random.uniform(2.5, 11), random.uniform(.25, .7)) for _ in range(70)]
# Creases: one fold down the middle-ish and one across, as a page kept folded in a pocket.
cx_fold = W * random.uniform(.47, .53)
cy_fold = H * random.uniform(.46, .54)

rows = bytearray()
for y in range(H):
    rows.append(0)
    for x in range(W):
        n = pix[y][x]
        t = min(1.0, max(0.0, (n - .28) / .55))
        r = base[0][0] + (base[1][0] - base[0][0]) * t
        g = base[0][1] + (base[1][1] - base[0][1]) * t
        b = base[0][2] + (base[1][2] - base[0][2]) * t
        f = fibre[y][x]
        r += f * 255 * .9; g += f * 255 * .85; b += f * 255 * .7
        # Water stains: broad tide-lined blotches.
        s = value_noise(stain_grid, 4, 5, x, y) * .75 + value_noise(stain_fine, 11, 14, x, y) * .25
        ring = max(0.0, 1 - abs(s - .62) * 14)         # a darker rim where the stain dried
        wash = max(0.0, (s - .58) * 2.2)
        r -= wash * 26 + ring * 22; g -= wash * 34 + ring * 28; b -= wash * 44 + ring * 36
        # Creases.
        dx, dy = abs(x - cx_fold), abs(y - cy_fold)
        crease = max(0.0, 1 - dx / 3.2) * .5 + max(0.0, 1 - dy / 3.2) * .4
        light = max(0.0, 1 - (dx - 3) / 4.0) * (1 if x > cx_fold else 0) * .0
        r -= crease * 38; g -= crease * 40; b -= crease * 44
        # Edges: wear, brown and a little ragged.
        edge = min(x, W - 1 - x, y, H - 1 - y)
        jag = (math.sin(x * .21) + math.sin(y * .17) + math.sin((x + y) * .09)) * 2.2
        burn = max(0.0, 1 - (edge + jag) / 70.0) ** 1.7
        r -= burn * 98; g -= burn * 118; b -= burn * 112
        px = [r, g, b]
        # Fine grain.
        gr = random.uniform(-4, 4)
        rows += bytes(max(0, min(255, int(c + gr))) for c in px)

# Foxing spots painted over the finished rows.
raw = bytearray(rows)
stride = 1 + W * 3
for sx, sy, rad, strength in spots:
    for yy in range(int(sy - rad * 2.5), int(sy + rad * 2.5) + 1):
        if not 0 <= yy < H:
            continue
        for xx in range(int(sx - rad * 2.5), int(sx + rad * 2.5) + 1):
            if not 0 <= xx < W:
                continue
            d = math.hypot(xx - sx, yy - sy) / rad
            if d > 2.5:
                continue
            k = strength * (math.exp(-d * d * 1.3))
            i = yy * stride + 1 + xx * 3
            raw[i] = max(0, int(raw[i] - k * 90))
            raw[i + 1] = max(0, int(raw[i + 1] - k * 125))
            raw[i + 2] = max(0, int(raw[i + 2] - k * 150))


def chunk(tag, data):
    c = struct.pack('>I', len(data)) + tag + data
    return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(png)
print('wrote', OUT, len(png), 'bytes')
