"""Gunport covers for the hull scripts (owner, October 17: each hull port has a sliding dark opaque glass cover,
individually opened and closed; a cannon cannot fire through a shut port, and its carriage extends and retracts).

A cover is a pane of dark glass in an iron rim, square or round to its port, standing just outside the port's frame in
the hull's skin. Opened, it slides aft along the hull clear of the port (AEWShip::ShowGunports), and the cannon runs out
behind it. DECIDED (delegated): the cover slides aft; sizes and the glass's look are tuning.
"""
import math
import unreal

from ship_geometry import Builder, material_builder, write_static_mesh

FOLDER = '/Game/Elitewake/World/Ships'
COVER_STANDOFF = 5.5   # cm outside the hull's half-beam: just clear of the port frame's outer face
RIM = 4.0              # the iron rim's width round the glass


def glass_material():
    """Dark, opaque, glossy glass: almost black, a cold sheen, and reflections of the sky and sea."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_GunportGlass_v1')
    colour = custom('return lerp(float3(.012, .016, .02), float3(.02, .026, .03), saturate(N.z * .5 + .5));',
                    unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('N',))
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionVertexNormalWS), '', colour, 'N')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.06), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.9), '', unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def square_cover(w, h):
    """A rectangular pane (in the mount's Y-Z plane, facing +X, outward) in an iron rim."""
    b = Builder()
    b.slot = 0
    b.box((0.0, 0.0, 0.0), (3.0, w, h))
    b.slot = 1
    for y, z, sy, sz in ((0, h / 2 + RIM / 2, w + 2 * RIM, RIM), (0, -h / 2 - RIM / 2, w + 2 * RIM, RIM),
                         (w / 2 + RIM / 2, 0, RIM, h), (-w / 2 - RIM / 2, 0, RIM, h)):
        b.box((0.5, y, z), (5.0, sy, sz), iron=1.0)
    return b


def round_cover(d):
    """A round pane in an iron ring."""
    b = Builder()
    b.slot = 1
    b.tube([(-2.0, 0.0, 0.0), (2.0, 0.0, 0.0)], d / 2 + RIM, sides=28, iron=1.0)
    b.slot = 0
    b.tube([(1.0, 0.0, 0.0), (3.0, 0.0, 0.0)], d / 2, sides=28)
    return b


def cover_meshes(timber):
    """Build both covers with the glass and the hull's timber material (its iron flag darkens the rim)."""
    glass = glass_material()
    return {'square': lambda w, h: write_static_mesh(square_cover(w, h), f'{FOLDER}/SM_GunportCoverSquare_v1', [glass, timber], 60.0),
            'round': lambda d: write_static_mesh(round_cover(d), f'{FOLDER}/SM_GunportCoverRound_v1', [glass, timber], 60.0)}


def _to_mount(m, v, point=True):
    """A hull-space point (or vector) in the mount's own space."""
    t = m.get_editor_property('transform')
    loc, yaw = t.translation, math.radians(t.rotation.rotator().yaw)
    dx, dy, dz = (v[0] - loc.x, v[1] - loc.y, v[2] - loc.z) if point else v
    c, s = math.cos(yaw), math.sin(yaw)
    return unreal.Vector(dx * c + dy * s, -dx * s + dy * c, dz)


def gunport(m, hull, port, side, mesh):
    """Make a cannon mount the gunport it stands behind: its cover closing the port and sliding aft to open it."""
    cx, w, z0, z1 = port[:4]
    at = (cx, side * (hull.half_beam(cx) + COVER_STANDOFF), (z0 + z1) / 2)
    m.set_editor_property('gunport', True)
    m.set_editor_property('cover_mesh', mesh)
    m.set_editor_property('cover_transform', unreal.Transform(location=_to_mount(m, at)))
    m.set_editor_property('cover_slide', _to_mount(m, (-(w + 2 * RIM + 10.0), 0.0, 0.0), point=False))
    return m
