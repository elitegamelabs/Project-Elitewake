"""Draw the broadleaf foliage card for the Maravai tree. Safe to run again.
Run with ordinary Python (Pillow), outside Unreal:
    python Scripts/Art/make_leaf_cluster.py

Writes Art/Flora/Maravai-Leaves-v1.png: a 1024 px square of overlapping glossy tropical leaves on transparency,
thickest in the middle and thinning to single leaves at the edge, so crossed cards of it read as a leafy clump.
Each leaf is a pointed oval with a pale midrib, lit from above (lighter tips, darker bases), in several greens.
Scripts/Setup/build_coastal_flora.py imports it.
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Art/Flora/Maravai-Leaves-v1.png'
SIZE = 1024
GREENS = [(46, 92, 34), (58, 108, 40), (38, 80, 30), (72, 118, 44), (52, 98, 52), (84, 124, 50)]


def leaf(draw, x, y, angle, length, width, colour, rng):
    """A pointed oval leaf from its stalk at (x, y) along `angle`, shaded from base to tip, with a midrib."""
    ca, sa = math.cos(angle), math.sin(angle)
    steps = 14
    for band in range(steps, 0, -1):
        # Draw from the outline inward so the base is darker and the upper face catches the light.
        f = band / steps
        shade = .72 + .38 * (1 - f) + rng.uniform(-.04, .04)
        fill = tuple(max(0, min(255, int(c * shade))) for c in colour) + (255,)
        pts = []
        for k in range(25):
            t = k / 24
            w = width * f * math.sin(math.pi * t) ** .8 * (1 - .25 * t)
            pts.append((t * length, w))
        for k in range(24, -1, -1):
            t = k / 24
            w = width * f * math.sin(math.pi * t) ** .8 * (1 - .25 * t)
            pts.append((t * length, -w))
        draw.polygon([(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts], fill=fill)
    rib = tuple(min(255, int(c * 1.45)) for c in colour) + (255,)
    draw.line([(x, y), (x + length * .92 * ca, y + length * .92 * sa)], fill=rib, width=2)


def main():
    rng = random.Random(7)
    image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    centre = SIZE / 2
    # Leaves farther out are drawn first so the clump's heart sits on top; fewer leaves toward the edge.
    leaves = []
    for _ in range(420):
        r = (rng.random() ** .75) * SIZE * .42
        a = rng.uniform(0, 2 * math.pi)
        leaves.append((r, a))
    for r, a in sorted(leaves, reverse=True):
        x, y = centre + r * math.cos(a), centre + r * math.sin(a)
        out = a + rng.uniform(-.7, .7)              # leaves point roughly away from the clump's heart
        length = rng.uniform(70, 120)
        leaf(draw, x, y, out, length, length * rng.uniform(.26, .34), rng.choice(GREENS), rng)
    # A soft edge on the alpha so the masked cut-out stays clean at a distance.
    alpha = image.getchannel('A').filter(ImageFilter.GaussianBlur(.7))
    image.putalpha(alpha)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(OUT, image.size)


if __name__ == '__main__':
    main()
