"""Fresh isolated-map listen/client Play: craft generated-icon tools, equip, harvest.
All grants/unlocks/nodes are temporary fixtures; no production prologue trigger.
"""
import unreal, json, time
from pathlib import Path
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds()
pcs=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
assert len(worlds)==2 and all('Lvl_M5PickupTest' in w.get_name() for w in worlds)
client=next(c for c in pcs if not c.has_authority())
server=next(w for w,c in zip(worlds,pcs) if c.has_authority())
local=worlds[pcs.index(client)]
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
owner=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if pid(p)==pid(client.get_controlled_pawn()))
inv=owner.get_inventory_component()
assert not inv.get_inventory_entries() and not inv.get_available_recipes()
items={n:unreal.load_asset('/Game/Elitewake/Items/Testing/DA_Test'+n) for n in ['Wood','Thatch','Stone','WoodenAxe','WoodenPickaxe','WoodenShovel','HideWaterFlask','InnTorch']}
recipes={n:unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_Recipe'+n) for n in ['WoodenAxe','WoodenPickaxe']}
for _r in recipes.values(): _r.set_editor_property('craft_seconds',0.2)  # crafting takes seconds now; these checks are about what it makes (verify_craft_time_play times it)
icons={n:unreal.load_asset('/Game/Elitewake/UI/PlaceholderIcons/T_'+t+'_v1') for n,t in [('WoodenAxe','Axe'),('WoodenPickaxe','Pickaxe'),('WoodenShovel','Shovel'),('HideWaterFlask','Flask'),('InnTorch','Torch')]}
assert all(items.values()) and all(recipes.values()) and all(icons.values())
assert inv.add_item(items['Wood'],40)==40
for r in recipes.values(): assert inv.unlock_recipe(r)
# The retained diagnostic map includes pickups on the same aim line as our temporary nodes.
# Clear only PIE instances; never edit or save the map.
for pickup in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWPickup): pickup.destroy_actor()
for w in worlds:
    for p in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.EWCharacter):
        p.teleport(unreal.Vector(0,0,96) if pid(p)==pid(owner) else unreal.Vector(-500,500,96),unreal.Rotator())
for c in pcs: c.set_control_rotation(unreal.Rotator())
phase=0; next_at=time.monotonic()+3; handle=None; target=None; checks=[]
def peer(cls): return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(local,cls) if a.get_name()==target.get_name())
def count(n): return inv.get_item_count(items[n])
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    if target and unreal.SystemLibrary.is_valid(target): target.destroy_actor()
    Path(unreal.Paths.project_saved_dir(),'StarterToolLoopResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at,target
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0:
            client.set_inventory_open(True)
            assert lib.send_verification_ui_key(client,'Tab')
            assert lib.send_verification_ui_key(client,'Enter')
        elif phase==1:
            assert count('Wood')==20 and count('WoodenAxe')==1
            checks.append('Client crafts wooden axe for exactly 20 generic Wood')
            assert lib.send_verification_ui_key(client,'Down')
            assert lib.send_verification_ui_key(client,'Enter')
        elif phase==2:
            assert count('Wood')==0 and count('WoodenPickaxe')==1
            checks.append('Client crafts wooden pickaxe for remaining 20 Wood')
            client.set_inventory_open(False)
            for n in ['WoodenShovel','HideWaterFlask','InnTorch']: assert inv.add_item(items[n],1)==1
        elif phase==3: client.set_inventory_open(True)
        elif phase==4:
            menu=next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(local,unreal.EWInventoryWidget,False) if w.get_owning_player()==client and w.is_in_viewport())
            # Each item shows its own icon (the item art replaced the generated placeholders, 3b3e942).
            for n in icons: assert items[n].get_editor_property('icon') and menu.get_displayed_inventory_icon(items[n])==items[n].get_editor_property('icon'),n
            checks.append('All five item icons resolve in owning-client inventory')
            for slot,n in enumerate(icons): assert lib.send_verification_hotbar_request(client,slot,items[n],False)
            client.set_inventory_open(False)
        elif phase==5: assert lib.send_verification_hotbar_request(client,0,None,True)
        elif phase==6:
            assert owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)==items['WoodenAxe']
            assert count('WoodenAxe')==0
            checks.append('Hotbar equips the crafted axe without duplicating its unit')
            target=lib.spawn_verification_harvest_tree(server,unreal.Vector(150,0,160),items['Wood'],items['Thatch'])
            assert target
        elif phase==7: assert lib.send_verification_attack(client,peer(unreal.EWHarvestTree))
        elif phase==8:
            assert count('Wood')==3 and count('Thatch')==1
            assert target.get_editor_property('wood_remaining')==9 and target.get_editor_property('thatch_remaining')==3
            checks.append('Crafted axe harvests through owned Attack and conserves existing fixture pool')
            target.destroy_actor()
            target=lib.spawn_verification_mineable(server,unreal.Vector(150,0,160),items['Stone'],12)
        elif phase==9: assert lib.send_verification_attack(client,peer(unreal.EWMineable))
        elif phase==10:
            assert count('Stone')==0 and target.get_editor_property('remaining')==12
            checks.append('Equipped axe cannot mine stone')
            assert lib.send_verification_hotbar_request(client,1,None,True)
        elif phase==11:
            assert owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)==items['WoodenPickaxe']
            assert count('WoodenAxe')==1 and count('WoodenPickaxe')==0
            assert lib.send_verification_attack(client,peer(unreal.EWMineable))
        elif phase==12:
            assert count('Stone')==3 and target.get_editor_property('remaining')==9
            assert client.get_controlled_pawn().get_inventory_component().get_item_count(items['Stone'])==3
            assert client.get_controlled_pawn().get_hotbar_component().get_selected_slot()==1
            host=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if p!=owner)
            assert not host.get_inventory_component().get_inventory_entries() and not host.get_inventory_component().get_available_recipes()
            checks.append('Crafted pickaxe mines through owned Attack; output, pool and selection replicate; host stays independent')
            finish();return
        phase+=1
    except Exception as exc: finish('Phase '+str(phase)+': '+repr(exc))
handle=unreal.register_slate_post_tick_callback(tick)
