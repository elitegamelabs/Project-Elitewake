"""Fresh Lvl_M5PickupTest PIE: standalone or in-process listen/client.
Normal input and owned-controller RPCs; opt-in finite tree and saved test assets.
"""
import unreal, json, os, datetime, traceback
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert len(worlds) in (1,2)
controllers = [unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
server = next(w for w,c in zip(worlds,controllers) if c.has_authority())
network = len(worlds)==2
pc = next((c for c in controllers if not c.has_authority()),controllers[0])
local_world = worlds[controllers.index(pc)]
character_cls = unreal.load_class(None,'/Script/EW.EWCharacter')
tree_cls = unreal.load_class(None,'/Script/EW.EWHarvestTree')
pickup_cls = unreal.load_class(None,'/Script/EW.EWPickup')
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
thatch = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestThatch')
hatchet = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatchet')
assert wood and thatch and hatchet
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
player_id = pid(pc.get_controlled_pawn())
server_pawns = unreal.GameplayStatics.get_all_actors_of_class(server,character_cls)
owner = next(p for p in server_pawns if pid(p)==player_id)
inventory = owner.get_inventory_component()
assert all(not p.get_inventory_component().get_inventory_entries() for p in server_pawns), 'Use fresh Play'
widget_cls = unreal.load_class(None,'/Script/EW.EWInteractionWidget')
widget = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(local_world,widget_cls,False) if w.get_owning_player()==pc)
settings = unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
old_network = [(w,lib.get_verification_network_settings(w)) for w in worlds] if network else []
for w,_ in old_network: lib.set_verification_network_settings(w,100,1)
pc.set_inventory_open(False)
for c in controllers: lib.flush_verification_input(c)
for a in unreal.GameplayStatics.get_all_actors_of_class(server,pickup_cls): a.destroy_actor()
for w in worlds:
    for p in unreal.GameplayStatics.get_all_actors_of_class(w,character_cls):
        p.teleport(unreal.Vector(0,0,96) if pid(p)==player_id else unreal.Vector(-500,500,96),unreal.Rotator())
for c in controllers: c.set_control_rotation(unreal.Rotator())
tree, fixtures, walls, steps = None, [], [], []
report={'success':False,'network':network,'lag_ms':100 if network else 0,'loss_percent':1 if network else 0,
        'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checkpoints':[],'errors':[]}
path=os.path.join(unreal.Paths.project_saved_dir(),'HatchetNetworkResult.json' if network else 'HatchetPlayResult.json')
def valid(a):
    try: return a is not None and unreal.SystemLibrary.is_valid(a)
    except (TypeError,RuntimeError): return False
def step(action,delay=1.25): steps.append((action,delay))
def spawn(x=150):
    global tree
    if valid(tree): tree.destroy_actor()
    tree=lib.spawn_verification_harvest_tree(server,unreal.Vector(x,0,160),wood,thatch)
    fixtures.append(tree)
def trees(w): return unreal.GameplayStatics.get_all_actors_of_class(w,tree_cls)
def peer(w): return next(a for a in trees(w) if a.get_name()==tree.get_name())
def request(): assert lib.send_verification_attack(pc,peer(local_world))
def tap(key): assert lib.send_verification_ui_key(pc,key)
def check(label,expected_wood,expected_thatch,pool_wood,pool_thatch,prompt=None):
    rows=[{str(pid(p)):[p.get_inventory_component().get_item_count(wood),p.get_inventory_component().get_item_count(thatch)] for p in unreal.GameplayStatics.get_all_actors_of_class(w,character_cls)} for w in worlds]
    assert all(r==rows[0] for r in rows),label+': inventory replication differs '+str(rows)
    assert all(sum(v[0] for v in r.values())==expected_wood and sum(v[1] for v in r.values())==expected_thatch for r in rows),label+': inventory totals differ '+str(rows)
    pools=[[sum(a.get_editor_property('wood_remaining') for a in trees(w)),sum(a.get_editor_property('thatch_remaining') for a in trees(w))] for w in worlds]
    assert all(v==[pool_wood,pool_thatch] for v in pools),label+': pool differs '+str(pools)
    text=str(widget.get_displayed_prompt())
    if prompt is not None: assert (prompt in text) if prompt else not text,label+': prompt differs '+text
    assert abs(owner.get_survival_component().get_carried_weight()-(inventory.get_total_weight()+owner.get_equipment_component().get_total_weight()))<.001
    report['checkpoints'].append({'label':label,'inventory_by_world':rows,'pools':pools,'prompt':text})
