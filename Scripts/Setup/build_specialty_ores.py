"""The islands' mined specialties (CLAUDE.md 5.7; November 7): copper ore, iron ore, sulfur ore, salt, amber and bog iron as
mineable deposits on their islands only (world_specialty_ores.py). Safe to run again: it replaces only its own deposits; no
world rebuild. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"
EW_QUIT_WHEN_DONE=1 closes the editor at the end.

Makes each ore's item (Items/Resources), a lumpy outcrop mesh and a rock material in the ore's colours (green-streaked
copper, rust-red iron, yellow sulfur, white salt crust, honey amber, dark rusty bog iron), and places AEWMineable nodes on
the ground (ray-cast on the built island meshes), bedded in and leaning with the slope. Mining: any pickaxe for most; a
Metal pickaxe or better for sulfur (CLAUDE.md 4). A node holds 4 to 8 and comes back an hour after it is emptied.
The deposits are always loaded, like everything but the ground cover. Writes Saved/SpecialtyOresResult.json.
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
import world_specialty_ores as O  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ores'
ITEM_FOLDER = '/Game/Elitewake/Items/Resources'
LEVEL_FOLDER = 'Coast/Resources/SpecialtyOres'
# dark, light (linear), roughness, sparkle; outcrop size (cm)
LOOKS = {'CopperOre': ((.03, .04, .035), (.06, .22, .17), .8, .6, 1.0),
         'IronOre': ((.05, .02, .012), (.25, .08, .03), .85, .4, 1.0),
         'SulfurOre': ((.18, .15, .02), (.6, .52, .05), .7, .3, .9),
         'Salt': ((.4, .4, .38), (.75, .75, .72), .6, 1.0, .7),
         'Amber': ((.2, .08, .01), (.7, .35, .04), .25, 1.5, .75),
         'BogIron': ((.03, .02, .012), (.14, .06, .02), .9, .2, .8)}
# What a Port's resource trader pays for one (Copper; tuning, beside the generic ore's 12, coal's 6 and a gem's 60).
PRICES = {'CopperOre': 10, 'IronOre': 10, 'SulfurOre': 18, 'Salt': 6, 'Amber': 40, 'BogIron': 6}


def outcrop(seed, size):
    """A low cluster of lumps, the biggest in the middle, most of it above the ground."""
    rng = random.Random(seed)
    b = Builder()
    lump(b, (0, 0, 22 * size), (60 * size, 50 * size, 40 * size), rng, rough=.35, rows=8, cols=12)
    for _ in range(3):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(40, 60) * size
        lump(b, (math.cos(a) * r, math.sin(a) * r, 10 * size), (rng.uniform(22, 34) * size, rng.uniform(20, 30) * size, rng.uniform(16, 26) * size),
             rng, rough=.35, rows=7, cols=10)
    return b


def item(key):
    name, description = O.ORES[key][0], O.ORES[key][1]
    path = f'{ITEM_FOLDER}/DA_{key}'
    asset = unreal.load_asset(path)
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(f'DA_{key}', ITEM_FOLDER, unreal.EWItemDefinition, factory)
    for k, v in {'item_id': key, 'display_name': name, 'description': description, 'category': unreal.EWItemCategory.RESOURCE,
                 'max_stack_size': 50, 'unit_weight': .5 if key != 'Salt' else .2, 'sell_value_copper': PRICES[key]}.items():
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
    rng = random.Random(1107)
    report = {'ores': {}}
    for key, (dark, light, rough, sparkle, size) in LOOKS.items():
        material = rock_material(f'{FOLDER}/M_{key}_v1', dark, light, rough, sparkle)
        meshes = [write_static_mesh(outcrop(sum(map(ord, key)) + k, size), f'{FOLDER}/SM_{key}_{k + 1}_v1', [material], 100.0)
                  for k in range(2)]
        resource = item(key)
        tier = getattr(unreal.EWPickaxeTier, O.ORES[key][2])
        report['ores'][key] = {}
        for island, nodes in O.PLAN[key].items():
            made = 0
            for n, (x, y) in enumerate(nodes):
                z = ground(x, y)
                zx, zy = ground(x + 80, y), ground(x, y + 80)
                if z is None or zx is None or zy is None:
                    continue
                # Lean with the slope, half way to upright.
                nx, ny = -(zx - z) / 80, -(zy - z) / 80
                pitch = math.degrees(math.atan(ny)) * .5
                roll = -math.degrees(math.atan(nx)) * .5
                node = actors.spawn_actor_from_class(unreal.EWMineable, unreal.Vector(x, y, z - 12),
                                                     unreal.Rotator(roll=pitch, pitch=roll, yaw=rng.uniform(0, 360)))
                node.set_actor_label(f'{O.ORES[key][0]} Deposit {island} {n + 1}')
                node.set_folder_path(f'{LEVEL_FOLDER}/{key}')
                mesh = node.get_editor_property('mesh')
                mesh.set_static_mesh(meshes[n % 2])
                scale = rng.uniform(.85, 1.25)
                mesh.set_relative_scale3d(unreal.Vector(scale, scale, scale))
                mesh.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                for k, v in {'resource': resource, 'minimum_pickaxe_tier': tier, 'respawn_when_depleted': True,
                             'respawn_seconds': 3600.0, 'randomize_stock': True, 'minimum_stock': 4, 'maximum_stock': 8,
                             'per_strike': 2}.items():
                    node.set_editor_property(k, v)
                world_map.keep_loaded(node)
                made += 1
            report['ores'][key][island] = made
            unreal.log(f'EWORES {key} {island}: {made}')
    assert world_map.save_map()
    report.update(success=True, nodes=sum(sum(v.values()) for v in report['ores'].values()),
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    Path(unreal.Paths.project_saved_dir(), 'SpecialtyOresResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f"EWORES done: {report['nodes']} deposits")


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
