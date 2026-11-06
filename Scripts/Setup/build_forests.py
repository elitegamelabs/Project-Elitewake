"""Dense, varied forests with open ground on every island (owner, November 6). Safe to run again; no world rebuild.
Run forest_plan.py first (it writes Saved/ForestPlan.json), then in the editor, outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"

1. Six models of each tree species: the three made by build_coastal_flora.py plus three more of other proportions here
   (squat and broad, tall and lean, crooked), in the same materials.
2. Removes the old one-actor-per-tree trees (build_coastal_flora.dress_islands) on every island, keeping the starter's
   own authored oaks on its old ground, and any forests from an earlier run.
3. Places the plan's trees as AEWForest stands, one actor per island and model, each tree its own size, girth, height,
   lean and turn; a hatchet turns a tree into an ordinary harvestable tree (C++ AEWForest). Trees keep off rocks and
   gatherable plants already there, and stand on the island's ground as built.
4. Lays the plan's bushes as foliage (walk-through, no collision): FT_ForestBush_*.
Writes Saved/ForestsResult.json. EW_QUIT_WHEN_DONE=1 closes the editor at the end.
"""
import json
import math
import os
import random
import sys
import time
from pathlib import Path
import unreal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_coastal_flora as F  # noqa: E402
import build_grass as G  # noqa: E402
import world_layout as W  # noqa: E402
import world_sublevels as S  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FLORA = '/Game/Elitewake/World/Flora'
LEVEL_FOLDER = 'Coast/Flora/Forests'
PLAN = Path(unreal.Paths.project_saved_dir()) / 'ForestPlan.json'
# The three extra models per species (tuning): squat and broad, tall and lean, crooked or small.
EXTRA = {'Oak': (F.oak, [dict(height=900.0, spread=900.0, limbs=10, seed=44), dict(height=1500.0, spread=560.0, limbs=6, seed=45),
                        dict(height=1150.0, spread=680.0, limbs=7, seed=46)]),
         'Ash': (F.ash, [dict(height=1450.0, reach=420.0, branches=8, seed=54), dict(height=2600.0, reach=360.0, branches=12, seed=55),
                        dict(height=1900.0, reach=300.0, branches=9, seed=56)]),
         'Birch': (F.birch, [dict(height=800.0, reach=190.0, branches=7, seed=24), dict(height=1600.0, reach=230.0, branches=11, seed=25),
                            dict(height=1250.0, reach=280.0, branches=9, seed=26)]),
         'Spruce': (F.spruce, [dict(height=1200.0, reach=320.0, whorls=11, seed=34), dict(height=2700.0, reach=440.0, whorls=22, seed=35),
                              dict(height=2000.0, reach=330.0, whorls=17, seed=36)]),
         'Maravai': (F.maravai, [dict(height=800.0, spread=480.0, limbs=8, seed=14), dict(height=1350.0, spread=420.0, limbs=6, seed=15),
                                dict(height=1000.0, spread=560.0, limbs=7, seed=16)]),
         'Palm': (F.palm, [dict(height=1050.0, lean=330.0, fronds=12, frond=450.0, seed=4), dict(height=520.0, lean=60.0, fronds=15, frond=320.0, seed=5),
                          dict(height=800.0, lean=210.0, fronds=13, frond=400.0, seed=6)])}
MESH_NAME = {'Palm': 'VeyranPalm'}
LEAVES = {'Oak': 'M_OakLeaves_v1', 'Ash': 'M_AshLeaves_v1', 'Birch': 'M_BirchLeaves_v1', 'Spruce': 'M_SpruceNeedles_v1',
          'Maravai': 'M_MaravaiLeaves_v1', 'Palm': 'M_PalmFrond_v1'}
