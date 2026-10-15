"""One continuous, fresh Lvl_M5PickupTest PIE acceptance flow.
Standalone or in-process listen/client. Items come from world interactions;
inventory selection, hotbar assignment/activation and unequip use normal Slate input.
Fixture placement is isolated test arrangement, not production-world traversal.
"""
import unreal, json, os, datetime, traceback
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds()
assert len(worlds) in (1,2) and all('Lvl_M5PickupTest' in w.get_name() for w in worlds)
controllers=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
server=next(w for w,c in zip(worlds,controllers) if c.has_authority())
pc=next((c for c in controllers if not c.has_authority()),controllers[0])
world=worlds[controllers.index(pc)]; pawn=pc.get_controlled_pawn()
def pid(p):return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
owner_id=pid(pawn)
characters=lambda w:unreal.GameplayStatics.get_all_actors_of_class(w,unreal.EWCharacter)
owner=next(p for p in characters(server) if pid(p)==owner_id)
assert all(not p.get_inventory_component().get_inventory_entries() and not p.get_equipment_component().get_equipment_entries() for p in characters(server)), 'Use fresh empty Play'
items={k:unreal.load_asset('/Game/Elitewake/Items/Testing/DA_Test'+n) for k,n in
       [('fiber','Fiber'),('sticks','Sticks'),('hatchet','Hatchet'),('pickaxe','Pickaxe'),('wood','Wood'),('thatch','Thatch'),('stone','Stone'),('ore','Ore'),('berry','AzulBerry')]}
assert all(items.values())
def widget(name):
    cls=unreal.load_class(None,'/Script/EW.'+name)
    return next((u for u in unreal.WidgetLibrary.get_all_widgets_of_class(world,cls,False) if u.get_owning_player()==pc and u.is_in_viewport()),None)
prompt=widget('EWInteractionWidget'); hud=widget('EWSurvivalWidget')
assert prompt and hud and widget('EWHotbarWidget')
settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
old_network=[(w,lib.get_verification_network_settings(w)) for w in worlds] if len(worlds)==2 else []
for w,_ in old_network:assert lib.set_verification_network_settings(w,100,1)
saved_stats=[(p.get_survival_component(),p.get_survival_component().get_hydration()) for p in characters(server)]
for c in controllers:lib.flush_verification_input(c)
pc.set_inventory_open(False)
for a in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWPickup):a.destroy_actor()
for w in worlds:
    for p in characters(w):p.teleport(unreal.Vector(0,0,96) if pid(p)==owner_id else unreal.Vector(-500,500,96),unreal.Rotator())
for c in controllers:c.set_control_rotation(unreal.Rotator())
fixtures=[]; source=None; steps=[]; expected={k:0 for k in items}; bindings={}; equipped=None
report={'success':False,'network':len(worlds)==2,'lag_ms':100 if old_network else 0,'loss_percent':1 if old_network else 0,
        'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checkpoints':[],'errors':[]}
path=os.path.join(unreal.Paths.project_saved_dir(),'IntegratedNetworkResult.json' if old_network else 'IntegratedPlayResult.json')
def valid(a):
    try:return a is not None and unreal.SystemLibrary.is_valid(a)
    except (TypeError,RuntimeError):return False
def step(action,delay=1.25):steps.append((action,delay))
def key(name):assert lib.send_verification_ui_key(pc,name)
def turn():
    for c in controllers:c.set_control_rotation(unreal.Rotator())
def spawn(kind):
    global source
    if valid(source):source.destroy_actor()
    location=unreal.Vector(150,0,160)
    if kind in ('fiber','sticks','berry'):
        source=lib.spawn_verification_hand_gatherable(server,location,items[kind],6 if kind=='sticks' else 10,kind=='sticks')
        if kind=='berry':source.set_editor_property('gathering_kind',unreal.EWHandGatheringKind.BERRIES);source.force_net_update()
    elif kind in ('hatchet','pickaxe'):source=lib.spawn_verification_pickup(server,location,items[kind],1)
    elif kind=='tree':source=lib.spawn_verification_harvest_tree(server,location,items['wood'],items['thatch'])
    elif kind in ('stone','ore'):source=lib.spawn_verification_mineable(server,location,items[kind])
    elif kind=='water':source=lib.spawn_verification_water_source(server,location,True)
    elif kind=='hold':source=lib.spawn_verification_interactable(server,location,False,True,False,1.2)
    assert source;fixtures.append(source)
def peer():return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,source.get_class()) if a.get_name()==source.get_name())
def select(item,gear=False):
    ui=widget('EWInventoryWidget');assert ui
    entries=pawn.get_inventory_component().get_inventory_entries()
    index=len(entries) if gear else next(i for i,e in enumerate(entries) if e.item_definition==items[item])
    delta=index-ui.get_selected_index()
    for _ in range(abs(delta)):key('Down' if delta>0 else 'Up')
    key('Enter')
