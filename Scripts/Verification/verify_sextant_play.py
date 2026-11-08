"""Play: the sextant (FUTURE_IMPLEMENTATIONS Part 8, 09; November 8). One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_sextant_play.py -Result SextantPlayResult.json -Players 1 -Standalone 1 -Kit 1
  1. Without a sextant in hand the HUD shows no latitude.
  2. Crafted at a fire from 3 copper ingots, 1 iron ingot and 1 wood, then held in the main hand.
  3. Its reading on the starter island, a Winter island and a Swamp island: north reads higher, south lower, each as the
     chart's formula gives it (18 N at the origin, a degree per kilometre).
Writes Saved/SextantPlayResult.json; a capture in Saved/Screenshots/Sextant.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
(saved / 'Screenshots' / 'Sextant').mkdir(parents=True, exist_ok=True)
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
pack = pawn.get_inventory_component()
ITEMS = '/Game/Elitewake/Items'
sextant = unreal.load_asset(f'{ITEMS}/Tools/DA_Sextant')
recipe = unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipeSextant')
report = {'checks': [], 'readings': {}}
state = {'phase': 0, 'at': time.monotonic() + 6, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'SextantPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Sextant success={error is None} error={error}')


def hud():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world, unreal.EWSurvivalWidget, False) if w.is_in_viewport())


def inland(key, depth=2500.0):
    i = W.island(key)
    for k in range(24):
        a = 2 * math.pi * k / 24
        r = i.radius(a) - depth
        x, y = i.cx + r * math.cos(a), i.cy + r * math.sin(a)
        if T.height(x, y) > T.SEA + 100:
            return unreal.Vector(x, y, T.height(x, y) + 150)
    return unreal.Vector(i.cx, i.cy, T.height(i.cx, i.cy) + 150)


def expected(location):
    lat = 18.0 + location.y / 100000.0
    d = int(math.floor(abs(lat)))
    m = round((abs(lat) - d) * 60)
    if m == 60:
        d, m = d + 1, 0
    return f"{d}°{m:02d}' {'N' if lat >= 0 else 'S'}"


PLACES = [('Starter', 'Starter'), ('Winter', next(i.key for i in W.ISLANDS if i.region == 'Winter' and i.key == 'Winter4')),
          ('Swamp', 'Swamp4')]


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            for animal in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal):
                animal.destroy_actor()
            check('without a sextant no latitude is shown', hud().get_displayed_latitude() == '')
            check('the recipe needs a fire', recipe.get_editor_property('needs_fire'))
            pack.unlock_recipe(recipe)
            for path, n in (('Resources/DA_CopperIngot', 3), ('Resources/DA_IronIngot', 1), ('Testing/DA_TestWood', 1)):
                pack.add_item(unreal.load_asset(f'{ITEMS}/{path}'), n)
            at = pawn.get_actor_location()
            lib.spawn_verification_campfire(world, unreal.Vector(at.x + 150, at.y, at.z - 90), 600.0)
            state.update(phase=1, at=time.monotonic() + 1.5)
        elif p == 1:
            check('beside the fire it can be made', pack.get_craft_readiness(recipe) == unreal.EWCraftResult.SUCCESS,
                  readiness=pack.get_craft_readiness(recipe))
            pc.request_craft(recipe)
            state.update(phase=2, at=time.monotonic() + recipe.get_editor_property('craft_seconds') + 2)
        elif p == 2:
            check('a sextant is made', pack.get_item_count(sextant) == 1)
            check('held in the main hand', lib.send_verification_equipment_request(pc, sextant, unreal.EWEquipmentSlot.MAIN_HAND))
            state.update(phase=3, at=time.monotonic() + 1, place=0)
        elif p == 3:
            name, key = PLACES[state['place']]
            pawn.teleport(inland(key), unreal.Rotator())
            state.update(phase=4, at=time.monotonic() + 3)
        elif p == 4:
            name, key = PLACES[state['place']]
            shown, want = hud().get_displayed_latitude(), expected(pawn.get_actor_location())
            report['readings'][name] = shown
            check(f'the sextant reads {want} on {name}', shown == want, shown=shown)
            if name == 'Starter':
                unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{saved / "Screenshots" / "Sextant" / "Starter.png"}"')
            state['place'] += 1
            state.update(phase=3 if state['place'] < len(PLACES) else 5, at=time.monotonic() + 1)
        else:
            r = report['readings']
            lat = lambda s: float(s.split('°')[0]) + float(s.split('°')[1][:2]) / 60   # noqa: E731
            check('north reads higher and south lower', lat(r['Winter']) > lat(r['Starter']) > lat(r['Swamp']), readings=r)
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
