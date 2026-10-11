"""Saved coastal map listen/client acceptance using owned interaction requests.
Only pawn positions and a hydration deficit are arranged in PIE; no item/recipe
grants, world replacements or saved map mutations occur.
"""
import json, time
from pathlib import Path
import unreal
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert len(worlds)==2 and all('Lvl_CoastalPlayground' in w.get_name() for w in worlds)
pcs=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
client=next(c for c in pcs if not c.has_authority())
local=worlds[pcs.index(client)]
server=next(w for w,c in zip(worlds,pcs) if c.has_authority())
def pid(p): return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
pawn=client.get_controlled_pawn()
owner=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWCharacter) if pid(a)==pid(pawn))
inv=owner.get_inventory_component()
wood=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
checks=[]; phase=0; next_at=time.monotonic()+1; handle=None
def peer(a): return next(x for x in unreal.GameplayStatics.get_all_actors_of_class(local,a.get_class()) if x.get_name()==a.get_name())
def face(a,xyz):
    for p in [owner,pawn]: assert p.teleport(unreal.Vector(*xyz),unreal.Rotator())
    eye=unreal.Vector(xyz[0],xyz[1],xyz[2]+64)
    rot=unreal.MathLibrary.find_look_at_rotation(eye,a.get_actor_location())
    owner.get_controller().set_control_rotation(rot); client.set_control_rotation(rot)
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(),'CoastalPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at,target
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0:
            assert len(inv.get_inventory_entries()) == 0 and len(inv.get_available_recipes()) == 0
            assert not owner.get_component_by_class(unreal.CharacterMovementComponent).is_falling()
            assert abs(owner.get_actor_location().z-96)<15
            checks.append('Both worlds load coastal map; client possesses survivor; beach spawn grounded with empty inventory and locked recipes')
            target=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWPickup) if a.get_editor_property('item_definition')==wood and a.get_actor_location().x==400)
            face(target,(270,-120,96))
        elif phase==1:
            assert lib.send_verification_interaction_request(client,peer(target))
        elif phase==2:
            assert inv.get_item_count(wood)==5
            assert pawn.get_inventory_component().get_item_count(wood)==5
            assert not unreal.SystemLibrary.is_valid(target)
            checks.append('Placed beach Wood transfers exactly five units through client request, replicates and consumes the world stack')
            target=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWWaterSource))
            owner.get_survival_component().set_hydration(40)
            face(target,(-1920,1500,110))
        elif phase==3:
            assert lib.send_verification_interaction_request(client,peer(target))
        elif phase==4:
            assert owner.get_survival_component().get_hydration()==100
            assert pawn.get_survival_component().get_hydration()==100
            checks.append('Placed freshwater spring restores hydration through client request and replicates')
            for p in [owner,pawn]: assert p.teleport(unreal.Vector(5600,900,140),unreal.Rotator())
        elif phase==5:
            assert not owner.get_component_by_class(unreal.CharacterMovementComponent).is_falling()
            assert 115<owner.get_actor_location().z<135
            assert len(inv.get_available_recipes()) == 0
            checks.append('Dock collision supports the survivor; gathering does not unlock intro-gated recipes')
            for p in [owner,pawn]: assert p.teleport(unreal.Vector(150,0,100),unreal.Rotator())
            client.set_control_rotation(unreal.Rotator(0,0,0))
            finish(); return
        phase+=1
    except Exception as e: finish(repr(e))
handle=unreal.register_slate_post_tick_callback(tick)

