"""Draws the inventory icons for the crystals, obsidian and coal (owner rules, October 28): 256 x 256 RGBA PNGs in Art/Items/Icons,
in the same size and transparent-background form as the other item icons. They are drawn from flat facets (a cut gem seen from
above, a shard, a lump), so they are placeholders for painted art. Run with plain Python (Pillow):
    python Scripts/Art/make_crystal_icons.py
Then import with Scripts/Setup/import_crystal_icons.py inside the editor."""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[2] / 'Art' / 'Items' / 'Icons'
SIZE = 256


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)


def gem(base, name, seed):
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    glow = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    cx, cy = 128, 132
    # an octagonal cut gem: a table (flat top), a crown ring of eight facets, an outline
    outer = [(cx + 98 * math.cos(math.radians(a)), cy + 88 * math.sin(math.radians(a))) for a in range(22, 382, 45)]
    table = [(cx + 46 * math.cos(math.radians(a)), cy - 8 + 40 * math.sin(math.radians(a))) for a in range(22, 382, 45)]
    g.polygon(outer, fill=base + (255,))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.polygon(outer, fill=shade(base, .62))
    rng = random.Random(seed)
    for i in range(8):
        a, b = outer[i], outer[(i + 1) % 8]
        c, e = table[(i + 1) % 8], table[i]
        light = .55 + .75 * max(0.0, math.cos(math.radians(45 * i + 22 - 235)))   # lit from the upper left
        d.polygon([a, b, c, e], fill=shade(base, light * (0.92 + rng.random() * .16)))
    d.polygon(table, fill=shade(base, 1.25))
    d.line(table + [table[0]], fill=shade(base, 1.7), width=2)
    for i in range(8):
        d.line([outer[i], table[i]], fill=shade(base, 1.45), width=1)
    d.line(outer + [outer[0]], fill=shade(base, .35), width=3)
    # a small highlight
    d.polygon([(cx - 36, cy - 34), (cx - 10, cy - 46), (cx - 4, cy - 38), (cx - 28, cy - 24)], fill=(255, 255, 255, 190))
    img.save(OUT / f'{name}-v1.png')


def obsidian():
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # a glassy black shard with sharp planes and a violet sheen
    pts = [(128, 22), (190, 96), (176, 214), (112, 236), (62, 190), (70, 96)]
    planes = [((128, 22), (190, 96), (128, 120), 1.5), ((128, 22), (128, 120), (70, 96), .9), ((190, 96), (176, 214), (128, 120), .55),
              ((70, 96), (128, 120), (62, 190), .35), ((128, 120), (176, 214), (112, 236), .7), ((128, 120), (112, 236), (62, 190), .25)]
    base = (30, 26, 44)
    d.polygon(pts, fill=shade(base, .3))
    for a, b, c, k in planes:
        d.polygon([a, b, c], fill=shade(base, k * 1.7))
    d.line(pts + [pts[0]], fill=(8, 6, 14, 255), width=4)
    d.line([(128, 22), (128, 120), (112, 236)], fill=(150, 130, 210, 255), width=2)
    d.polygon([(118, 44), (132, 40), (130, 96), (120, 100)], fill=(190, 175, 240, 150))
    img.save(OUT / 'Obsidian-v1.png')


def coal():
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(5)
    # three angular lumps, each a dark polygon with lit and shaded planes
    for cx, cy, r, k in ((92, 150, 64, 1.0), (164, 156, 56, .85), (126, 98, 58, 1.15)):
        n = 9
        pts = [(cx + (r * (.75 + rng.random() * .3)) * math.cos(2 * math.pi * i / n), cy + (r * (.65 + rng.random() * .3)) * math.sin(2 * math.pi * i / n)) for i in range(n)]
        d.polygon(pts, fill=shade((38, 38, 42), k))
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            light = .6 + .9 * max(0.0, math.cos(2 * math.pi * (i + .5) / n + math.pi * .75))
            d.polygon([a, b, (cx, cy)], fill=shade((42, 42, 48), light * k))
        d.line(pts + [pts[0]], fill=(6, 6, 8, 255), width=3)
        d.polygon([(cx - r * .4, cy - r * .45), (cx - r * .1, cy - r * .55), (cx - r * .05, cy - r * .35), (cx - r * .35, cy - r * .25)], fill=(120, 120, 135, 150))
    img.save(OUT / 'Coal-v1.png')


if __name__ == '__main__':
    gem((205, 22, 52), 'Ruby', 1)
    gem((34, 82, 215), 'Sapphire', 2)
    gem((24, 182, 84), 'Emerald', 3)
    obsidian()
    coal()
    print('wrote', [p.name for p in sorted(OUT.glob('*-v1.png')) if p.stem[:-3] in ('Ruby', 'Sapphire', 'Emerald', 'Obsidian', 'Coal')])
