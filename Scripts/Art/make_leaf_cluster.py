"""Draw the foliage cards: the Maravai's and the birch's leaves and the Jungle spruce's needle sprays. Safe to run again.
Run with ordinary Python (Pillow), outside Unreal:
    python Scripts/Art/make_leaf_cluster.py

Also writes Art/Flora/Birch-Leaves-v1.png: the same kind of card of small, finely pointed birch leaves in yellowing
greens, sparser, for the Winter island's birches (owner, October 14: Winter has birch trees).
Writes Art/Flora/Maravai-Leaves-v1.png: a 1024 px square of overlapping glossy tropical leaves on transparency,
thickest in the middle and thinning to single leaves at the edge, so crossed cards of it read as a leafy clump.
Each leaf is a pointed oval with a pale midrib, lit from above (lighter tips, darker bases), in several greens.
Scripts/Setup/build_coastal_flora.py imports it.

Also writes, for the regional trees (owner, October 15: Central Plains Oak, Jungle Ash): Art/Flora/Oak-Leaves-v1.png,
a card of deep-green lobed oak leaves, and Art/Flora/Ash-Leaves-v1.png, a card of ash's compound leaves, each a stalk
with pairs of narrow pointed leaflets and one at its tip.
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


def oak_leaf(draw, x, y, angle, length, width, colour, rng):
    """A lobed oak leaf: the outline swells and pinches in rounded lobes along both sides, shaded like the others."""
    ca, sa = math.cos(angle), math.sin(angle)
    lobes = rng.choice((4, 5))
    for band in range(10, 0, -1):
        f = band / 10
        shade = .7 + .38 * (1 - f) + rng.uniform(-.04, .04)
        fill = tuple(max(0, min(255, int(c * shade))) for c in colour) + (255,)
        side = []
        for k in range(41):
            t = k / 40
            lobe = .62 + .38 * abs(math.sin(math.pi * lobes * t))
            side.append((t * length, width * f * math.sin(math.pi * t) ** .6 * lobe * (1 - .2 * t)))
        pts = side + [(px, -py) for px, py in reversed(side)]
        draw.polygon([(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts], fill=fill)
    rib = tuple(min(255, int(c * 1.4)) for c in colour) + (255,)
    draw.line([(x, y), (x + length * .9 * ca, y + length * .9 * sa)], fill=rib, width=2)


OAK_OUT = ROOT / 'Art/Flora/Oak-Leaves-v1.png'
OAK_GREENS = [(40, 78, 28), (52, 92, 32), (34, 68, 24), (62, 100, 36), (46, 84, 40)]


def oak_card(out=OAK_OUT, seed=17):
    rng = random.Random(seed)
    image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    leaves = sorted(((rng.random() ** .7) * SIZE * .42, rng.uniform(0, 2 * math.pi)) for _ in range(300))
    for r, a in reversed(leaves):
        length = rng.uniform(80, 120)
        oak_leaf(draw, SIZE / 2 + r * math.cos(a), SIZE / 2 + r * math.sin(a), a + rng.uniform(-.7, .7), length,
                 length * rng.uniform(.3, .38), rng.choice(OAK_GREENS), rng)
    image.putalpha(image.getchannel('A').filter(ImageFilter.GaussianBlur(.7)))
    image.save(out)
    print(out, image.size)


ASH_OUT = ROOT / 'Art/Flora/Ash-Leaves-v1.png'
ASH_GREENS = [(64, 110, 42), (76, 124, 48), (56, 98, 38), (88, 132, 54)]


def ash_card(out=ASH_OUT, seed=19):
    rng = random.Random(seed)
    image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    stalks = sorted(((rng.random() ** .8) * SIZE * .3, rng.uniform(0, 2 * math.pi)) for _ in range(46))
    for r, a in reversed(stalks):
        x0, y0 = SIZE / 2 + r * math.cos(a), SIZE / 2 + r * math.sin(a)
        heading = a + rng.uniform(-.5, .5)
        length = rng.uniform(150, 230)
        colour = rng.choice(ASH_GREENS)
        ca, sa = math.cos(heading), math.sin(heading)
        draw.line([(x0, y0), (x0 + length * ca, y0 + length * sa)], fill=(70, 86, 40, 255), width=3)
        pairs = rng.choice((3, 4, 5))
        for k in range(pairs):
            t = .25 + .7 * k / pairs
            px, py = x0 + length * t * ca, y0 + length * t * sa
            for side in (-1, 1):
                leaf(draw, px, py, heading + side * rng.uniform(.9, 1.2), rng.uniform(46, 62), 7.5, colour, rng)
        leaf(draw, x0 + length * ca, y0 + length * sa, heading, rng.uniform(50, 64), 8.0, colour, rng)
    image.putalpha(image.getchannel('A').filter(ImageFilter.GaussianBlur(.6)))
    image.save(out)
    print(out, image.size)


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
    oak_card()
    ash_card()
