"""Draw the whole world for the Freeport choice screen (owner, November 7: after Single Player, a wide rectangle showing
every island, each Freeport selectable). Safe to run again:
    python Scripts/Art/draw_port_select_map.py
Writes Art/UI/FrontEnd/WorldMap_PortSelect.png (3200 x 1440, north up, wider than any screen's box): every island's real ground from world_terrain,
hill-shaded in its region's palette (CLAUDE.md 9.1), shallow water lighter near the coasts, the open sea deep blue, and
a faint chart grid. No text: names and the port markers are drawn by the game (UEWPortSelectWidget), which places
them with the world rectangle printed here (WORLD_RECT_CM, also in EWPortSelectWidget.h).
"""
import math
import sys
from multiprocessing import Pool
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Scripts/Setup'))
import world_layout as W   # noqa: E402

OUT = ROOT / 'Art/UI/FrontEnd/WorldMap_PortSelect.png'
WIDTH, HEIGHT = 3200, 1440
# The world rectangle shown, in cm: the islands' bounds with a margin of sea, widened to the picture's shape.
HALF_Y = 1800000.0
HALF_X = HALF_Y * WIDTH / HEIGHT
CM_PER_PX = 2 * HALF_Y / HEIGHT
DEEP = (12, 38, 66)
SHALLOW = (46, 112, 132)
REGION = {'Plains': ((113, 131, 77), (150, 140, 100)), 'Winter': ((105, 121, 135), (226, 230, 234)),
          'Swamp': ((89, 96, 58), (70, 78, 48)), 'Desert': ((183, 122, 61), (200, 160, 105)),
          'Jungle': ((36, 75, 54), (64, 96, 70))}
SAND = (214, 199, 168)


def to_px(x, y):
    return (x + HALF_X) / CM_PER_PX, (HALF_Y - y) / CM_PER_PX


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def island_tile(index):
    """The pixels around one island: (left, top, width, height, rgba bytes)."""
    import world_terrain as T   # noqa: E402  (heavy; imported in each worker)
    i = W.ISLANDS[index]
    reach = i.reach() + 600 * W.M          # with its shallows
    left, top = to_px(i.cx - reach, i.cy + reach)
    right, bottom = to_px(i.cx + reach, i.cy - reach)
    left, top, right, bottom = int(left), int(top), int(math.ceil(right)), int(math.ceil(bottom))
    w, h = right - left, bottom - top
    heights = [[0.0] * (w + 1) for _ in range(h + 1)]
    for py in range(h + 1):
        y = HALF_Y - (top + py + .5) * CM_PER_PX
        for px in range(w + 1):
            x = (left + px + .5) * CM_PER_PX - HALF_X
            heights[py][px] = T.height(x, y)
    low, high = REGION[i.region]
    outline = [to_px(x, y) for x, y in i.outline(180)]
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).polygon([(x - left, y - top) for x, y in outline], fill=255)
    inside = mask.load()
    peak = max(max(r) for r in heights) or 1.0
    out = bytearray()
    for py in range(h):
        for px in range(w):
            z = heights[py][px]
            if z <= 0 and inside[px, py]:
                # Inland water: the Swamp's river and pools, lakes and ponds.
                colour = (52, 66, 50) if i.region == 'Swamp' else (40, 92, 112)
                alpha = 255
            elif z <= 0:
                depth = -z
                colour = lerp(SHALLOW, DEEP, depth / 3000.0)
                alpha = int(255 * max(0.0, 1 - depth / 4000.0))
            else:
                # Hill shade from the north-west.
                dzx = heights[py][px + 1] - z
                dzy = heights[py + 1][px] - z
                shade = 1.0 + (-dzx + dzy) / CM_PER_PX * 1.6
                beach = 40.0 if i.region == 'Swamp' else 250.0      # the marsh is low: little of it is beach
                base = lerp(low, high, (z / peak) ** 1.3) if z > beach else lerp(SAND, low, z / beach)
                if i.region == 'Winter' and z > peak * .55:
                    base = lerp(base, (236, 238, 240), (z / peak - .55) / .3)
                colour = tuple(int(max(0, min(255, c * shade))) for c in base)
                alpha = 255
            out += bytes((*colour, alpha))
    tile = Image.frombytes('RGBA', (w, h), bytes(out))
    if i.region == 'Swamp':
        tile = tile.filter(ImageFilter.MedianFilter(5))
    return left, top, w, h, tile.tobytes()


def main():
    image = Image.new('RGB', (WIDTH, HEIGHT), DEEP)
    draw = ImageDraw.Draw(image)
    # Faint chart grid every 2 km.
    step = 200000.0
    for k in range(-20, 21):
        x, _ = to_px(k * step, 0)
        _, y = to_px(0, k * step)
        draw.line([(x, 0), (x, HEIGHT)], fill=(20, 50, 80), width=1)
        draw.line([(0, y), (WIDTH, y)], fill=(20, 50, 80), width=1)
    with Pool() as pool:
        tiles = pool.map(island_tile, range(len(W.ISLANDS)))
    for left, top, w, h, data in tiles:
        tile = Image.frombytes('RGBA', (w, h), data)
        image.paste(tile, (left, top), tile)
    # Soft vignette toward the edges, as on an old chart.
    shade = Image.new('L', (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(shade).rectangle([60, 60, WIDTH - 60, HEIGHT - 60], fill=255)
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    image = Image.composite(image, Image.new('RGB', (WIDTH, HEIGHT), (6, 20, 36)), shade)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print('wrote', OUT, 'world rect cm', -HALF_X, -HALF_Y, HALF_X, HALF_Y)


if __name__ == '__main__':
    main()
