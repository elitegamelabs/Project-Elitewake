"""PIE-only tree and hatchet pickup in Lvl_M5PickupTest; never saves a map.
Pick up the hatchet with E/X, equip MainHand through inventory/hotbar, then
aim at the other cube and click Left Mouse/RT. Test pools 12 Wood/4 Thatch,
per-strike 3/1 and one-second admission are draft tuning. Bare hands disabled.
"""
import unreal
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert worlds and all('Lvl_M5PickupTest' in w.get_name() for w in worlds)
server = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w,0).has_authority())
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
thatch = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestThatch')
hatchet = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestHatchet')
assert wood and thatch and hatchet
tree_cls = unreal.load_class(None,'/Script/EW.EWHarvestTree')
for a in unreal.GameplayStatics.get_all_actors_of_class(server,tree_cls): a.destroy_actor()
assert lib.spawn_verification_harvest_tree(server,unreal.Vector(120,100,160),wood,thatch)
assert lib.spawn_verification_pickup(server,unreal.Vector(120,-100,160),hatchet,1)
unreal.log('Hatchet pickup and tree are opt-in cubes. E/X collects the tool; Left Mouse/RT harvests after MainHand equip. Stop Play removes fixtures.')
