"""How much higher than the old flat test ground the Plains ground lies at the origin (the starter beach rises about 68 cm there). Checks that lay fixtures out at fixed
heights (a pickup at eye level 1.5 m ahead of a survivor teleported to (0, 0, 96)) add this to those heights, so the fixtures stay at the survivor's eye line."""
import unreal


def lift(world, x=0.0, y=0.0):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 3000), unreal.Vector(x, y, -3000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                 False, [], unreal.DrawDebugTrace.NONE, True)
    ground = hit.to_tuple()[4].z if hit else 0.0
    return max(0.0, ground)
