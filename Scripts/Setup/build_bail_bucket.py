"""Build the small bailing bucket used by every ship.

Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py C:/UnrealProjects/EW/Scripts/Setup/build_bail_bucket.py"

The bucket is a tapered, open-topped assembly of separate curved oak staves, a fitted bottom, two iron hoops and a
rope bail. Its base is the origin and its footprint is about 30 cm across by 30 cm high. Safe to rerun in place.
"""
import json
import math
import sys
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402

ASSET = '/Game/Elitewake/World/Ships/SM_BailBucket_v1'
TIMBER_UV_TILE = 45.0
SIDES = 14
BOTTOM_RADIUS = 13.8
TOP_RADIUS = 15.0
HEIGHT = 30.0
STAVE_GAP = 0.012


def ring_path(radius, z, points=49):
    """Closed, round path for a narrow forged-iron hoop."""
    return [(radius * math.cos(2.0 * math.pi * i / (points - 1)),
             radius * math.sin(2.0 * math.pi * i / (points - 1)), z) for i in range(points)]


def bucket_mesh():
    b = Builder()
    levels = (0.8, 2.2, 7.0, 14.0, 21.5, 27.8, 29.6)

    # Separate staves follow the taper and a slight crown across their width, with narrow joints left open.
    for stave in range(SIDES):
        centre = 2.0 * math.pi * (stave + 0.5) / SIDES
        half = math.pi / SIDES * (1.0 - STAVE_GAP)
        angles = (centre - half, centre, centre + half)
        rows = []
        for z in levels:
            t = z / HEIGHT
            radius = BOTTOM_RADIUS + (TOP_RADIUS - BOTTOM_RADIUS) * t
            rows.append([(radius * math.cos(a), radius * math.sin(a), z) for a in angles])
        b.grid(rows, lambda i, j, a=centre: (math.cos(a), math.sin(a), 0.0),
               tone_of=lambda i, j, s=stave: 0.40 + (s % 5) * 0.025)

        # The inner face of each stave gives the open rim real wall thickness.
        inner_rows = []
        for z in levels:
            t = z / HEIGHT
            radius = BOTTOM_RADIUS - 1.1 + (TOP_RADIUS - BOTTOM_RADIUS) * t
            inner_rows.append([(radius * math.cos(a), radius * math.sin(a), z) for a in angles])
        b.grid(inner_rows, lambda i, j, a=centre: (-math.cos(a), -math.sin(a), 0.0),
               tone_of=lambda i, j, s=stave: 0.32 + (s % 5) * 0.018)

    # The bottom is fitted inside the lower stave edges, visible through the open top.
    floor_z = 1.0
    centre_id = b.vertex((0.0, 0.0, floor_z), tone=0.30)
    floor_ring = []
    for i in range(SIDES):
        a = 2.0 * math.pi * i / SIDES
        floor_ring.append(b.vertex(((BOTTOM_RADIUS - 1.2) * math.cos(a),
                                    (BOTTOM_RADIUS - 1.2) * math.sin(a), floor_z), tone=0.34))
    for i in range(SIDES):
        b.tri(centre_id, floor_ring[i], floor_ring[(i + 1) % SIDES], (0.0, 0.0, 1.0))

    # Two narrow iron hoops cinch the outside of the staves.
    b.tube(ring_path(14.1, 7.0), 0.8, sides=8, iron=1.0)
    b.tube(ring_path(14.7, 23.0), 0.8, sides=8, iron=1.0)

    # Forged eyes hold an arched rope bail that can be gripped to carry the bucket.
    for x in (-14.1, 14.1):
        eye = [(x, 0.8 * math.cos(2.0 * math.pi * i / 16), 28.0 + 0.8 * math.sin(2.0 * math.pi * i / 16))
               for i in range(17)]
        b.tube(eye, 0.55, sides=6, iron=1.0)
    b.tube([(-14.1, 0.0, 28.0), (-14.0, 0.0, 34.0), (-10.0, 0.0, 38.0),
            (-5.0, 0.0, 40.0), (0.0, 0.0, 40.5), (5.0, 0.0, 40.0),
            (10.0, 0.0, 38.0), (14.0, 0.0, 34.0), (14.1, 0.0, 28.0)],
           lambda k: 0.9 - 0.12 * k / 8.0, sides=8)
    return b


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = make_timber_material()
    mesh = write_static_mesh(bucket_mesh(), ASSET, [timber], TIMBER_UV_TILE, collision=False)
    assert mesh, 'Bucket static mesh was not created'
    result = {
        'success': True,
        'asset': ASSET,
        'staves': SIDES,
        'dimensions_cm': {'width': 30.0, 'height': 30.0, 'rope_bail_height': 40.5},
        'features': ['open top', 'fitted bottom', 'tapered oak staves', 'two iron hoops', 'rope bail'],
    }
    Path(unreal.Paths.project_saved_dir(), 'BailBucketBuildResult.json').write_text(json.dumps(result, indent=2))
    unreal.log('Built SM_BailBucket_v1')


if __name__ == '__main__':
    main()
