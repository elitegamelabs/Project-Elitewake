"""Build the first resources of the Plains arrival (CLAUDE.md Phase 1, slice 2; arrival_layout.FIRST_RESOURCES). Safe to run again.
Run in the editor outside Play, after build_arrival.py:
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -run=pythonscript -script=<this file>

Owner, October 31: the test starter kit is no longer the normal start, so a new survivor makes their first tool by hand:
  - near the spawn, gathered by hand with E: fallen oak sticks, fibre plants, loose stones (a new hand-gathered kind) and a
    berry bush, each pile a different shape, grass cleared round the small ones so they read;
  - the Stone Hatchet recipe (DA_RecipeStoneHatchet: 3 sticks, 2 stones, 4 fibre, 5 s), which a survivor arriving on this
    map knows (UEWArrivalComponent::FirstRecipes, with the Pickaxe from 20 wood);
  - the hatchet item (DA_TestWoodenAxe) becomes the Stone Hatchet: a knapped flint head lashed to its haft
    (build_held_tools.stone_hatchet).
The piles are finite (no regrowth yet). Every amount is tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arrival_layout as A  # noqa: E402
import build_held_tools as H  # noqa: E402
from build_coastal_flora import MAP, Ground, easy_to_aim_at  # noqa: E402
from ship_geometry import TIMBER_MATERIAL, Builder, make_timber_material, write_static_mesh  # noqa: E402
import world_map  # noqa: E402  (opens and saves the map, World Partition or not)

FOLDER = 'World/FirstResources'
ASSETS = '/Game/Elitewake/World/Arrival'
ITEMS = '/Game/Elitewake/Items/Testing'
FLORA = '/Game/Elitewake/World/Flora'
RECIPE = '/Game/Elitewake/Crafting/Testing/DA_RecipeStoneHatchet'
LOOKS = {'LOOSE_STICKS': [f'{FLORA}/SM_FallenSticks_{k}' for k in (1, 2, 3)],
         'PLANT_FIBER': [f'{FLORA}/SM_FiberPlant_{k}' for k in (1, 2, 3)],
         'BERRIES': [f'{FLORA}/SM_BerryBush_{k}' for k in (1, 2)]}
CLEAR = {'LOOSE_STICKS': 130.0, 'LOOSE_STONES': 120.0}   # grass cleared round the small piles, cm


def stone_pile(seed):
    """A heap of loose stones about 80 cm across and a quarter-metre high, readable at 20 m: one broad flat limestone it leans
    on and eight fist- to head-sized stones round it, grey limestone (slot 0) with dark flints among them (slot 1)."""
    rng = random.Random(seed)
    b = Builder()
    for k in range(9):
        b.slot = 1 if k % 3 == 1 else 0
        a, d = rng.uniform(0, 2 * math.pi), (0.0 if k == 0 else rng.uniform(14, 36))
        cx, cy = d * math.cos(a), d * math.sin(a)
        size = 30.0 if k == 0 else rng.uniform(12, 24)
        height = size * (.55 if k == 0 else rng.uniform(.6, .9))
        sides = 7
        radii = [size * rng.uniform(.75, 1.2) for _ in range(sides)]
        turn = rng.uniform(0, 2 * math.pi)
        rings = []
        for share, girth, dry in ((0.0, .9, 0.0), (.45, 1.0, .5), (1.0, .45, 1.0)):
            rings.append([b.vertex((cx + radii[j] * girth * math.cos(turn + 2 * math.pi * j / sides),
                                    cy + radii[j] * girth * math.sin(turn + 2 * math.pi * j / sides), -3 + height * share), 0, 0, dry)
                          for j in range(sides)])
        top = b.vertex((cx, cy, -3 + height * 1.06), 0, 0, 1.0)
        for j in range(sides):
            n = (j + 1) % sides
            out = (math.cos(turn + 2 * math.pi * (j + .5) / sides), math.sin(turn + 2 * math.pi * (j + .5) / sides), .3)
            for lower, upper in zip(rings, rings[1:]):
                b.quad(lower[j], lower[n], upper[n], upper[j], out)
            b.tri(rings[-1][j], rings[-1][n], top, (out[0], out[1], 2.0))
    return b


def aim_box(mesh):
    """Makes sure the pile has its one box for a look to land on: on a mesh made this same run, easy_to_aim_at's box does not
    take (found October 31, the pile had none and E never found it), so the box is written here, round the mesh's bounds.
    Where easy_to_aim_at's box did take (a mesh made on an earlier run), it is set again all the same: the box alone leaves
    the mesh's built collision as it was, without it, so nothing in Play could hit it (found November 1, the yarrow)."""
    body = mesh.get_editor_property('body_setup')
    geo = body.get_editor_property('agg_geom')
    if not geo.get_editor_property('box_elems'):
        bounds = mesh.get_bounds()
        o, e = bounds.get_editor_property('origin'), bounds.get_editor_property('box_extent')
        box = unreal.KBoxElem()
        box.set_editor_property('center', o)
        for axis, half in (('x', e.x), ('y', e.y), ('z', e.z)):
            box.set_editor_property(axis, 2 * half)
        geo.set_editor_property('box_elems', [box])
    body.set_editor_property('agg_geom', geo)                 # setting it rebuilds the collision Play uses
    body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    assert mesh.get_editor_property('body_setup').get_editor_property('agg_geom').get_editor_property('box_elems'), mesh.get_name()
    return mesh


