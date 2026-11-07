"""Opt-in Repair Kit client-menu acceptance in fresh listen/client PIE.
Only this temporary test grants knowledge/materials; no map or default changes.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
local = next(w for w in worlds if not unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
client = unreal.GameplayStatics.get_player_controller(local, 0)
server = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
def pid(pawn):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(pawn.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']
owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server, unreal.EWCharacter)
             if pid(p) == pid(client.get_controlled_pawn()))
host = unreal.GameplayStatics.get_player_controller(server, 0).get_controlled_pawn().get_inventory_component()
inv = owner.get_inventory_component()
remote = client.get_controlled_pawn().get_inventory_component()
recipe = unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipePrologueRepairKit')
recipe.set_editor_property('craft_seconds', 0.2)  # crafting takes seconds now; these checks are about what it makes (verify_craft_time_play times it)
assert recipe
output = recipe.get_editor_property('output')
costs = recipe.get_editor_property('ingredients')
wood, stone = [c.get_editor_property('item') for c in costs]
assert [c.get_editor_property('quantity') for c in costs] == [20, 20]
for _who in (inv, host):      # the starter kit is not what this check is about
    for _e in list(_who.get_inventory_entries()):
        _who.remove_item(_e.get_editor_property('item_definition'), _e.get_editor_property('quantity'))
assert not inv.get_inventory_entries() and not inv.get_available_recipes()
assert not host.get_inventory_entries() and not host.get_available_recipes()
checks = ['Normal test-world starts remain empty without automatic Repair Kit or starter knowledge',
          'Saved recipe costs are exactly 20 Wood and 20 Stone']
assert inv.unlock_recipe(recipe)
assert inv.add_item(wood, 19) == 19 and inv.add_item(stone, 19) == 19
phase = 0
started = time.monotonic()
next_at = started + 3
handle = None
def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(local, unreal.EWInventoryWidget, False)
                if w.get_owning_player() == client and w.is_in_viewport())
def counts(w, s, kit):
    for inventory in (inv, remote):
        assert inventory.get_item_count(wood) == w
        assert inventory.get_item_count(stone) == s
        assert inventory.get_item_count(output) == kit
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(), 'PrologueRepairRecipePlayResult.json').write_text(json.dumps({
        'success': error is None, 'checks': checks, 'error': error,
        'scope': 'Opt-in client menu transaction and replication only; not prologue unlock/event, repair use, art or balance'
    }, indent=2), encoding='utf-8')
def tick(delta):
    global phase, next_at
    if time.monotonic() - started > 50:
        finish('Timed out at phase ' + str(phase)); return
    if time.monotonic() < next_at: return
    next_at = time.monotonic() + 2
    try:
        if phase == 0:
            assert remote.get_available_recipes() == [recipe]
            client.set_inventory_open(True)
            menu().focus_crafting()
        elif phase == 1:
            counts(19, 19, 0)
            assert not menu().is_craft_action_enabled()
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 2:
            counts(19, 19, 0)
            checks.append('Both ingredient shortages disable crafting and preserve materials/output')
            assert inv.add_item(wood, 1) == 1
        elif phase == 3:
            counts(20, 19, 0)
            assert not menu().is_craft_action_enabled()
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 4:
            counts(20, 19, 0)
            checks.append('Stone shortage still prevents crafting with enough Wood; no partial consumption')
            assert inv.add_item(stone, 1) == 1
        elif phase == 5:
            counts(20, 20, 0)
            assert menu().is_craft_action_enabled()
            checks.append('Replicated complete ingredients enable the client Craft action')
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 6:
            counts(0, 0, 1)
            checks.append('Owned client menu consumes exactly 20 Wood + 20 Stone and replicates one Repair Kit')
            assert not menu().is_craft_action_enabled()
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 7:
            counts(0, 0, 1)
            assert not host.get_inventory_entries() and not host.get_available_recipes()
            assert remote.get_available_recipes() == [recipe]
            checks.append('Unaffordable repeat grants nothing; host remains independent and regular starter recipes remain locked')
            finish(); return
        phase += 1
    except Exception as exc:
        finish('Phase ' + str(phase) + ': ' + repr(exc))
handle = unreal.register_slate_post_tick_callback(tick)
