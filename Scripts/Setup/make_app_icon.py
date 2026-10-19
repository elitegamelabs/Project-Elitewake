"""Make the game's Windows icon (owner, October 19: a capital EW with a silver box around it; the program is called
Elite_Wake.exe). Writes Art/Branding/Elite_Wake-Icon-v1.png (1024 px) and Build/Windows/Application.ico (16 to 256 px),
which Unreal stamps on the packaged game and its window; the release packer stamps it on the downloadable EXE too.
Run with plain Python (Pillow): python Scripts/Setup/make_app_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PNG = ROOT / 'Art/Branding/Elite_Wake-Icon-v1.png'
ICO = ROOT / 'Build/Windows/Application.ico'
SIZE = 1024
FONTS = ('C:/Windows/Fonts/georgiab.ttf', 'C:/Windows/Fonts/timesbd.ttf')   # a bold Roman serif, like the title art


def silver(size, top=(246, 248, 252), mid=(160, 166, 176), low=(222, 226, 232), bottom=(118, 124, 134)):
    """A vertical brushed-silver gradient: bright top, darker band, highlight, dark foot."""
    im = Image.new('RGB', (1, size))
    stops = ((0.0, top), (0.45, mid), (0.62, low), (1.0, bottom))
    for y in range(size):
        t = y / (size - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0)
                im.putpixel((0, y), tuple(round(a + (b - a) * f) for a, b in zip(c0, c1)))
                break
    return im.resize((size, size))


def icon():
    s = SIZE
    base = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    # The silver box: a rounded square plate with a bevelled silver frame round a dark inner field.
    frame = Image.new('L', (s, s), 0)
    ImageDraw.Draw(frame).rounded_rectangle((24, 24, s - 24, s - 24), radius=120, fill=255)
    base.paste(silver(s), (0, 0), frame)
    inner = Image.new('L', (s, s), 0)
    ImageDraw.Draw(inner).rounded_rectangle((96, 96, s - 96, s - 96), radius=72, fill=255)
    field = Image.new('RGB', (s, s))
    fd = ImageDraw.Draw(field)
    for y in range(s):                                    # deep sea-night blue to near black
        t = y / s
        fd.line([(0, y), (s, y)], fill=(round(22 - 12 * t), round(30 - 16 * t), round(46 - 24 * t)))
    base.paste(field, (0, 0), inner)
    # A thin dark line where the frame meets the field, and a fine bright line inside it (the bevel's edge).
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((96, 96, s - 96, s - 96), radius=72, outline=(40, 44, 52, 255), width=8)
    d.rounded_rectangle((112, 112, s - 112, s - 112), radius=60, outline=(150, 156, 166, 255), width=3)
    # The capital EW in silver, with a soft shadow beneath.
    # Sized to sit inside the dark field with a margin all round (the field is 832 px across).
    path = next(f for f in FONTS if Path(f).exists())
    text = 'EW'
    size = 470
    while True:
        font = ImageFont.truetype(path, size)
        box = d.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= 640 and box[3] - box[1] <= 420:
            break
        size -= 10
    x = (s - (box[2] - box[0])) / 2 - box[0]
    y = (s - (box[3] - box[1])) / 2 - box[1]
    mask = Image.new('L', (s, s), 0)
    ImageDraw.Draw(mask).text((x, y), text, font=font, fill=255)
    shadow = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 200), (14, 18), mask)
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    letters = silver(s, top=(255, 255, 255), mid=(178, 184, 194), low=(236, 239, 244), bottom=(140, 146, 156))
    base.paste(letters, (0, 0), mask)
    return base


def main():
    im = icon()
    PNG.parent.mkdir(parents=True, exist_ok=True)
    ICO.parent.mkdir(parents=True, exist_ok=True)
    im.save(PNG)
    im.save(ICO, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(PNG, ICO)


if __name__ == '__main__':
    main()
