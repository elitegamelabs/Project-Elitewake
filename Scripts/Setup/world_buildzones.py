"""Where Build Mode may place a piece (owner, October 26-27: build on every island outside Ports and obstruction zones;
zones only carve out parts of an island, the rest is buildable; beaches are not buildable near docks).
Design: Design/Gameplay/BUILD_MODE_ISLAND_BUILDING_DESIGN_2026-10-27.md. Plain Python (no Unreal). The same zone list is
exported to Content/Elitewake/Data/BuildZones.json (export_buildzones.py) and read by UEWBuildZones in the game, so the
editor, the checks and the game agree. Every size and limit is tuning, not an owner-approved value.

A point is buildable when it is island ground above the waterline and in none of the zones. A footprint (a rectangle on the
ground) is buildable when its middle, corners and edge middles all are, and the ground under it is not too steep."""
import json
import math
from pathlib import Path

import world_landmarks as L
import world_layout as W
import world_terrain as T

SEA = T.SEA
GROUND_ABOVE_SEA = 40.0        # cm: ground must stand at least this far above the waterline
PORT_MARGIN = 1500.0           # cm: keep clear of a Port's site (the layout's own near_port margin)
PORT_STRIP_MARGIN = 500.0      # cm beyond the Port's waterfront strip
CAVE_MARGIN = 600.0
LANDMARK_MARGIN = 300.0
DOCK_BEACH_RADIUS = 5000.0     # cm round every dock: its beach is not buildable
DOCK_BEACH_TOP = 150.0         # cm above the waterline: the 'beach' part of the dock zone
MAX_SLOPE_RISE = 120.0         # cm: the ground under one footprint may differ by no more than this (visible supports level it)
STARTER_DOCK = (4000.0, 900.0)
SLOPE_LIMIT_DEG = 35.0


def zones():
    """The obstruction zones as shapes: circles (x, y, r) and boxes (x, y, yaw, u0, u1, half_v) in the box's frame.
    A shape with max_z only applies to ground below that height."""
    out = []
    for region, p in W.PORTS.items():
        out.append({'kind': 'circle', 'x': p.cx, 'y': p.cy, 'r': W.PORT_PAD + PORT_MARGIN, 'reason': f'{region} Port'})
        out.append({'kind': 'box', 'x': p.cx, 'y': p.cy, 'yaw': p.facing, 'u0': 0.0, 'u1': W.PORT_INLAND + 6000.0,
                    'half_v': 1800.0 + PORT_STRIP_MARGIN, 'reason': f'{region} Port waterfront'})
        out.append({'kind': 'circle', 'x': p.shore[0], 'y': p.shore[1], 'r': DOCK_BEACH_RADIUS, 'max_z': SEA + DOCK_BEACH_TOP,
                    'reason': f'{region} Port dock beach'})
    # The starter island's spawn, dock and spring keep tighter rings for building than the 20 m rings that keep trees off them.
    for (x, y, _), r, what in zip(T.STARTER_CLEAR, (800.0, 2200.0, 1200.0), ('the spawn', 'the starter dock', 'the spring')):
        out.append({'kind': 'circle', 'x': x, 'y': y, 'r': r, 'reason': what})
    out.append({'kind': 'circle', 'x': STARTER_DOCK[0], 'y': STARTER_DOCK[1], 'r': DOCK_BEACH_RADIUS, 'max_z': SEA + DOCK_BEACH_TOP,
                'reason': 'the starter dock beach'})
    for key, c in T.CAVES.items():
        if c:
            out.append({'kind': 'box', 'x': c.mx, 'y': c.my, 'yaw': c.heading, 'u0': -CAVE_MARGIN - 600.0, 'u1': c.depth + CAVE_MARGIN,
                        'half_v': c.half + CAVE_MARGIN, 'reason': f'the {key} cave'})
    for group in (L.LANDMARKS, L.PILLARS):
        for key, m in group.items():
            if m:
                for px, py, _, _ in m.parts:
                    out.append({'kind': 'circle', 'x': px, 'y': py, 'r': m.reach + LANDMARK_MARGIN, 'reason': f'the {key} landmark'})
    return out


ZONES = zones()


def _in_shape(s, x, y, z):
    if 'max_z' in s and z >= s['max_z']:
        return False
    if s['kind'] == 'circle':
        return math.hypot(x - s['x'], y - s['y']) < s['r']
    dx, dy = x - s['x'], y - s['y']
    c, sn = math.cos(s['yaw']), math.sin(s['yaw'])
    u, v = dx * c + dy * sn, -dx * sn + dy * c
    return s['u0'] <= u <= s['u1'] and abs(v) <= s['half_v']


def point_reason(x, y):
    """None when a piece may stand at this point, otherwise why not."""
    z = T.height(x, y)
    if z < SEA + GROUND_ABOVE_SEA:
        return 'not on island ground (water or too low)'
    for s in ZONES:
        if _in_shape(s, x, y, z):
            return f"in an obstruction zone ({s['reason']})"
    return None


def footprint_points(cx, cy, half_x, half_y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    pts = [(0.0, 0.0)] + [(sx * half_x, sy * half_y) for sx in (-1, 0, 1) for sy in (-1, 0, 1) if (sx or sy)]
    return [(cx + u * c - v * s, cy + u * s + v * c) for u, v in pts]


def footprint_reason(cx, cy, half_x, half_y, yaw=0.0):
    """None when a rectangular footprint (half sizes in cm, yaw in radians) may be built on, otherwise the first reason."""
    pts = footprint_points(cx, cy, half_x, half_y, yaw)
    for x, y in pts:
        why = point_reason(x, y)
        if why:
            return why
    heights = [T.height(x, y) for x, y in pts]
    if max(heights) - min(heights) > MAX_SLOPE_RISE:
        return 'ground too uneven'
    return None


def export(path):
    data = {'version': 1, 'sea_z': SEA, 'ground_above_sea': GROUND_ABOVE_SEA, 'max_slope_rise': MAX_SLOPE_RISE,
            'shapes': ZONES}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=1))
    return len(ZONES)