# Trunk at scale 1 (radius, half height, cm; as build_coastal_flora's trees), how far a trunk sinks, and wood at scale 1.
TRUNK = {'Palm': (26.0, 160.0, 8, 8), 'Maravai': (38.0, 220.0, 12, 14), 'Birch': (20.0, 220.0, 10, 8),
         'Spruce': (30.0, 260.0, 12, 12), 'Oak': (52.0, 220.0, 12, 14), 'Ash': (30.0, 260.0, 12, 12)}
BUSHES = 3


def allow_instancing():
    """Tree materials drawn by a forest's instances must say so, or the engine draws its grey checker material instead
    (November 6: leaves and birch bark showed as grey squares)."""
    for asset in unreal.EditorAssetLibrary.list_assets(FLORA, recursive=False):
        material = unreal.load_asset(asset)
        if isinstance(material, unreal.Material) and not material.get_editor_property('used_with_instanced_static_meshes'):
            material.set_editor_property('used_with_instanced_static_meshes', True)
            unreal.MaterialEditingLibrary.recompile_material(material)
            assert unreal.EditorAssetLibrary.save_loaded_asset(material), asset


def models():
    """Every species' six meshes."""
    allow_instancing()
    bark = unreal.load_asset(f'{FLORA}/M_PalmBark_v1')
    birch_bark = unreal.load_asset(f'{FLORA}/M_BirchBark_v1')
    out = {}
    for kind, (make, shapes) in EXTRA.items():
        name = MESH_NAME.get(kind, kind)
        leaves = unreal.load_asset(f'{FLORA}/{LEAVES[kind]}')
        mats = [birch_bark if kind == 'Birch' else bark, leaves]
        assert all(mats), kind
        meshes = [unreal.load_asset(f'{FLORA}/SM_{name}_{k + 1}') for k in range(3)]
        for k, shape in enumerate(shapes):
            path = f'{FLORA}/SM_{name}_{k + 4}'
            if kind == 'Palm':
                meshes.append(F.write_static_mesh(make(**shape), path, mats, 120.0))
            else:
                meshes.append(F.write_tree_mesh(make, shape, path, mats))
        assert all(meshes), kind
        out[kind] = meshes
    return out