def equip(): assert lib.send_verification_equipment_request(pc,hatchet,unreal.EWEquipmentSlot.MAIN_HAND)
def turn(yaw):
    for c in controllers: c.set_control_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0))
def blocker():
    for w in worlds:
        a=lib.spawn_verification_box(w,unreal.Vector(75,0,160),unreal.Vector(10,100,100),unreal.Rotator()); walls.append(a); fixtures.append(a)
def remove_walls():
    for a in walls:
        if valid(a): a.destroy_actor()
    walls.clear()
def empty_resources():
    for p in server_pawns:
        for item in (wood,thatch): p.get_inventory_component().remove_item(item,100000)
def compete():
    empty_resources()
    for p in server_pawns:
        if not p.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND):
            p.get_inventory_component().add_item(hatchet,1); p.get_equipment_component().equip_item(hatchet,unreal.EWEquipmentSlot.MAIN_HAND)
    for w in worlds:
        for p in unreal.GameplayStatics.get_all_actors_of_class(w,character_cls): p.teleport(unreal.Vector(0,-60 if pid(p)==player_id else 60,96),unreal.Rotator())
    tree.set_actor_scale3d(unreal.Vector(1,5,2)); turn(0)
def compete_requests():
    for c,w in zip(controllers,worlds): assert lib.send_verification_attack(c,peer(w))

step(spawn); step(request); step(lambda:check('Bare hands gated',0,0,12,4,''))
step(lambda:inventory.add_item(hatchet,1)); step(request); step(lambda:check('Inventory-only hatchet rejected',0,0,12,4))
step(equip); step(lambda:check('Equipped hatchet enables Attack hint',0,0,12,4,''))
step(lambda:tap('E')); step(lambda:check('E cannot harvest',0,0,12,4))
step(lambda:tap('LeftMouseButton')); step(lambda:check('Mouse Attack grants wood and thatch',3,1,9,3))
step(lambda:tap('Gamepad_RightTrigger')); step(lambda:check('RT Attack and device hint',6,2,6,2,''))
step(request,.05); step(request,1.3); step(lambda:check('Rapid duplicate request rejected',9,3,3,1))
step(lambda:tap('I')); step(request); step(lambda:check('Menu blocks forged Attack',9,3,3,1,'')); step(lambda:tap('I')); step(lambda:turn(0))
step(lambda:turn(90)); step(request); step(lambda:check('Aim rejects Attack',9,3,3,1,'')); step(lambda:turn(0))
step(blocker); step(request); step(lambda:check('Wall rejects Attack',9,3,3,1,'')); step(remove_walls)
step(lambda:spawn(450)); step(request); step(lambda:check('Range rejects Attack',9,3,12,4,''))
step(spawn); step(lambda:owner.get_survival_component().apply_damage(100)); step(request); step(lambda:check('Death rejects Attack',9,3,12,4,'')); step(lambda:owner.get_survival_component().restore_health(100))
step(empty_resources); step(lambda:inventory.add_item(wood,5999)); step(request); step(lambda:check('Partial strike preserves rejected wood/thatch',6000,0,11,4))
step(request); step(lambda:check('Full inventory preserves both pools',6000,0,11,4))
step(empty_resources); step(spawn); step(compete); step(compete_requests); step(lambda:check('Two strikes conserve a shared tree',3*len(worlds),len(worlds),12-3*len(worlds),4-len(worlds)))

index,next_time,handle=0,unreal.GameplayStatics.get_time_seconds(server)+1,None
def finish():
    unreal.unregister_slate_post_tick_callback(handle)
    for c in controllers: lib.flush_verification_input(c)
    if pc.get_interaction_component().is_menu_blocked(): tap('I')
    owner.get_survival_component().restore_health(100)
    empty_resources()
    for p in server_pawns:
        p.get_equipment_component().unequip_item(unreal.EWEquipmentSlot.MAIN_HAND); p.get_inventory_component().remove_item(hatchet,100)
    for a in fixtures:
        if valid(a): a.destroy_actor()
    for w,old in old_network: lib.set_verification_network_settings(w,old.x,old.y)
    settings.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
    report['success']=not report['errors'] and index==len(steps)
    report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(path,'w') as f: json.dump(report,f,indent=2)
def tick(delta):
    global index,next_time
    try:
        assert all(w in lib.get_play_worlds() for w in worlds),'Play ended during verification'
        now=unreal.GameplayStatics.get_time_seconds(server)
        if now<next_time:return
        if index==len(steps):finish();return
        action,delay=steps[index];action();index+=1;next_time=now+delay
    except Exception:
        report['errors'].append(traceback.format_exc());finish()
handle=unreal.register_slate_post_tick_callback(tick)
