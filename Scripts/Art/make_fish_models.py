"""Cut the owner's fish art from its studio background and inflate each silhouette into a body. Safe to run again.
Run with ordinary Python (Pillow), outside Unreal:
    python Scripts/Art/make_fish_models.py

For each aquatic creature in Art/Concepts/Animals/2026-10-12 it writes, under Art/Fauna/Fish:
  <Name>-v1.png       the creature cut out on transparency, cropped, head toward the right (+X in Unreal)
  <Name>-v1.mesh.json a body for it, in two parts. The trunk is truly round (owner, October 15: the creatures
                      looked flat): along its length, an oval cross-section as tall as the silhouette's body with the
                      fins trimmed off, as wide as the creature is broad, its sides mapped with the art. Around it, the
                      silhouette thinly inflated carries the fins and tail. Units are centimetres at the creature's
                      working length. A ray stays a flat inflated wing.
Scripts/Setup/build_fish.py turns these into Unreal assets.

The background is the art's plain studio grey with a soft shadow: it is flood-filled from the border while colours
change gently, so the creature's sharper outline stops the fill. Lengths are tuning.
"""
import json
import math
from collections import deque
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Art/Concepts/Animals/2026-10-12'
OUT = ROOT / 'Art/Fauna/Fish'

# name, source art, which way the head faces in the art, working length in cm (tuning), how thick the inflated
# silhouette is for its height (fins, tail; a ray's whole body), and how broad the round trunk is for its height
# (0 for a ray, which has none). All tuning.
CREATURES = [
    ('Piranha', 'piranha.png', 'left', 30.0, .10, .42),
    ('Bass', 'bass.png', 'left', 50.0, .10, .48),
    ('Catfish', 'catfish.png', 'left', 90.0, .12, .95),
    ('MantaRay', 'manta_ray.png', 'left', 380.0, .12, 0.0),
    ('GreatWhiteShark', 'great_white_shark.png', 'left', 450.0, .08, .78),
    ('HammerheadShark', 'hammerhead_shark.png', 'left', 400.0, .08, .74),
    ('Squid', 'squid.png', 'left', 180.0, .12, .95),
]
RING = 20           # points round the trunk's cross-section
FIN_WINDOW = .13    # fins are trimmed from the trunk over this share of the length
WORK = 640          # mask width in pixels while segmenting
COLUMNS = 72        # mesh columns along the body
STEP_TOLERANCE = 5  # largest colour step between neighbouring background pixels
DRIFT_TOLERANCE = 12  # largest difference from the background colour carried by the fill


def background_mask(image):
    """True where the studio background is, at WORK width. The fill carries the colour of the background it has
    crossed, updated slowly, so it follows the grey's gentle gradient and the soft shadow but stops where a body
    differs from what lies just outside it, even across a gradual edge."""
    small = image.convert('RGB').resize((WORK, round(image.height * WORK / image.width)), Image.BILINEAR)
    small = small.filter(ImageFilter.MedianFilter(3))
    w, h = small.size
    px = small.load()
    seen = [[False] * w for _ in range(h)]
    ref = {}
    queue = deque()
    for x in range(w):
        for y in (0, h - 1):
            seen[y][x] = True; ref[(x, y)] = px[x, y]; queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not seen[y][x]:
                seen[y][x] = True; ref[(x, y)] = px[x, y]; queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        here, carried = px[x, y], ref[(x, y)]
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx]:
                there = px[nx, ny]
                step = max(abs(there[i] - here[i]) for i in range(3))
                drift = max(abs(there[i] - carried[i]) for i in range(3))
                if step <= STEP_TOLERANCE and drift <= DRIFT_TOLERANCE and max(there) - min(there) < 40:
                    seen[ny][nx] = True
                    ref[(nx, ny)] = tuple(carried[i] * .92 + there[i] * .08 for i in range(3))
                    queue.append((nx, ny))
    return seen, w, h


def largest_region(inside, w, h):
    """Keep the biggest connected creature region; drop specks."""
    label = [[0] * w for _ in range(h)]
    best, best_size, current = 0, 0, 0
    for y in range(h):
        for x in range(w):
            if inside[y][x] and not label[y][x]:
                current += 1
                size, queue = 0, deque([(x, y)])
                label[y][x] = current
                while queue:
                    cx, cy = queue.popleft()
                    size += 1
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and inside[ny][nx] and not label[ny][nx]:
                            label[ny][nx] = current
                            queue.append((nx, ny))
                if size > best_size:
                    best, best_size = current, size
    return [[label[y][x] == best for x in range(w)] for y in range(h)]


