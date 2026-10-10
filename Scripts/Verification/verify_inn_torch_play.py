"""Fresh in-process listen-server/client Play; tests per-player torch and local HUD. PIE-only state."""
import unreal,json,time
from pathlib import Path
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds()
pcs=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
client=next(c for c in pcs if not c.has_authority())
host=next(c for c in pcs if c.has_authority())
server_world=worlds[pcs.index(host)]
client_world=worlds[pcs.index(client)]
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
owner=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world,unreal.EWCharacter) if pid(p)==pid(client.get_controlled_pawn()))
host_pawn=host.get_controlled_pawn()
base=owner.get_actor_location()
host_pawn.set_actor_location(base+unreal.Vector(-1000,500,0),False,True)
client.set_control_rotation(unreal.Rotator());host.set_control_rotation(unreal.Rotator())
eye,_=owner.get_actor_eyes_view_point()
item=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestInnTorch')
torch=lib.spawn_verification_inn_torch(server_world,eye+unreal.Vector(150,0,0),item)
assert torch
wood=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
inv=owner.get_inventory_component()
remote=client.get_controlled_pawn().get_inventory_component()
phase=0;next_at=time.monotonic()+3;checks=[];handle=None
replacement=None
server_pc=owner.get_controller()
def ui():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world,unreal.EWInteractionWidget,False) if w.get_owning_player()==client)
def local_torch(): return unreal.GameplayStatics.get_all_actors_of_class(client_world,unreal.EWInnTorchPickup)[0]
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    if replacement:
        server_pc.possess(owner)
        replacement.destroy_actor()
    Path(unreal.Paths.project_saved_dir(),'InnTorchPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at,replacement
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0:
            assert str(ui().get_inn_message())=='ye, this looks like it will be useful'
            assert ui().get_highlighted_torch_count()==1
            checks.append('Exact intro message and highlight appear on client')
            client.set_control_rotation(unreal.Rotator(0,90,0))
        elif phase==1:
            assert ui().get_highlighted_torch_count()==1 and str(ui().get_inn_message())==''
            checks.append('Highlight persists after looking away')
            client.set_control_rotation(unreal.Rotator())
            assert inv.add_item(wood,6000)==6000
        elif phase==2:
            assert lib.send_verification_interaction_request(client,local_torch(),False)
        elif phase==3:
            assert not torch.has_collected(owner) and inv.get_item_count(item)==0
            checks.append('Full inventory preserves entitlement')
            inv.remove_item(wood,6000)
        elif phase==4:
            assert lib.send_verification_interaction_request(client,local_torch(),False)
        elif phase==5:
            assert torch.has_collected(owner) and remote.get_item_count(item)==1
            assert ui().get_highlighted_torch_count()==0
            assert not local_torch().mesh.is_visible()
            checks.append('Client gets one torch; local mesh and highlight disappear')
            assert lib.send_verification_interaction_request(client,local_torch(),False)
        elif phase==6:
            assert inv.get_item_count(item)==1 and not torch.has_collected(host_pawn)
            checks.append('Repeat cannot duplicate; host entitlement remains')
            owner.set_actor_location(base+unreal.Vector(-1000,-500,0),False,True)
            host_pawn.set_actor_location(base,False,True)
        elif phase==7:
            assert lib.send_verification_interaction_request(host,torch,False)
        elif phase==8:
            assert torch.has_collected(host_pawn) and host_pawn.get_inventory_component().get_item_count(item)==1
            assert inv.get_item_count(item)==1
            checks.append('Same wall actor grants independently to both players')
            host_pawn.set_actor_location(base+unreal.Vector(-1000,500,0),False,True)
            replacement=lib.spawn_verification_recipe_character(server_world,owner.get_class(),base,[])
            assert replacement
            server_pc.possess(replacement)
        elif phase==9:
            assert torch.has_collected(replacement)
            assert not local_torch().mesh.is_visible()
            assert str(ui().get_inn_message())=='' and ui().get_highlighted_torch_count()==0
            assert lib.send_verification_interaction_request(client,local_torch(),False)
        elif phase==10:
            assert replacement.get_inventory_component().get_item_count(item)==0
            assert client.get_controlled_pawn().get_inventory_component().get_item_count(item)==0
            checks.append('Replacement pawn retains session entitlement and cannot collect a second torch')
            finish();return
        phase+=1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}; server_collected={torch.has_collected(owner)}, server_count={inv.get_item_count(item)}, client_count={remote.get_item_count(item)}, highlights={ui().get_highlighted_torch_count()}, local_visible={local_torch().mesh.is_visible()}')
handle=unreal.register_slate_post_tick_callback(tick)
