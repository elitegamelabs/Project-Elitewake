"""Draw the Veyran Palm frond texture: a feather palm leaf seen flat, its leaflets cut out by alpha.
Runs in ordinary Python with Pillow (not in Unreal):
    python Scripts/Art/make_palm_frond.py
Writes Art/Flora/Veyran-Palm-Frond-v1.png (2048 x 512). The rachis (the leaf's stem) runs along the image from
the base at the left to the tip at the right, through the middle; U runs along the frond, V across it.
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

W, H = 2048, 512
SCALE = 2                      # drawn at twice the size, then reduced, for smooth edges
OUT = Path(__file__).resolve().parents[2] / 'Art' / 'Flora' / 'Veyran-Palm-Frond-v1.png'


def main():
    random.seed(7)
    w, h = W * SCALE, H * SCALE
    img = Image.new('RGBA', (w, h), (58, 82, 34, 0))
    d = ImageDraw.Draw(img)
    mid = h / 2
    # Leaflets: paired along the rachis, swept toward the tip, longest a little past the middle of the frond.
    count = 96
    for i in range(count):
        u = 0.05 + 0.93 * i / (count - 1)
        reach = math.sin(math.pi * min(1.0, u * 1.05)) ** 0.7 * (0.47 * h) * (0.85 + 0.3 * random.random())
        if u > 0.9:
            reach *= (1.0 - u) / 0.1 * 0.8 + 0.2
        for side in (-1, 1):
            x0 = u * w
            sweep = math.radians(38 + 10 * random.random())          # angle from the rachis toward the tip
            droop = 0.08 * random.random()
            dx, dy = math.cos(sweep) * reach, math.sin(sweep) * reach
            width = (15 + 8 * random.random()) * SCALE * (0.6 + 0.4 * math.sin(math.pi * u))
            # A narrow blade: wide at its base on the rachis, curving and tapering to a point.
            pts = []
            for k in range(9):
                t = k / 8
                cx = x0 + dx * t + droop * reach * t * t
                cy = mid + side * dy * t
                half = width * (1 - t) ** 0.8 / 2
                pts.append((cx - half * 0.5, cy - side * half))
            for k in range(8, -1, -1):
                t = k / 8
                cx = x0 + dx * t + droop * reach * t * t
                cy = mid + side * dy * t
                half = width * (1 - t) ** 0.8 / 2
                pts.append((cx + half * 0.5, cy + side * half))
            g = random.randint(-14, 14)
            dry = random.random() < 0.08
            base = (78 + g, 112 + g, 38 + g // 2) if not dry else (128 + g, 112 + g, 58)
            d.polygon(pts, fill=base + (255,))
            # A lighter midline down each leaflet.
            d.line([(x0, mid), (x0 + dx * 0.9, mid + side * dy * 0.9)], fill=(min(255, base[0] + 30), min(255, base[1] + 34), base[2] + 10, 255), width=SCALE)
    # The rachis itself, thick at the base and tapering to the tip.
    for k in range(200):
        t0, t1 = k / 200, (k + 1) / 200
        d.line([(t0 * w, mid), (t1 * w, mid)], fill=(112, 104, 58, 255), width=max(1, int((16 * (1 - t0) + 3) * SCALE)))
    img = img.filter(ImageFilter.GaussianBlur(0.6)).resize((W, H), Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(OUT)


if __name__ == '__main__':
    main()