def stone_hatchet_recipe(hatchet):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    folder, name = RECIPE.rsplit('/', 1)
    recipe = unreal.load_asset(RECIPE)
    if not recipe:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', unreal.EWCraftingRecipe)
        recipe = tools.create_asset(name, folder, unreal.EWCraftingRecipe, factory)
    ingredients = []
    for item_name, quantity in A.STONE_HATCHET.items():
        ingredient = unreal.EWCraftingIngredient()
        ingredient.set_editor_property('item', unreal.load_asset(f'{ITEMS}/{item_name}'))
        ingredient.set_editor_property('quantity', quantity)
        ingredients.append(ingredient)
    recipe.set_editor_property('ingredients', ingredients)
    recipe.set_editor_property('output', hatchet)
    recipe.set_editor_property('craft_seconds', 5.0)
    assert unreal.EditorAssetLibrary.save_loaded_asset(recipe)
    return recipe


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert world_map.open_map(level, MAP)
    report = {'removed': [], 'placed': []}
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()).startswith(FOLDER):
            report['removed'].append(actor.get_actor_label())
            actors.destroy_actor(actor)

    # The stone hatchet: its look, its name and the recipe for it.
    timber = unreal.load_asset(TIMBER_MATERIAL) or make_timber_material()   # the shared ship timber, left as it is
    flint = H.flint_material()
    hatchet, _ = H.build_tool('DA_TestWoodenAxe', timber, flint)
    assert unreal.EditorAssetLibrary.save_loaded_asset(hatchet)
    recipe = stone_hatchet_recipe(hatchet)
    report['recipe'] = {i.get_editor_property('item').get_name(): i.get_editor_property('quantity') for i in recipe.get_editor_property('ingredients')}

    limestone = unreal.load_asset(f'{ASSETS}/M_SpringStone_v1')
    assert limestone, 'run build_arrival.py first'
    stones = [aim_box(easy_to_aim_at(write_static_mesh(stone_pile(40 + k), f'{ASSETS}/SM_LooseStones_{k + 1}_v1', [limestone, flint], 30.0)))
              for k in range(2)]
    looks = {kind: [unreal.load_asset(p) for p in paths] for kind, paths in LOOKS.items()}
    looks['LOOSE_STONES'] = stones
    ground = Ground()
    rng = random.Random(3102)
    circles = []
    for k, (label, kind, item_name, x, y, quantity) in enumerate(A.FIRST_RESOURCES):
        item = unreal.load_asset(f'{ITEMS}/{item_name}')
        assert item, item_name
        node = actors.spawn_actor_from_class(unreal.EWHandGatherable, unreal.Vector(x, y, ground(x, y)),
                                             unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
        node.set_actor_label(label)
        node.set_folder_path(FOLDER)
        mesh = node.get_editor_property('mesh')
        mesh.set_static_mesh(looks[kind][k % len(looks[kind])])
        mesh.set_relative_scale3d(unreal.Vector(*[rng.uniform(.95, 1.1)] * 3))
        for prop, value in {'item_definition': item, 'quantity': quantity,
                            'gathering_kind': getattr(unreal.EWHandGatheringKind, kind)}.items():
            node.set_editor_property(prop, value)
        if kind in CLEAR:
            circles.append(unreal.Vector(x, y, CLEAR[kind]))
        report['placed'].append(label)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    report['grass_cleared'] = unreal.EWWorldEditorLibrary.remove_foliage_in_circles(world, circles, 'SM_GrassClump')

    assert world_map.save_map()
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'FirstResourcesResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'First resources built: {len(report["placed"])} placed')


if __name__ == '__main__':
    main()
