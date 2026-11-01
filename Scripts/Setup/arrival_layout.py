"""The Plains arrival (CLAUDE.md, Phase 1 slice 1): where a new survivor first stands and what the first ten seconds show.
Plain Python (no Unreal), shared by build_arrival.py, build_grass.py and Scripts/Tests/test_arrival_layout.py.

Owner, October 31: the spawn moves from the east beach (by the pond, dock and moored sloop) to the starter island's south
shore, because from the old beach the ridge hides Saltreach completely. From here, at late morning, facing west-north-west:
  - the sea lies to the right, from about 30 degrees out (CLAUDE.md: behind or 30-90 degrees to one side);
  - Saltreach's lighthouse, roofs and pier stand about 20 degrees right of centre, 487 m off;
  - a 4.5 m worn track crosses the sand into the grass and runs about 410 m round the flooded hollows to the town's edge;
  - an oak group rises on the slope to the forward left, and a small freshwater spring sits below it, beside the track.

Every position is a fixed, authored number (cm, Unreal units), found once by measuring world_terrain.py's ground and the
map's actors; nothing here is random. The old beach spawn, the dock, the pond and the sloop stay where they are.
"""
import math

SPAWN = (-18300.0, -64700.0)     # the PlayerStart's x, y; its z is the ground plus STAND_HEIGHT
SPAWN_YAW = -196.0               # degrees; the first view
STAND_HEIGHT = 100.0             # cm above the ground for the PlayerStart (as the old beach spawn had)
SALTREACH_LIGHT = (-66867.0, -67739.0, 1861.0)   # the lighthouse's lamp (build_freeport.py), for the sight-line checks

ROUTE_WIDTH = 450.0              # cm; CLAUDE.md asks for a 3-6 m traversable route
# The track's centre line, from the spawn to Saltreach's east edge, every 10 m or so (a grid search over world_terrain.py
# keeping 4 m clear of any flooded ground), before smoothing.
ROUTE = [(-18400, -64600), (-19400, -64600), (-20400, -64600), (-21400, -64600), (-22400, -64600), (-23400, -64600),
         (-24400, -64600), (-25200, -63800), (-26000, -63000), (-26800, -62200), (-27600, -61400), (-28600, -61000),
         (-29600, -61000), (-30600, -61000), (-31600, -61000), (-32600, -60600), (-33600, -60600), (-34600, -60600),
         (-35600, -60600), (-36600, -60600), (-37600, -60600), (-38600, -60600), (-39600, -60600), (-40600, -60600),
         (-41600, -60600), (-42600, -60600), (-43600, -60600), (-44600, -60800), (-45400, -61400), (-46400, -61400),
         (-47400, -61400), (-48400, -61400), (-49400, -61400), (-50400, -61400), (-51400, -61800), (-52200, -62600),
         (-53000, -63400), (-53800, -64200), (-54600, -65000), (-55200, -65600)]

# The oak group on the rise to the forward left: (x, y, scale). Uneven spacing, none on the track or in the line to Saltreach.
OAKS = [(-21127.0, -62225.0, 1.15), (-21635.0, -61455.0, 0.95), (-20346.0, -62506.0, 1.05), (-22336.0, -62086.0, 0.9)]
# The spring: a small stone-ringed pool of fresh water on the gentle slope below the oaks, a few metres off the track.
SPRING = (-20565.0, -63530.0)
SPRING_RADIUS = 110.0            # cm, the water's radius inside its stones

# The first things to gather by hand (Phase 1 slice 2, minutes 5-10), within 15-60 m and a few metres off the track: fallen
# oak sticks under the oaks, fibre plants in the grass, loose stones by the spring and on the beach's top, a berry bush on
# ahead. (label, gathering kind as unreal.EWHandGatheringKind names it, item asset, x, y, quantity). Between them they hold
# more than the stone hatchet takes (3 sticks, 2 stones, 4 fibre; DA_RecipeStoneHatchet), with some left for mistakes.
FIRST_RESOURCES = [
    ('Arrival sticks 1', 'LOOSE_STICKS', 'DA_TestSticks', -20750.0, -62900.0, 6),
    ('Arrival sticks 2', 'LOOSE_STICKS', 'DA_TestSticks', -21900.0, -62650.0, 6),
    ('Arrival fiber 1', 'PLANT_FIBER', 'DA_TestFiber', -19500.0, -63800.0, 10),
    ('Arrival fiber 2', 'PLANT_FIBER', 'DA_TestFiber', -23100.0, -63650.0, 10),
    ('Arrival stones 1', 'LOOSE_STONES', 'DA_TestStone', -20050.0, -63100.0, 4),
    ('Arrival stones 2', 'LOOSE_STONES', 'DA_TestStone', -21600.0, -65150.0, 4),
    ('Arrival berries 1', 'BERRIES', 'DA_TestAzulBerry', -24300.0, -63450.0, 10),
]
STONE_HATCHET = {'DA_TestSticks': 3, 'DA_TestStone': 2, 'DA_TestFiber': 4}   # the recipe build_first_resources.py writes

# How far round the arrival other generators keep clear (grass, scattered flora): the track's edge plus this margin.
CLEAR_MARGIN = 150.0


def smoothed_route(passes=3):
    """The track's centre line with its grid corners rounded off (Chaikin), starting and ending where ROUTE does."""
    pts = [(float(x), float(y)) for x, y in ROUTE]
    for _ in range(passes):
        out = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            out += [(.75 * ax + .25 * bx, .75 * ay + .25 * by), (.25 * ax + .75 * bx, .25 * ay + .75 * by)]
        out.append(pts[-1])
        pts = out
    return pts


def route_length(points=None):
    pts = points or smoothed_route()
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def distance_to_route(x, y, points=None):
    """Horizontal distance in cm from (x, y) to the track's centre line."""
    pts = points or _SMOOTH
    best = 1e18
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy or 1.0)))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return best


def near_arrival(x, y, margin=CLEAR_MARGIN):
    """True where other generators should leave the ground alone: on the track, at the spring or by the spawn."""
    if math.hypot(x - SPAWN[0], y - SPAWN[1]) < 300 + margin:
        return True
    if math.hypot(x - SPRING[0], y - SPRING[1]) < SPRING_RADIUS + 60 + margin:
        return True
    if abs(x - SPAWN[0]) > 40000 or y > -59000 or y < -67500:
        return False                              # quick reject: nowhere near the track's box
    return distance_to_route(x, y) < ROUTE_WIDTH / 2 + margin


def bearing(x, y, tx, ty):
    """Unreal yaw in degrees from (x, y) toward (tx, ty)."""
    return math.degrees(math.atan2(ty - y, tx - x))


def relative(yaw, to):
    """Signed degrees from yaw to `to`, -180..180 (positive: to the right in Unreal's left-handed frame)."""
    return (to - yaw + 180.0) % 360.0 - 180.0


_SMOOTH = smoothed_route()
