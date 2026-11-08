"""Play: the three armor sets (owner, November 8). One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_armor_play.py -Result ArmorPlayResult.json -Players 1 -Standalone 1 -Kit 1
  1. A recipe without its materials cannot be made and takes nothing.
  2. Cloth from fiber; leather from hide at a fire; then all nine pieces through the real crafting path (metal at a fire).
  3. Each piece equips alone into its own slot (helmet, chest, pants), draws shapes on the survivor, and unequips back to the pack.
  4. Full sets: damage stopped 10% cloth, 8% fur, 40% metal; overheating 1.10x, 1.30x, 1.50x; only fur keeps out cold.
     A mixed outfit (metal helmet, fur chest, cloth pants) adds up its pieces.
  5. A 20-point blow takes 20 with nothing worn and 12 in full metal.
  6. On a Winter island the body's target warmth is the same bare, in cloth and in metal, and higher in fur.
  7. Overheating in the Desert: the heat damage multiplier follows the set worn, and health falls faster in metal.
  8. Saved in full metal and put back: the pieces are worn again and drawn.
  9. The furred and hided animals carry their pelts.
Captures in Saved/Screenshots/Armor. Writes Saved/ArmorPlayResult.json.
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
SHOTS = saved / 'Screenshots' / 'Armor'
SHOTS.mkdir(parents=True, exist_ok=True)
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
pack = pawn.get_inventory_component()
needs = pawn.get_survival_component()
ITEMS = '/Game/Elitewake/Items'
RECIPES = '/Game/Elitewake/Crafting/Testing'
SETS = {'Cloth': ('ClothHeadWrap', 'ClothChest', 'ClothPants'), 'Fur': ('FurHood', 'FurJacket', 'FurPants'),
        'Metal': ('MetalTricornHelmet', 'MetalCuirass', 'MetalPants')}
SLOTS = (unreal.EWEquipmentSlot.HEAD, unreal.EWEquipmentSlot.CHEST, unreal.EWEquipmentSlot.LEGS)
EXPECT = {'Cloth': (.10, 1.10, 0.0), 'Fur': (.08, 1.30, 1.0), 'Metal': (.40, 1.50, 0.0)}
report = {'checks': []}
state = {'phase': 'start', 'at': time.monotonic() + 6, 'handle': None, 'queue': [], 'memo': {}}


def load(path):
    return unreal.load_asset(path)


def piece(name):
    return load(f'{ITEMS}/Armor/DA_{name}')


def recipe(name):
    return load(f'{RECIPES}/DA_Recipe{name}')


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    (saved / 'ArmorPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Armor success={error is None} error={error}')


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, f'Shot showui filename="{SHOTS / (name + ".png")}"')


def equip(item, slot):
    return lib.send_verification_equipment_request(pc, item, slot)


def unequip(slot):
    return lib.send_verification_equipment_request(pc, None, slot, True)


def wear(names):
    for name, slot in zip(names, SLOTS):
        if name:
            pack.add_item(piece(name), 1)
            assert equip(piece(name), slot), name


def strip():
    for slot in SLOTS:
        if pawn.get_equipment_component().get_equipped_item(slot):
            unequip(slot)


def worn():
    return [e.get_editor_property('item_definition').get_name() for e in pawn.get_equipment_component().get_equipment_entries()
            if e.get_editor_property('item_definition') and e.get_editor_property('slot') in SLOTS]


def inland(key, depth=2500.0):
    i = W.island(key)
    for k in range(24):
        a = 2 * math.pi * k / 24
        r = i.radius(a) - depth
        x, y = i.cx + r * math.cos(a), i.cy + r * math.sin(a)
        z = T.height(x, y)
        if z > T.SEA + 100:
            return unreal.Vector(x, y, z + 150)
    return unreal.Vector(i.cx, i.cy, T.height(i.cx, i.cy) + 150)


def near_fire():
    at = pawn.get_actor_location()
    state['memo']['fire'] = lib.spawn_verification_campfire(world, unreal.Vector(at.x + 150, at.y, at.z - 90), 900.0)


# ---- the steps: (label, action, wait seconds) -----------------------------------------------------------------------------
def step_recipes():
    for animal in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal):
        animal.destroy_actor()          # nothing to bite the tailor
    for kind, names in SETS.items():
        for name in names:
            r = recipe(name)
            check(f'{name} has a recipe', r is not None and r.get_editor_property('output') == piece(name))
            check(f'{name} is metal at a fire, else by hand', r.get_editor_property('needs_fire') == (kind == 'Metal'))
            pack.unlock_recipe(r)
    for name in ('Cloth', 'Leather'):
        pack.unlock_recipe(recipe(name))
    # Nothing in the pack: not ready, and asking changes nothing.
    r = recipe('ClothHeadWrap')
    check('without materials a piece cannot be made', pack.get_craft_readiness(r) != unreal.EWCraftResult.SUCCESS)
    before = len(pack.get_inventory_entries())
    pc.request_craft(r)
    state['memo']['empty_before'] = before


def step_failed_craft_took_nothing():
    check('a failed craft takes nothing and makes nothing', pack.get_item_count(piece('ClothHeadWrap')) == 0
          and len(pack.get_inventory_entries()) == state['memo']['empty_before'])
    pack.add_item(load(f'{ITEMS}/Testing/DA_TestFiber'), 9)
    pc.request_craft(recipe('Cloth'))


def step_cloth_made():
    cloth = load(f'{ITEMS}/Resources/DA_Cloth')
    check('3 fiber weave 1 cloth', pack.get_item_count(cloth) == 1 and pack.get_item_count(load(f'{ITEMS}/Testing/DA_TestFiber')) == 6,
          cloth=pack.get_item_count(cloth))
    near_fire()
    pack.add_item(load(f'{ITEMS}/Testing/DA_TestHide'), 2)


def step_leather():
    pc.request_craft(recipe('Leather'))


def step_leather_made():
    check('2 hide and 1 fiber make 1 leather at a fire', pack.get_item_count(load(f'{ITEMS}/Resources/DA_Leather')) == 1)
    # Plenty of everything for the nine pieces.
    for path, n in (('Resources/DA_Cloth', 60), ('Resources/DA_Leather', 40), ('Resources/DA_Fur', 30),
                    ('Resources/DA_IronIngot', 40), ('Testing/DA_TestFiber', 30)):
        pack.add_item(load(f'{ITEMS}/{path}'), n)
    state['memo']['to_craft'] = [n for names in SETS.values() for n in names]


def step_craft_next():
    todo = state['memo']['to_craft']
    if not todo:
        return
    name = todo[0]
    check(f'{name} is ready to make', pack.get_craft_readiness(recipe(name)) == unreal.EWCraftResult.SUCCESS,
          readiness=pack.get_craft_readiness(recipe(name)))
    state['memo']['crafting'] = name
    pc.request_craft(recipe(name))
    state['wait'] = recipe(name).get_editor_property('craft_seconds') + 1.5


def step_crafted():
    name = state['memo']['crafting']
    check(f'{name} crafted', pack.get_item_count(piece(name)) == 1, count=pack.get_item_count(piece(name)))
    state['memo']['to_craft'].pop(0)
    if state['memo']['to_craft']:
        state['queue'][0:0] = [('craft', step_craft_next, 0.2), ('crafted', step_crafted, 0.0)]


def step_each_alone():
    for kind, names in SETS.items():
        for name, slot in zip(names, SLOTS):
            check(f'{name} equips into its slot', equip(piece(name), slot) and worn() == [f'DA_{name}'], worn=worn())
            check(f'{name} is drawn on the survivor', pawn.get_armor_piece_count() > 0, shapes=pawn.get_armor_piece_count())
            check(f'{name} unequips back to the pack', unequip(slot) and worn() == [] and pack.get_item_count(piece(name)) == 1
                  and pawn.get_armor_piece_count() == 0)


def step_full_sets():
    sums = {}
    for kind, names in SETS.items():
        for name, slot in zip(names, SLOTS):
            equip(piece(name), slot)
        stop, heat, warm = EXPECT[kind]
        got = (pawn.get_armor_reduction(), pawn.get_overheat_multiplier(), pawn.get_clothing_insulation())
        sums[kind] = [round(v, 3) for v in got]
        check(f'full {kind}: {int(stop * 100)}% stopped, overheating x{heat}, warmth {warm}',
              abs(got[0] - stop) < .002 and abs(got[1] - heat) < .002 and abs(got[2] - warm) < .002, got=got)
        state['memo'].setdefault('shapes', {})[kind] = pawn.get_armor_piece_count()
        strip()
    report['full_sets'] = sums
    # Mixed: metal helmet, fur chest, cloth pants.
    equip(piece('MetalTricornHelmet'), SLOTS[0])
    equip(piece('FurJacket'), SLOTS[1])
    equip(piece('ClothPants'), SLOTS[2])
    got = (pawn.get_armor_reduction(), pawn.get_overheat_multiplier(), pawn.get_clothing_insulation())
    check('a mixed outfit adds its pieces: 15.1% stopped, x1.27, the jacket\'s warmth only',
          abs(got[0] - (.08 + .036 + .035)) < .002 and abs(got[1] - 1.27) < .002 and abs(got[2] - .45) < .002, got=got)
    shot('Mixed_MetalHelmet_FurChest_ClothPants')


def step_blow():
    strip()
    needs.restore_health(1000)
    h = needs.get_health()
    pawn.take_physical_damage(20)
    bare = h - needs.get_health()
    wear(SETS['Metal'])
    needs.restore_health(1000)
    h = needs.get_health()
    pawn.take_physical_damage(20)
    metal = h - needs.get_health()
    check('a 20-point blow: 20 bare, 12 in full metal', abs(bare - 20) < .01 and abs(metal - 12) < .01, bare=bare, metal=metal)
    needs.restore_health(1000)
    shot('Full_Metal')


def wear_set(kind):
    strip()
    if kind:
        for name, slot in zip(SETS[kind], SLOTS):
            if pack.get_item_count(piece(name)) == 0:
                pack.add_item(piece(name), 1)
            equip(piece(name), slot)


def cold_round():
    order = state['memo'].setdefault('cold_order', [None, 'Cloth', 'Metal', 'Fur'])
    kind = order.pop(0)
    wear_set(kind)
    state['memo']['cold_kind'] = kind


def cold_read():
    state['memo'].setdefault('cold', {})[str(state['memo']['cold_kind'])] = needs.get_target_body_temperature()
    if state['memo']['cold_kind'] == 'Fur':
        shot('Full_Fur_Winter')


def step_cold_judge():
    c = state['memo']['cold']
    report['winter_target_body'] = c
    check('in the Winter cold, cloth gives no warmth', abs(c['Cloth'] - c['None']) < .01, cold=c)
    check('metal gives no warmth', abs(c['Metal'] - c['None']) < .01, cold=c)
    check('fur keeps the body warmer', c['Fur'] > c['None'] + .5, cold=c)


def heat_round():
    order = state['memo'].setdefault('heat_order', [None, 'Cloth', 'Fur', 'Metal'])
    kind = order.pop(0)
    wear_set(kind)
    needs.restore_health(1000)
    needs.set_body_temperature(41.5)
    state['memo']['heat_kind'] = kind
    state['memo']['heat_health'] = needs.get_health()


def heat_read():
    kind = str(state['memo']['heat_kind'])
    lost = state['memo']['heat_health'] - needs.get_health()
    state['memo'].setdefault('heat', {})[kind] = (round(needs.get_last_heat_multiplier(), 3), round(lost, 3), needs.is_overheating())
    if kind == 'Cloth':
        shot('Full_Cloth_Desert')


def step_heat_judge():
    h = state['memo']['heat']
    report['desert_overheating'] = h
    for kind, want in (('None', 1.0), ('Cloth', 1.1), ('Fur', 1.3), ('Metal', 1.5)):
        check(f'overheating multiplier {want} for {kind}', abs(h[kind][0] - want) < .002, heat=h[kind])
    check('health falls while overheating', h['None'][1] > 0, heat=h)
    check('and faster in metal than bare', h['Metal'][1] > h['None'][1] * 1.2, heat=h)


def step_save():
    wear_set('Metal')
    pawn.teleport(inland('Starter', 4000), unreal.Rotator())


def step_save2():
    check('saved in full metal', unreal.EWSurvivorSave.save_survivor(pawn, 'ArmorTest', False))
    strip()
    check('stripped before loading', worn() == [])
    check('put back', unreal.EWSurvivorSave.load_save('ArmorTest').apply_to(pawn))


def step_loaded():
    check('the metal set is worn again', sorted(worn()) == sorted(f'DA_{n}' for n in SETS['Metal']), worn=worn())
    check('and drawn', pawn.get_armor_piece_count() == state['memo']['shapes']['Metal'], shapes=pawn.get_armor_piece_count())


def step_pelts():
    fur, hide = load(f'{ITEMS}/Resources/DA_Fur'), load(f'{ITEMS}/Testing/DA_TestHide')
    for species, want in (('Wolf', fur), ('PolarBear', fur), ('Bear', fur), ('Boar', hide), ('Deer', hide)):
        a = load(f'/Game/Elitewake/Wildlife/Animals/DA_Animal_{species}')
        check(f'the {species} carries its pelt', a.get_editor_property('pelt') == want)
    check('birds carry none', load('/Game/Elitewake/Wildlife/Animals/DA_Animal_Pelican').get_editor_property('pelt') is None)


def build_queue():
    q = [('recipes', step_recipes, 1.0), ('failed', step_failed_craft_took_nothing, 4.5), ('cloth', step_cloth_made, 1.5),
         ('leather', step_leather, 7.5), ('leather made', step_leather_made, .5),
         ('craft', step_craft_next, 0.2), ('crafted', step_crafted, 0.0),
         ('each alone', step_each_alone, 1.0), ('full sets', step_full_sets, 2.0), ('blow', step_blow, 2.0),
         ('to winter', lambda: (strip(), pawn.teleport(inland(next(i.key for i in W.ISLANDS if i.region == 'Winter')), unreal.Rotator())), 3.0)]
    for _ in range(4):
        q += [('cold wear', cold_round, 2.0), ('cold read', cold_read, .5)]
    q += [('cold judge', step_cold_judge, .5),
          ('to desert', lambda: (strip(), pawn.teleport(inland(next(i.key for i in W.ISLANDS if i.region == 'Desert')), unreal.Rotator())), 3.0)]
    for _ in range(4):
        q += [('heat wear', heat_round, 3.0), ('heat read', heat_read, .5)]
    q += [('heat judge', step_heat_judge, .5), ('save', step_save, 3.0), ('save2', step_save2, 2.0), ('loaded', step_loaded, .5),
          ('pelts', step_pelts, .5)]
    return q


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        if state['phase'] == 'start':
            state['queue'] = build_queue()
            state['phase'] = 'run'
        if not state['queue']:
            finish()
            return
        label, action, wait = state['queue'].pop(0)
        state['wait'] = None
        action()
        state['at'] = time.monotonic() + (state['wait'] if state.get('wait') else wait)
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
