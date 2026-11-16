"""Slice 3: playable boots/accessory, real UI, owner/server replication, appearance and layout.
Fresh standalone or host/client PIE. EW_PLAY_STARTER_KIT=0. No survivor saves or asset edits.
"""
import json
import time
import traceback
from pathlib import Path
import unreal as u

lib = u.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
pcs = [u.GameplayStatics.get_player_controller(w, 0) for w in worlds]
pc = next((c for c in pcs if not c.has_authority()), pcs[0])
world = worlds[pcs.index(pc)]
server = next(w for w, c in zip(worlds, pcs) if c.has_authority())


def pid(p):
    return json.loads(u.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


pawn = pc.get_controlled_pawn()
owner = next(p for p in u.GameplayStatics.get_all_actors_of_class(server, u.EWCharacter) if pid(p) == pid(pawn))
pack = owner.get_inventory_component()
gear = owner.get_equipment_component()
slots = [u.EWEquipmentSlot.HEAD, u.EWEquipmentSlot.CHEST, u.EWEquipmentSlot.LEGS,
         u.EWEquipmentSlot.FEET, u.EWEquipmentSlot.ACCESSORY]
recipes = [u.load_asset('/Game/Elitewake/Crafting/Testing/DA_Recipe' + n) for n in ('LeatherSeaBoots', 'LeatherWristCuff')]
boots, cuff = [r.get_editor_property('output') for r in recipes]
leather = u.load_asset('/Game/Elitewake/Items/Resources/DA_Leather')
fiber = u.load_asset('/Game/Elitewake/Items/Testing/DA_TestFiber')
for e in list(gear.get_equipment_entries()):
    gear.unequip_item(e.get_editor_property('slot'))
for e in list(pack.get_inventory_entries()):
    pack.remove_item(e.get_editor_property('item_definition'), e.get_editor_property('quantity'))
for r in recipes:
    pack.unlock_recipe(r)
pack.add_item(leather, 6)
pack.add_item(fiber, 6)
result = Path(u.Paths.project_saved_dir(), 'InventoryEquipmentSlotsNetworkResult.json'
              if len(worlds) > 1 else 'InventoryEquipmentSlotsPlayResult.json')
folder = Path(u.Paths.project_saved_dir(), 'Screenshots', 'InventorySlice3')
folder.mkdir(parents=True, exist_ok=True)
state = dict(step=0, at=time.monotonic() + 2)
report = dict(success=False, network=len(worlds) > 1, checks=[], error=None)


def menu():
    return next(w for w in u.WidgetLibrary.get_all_widgets_of_class(world, u.EWInventoryWidget, False)
                if w.is_in_viewport() and w.get_owning_player() == pc)


def check(label, condition):
    report['checks'].append(dict(check=label, passed=bool(condition)))
    assert condition, label


def key(name):
    assert lib.send_verification_ui_key(pc, name)


def select_item(item):
    menu().set_inventory_search(str(item.get_editor_property('display_name')))
    menu().focus_inventory()
    for _ in range(12):
        if menu().get_selected_index() == 0:
            break
        key('Left' if menu().get_selected_index() > 0 else 'Right')
    key('Enter')
    assert menu().get_selected_item_definition() == item


def click_slot(slot):
    widget = menu().get_equipment_slot_widget(slot)
    assert widget
    assert lib.click_verification_widget(menu(), widget.get_fname())


def wears(slot, item):
    return all(p.get_equipment_component().get_equipped_item(slot) == item for p in (owner, pawn))


def parts(p, item):
    tag = str(item.get_editor_property('item_id'))
    return [c for c in p.get_components_by_class(u.StaticMeshComponent)
            if tag in list(map(str, c.get_editor_property('component_tags')))]


def shot(name):
    if len(worlds) == 1:
        assert lib.capture_verification_play_viewport(world, str(folder / (name + '.png')))


def finish(error=None):
    pc.set_inventory_open(False)
    report['error'] = error
    report['success'] = error is None
    result.write_text(json.dumps(report, indent=2))
    u.unregister_slate_post_tick_callback(handle)


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        n = state['step']
        delay = .7
        if n == 0:
            lib.resize_verification_play_viewport(world, 1920, 1080)
            pc.set_inventory_open(True)
            check('Five real equipment slots exist', all(menu().get_equipment_slot_widget(s) for s in slots))
            starts = list(map(str, u.get_default_object(u.EWArrivalComponent).get_editor_property('first_recipes')))
            check('Both recipes are included in arrival baseline', all(any(r.get_name() in s for s in starts) for r in recipes))
            delay = 1
        elif n == 1:
            click_slot(slots[3])
            check('Empty boots slot accepts mouse selection', menu().get_selected_item_definition() is None)
            state['boots_index'] = menu().get_selected_index()
            key('Gamepad_DPad_Right')
            check('Controller reaches empty accessory slot', menu().get_selected_index() == state['boots_index'] + 1)
            key('Gamepad_FaceButton_Left')
            check('Empty slot action does not invent an item', not gear.get_equipment_entries())
            menu().set_recipe_search('Leather Sea Boots')
            menu().focus_crafting()
            key('R')
            check('Boots card uses actual recipe ingredients', 'Need 4' in str(menu().get_recipe_card_requirements())
                  and 'Have 6' in str(menu().get_recipe_card_requirements()))
            key('Enter')
            delay = 9
        elif n == 2:
            check('Boots crafted once with actual cost and time', pack.get_item_count(boots) == 1
                  and pack.get_item_count(leather) == 2 and pack.get_item_count(fiber) == 2)
            select_item(boots)
            key('R')
            delay = 1.5
        elif n == 3:
            check('Keyboard equips boots on server and owner', wears(slots[3], boots) and pack.get_item_count(boots) == 0)
            check('Boots produce real world mesh parts', all(len(parts(p, boots)) == 4 for p in (owner, pawn)))
            check('Boots apply existing protection and insulation', abs(owner.get_armor_reduction() - .01) < .001
                  and abs(owner.get_clothing_insulation() - .05) < .001)
            menu().set_inventory_search('')
            menu().set_recipe_search('Leather Wrist Cuff')
            menu().focus_crafting()
            key('Gamepad_FaceButton_Left')
            key('Gamepad_FaceButton_Bottom')
            delay = 7.5
        elif n == 4:
            check('Accessory crafted through existing controller crafting', pack.get_item_count(cuff) == 1
                  and pack.get_item_count(leather) == 0 and pack.get_item_count(fiber) == 0)
            select_item(cuff)
            key('Gamepad_FaceButton_Left')
            delay = 1.5
        elif n == 5:
            check('Controller equips appended accessory slot', wears(slots[4], cuff) and pack.get_item_count(cuff) == 0)
            check('Accessory mesh is attached on both peers', all(len(parts(p, cuff)) == 1
                  and str(parts(p, cuff)[0].get_attach_socket_name()) == 'hand_l' for p in (owner, pawn)))
            check('Cosmetic accessory does not invent attribute buffs', abs(owner.get_armor_reduction() - .01) < .001)
            check('Worn item weight is counted on server and owner', all(abs(p.get_survival_component().get_carried_weight() - 1.5) < .02 for p in (owner, pawn)))
            for name in ('ClothHeadWrap', 'ClothChest', 'ClothPants'):
                item = u.load_asset('/Game/Elitewake/Items/Armor/DA_' + name)
                pack.add_item(item, 1)
                gear.equip_item(item, item.get_editor_property('equipment_slot'))
            menu().set_inventory_search('')
            menu().set_recipe_search('')
            delay = 2
        elif n == 6:
            check('Five worn positions coexist', all(p.get_equipment_component().get_equipped_item(s) for p in (owner, pawn) for s in slots))
            pants = u.load_asset('/Game/Elitewake/Items/Armor/DA_ClothPants')
            check('Separate boots suppress pants included shoes', all(len(parts(p, pants)) == 5 for p in (owner, pawn)))
            check('Full-body live preview remains present', menu().has_survivor_portrait())
            shot('Inventory-Five-Slots-1920x1080')
            lib.resize_verification_play_viewport(world, 1280, 720)
            delay = 1.5
        elif n == 7:
            shot('Inventory-Five-Slots-1280x720')
            click_slot(slots[4])
        elif n == 8:
            assert lib.click_verification_widget(menu(), 'EquipmentAction')
            delay = 1.5
        elif n == 9:
            check('Mouse unequips accessory through actual action button', wears(slots[4], None)
                  and pack.get_item_count(cuff) == 1 and not parts(pawn, cuff))
            click_slot(slots[3])
            key('Gamepad_FaceButton_Left')
            delay = 1.5
        elif n == 10:
            pants = u.load_asset('/Game/Elitewake/Items/Armor/DA_ClothPants')
            check('Controller unequips boots without losing item', wears(slots[3], None) and pack.get_item_count(boots) == 1)
            check('Original pants footwear returns when boots removed', all(len(parts(p, pants)) == 7 for p in (owner, pawn)))
            check('Removing boots restores existing armor values', abs(owner.get_armor_reduction() - .1) < .001)
            finish()
            return
        state['step'] += 1
        state['at'] = time.monotonic() + delay
    except Exception:
        finish(traceback.format_exc())


handle = u.register_slate_post_tick_callback(tick)
