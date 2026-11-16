"""Publish the approved transparent cutouts for the nine existing clothing icons.
Copies existing raster artwork without regenerating, resizing or changing pixels:
    python Scripts/Art/make_armor_icons.py
The original RGB crop generator painted an opaque square behind every garment. Curated RGBA cutouts now live in
Art/UI/Icons/Armor/Transparent. Missing/opaque cutouts fail clearly instead of silently rebuilding those backgrounds.
The old crop coordinates below remain as provenance; the concept sheets and recovery copies are preserved.
"""
from pathlib import Path
from PIL import Image
import shutil

ROOT = Path(__file__).resolve().parents[2]
SHEETS = ROOT / 'Art' / 'Reference' / 'Armor'
OUT = ROOT / 'Art' / 'UI' / 'Icons' / 'Armor'
SIZE = 256
CURATED = OUT / 'Transparent'

# (sheet, piece, crop box in the 1536 x 1024 sheet: left, top, right, bottom)
CROPS = [
    ('EW_Armor_Cloth_Sheet.webp', 'ClothHeadWrap', (916, 186, 1098, 393)),
    ('EW_Armor_Cloth_Sheet.webp', 'ClothChest', (920, 420, 1124, 628)),
    ('EW_Armor_Cloth_Sheet.webp', 'ClothPants', (912, 652, 1100, 1000)),
    ('EW_Armor_Fur_Sheet.webp', 'FurHood', (560, 64, 750, 283)),
    ('EW_Armor_Fur_Sheet.webp', 'FurJacket', (556, 312, 785, 606)),
    ('EW_Armor_Fur_Sheet.webp', 'FurPants', (568, 628, 752, 1005)),
    ('EW_Armor_Metal_Sheet.webp', 'MetalTricornHelmet', (888, 206, 1084, 377)),
    ('EW_Armor_Metal_Sheet.webp', 'MetalCuirass', (898, 402, 1104, 627)),
    ('EW_Armor_Metal_Sheet.webp', 'MetalPants', (898, 650, 1078, 985)),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for sheet, piece, box in CROPS:
        source = CURATED / f'T_Icon_{piece}.png'
        with Image.open(source) as image:
            assert image.mode == 'RGBA', f'{piece}: expected RGBA'
            assert image.getchannel('A').getextrema() == (0, 255), f'{piece}: missing cutout alpha'
            assert all(image.getpixel(at)[3] == 0 for at in ((0, 0), (image.width-1, 0),
                       (0, image.height-1), (image.width-1, image.height-1))), f'{piece}: opaque corner'
        shutil.copy2(source, OUT / source.name)
        print('published transparent icon', piece)


if __name__ == '__main__':
    main()
