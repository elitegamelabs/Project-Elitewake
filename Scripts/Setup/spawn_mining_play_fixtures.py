"""PIE-only stone/ore cubes and pickaxe pickup in Lvl_M5PickupTest.
E/X picks up the tool; equip MainHand then Left Mouse/RT mines. No map saves.
Pools 12 and yields 3 are draft tuning; no animations, durability or regrowth.
"""
import unreal
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert worlds and all('Lvl_M5PickupTest' in w.get_name() for w in worlds)
server = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w,0).has_authority())
stone = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestStone')
ore = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestOre')
pickaxe = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestPickaxe')
assert stone and ore and pickaxe
cls = unreal.load_class(None,'/Script/EW.EWMineable')
for a in unreal.GameplayStatics.get_all_actors_of_class(server,cls): a.destroy_actor()
assert lib.spawn_verification_mineable(server,unreal.Vector(120,100,160),stone)
assert lib.spawn_verification_mineable(server,unreal.Vector(120,-100,160),ore)
assert lib.spawn_verification_pickup(server,unreal.Vector(100,0,160),pickaxe,1)
unreal.log('Stone/ore nodes and pickaxe pickup are transient cubes. Equip the pickaxe in MainHand and Attack a node. Stop Play removes fixtures.')
