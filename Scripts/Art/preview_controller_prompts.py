"""Preview-only (run extract_controller_icons.py first): example prompts with the extracted icons at their in-game size (1920x1080; the arrival prompt is 28 px text on a
dark plate), over a real gameplay screenshot. Nothing goes into the game."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parents[2] / 'Saved' / 'ControllerIconPreview'
ICONS = HERE / 'icons'
BG = Path(r'C:\UnrealProjects\EW_CLEAN\Saved\Screenshots\VoyageReady\01_boat_prompt00000.png')
canvas = Image.open(BG).convert('RGBA')
d = ImageDraw.Draw(canvas)
font = ImageFont.truetype('arial.ttf', 28)
small = ImageFont.truetype('arial.ttf', 18)


def icon(name, height):
    im = Image.open(ICONS / f'T_Icon_{name}.png')
    return im.resize((round(im.width * height / im.height), height), Image.LANCZOS)


def prompt(y, parts, label):
    """parts: strings and ('icon', name) pairs; drawn centred on a dark plate like the game's prompt."""
    h = 44
    pieces = [(p, icon(p[1], h)) if isinstance(p, tuple) else (p, None) for p in parts]
    width = sum(img.width + 6 if img else d.textlength(p, font=font) + 6 for p, img in pieces) + 30
    x = (canvas.width - width) // 2
    d.rectangle([x, y, x + width, y + h + 14], fill=(20, 24, 28, 210))
    d.text((x - 250, y + 16), label, fill=(255, 220, 120, 255), font=small)
    cx = x + 15
    for p, img in pieces:
        if img:
            canvas.alpha_composite(img, (int(cx), y + 7))
            cx += img.width + 6
        else:
            d.text((cx, y + 13), p, fill=(255, 255, 255, 255), font=font)
            cx += d.textlength(p, font=font) + 6


prompt(330, ['Hold', ('icon', 'Xbox_LB'), '+', ('icon', 'Xbox_DPad_Right'), ': build'], 'Xbox (44 px icons)')
prompt(410, ['Hold', ('icon', 'PlayStation_L1'), '+', ('icon', 'PlayStation_DPad_Right'), ': build'], 'PlayStation')
prompt(490, ['B : build'], 'Keyboard')
prompt(570, [('icon', 'Xbox_X'), ': buy your first boat from Elias Thorne'], 'Xbox interact')
prompt(650, [('icon', 'PlayStation_Square'), ': buy your first boat from Elias Thorne'], 'PlayStation interact')
prompt(730, [('icon', 'Xbox_RightStickPress'), ': demolish    ', ('icon', 'PlayStation_R3'), ': demolish'], 'R3 at 44 px')
# The smallest use: the hotbar's 18 px key hints, here at 26 px icons.
for i, name in enumerate(['DPad_Left', 'DPad_Up', 'DPad_Right', 'DPad_Down', 'X', 'Y', 'B', 'A']):
    canvas.alpha_composite(icon(f'Xbox_{name}', 26), (676 + i * 73, 958))
canvas.save(HERE / 'prompt_preview_1080p.png')
print('ok')
