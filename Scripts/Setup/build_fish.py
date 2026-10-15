"""Bring the owner's fish and sea creatures into the game and set them in the coastal sea. Safe to run again.
Run Scripts/Art/make_fish_models.py and Scripts/Art/make_food_icons.py first, then in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

From the owner's art (Art/Concepts/Fish/2026-10-12), each creature gets its cut-out art as a texture, a body
inflated from its silhouette, and a material that makes it swim: fish sway their tails, the manta beats its wings.
Every creature has a definition with its habits from the design reference: bass, catfish and manatees are
peaceful; piranhas, mantas (a tail sting), sharks (a bite) and squid are aggressive. Killed, a creature floats up
and is harvested for Raw Fish, or Raw Meat from a manatee; both are new items, not yet edible.

In the coastal sea: mantas and manatees in the warmer shallows, sharks and squid out in deeper water, the aggressive
ones well away from the spawn, the dock and the moorings. In the island's freshwater pond (build_freshwater_pond.py
first): bass, catfish and piranhas. All numbers are tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402
from build_coastal_flora import Ground, SEA  # noqa: E402
from coastal_layout import POND, POND_RADIUS, POND_SURFACE  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'  # sea life stays on the island (owner, October 14)
FOLDER = '/Game/Elitewake/Wildlife/Fish'
ITEM_FOLDER = '/Game/Elitewake/Items/Food'
LEVEL_FOLDER = 'Coast/Wildlife'
ROOT = Path(unreal.Paths.project_dir()).resolve()
ART = ROOT / 'Art/Fauna/Fish'
ICONS = ROOT / 'Art/Items'

# Name, display name, water, aggressive, [swim, dash, turn], roam, shallowest and deepest it goes, notice, [damage, interval, reach],
# attack name, health, yield (item, (fewest, most): 2-5 fish meat for ordinary fish, 6-10 for sharks, the manatee and
# bigger creatures, owner, October 14), and how its body moves: (amplitude cm, beats per second, waves along
# the body, wing beat 0/1).
CREATURES = {
    'Piranha': dict(display='Piranha', water='FRESH', aggressive=True, speeds=(150, 420, 220), roam=800, depth=40, deepest=200,
                    notice=800, attack=(4, 1.0, 25), attack_name='bite', health=15, yield_=('RawFish', (2, 5)), swim=(2.5, 2.6, .8, 0)),
    'Bass': dict(display='Bass', water='FRESH', aggressive=False, speeds=(100, 360, 180), roam=900, depth=40, deepest=250,
                 notice=0, attack=(0, 1, 0), attack_name='', health=15, yield_=('RawFish', (2, 5)), swim=(3, 2.0, .8, 0)),
    'Catfish': dict(display='Catfish', water='FRESH', aggressive=False, speeds=(80, 300, 140), roam=900, depth=60, deepest=300,
                    notice=0, attack=(0, 1, 0), attack_name='', health=25, yield_=('RawFish', (2, 5)), swim=(5, 1.2, 1.0, 0)),
    'MantaRay': dict(display='Manta Ray', water='SALT', aggressive=True, speeds=(140, 380, 70), roam=2200, depth=150, deepest=450,
                     notice=600, attack=(15, 2.0, 120), attack_name='sting', health=120, yield_=('RawFish', (6, 10)), swim=(45, .35, 0, 1)),
    'Manatee': dict(display='Manatee', water='SALT', aggressive=False, speeds=(60, 200, 40), roam=1500, depth=90, deepest=300,
                    notice=0, attack=(0, 1, 0), attack_name='', health=200, yield_=('RawFish', (6, 10)), swim=(7, .45, .6, 0)),
    'GreatWhiteShark': dict(display='Great White Shark', water='SALT', aggressive=True, speeds=(200, 560, 70), roam=3500, depth=200, deepest=600,
                            notice=1500, attack=(25, 1.5, 90), attack_name='bite', health=400, yield_=('RawFish', (6, 10)), swim=(20, .8, .7, 0)),
    'HammerheadShark': dict(display='Hammerhead Shark', water='SALT', aggressive=True, speeds=(220, 520, 80), roam=3500, depth=200, deepest=600,
                            notice=1300, attack=(20, 1.5, 80), attack_name='bite', health=320, yield_=('RawFish', (6, 10)), swim=(18, .9, .7, 0)),
    'Squid': dict(display='Squid', water='SALT', aggressive=True, speeds=(120, 450, 120), roam=2000, depth=300, deepest=800,
                  notice=900, attack=(12, 1.2, 120), attack_name='grab', health=150, yield_=('RawFish', (6, 10)), swim=(7, 1.0, 1.2, 0)),
}
ITEMS = {'RawFish': ('Raw Fish', 'Raw-Fish-v1.png', 'Fresh from the sea or a pond. Cook it before eating: raw fish makes you sick.'),
         'RawMeat': ('Raw Meat', 'Raw-Meat-v1.png', 'Fresh meat. Cook it before eating: raw meat makes you sick.')}
# Sea creatures on the coastal map: how many, how deep the water must be (cm below the surface), and how far from
# the spawn, the dock and the moorings they must start (cm).
PLACEMENT = {'MantaRay': (3, 250, 3500), 'Manatee': (3, 180, 1500), 'GreatWhiteShark': (2, 700, 6000),
             'HammerheadShark': (2, 700, 6000), 'Squid': (3, 900, 5500)}
# Freshwater kinds in the island's pond (build_freshwater_pond.py): how many of each.
POND_FISH = {'Bass': 3, 'Catfish': 2, 'Piranha': 2}
PEOPLE = [(150.0, 0.0), (4000.0, 900.0), (5300.0, 350.0), (6200.0, 2350.0)]   # spawn, dock landing, moorings
SEARCH = ((-20000.0, 17000.0), (-18000.0, 13000.0))   # within reach of the islands, x and y ranges


def import_texture(name, source):
    path = f'{FOLDER}/{name}'
    task = unreal.AssetImportTask()
    for k, v in {'filename': str(source), 'destination_path': FOLDER, 'destination_name': name, 'automated': True,
                 'replace_existing': True, 'save': True}.items():
        task.set_editor_property(k, v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(path)
    assert isinstance(texture, unreal.Texture2D), path
    return texture


def swim_material():
    """Masked art on both sides, wet-looking, moved by a swimming wave in the body's own space."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_Fish_v1')
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    material.set_editor_property('two_sided', True)
    art = node(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name='Art')
    assert mel.connect_material_property(art, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(art, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.38), '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(node(unreal.MaterialExpressionConstant, r=.6), '', unreal.MaterialProperty.MP_SPECULAR)
    # The wave: sideways sway growing toward the tail, or for a ray, wingtips rising and falling.
    wave = custom(
        'float u = saturate((HalfLength - P.x) / (2.0 * HalfLength));\n'
        'float sway = Amplitude * sin(6.2832 * (T * Rate - u * Waves)) * (0.1 + 0.9 * u * u);\n'
        'float s = saturate(abs(P.y) / HalfSpan);\n'
        'float lift = Amplitude * sin(6.2832 * T * Rate - s * 1.5) * s * s;\n'
        'return lerp(float3(0, sway, 0), float3(0, 0, lift), Wings);',
        unreal.CustomMaterialOutputType.CMOT_FLOAT3, ['P', 'T', 'Amplitude', 'Rate', 'Waves', 'HalfLength', 'HalfSpan', 'Wings'])
    world = node(unreal.MaterialExpressionWorldPosition)
    local = node(unreal.MaterialExpressionTransformPosition,
                 transform_source_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,
                 transform_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    assert mel.connect_material_expressions(world, '', local, '')
    assert mel.connect_material_expressions(local, '', wave, 'P')
    assert mel.connect_material_expressions(node(unreal.MaterialExpressionTime), '', wave, 'T')
    for name, default in (('Amplitude', 3.0), ('Rate', 1.0), ('Waves', .8), ('HalfLength', 25.0), ('HalfSpan', 50.0), ('Wings', 0.0)):
        assert mel.connect_material_expressions(node(unreal.MaterialExpressionScalarParameter, parameter_name=name, default_value=default), '', wave, name)
    to_world = node(unreal.MaterialExpressionTransform,
                    transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
                    transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    assert mel.connect_material_expressions(wave, '', to_world, '')
    assert mel.connect_material_property(to_world, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def creature_mesh(name, flat, material):
    """The body from make_fish_models.py, a round trunk inside the inflated fins: nose toward +X, up +Z; a ray lies
    flat, wings along Y."""
    data = json.loads((ART / f'{name}-v1.mesh.json').read_text(encoding='utf-8'))
    b = Builder()
    for (x, y, z), uv in zip(data['verts'], data['uvs']):
        b.vertex((x, -z, y) if flat else (x, y, z), uv=uv)
    for a, c, d, side in data['tris']:
        b.tri(a, c, d, (0, 0, side) if flat else (0, side, 0))
    # The round trunk (make_fish_models.py), each triangle facing its own way out.
    trunk = data.get('trunk', {'verts': []})
    base = len(b.verts)
    for (x, y, z), uv in zip(trunk['verts'], trunk.get('uvs', [])):
        b.vertex((x, y, z), uv=uv)
    for a, c, d, out in trunk.get('tris', []):
        b.tri(base + a, base + c, base + d, tuple(out))
    return write_static_mesh(b, f'{FOLDER}/SM_{name}_v1', [material], 100.0, collision=False), data


def data_asset(folder, name, cls):
    asset = unreal.load_asset(f'{folder}/{name}')
    if asset:
        return asset
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', cls)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    assert asset, name
    return asset


def food_items():
    items = {}
    for key, (display, icon, description) in ITEMS.items():
        texture = import_texture(f'T_{key}_Icon_v1', ICONS / icon)
        item = data_asset(ITEM_FOLDER, f'DA_{key}', unreal.EWItemDefinition)
        for k, v in {'item_id': key, 'display_name': display, 'description': description, 'icon': texture,
                     'category': unreal.EWItemCategory.CONSUMABLE, 'max_stack_size': 20, 'unit_weight': .5}.items():
            item.set_editor_property(k, v)
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
        items[key] = item
    return items


def build_creatures(items):
    mel = unreal.MaterialEditingLibrary
    base = swim_material()
    definitions = {}
    for name, c in CREATURES.items():
        flat = c['swim'][3] == 1
        texture = import_texture(f'T_{name}_v1', ART / f'{name}-v1.png')
        mi = unreal.load_asset(f'{FOLDER}/MI_{name}_v1') or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            f'MI_{name}_v1', FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, base)
        mel.set_material_instance_texture_parameter_value(mi, 'Art', texture)
        mesh, data = creature_mesh(name, flat, mi)
        amplitude, rate, waves, wings = c['swim']
        for param, value in (('Amplitude', amplitude), ('Rate', rate), ('Waves', waves), ('Wings', float(wings)),
                             ('HalfLength', data['length_cm'] * .5), ('HalfSpan', data['height_cm'] * .5)):
            mel.set_material_instance_scalar_parameter_value(mi, param, value)
        mel.update_material_instance(mi)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mi)
        mesh.set_material(0, mi)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)

        definition = data_asset(FOLDER, f'DA_Fish_{name}', unreal.EWFishDefinition)
        swim, dash, turn = c['speeds']
        damage, interval, reach = c['attack']
        item, quantity = c['yield_']
        # A ray's height in the art is its wingspan; lying flat, its body is about a fifth of that thick.
        size = (data['length_cm'], data['height_cm'] * (.2 if flat else 1.0))
        for k, v in {'display_name': c['display'], 'mesh': mesh, 'size': unreal.Vector2D(*size),
                     'water': getattr(unreal.EWWaterKind, c['water']), 'aggressive': c['aggressive'],
                     'swim_speed': float(swim), 'dash_speed': float(dash), 'turn_rate': float(turn),
                     'roam_radius': float(c['roam']), 'min_depth': float(c['depth']), 'max_depth': float(c['deepest']), 'notice_range': float(c['notice']),
                     'attack_damage': float(damage), 'attack_interval': float(interval), 'attack_reach': float(reach),
                     'attack_name': c['attack_name'], 'max_health': float(c['health']),
                     'yield': items[item], 'yield_min': quantity[0], 'yield_max': quantity[1], 'respawn_seconds': 300.0}.items():
            definition.set_editor_property(k, v)
        assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
        definitions[name] = definition
    return definitions


def sea_spots(ground, name, count, depth, keep_away, taken):
    """Open water at least `depth` deep, away from people and from the other creatures."""
    rng = random.Random(sum(map(ord, name)))
    found, tries = [], 0
    while len(found) < count and tries < 20000:
        tries += 1
        x, y = rng.uniform(*SEARCH[0]), rng.uniform(*SEARCH[1])
        floor = ground(x, y)
        if floor is None or floor > SEA - depth:
            continue
        if any(math.hypot(x - px, y - py) < keep_away for px, py in PEOPLE):
            continue
        if any(math.hypot(x - fx, y - fy) < 2500 for fx, fy, _ in taken + found):
            continue
        # Start a little down, clear of the bottom.
        found.append((x, y, max(floor + 150.0, SEA - 250.0)))
    assert len(found) == count, f'only {len(found)} spots for {name}'
    return found


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    items = food_items()
    definitions = build_creatures(items)

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWFish):
            actors.destroy_actor(actor)
    ground = Ground()
    placed, report = [], {}
    for name, (count, depth, keep_away) in PLACEMENT.items():
        spots = sea_spots(ground, name, count, depth, keep_away, placed)
        for k, (x, y, z) in enumerate(spots):
            fish = actors.spawn_actor_from_class(unreal.EWFish, unreal.Vector(x, y, z), unreal.Rotator(0, 0, random.uniform(-180, 180)))
            fish.set_editor_property('definition', definitions[name])
            fish.set_editor_property('surface_z', SEA)
            fish.set_actor_label(f'{CREATURES[name]["display"]} {k + 1}')
            fish.set_folder_path(LEVEL_FOLDER)
        placed += spots
        report[name] = [[round(v) for v in s] for s in spots]
    # The pond's fish, spread about its middle a metre down, living under its surface.
    rng = random.Random(7)
    for name, count in POND_FISH.items():
        report[name] = []
        for k in range(count):
            angle, reach = rng.uniform(0, 2 * math.pi), POND_RADIUS * rng.uniform(.1, .5)
            spot = unreal.Vector(POND[0] + math.cos(angle) * reach, POND[1] + math.sin(angle) * reach, POND_SURFACE - 100)
            fish = actors.spawn_actor_from_class(unreal.EWFish, spot, unreal.Rotator(0, 0, rng.uniform(-180, 180)))
            fish.set_editor_property('definition', definitions[name])
            fish.set_editor_property('surface_z', POND_SURFACE)
            fish.set_actor_label(f'{CREATURES[name]["display"]} {k + 1}')
            fish.set_folder_path(LEVEL_FOLDER)
            report[name].append([round(spot.x), round(spot.y), round(spot.z)])
    assert level.save_current_level()
    Path(unreal.Paths.project_saved_dir(), 'FishResult.json').write_text(json.dumps({'success': True, 'placed': report}, indent=2))
    unreal.log('Fish built and placed')


if __name__ == '__main__':
    main()
