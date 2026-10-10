"""Fresh listen-server/client Play. Deferred fixture authoring exercises real BeginPlay and possession."""
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
original=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world,unreal.EWCharacter) if pid(p)==pid(client.get_controlled_pawn()))
server_pc=original.get_controller()
assert not original.get_inventory_component().get_available_recipes()
recipes=[unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_Recipe'+n) for n in ['WoodenShovel','WoodenAxe','WoodenPickaxe','HideWaterFlask']]
assert all(recipes)
fixture=lib.spawn_verification_recipe_character(server_world,original.get_class(),original.get_actor_location()+unreal.Vector(250,0,0),recipes+[recipes[0],None])
assert fixture
inventory=fixture.get_inventory_component()
assert len(inventory.get_available_recipes())==4
assert inventory.get_used_slot_count()==0
server_pc.possess(fixture)
phase=0;next_at=time.monotonic()+3;checks=['Real BeginPlay grants four unique recipes and no finished items'];handle=None
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    server_pc.possess(original)
    fixture.destroy_actor()
    Path(unreal.Paths.project_saved_dir(),'StartingRecipesPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0:
            remote=client.get_controlled_pawn().get_inventory_component()
            assert len(remote.get_available_recipes())==4 and remote.get_used_slot_count()==0
            assert not host.get_controlled_pawn().get_inventory_component().get_available_recipes()
            checks.append('Possessed client receives only its authored recipes, with no inventory grant')
            client.set_inventory_open(True)
            assert lib.send_verification_ui_key(client,'Tab')
        elif phase==1:
            ui=next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world,unreal.EWInventoryWidget,False) if w.get_owning_player()==client and w.is_in_viewport())
            assert not ui.is_craft_action_enabled()
            checks.append('Fresh character menu requires ingredients despite baseline unlocks')
            finish();return
        phase+=1
    except Exception as exc: finish(f'Phase {phase}: {exc!r}')
handle=unreal.register_slate_post_tick_callback(tick)
