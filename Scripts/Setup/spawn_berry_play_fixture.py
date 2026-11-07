"""One transient Azren bush cube in Lvl_M5PickupTest. E/X gathers; inventory R/X or hotbar eats.
Ten-unit pool and .01 kg unit weight are test tuning. Never saves a map.
"""
import unreal
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds()
assert worlds and all('Lvl_M5PickupTest' in w.get_name() for w in worlds)
server=next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w,0).has_authority())
berry=unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestAzulBerry'); assert berry
cls=unreal.load_class(None,'/Script/EW.EWHandGatherable')
for a in unreal.GameplayStatics.get_all_actors_of_class(server,cls):
    if a.get_editor_property('gathering_kind')==unreal.EWHandGatheringKind.BERRIES:a.destroy_actor()
node=lib.spawn_verification_hand_gatherable(server,unreal.Vector(120,100,160),berry,10)
assert node
node.set_editor_property('gathering_kind',unreal.EWHandGatheringKind.BERRIES); node.force_net_update()
unreal.log('Aim at the berry cube and press E/X. Inspect berries in inventory, then Eat (R/X) or assign a hotbar slot. Freshness lasts 20 real minutes. Stop Play removes the fixture.')
