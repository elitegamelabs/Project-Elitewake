"""Furniture and lanterns for ships' cabins and holds (owner, October 18: the ship design sheet,
Art/Concepts/Boats/2026-10-18/Ship-Design-Sheet-v1.webp, shows every ship's rooms furnished and lantern-lit: a bed,
a table and stools, barrels, sea chests, benches, shelves, rugs, lanterns on the beams).

The pieces are built into a hull's own mesh with three material slots: 0 the hull's timber (make_timber_material:
tar, iron and brass by vertex colour), 1 cloth (FABRIC: the vertex tone picks linen, a red rug or a blue rug) and 2
lantern glass, which glows warm. Each lantern's position goes in the ship definition's LanternLights, where the ship
hangs a warm point light (AEWShip). Sizes and colours are tuning.
"""
import math
import unreal

from ship_geometry import material_builder

FOLDER = '/Game/Elitewake/World/Ships'
TIMBER, FABRIC, GLASS, WINDOW_GLASS = 0, 1, 2, 3
LINEN, RED_RUG, BLUE_RUG = .8, .15, .45      # vertex tones FABRIC reads


def fabric_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_ShipFabric_v1')
    flags = node(unreal.MaterialExpressionVertexColor)
    position = node(unreal.MaterialExpressionWorldPosition)
    colour = custom('float weave = .92 + .08 * sin(P.x * 3.1) * sin(P.y * 2.7);'
                    ' float t = F.b;'
                    ' float3 linen = float3(.5, .47, .41), red = float3(.3, .045, .035), blue = float3(.06, .09, .22);'
                    ' float3 c = t > .6 ? linen : t > .3 ? blue : red;'
                    # A rug's woven motif: fine gold diamonds, faint, from where it lies.
                    ' float2 q = abs(frac(P.xy / 31.0) - .5);'
                    ' float diamond = smoothstep(.06, .0, abs(q.x + q.y - .32));'
                    ' c = t <= .6 ? lerp(c, float3(.42, .31, .12), diamond * .55) : c;'
                    ' return c * weave;', unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('F', 'P'))
    assert mel.connect_material_expressions(flags, '', colour, 'F')
    assert mel.connect_material_expressions(position, '', colour, 'P')
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.92), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def glass_material():
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_LanternGlass_v1')
    glow = node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(4.0, 2.2, .8, 1))
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.9, .7, .4, 1)), '',
                                         unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def window_material():
    """A restrained, translucent blue-grey pane; collision remains part of the hull mesh."""
    mel = unreal.MaterialEditingLibrary
    material, node, _ = material_builder(f'{FOLDER}/M_ShipWindowGlass_v1')
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    colour = node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.24, .34, .38, 1))
    opacity = node(unreal.MaterialExpressionConstant, r=.28)
    roughness = node(unreal.MaterialExpressionConstant, r=.16)
    specular = node(unreal.MaterialExpressionConstant, r=.72)
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(opacity, '', unreal.MaterialProperty.MP_OPACITY)
    assert mel.connect_material_property(roughness, '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(specular, '', unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def materials(timber):
    """Stable material slots: timber, fabric, lantern glow and separate hull-window glass."""
    return [timber, fabric_material(), glass_material(), window_material()]


def _rot(dx, dy, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return dx * c - dy * s, dx * s + dy * c


class Room:
    """Places furniture in a room at (x, y) on a floor at z, each piece turned by yaw degrees."""

    def __init__(self, b, z):
        self.b, self.z, self.lights = b, z, []

    def box(self, x, y, yaw, dx, dy, dz, size, slot=TIMBER, tone=.5, iron=0.0):
        ox, oy = _rot(dx, dy, yaw)
        sx, sy = (size[0], size[1]) if abs(math.sin(math.radians(yaw))) < .5 else (size[1], size[0])
        b = self.b
        b.slot = slot
        first = len(b.colours)
        b.box((x + ox, y + oy, self.z + dz), (sx, sy, size[2]), iron=iron)
        for k in range(first, len(b.colours)):
            r, g, _ = b.colours[k]
            b.colours[k] = (r, g, tone)
        b.slot = TIMBER

    def bed(self, x, y, yaw=0.0, length=200.0, width=110.0):
        """A wooden cot: frame on legs, linen mattress and pillow, a blanket and a headboard; 200 by 110 cm unless sized."""
        h, w = length / 2, width / 2
        for dx in (-(h - 5), h - 5):
            for dy in (-(w - 5), w - 5):
                self.box(x, y, yaw, dx, dy, 20, (8, 8, 40))
        self.box(x, y, yaw, 0, 0, 38, (length, width, 10))
        self.box(x, y, yaw, 0, 0, 50, (length - 10, width - 10, 14), slot=FABRIC, tone=LINEN)
        self.box(x, y, yaw, -(h - 22), 0, 62, (30, width - 40, 10), slot=FABRIC, tone=LINEN)
        self.box(x, y, yaw, h * .11, 0, 58, (length * .7, width - 6, 4), slot=FABRIC, tone=RED_RUG)    # the blanket
        self.box(x, y, yaw, -(h + 2), 0, 60, (6, width + 2, 80))
        self.box(x, y, yaw, h + 2, 0, 45, (6, width + 2, 50))

    def table(self, x, y, yaw=0.0, length=120.0, width=70.0):
        for dx in (-length / 2 + 8, length / 2 - 8):
            for dy in (-width / 2 + 8, width / 2 - 8):
                self.box(x, y, yaw, dx, dy, 36, (7, 7, 72))
        self.box(x, y, yaw, 0, 0, 75, (length, width, 6))

    def stool(self, x, y):
        for dx, dy in ((-12, -12), (12, -12), (-12, 12), (12, 12)):
            self.box(x, y, 0, dx, dy, 22, (5, 5, 44))
        self.box(x, y, 0, 0, 0, 46, (36, 36, 5))

    def bench(self, x, y, yaw=0.0, length=160.0):
        for dx in (-length / 2 + 10, length / 2 - 10):
            self.box(x, y, yaw, dx, 0, 20, (8, 36, 40))
        self.box(x, y, yaw, 0, 0, 43, (length, 40, 6))

    def barrel(self, x, y, height=90.0, radius=30.0):
        b = self.b
        b.tube([(x, y, self.z), (x, y, self.z + height * .5), (x, y, self.z + height)], lambda k: (radius * .88, radius, radius * .88)[k], sides=14)
        for f in (.15, .85):
            b.tube([(x, y, self.z + height * f - 2), (x, y, self.z + height * f + 2)], radius * (.93 if f in (.15, .85) else 1) + 1, sides=14, iron=1.0)

    def chest(self, x, y, yaw=0.0):
        self.box(x, y, yaw, 0, 0, 22, (80, 45, 44))
        self.box(x, y, yaw, 0, 0, 47, (82, 47, 8))
        for dx in (-30, 30):
            self.box(x, y, yaw, dx, 0, 25, (4, 48, 46), iron=1.0)

    def shelf(self, x, y, yaw=0.0, length=120.0, height=150.0):
        for dx in (-length / 2, length / 2):
            self.box(x, y, yaw, dx, 0, height / 2, (5, 30, height))
        for k in range(4):
            self.box(x, y, yaw, 0, 0, 10 + k * (height - 20) / 3, (length, 30, 4))
        # Jars and bundles on the shelves.
        for k in range(1, 4):
            for j in range(-2, 3):
                self.box(x, y, yaw, j * length / 6, 0, 10 + k * (height - 20) / 3 - (height - 20) / 6 + 6, (14, 14, 16), tone=.2 + .15 * ((j + k) % 3))

    def crate(self, x, y, size=60.0, yaw=0.0):
        self.box(x, y, yaw, 0, 0, size / 2, (size, size, size))
        for dz in (6, size - 6):
            self.box(x, y, yaw, 0, 0, dz, (size + 2, size + 2, 5), tone=.25)

    def rug(self, x, y, yaw=0.0, length=200.0, width=130.0, tone=RED_RUG):
        self.box(x, y, yaw, 0, 0, 1, (length, width, 2), slot=FABRIC, tone=tone)

    def lantern(self, x, y, z_top):
        """A lantern hung under a beam at z_top: iron hook and frame round glowing glass. Its light is recorded."""
        b = self.b
        z = z_top
        b.tube([(x, y, z), (x, y, z - 18)], .8, sides=5, iron=1.0)
        b.box((x, y, z - 21), (14, 14, 3), iron=1.0)
        b.box((x, y, z - 47), (16, 16, 3), iron=1.0)
        for dx, dy in ((-7, -7), (7, -7), (-7, 7), (7, 7)):
            b.box((x + dx, y + dy, z - 34), (1.6, 1.6, 26), iron=1.0)
        b.slot = GLASS
        b.box((x, y, z - 34), (11, 11, 23))
        b.slot = TIMBER
        self.lights.append((x, y, z - 34))
