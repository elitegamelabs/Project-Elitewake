"""Paint the inventory icons for Raw Fish and Raw Meat. Safe to run again.
Run with ordinary Python (Pillow), outside Unreal:
    python Scripts/Art/make_food_icons.py

Writes Art/Items/Raw-Fish-v1.png (a pink fillet with pale fat lines and a silver skin edge) and
Art/Items/Raw-Meat-v1.png (a red steak with a fat rim, marbling and a bone), 512 x 512 on transparency.
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[2] / 'Art/Items'
SIZE = 512


def blob(points, size=SIZE, blur=3):
    mask = Image.new('L', (size, size))
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def outline(cx, cy, rx, ry, wobble, seed, tilt=0.0, steps=90):
    rng = random.Random(seed)
    bumps = [(rng.uniform(.5, 1.5), rng.uniform(0, 6.28)) for _ in range(4)]
    points = []
    for k in range(steps):
        a = k / steps * 2 * math.pi
        r = 1 + sum(wobble * math.sin(a * (n + 2) * f + p) / (n + 2) for n, (f, p) in enumerate(bumps))
        x, y = rx * r * math.cos(a), ry * r * math.sin(a)
        points.append((cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)))
    return points


def speckle(image, mask, amount, seed):
    """Fine tonal noise inside the mask, so flat colour reads as flesh."""
    rng = random.Random(seed)
    noise = Image.new('L', image.size)
    noise.putdata([128 + int(rng.gauss(0, amount)) for _ in range(image.width * image.height)])
    noise = noise.filter(ImageFilter.GaussianBlur(1.2))
    grey = Image.merge('RGB', (noise, noise, noise))
    textured = ImageChops.overlay(image.convert('RGB'), grey)
    return Image.composite(textured, image.convert('RGB'), mask)


def shade(image, mask, light=(-.5, -.7)):
    """Light from the upper left: lighter toward it, darker away, following the mask's thickness."""
    soft = mask.filter(ImageFilter.GaussianBlur(28))
    shifted = ImageChops.offset(soft, int(light[0] * 18), int(light[1] * 18))
    lit = ImageChops.subtract(soft, shifted, scale=1, offset=128)
    tone = Image.merge('RGB', (lit, lit, lit))
    return Image.composite(ImageChops.overlay(image.convert('RGB'), tone), image.convert('RGB'), mask)


def raw_fish():
    shape = outline(256, 262, 200, 118, .07, 3, tilt=-.32)
    mask = blob(shape)
    art = Image.new('RGB', (SIZE, SIZE), (238, 124, 96))
    draw = ImageDraw.Draw(art)
    # Pale fat lines curving across the fillet.
    for k in range(-6, 8):
        x = 256 + k * 30
        draw.arc((x - 150, 70, x + 40, 470), 300, 60, fill=(252, 214, 196), width=7)
    art = art.filter(ImageFilter.GaussianBlur(2.2))
    # Silver skin along the lower edge.
    skin = blob(outline(256, 300, 200, 104, .07, 3, tilt=-.32))
    inner = blob(outline(244, 250, 186, 104, .07, 3, tilt=-.32))
    edge = ImageChops.subtract(skin, inner)
    art = Image.composite(Image.new('RGB', art.size, (176, 186, 196)), art, edge)
    art = shade(speckle(art, mask, 14, 4), mask)
    art.putalpha(mask)
    return art


def raw_meat():
    shape = outline(250, 262, 196, 150, .09, 7, tilt=.25)
    mask = blob(shape)
    art = Image.new('RGB', (SIZE, SIZE), (164, 30, 34))
    # Fat rim round the edge.
    inner = blob(outline(258, 258, 168, 124, .09, 7, tilt=.25))
    rim = ImageChops.subtract(mask, inner)
    art = Image.composite(Image.new('RGB', art.size, (244, 226, 204)), art, rim)
    # Marbling: thin pale veins.
    draw = ImageDraw.Draw(art)
    rng = random.Random(9)
    for _ in range(14):
        x, y, heading = rng.uniform(130, 370), rng.uniform(160, 360), rng.uniform(0, 6.28)
        points = [(x, y)]
        for _ in range(14):
            heading += rng.uniform(-.35, .35)
            x += 7 * math.cos(heading); y += 7 * math.sin(heading)
            points.append((x, y))
        draw.line(points, fill=(226, 160, 150), width=rng.choice((2, 3)), joint='curve')
    art = art.filter(ImageFilter.GaussianBlur(2.0))
    # A round bone, cut across.
    bone = blob(outline(196, 222, 34, 30, .05, 2), blur=2)
    marrow = blob(outline(196, 222, 15, 13, .05, 2), blur=2)
    art = Image.composite(Image.new('RGB', art.size, (236, 228, 210)), art, bone)
    art = Image.composite(Image.new('RGB', art.size, (150, 82, 70)), art, marrow)
    art = shade(speckle(art, mask, 16, 10), mask)
    art.putalpha(mask)
    return art


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    raw_fish().save(OUT / 'Raw-Fish-v1.png')
    raw_meat().save(OUT / 'Raw-Meat-v1.png')
    print('written', OUT)
