"""Ice sheets on the Winter mountains (owner, November 6: different sheets of ice around the Winter mountains only, like
the real Arctic, as tall as the nearest cliff or landing; the ice is solid; not literal blocks). Safe to run again; no
world rebuild. Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"

The sheets' shapes come from glacier_shapes.py (plain Python): several separate sheets round each mountain, each the slope
smoothed and raised by a thickness near the height of its nearest cliff or bank (12-45 m), ending in a steep ice wall.
Here each becomes its own mesh with full collision (a survivor cannot pass through it and can climb onto and stand on
it), blue ice on the walls and in the cracks and snow on the tops, placed in the forests' sublevel (world_sublevels.py).
Trees, bushes, rocks, plants and animals under the ice are removed. Writes Saved/GlaciersResult.json.
EW_QUIT_WHEN_DONE=1 closes the editor at the end.
"""
import json
import math
import os
import sys
import time
from pathlib import Path
import unreal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_coastal_rocks as R  # noqa: E402
import glacier_shapes as G  # noqa: E402
import world_layout as W  # noqa: E402
import world_sublevels as S  # noqa: E402
import world_terrain as T  # noqa: E402
from ship_geometry import Builder, material_builder, write_static_mesh  # noqa: E402

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
FOLDER = '/Game/Elitewake/World/Glaciers'
LEVEL_FOLDER = 'Coast/Winter/Glaciers'


