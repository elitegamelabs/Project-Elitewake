"""Places on the coastal map that several setup scripts share. Not run on its own."""

# The freshwater pond inland: centre, radius of the water, height of its surface and depth at its middle, in cm.
# build_coastal_terrain.py carves its basin, build_freshwater_pond.py fills it and build_fish.py stocks it.
POND = (-1700.0, 1500.0)
POND_RADIUS = 700.0
POND_SURFACE = 5.0
POND_DEPTH = 260.0
