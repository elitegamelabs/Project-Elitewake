"""Build Saltreach's welcome for a new survivor (CLAUDE.md Phase 1, slice 5, minutes 20-25). Safe to run again.
Run in the editor outside Play, after build_freeport.py:
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -run=pythonscript -script=<this file>

  - The strongbox (AEWStrongbox): an oak chest bound with black iron, 90 x 55 cm and 55 cm tall, in front of the warehouse,
    facing the town square. Whoever opens it sees only their own store (kept on their player and saved with the survivor).
    One of the town's lantern posts stands beside it, lit at night like the street's, so it can be found and used after dark.
The town steps themselves (sell, store, shipyard, Company) are code (UEWArrivalComponent); nothing else here is placed.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402
from build_coastal_flora import MAP, easy_to_aim_at  # noqa: E402
from build_first_resources import aim_box  # noqa: E402
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

ASSETS = '/Game/Elitewake/World/Freeport'
FOLDER = 'World/Freeport'
LABEL = 'Saltreach Freeport: strongbox'
# In Saltreach's own frame (build_freeport.py: along = out to sea, across = to the right): the warehouse stands at (1250, 2950),
# 900 cm along its front, turned (snapped) to face the square at -90 degrees, its door and step in the middle of that front. The
# chest stands 2.3 m to the door's left as the square sees it, 80 cm out from the wall, clear of the step.
WAREHOUSE = (1250.0, 2950.0, 900.0)
STRONGBOX = (WAREHOUSE[0] - 230.0, WAREHOUSE[1] - WAREHOUSE[2] / 2 - 80.0)
STRONGBOX_YAW = -90.0            # its hasp faces the square, as the warehouse's door does
# The lantern post (build_freeport's SM_Freeport_LanternPost_v1, its arm along the harbor's axis) 1.1 m to the chest's side and
# 1.6 m out toward the square, its lantern 50 cm out on the arm toward the chest and 2.4 m up, lit as the street lamps are
# (build_freeport.light): in front, so it lights the hasp side a survivor uses (behind the chest, it left that side black at night).
LANTERN = (STRONGBOX[0] - 110.0, STRONGBOX[1] - 160.0)

# Linear vertex colours for the anchors in CLAUDE.md 9.1 (M_Strongbox_v1 reads them): warm weathered timber #5B402D, dark wet
# timber #2D241E between the planks, black iron with a little warmth.
OAK, SEAM, IRON = (.104, .051, .026), (.026, .018, .013), (.022, .021, .02)


def cuboid(b, centre, size, colour):
    """A closed box of one colour, centred at `centre` (cm), each face its own corners so the edges stay hard."""
    cx, cy, cz = centre
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    for axis in range(3):
        for sign in (-1, 1):
            corners = []
            for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):      # round the face in order
                p = [0.0, 0.0, 0.0]
                p[axis] = sign
                p[(axis + 1) % 3] = u
                p[(axis + 2) % 3] = v
                corners.append(b.vertex((cx + p[0] * hx, cy + p[1] * hy, cz + p[2] * hz), *colour))
            normal = [0.0, 0.0, 0.0]
            normal[axis] = sign
            b.quad(*corners, tuple(normal))


def chest(seed):
    """The strongbox: a body of three horizontal oak planks a side over a dark core (the seams show between them), a lid
    of two, four squat feet, three iron straps over the lid and down the front and back, iron corner plates and a hasp
    with a hanging lock plate on the front (+X). Its base at the origin so it stands on the ground."""
    rng = random.Random(seed)
    b = Builder()
    length, depth, body, lid, foot = 90.0, 55.0, 38.0, 13.0, 4.0
    top = foot + body + lid

    def tone(c):
        k = rng.uniform(.88, 1.1)
        return tuple(min(1.0, x * k) for x in c)

    # Feet and the dark core (seen only between the planks).
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuboid(b, (sx * (length / 2 - 7), sy * (depth / 2 - 6), foot / 2), (10, 9, foot), SEAM)
    cuboid(b, (0, 0, foot + body / 2), (length - 1.2, depth - 1.2, body), SEAM)
    cuboid(b, (0, 0, foot + body + lid / 2), (length + .8, depth + .8, lid - .8), SEAM)
    # The planks: three up the body, two in the lid, a little proud of the core, each its own shade.
    for k in range(3):
        h = body / 3
        z = foot + h * k + h / 2
        cuboid(b, (0, 0, z), (length, depth, h - .5), tone(OAK))
    for k in range(2):
        h = lid / 2
        z = foot + body + h * k + h / 2
        cuboid(b, (0, 0, z), (length + 2, depth + 2, h - .5), tone(OAK))
    cuboid(b, (0, 0, top - .6), (length + 1, depth + 1, 1.2), tone(OAK))          # the lid's top boards
    # Iron: three straps over the lid and down front and back; plates at the corners; the hasp and lock on the front.
    for x in (-length / 2 + 12, 0.0, length / 2 - 12):
        cuboid(b, (x, 0, top + .3), (5, depth + 3.2, .9), IRON)
        for sy in (-1, 1):
            cuboid(b, (x, sy * (depth / 2 + 1.4), foot + (body + lid) / 2), (5, 1.0, body + lid), IRON)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (foot + 5, top - 5):
                cuboid(b, (sx * (length / 2 + .5), sy * (depth / 2 - 4), z), (1.0, 9, 9), IRON)
    cuboid(b, (length / 2 + 1.4, 0, foot + body + 2), (1.2, 8, 12), IRON)          # the hasp, over the lid's edge
    cuboid(b, (length / 2 + 2.6, 0, foot + body - 6), (1.6, 7, 9), IRON)           # the lock plate below it
    return b


def strongbox_material():
    """Base colour from the vertex colour; the iron (dark, near-neutral) a little smoother than the oak."""
    mel = unreal.MaterialEditingLibrary
    material, node, _ = material_builder(f'{ASSETS}/M_Strongbox_v1')
    assert mel.connect_material_property(node(unreal.MaterialExpressionVertexColor), '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.78), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


TOWN = T.PORT_LEVEL + 5          # the street's top on Saltreach's levelled terrace (build_freeport.TOWN)
TERRACE = 3650.0                 # how far the terrace runs from the town's centre (build_freeport.ground_z)


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    report = {'removed': []}
    mesh = aim_box(easy_to_aim_at(write_static_mesh(chest(1748), f'{ASSETS}/SM_Strongbox_v1', [strongbox_material()], 30.0)))
    report['mesh'] = mesh.get_path_name()

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWStrongbox) or actor.get_actor_label().startswith(LABEL):
            report['removed'].append(actor.get_actor_label())
            actors.destroy_actor(actor)
    port = W.PORTS['Plains']
    assert math.hypot(*STRONGBOX) < TERRACE, 'the strongbox must stand on the street'
    x, y = port.world(*STRONGBOX)
    z = TOWN
    box = actors.spawn_actor_from_class(unreal.EWStrongbox, unreal.Vector(x, y, z),
                                        unreal.Rotator(0, 0, math.degrees(port.facing) + STRONGBOX_YAW))
    box.set_actor_label(LABEL)
    box.set_folder_path(FOLDER)
    chest_mesh = box.get_component_by_class(unreal.StaticMeshComponent)
    chest_mesh.set_static_mesh(mesh)
    chest_mesh.set_relative_scale3d(unreal.Vector(1, 1, 1))
    report['strongbox'] = [round(x), round(y), round(z)]

    lx, ly = port.world(*LANTERN)
    post = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(lx, ly, z), unreal.Rotator(0, 0, math.degrees(port.facing)))
    post.set_actor_label(f'{LABEL} lantern')
    post.set_folder_path(FOLDER)
    post.static_mesh_component.set_static_mesh(unreal.load_asset(f'{ASSETS}/SM_Freeport_LanternPost_v1'))
    hx, hy = port.world(LANTERN[0] + 50, LANTERN[1])
    lamp = actors.spawn_actor_from_class(unreal.EWNightLight, unreal.Vector(hx, hy, z + 240))
    lamp.set_actor_label(f'{LABEL} lantern light')
    lamp.set_folder_path(FOLDER)
    glow = lamp.get_component_by_class(unreal.PointLightComponent)
    glow.set_editor_property('intensity', 2600.0)
    glow.set_editor_property('attenuation_radius', 1300.0)
    glow.set_editor_property('light_color', unreal.Color(r=255, g=178, b=105, a=255))
    glow.set_editor_property('cast_shadows', False)
    report['lantern'] = [round(lx), round(ly)]

    assert level.save_current_level()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'SaltreachWelcomeResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Saltreach welcome built: strongbox at {report["strongbox"]}')


if __name__ == '__main__':
    main()