def fill_holes(inside, w, h):
    """Background enclosed by the creature (between fins and body) that the border fill never reached is the creature."""
    outside = [[False] * w for _ in range(h)]
    queue = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not inside[y][x]:
                outside[y][x] = True
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not inside[y][x] and not outside[y][x]:
                outside[y][x] = True
                queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not inside[ny][nx] and not outside[ny][nx]:
                outside[ny][nx] = True
                queue.append((nx, ny))
    return [[not outside[y][x] for x in range(w)] for y in range(h)]


def distance_inside(inside, w, h):
    """Chamfer distance from each inside pixel to the nearest outside pixel."""
    big = 1e9
    d = [[0.0 if not inside[y][x] else big for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if d[y][x]:
                for dx, dy, c in ((-1, 0, 1), (0, -1, 1), (-1, -1, 1.414), (1, -1, 1.414)):
                    nx, ny = x + dx, y + dy
                    d[y][x] = min(d[y][x], (d[ny][nx] + c) if 0 <= nx < w and 0 <= ny < h else 1.0)
    for y in range(h - 1, -1, -1):
        for x in range(w - 1, -1, -1):
            if d[y][x]:
                for dx, dy, c in ((1, 0, 1), (0, 1, 1), (1, 1, 1.414), (-1, 1, 1.414)):
                    nx, ny = x + dx, y + dy
                    d[y][x] = min(d[y][x], (d[ny][nx] + c) if 0 <= nx < w and 0 <= ny < h else 1.0)
    return d


def build(name, source, head, length, thickness, breadth):
    image = Image.open(SOURCE / source).convert('RGB')
    if head == 'left':
        image = image.transpose(Image.FLIP_LEFT_RIGHT)
    background, w, h = background_mask(image)
    inside = fill_holes(largest_region([[not b for b in row] for row in background], w, h), w, h)
    xs = [x for y in range(h) for x in range(w) if inside[y][x]]
    ys = [y for y in range(h) for x in range(w) if inside[y][x]]
    x0, x1, y0, y1 = max(min(xs) - 2, 0), min(max(xs) + 3, w), max(min(ys) - 2, 0), min(max(ys) + 3, h)
    inside = [row[x0:x1] for row in inside[y0:y1]]
    w, h = x1 - x0, y1 - y0

    # The cut-out art: full resolution, alpha from the mask, edges softened a little.
    scale = image.width / WORK
    box = (round(x0 * scale), round(y0 * scale), round(x1 * scale), round(y1 * scale))
    art = image.crop(box)
    mask = Image.new('L', (w, h))
    mask.putdata([255 if inside[y][x] else 0 for y in range(h) for x in range(w)])
    mask = mask.resize(art.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: 0 if v < 100 else min(255, (v - 100) * 2))
    art.putalpha(mask)
    if art.width > 1024:
        art = art.resize((1024, round(art.height * 1024 / art.width)), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    art.save(OUT / f'{name}-v1.png')

    # The body: a grid over the silhouette, each point raised by how deep inside it lies; flat fins, round body.
    dist = distance_inside(inside, w, h)
    deepest = max(max(row) for row in dist)
    cm = length / w                          # centimetres per mask pixel
    rows = max(8, round(COLUMNS * h / w))
    def sample(u, v):
        x, y = min(int(u * (w - 1) + .5), w - 1), min(int(v * (h - 1) + .5), h - 1)
        return dist[y][x], inside[y][x]
    grid = [[sample(i / COLUMNS, j / rows) for i in range(COLUMNS + 1)] for j in range(rows + 1)]
    # A cell is drawn if any corner is inside, so the art's alpha, not the grid, makes the outline.
    keep = [[any(grid[j + a][i + b][1] for a in (0, 1) for b in (0, 1)) for i in range(COLUMNS)] for j in range(rows)]
    verts, uvs, tris, index = [], [], [], {}
    for side in (1, -1):
        for j in range(rows + 1):
            for i in range(COLUMNS + 1):
                if not any(keep[jj][ii] for jj in (j - 1, j) for ii in (i - 1, i) if 0 <= jj < rows and 0 <= ii < COLUMNS):
                    continue
                u, v = i / COLUMNS, j / rows
                depth = grid[j][i][0] / deepest
                bulge = thickness * deepest * cm * (depth ** .75)
                index[(side, i, j)] = len(verts)
                verts.append((round((u - .5) * w * cm, 3), round(side * bulge, 3), round((.5 - v) * h * cm, 3)))
                uvs.append((round(u, 5), round(v, 5)))
        for j in range(rows):
            for i in range(COLUMNS):
                if keep[j][i]:
                    a, b, c, d = (index[(side, i, j)], index[(side, i + 1, j)], index[(side, i + 1, j + 1)], index[(side, i, j + 1)])
                    tris += [(a, b, c, side), (a, c, d, side)]
    loft = trunk(inside, w, h, cm, breadth) if breadth > 0 else {'verts': [], 'uvs': [], 'tris': []}
    (OUT / f'{name}-v1.mesh.json').write_text(json.dumps({
        'name': name, 'length_cm': length, 'height_cm': round(h * cm, 1), 'source': f'Art/Concepts/Animals/2026-10-12/{source}',
        'verts': verts, 'uvs': uvs, 'tris': tris, 'trunk': loft}), encoding='utf-8')
    return name, art.size, len(verts), len(tris)


def trunk(inside, w, h, cm, breadth):
    """The round body: per column, the silhouette's main vertical run with fins trimmed off (a fin juts out of the
    body over a short stretch, so over a window the body's top is the lowest top and its bottom the highest
    bottom), lofted into ovals. Each point is mapped to the art at its height on the side, pulled a little inward
    so the top and belly take the body's own colours rather than the cut-out's edge. Triangles carry an outward
    direction for orientation."""
    columns = []
    for i in range(COLUMNS + 1):
        x = min(int(i / COLUMNS * (w - 1) + .5), w - 1)
        runs, start = [], None
        for y in range(h + 1):
            on = y < h and inside[y][x]
            if on and start is None:
                start = y
            elif not on and start is not None:
                runs.append((start, y - 1))
                start = None
        columns.append(max(runs, key=lambda r: r[1] - r[0]) if runs else None)
    half = max(1, round(FIN_WINDOW * COLUMNS / 2))
    body = []
    for i in range(COLUMNS + 1):
        near = [columns[k] for k in range(max(0, i - half), min(COLUMNS, i + half) + 1) if columns[k]]
        if not columns[i] or len(near) < half:
            body.append(None)
            continue
        top, bottom = max(r[0] for r in near), min(r[1] for r in near)
        top, bottom = max(top, columns[i][0]), min(bottom, columns[i][1])
        body.append((top, bottom) if bottom - top > 2 else None)
    # Taper to a point at both ends of the run of body columns.
    first = next(i for i, b in enumerate(body) if b)
    last = len(body) - 1 - next(i for i, b in enumerate(reversed(body)) if b)
    verts, uvs, tris, rings = [], [], [], []
    for i in range(first, last + 1):
        if not body[i]:
            continue
        top, bottom = body[i]
        u = i / COLUMNS
        x = (u - .5) * w * cm
        mid, hh = (top + bottom) / 2, (bottom - top) / 2
        ends = min(i - first, last - i)
        taper = min(1.0, (ends + .35) / 3.0) ** .5      # round off the last few columns at nose and tail
        ring = []
        for k in range(RING):
            a = 2 * math.pi * k / RING
            c, s = math.cos(a), math.sin(a)
            y_px = mid - c * hh * taper                  # c = 1 at the top
            ring.append(len(verts))
            verts.append((round(x, 3), round(s * breadth * hh * cm * taper, 3), round((.5 - y_px / h) * h * cm, 3)))
            uvs.append((round(u, 5), round((mid - c * hh * .82 * taper) / h, 5)))
        rings.append((ring, x))
    for (ra, xa), (rb, xb) in zip(rings, rings[1:]):
        for k in range(RING):
            a, b, c, d = ra[k], ra[(k + 1) % RING], rb[(k + 1) % RING], rb[k]
            angle = 2 * math.pi * (k + .5) / RING
            out = (0.0, math.sin(angle), math.cos(angle))
            tris += [(a, b, c, out), (a, c, d, out)]
    for (ring, x), sign in ((rings[0], -1.0), (rings[-1], 1.0)):    # caps
        centre = len(verts)
        verts.append((round(x, 3), 0.0, round(sum(verts[v][2] for v in ring) / RING, 3)))
        uvs.append((uvs[ring[0]][0], round(sum(uvs[v][1] for v in ring) / RING, 5)))
        for k in range(RING):
            tris.append((centre, ring[k], ring[(k + 1) % RING], (sign, 0.0, 0.0)))
    return {'verts': verts, 'uvs': uvs, 'tris': tris}


if __name__ == '__main__':
    for creature in CREATURES:
        print(build(*creature))
