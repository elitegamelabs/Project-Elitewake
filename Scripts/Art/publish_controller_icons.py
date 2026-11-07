"""Turn the extracted controller icons (Scripts/Art/extract_controller_icons.py, Saved/ControllerIconPreview/icons) into the
game's source art (owner-approved overnight, November 1): Art/UI/ControllerIcons/<Xbox|PlayStation>/T_Icon_*.png, each scaled so
its longer side is 256 px with its own shape kept (LB is wide, A is round), on a transparent margin whose outer 4 px are faded
to nothing, so no cut edge can show. The two Home
buttons are left out: both are platform logos, and the game never asks for them.
    python Scripts/Art/extract_controller_icons.py
    python Scripts/Art/publish_controller_icons.py
Then import them in the editor: Scripts/Setup/import_controller_icons.py.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'Saved' / 'ControllerIconPreview' / 'icons'
OUT = ROOT / 'Art' / 'UI' / 'ControllerIcons'
SIZE, MARGIN, FADE = 256, 6, 4
LEFT_OUT = {'T_Icon_Xbox_Home', 'T_Icon_PlayStation_Home'}


def publish(path):
    icon = Image.open(path).convert('RGBA')
    scale = (SIZE - 2 * MARGIN) / max(icon.size)
    icon = icon.resize((max(1, round(icon.width * scale)), max(1, round(icon.height * scale))), Image.LANCZOS)
    width, height = icon.width + 2 * MARGIN, icon.height + 2 * MARGIN
    canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(icon, (MARGIN, MARGIN))
    pixels = np.array(canvas).astype(np.float32)
    rows = np.minimum(np.arange(height), np.arange(height)[::-1]).astype(np.float32)
    columns = np.minimum(np.arange(width), np.arange(width)[::-1]).astype(np.float32)
    edge = np.clip(np.minimum.outer(rows, columns) / FADE, 0, 1)
    pixels[:, :, 3] *= edge
    return Image.fromarray(pixels.round().clip(0, 255).astype(np.uint8), 'RGBA')


def main():
    written = []
    for path in sorted(SRC.glob('T_Icon_*.png')):
        if path.stem in LEFT_OUT:
            continue
        family = 'Xbox' if path.stem.startswith('T_Icon_Xbox_') else 'PlayStation'
        target = OUT / family / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        publish(path).save(target)
        written.append(target.relative_to(ROOT).as_posix())
    assert len(written) == 36, f'expected 36 icons, wrote {len(written)}: run extract_controller_icons.py first'
    print('\n'.join(written))


if __name__ == '__main__':
    main()
