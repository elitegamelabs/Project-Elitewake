"""Build risk and recovery on the Plains arrival (CLAUDE.md Phase 1, slice 4, minutes 15-20). Safe to run again.
Run in the editor outside Play, after build_first_resources.py:
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -run=pythonscript -script=<this file>

  - The wild boar (build_animals.boar and ANIMALS['Boar']): the Plains' modest threat (CLAUDE.md 5.2, "boar/predator
    pockets"), its model, definition and synthesized sounds (Scripts/Art/make_boar_sound.py: three grunts for its warning
    call, a snort as it gores, a squeal as it dies). Two are placed in a pocket about 45 m off the track
    (arrival_layout.BOARS), seen from it; they charge only a survivor who comes within 6 m. Killed, each gives 3-5 Raw
    Meat (25% food sickness eaten raw, safe cooked at a campfire).
  - Medicinal herbs (yarrow): patches of white flat flower heads on stalks above low rosettes of fine leaves, gathered by hand with E
    (EEWHandGatheringKind::Herbs), two clumps beside the track (arrival_layout.HERBS). Eaten, one ends food sickness.
  - The death bag's look: a tied canvas sack (EWDeathBag drops it on the ground where a survivor fell; it was a grey sphere).
The boars and herbs do not regrow. build_animals.py's own placement leaves boars out (it would remove them with the other
animals: run this again after it). Every amount is tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arrival_layout as A  # noqa: E402
import build_animals as BA  # noqa: E402
import import_audio as IA  # noqa: E402
from build_coastal_flora import MAP, Ground, easy_to_aim_at  # noqa: E402
from build_first_resources import aim_box  # noqa: E402
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

FOLDER = 'World/RiskAndRecovery'
ASSETS = '/Game/Elitewake/World/Arrival'
DEATH = '/Game/Elitewake/World/Death'
HERB = '/Game/Elitewake/Items/Food/DA_MedicinalHerb'
LEVEL_FOLDER = 'Coast/Wildlife/Animals'
SEA = -65.0
GREEN, LEAF, FLOWER = (.13, .19, .06), (.07, .11, .035), (.62, .59, .48)


def yarrow(seed):
    """A small patch of yarrow, as it grows, about 1 m across: three plants, each a low rosette of fine
    narrow leaves and seven to ten stalks, 80-105 cm (yarrow grows to about a metre, so the heads clear the grass), topped with a flat 14-18 cm head of small cream florets, so the patch shows as
    a spread of white above the grass from the track (20-30 m). Colours are in the vertex colour (M_Yarrow_v1 reads them)."""
    rng = random.Random(seed)
    b = Builder()

    def v(p, c):
        return b.vertex(p, *c)

    for plant in range(3):
        a0 = 2 * math.pi * plant / 3 + rng.uniform(-.4, .4)
        ox, oy = (0.0, 0.0) if plant == 0 else (rng.uniform(30, 42) * math.cos(a0), rng.uniform(30, 42) * math.sin(a0))
        for k in range(9):                                         # the rosette: arching strips 3 cm wide
            a = 2 * math.pi * k / 9 + rng.uniform(-.25, .25)
            length, rise, w = rng.uniform(20, 32), rng.uniform(8, 16), 1.5
            c, s_ = math.cos(a), math.sin(a)
            rows = []
            for i in range(5):
                t = i / 4
                d, z = length * t, 1.0 + rise * math.sin(math.pi * t * .8)
                half = w * (1 - .7 * t)
                rows.append([v((ox + d * c - half * s_, oy + d * s_ + half * c, z), LEAF),
                             v((ox + d * c + half * s_, oy + d * s_ - half * c, z), LEAF)])
            for i in range(4):
                b.quad(rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0], (0, 0, 1))
        for k in range(rng.randint(7, 10)):                        # the stalks and their flower heads
            a, lean = rng.uniform(0, 2 * math.pi), rng.uniform(4, 16)
            top = (ox + lean * math.cos(a), oy + lean * math.sin(a), rng.uniform(80, 105))
            start = len(b.verts)
            b.tube([(ox, oy, 1.0), (ox + (top[0] - ox) * .5, oy + (top[1] - oy) * .5, top[2] * .55), top], .6, sides=5)
            for i in range(start, len(b.verts)):
                b.colours[i] = GREEN
            radius = rng.uniform(7, 9)
            for j in range(34):                                    # florets in a flat, slightly domed head
                r, t = radius * math.sqrt(rng.random()), rng.uniform(0, 2 * math.pi)
                fx, fy = top[0] + r * math.cos(t), top[1] + r * math.sin(t)
                fz = top[2] + 1.8 * (1 - (r / radius) ** 2)
                start = len(b.verts)
                b.tube([(fx, fy, fz - 1.0), (fx, fy, fz), (fx, fy, fz + 1.0)], lambda q: (.6, 1.4, .6)[q], sides=5)
                for i in range(start, len(b.verts)):
                    b.colours[i] = FLOWER
    return b


def sack(seed):
    """The death bag (EWDeathBag): a slumped hemp-canvas sack about 55 x 40 cm and 45 cm tall, its neck gathered and tied with
    a darker rope band, a short flared fringe above; its base at the origin so it sits on the ground. Canvas #A88961 with a
    little hand-made unevenness, in the vertex colour (M_Sackcloth_v1 reads it)."""
    rng = random.Random(seed)
    b = Builder()
    canvas, rope = (.36, .24, .12), (.16, .11, .06)
    # (height, half-width, half-depth) up the sack; the lumps are fixed per ring and side.
    profile = [(0.0, 17, 13), (3, 25, 19), (10, 28, 21), (20, 27, 20), (28, 21, 16), (33, 13, 10), (36, 7.5, 6.5),
               (37.5, 7, 6), (39.5, 7.5, 6.5), (41, 9, 7.5), (45, 12, 9)]
    sides = 18
    rings = []
    for i, (z, rx, ry) in enumerate(profile):
        tied = 36 <= z <= 39.5
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            lump = 1.0 if tied or i in (0, len(profile) - 1) else rng.uniform(.93, 1.07)
            slump = 1.0 + (.12 if z < 12 and math.cos(a) > 0 else 0.0)        # it has settled to one side
            ring.append(b.vertex((rx * lump * slump * math.cos(a), ry * lump * math.sin(a), z), *(rope if tied else canvas)))
        rings.append(ring)
    for lower, upper in zip(rings, rings[1:]):
        for j in range(sides):
            n = (j + 1) % sides
            a = 2 * math.pi * (j + .5) / sides
            b.quad(lower[j], lower[n], upper[n], upper[j], (math.cos(a), math.sin(a), 0.0))
    base = b.vertex((0.0, 0.0, 0.0), *canvas)
    for j in range(sides):
        b.tri(rings[0][j], rings[0][(j + 1) % sides], base, (0, 0, -1))
    top = b.vertex((0.0, 0.0, 41.0), *canvas)                                 # the fringe's open mouth, closed low inside
    for j in range(sides):
        b.tri(rings[-1][j], rings[-1][(j + 1) % sides], top, (0, 0, 1))
    return b


def sackcloth_material():
    """Base colour from the vertex colour, matte."""
    mel = unreal.MaterialEditingLibrary
    material, node, _ = material_builder(f'{DEATH}/M_Sackcloth_v1')
    assert mel.connect_material_property(node(unreal.MaterialExpressionVertexColor), '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.92), '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def yarrow_material():
    """Base colour from the vertex colour, matte, two-sided for the thin leaves."""
    mel = unreal.MaterialEditingLibrary
    material, node, _ = material_builder(f'{ASSETS}/M_Yarrow_v1')
    colour = node(unreal.MaterialExpressionVertexColor)
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.82), '', unreal.MaterialProperty.MP_ROUGHNESS)
    material.set_editor_property('two_sided', True)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def boar_sounds():
    """Imports the boar's sounds and gives its definition its calls, gore and death (import_audio's own tables)."""
    falloffs = {name: IA.attenuation(name) for name in IA.FALLOFFS}
    waves = {name: IA.import_sound(source, name, volume, mode, falloffs)
             for source, (name, volume, mode) in IA.SOUNDS.items() if 'Boar' in source}
    definition = unreal.load_asset(f'{BA.FOLDER}/DA_Animal_Boar')
    calls, interval = IA.CALLS['Boar']
    attacks, deaths = IA.STRIKES['Boar']
    definition.set_editor_property('calls', [waves[c] for c in calls])
    definition.set_editor_property('call_interval', unreal.Vector2D(*interval))
    definition.set_editor_property('attack_sounds', [waves[c] for c in attacks])
    definition.set_editor_property('death_sounds', [waves[c] for c in deaths])
    assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
    return {n: round(w.get_editor_property('duration'), 2) for n, w in waves.items()}


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    meat = unreal.load_asset(BA.RAW_MEAT)
    herb = unreal.load_asset(HERB)
    assert meat and herb, 'run build_fish.py and create_food_items.py first'
    BA.ANIMALS = {'Boar': BA.ANIMALS['Boar']}
    shared = unreal.load_asset(f'{BA.FOLDER}/M_Animal_v1')
    assert shared, 'run build_animals.py first'
    BA.animal_material = lambda: shared        # the shared animal material is left as it is, not rebuilt
    boar = BA.build_definitions(meat)['Boar']
    report = {'sounds': boar_sounds(), 'boars': [], 'herbs': [], 'removed': []}

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if (isinstance(actor, unreal.EWAnimal) and actor.get_editor_property('definition') == boar) \
                or str(actor.get_folder_path()).startswith(FOLDER):
            report['removed'].append(actor.get_actor_label())
            actors.destroy_actor(actor)
    ground = Ground()
    rng = random.Random(1752)
    half_height = BA.ANIMALS['Boar']['size'][1] * .5
    for k, (x, y) in enumerate(A.BOARS):
        z = ground(x, y)
        animal = actors.spawn_actor_from_class(unreal.EWAnimal, unreal.Vector(x, y, z + half_height),
                                               unreal.Rotator(0, 0, rng.uniform(-180, 180)))
        animal.set_actor_label(f'Wild Boar Plains {k + 1}')
        animal.set_folder_path(LEVEL_FOLDER)
        animal.set_editor_property('definition', boar)
        animal.set_editor_property('surface_z', SEA)
        report['boars'].append((round(x), round(y), round(z)))

    # The death bag's sack (EWDeathBag loads it by path; until it exists the bag is a plain sphere).
    report['sack'] = aim_box(easy_to_aim_at(write_static_mesh(sack(5), f'{DEATH}/SM_DeathBag_v1', [sackcloth_material()], 30.0))).get_path_name()

    material = yarrow_material()
    looks = [aim_box(easy_to_aim_at(write_static_mesh(yarrow(70 + k), f'{ASSETS}/SM_Yarrow_{k + 1}_v1', [material], 30.0)))
             for k in range(2)]
    circles = []
    for k, (label, x, y, quantity) in enumerate(A.HERBS):
        node = actors.spawn_actor_from_class(unreal.EWHandGatherable, unreal.Vector(x, y, ground(x, y)),
                                             unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
        node.set_actor_label(label)
        node.set_folder_path(FOLDER)
        mesh = node.get_editor_property('mesh')
        mesh.set_static_mesh(looks[k % len(looks)])
        mesh.set_relative_scale3d(unreal.Vector(*[rng.uniform(.95, 1.1)] * 3))     # a pickup's own scale is small
        for prop, value in {'item_definition': herb, 'quantity': quantity, 'gathering_kind': unreal.EWHandGatheringKind.HERBS}.items():
            node.set_editor_property(prop, value)
        circles.append(unreal.Vector(x, y, 160.0))
        report['herbs'].append(label)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    report['grass_cleared'] = unreal.EWWorldEditorLibrary.remove_foliage_in_circles(world, circles, 'SM_GrassClump')

    assert level.save_current_level()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'PlainsThreatResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Plains threat built: {len(report["boars"])} boars, {len(report["herbs"])} herb clumps')


if __name__ == '__main__':
    main()
