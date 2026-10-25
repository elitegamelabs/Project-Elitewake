def run_inventory_selection_verification():
    """Fresh single-player or host/client PIE. Real Slate keys/analog route through focused UI.

    Uses only the saved Wood fixture and authority inventory mutations. No saved world changes.
    Restores focus, panel, network/throttle settings and removes callback on completion/failure.
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
    owner_id=pid(pawn)
    server=next(w for w,c in zip(worlds,controllers) if c.has_authority())
    server_pawn=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if pid(p)==owner_id)
    inventory=server_pawn.get_inventory_component()
    item=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
    assert item
    for e in list(server_pawn.get_equipment_component().get_equipment_entries()): server_pawn.get_equipment_component().unequip_item(e.get_editor_property('slot'))
    for e in list(inventory.get_inventory_entries()): inventory.remove_item(e.get_editor_property('item_definition'),e.get_editor_property('quantity'))      # the starter kit arrives with every survivor
    settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
    old_throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground')
    settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
    old_network=[]
    if len(worlds)==2:
        for w in worlds:
            old_network.append((w,lib.get_verification_network_settings(w)))
            lib.set_verification_network_settings(w,100,1)
    controller.set_inventory_open(False)
    inventory.remove_item(item,100000)
    unreal.WidgetLibrary.set_focus_to_game_viewport()
    report={'success':False,'network':len(worlds)==2,'checkpoints':[],'errors':[]}
    path=os.path.join(unreal.Paths.project_saved_dir(),'M5ESelectionNetworkResult.json' if len(worlds)==2 else 'M5ESelectionPlayResult.json')
    def widget():
        return next((w for w in unreal.WidgetLibrary.get_all_widgets_of_class(world,unreal.EWInventoryWidget,False)
                     if w.get_owning_player()==controller),None)
    def key(name):assert lib.send_verification_ui_key(controller,name)
    def analog(value):assert lib.send_verification_ui_analog(controller,value)
    def check(label,selected=None,details=None,opened=True,count=None):
        ui=widget()
        row={'label':label,'open':bool(ui and ui.is_in_viewport()),'selected':ui.get_selected_index() if ui else None,
             'details':ui.is_showing_details() if ui else None,'count':pawn.get_inventory_component().get_item_count(item),
             'move_ignored':controller.is_move_input_ignored(),'look_ignored':controller.is_look_input_ignored(),
             'focus':ui.has_user_focus(controller) if ui else False}
        report['checkpoints'].append(row)
        assert row['open']==opened,label+': panel lifecycle differs'
        assert row['move_ignored']==opened and row['look_ignored']==opened,label+': gameplay input lock differs'
        if opened:assert row['focus'],label+': UI does not own focus'
        if selected is not None:assert row['selected']==selected,label+': wrong selection'
        if details is not None:assert row['details']==details,label+': wrong details state'
        if count is not None:assert row['count']==count,label+': wrong replicated item count'
    steps=[(lambda:key('I'),.4),(lambda:check('empty open',-1,False,count=0),.1),
           (lambda:key('Right'),.1),(lambda:key('Down'),.1),(lambda:key('Enter'),.1),(lambda:check('empty navigation safe',-1,False),.1),
           (lambda:key('I'),.4),(lambda:check('I closes',opened=False),.1),
           (lambda:inventory.add_item(item,751),1.5),(lambda:key('Gamepad_FaceButton_Top'),.4),
           (lambda:check('Y opens first valid row',0,False,count=751),.1),
           (lambda:key('Right'),.2),(lambda:check('keyboard next',1,False),.1),
           (lambda:key('Enter'),.2),(lambda:check('keyboard confirms',1,True),.1),
           (lambda:key('Gamepad_DPad_Right'),.2),(lambda:check('D-pad next',2,False),.1),
           (lambda:key('Gamepad_FaceButton_Bottom'),.2),(lambda:check('A confirms',2,True),.1),
           (lambda:analog(.2),.4),(lambda:check('stick dead zone',2,True),.1),
           (lambda:analog(-1),.1),(lambda:analog(0),.1),(lambda:check('stick down on the last row stays (the crafting list below is empty)',2,True),.1),
           (lambda:analog(1),.8),(lambda:analog(0),.1),(lambda:check('stick up on the top row stays',2,True),.1),
           (lambda:key('Gamepad_DPad_Left'),.2),(lambda:check('D-pad left',1,False),.1),(lambda:key('Left'),.2),(lambda:key('Left'),.2),(lambda:check('left stops at the first slot',0,False),.1),
           (lambda:key('Gamepad_FaceButton_Right'),.4),(lambda:check('B closes',opened=False),.1),
           (lambda:key('I'),.4),(lambda:key('Right'),.1),(lambda:key('Right'),.1),(lambda:key('Right'),.1),
           (lambda:inventory.remove_item(item,251),1.5),(lambda:check('removed selected row clamps',1,False,count=500),.1),
           (lambda:key('Enter'),.1),(lambda:inventory.add_item(item,1),1.5),
           (lambda:check('live refresh retains selected stack and details',1,True,count=501),.1),
           (lambda:inventory.remove_item(item,100000),1.5),(lambda:check('live empty clears selection',-1,False,count=0),.1),
           (lambda:inventory.add_item(item,251),1.5),(lambda:check('empty to populated selects first',0,False,count=251),.1),
           (lambda:key('Escape'),.4),(lambda:check('Escape closes',opened=False),.1),
           (lambda:key('Gamepad_FaceButton_Top'),.4),(lambda:check('Y reopens',0,False),.1),
           (lambda:key('Gamepad_FaceButton_Right'),.4),(lambda:check('B closes (Y quick-assigns to the hotbar inside the menu)',opened=False),.1)]
    index=0
    next_time=unreal.GameplayStatics.get_time_seconds(world)+1
    handle=None
    def finish():
        if world in lib.get_play_worlds() and unreal.SystemLibrary.is_valid(controller):
            lib.send_verification_ui_analog(controller,0)
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
            if world not in lib.get_play_worlds():raise RuntimeError('Play ended before verification finished')
            now=unreal.GameplayStatics.get_time_seconds(world)
            if now<next_time:return
            if index==len(steps):finish();return
            action,wait=steps[index];action();index+=1;next_time=now+wait
        except Exception:
            report['errors'].append(traceback.format_exc());finish()
    handle=unreal.register_slate_post_tick_callback(tick)

run_inventory_selection_verification()
