"""Fresh listen-server/client Play: authored-icon identity across inventory and material rows."""
import unreal,json,time
from pathlib import Path
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds()
pcs=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
client=next(c for c in pcs if not c.has_authority())
server_world=next(w for w,c in zip(worlds,pcs) if c.has_authority())
client_world=worlds[pcs.index(client)]
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
owner=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world,unreal.EWCharacter) if pid(p)==pid(client.get_controlled_pawn()))
inv=owner.get_inventory_component()
material=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestIconMaterial')
output=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestIconOutput')
texture=unreal.load_asset('/Engine/EngineResources/DefaultTexture')
recipe=unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipeIconCheck')
assert material and output and recipe and texture
assert inv.add_item(material,1)==1 and inv.unlock_recipe(recipe)
phase=0;next_at=time.monotonic()+2;checks=[];handle=None
def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world,unreal.EWInventoryWidget,False) if w.get_owning_player()==client and w.is_in_viewport())
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(),'ItemIconsPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0: client.set_inventory_open(True)
        elif phase==1:
            assert menu().get_displayed_inventory_icon(material)==texture
            checks.append('Inventory renders the assigned item texture')
            assert lib.send_verification_ui_key(client,'Tab')
        elif phase==2:
            assert menu().get_displayed_material_icon(material)==texture
            checks.append('Crafting material uses identical authored texture')
            assert menu().is_craft_action_enabled()
            assert lib.send_verification_ui_key(client,'Enter')
        elif phase==3:
            assert inv.get_item_count(output)==1 and inv.get_item_count(material)==0
            assert lib.send_verification_ui_key(client,'PageUp')
        elif phase==4:
            assert menu().get_displayed_inventory_icon(output)==texture
            assert menu().get_displayed_inventory_icon(material) is None
            checks.append('Crafted output renders assigned texture; consumed item image is cleared')
            finish();return
        phase+=1
    except Exception as exc: finish(f'Phase {phase}: {exc!r}')
handle=unreal.register_slate_post_tick_callback(tick)
