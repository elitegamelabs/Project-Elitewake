"""The islands' gathered specialties (CLAUDE.md 5.7; November 7): clay, sand, reeds, peat, spruce resin, mushrooms, dates,
coconuts, wild fruit, spices and vines, gathered by hand with E on their islands only (world_gathered_specialties.py). Safe to
run again: it replaces only its own patches; no world rebuild. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"
EW_QUIT_WHEN_DONE=1 closes the editor at the end.

Makes each item (Items/Resources; dates, coconuts and wild fruit are food that spoils like berries), a placeholder look for
each (lumpy piles for clay, sand, peat, resin, dates, coconuts and fruit, a tinted plant for reeds, vines and spices, a
mushroom cluster), and places AEWHandGatherable patches on the ground (ray-cast on the built island meshes). Each patch
holds a few units (no regrowth yet, like every hand-gathered resource). A Port's resource trader buys them. Always loaded.
Writes Saved/GatheredSpecialtiesResult.json.
"""
import json
import math
import os
import random
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, write_static_mesh  # noqa: E402
from build_crystals import lump, rock_material  # noqa: E402
from build_coastal_flora import MAP, Ground  # noqa: E402
import world_map  # noqa: E402
import world_gathered_specialties as G  # noqa: E402

FOLDER = '/Game/Elitewake/World/Gathered'
ITEM_FOLDER = '/Game/Elitewake/Items/Resources'
FLORA = '/Game/Elitewake/World/Flora'
LEVEL_FOLDER = 'Coast/Resources/GatheredSpecialties'
SPOILED = '/Game/Elitewake/Items/Testing/DA_TestToxicBerry'
# dark, light (linear), roughness, sparkle; the shape
LOOKS = {'Clay': ((.2, .08, .04), (.35, .16, .08), .5, .2, 'pile'),
         'Sand': ((.45, .38, .25), (.6, .52, .36), .9, .3, 'mound'),
         'Reeds': ((.12, .14, .05), (.3, .32, .12), .7, 0, 'plant'),
         'Peat': ((.03, .02, .012), (.08, .05, .03), .95, 0, 'pile'),
         'Resin': ((.25, .1, .01), (.6, .3, .03), .2, 1.5, 'drops'),
         'Mushrooms': ((.3, .22, .14), (.55, .5, .4), .7, 0, 'mushrooms'),
         'Dates': ((.15, .06, .02), (.3, .12, .03), .4, .3, 'drops'),
         'Coconuts': ((.12, .07, .03), (.25, .16, .08), .8, 0, 'nuts'),
         'WildFruit': ((.45, .2, .02), (.7, .45, .05), .4, .2, 'drops'),
         'Spices': ((.25, .08, .03), (.4, .2, .05), .8, 0, 'plant'),
         'Vines': ((.03, .08, .02), (.08, .18, .04), .8, 0, 'plant')}
# What a Port's resource trader pays for one (Copper; tuning).
PRICES = {'Clay': 2, 'Sand': 1, 'Reeds': 1, 'Peat': 3, 'Resin': 6, 'Mushrooms': 4, 'Dates': 3, 'Coconuts': 4, 'WildFruit': 3,
          'Spices': 15, 'Vines': 2}


def shape(kind, seed):
    rng = random.Random(seed)
    b = Builder()
    if kind == 'pile':          # a low heap of lumps about 70 cm across
        lump(b, (0, 0, 8), (34, 30, 14), rng, rough=.3, rows=7, cols=10)
        for _ in range(4):
            a = rng.uniform(0, 2 * math.pi)
            lump(b, (math.cos(a) * 28, math.sin(a) * 28, 5), (14, 12, 8), rng, rough=.3, rows=6, cols=8)
    elif kind == 'mound':       # a soft mound of sand
        lump(b, (0, 0, 4), (60, 50, 16), rng, rough=.15, rows=8, cols=12)
    elif kind == 'drops':       # a scatter of small round pieces (fruit, dates, resin beads)
        for _ in range(9):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 26)
            s = rng.uniform(4, 7)
            lump(b, (math.cos(a) * r, math.sin(a) * r, s * .8), (s * 1.3, s, s), rng, rough=.1, rows=5, cols=7)
    elif kind == 'nuts':        # three coconuts
        for k in range(3):
            a = k * 2.1 + rng.uniform(-.3, .3)
            lump(b, (math.cos(a) * 18, math.sin(a) * 18, 11), (13, 12, 11), rng, rough=.12, rows=6, cols=9)
    elif kind == 'mushrooms':   # a cluster of stems and caps
        for _ in range(6):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 18)
            x, y, h = math.cos(a) * r, math.sin(a) * r, rng.uniform(8, 16)
            lump(b, (x, y, h / 2), (2.5, 2.5, h / 2), rng, rough=.05, rows=5, cols=6)
            lump(b, (x, y, h), (rng.uniform(6, 10), rng.uniform(6, 10), 3), rng, rough=.1, rows=5, cols=8)
    return b


