"""Draw the foliage cards: the Maravai's and the birch's leaves and the Jungle spruce's needle sprays. Safe to run again.
Run with ordinary Python (Pillow), outside Unreal:
    python Scripts/Art/make_leaf_cluster.py

Also writes Art/Flora/Birch-Leaves-v1.png: the same kind of card of small, finely pointed birch leaves in yellowing
greens, sparser, for the Winter island's birches (owner, October 14: Winter has birch trees).
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
BIRCH_OUT = ROOT / 'Art/Flora/Birch-Leaves-v1.png'
BIRCH_GREENS = [(118, 132, 52), (138, 140, 58), (96, 118, 46), (160, 150, 66), (126, 126, 48), (170, 138, 52)]
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


def main(out=OUT, greens=GREENS, count=420, sizes=(70, 120), seed=7, widths=(.26, .34)):
    rng = random.Random(seed)
    image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    centre = SIZE / 2
    # Leaves farther out are drawn first so the clump's heart sits on top; fewer leaves toward the edge.
    leaves = []
    for _ in range(count):
        r = (rng.random() ** .75) * SIZE * .42
        a = rng.uniform(0, 2 * math.pi)
        leaves.append((r, a))
    for r, a in sorted(leaves, reverse=True):
        x, y = centre + r * math.cos(a), centre + r * math.sin(a)
        out_angle = a + rng.uniform(-.7, .7)        # leaves point roughly away from the clump's heart
        length = rng.uniform(*sizes)
        leaf(draw, x, y, out_angle, length, length * rng.uniform(*widths), rng.choice(greens), rng)
    # A soft edge on the alpha so the masked cut-out stays clean at a distance.
    alpha = image.getchannel('A').filter(ImageFilter.GaussianBlur(.7))
    image.putalpha(alpha)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    print(out, image.size)


SPRUCE_OUT = ROOT / 'Art/Flora/Spruce-Needles-v1.png'


def spruce_spray(out=SPRUCE_OUT, seed=13):
    """A spruce branch spray seen from above: a twig from the left edge's middle to the right, side twigs off it, all
    bristling with short dark needles, thinning toward the tip. Cards of it make the Jungle's spruce boughs."""
    rng = random.Random(seed)
    image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    greens = [(22, 52, 30), (30, 64, 36), (18, 44, 26), (38, 74, 42), (26, 58, 34)]

    def twig(x0, y0, angle, length, width, depth):
        # The twig first, so its needles lie over it.
        draw.line([(x0, y0), (x0 + math.cos(angle) * length, y0 + math.sin(angle) * length)], fill=(58, 40, 24, 255), width=max(2, int(width)))
        steps = int(length / 5)
        for k in range(steps):
            t = k / max(steps - 1, 1)
            x, y = x0 + math.cos(angle) * length * t, y0 + math.sin(angle) * length * t
            reach = (1 - t * .5) * (46 if depth == 0 else 30)
            for side in (-1, 1):
                for _ in range(4):
                    a = angle + side * rng.uniform(.45, 1.25)
                    l = reach * rng.uniform(.55, 1.0)
                    c = rng.choice(greens)
                    draw.line([(x, y), (x + math.cos(a) * l, y + math.sin(a) * l)], fill=c + (255,), width=4)
            if depth == 0 and k % 6 == 3 and t < .85:
                twig(x, y, angle + rng.choice((-1, 1)) * rng.uniform(.45, .8), length * (1 - t) * rng.uniform(.4, .6), width * .6, 1)

    twig(8, SIZE / 2, 0.0, SIZE * .95, 9, 0)
    alpha = image.getchannel('A').filter(ImageFilter.GaussianBlur(.6))
    image.putalpha(alpha)
    image.save(out)
    print(out, image.size)


if __name__ == '__main__':
    main()
    main(BIRCH_OUT, BIRCH_GREENS, 380, (34, 56), 11, (.3, .4))
    spruce_spray()
