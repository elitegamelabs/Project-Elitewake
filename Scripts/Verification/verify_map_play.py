"""Fresh listen-server/client local map capture and input/lifecycle checks."""
import unreal,json,time
from pathlib import Path
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds();pcs=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
c=next(p for p in pcs if not p.has_authority());host=next(p for p in pcs if p.has_authority())
cw=worlds[pcs.index(c)];sw=worlds[pcs.index(host)]
def pid(p):return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
owner=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(sw,unreal.EWCharacter) if pid(p)==pid(c.get_controlled_pawn()))
server_pc=owner.get_controller();pawn=c.get_controlled_pawn()
base=pawn.get_actor_location();start_world=unreal.GameplayStatics.get_time_seconds(cw)
checks=[];phase=0;handle=None;next_at=time.monotonic()+3
assert not c.is_map_open()
assert lib.send_verification_gameplay_key(c,'M')
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    lib.send_verification_gameplay_key(c,'M') if c.is_map_open() else None
    c.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(),'MapPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at
    if phase==1:pawn.add_movement_input(unreal.Vector(1,0,0),1)
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0:
            assert c.is_map_open() and server_pc.is_map_open() and not host.is_map_open()
            ui=next(x for x in unreal.WidgetLibrary.get_all_widgets_of_class(cw,unreal.EWMapWidget,False) if x.get_owning_player()==c and x.is_in_viewport())
            assert ui.has_map_capture()
            assert len(unreal.GameplayStatics.get_all_actors_of_class(cw,unreal.SceneCapture2D))==1
            assert not unreal.GameplayStatics.get_all_actors_of_class(sw,unreal.SceneCapture2D)
            assert not c.is_move_input_ignored() and c.is_look_input_ignored()
            checks.append('M opens a local-only capture; server sees menu state; host unaffected')
            c.set_inventory_open(True);assert not any(x.is_in_viewport() and x.get_owning_player()==c for x in unreal.WidgetLibrary.get_all_widgets_of_class(cw,unreal.EWInventoryWidget,False))
            assert lib.send_verification_gameplay_key(c,'C') and lib.send_verification_gameplay_key(c,'LeftShift')
            checks.append('Map blocks inventory, stance and sprint keys while retaining walking input')
        elif phase==1:
            assert (pawn.get_actor_location()-base).length()>15
            assert unreal.GameplayStatics.get_time_seconds(cw)>start_world+2
            ui=next(x for x in unreal.WidgetLibrary.get_all_widgets_of_class(cw,unreal.EWMapWidget,False) if x.is_in_viewport())
            assert (ui.get_map_center()-pawn.get_actor_location()).length()<350
            checks.append('Walking and world time continue; map follows local player')
            assert lib.send_verification_gameplay_key(c,'M')
        elif phase==2:
            assert not c.is_map_open() and not server_pc.is_map_open()
            assert not c.is_look_input_ignored() and not c.is_move_input_ignored()
            assert not unreal.GameplayStatics.get_all_actors_of_class(cw,unreal.SceneCapture2D)
            checks.append('M closes and destroys capture; input restrictions clear')
            c.set_inventory_open(True)
            assert lib.send_verification_ui_key(c,'M')
        elif phase==3:
            assert c.is_map_open() and not any(x.is_in_viewport() and x.get_owning_player()==c for x in unreal.WidgetLibrary.get_all_widgets_of_class(cw,unreal.EWInventoryWidget,False))
            checks.append('M switches inventory into map without leaving inventory input locks')
            assert lib.send_verification_gameplay_key(c,'M')
        elif phase==4:
            for i in range(5):
                assert lib.send_verification_gameplay_key(c,'M');assert lib.send_verification_gameplay_key(c,'M')
            assert not c.is_map_open() and not c.is_look_input_ignored()
            checks.append('Repeated open/close leaves no persistent input lock')
            finish();return
        phase+=1
    except Exception as exc:finish(f'Phase {phase}: {exc!r}')
handle=unreal.register_slate_post_tick_callback(tick)
