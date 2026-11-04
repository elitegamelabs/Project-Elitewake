"""Draw the canonical twenty-island layout as a reference picture. Safe to run again.
    python Scripts/Art/draw_world_layout.py
Writes Art/World/WorldLayout_TwentyIslands.png: every island's real outline in its region's colour, labelled, the region
names at their centres, each Port (site centre plus a quay line along its waterfront) and each cave mouth
(an arrow along its heading, coloured by kind), a legend, a 1 km scale bar and north up. A reference picture, not
the in-game map. Does not edit world_layout.py or world_terrain.py.
"""
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Scripts/Setup'))
import world_layout as W   # noqa: E402
import world_terrain as T  # noqa: E402

OUT = ROOT / 'Art/World/WorldLayout_TwentyIslands.png'
SIZE = 1600
COLOURS = {'Plains': (122, 160, 70), 'Winter': (225, 235, 245), 'Swamp': (90, 105, 60), 'Desert': (222, 196, 130),
           'Jungle': (40, 110, 60)}
PORT_COLOUR = (235, 60, 60)
CAVE_COLOURS = {'inland': (210, 170, 40), 'cliff': (160, 90, 220), 'coastal': (60, 190, 230),
                'sea': (60, 225, 235)}


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
    for i in W.ISLANDS:
        pts = [px(x, y) for x, y in i.outline(120)]
        draw.polygon(pts, fill=COLOURS[i.region], outline=(250, 240, 210))
        x_min, x_max = min(p[0] for p in pts), max(p[0] for p in pts)
        y_min = min(p[1] for p in pts)
        draw.text(((x_min + x_max) / 2, y_min - 34), i.region.upper(),
                  fill=(200, 220, 235), font=big, anchor='mm')
        x, y = px(i.cx, i.cy - i.reach())
        draw.text((x, y + 14), i.key + (' (start)' if i.key == 'Starter' else ''), fill=(240, 240, 240), font=font, anchor='mm')

    # Ports: the site centre as a square, a quay line along the waterfront.
    for region, port in W.PORTS.items():
        cx, cy = px(port.cx, port.cy)
        half = 7
        draw.rectangle([cx - half, cy - half, cx + half, cy + half], fill=PORT_COLOUR, outline=(255, 255, 255))
        sx, sy = px(*port.shore)
        qx, qy = port.world(0.0, 1800.0)
        qx2, qy2 = port.world(0.0, -1800.0)
        q1 = px(qx, qy)
        q2 = px(qx2, qy2)
        draw.line([q1, q2], fill=PORT_COLOUR, width=4)
        draw.text((cx, cy - 18), f'{region} Port', fill=PORT_COLOUR, font=font, anchor='mm')

    # Caves: an arrow from just outside the mouth, pointing in along heading, coloured by kind.
    for key, cave in T.CAVES.items():
        if not cave:
            continue
        colour = CAVE_COLOURS[cave.kind]
        mx, my = px(cave.mx, cave.my)
        tx, ty = px(*cave.world(600.0, 0.0))
        draw.line([(mx, my), (tx, ty)], fill=colour, width=3)
        # Arrowhead.
        ang = math.atan2(ty - my, tx - mx)
        for side in (-1, 1):
            a2 = ang + side * 2.6
            hx, hy = tx + 10 * math.cos(a2), ty + 10 * math.sin(a2)
            draw.line([(tx, ty), (hx, hy)], fill=colour, width=3)
        draw.ellipse([mx - 4, my - 4, mx + 4, my + 4], fill=colour, outline=(255, 255, 255))

    # Legend.
    lx, ly = 20, 20
    draw.text((lx, ly), 'Ports', fill=PORT_COLOUR, font=font, anchor='lm')
    ly += 22
    for kind, colour in CAVE_COLOURS.items():
        draw.line([(lx, ly), (lx + 26, ly)], fill=colour, width=3)
        draw.text((lx + 34, ly), f'{kind} cave', fill=(220, 230, 240), font=font, anchor='lm')
        ly += 20

    # Scale bar: 1 km.
    bx, by = 70, SIZE - 30
    draw.line([(bx, by), (bx + 1000 * W.M * scale, by)], fill=(255, 255, 255), width=4)
    draw.text((bx + 1000 * W.M * scale + 10, by), '1 km', fill=(255, 255, 255), font=font, anchor='lm')
    draw.text((SIZE - 70, 40), 'N  ↑', fill=(255, 255, 255), font=big, anchor='mm')
    problems, nearest = W.check(W.ISLANDS)
    gaps = sorted(nearest.values())
    cave_count = sum(1 for c in T.CAVES.values() if c)
    draw.text((SIZE - 20, SIZE - 30),
              f'{len(W.ISLANDS)} islands, {len(W.PORTS)} Ports, {cave_count} caves; '
              f'nearest shore-to-shore gaps {gaps[0] / W.M:.0f}-{gaps[-1] / W.M:.0f} m',
              fill=(220, 230, 240), font=font, anchor='rm')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(OUT, 'PASS' if not problems else problems)


if __name__ == '__main__':
    main()
