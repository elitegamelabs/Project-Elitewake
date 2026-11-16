"""Slice 4 real UI/authority/save check. Standalone or host/client; EW_PLAY_STARTER_KIT=0.
Uses and cleans only a uniquely named test save; never writes a real Survivor/server-profile slot.
"""
import json, time, traceback, uuid
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
progress, wallet = owner.get_progression_component(), owner.get_wallet_component()
remote = pawn.get_progression_component()
save_slot = 'EW_AttributeVerification_' + uuid.uuid4().hex
assert lib.configure_attribute_verification_save(owner.get_controller(), save_slot)
for _ in range(5): progress.grant_experience(progress.get_experience_for_next_level())
progress.grant_experience(25)
assert progress.unlock_skill('Gatherer')
wallet.set_copper(150001)
skills, unlocked = progress.get_skill_points(), progress.get_unlocked_skill_count()
path = Path(u.Paths.project_saved_dir(), 'InventoryAttributesNetworkResult.json' if len(worlds)>1 else 'InventoryAttributesPlayResult.json')
folder = Path(u.Paths.project_saved_dir(), 'Screenshots', 'InventorySlice4')
folder.mkdir(parents=True, exist_ok=True)
report = dict(success=False, network=len(worlds)>1, checks=[], error=None)
state = dict(step=0, at=time.monotonic()+2)
def ui():
    return next(w for w in u.WidgetLibrary.get_all_widgets_of_class(world, u.EWInventoryWidget, False) if w.is_in_viewport() and w.get_owning_player()==pc)
def key(name): assert lib.send_verification_ui_key(pc, name)
def click(name): assert lib.click_verification_widget(ui(), name), name
def check(label, condition):
    report['checks'].append(dict(check=label, passed=bool(condition)))
    assert condition, label
def shot(name):
    if len(worlds)==1: assert lib.capture_verification_play_viewport(world, str(folder/(name+'.png')))
def saved(): return u.EWSurvivorSave.load_save(save_slot)
def finish(error=None):
    pc.set_inventory_open(False)
    report['error'], report['success'] = error, error is None
    report['isolated_save_slot'] = save_slot
    if u.GameplayStatics.does_save_game_exist(save_slot, 0): assert u.GameplayStatics.delete_game_in_slot(save_slot, 0)
    path.write_text(json.dumps(report, indent=2))
    u.unregister_slate_post_tick_callback(handle)
def tick(_):
    if time.monotonic()<state['at']: return
    try:
        n, delay = state['step'], .7
        if n==0:
            lib.resize_verification_play_viewport(world,1920,1080)
            pc.set_inventory_open(True)
            state['health']=owner.get_survival_component().get_max_health()
            delay=1
        elif n==1: click('AttributePlus_HEALTH')
        elif n==2:
            check('Mouse plus is pending only',ui().get_pending_attribute_points(0)==1 and progress.get_unspent_points()==5 and owner.get_survival_component().get_max_health()==state['health'])
            click('AttributeMinus_HEALTH')
        elif n==3:
            check('Minus undoes pending only',ui().get_pending_attribute_total()==0 and progress.get_unspent_points()==5)
            ui().set_stat_focus(0)
            key('Right'); key('Right')
        elif n==4:
            check('Keyboard drafts two health points',ui().get_pending_attribute_points(0)==2 and progress.get_unspent_points()==5)
            shot('Attributes-Pending-1920x1080')
            key('Gamepad_FaceButton_Right')
        elif n==5:
            check('Controller cancels without spending',ui().get_pending_attribute_total()==0 and progress.get_unspent_points()==5)
            key('Gamepad_RightTrigger'); key('Gamepad_DPad_Right'); key('Gamepad_DPad_Down'); key('Gamepad_DPad_Right')
            state['commit_revision']=progress.get_attribute_revision()
            key('Gamepad_FaceButton_Bottom'); delay=2
        elif n==6:
            check('Controller confirms batch on both peers',all(p.get_unspent_points()==3 and p.get_stat_points(u.EWStat.VITALITY)==1 and p.get_stat_points(u.EWStat.ENDURANCE)==1 for p in (progress,remote)))
            check('Committed points affect real health',owner.get_survival_component().get_max_health()==state['health']+10)
            record=saved()
            check('Confirmed allocation persists',record and record.get_editor_property('unspent_stat_points')==3 and list(record.get_editor_property('stat_points'))==[1,1,0,0])
            assert lib.send_verification_attribute_request(pc,[1,1,0,0],state['commit_revision']); delay=1.5
        elif n==7:
            check('Allocation replay cannot spend twice',progress.get_unspent_points()==3)
            check('Minus cannot remove committed investment',not lib.is_verification_widget_enabled(ui(), 'AttributeMinus_HEALTH'))
            click('ResetAttributePoints')
        elif n==8:
            check('Reset asks before charging',ui().is_attribute_reset_confirmation_open() and wallet.get_copper()==150001)
            shot('Attributes-Reset-Confirmation-1920x1080'); key('Escape')
        elif n==9:
            check('Reset cancellation preserves money and points',wallet.get_copper()==150001 and progress.get_unspent_points()==3)
            key('Gamepad_RightTrigger'); key('Gamepad_FaceButton_Left')
            state['reset_revision']=progress.get_attribute_revision()
            key('Gamepad_FaceButton_Bottom'); delay=2
        elif n==10:
            check('Reset charges exactly five gold',wallet.get_copper()==75001 and pawn.get_wallet_component().get_copper()==75001)
            check('Reset refunds points and recalculates health',progress.get_unspent_points()==5 and list(saved().get_editor_property('stat_points'))==[0,0,0,0] and owner.get_survival_component().get_max_health()==state['health'])
            check('Constellation progression preserved',progress.get_skill_points()==skills and progress.get_unlocked_skill_count()==unlocked)
            check('Reset purse and balance persist',saved().get_editor_property('copper')==75001 and saved().get_editor_property('unspent_stat_points')==5)
            assert lib.send_verification_attribute_request(pc,[],state['reset_revision'],True); delay=1.5
        elif n==11:
            check('Reset replay cannot charge again',wallet.get_copper()==75001 and progress.get_unspent_points()==5)
            click('AttributePlus_HEALTH')
        elif n==12: progress.grant_experience(1); delay=1.5
        elif n==13:
            check('Server changes invalidate stale draft',ui().get_pending_attribute_total()==0 and progress.get_unspent_points()==5)
            ui().set_stat_focus(0); key('Right'); key('Enter'); delay=2
        elif n==14: wallet.set_copper(74999); delay=1.5
        elif n==15: click('ResetAttributePoints')
        elif n==16:
            check('Insufficient funds do not charge or confirm',not ui().is_attribute_reset_confirmation_open() and wallet.get_copper()==74999 and progress.get_stat_points(u.EWStat.VITALITY)==1)
            check('Oxygen and Intelligence stay unallocatable',not lib.is_verification_widget_enabled(ui(), 'AttributePlus_OXYGEN') and not lib.is_verification_widget_enabled(ui(), 'AttributePlus_INTELLIGENCE'))
            lib.resize_verification_play_viewport(world,1280,720); ui().set_stat_focus(0); delay=1.5
        elif n==17: key('Right'); shot('Attributes-Pending-1280x720'); key('Escape')
        elif n==18:
            check('720p cancellation works',ui().get_pending_attribute_total()==0 and progress.get_unspent_points()==4)
            finish(); return
        state['step'],state['at']=n+1,time.monotonic()+delay
    except Exception: finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
