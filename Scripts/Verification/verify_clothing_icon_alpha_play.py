"""Real Inventory/recipe icons over a bright shore and a dim ship deck, at 1080p and 720p.
PIE-only inventories, light settings and teleports; no saves, equipment mutations or map edits.
"""
import json
import time
import traceback
from pathlib import Path
import unreal as u

lib = u.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = u.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
pack = pawn.get_inventory_component()
names = ['ClothHeadWrap','ClothChest','ClothPants','FurHood','FurJacket','FurPants',
         'MetalTricornHelmet','MetalCuirass','MetalPants']
items = [u.load_asset('/Game/Elitewake/Items/Armor/DA_'+n) for n in names]
for entry in list(pack.get_inventory_entries()):
    pack.remove_item(entry.get_editor_property('item_definition'), entry.get_editor_property('quantity'))
for name, item in zip(names, items):
    pack.add_item(item, 1)
    pack.unlock_recipe(u.load_asset('/Game/Elitewake/Crafting/Testing/DA_Recipe'+name))
out = Path(u.Paths.project_saved_dir(),'Screenshots','ClothingIconAlpha')
out.mkdir(parents=True,exist_ok=True)
report = dict(success=False,checks=[],runtime_textures={},error=None)
state = dict(step=0,at=time.monotonic()+1,lights=[])
result = Path(u.Paths.project_saved_dir(),'ClothingIconAlphaPlayResult.json')
def ui():
    return next(w for w in u.WidgetLibrary.get_all_widgets_of_class(world,u.EWInventoryWidget,False)
                if w.is_in_viewport() and w.get_owning_player()==pc)
def check(label, condition):
    report['checks'].append(dict(check=label,passed=bool(condition)))
    assert condition,label
def shot(name):
    assert lib.capture_verification_play_viewport(world,str(out/(name+'.png')))
def finish(error=None):
    for light, intensity in state['lights']:
        if u.SystemLibrary.is_valid(light): light.set_intensity(intensity)
    if 'exposure' in state: u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality '+str(state['exposure']))
    pc.set_inventory_open(False)
    report['error'],report['success']=error,error is None
    result.write_text(json.dumps(report,indent=2))
    u.unregister_slate_post_tick_callback(handle)
def tick(_):
    if time.monotonic()<state['at']:return
    try:
        n,delay=state['step'],.6
        if n==0:
            lib.resize_verification_play_viewport(world,1920,1080)
            pc.set_inventory_open(True)
            pc.set_control_rotation(u.Rotator(pitch=-9,yaw=0))
            delay=1.5
        elif n==1:
            check('All nine real clothing items shown',ui().get_shown_item_count()==9)
            check('All nine real recipe outputs shown',ui().get_shown_recipe_count()==9)
            for name,item in zip(names,items):
                expected=u.load_asset('/Game/Elitewake/UI/Icons/Armor/T_Icon_'+name)
                check(name+' keeps original texture reference',ui().get_displayed_inventory_icon(item)==expected)
                size=[expected.blueprint_get_size_x(),expected.blueprint_get_size_y()]
                report['runtime_textures'][name]=size
                check(name+' stays within 256-pixel UI texture limit',max(size)<=256)
            shot('Clothing-Icons-Bright-Shore-1920x1080')
            state['time']=u.GameplayStatics.get_time_seconds(world)
            lib.resize_verification_play_viewport(world,1280,720)
            delay=1.5
        elif n==2:
            shot('Clothing-Icons-Bright-Shore-1280x720')
            check('World continues running behind Inventory',u.GameplayStatics.get_time_seconds(world)>state['time']+.5)
            lib.resize_verification_play_viewport(world,1920,1080)
            pawn.set_first_person_view(True)
            state['exposure']=u.SystemLibrary.get_console_variable_int_value('r.EyeAdaptationQuality')
            u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0')
            for actor_class,component_class in ((u.DirectionalLight,u.DirectionalLightComponent),(u.SkyLight,u.SkyLightComponent)):
                for actor in u.GameplayStatics.get_all_actors_of_class(world,actor_class):
                    component=actor.get_component_by_class(component_class)
                    if component:
                        value=component.get_editor_property('intensity')
                        state['lights'].append((component,value))
                        component.set_intensity(value*.015)
            ship=next(s for s in u.GameplayStatics.get_all_actors_of_class(world,u.EWShip)
                      if s.get_editor_property('definition') and str(s.get_editor_property('definition').get_editor_property('ship_id'))=='Sloop')
            at=ship.get_actor_transform().transform_location(u.Vector(-150,0,ship.get_deck_height()+98))
            assert pawn.teleport(at,ship.get_actor_rotation())
            pc.set_control_rotation(u.Rotator(pitch=-11,yaw=ship.get_actor_rotation().yaw))
            check('Dim view uses real ship deck and scene lights',len(state['lights'])>0)
            delay=2
        elif n==3:
            shot('Clothing-Icons-Dim-Deck-1920x1080')
            lib.resize_verification_play_viewport(world,1280,720)
            delay=1.5
        elif n==4:
            shot('Clothing-Icons-Dim-Deck-1280x720')
            check('720p Inventory keeps all nine icon references',all(ui().get_displayed_inventory_icon(item) for item in items))
        elif n==5:
            finish();return
        state['step'],state['at']=n+1,time.monotonic()+delay
    except Exception:finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