class Taken:
    """Rocks, plants and kept trees already in the map, on a 10 m grid: a tree keeps clear of them."""

    def __init__(self):
        self.cells = {}

    def add(self, x, y, r):
        self.cells.setdefault((int(x // 1000), int(y // 1000)), []).append((x, y, r))

    def near(self, x, y, r):
        cx, cy = int(x // 1000), int(y // 1000)
        return any(math.hypot(x - px, y - py) < r + pr for i in (cx - 1, cx, cx + 1) for j in (cy - 1, cy, cy + 1)
                   for px, py, pr in self.cells.get((i, j), ()))


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    assert PLAN.exists(), 'Run python Scripts/Setup/forest_plan.py first (outside Unreal: it uses every core)'
    plan = json.loads(PLAN.read_text())
    meshes = models()
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    keys = [i.key for i in W.ISLANDS]
    removed, taken = 0, Taken()
    for actor in actors.get_all_level_actors():
        if isinstance(actor, unreal.EWForest):
            actors.destroy_actor(actor)
            continue
        label = actor.get_actor_label()
        p = actor.get_actor_location()
        if isinstance(actor, unreal.EWHarvestTree):
            if any(f' {k} ' in f' {label} ' for k in keys):
                actors.destroy_actor(actor)          # an old one-actor tree: the forest replaces it
                removed += 1
            else:
                taken.add(p.x, p.y, 500.0)           # the starter's own oaks stay
        elif isinstance(actor, unreal.EWMineable):
            taken.add(p.x, p.y, 350.0)
        elif isinstance(actor, unreal.EWHandGatherable):
            taken.add(p.x, p.y, 120.0)
    S.use(S.FORESTS)        # forests and bushes live in their own sublevel (the map file nears GitHub's 2 GB limit)
    wood, thatch = unreal.load_asset(F.WOOD), unreal.load_asset(F.THATCH)
    ground = F.Ground()
    report = {'old_trees_removed': removed, 'islands': {}}
    task = unreal.ScopedSlowTask(len(plan), 'Growing the forests')
    task.make_dialog(True)
    for key, stand in plan.items():
        task.enter_progress_frame(1, f'Growing the forests: {key}')
        island = W.island(key)
        groups, skipped = {}, 0
        for kind, variant, x, y, z, yaw, pitch, roll, girth, height in stand['trees']:
            if taken.near(x, y, 150.0):
                skipped += 1
                continue
            g = ground(x, y)
            g = z if g is None else g
            radius, half, sink, _ = TRUNK[kind]
            t = unreal.Transform(unreal.Vector(x, y, g - sink * height), unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw),
                                 unreal.Vector(girth, girth, height))
            groups.setdefault((kind, variant), []).append(t)
        made = {}
        for (kind, variant), transforms in sorted(groups.items()):
            radius, half, _, base_wood = TRUNK[kind]
            forest = actors.spawn_actor_from_class(unreal.EWForest, unreal.Vector(island.cx, island.cy, 0.0), unreal.Rotator())
            forest.set_actor_label(f'Forest {key} {kind} {variant + 1}')
            forest.set_folder_path(LEVEL_FOLDER)
            for prop, value in {'wood': wood, 'thatch': thatch, 'trunk_radius': radius, 'trunk_half_height': half,
                                'base_wood': base_wood, 'base_thatch': max(2, base_wood // 3)}.items():
                forest.set_editor_property(prop, value)
            trees = forest.get_editor_property('trees')
            trees.set_static_mesh(meshes[kind][variant])
            trees.add_instances(transforms, False, True)
            trunks = forest.get_editor_property('trunks')
            cores = []
            for t in transforms:
                s = t.scale3d
                r, h = radius * max(s.x, s.y), half * s.z
                cores.append(unreal.Transform(unreal.Vector(t.translation.x, t.translation.y, t.translation.z + h), unreal.Rotator(),
                                              unreal.Vector(r / 50.0, r / 50.0, h / 50.0)))
            trunks.add_instances(cores, False, True)
            made[f'{kind} {variant + 1}'] = len(transforms)
        report['islands'][key] = {'trees': sum(made.values()), 'skipped_near_rocks_or_plants': skipped, 'by_model': made}
        unreal.log(f'EWFORESTS {key}: {sum(made.values())} trees')
    # Bushes: walk-through foliage, thickest along the forests' edges.
    looks = [G.foliage_type(f'FT_ForestBush_{k + 1}_v1', unreal.load_asset(f'/Game/Elitewake/World/Grass/SM_Bush_{k + 1}_v1')) for k in range(BUSHES)]
    for kind in looks:
        unreal.InstancedFoliageActor.remove_all_instances(world, kind)
    bushes = 0
    for key, stand in plan.items():
        transforms = []
        for x, y, z, yaw, scale in stand['bushes']:
            if taken.near(x, y, 60.0):
                continue
            g = ground(x, y)
            transforms.append(unreal.Transform(unreal.Vector(x, y, (z if g is None else g) - 5), unreal.Rotator(yaw=yaw),
                                               unreal.Vector(scale, scale, scale * random.Random(x * 7 + y).uniform(.85, 1.2))))
        for k, kind in enumerate(looks):
            share = transforms[k::BUSHES]
            if share:
                unreal.InstancedFoliageActor.add_instances(world, kind, share)
        bushes += len(transforms)
        report['islands'].setdefault(key, {})['bushes'] = len(transforms)
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
        for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = comp.get_editor_property('static_mesh')
            if mesh and 'SM_Bush' in mesh.get_name():
                comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    S.save()
    report.update(success=True, trees=sum(v.get('trees', 0) for v in report['islands'].values()), bushes=bushes,
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    Path(unreal.Paths.project_saved_dir(), 'ForestsResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f"EWFORESTS done: {report['trees']} trees, {bushes} bushes, {removed} old trees removed")


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
