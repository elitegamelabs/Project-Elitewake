"""Draws the sextant's placeholder inventory icon (Part 8, 09): a brass frame and arc with its index arm and eyepiece on the
dark panel used by the armor icons. Plain Python with Pillow, from the repository root:
    python Scripts/Art/draw_sextant_icon.py
Writes Art/UI/Icons/Tools/T_Icon_Sextant.png (256 x 256). Original studio work; a placeholder until production icons.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Art' / 'UI' / 'Icons' / 'Tools' / 'T_Icon_Sextant.png'
S = 4                     # drawn large, then shrunk for smooth edges
BRASS, DARK, GLASS, PANEL = (196, 150, 70), (92, 64, 30), (120, 160, 170), (22, 21, 23)


def main():
    size = 256 * S
    img = Image.new('RGB', (size, size), PANEL)
    d = ImageDraw.Draw(img)
    apex = (size * .5, size * .16)
    r = size * .66
    left, right = math.radians(90 + 30), math.radians(90 - 30)
    p1 = (apex[0] + r * math.cos(left), apex[1] + r * math.sin(left))
    p2 = (apex[0] + r * math.cos(right), apex[1] + r * math.sin(right))
    # The frame: two radii and a crossbar.
    for a, b in ((apex, p1), (apex, p2), ((apex[0] - r * .32, apex[1] + r * .55), (apex[0] + r * .32, apex[1] + r * .55))):
        d.line([a, b], fill=BRASS, width=10 * S)
    # The graduated arc.
    box = [apex[0] - r, apex[1] - r, apex[0] + r, apex[1] + r]
    d.arc(box, 58, 122, fill=BRASS, width=22 * S)
    for k in range(25):
        ang = math.radians(60 + k * 2.5)
        o = (apex[0] + r * math.cos(ang), apex[1] + r * math.sin(ang))
        i = (apex[0] + (r - 18 * S) * math.cos(ang), apex[1] + (r - 18 * S) * math.sin(ang))
        d.line([i, o], fill=DARK, width=2 * S)
    # The index arm, swung a little, and its mirror at the pivot; the telescope across the frame.
    arm = math.radians(97)
    d.line([apex, (apex[0] + r * 1.02 * math.cos(arm), apex[1] + r * 1.02 * math.sin(arm))], fill=DARK, width=8 * S)
    d.rectangle([apex[0] - 14 * S, apex[1] - 22 * S, apex[0] + 14 * S, apex[1] + 6 * S], fill=GLASS, outline=DARK, width=3 * S)
    t0, t1 = (apex[0] - r * .42, apex[1] + r * .34), (apex[0] + r * .2, apex[1] + r * .34)
    d.line([t0, t1], fill=DARK, width=16 * S)
    d.ellipse([apex[0] - 10 * S, apex[1] - 10 * S, apex[0] + 10 * S, apex[1] + 10 * S], fill=BRASS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.resize((256, 256), Image.LANCZOS).save(OUT)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
