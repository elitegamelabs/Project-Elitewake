def run_survival_hud_verification():
    """Fresh standalone/listen-client PIE; read actual HUD labels after authority changes.

    Opt-in saved fixtures only. Restore packet/throttle/input/panel state and remove callback.
    Does not tune survival rates or add default grants.
    """
    import unreal,json,os,traceback
    lib=unreal.EWEditorVerificationLibrary
    worlds=lib.get_play_worlds();assert len(worlds) in (1,2)
    controllers=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
    c=next((x for x in controllers if not x.has_authority()),controllers[0])
    w=worlds[controllers.index(c)];pawn=c.get_controlled_pawn()
    def pid(p):return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
    server=next(x for x,y in zip(worlds,controllers) if y.has_authority())
    authority=next(x for x in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if pid(x)==pid(pawn))
    authority_controller=authority.get_controller()
    other=next((x for x in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if x!=authority),None)
    s=authority.get_survival_component();inv=authority.get_inventory_component()
    hat=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHat')
    wood=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
    assert not inv.get_inventory_entries() and not authority.get_equipment_component().get_equipment_entries(),'Use fresh PIE'
    settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
    old_throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground')
    settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
    old_network=[]
    if len(worlds)==2:
        for world in worlds:
            old_network.append((world,lib.get_verification_network_settings(world)))
            assert lib.set_verification_network_settings(world,100,1)
    c.set_inventory_open(False)
    report={'success':False,'network':len(worlds)==2,'checkpoints':[],'errors':[]}
    path=os.path.join(unreal.Paths.project_saved_dir(),'M4HUDNetworkResult.json' if len(worlds)==2 else 'M4HUDPlayResult.json')
    def hud():return next(x for x in unreal.WidgetLibrary.get_all_widgets_of_class(w,unreal.EWSurvivalWidget,False) if x.get_owning_player()==c and x.is_in_viewport())
    def check(label,expected,warnings=None):
        u=hud();text=str(u.get_displayed_summary());notice=str(u.get_displayed_warnings())
        report['checkpoints'].append({'label':label,'display':text,'warnings':notice})
        for value in expected:assert value in text,label+': missing '+value
        if warnings is not None:assert notice==warnings,label+': warning differs '+notice
        if other:
            o=other.get_survival_component()
            assert o.get_health()==100 and o.get_hunger()==100 and o.get_hydration()==100 and o.get_carried_weight()==0,label+': foreign survivor changed'
        unreal.log('M4 HUD checkpoint: '+label)
    def values():
        s.apply_damage(25);s.set_hunger(25);s.set_hydration(40)
        assert inv.add_item(wood,251)==251 and inv.add_item(hat,1)==1
    def inventory_check():
        check('HUD stays current with inventory open',['Health 75 / 100','Food 25%','Hydration 40%','Weight 27.1 / 50.0 kg'],'')
        assert c.is_move_input_ignored() and c.is_look_input_ignored()
    def absent():
        assert c.get_controlled_pawn() is None
        check('unpossessed HUD clears stale values',[], '')
        assert not str(hud().get_displayed_summary())
    stamina_observation={'drained':False,'warning':False,'warning_started':None,'warning_ended':None}
    def stamina_check():
        assert stamina_observation['drained'],'HUD did not follow real sprint drain'
        assert stamina_observation['warning'],'HUD missed stamina exhaustion'
        check('real sprint exhaustion warning observed',['Stamina'],None)
    def warning_duration():
        start=stamina_observation['warning_started'];end=stamina_observation['warning_ended']
        assert start is not None and end is not None and 1.35<=end-start<=1.8,'Stamina warning did not persist for 1.5 seconds'
        check('stamina warning lasts through automatic recovery',['Stamina'],'')
        report['stamina_warning_seconds']=end-start
    steps=[(lambda:check('fresh full stats and empty weight',['Health 100 / 100','Stamina 100 / 100','Food 100%','Hydration 100%','Weight 0.0 / 50.0 kg'],''),.1),
           (values,1.5),(lambda:check('replicated damage needs and inventory weight',['Health 75 / 100','Food 25%','Hydration 40%','Weight 27.1 / 50.0 kg'],''),.1),
           (lambda:lib.send_verification_equipment_request(c,hat,unreal.EWEquipmentSlot.HEAD,False),1.5),
           (lambda:check('worn gear remains in HUD carried weight',['Weight 27.1 / 50.0 kg'],''),.1),
           (lambda:lib.send_verification_ui_key(c,'I'),.4),(inventory_check,.1),
           (lambda:lib.send_verification_ui_key(c,'I'),.4),
           (lambda:s.set_hunger(0),.5),(lambda:check('empty food warning',['Food 0%'],'You are hungry!'),1.6),
           (lambda:check('food warning expires while food stays empty',['Food 0%'],''),.1),
           (lambda:s.set_hydration(0),.5),(lambda:check('empty hydration warning',['Hydration 0%'],'You are thirsty!'),1.6),
           (lambda:check('hydration warning expires while needs stay empty',['Food 0%','Hydration 0%'],''),.1),
           (lambda:s.set_hunger(5),.5),(lambda:check('small food refill updates immediately',['Food 5%','Hydration 0%'],''),.1),
           (lambda:s.set_hunger(0),.5),(lambda:check('new empty transition warns again',['Food 0%'],'You are hungry!'),1.6),
           (lambda:s.set_hunger(100),.1),(lambda:s.set_hydration(100),.1),(lambda:s.restore_health(50),1.5),
           (lambda:check('health and needs restore',['Health 100 / 100','Food 100%','Hydration 100%'],''),.1),
           (lambda:(s.set_hunger(0),s.set_hydration(0)),.5),
           (lambda:check('simultaneous empty needs keep both warnings',['Food 0%','Hydration 0%'],'You are hungry!\nYou are thirsty!'),1.6),
           (lambda:(s.set_hunger(100),s.set_hydration(100)),1.5),
           (lambda:inv.remove_item(wood,251),1.5),(lambda:check('equipment only weight',['Weight 2.0 / 50.0 kg'],''),.1),
           (lambda:lib.send_verification_equipment_request(c,None,unreal.EWEquipmentSlot.HEAD,True),1.5),
           (lambda:check('unequip conserves carried weight',['Weight 2.0 / 50.0 kg'],''),.1),
           (lambda:inv.remove_item(hat,1),1.5),(lambda:check('removal clears carried weight',['Weight 0.0 / 50.0 kg'],''),.1),
           (lambda:inv.add_item(wood,1000),1.5),(lambda:check('HUD shows real weight above prototype capacity',['Weight 100.0 / 50.0 kg'],''),.1),
           (lambda:inv.remove_item(wood,1000),1.5),
           (lambda:authority_controller.un_possess(),1.5),(absent,.1),
           (lambda:authority_controller.possess(authority),1.5),
           (lambda:check('repossession restores current stats',['Health 100 / 100','Food 100%','Hydration 100%','Weight 0.0 / 50.0 kg'],''),.1),
           (lambda:lib.send_verification_ui_key_event(c,'LeftShift',True),7.5),(stamina_check,.1),
           (lambda:lib.send_verification_ui_key_event(c,'LeftShift',False),2),(warning_duration,.1)]
    index=0;next_time=unreal.GameplayStatics.get_time_seconds(w)+1;handle=None
    def finish():
        if server in lib.get_play_worlds() and authority_controller.get_controlled_pawn() is None:authority_controller.possess(authority)
        if w in lib.get_play_worlds():c.set_inventory_open(False)
        if w in lib.get_play_worlds():lib.send_verification_ui_key_event(c,'LeftShift',False)
        for world,old in old_network:
            if world in lib.get_play_worlds():lib.set_verification_network_settings(world,old.x,old.y)
        settings.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
        report['success']=not report['errors'] and index==len(steps)
        with open(path,'w') as f:json.dump(report,f,indent=2)
        unreal.unregister_slate_post_tick_callback(handle)
    def tick(delta):
        nonlocal index,next_time
        try:
            if w not in lib.get_play_worlds():raise RuntimeError('Play ended before HUD verification finished')
            now=unreal.GameplayStatics.get_time_seconds(w)
            if c.get_controlled_pawn():
                if c.get_controlled_pawn().get_survival_component().get_stamina()<90:stamina_observation['drained']=True
                active='You are out of stamina!' in str(hud().get_displayed_warnings())
                if active:
                    stamina_observation['warning']=True
                    if stamina_observation['warning_started'] is None:stamina_observation['warning_started']=now
                elif stamina_observation['warning_started'] is not None and stamina_observation['warning_ended'] is None:
                    stamina_observation['warning_ended']=now
            if now<next_time:return
            if index==len(steps):finish();return
            action,wait=steps[index];action();index+=1;next_time=now+wait
        except Exception:report['errors'].append(traceback.format_exc());finish()
    handle=unreal.register_slate_post_tick_callback(tick)

run_survival_hud_verification()
