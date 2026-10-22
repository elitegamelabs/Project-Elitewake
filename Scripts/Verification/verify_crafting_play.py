"""Opt-in listen-server/client crafting menu smoke check. PIE-only grants/unlocks.
Start listen-server plus one in-process client first; results under Saved.
"""
import unreal, time, json
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
client_world = next(w for w in worlds if not unreal.GameplayStatics.get_player_controller(w,0).has_authority())
client = unreal.GameplayStatics.get_player_controller(client_world,0)
server_world = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w,0).has_authority())
def player_id(pawn):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(pawn.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world,unreal.EWCharacter)
             if player_id(p)==player_id(client.get_controlled_pawn()))
inv = owner.get_inventory_component()
remote = client.get_controlled_pawn().get_inventory_component()
recipes = [unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_Recipe'+n)
           for n in ['WoodenShovel','WoodenAxe','WoodenPickaxe','HideWaterFlask']]
assert all(recipes)
for recipe in recipes[:3]:
    costs=recipe.get_editor_property('ingredients')
    assert len(costs)==1 and costs[0].get_editor_property('quantity')==20
flask_costs=recipes[3].get_editor_property('ingredients')
assert [c.get_editor_property('quantity') for c in flask_costs]==[1,10]
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
output = recipes[0].get_editor_property('output')
outputs = [r.get_editor_property('output') for r in recipes]
hide = flask_costs[0].get_editor_property('item')
base = [inv.get_item_count(o) for o in outputs]   # the starter kit already carries some of these tools
thatch = flask_costs[1].get_editor_property('item')
for r in recipes:
    r.set_editor_property('craft_seconds', 0.2)   # the timing has its own check (verify_craft_time_play)
    assert inv.unlock_recipe(r)
phase = 0
started = time.monotonic()
next_at = started + 2
handle = None
checks = ['Saved starter recipe quantities match owner decisions']
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(),'CraftingPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0:
            assert len(remote.get_available_recipes())==4
            checks.append('Client receives four unlocked recipes')
            client.set_inventory_open(True)
            assert lib.send_verification_ui_key(client,'Tab')
        elif phase==1:
            menu=next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world,unreal.EWInventoryWidget,False)
                      if w.get_owning_player()==client and w.is_in_viewport())
            assert not menu.is_craft_action_enabled()
            checks.append('Missing ingredients disable client Craft action')
            assert lib.send_verification_ui_key(client,'Enter')
        elif phase==2:
            assert inv.get_item_count(output)==0 and remote.get_item_count(output)==0
            checks.append('Menu craft with missing ingredients grants nothing')
            assert inv.add_item(wood,20)==20
        elif phase==3:
            assert remote.get_item_count(wood)==20
            menu=next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world,unreal.EWInventoryWidget,False)
                      if w.get_owning_player()==client and w.is_in_viewport())
            assert menu.is_craft_action_enabled()
            checks.append('Replicated materials enable client Craft action')
            assert lib.send_verification_ui_key(client,'Enter')
        elif phase==4:
            assert inv.get_item_count(wood)==0 and inv.get_item_count(output)==1
            assert remote.get_item_count(wood)==0 and remote.get_item_count(output)==1
            checks.append('Menu request consumes 20 Wood and replicates exactly one shovel')
            assert inv.add_item(wood,40)==40
            assert inv.add_item(hide,1)==1
            assert inv.add_item(thatch,10)==10
        elif phase==5:
            assert lib.send_verification_ui_key(client,'Down')
            assert lib.send_verification_ui_key(client,'Enter')
        elif phase==6:
            assert inv.get_item_count(outputs[1])==base[1]+1 and remote.get_item_count(outputs[1])==base[1]+1
            assert inv.get_item_count(wood)==20 and remote.get_item_count(wood)==20
            checks.append('Wooden Axe consumes 20 Wood and replicates one output')
            assert lib.send_verification_ui_key(client,'Down')
            assert lib.send_verification_ui_key(client,'Enter')
        elif phase==7:
            assert inv.get_item_count(outputs[2])==base[2]+1 and remote.get_item_count(outputs[2])==base[2]+1
            assert inv.get_item_count(wood)==0 and remote.get_item_count(wood)==0
            checks.append('Wooden Pickaxe consumes 20 Wood and replicates one output')
            assert lib.send_verification_ui_key(client,'Down')
            assert lib.send_verification_ui_key(client,'Enter')
        elif phase==8:
            assert inv.get_item_count(outputs[3])==base[3]+1 and remote.get_item_count(outputs[3])==base[3]+1
            assert inv.get_item_count(hide)==0 and remote.get_item_count(hide)==0
            assert inv.get_item_count(thatch)==0 and remote.get_item_count(thatch)==0
            checks.append('Hide Water Flask consumes 1 Hide and 10 Thatch and replicates one output')
            assert lib.send_verification_ui_key(client,'PageUp')
            checks.append('Returns to inventory')
            finish();return
        phase+=1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r} wood={inv.get_item_count(wood)}/{remote.get_item_count(wood)} outputs={[inv.get_item_count(o) for o in outputs]} hide={inv.get_item_count(hide)} thatch={inv.get_item_count(thatch)}')
handle=unreal.register_slate_post_tick_callback(tick)
