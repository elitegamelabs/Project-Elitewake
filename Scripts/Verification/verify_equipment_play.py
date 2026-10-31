def run_equipment_verification():
    """Opt-in fresh PIE fixture; exercise owned RPCs and focused inventory Slate input.

    Supports standalone or listen-server/client. Restores panel, throttle, network settings
    and removes its callback. Fixture grants affect PIE only, never saved/default inventory.
    """
    import unreal,json,os,traceback
    lib=unreal.EWEditorVerificationLibrary
    worlds=lib.get_play_worlds()
    assert len(worlds) in (1,2)
    controllers=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
    controller=next((c for c in controllers if not c.has_authority()),controllers[0])
    world=worlds[controllers.index(controller)]
    pawn=controller.get_controlled_pawn()
    def pid(p):return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
    server=next(w for w,c in zip(worlds,controllers) if c.has_authority())
    server_pawns=unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter)
    authority=next(p for p in server_pawns if pid(p)==pid(pawn))
    inventory=authority.get_inventory_component()
    equipment=authority.get_equipment_component()
    hat=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHat')
    alternate=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatAlternate')
    wood=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
    assert hat and alternate and wood
    head=unreal.EWEquipmentSlot.HEAD
    for e in list(equipment.get_equipment_entries()): equipment.unequip_item(e.get_editor_property('slot'))
    for e in list(inventory.get_inventory_entries()): inventory.remove_item(e.get_editor_property('item_definition'),e.get_editor_property('quantity'))      # the starter kit arrives with every survivor
    assert not inventory.get_inventory_entries() and not equipment.get_equipment_entries(),'could not empty the starter kit'
    settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
    old_throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground')
    settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
    old_network=[]
    if len(worlds)==2:
        for w in worlds:
            old_network.append((w,lib.get_verification_network_settings(w)))
            lib.set_verification_network_settings(w,100,1)
    other=next((p for p in server_pawns if p!=authority),None)
    if other:assert other.get_inventory_component().add_item(alternate,1)==1
    controller.set_inventory_open(False)
    unreal.WidgetLibrary.set_focus_to_game_viewport()
    report={'success':False,'network':len(worlds)==2,'checkpoints':[],'errors':[]}
    path=os.path.join(unreal.Paths.project_saved_dir(),'M5FEquipmentNetworkResult.json' if len(worlds)==2 else 'M5FEquipmentPlayResult.json')
    def ui():return next((w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world,unreal.EWInventoryWidget,False) if w.get_owning_player()==controller and w.is_in_viewport()),None)
    def key(name):assert lib.send_verification_ui_key(controller,name)
    def request(item,slot,unequip=False):assert lib.send_verification_equipment_request(controller,item,slot,unequip)
    def check(label,expected,hat_count,alt_count,wood_count=1,weight=5.1):
        row={'label':label,'states':[]}
        report['checkpoints'].append(row)
        widget=ui()
        row['selected']=widget.get_selected_index() if widget else None
        row['details']=widget.is_showing_details() if widget else None
        for p in (authority,pawn):
            inv=p.get_inventory_component();eq=p.get_equipment_component()
            state={'hat':inv.get_item_count(hat),'alternate':inv.get_item_count(alternate),'wood':inv.get_item_count(wood),
                   'equipped':eq.get_equipped_item(head).get_name() if eq.get_equipped_item(head) else None,
                   'carried_weight':p.get_survival_component().get_carried_weight(),
                   'inventory_weight':inv.get_total_weight(),'equipment_weight':eq.get_total_weight()}
            row['states'].append(state)
            assert eq.get_equipped_item(head)==expected,label+': equipment differs'
            assert (state['hat'],state['alternate'],state['wood'])==(hat_count,alt_count,wood_count),label+': item count differs'
            assert abs(state['carried_weight']-weight)<.02,label+': survival weight differs'
            assert abs(state['inventory_weight']+state['equipment_weight']-weight)<.02,label+': composite weight differs'
        if other:
            assert other.get_inventory_component().get_item_count(alternate)==1 and not other.get_equipment_component().get_equipment_entries(),label+': foreign pawn changed'
    def select(index):
        widget=ui();assert widget and widget.has_user_focus(controller)
        while widget.get_selected_index()<index:key('Right')
        while widget.get_selected_index()>index:key('Left')
        key('Enter')
    def client_reject():
        if not controller.has_authority():
            assert pawn.get_equipment_component().equip_item(hat,head)==unreal.EWEquipmentResult.NOT_AUTHORITY
        request(alternate,head) # Only the other pawn owns it initially.
    steps=[(lambda:inventory.add_item(hat,1),.1),(lambda:inventory.add_item(wood,1),1.5),
           (client_reject,1.5),(lambda:check('unowned/foreign item rejected',None,1,0,weight=2.1),.1),
           (lambda:request(hat,unreal.EWEquipmentSlot.FEET),1.5),
           (lambda:check('wrong slot rejected',None,1,0,weight=2.1),.1),
           (lambda:key('I'),.4),(lambda:select(0),.2),(lambda:key('R'),1.5),
           (lambda:check('R equips one owned unit',hat,0,0,weight=2.1),.1),
           (lambda:request(hat,head),1.5),
           (lambda:check('replayed equip does not duplicate',hat,0,0,weight=2.1),.1),
           (lambda:select(1),.2),(lambda:key('Gamepad_FaceButton_Left'),1.5),
           (lambda:check('X unequips into inventory',None,1,0,weight=2.1),.1),
           (lambda:inventory.add_item(alternate,1),1.5),(lambda:select(1),.2),(lambda:key('R'),1.5),
           (lambda:check('equip head fixture',hat,0,1),.1),
           (lambda:select(1),.2),(lambda:key('Gamepad_FaceButton_Left'),1.5),
           (lambda:check('occupied head swaps atomically',alternate,1,0),.1),
           (lambda:inventory.add_item(wood,5750),1.5),
           (lambda:select(24),.2),(lambda:key('R'),1.5),
           (lambda:check('full inventory leaves gear equipped',alternate,1,0,5750,580.0),.1),
           (lambda:select(1),.2),(lambda:key('R'),1.5),
           (lambda:check('full inventory swap uses freed source slot',hat,0,1,5750,580.0),.1),
           (lambda:inventory.remove_item(wood,250),1.5),(lambda:select(23),.2),(lambda:key('R'),1.5),
           (lambda:check('space allows unequip',None,1,1,5500,555.0),.1),
           (lambda:request(None,head,True),1.5),
           (lambda:check('empty slot replay leaves inventory intact',None,1,1,5500,555.0),.1),
           (lambda:request(wood,head),1.5),
           (lambda:check('resource cannot be equipped',None,1,1,5500,555.0),.1),
           (lambda:key('I'),.4)]
    index=0;next_time=unreal.GameplayStatics.get_time_seconds(world)+1;handle=None
    def finish():
        if world in lib.get_play_worlds() and unreal.SystemLibrary.is_valid(controller):controller.set_inventory_open(False)
        for w,old in old_network:
            if w in lib.get_play_worlds():lib.set_verification_network_settings(w,old.x,old.y)
        settings.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
        report['success']=not report['errors'] and index==len(steps)
        with open(path,'w') as f:json.dump(report,f,indent=2)
        unreal.unregister_slate_post_tick_callback(handle)
    def tick(delta):
        nonlocal index,next_time
        try:
            if world not in lib.get_play_worlds():raise RuntimeError('Play ended before verification finished')
            now=unreal.GameplayStatics.get_time_seconds(world)
            if now<next_time:return
            if index==len(steps):finish();return
            action,wait=steps[index];action();index+=1;next_time=now+wait
        except Exception:
            report['errors'].append(traceback.format_exc());finish()
    handle=unreal.register_slate_post_tick_callback(tick)

run_equipment_verification()
