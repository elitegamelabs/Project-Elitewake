"""Draw the Campfire item's inventory icon (Phase 1 slice 3): a ring of grey stones round crossed logs with a low flame, seen a
little from above, on a transparent ground; no text (CLAUDE.md 9.2). Plain Python with Pillow, so the picture is original.
Writes Art/Items/Icons/Campfire-v1.png (512 x 512, RGBA). Shapes and colours are tuning.
    python Scripts/Art/make_campfire_icon.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SIZE = 512
OUT = Path(__file__).resolve().parents[2] / 'Art' / 'Items' / 'Icons' / 'Campfire-v1.png'
rng = random.Random(33)


def main():
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = SIZE / 2, SIZE * .62
    # Ash bed.
    d.ellipse((cx - 150, cy - 55, cx + 150, cy + 55), fill=(38, 32, 28, 255))
    # Back stones first, front stones last, so the ring overlaps itself as seen from above.
    stones = []
    for k in range(11):
        a = 2 * math.pi * k / 11 + rng.uniform(-.1, .1)
        x, y = cx + 175 * math.cos(a), cy + 70 * math.sin(a)
        r = rng.uniform(34, 46)
        tone = rng.randint(118, 160)
        stones.append((y, x, r, tone))
    back = [s for s in stones if s[0] <= cy]
    front = [s for s in stones if s[0] > cy]
    for y, x, r, tone in sorted(back):
        d.ellipse((x - r, y - r * .7, x + r, y + r * .7), fill=(tone, tone - 8, tone - 22, 255), outline=(60, 55, 50, 255), width=4)
    # Logs crossed over the ash.
    for a, length in ((.35, 230), (-.35, 230), (1.25, 170)):
        dx, dy = math.cos(a) * length / 2, math.sin(a) * length / 2 * .45
        d.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=(84, 58, 38, 255), width=34)
        d.line((cx - dx, cy - dy - 6, cx + dx, cy + dy - 6), fill=(112, 80, 52, 255), width=10)
    # The flame: outer orange, inner yellow, softened.
    flame = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    f = ImageDraw.Draw(flame)
    f.polygon([(cx - 85, cy - 10), (cx - 40, cy - 150), (cx - 10, cy - 95), (cx + 20, cy - 230), (cx + 50, cy - 120),
               (cx + 85, cy - 10)], fill=(232, 112, 36, 255))
    f.polygon([(cx - 45, cy - 12), (cx - 10, cy - 105), (cx + 18, cy - 150), (cx + 45, cy - 12)], fill=(250, 196, 82, 255))
    img.alpha_composite(flame.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(img)
    for y, x, r, tone in sorted(front):
        d.ellipse((x - r, y - r * .7, x + r, y + r * .7), fill=(tone, tone - 8, tone - 22, 255), outline=(60, 55, 50, 255), width=4)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(OUT.name)


if __name__ == '__main__':
    main()