def check(label,changes=None,tool='keep',opened=False,hint=None,stock=None,hydration=None):
    global equipped
    if changes:expected.update(changes)
    if tool!='keep':equipped=tool
    states=[]
    for w in worlds:
        p=next(p for p in characters(w) if pid(p)==owner_id)
        inv=p.get_inventory_component();eq=p.get_equipment_component()
        main=eq.get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)
        assert main==(items[equipped] if equipped else None),label+': equipment differs'
        counts={k:inv.get_item_count(v)+(1 if main==v else 0) for k,v in items.items()}
        assert counts==expected,label+': owned totals differ '+str(counts)
        weight=inv.get_total_weight()+eq.get_total_weight()
        assert abs(weight-p.get_survival_component().get_carried_weight())<.001,label+': composite weight differs'
        if hydration is not None:assert abs(p.get_survival_component().get_hydration()-hydration)<.01,label+': hydration differs'
        for other in characters(w):
            if pid(other)!=owner_id:assert not other.get_inventory_component().get_inventory_entries() and not other.get_equipment_component().get_equipment_entries(),label+': foreign player changed'
        states.append({'counts':counts,'equipped':equipped,'weight':weight})
    for p in (owner,pawn):
        h=p.get_hotbar_component()
        assert all(h.get_bound_item(i)==(items[bindings[i]] if i in bindings else None) for i in range(8)),label+': hotbar differs'
    ui=widget('EWInventoryWidget')
    assert bool(ui)==opened,label+': inventory lifecycle differs'
    assert pc.is_move_input_ignored()==opened and pc.is_look_input_ignored()==opened,label+': input isolation differs'
    if opened:assert ui.has_user_focus(pc),label+': inventory focus lost'
    text=str(prompt.get_displayed_prompt())
    if hint is not None:assert (hint in text) if hint else not text,label+': prompt differs '+text
    if stock is not None:
        assert all(next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,source.get_class()) if a.get_name()==source.get_name()).get_editor_property(stock[0])==stock[1] for w in worlds),label+': source stock differs'
    summary=str(hud.get_displayed_summary())
    assert 'Weight '+format(states[0]['weight'],'.1f')+' /' in summary,label+': rendered weight differs '+summary
    if hydration is not None:assert 'Hydration '+str(int(hydration))+'%' in summary,label+': rendered hydration differs'
    report['checkpoints'].append({'label':label,'states':states,'prompt':text,'hud':summary,'open':opened})
    with open(path,'w') as f:json.dump(report,f,indent=2)
def bound(slot,item):bindings[slot]=item
def details(label):
    ui=widget('EWInventoryWidget');assert ui and ui.is_showing_details(),label+': details not visible'
    check(label,opened=True)
def close():key('I');turn()
def blocked_attack():assert lib.send_verification_attack(pc,peer())
def hold_check():
    assert source.get_acknowledgement_count()==1 and peer().get_acknowledgement_count()==1
    check('Held interaction completes once after gathering')

step(lambda:check('Fresh survivor, empty inventory and hotbar'))
for kind,count,button in [('fiber',10,'E'),('sticks',6,'Gamepad_FaceButton_Left'),('hatchet',1,'E'),('pickaxe',1,'Gamepad_FaceButton_Left')]:
    step(lambda k=kind:spawn(k));step(lambda b=button:key(b),1.9);step(lambda k=kind,n=count:check('Collect '+k,{k:n}))