def ice_material():
    """Glacier ice: pale blue faces, deep blue in the cracks and toward the base, snow on the tops; glossy ice, matte snow."""
    mel = unreal.MaterialEditingLibrary
    material, node, custom = material_builder(f'{FOLDER}/M_GlacierIce_v1')
    material.set_editor_property('tangent_space_normal', False)
    position = node(unreal.MaterialExpressionWorldPosition)
    normal = node(unreal.MaterialExpressionVertexNormalWS)
    flags = node(unreal.MaterialExpressionVertexColor)
    colour = custom(R.NOISE + """
float big = r.fbm(P / 260.0), mid = r.fbm(P / 40.0), fine = r.n(P / 2.0);
float3 deep = float3(.05, .16, .30), pale = float3(.42, .62, .76), white = float3(.80, .86, .92);
float3 c = lerp(deep, pale, saturate(big * 1.6 - .2 + F.b * .6));
float band = sin(P.z / 55.0 + big * 9.0) * .5 + .5;              // the glacier's layers
c *= lerp(.82, 1.08, band) * lerp(.9, 1.06, mid);
c = lerp(c, deep * .7, saturate(r.cracks(P / 3.0)) * .8);        // crevasses
float snow = saturate((N.z - .55) * 4.0) * saturate(r.fbm(P / 120.0) * 2.2 - .1);
c = lerp(c, white * lerp(.9, 1.03, fine), snow);
return c;""", unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'N', 'F'))
    rough = custom(R.NOISE + 'float snow = saturate((N.z - .55) * 4.0) * saturate(r.fbm(P / 120.0) * 2.2 - .1);'
                   ' return lerp(.12 + r.n(P / 9.0) * .12, .8, snow);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, ('P', 'N'))
    bumped = custom(R.NOISE + """
float e = 2.0, h0 = r.height(P / 3.0);
float3 g = float3(r.height((P + float3(e, 0, 0)) / 3.0) - h0, r.height((P + float3(0, e, 0)) / 3.0) - h0, r.height((P + float3(0, 0, e)) / 3.0) - h0) / e;
g -= N * dot(g, N);
return normalize(N - g * 6.0);""", unreal.CustomMaterialOutputType.CMOT_FLOAT3, ('P', 'N'))
    for target, pins in ((colour, ('P', 'N', 'F')), (rough, ('P', 'N')), (bumped, ('P', 'N'))):
        for pin in pins:
            assert mel.connect_material_expressions({'P': position, 'N': normal, 'F': flags}[pin], '', target, pin), pin
    assert mel.connect_material_property(colour, '', unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    assert mel.connect_material_property(bumped, '', unreal.MaterialProperty.MP_NORMAL)
    mel.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def sheet_mesh(sheet):
    """The sheet's points as a mesh about its centre: the ice's top and, where it meets the sunken rim, its walls."""
    cx, cy = sheet['centre']
    b = Builder()
    index = {}
    for key, (x, y, z, on) in sheet['cells'].items():
        crack = .5 + .5 * math.sin(x * .004 + y * .0027) * math.sin(y * .005 - x * .0013)
        index[key] = b.vertex((x - cx, y - cy, z), 0.0, 0.0, .55 + .3 * crack if on else .15)
    for (i, j) in sheet['cells']:
        quad = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        if all(q in index for q in quad) and any(sheet['cells'][q][3] for q in quad):
            a, c, d, e = (index[q] for q in quad)
            b.quad(a, c, d, e, (0.0, 0.0, 1.0))
    return b


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    ice = ice_material()
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()) == LEVEL_FOLDER:
            actors.destroy_actor(actor)
    for old in unreal.EditorAssetLibrary.list_assets(FOLDER, recursive=False):
        if 'SM_GlacierBlock_' in old:
            unreal.EditorAssetLibrary.delete_asset(old)         # the first, block-shaped try of November 6
    S.use(S.FORESTS)        # the ice lives in the forests' sublevel (the map file nears GitHub's 2 GB limit)
    report, spots = {'islands': {}}, []
    for island in [i for i in W.ISLANDS if i.region == 'Winter']:
        sheets = G.plan_island(island, T.height)
        for n, sheet in enumerate(sheets):
            mesh = write_static_mesh(sheet_mesh(sheet), f'{FOLDER}/SM_IceSheet_{island.key}_{n + 1}', [ice], 400.0, split_angle=50.0)
            cx, cy = sheet['centre']
            actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(cx, cy, 0.0), unreal.Rotator())
            actor.set_actor_label(f'Ice Sheet {island.key} {n + 1}')
            actor.set_folder_path(LEVEL_FOLDER)
            comp = actor.static_mesh_component
            comp.set_static_mesh(mesh)
            comp.set_mobility(unreal.ComponentMobility.STATIC)
            # Solid ice (owner, November 6): it blocks survivors, animals, the camera and aiming alike.
            comp.set_collision_profile_name('BlockAll')
            spots += [(x, y) for (x, y, z, on) in sheet['cells'].values() if on]
        report['islands'][island.key] = [{'area_m2': s['area_m2'], 'thick_m': s['thick_m']} for s in sheets]
        unreal.log(f'EWGLACIERS {island.key}: {len(sheets)} ice sheets')
    # Clear what stood where the ice now is.
    cells = {(int(x // G.CELL), int(y // G.CELL)) for x, y in spots}

    def under(x, y):
        i, j = int(x // G.CELL), int(y // G.CELL)
        return any((i + di, j + dj) in cells for di in (-1, 0, 1) for dj in (-1, 0, 1))
    removed = {'trees': 0, 'bushes': 0, 'actors': 0}
    for forest in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWForest):
        if ' Winter' not in forest.get_actor_label():
            continue
        trees, trunks = forest.get_editor_property('trees'), forest.get_editor_property('trunks')
        doomed = []
        for i in range(trees.get_instance_count()):
            t = trees.get_instance_transform(i, True)
            t = t[-1] if isinstance(t, tuple) else t
            if under(t.translation.x, t.translation.y):
                doomed.append(i)
        if doomed:
            trees.remove_instances(doomed)
            trunks.remove_instances(doomed)
            removed['trees'] += len(doomed)
    xs, ys = [x for x, _ in spots], [y for _, y in spots]
    for foliage in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.InstancedFoliageActor):
        for comp in foliage.get_components_by_class(unreal.InstancedStaticMeshComponent):
            found = set()
            for x, y in spots[::40]:
                for z in (0.0, 10000.0, 20000.0, 30000.0):
                    found.update(comp.get_instances_overlapping_sphere(unreal.Vector(x, y, z), 9000.0, True))
            doomed = []
            for i in sorted(found):
                t = comp.get_instance_transform(i, True)
                t = t[-1] if isinstance(t, tuple) else t
                if t and under(t.translation.x, t.translation.y):
                    doomed.append(i)
            if doomed:
                comp.remove_instances(doomed)
                removed['bushes'] += len(doomed)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, (unreal.EWMineable, unreal.EWHandGatherable, unreal.EWHarvestTree, unreal.EWAnimal)):
            p = actor.get_actor_location()
            if under(p.x, p.y):
                actors.destroy_actor(actor)
                removed['actors'] += 1
    S.save()
    report.update(success=True, sheets=sum(len(v) for v in report['islands'].values()), removed=removed,
                  finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    Path(unreal.Paths.project_saved_dir(), 'GlaciersResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f"EWGLACIERS done: {report['sheets']} ice sheets; removed {removed}")


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
