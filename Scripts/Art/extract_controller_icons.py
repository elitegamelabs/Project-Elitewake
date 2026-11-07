"""Preview-only extraction of the owner's controller icon sheet (November 1): separate the 38 icons by their own alpha, keep
glow and shadow, name them, check every crop edge, write a contact sheet. Writes only to Saved/ControllerIconPreview
(generated, never committed); nothing is imported into the game until the owner approves (CLAUDE.md).
    python Scripts/Art/extract_controller_icons.py
"""
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC = Path(r'C:\Users\elite\Downloads\Glossy Xbox and PlayStation Button Icon Sheet.png')
OUT = Path(__file__).resolve().parents[2] / 'Saved' / 'ControllerIconPreview' / 'icons'
OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob('*.png'):
    old.unlink()

im = Image.open(SRC).convert('RGBA')
a = np.array(im)[:, :, 3]
H, W = a.shape
mask = a > 8                                   # any visible pixel, faint glow and soft shadow included

# Join pixels within JOIN px of each other (a glow separated from its button by a hairline), by a coarse grid label.
JOIN = 6
cell = JOIN
gh, gw = (H + cell - 1) // cell, (W + cell - 1) // cell
grid = np.zeros((gh, gw), bool)
ys, xs = np.nonzero(mask)
grid[ys // cell, xs // cell] = True
labels = np.zeros((gh, gw), int)
n = 0
for gy in range(gh):
    for gx in range(gw):
        if grid[gy, gx] and not labels[gy, gx]:
            n += 1
            q = deque([(gy, gx)])
            labels[gy, gx] = n
            while q:
                y, x = q.popleft()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < gh and 0 <= xx < gw and grid[yy, xx] and not labels[yy, xx]:
                            labels[yy, xx] = n
                            q.append((yy, xx))

boxes = []
for k in range(1, n + 1):
    gy, gx = np.nonzero(labels == k)
    y0, y1, x0, x1 = gy.min() * cell, min(H, (gy.max() + 1) * cell), gx.min() * cell, min(W, (gx.max() + 1) * cell)
    sub = mask[y0:y1, x0:x1]
    if sub.sum() < 400:                        # specks, not icons
        continue
    # Tight box on real pixels inside the cell box.
    yy, xx = np.nonzero(sub)
    boxes.append((x0 + xx.min(), y0 + yy.min(), x0 + xx.max() + 1, y0 + yy.max() + 1))

# Rows by vertical centre, then left to right; the left half is Xbox, the right half PlayStation.
boxes.sort(key=lambda b: ((b[1] + b[3]) / 2, b[0]))
rows = []
for b in boxes:
    c = (b[1] + b[3]) / 2
    if rows and abs(c - rows[-1][0]) < 60:
        rows[-1][1].append(b)
    else:
        rows.append([c, [b]])
NAMES = {
    'Xbox': [['A', 'B', 'X', 'Y'], ['DPad_Up', 'DPad_Down', 'DPad_Left', 'DPad_Right'], ['LB', 'RB', 'LT', 'RT'],
             ['LeftStick', 'RightStick', 'LeftStickPress', 'RightStickPress'], ['Menu', 'View', 'Home']],
    'PlayStation': [['Cross', 'Square', 'Triangle', 'Circle'], ['DPad_Up', 'DPad_Down', 'DPad_Left', 'DPad_Right'],
                    ['L1', 'R1', 'L2', 'R2'], ['LeftStick', 'RightStick', 'L3', 'R3'], ['Options', 'Create', 'Home']]}
PAD = 4
report = {'source': str(SRC), 'size': [W, H], 'mode': im.mode, 'alpha_range': [int(a.min()), int(a.max())],
          'corners_transparent': bool(a[0, 0] == 0 and a[-1, -1] == 0 and a[0, -1] == 0 and a[-1, 0] == 0),
          'rows_found': [len(r[1]) for r in rows], 'icons': []}
for r, (_, row) in enumerate(rows):
    row.sort(key=lambda b: b[0])
    for family in ('Xbox', 'PlayStation'):
        mine = [b for b in row if ((b[0] + b[2]) / 2 < W / 2) == (family == 'Xbox')]
        names = NAMES[family][r] if r < len(NAMES[family]) else []
        for i, b in enumerate(mine):
            name = f'T_Icon_{family}_{names[i] if i < len(names) else f"Row{r + 1}_{i + 1}"}'
            x0, y0, x1, y1 = max(0, b[0] - PAD), max(0, b[1] - PAD), min(W, b[2] + PAD), min(H, b[3] + PAD)
            # Grow each side while its edge still carries any faint glow or shadow (up to 30 px), never into a neighbour.
            others = [o for o in boxes if o is not b]
            def free(nx0, ny0, nx1, ny1):
                return not any(nx0 < o[2] and o[0] < nx1 and ny0 < o[3] and o[1] < ny1 for o in others)
            for _ in range(30):
                grew = False
                if y0 > 0 and a[y0, x0:x1].max() > 0 and free(x0, y0 - 1, x1, y1): y0 -= 1; grew = True
                if y1 < H and a[y1 - 1, x0:x1].max() > 0 and free(x0, y0, x1, y1 + 1): y1 += 1; grew = True
                if x0 > 0 and a[y0:y1, x0].max() > 0 and free(x0 - 1, y0, x1, y1): x0 -= 1; grew = True
                if x1 < W and a[y0:y1, x1 - 1].max() > 0 and free(x0, y0, x1 + 1, y1): x1 += 1; grew = True
                if not grew: break
            x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
            icon = im.crop((x0, y0, x1, y1))
            ia = np.array(icon)[:, :, 3]
            # Clipping check: any visible pixel on the crop's own edge means the glow or shadow was cut.
            edge = int(max(ia[0].max(), ia[-1].max(), ia[:, 0].max(), ia[:, -1].max()))
            icon.save(OUT / f'{name}.png')
            report['icons'].append({'name': name, 'box': [x0, y0, x1, y1], 'size': [x1 - x0, y1 - y0], 'edge_alpha_max': edge,
                                    'opaque_corner': int(max(ia[0, 0], ia[0, -1], ia[-1, 0], ia[-1, -1]))})

# Contact sheet: every icon on a mid-grey checker (shows any black box), with its name.
cols = 8
tile = 190
names_h = 34
sheet = Image.new('RGBA', (cols * tile, ((len(report['icons']) + cols - 1) // cols) * (tile + names_h)), (60, 60, 60, 255))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('arial.ttf', 13)
except OSError:
    font = ImageFont.load_default()
for i, info in enumerate(report['icons']):
    x, y = (i % cols) * tile, (i // cols) * (tile + names_h)
    for cy in range(0, tile, 16):
        for cx in range(0, tile, 16):
            if (cx // 16 + cy // 16) % 2:
                d.rectangle([x + cx, y + cy, x + cx + 15, y + cy + 15], fill=(150, 150, 150, 255))
    icon = Image.open(OUT / f'{info["name"]}.png')
    icon.thumbnail((tile - 10, tile - 10))
    sheet.alpha_composite(icon, (x + (tile - icon.width) // 2, y + (tile - icon.height) // 2))
    d.text((x + 4, y + tile + 4), info['name'].replace('T_Icon_', ''), fill=(255, 255, 255, 255), font=font)
sheet.save(OUT.parent / 'contact_sheet.png')
(OUT.parent / 'extraction.json').write_text(json.dumps(report, indent=2, default=int))
print(json.dumps({k: report[k] for k in ('size', 'mode', 'alpha_range', 'corners_transparent', 'rows_found')}), len(report['icons']), 'icons')
for info in report['icons']:
    flag = '' if info['edge_alpha_max'] == 0 and info['opaque_corner'] == 0 else '  <-- CHECK'
    print(info['name'], info['size'], 'edge alpha', info['edge_alpha_max'], flag)


