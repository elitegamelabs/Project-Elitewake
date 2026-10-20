def run_hotbar_verification():
    """Fresh standalone or host/client PIE in the saved M5 pickup map.

    Normal Slate key events and owned RPC intents; no saved/default item grants.
    Restores packet settings, throttle, held keys and UI; unregisters callback.
    """
    import unreal,json,os,traceback
    lib=unreal.EWEditorVerificationLibrary
    worlds=lib.get_play_worlds();assert len(worlds) in (1,2)
    controllers=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
    controller=next((c for c in controllers if not c.has_authority()),controllers[0])
    world=worlds[controllers.index(controller)];pawn=controller.get_controlled_pawn()
    def pid(p):return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
    server=next(w for w,c in zip(worlds,controllers) if c.has_authority())
    authority=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if pid(p)==pid(pawn))
    other=next((p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if p!=authority),None)
    inv=authority.get_inventory_component();hotbar=authority.get_hotbar_component()
    hat=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHat')
    alternate=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatAlternate')
    wood=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
    stone=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestStone')
    torch=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestInnTorch')
    assert torch, 'Y quick-assign needs the existing hand-tool fixture'
    assert not inv.get_inventory_entries() and not authority.get_equipment_component().get_equipment_entries(),'Use fresh PIE'
    assert all(hotbar.get_bound_item(i) is None for i in range(8))
    if other:assert other.get_inventory_component().add_item(alternate,1)==1
    settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
    old_throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground')
    settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
    old_network=[]
    if len(worlds)==2:
        for w in worlds:
            old_network.append((w,lib.get_verification_network_settings(w)))
            assert lib.set_verification_network_settings(w,100,1)
    controller.set_inventory_open(False)
    report={'success':False,'network':len(worlds)==2,'checkpoints':[],'errors':[]}
    path=os.path.join(unreal.Paths.project_saved_dir(),'M5GHotbarNetworkResult.json' if len(worlds)==2 else 'M5GHotbarPlayResult.json')
    def key(name):assert lib.send_verification_ui_key(controller,name)
    def event(name,pressed):assert lib.send_verification_ui_key_event(controller,name,pressed)
    def request(slot,item=None,activate=False):assert lib.send_verification_hotbar_request(controller,slot,item,activate)
    def ui():return next((u for u in unreal.WidgetLibrary.get_all_widgets_of_class(world,unreal.EWInventoryWidget,False) if u.get_owning_player()==controller and u.is_in_viewport()),None)
    def chord(name):event('Gamepad_LeftShoulder',True);key(name);event('Gamepad_LeftShoulder',False)
    names=['Gamepad_DPad_Left','Gamepad_DPad_Up','Gamepad_DPad_Right','Gamepad_DPad_Down',
           'Gamepad_FaceButton_Bottom','Gamepad_FaceButton_Left','Gamepad_FaceButton_Right','Gamepad_FaceButton_Top']
    def check(label,bindings,selected,equipped,hat_count=1,alt_count=0,wood_count=251,stone_count=0,torch_count=0,main_hand=None,opened=False):
        row={'label':label,'states':[]};report['checkpoints'].append(row)
        hud=next((u for u in unreal.WidgetLibrary.get_all_widgets_of_class(world,unreal.EWHotbarWidget,False) if u.get_owning_player()==controller and u.is_in_viewport()),None)
        assert hud,label+': local HUD missing'
        assert bool(ui())==opened,label+': inventory lifecycle differs'
        for p in (authority,pawn):
            h=p.get_hotbar_component();inventory=p.get_inventory_component();equipment=p.get_equipment_component()
            state={'bindings':[h.get_bound_item(i).get_name() if h.get_bound_item(i) else None for i in range(8)],
                   'selected':h.get_selected_slot(),'hat':inventory.get_item_count(hat),'alternate':inventory.get_item_count(alternate),
                   'wood':inventory.get_item_count(wood),'stone':inventory.get_item_count(stone),'torch':inventory.get_item_count(torch),
                   'main_hand':equipment.get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND).get_name() if equipment.get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND) else None,
                   'equipment':equipment.get_equipped_item(unreal.EWEquipmentSlot.HEAD).get_name() if equipment.get_equipped_item(unreal.EWEquipmentSlot.HEAD) else None,
                   'weight':p.get_survival_component().get_carried_weight()}
            row['states'].append(state)
            assert all(h.get_bound_item(i)==bindings.get(i) for i in range(8)),label+': binding replication differs'
            assert state['selected']==selected,label+': wrong selected slot'
            assert equipment.get_equipped_item(unreal.EWEquipmentSlot.HEAD)==equipped,label+': wrong equipped item'
            assert (state['hat'],state['alternate'],state['wood'])==(hat_count,alt_count,wood_count),label+': item quantities differ'
            assert state['stone']==stone_count,label+': stone quantity differs'
            assert state['torch']==torch_count,label+': torch quantity differs'
            assert state['main_hand']==(main_hand.get_name() if main_hand else None),label+': main-hand item differs'
            expected_weight=hat_count*2+alt_count*3+wood_count*.1+stone_count*stone.get_editor_property('unit_weight')+torch_count*torch.get_editor_property('unit_weight')+(equipped.get_editor_property('unit_weight') if equipped else 0)+(main_hand.get_editor_property('unit_weight') if main_hand else 0)
            assert abs(state['weight']-expected_weight)<.02,label+': carried weight differs'
        if other:
            assert other.get_inventory_component().get_item_count(alternate)==1 and not other.get_equipment_component().get_equipment_entries(),label+': foreign player changed'
        unreal.log('M5G checkpoint: '+label)
    def initial():
        check('eight empty slots and local HUD',{},-1,None,hat_count=0,wood_count=0)
        if not controller.has_authority():assert pawn.get_hotbar_component().bind_item(0,hat)==unreal.EWHotbarResult.NOT_AUTHORITY
    def world_chord_check(index,label='LB world combination '):
        expected=hat if index==0 else alternate
        check(label+str(index+1),{0:hat,1:alternate,7:wood},index,expected,
              hat_count=0 if expected==hat else 1,alt_count=1 if expected==hat else 0,wood_count=1)
        assert not pawn.is_prone and not pawn.get_editor_property('bIsCrouched') and not pawn.get_movement_component().is_falling(),'Chord leaked into stance/jump'
    def position_for_pickup():
        if other:other.teleport(unreal.Vector(-500,500,96),unreal.Rotator())
        authority.teleport(unreal.Vector(0,0,96),unreal.Rotator())
        authority.get_controller().set_control_rotation(unreal.Rotator())
        controller.set_control_rotation(unreal.Rotator())
    steps=[(initial,.1),(lambda:inv.add_item(hat,1),.1),(lambda:inv.add_item(wood,251),1.5),
           (lambda:request(0,alternate),1.5),(lambda:check('unowned foreign binding rejected',{},-1,None),.1),
           (lambda:request(-1,hat),1.5),(lambda:request(8,hat),1.5),
           (lambda:check('invalid indices do not change selection',{},-1,None),.1),
           (lambda:key('I'),.4),(lambda:key('Enter'),.2),(lambda:key('One'),1.5),
           (lambda:check('keyboard assigns owned item without transfer',{0:hat},0,None,opened=True),.1),
           (lambda:key('Eight'),1.5),(lambda:check('assignment moves unique shortcut to slot eight',{7:hat},7,None,opened=True),.1),
           (lambda:key('Eight'),1.5),(lambda:check('same assignment removes shortcut',{},7,None,opened=True),.1)]
    for index,name in enumerate(names):
        steps.extend([(lambda n=name:chord(n),1.5),
                      (lambda i=index:check('LB inventory combination '+str(i+1),{i:hat},i,None,opened=True),.1)])
    steps.extend([(lambda:key('Eight'),1.5),(lambda:key('One'),1.5),(lambda:key('I'),.4),
                  (lambda:key('One'),1.5),(lambda:check('keyboard activates equipment shortcut',{0:hat},0,hat,hat_count=0),.1),
                  (lambda:key('One'),1.5),(lambda:check('repeat activation keeps one worn unit',{0:hat},0,hat,hat_count=0),.1),
                  (lambda:key('Eight'),1.5),(lambda:check('empty slot activation preserves equipment',{0:hat},7,hat,hat_count=0),.1),
                  (lambda:inv.add_item(alternate,1),1.5),(lambda:request(1,alternate),1.5),(lambda:key('Two'),1.5),
                  (lambda:check('hotbar swaps through M5F rules',{0:hat,1:alternate},1,alternate),.1),
                  (lambda:request(7,wood),1.5),(lambda:key('Eight'),1.5),
                  (lambda:check('resource has no invented consumption',{0:hat,1:alternate,7:wood},7,alternate),.1),
                  (lambda:inv.remove_item(wood,251),1.5),(lambda:key('Eight'),1.5),
                  (lambda:check('unavailable reference retained safely',{0:hat,1:alternate,7:wood},7,alternate,wood_count=0),.1),
                  (lambda:inv.add_item(wood,1),1.5),(lambda:key('Eight'),1.5),
                  (lambda:check('replenishment restores shortcut quantity',{0:hat,1:alternate,7:wood},7,alternate,wood_count=1),.1)])
    for index,name in enumerate(['One','Two','Three','Four','Five','Six','Seven','Eight']):
        steps.extend([(lambda n=name:key(n),1.5),(lambda i=index:world_chord_check(i,'Keyboard world key '),.1)])
    steps.append((position_for_pickup,2))
    for index,name in enumerate(names):
        steps.extend([(lambda n=name:chord(n),1.5),(lambda i=index:world_chord_check(i),.1)])
    steps.extend([(lambda:event('Gamepad_LeftShoulder',True),.1),(lambda:event('Gamepad_FaceButton_Bottom',True),.1),
                  (lambda:event('Gamepad_LeftShoulder',False),.1),(lambda:event('Gamepad_FaceButton_Bottom',False),1.5),
                  (lambda:world_chord_check(0),.1),
                  (lambda:inv.add_item(torch,1),1.5),
                  (lambda:key('Gamepad_FaceButton_Top'),.4),
                  (lambda:select_inventory_item(torch),.2),
                  (lambda:key('Gamepad_FaceButton_Top'),1.5),
                  (lambda:check('Xbox Y quick-assigns selected item to nearest empty slot',
                                {0:hat,1:alternate,2:torch,7:wood},2,alternate,hat_count=0,alt_count=1,wood_count=1,torch_count=1,opened=True),.1),
                  (lambda:key('Gamepad_FaceButton_Right'),.4),
                  (lambda:key('Gamepad_DPad_Right'),1.5),
                  (lambda:check('Y-assigned item activates from slot 3',{0:hat,1:alternate,2:torch,7:wood},2,alternate,hat_count=0,alt_count=1,wood_count=1,torch_count=0,main_hand=torch),.1),
                  (lambda:lib.send_verification_equipment_request(controller,None,unreal.EWEquipmentSlot.MAIN_HAND,True),1.5),
                  (lambda:request(2,None),1.5),(lambda:inv.remove_item(torch,1),1.5),
                  (lambda:request(1,alternate),1.5),
                  (lambda:key('Gamepad_DPad_Right'),.4),
                  (lambda:key('Gamepad_FaceButton_Right'),.4),
                  (lambda:check('Y/B normal inventory roles return',{0:hat,1:alternate,7:wood},0,hat_count=0,alt_count=1,wood_count=1),.1),
                  # Closing UI recaptures the mouse; re-aim after any resulting cursor delta.
                  (position_for_pickup,2),
                  (lambda:key('Gamepad_FaceButton_Left'),1.5),
                  (lambda:check('X ordinary pickup restored after LB release',{0:hat,1:alternate,7:wood},0,hat,hat_count=0,alt_count=1,wood_count=11),.1),
                  (lambda:key('Gamepad_FaceButton_Bottom'),.15),
                  (lambda:report['checkpoints'].append({'label':'A ordinary jump restored','falling':pawn.get_movement_component().is_falling()}),.1),
                  (lambda:assert_jump(),1.5),
                  (lambda:event('Gamepad_LeftShoulder',True),.1),
                  (lambda:assert_flush(),.1),(lambda:key('Gamepad_FaceButton_Top'),.4),
                  (lambda:check('engine focus flush releases LB',{0:hat,1:alternate,7:wood},0,hat,hat_count=0,alt_count=1,wood_count=11,opened=True),.1),
                  (lambda:key('Gamepad_FaceButton_Right'),.4)])
    def assert_jump():assert report['checkpoints'][-1]['falling'],'Normal A did not jump'
    def assert_flush():assert lib.flush_verification_input(controller),'Engine flush did not clear LB'
    def select_inventory_item(item):
        panel=ui();assert panel,'Y quick-assign needs the inventory open'
        for _ in range(32):
            if panel.get_selected_item_definition()==item:return
            key('Down')
        assert panel.get_selected_item_definition()==item,'Could not select quick-assign item'
    index=0;next_time=unreal.GameplayStatics.get_time_seconds(world)+1;handle=None
    def finish():
        if world in lib.get_play_worlds() and unreal.SystemLibrary.is_valid(controller):
            event('Gamepad_LeftShoulder',False);event('Gamepad_FaceButton_Bottom',False)
            controller.set_inventory_open(False)
        for w,old in old_network:
            if w in lib.get_play_worlds():lib.set_verification_network_settings(w,old.x,old.y)
        settings.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
        report['success']=not report['errors'] and index==len(steps)
        with open(path,'w') as f:json.dump(report,f,indent=2)
        unreal.unregister_slate_post_tick_callback(handle)
    def tick(delta):
        nonlocal index,next_time
        try:
            if world not in lib.get_play_worlds():raise RuntimeError('Play ended early')
            now=unreal.GameplayStatics.get_time_seconds(world)
            if now<next_time:return
            if index==len(steps):finish();return
            action,wait=steps[index];action();index+=1;next_time=now+wait
        except Exception:
            report['errors'].append(traceback.format_exc());finish()
    handle=unreal.register_slate_post_tick_callback(tick)

run_hotbar_verification()
