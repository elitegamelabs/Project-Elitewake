"""Fresh single-player or listen-server/client Play; test input, replication and competing intents.

PIE-only fixtures, no saved inventory. Restores packet settings/throttling and removes callbacks.
"""
import unreal, json, os, traceback
worlds = unreal.EWEditorVerificationLibrary.get_play_worlds()
assert len(worlds) in (1,2)
controllers = [unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
server = next(w for w,c in zip(worlds,controllers) if c.has_authority())
network = len(worlds)==2
character_cls = unreal.load_class(None,'/Script/EW.EWCharacter')
pickup_cls = unreal.load_class(None,'/Script/EW.EWPickup')
item = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
assert item, 'M5C test item missing'
settings = unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground',False)
previous_network = []
for w in worlds:
    if network:
        previous_network.append((w,unreal.EWEditorVerificationLibrary.get_verification_network_settings(w)))
        unreal.EWEditorVerificationLibrary.set_verification_network_settings(w,100,1)
def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
owned = [c.get_controlled_pawn() for c in controllers]
ids = [pid(p) for p in owned]
def peers(w):
    return [p for p in unreal.GameplayStatics.get_all_actors_of_class(w,character_cls) if pid(p) in ids]
def inv(p): return p.get_inventory_component()
def counts(w): return {str(pid(p)):inv(p).get_item_count(item) for p in peers(w)}
server_pawns = {pid(p):p for p in peers(server)}
geometry = []
home = list(server_pawns.values())[0].get_actor_location()      # laid out from the survivor's own start, not from fixed map coordinates
for p in unreal.GameplayStatics.get_all_actors_of_class(server,pickup_cls): p.destroy_actor()
for w in worlds:
    for p in peers(w):
        y = -45 if pid(p)==ids[0] else 45
        p.teleport(unreal.Vector(home.x,home.y+y,home.z),unreal.Rotator())
        if p.has_authority(): inv(p).remove_item(item,100000)
for c in controllers: c.set_control_rotation(unreal.Rotator())
subsystems = [unreal.EWEditorVerificationLibrary.get_player_input_subsystem(c) for c in controllers]
actions = [c.get_editor_property('interact_action') for c in controllers]
active = False
stack = None
report = {'success':False,'network':network,'lag_ms':100 if network else 0,'loss_percent':1 if network else 0,'checkpoints':[],'errors':[]}
path = os.path.join(unreal.Paths.project_saved_dir(),'M5DPickupNetworkResult.json' if network else 'M5DPickupPlayResult.json')
def spawn(quantity, x=150):
    global stack
    if stack and unreal.SystemLibrary.is_valid(stack): stack.destroy_actor()
    # Each player's parallel forward ray intersects this wider fixture mesh.
    stack = unreal.EWEditorVerificationLibrary.spawn_verification_pickup(server,unreal.Vector(home.x+x,home.y,home.z+64),item,quantity)
    stack.set_actor_scale3d(unreal.Vector(1,5,2))
def press():
    global active
    active=True
def release():
    global active
    active=False
def check(label,total,remaining):
    rows = [counts(w) for w in worlds]
    report['checkpoints'].append({'label':label,'inventory_by_world':rows,'remaining':stack.get_editor_property('quantity') if unreal.SystemLibrary.is_valid(stack) else 0})
    assert all(sum(r.values())==total for r in rows), label+': wrong inventory total'
    assert all(r==rows[0] for r in rows), label+': inventory replication differs'
    pickups = [unreal.GameplayStatics.get_all_actors_of_class(w,pickup_cls) for w in worlds]
    assert all(sum(p.get_editor_property('quantity') for p in ps)==remaining for ps in pickups),label+': world remainder replication differs'
def fill():
    for p in server_pawns.values(): inv(p).add_item(item,5997)
def free_capacity():
    for p in server_pawns.values(): inv(p).remove_item(item,10)
def empty():
    for p in server_pawns.values(): inv(p).remove_item(item,100000)
n=len(ids)
steps=[(lambda:spawn(10,450),1),(press,.2),(release,1.5),(lambda:check('out of range',0,10),.1),
       (lambda:spawn(10),1),(press,.2),(release,1.5),(lambda:check('competing pickup conserved',10,0),.1),
       (empty,.5),(fill,1),(lambda:spawn(10),1),(press,.2),(release,1.5),
       (lambda:check('partial capacity',6000*n,10-3*n),.1),
       (press,.2),(release,1.5),(lambda:check('full inventory preserves remainder',6000*n,10-3*n),.1),
       (free_capacity,1),(press,.2),(release,1.5),
       (lambda:check('remainder collected once',6000*n-10*n+10-3*n,0),.1)]
index=0
next_time=unreal.GameplayStatics.get_time_seconds(server)+1
handle=None
def finish():
    release()
    for a in geometry:
        if unreal.SystemLibrary.is_valid(a): a.destroy_actor()
    if stack and unreal.SystemLibrary.is_valid(stack): stack.destroy_actor()
    for w,old in previous_network:
        if w in unreal.EWEditorVerificationLibrary.get_play_worlds():
            unreal.EWEditorVerificationLibrary.set_verification_network_settings(w,old.x,old.y)
    settings.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
    report['success']=not report['errors'] and index==len(steps)
    with open(path,'w') as f: json.dump(report,f,indent=2)
    unreal.unregister_slate_post_tick_callback(handle)
def tick(delta):
    global index,next_time
    try:
        if any(w not in unreal.EWEditorVerificationLibrary.get_play_worlds() for w in worlds):
            raise RuntimeError('Play ended before verification completed')
        if active:
            for s,a in zip(subsystems,actions): s.inject_input_vector_for_action(a,unreal.Vector(1,0,0),[],[])
        now=unreal.GameplayStatics.get_time_seconds(server)
        if now<next_time:return
        if index==len(steps):finish();return
        action,wait=steps[index];action();index+=1;next_time=now+wait
    except Exception:
        report['errors'].append(traceback.format_exc());finish()
handle=unreal.register_slate_post_tick_callback(tick)
