"""Ice sheets on the Winter mountains (owner, November 6: different sheets of ice around the Winter mountains only, like
the real Arctic, as tall as the nearest cliff or landing; solid; not literal blocks). Plain Python, no Unreal;
build_glaciers.py turns each sheet into a mesh and places it.

DECIDED (owner-delegated, all tuning):
- Around each Winter mountain, several separate sheets lie on the slopes at different heights and sides, with bare rock
  and snow between them. Each is an irregular patch, longer down the fall line than across it.
- A sheet's surface is the slope smoothed out (the ice fills hollows and rides over bumps), raised by its thickness, so a
  high rock may poke through. Its edge is a steep ice wall.
- Its thickness is about the height of the nearest cliff or bank (the ground's relief round it), within THICK.
- Kept off caves, climb-outs, landmarks, the village and ports, apart from one another, and off the beaches.
"""
import math
import random

import world_layout as W
import world_terrain as T
from world_landmarks import near_landmark

CELL = 600.0                     # cm between mesh points
THICK = (1200.0, 4500.0)         # cm: an ice sheet's thickness at its middle
SIZE = (5000.0, 15000.0)         # cm: a sheet's half-length down the slope
SHEETS = {'Winter1': 9, 'Winter2': 8, 'Winter3': 10, 'Winter4': 14}
APART = 3000.0                   # cm of bare ground at least between two sheets


def _blocked(x, y):
    return W.near_port(x, y, 4000.0) or T.near_cave(x, y, 2000.0) or T.near_climb(x, y, 1500.0) or near_landmark(x, y, 2000.0)


def _hash(i, j, seed):
    n = (i * 374761393 + j * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _noise(x, y, size, seed):
    gx, gy = x / size, y / size
    i, j = math.floor(gx), math.floor(gy)
    fx, fy = gx - i, gy - j
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = _hash(i, j, seed), _hash(i + 1, j, seed), _hash(i, j + 1, seed), _hash(i + 1, j + 1, seed)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


def sheet(island, h, x, y, rng, seed):
    """One ice sheet centred near (x, y): {'cells': {(i, j): (x, y, z, on_ice)}, ...}. Points just outside the ice lie
    under the ground, so the triangles between them and the ice make the sheet's wall."""
    e = 2500.0
    gx, gy = (h(x + e, y) - h(x - e, y)) / (2 * e), (h(x, y + e) - h(x, y - e)) / (2 * e)
    g = math.hypot(gx, gy) or 1.0
    ax, ay = -gx / g, -gy / g                          # down the fall line
    half = rng.uniform(*SIZE)
    across = half * rng.uniform(.45, .8)
    # Thickness from the land round it: the relief within 120 m, about the height of its nearest cliff or bank.
    ring = [h(x + r * math.cos(a), y + r * math.sin(a)) for r in (6000.0, 12000.0) for a in [k * math.pi / 4 for k in range(8)]]
    thick = min(THICK[1], max(THICK[0], (max(ring) - min(ring)) * rng.uniform(.3, .45)))

    def inside(px, py):
        u = ((px - x) * ax + (py - y) * ay) / half
        v = (-(px - x) * ay + (py - y) * ax) / across
        wobble = .78 + .44 * _noise(px, py, 4500.0, seed) + .12 * _noise(px, py, 1500.0, seed + 5)
        return u * u + v * v < wobble * wobble

    def smooth(px, py):
        r = 2400.0
        return (2 * h(px, py) + sum(h(px + r * math.cos(a), py + r * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)])) / 8

    reach = half * 1.3
    n = int(reach / CELL) + 1
    cells, ice = {}, set()
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            px, py = x + i * CELL, y + j * CELL
            if inside(px, py) and island.distance(px, py) < -1500 and not _blocked(px, py):
                ice.add((i, j))
    if len(ice) < 120:
        return None
    rim = {(i + di, j + dj) for i, j in ice for di in (-1, 0, 1) for dj in (-1, 0, 1)} - ice
    for i, j in ice:
        px, py = x + i * CELL, y + j * CELL
        ground = h(px, py)
        top = smooth(px, py) + thick * (.85 + .15 * _noise(px, py, 3000.0, seed + 9)) + 120 * (_noise(px, py, 900.0, seed + 3) - .5)
        # A rock higher than the ice pokes through it: the point sinks under the ground there.
        cells[(i, j)] = (px, py, top if top > ground + 150 else ground - 200, top > ground + 150)
    for i, j in rim:
        px, py = x + i * CELL, y + j * CELL
        cells[(i, j)] = (px, py, h(px, py) - 300, False)
    return {'cells': cells, 'centre': (x, y), 'thick_m': round(thick / 100, 1), 'area_m2': round(len(ice) * (CELL / 100) ** 2),
            'reach': reach}


def plan_island(island, h, seed=0):
    """The island's ice sheets, round its mountains: on slopes high and low, on every side."""
    rng = random.Random(sum(map(ord, island.key)) * 4241 + seed)
    reach = island.reach()
    cells = []
    for i in range(-int(reach), int(reach), 2500):
        for j in range(-int(reach), int(reach), 2500):
            x, y = island.cx + i, island.cy + j
            if island.distance(x, y) < -4000:
                cells.append((h(x, y), x, y))
    peak = max(z for z, _, _ in cells)
    # Mountain ground: the upper part of the island's relief.
    slopes = [c for c in cells if c[0] > .35 * peak]
    rng.shuffle(slopes)
    out = []
    for z, x, y in slopes:
        if len(out) >= SHEETS.get(island.key, 8):
            break
        if _blocked(x, y) or any(math.hypot(x - s['centre'][0], y - s['centre'][1]) < s['reach'] + SIZE[1] * .9 + APART for s in out):
            continue
        s = sheet(island, h, x, y, rng, seed + len(out) * 17 + sum(map(ord, island.key)))
        if s:
            out.append(s)
    return out