step(lambda:key('I'));step(lambda:check('Inventory opens over populated HUD',opened=True))
step(lambda:select('hatchet'));step(lambda:details('Inspect collected hatchet'))
step(lambda:key('One'));step(lambda:bound(0,'hatchet'),.1);step(lambda:check('Assign hatchet to hotbar through inventory',opened=True))
step(lambda:select('pickaxe'));step(lambda:details('Inspect collected pickaxe'))
step(lambda:key('Two'));step(lambda:bound(1,'pickaxe'),.1);step(lambda:check('Assign pickaxe to hotbar through inventory',opened=True))
step(close);step(lambda:key('One'));step(lambda:check('Hotbar equips owned hatchet',tool='hatchet'))
step(lambda:spawn('tree'));step(lambda:check('Tree recognizes equipped hatchet',hint='Left Mouse: Chop tree'))
step(lambda:key('E'));step(lambda:check('Interact cannot harvest tree',stock=('wood_remaining',12)))
step(lambda:key('LeftMouseButton'));step(lambda:check('Chop transfers wood and thatch',{'wood':3,'thatch':1},stock=('wood_remaining',9)))
step(lambda:key('I'));step(blocked_attack);step(lambda:check('Inventory blocks Attack while retaining gear/resources',opened=True,stock=('wood_remaining',9)))
step(close);step(lambda:key('LeftMouseButton'));step(lambda:check('Closing inventory restores Attack',{'wood':6,'thatch':2},stock=('wood_remaining',6)))
step(lambda:key('Two'));step(lambda:check('Hotbar swaps hatchet for pickaxe without loss',tool='pickaxe'))
step(lambda:spawn('stone'));step(lambda:key('Gamepad_RightTrigger'));step(lambda:check('Pickaxe mines stone through RT',{'stone':3},hint='RT: Mine resource',stock=('remaining',9)))
step(lambda:spawn('ore'));step(lambda:key('LeftMouseButton'));step(lambda:check('Same pickaxe mines authored ore',{'ore':3},stock=('remaining',9)))
step(lambda:spawn('berry'));step(lambda:key('E'),1.9);step(lambda:check('Gather berries while pickaxe stays equipped',{'berry':10},hint=''))
step(lambda:key('I'));step(lambda:select('berry'));step(lambda:details('Inspect berry food alongside gathered materials'))
step(lambda:key('Three'));step(lambda:bound(2,'berry'),.1);step(lambda:check('Assign berry shortcut through inventory',opened=True))
step(close);step(lambda:key('Three'));step(lambda:check('Unsupported eating preserves berries and gear'))
step(lambda:owner.get_survival_component().set_hydration(25));step(lambda:spawn('water'));step(lambda:check('Water prompt with gathered inventory retained',hydration=25,hint='Drink'))
step(lambda:key('Gamepad_FaceButton_Left'));step(lambda:check('X drinks fresh water and updates HUD',hydration=100,hint=''))
step(lambda:key('E'));step(lambda:check('Repeated drink is harmless',hydration=100,hint=''))
step(lambda:spawn('hold'));step(lambda:lib.send_verification_ui_key_event(pc,'E',True),2);step(lambda:lib.send_verification_ui_key_event(pc,'E',False));step(hold_check)
step(lambda:key('I'));step(lambda:select('pickaxe',True));step(lambda:key('R'));step(lambda:check('Inventory unequip returns owned pickaxe without losing weight',tool=None,opened=True))
step(close);step(lambda:key('Two'));step(lambda:check('Shortcut re-equips returned pickaxe; all collected resources retained',tool='pickaxe',hydration=100))

index=0; next_time=unreal.GameplayStatics.get_time_seconds(server)+1;ready_deadline=next_time+10;handle=None
def finish():
    unreal.unregister_slate_post_tick_callback(handle)
    live=list(lib.get_play_worlds())
    def cleanup(action):
        try:action()
        except Exception:report['errors'].append('Cleanup: '+traceback.format_exc())
    for c,w in zip(controllers,worlds):
        if valid(w) and w in live and valid(c):cleanup(lambda:lib.flush_verification_input(c))
    if valid(world) and world in live and valid(pc):
        cleanup(lambda:pc.set_inventory_open(False))
        for i in range(8):cleanup(lambda:lib.send_verification_hotbar_request(pc,i,None,False))
    if valid(server) and server in live and valid(owner):
        cleanup(lambda:owner.get_equipment_component().unequip_item(unreal.EWEquipmentSlot.MAIN_HAND))
        for item in items.values():cleanup(lambda:owner.get_inventory_component().remove_item(item,100000))
        for stats,value in saved_stats:
            if valid(stats):cleanup(lambda:stats.set_hydration(value))
    for a in fixtures:
        if valid(a):cleanup(lambda:a.destroy_actor())
    for w,old in old_network:
        if valid(w) and w in live:cleanup(lambda:lib.set_verification_network_settings(w,old.x,old.y))
    settings.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
    report['success']=not report['errors'] and index==len(steps)
    report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(path,'w') as f:json.dump(report,f,indent=2)
def tick(delta):
    global index,next_time
    try:
        live=list(lib.get_play_worlds())
        assert all(valid(w) and w in live for w in worlds),'Play ended during integrated verification'
        now=unreal.GameplayStatics.get_time_seconds(server)
        if now<next_time:return
        if index==0 and not str(hud.get_displayed_summary()):
            assert now<ready_deadline,'Survival HUD did not initialize; use a visible interactive Play viewport'
            return
        if index==len(steps):finish();return
        action,delay=steps[index];action();index+=1;next_time=now+delay
    except Exception:report['errors'].append(traceback.format_exc());finish()
handle=unreal.register_slate_post_tick_callback(tick)
