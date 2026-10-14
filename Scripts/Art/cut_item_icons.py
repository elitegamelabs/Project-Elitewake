"""Cut inventory icons out of the reviewed item atlases. Safe to run again.
    python Scripts/Art/cut_item_icons.py

Each icon is one cell of an atlas in Art/CATALOG.json. Objects overflow the atlas's equal cells, and the
backgrounds were removed by a generator that left a red and yellow fringe and stray specks, so each cut is cleaned:
  - the cell is widened, and only the pieces whose centre lies in it are kept (not a neighbour's overhang),
  - specks and the thin fringe are opened and eroded away from the alpha,
  - the edge band takes its colour from the object's own interior, never from the fringe,
  - the object is trimmed, centred and scaled into a 256 px transparent square.
Writes Art/Items/Icons/<Name>-v1.png and Art/Items/Icons/contact-sheet.png for review. Art only: which item
uses which icon is set in Scripts/Setup/import_item_icons.py.
"""
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Art/Items/Icons'
SIZE, MARGIN = 256, 14
ATLASES = 'Art/Items/Atlases/2026-10-14'

# (icon name, atlas file, slot index). Names describe the picture, not an item's balance or recipe.
ICONS = [
    ('Wood', 'Core-Resources-Atlas-v1.png', 0), ('Thatch', 'Core-Resources-Atlas-v1.png', 1),
    ('Fiber', 'Core-Resources-Atlas-v1.png', 2), ('Stone', 'Core-Resources-Atlas-v1.png', 3),
    ('Sticks', 'Core-Resources-Atlas-v1.png', 4),
    ('AzrenBerry', 'forage1-Atlas-v1.png', 7), ('SpoiledBerries', 'medicine-Atlas-v1.png', 7),
    ('Hide', 'Animal-Marine-Materials-Atlas-v1.png', 0), ('CopperOre', 'Metal-Ores-Atlas-v1.png', 0),
    ('WoodenAxe', 'Portable-Tools-Atlas-v1.png', 0), ('WoodenPickaxe', 'Portable-Tools-Atlas-v1.png', 1),
    ('WoodenShovel', 'Portable-Tools-Atlas-v1.png', 2), ('WaterSkin', 'Portable-Tools-Atlas-v1.png', 3),
    ('StoneAxe', 'Portable-Tools-Atlas-v1.png', 4), ('StonePickaxe', 'Portable-Tools-Atlas-v1.png', 5),
    ('Torch', 'Portable-Tools-Atlas-v1.png', 10), ('RepairKit', 'Portable-Tools-Atlas-v1.png', 11),
    ('ShipWheel', 'fittings-Atlas-v1.png', 0), ('Cannon', 'fittings-Atlas-v1.png', 1),
    ('SmallSail', 'fittings-Atlas-v1.png', 4), ('MediumSail', 'fittings-Atlas-v1.png', 5),
    ('LargeSail', 'fittings-Atlas-v1.png', 6), ('CannonAmmo', 'ammo-Atlas-v1.png', 5),
]


def cell(atlas, index):
    """The cell, widened by a third on every side: objects overflow the atlas's equal cells. Returns the widened
    crop and the cell's own box inside it."""
    entry = next(e for e in json.loads((ROOT / 'Art/CATALOG.json').read_text(encoding='utf-8'))['assets']
                 if e['path'].endswith(f'{ATLASES}/{atlas}'))
    slot = next(i for i in entry['items'] if i['index'] == index)
    image = Image.open(ROOT / entry['path']).convert('RGBA')
    w, h = image.size
    (u0, v0), (u1, v1) = slot['uv']['min'], slot['uv']['max']
    x0, y0, x1, y1 = round(u0 * w), round(v0 * h), round(u1 * w), round(v1 * h)
    pad_x, pad_y = (x1 - x0) // 3, (y1 - y0) // 3
    X0, Y0, X1, Y1 = max(0, x0 - pad_x), max(0, y0 - pad_y), min(w, x1 + pad_x), min(h, y1 + pad_y)
    return image.crop((X0, Y0, X1, Y1)), (x0 - X0, y0 - Y0, x1 - X0, y1 - Y0)


def own_pieces(solid, box):
    """Keep the connected pieces whose centre lies in the cell: the object, not its neighbours' overhang or specks.
    Pieces under 2% of the largest such piece are dropped as specks."""
    w, h = solid.size
    px = solid.load()
    seen = bytearray(w * h)
    pieces = []
    for sy in range(h):
        for sx in range(w):
            if px[sx, sy] != 255 or seen[sy * w + sx]:
                continue
            stack, members = [(sx, sy)], []
            seen[sy * w + sx] = 1
            while stack:
                x, y = stack.pop()
                members.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny] == 255:
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
            cx = sum(m[0] for m in members) / len(members)
            cy = sum(m[1] for m in members) / len(members)
            if box[0] <= cx < box[2] and box[1] <= cy < box[3]:
                pieces.append(members)
    keep = Image.new('L', solid.size, 0)
    if pieces:
        largest = max(len(m) for m in pieces)
        kpx = keep.load()
        for members in pieces:
            if len(members) >= largest * .02:
                for x, y in members:
                    kpx[x, y] = 255
    return keep


def clean(image, box):
    rgb, alpha = image.convert('RGB'), image.getchannel('A')
    solid = alpha.point(lambda v: 255 if v > 128 else 0)
    # Opening drops specks smaller than the filter; a further erosion removes the fringe band.
    solid = solid.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    solid = own_pieces(solid, box)
    interior = solid.filter(ImageFilter.MinFilter(7))
    # The edge takes the interior's colour: blur colour weighted by the interior and divide by the blurred weight.
    weighted = ImageChops.multiply(rgb, Image.merge('RGB', (interior,) * 3)).filter(ImageFilter.GaussianBlur(4))
    weight = interior.filter(ImageFilter.GaussianBlur(4))
    px, wpx, ipx, spx = rgb.load(), weighted.load(), weight.load(), interior.load()
    for y in range(rgb.size[1]):
        for x in range(rgb.size[0]):
            if spx[x, y] == 255:
                continue
            k = ipx[x, y]
            if k > 8:
                r, g, b = wpx[x, y]
                px[x, y] = (min(255, r * 255 // k), min(255, g * 255 // k), min(255, b * 255 // k))
    out = rgb.copy()
    out.putalpha(solid.filter(ImageFilter.GaussianBlur(0.8)))
    return out


def fit(image):
    box = image.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
    image = image.crop(box)
    scale = (SIZE - 2 * MARGIN) / max(image.size)
    image = image.resize((max(1, round(image.size[0] * scale)), max(1, round(image.size[1] * scale))), Image.LANCZOS)
    square = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    square.alpha_composite(image, ((SIZE - image.size[0]) // 2, (SIZE - image.size[1]) // 2))
    return square


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, atlas, index in ICONS:
        icon = fit(clean(*cell(atlas, index)))
        icon.save(OUT / f'{name}-v1.png')
        made.append((name, icon))
    columns = 6
    sheet = Image.new('RGBA', (columns * SIZE, -(-len(made) // columns) * SIZE), (38, 44, 52, 255))
    for k, (_, icon) in enumerate(made):
        sheet.alpha_composite(icon, ((k % columns) * SIZE, (k // columns) * SIZE))
    sheet.save(OUT / 'contact-sheet.png')
    print(f'{len(made)} icons in {OUT}')


if __name__ == '__main__':
    main()
