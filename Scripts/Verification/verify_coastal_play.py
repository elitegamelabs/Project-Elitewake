"""Saved coastal map listen/client acceptance using owned interaction requests.
Only pawn positions and a hydration deficit are arranged in PIE; no item/recipe
grants, world replacements or saved map mutations occur. The map's test starter kit
is the only source of items.
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
axe=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenAxe')
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
            assert len(inv.get_available_recipes()) == 0
            # The starter supplies are the four core tools (owner, October 14).
            assert inv.get_item_count(axe)==1 and pawn.get_inventory_component().get_item_count(axe)==1
            assert not owner.get_component_by_class(unreal.CharacterMovementComponent).is_falling()
            checks.append('Both worlds load coastal map; client possesses survivor; beach spawn grounded with the starter tools replicated and recipes locked')
            target=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWWaterSource))
            owner.get_survival_component().set_hydration(40)
            at=target.get_actor_location(); out=unreal.Vector(at.x+1700,at.y-1500,0).normal()  # away from the pond's middle
            face(target,(at.x+out.x*120,at.y+out.y*120,at.z+100))
        elif phase==1:
            assert lib.send_verification_interaction_request(client,peer(target))
        elif phase==2:
            assert owner.get_survival_component().get_hydration()==100
            assert pawn.get_survival_component().get_hydration()==100
            checks.append('Placed freshwater spring restores hydration through client request and replicates')
            for p in [owner,pawn]: assert p.teleport(unreal.Vector(5600,900,140),unreal.Rotator())
        elif phase==3:
            assert not owner.get_component_by_class(unreal.CharacterMovementComponent).is_falling()
            assert 115<owner.get_actor_location().z<135
            assert len(inv.get_available_recipes()) == 0
            checks.append('Dock collision supports the survivor; the starter kit does not unlock intro-gated recipes')
            for p in [owner,pawn]: assert p.teleport(unreal.Vector(150,0,200),unreal.Rotator())
            client.set_control_rotation(unreal.Rotator(0,0,0))
            finish(); return
        phase+=1
    except Exception as e: finish(repr(e))
handle=unreal.register_slate_post_tick_callback(tick)

