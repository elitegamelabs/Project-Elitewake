"""Inventory icons for the nine armor pieces (owner, November 8), cut from the owner's three concept sheets in
Art/Reference/Armor: each sheet's front view of its helmet, chest piece and pants, set on the dark panel on a square.
Plain Python with Pillow; run from the repository root:
    python Scripts/Art/make_armor_icons.py
Writes Art/UI/Icons/Armor/T_Icon_<Piece>.png (256 x 256). The sheets are references, not finished art; these icons stand
until production icons are made from the production garments.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SHEETS = ROOT / 'Art' / 'Reference' / 'Armor'
OUT = ROOT / 'Art' / 'UI' / 'Icons' / 'Armor'
SIZE = 256
PANEL = (22, 21, 23)   # the sheets' dark panel

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
        image = Image.open(SHEETS / sheet).convert('RGB').crop(box)
        # Fitted inside a square of the sheet's own dark panel colour, keeping its proportions.
        scale = (SIZE - 16) / max(image.size)
        image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
        square = Image.new('RGB', (SIZE, SIZE), PANEL)
        square.paste(image, ((SIZE - image.width) // 2, (SIZE - image.height) // 2))
        square.save(OUT / f'T_Icon_{piece}.png')
        print('wrote', piece)


if __name__ == '__main__':
    main()
