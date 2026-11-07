"""Play: smelting at a fire (November 7). One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_smelting_play.py -Result SmeltingPlayResult.json -Players 1 -Standalone 1
  1. With iron ore and wood but no fire, the Iron Ingot recipe needs a fire.
  2. Beside a lit campfire it is ready; crafting takes 2 iron ore and 1 wood and gives 1 iron ingot.
  3. The Metalwork skill lists the smelting recipes.
Writes Saved/SmeltingPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
pack = pawn.get_inventory_component()
load = unreal.load_asset
recipe = load('/Game/Elitewake/Crafting/Testing/DA_RecipeIronIngot')
ore, wood, ingot = load('/Game/Elitewake/Items/Resources/DA_IronOre'), load('/Game/Elitewake/Items/Testing/DA_TestWood'), load('/Game/Elitewake/Items/Resources/DA_IronIngot')
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 2, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    (saved / 'SmeltingPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Smelting success={error is None} error={error}')


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            for f in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWCampfire):
                f.destroy_actor()
            check('the Iron Ingot recipe exists and needs a fire', recipe is not None and recipe.get_editor_property('needs_fire'))
            pack.unlock_recipe(recipe)
            for item, n in ((ore, 2), (wood, 1)):
                pack.remove_item(item, 100000)
                check(f'carrying {n} {item.get_name()}', pack.add_item(item, n) == n)
            pack.remove_item(ingot, 100000)
            check('without a fire the recipe needs one', pack.get_craft_readiness(recipe) == unreal.EWCraftResult.NEEDS_FIRE,
                  readiness=pack.get_craft_readiness(recipe))
            at = pawn.get_actor_location() + pawn.get_actor_forward_vector() * 150
            fire = lib.spawn_verification_campfire(world, unreal.Vector(at.x, at.y, at.z - 90), 600.0)
            state.update(fire=fire, phase=1, at=time.monotonic() + 1.0)
        elif p == 1:
            check('the campfire is lit', state['fire'].is_lit())
            check('beside the fire the recipe is ready', pack.get_craft_readiness(recipe) == unreal.EWCraftResult.SUCCESS,
                  readiness=pack.get_craft_readiness(recipe))
            pc.request_craft(recipe)
            state.update(phase=2, at=time.monotonic() + recipe.get_editor_property('craft_seconds') + 2.0)
        else:
            check('smelting gives an iron ingot', pack.get_item_count(ingot) == 1, ingots=pack.get_item_count(ingot))
            check('and uses 2 iron ore and 1 wood', pack.get_item_count(ore) == 0 and pack.get_item_count(wood) == 0,
                  ore=pack.get_item_count(ore), wood=pack.get_item_count(wood))
            node = next(n for n in unreal.EWSkillTree.get_nodes() if str(n.get_editor_property('id')) == 'Metalwork') \
                if hasattr(unreal, 'EWSkillTree') and hasattr(unreal.EWSkillTree, 'get_nodes') else None
            if node is not None:
                names = [str(r.get_asset_name()) for r in node.get_editor_property('recipes')]
                check('Metalwork unlocks the smelting recipes', 'DA_RecipeIronIngot' in names and 'DA_RecipeCopperIngot' in names, recipes=names)
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
