"""Draw the world layout (Scripts/Setup/world_layout.py) as a map picture for the docs. Safe to run again.
    python Scripts/Art/draw_world_layout.py
Writes Docs/images/world_layout_v1.png: every island's real outline in its region's colour, labelled, the region
names at their centres, a 1 km scale bar and north up. A reference picture, not the in-game map.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Scripts/Setup'))
import world_layout as W  # noqa: E402

OUT = ROOT / 'Docs/images/world_layout_v1.png'
SIZE = 1600
COLOURS = {'Plains': (122, 160, 70), 'Winter': (225, 235, 245), 'Swamp': (90, 105, 60), 'Desert': (222, 196, 130),
           'Jungle': (40, 110, 60)}


def main():
    x0, x1, y0, y1 = W.bounds(800 * W.M)
    span = max(x1 - x0, y1 - y0)
    scale = (SIZE - 120) / span

    def px(x, y):   # north (+Y) up
        return 60 + (x - x0) * scale, SIZE - 60 - (y - y0) * scale

    image = Image.new('RGB', (SIZE, SIZE), (24, 58, 92))
    draw = ImageDraw.Draw(image)
    try:
        font, big = ImageFont.truetype('arial.ttf', 15), ImageFont.truetype('arialbd.ttf', 30)
    except OSError:
        font = big = ImageFont.load_default()
    for region, (cx, cy) in W.REGION_CENTRES.items():
        x, y = px(cx, cy)
        draw.text((x, y - 170 if region != 'Swamp' else y + 150), region.upper(), fill=(200, 220, 235), font=big, anchor='mm')
    for i in W.ISLANDS:
        pts = [px(x, y) for x, y in i.outline(120)]
        draw.polygon(pts, fill=COLOURS[i.region], outline=(250, 240, 210))
        x, y = px(i.cx, i.cy - i.reach())
        draw.text((x, y + 14), i.key + (' (start)' if i.key == 'Starter' else ''), fill=(240, 240, 240), font=font, anchor='mm')
    # Scale bar: 1 km.
    bx, by = 70, SIZE - 30
    draw.line([(bx, by), (bx + 1000 * W.M * scale, by)], fill=(255, 255, 255), width=4)
    draw.text((bx + 1000 * W.M * scale + 10, by), '1 km', fill=(255, 255, 255), font=font, anchor='lm')
    draw.text((SIZE - 70, 40), 'N  ↑', fill=(255, 255, 255), font=big, anchor='mm')
    problems, nearest = W.check(W.ISLANDS)
    gaps = sorted(nearest.values())
    draw.text((SIZE - 20, SIZE - 30), f'{len(W.ISLANDS)} islands; nearest shore-to-shore gaps {gaps[0] / W.M:.0f}-{gaps[-1] / W.M:.0f} m',
              fill=(220, 230, 240), font=font, anchor='rm')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(OUT, 'PASS' if not problems else problems)


if __name__ == '__main__':
    main()
