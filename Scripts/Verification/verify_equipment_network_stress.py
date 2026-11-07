def run_equipment_network_stress():
    """Fresh two-player PIE: repeated owned intents and both owners/observer replicas.

    PIE-only grants; restores packet/throttle settings and unregisters its callback.
    This is a bounded local regression probe, not a production load test.
    """
    import unreal,json,os,traceback
    lib=unreal.EWEditorVerificationLibrary
    worlds=lib.get_play_worlds()
    assert len(worlds)==2
    controllers=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
    server=next(w for w,c in zip(worlds,controllers) if c.has_authority())
    hat=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHat')
    alternate=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatAlternate')
    wood=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
    head=unreal.EWEquipmentSlot.HEAD
    def pid(p):return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
    ids={pid(c.get_controlled_pawn()) for c in controllers}
    authority=[p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if pid(p) in ids]
    assert len(authority)==2
    for p in authority:
        assert not p.get_inventory_component().get_inventory_entries() and not p.get_equipment_component().get_equipment_entries(),'Use fresh PIE'
    settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
    old_throttle=settings.get_editor_property('bThrottleCPUWhenNotForeground')
    settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
    old_network=[(w,lib.get_verification_network_settings(w)) for w in worlds]
    for w in worlds:assert lib.set_verification_network_settings(w,100,1)
    for p in authority:
        inv=p.get_inventory_component()
        for item in (hat,alternate,wood):assert inv.add_item(item,1)==1
    report={'success':False,'lag_ms':100,'loss_percent':1,'checkpoints':[],'errors':[],'equip_requests':60,'unequip_requests':40}
    path=os.path.join(unreal.Paths.project_saved_dir(),'M5FEquipmentStressResult.json')
    def burst(unequip=False):
        for i in range(20 if unequip else 30):
            for c in controllers:
                assert lib.send_verification_equipment_request(c,None if unequip else (hat if i%2==0 else alternate),head,unequip)
    def check(label,equipped):
        row={'label':label,'replicas':[]};report['checkpoints'].append(row)
        for w in worlds:
            pawns=[p for p in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.EWCharacter) if pid(p) in ids]
            assert len(pawns)==2
            for p in pawns:
                inv=p.get_inventory_component();eq=p.get_equipment_component()
                state={'player_id':pid(p),'authority':p.has_authority(),'hat':inv.get_item_count(hat),
                       'alternate':inv.get_item_count(alternate),'wood':inv.get_item_count(wood),
                       'equipment':eq.get_equipped_item(head).get_name() if eq.get_equipped_item(head) else None,
                       'weight':p.get_survival_component().get_carried_weight()}
                row['replicas'].append(state)
                assert eq.get_equipped_item(head)==(alternate if equipped else None),label+': equipped state differs'
                assert (state['hat'],state['alternate'],state['wood'])==(1,0 if equipped else 1,1),label+': quantity differs'
                assert abs(state['weight']-5.1)<.01,label+': carried weight differs'
                assert abs(inv.get_total_weight()+eq.get_total_weight()-5.1)<.01,label+': composite weight differs'
    steps=[(lambda:burst(),5),(lambda:check('60 alternating equip intents agree on all four replicas',True),.1),
           (lambda:burst(True),5),(lambda:check('40 repeated unequip intents conserve all units',False),.1)]
    index=0;next_time=unreal.GameplayStatics.get_time_seconds(server)+2;handle=None
    def finish():
        for w,old in old_network:
            if w in lib.get_play_worlds():lib.set_verification_network_settings(w,old.x,old.y)
        settings.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
        report['success']=not report['errors'] and index==len(steps)
        with open(path,'w') as f:json.dump(report,f,indent=2)
        unreal.unregister_slate_post_tick_callback(handle)
    def tick(delta):
        nonlocal index,next_time
        try:
            if any(w not in lib.get_play_worlds() for w in worlds):raise RuntimeError('Play ended early')
            now=unreal.GameplayStatics.get_time_seconds(server)
            if now<next_time:return
            if index==len(steps):finish();return
            action,wait=steps[index];action();index+=1;next_time=now+wait
        except Exception:
            report['errors'].append(traceback.format_exc());finish()
    handle=unreal.register_slate_post_tick_callback(tick)

run_equipment_network_stress()