def item(key):
    name, description, _, food = G.ITEMS[key][:4]
    path = f'{ITEM_FOLDER}/DA_{key}'
    asset = unreal.load_asset(path)
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(f'DA_{key}', ITEM_FOLDER, unreal.EWItemDefinition, factory)
    props = {'item_id': key, 'display_name': name, 'description': description, 'max_stack_size': 50, 'unit_weight': .2,
             'sell_value_copper': PRICES[key]}
    if food:
        props.update(category=unreal.EWItemCategory.CONSUMABLE, food_kind=unreal.EWFoodKind.BERRY, food_consumption_enabled=True,
                     hunger_restore_fraction=food['hunger'], health_restore_fraction=food['health'],
                     fresh_lifetime_seconds=float(food['fresh']), spoiled_item_definition=unreal.load_asset(SPOILED))
    else:
        props.update(category=unreal.EWItemCategory.RESOURCE)
    for k, v in props.items():
        asset.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()).startswith(LEVEL_FOLDER):
            actors.destroy_actor(actor)
    ground = Ground()
    rng = random.Random(1171)
    plants = [unreal.load_asset(f'{FLORA}/SM_FiberPlant_{k}') for k in (1, 2, 3)]
    report = {'items': {}}
    for key, (dark, light, rough, sparkle, form) in LOOKS.items():
        material = rock_material(f'{FOLDER}/M_{key}_v1', dark, light, rough, sparkle)
        if form == 'plant':
            meshes = plants
        else:
            meshes = [write_static_mesh(shape(form, sum(map(ord, key)) + k), f'{FOLDER}/SM_{key}_{k + 1}_v1', [material], 100.0)
                      for k in range(2)]
            for m in meshes:
                # A simple box as well, so the aim (a simple-collision trace) finds the patch, not only complex traces.
                unreal.EditorStaticMeshLibrary.remove_collisions(m)
                unreal.EditorStaticMeshLibrary.add_simple_collisions(m, unreal.ScriptCollisionShapeType.BOX)
                m.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
                assert unreal.EditorAssetLibrary.save_loaded_asset(m)
        resource = item(key)
        name, _, kind, _, _, _, _, _, (low, high) = G.ITEMS[key]
        report['items'][key] = {}
        for island, nodes in G.PLAN[key].items():
            made = 0
            for n, (x, y) in enumerate(nodes):
                z = ground(x, y)
                if z is None:
                    continue
                node = actors.spawn_actor_from_class(unreal.EWHandGatherable, unreal.Vector(x, y, z - 2),
                                                     unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
                node.set_actor_label(f'{name} Patch {island} {n + 1}')
                node.set_folder_path(f'{LEVEL_FOLDER}/{key}')
                mesh = node.get_editor_property('mesh')
                mesh.set_static_mesh(meshes[n % len(meshes)])
                if form == 'plant':
                    for slot in range(mesh.get_num_materials()):
                        mesh.set_material(slot, material)
                scale = rng.uniform(.9, 1.15)
                mesh.set_relative_scale3d(unreal.Vector(scale, scale, scale))
                for prop, value in {'item_definition': resource, 'quantity': rng.randint(low, high),
                                    'gathering_kind': getattr(unreal.EWHandGatheringKind, kind)}.items():
                    node.set_editor_property(prop, value)
                world_map.keep_loaded(node)
                made += 1
            report['items'][key][island] = made
            unreal.log(f'EWGATHERED {key} {island}: {made}')
    assert world_map.save_map()
    report.update(success=True, patches=sum(sum(v.values()) for v in report['items'].values()),
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    Path(unreal.Paths.project_saved_dir(), 'GatheredSpecialtiesResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f"EWGATHERED done: {report['patches']} patches")


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
