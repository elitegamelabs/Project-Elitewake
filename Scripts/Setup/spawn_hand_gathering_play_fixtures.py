"""Opt-in finite fiber/stick pools in Lvl_M5PickupTest PIE. Never saves a map.
Resource quantities 10/6 and cube visuals are test tuning. Stop Play removes them.
"""
import unreal
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert worlds and all('Lvl_M5PickupTest' in w.get_name() for w in worlds)
server = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
cls = unreal.load_class(None, '/Script/EW.EWHandGatherable')
for a in unreal.GameplayStatics.get_all_actors_of_class(server, cls): a.destroy_actor()
fiber = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestFiber')
sticks = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestSticks')
assert fiber and sticks, 'Create the gathering test assets first'
assert lib.spawn_verification_hand_gatherable(server, unreal.Vector(120, 100, 160), fiber, 10)
assert lib.spawn_verification_hand_gatherable(server, unreal.Vector(120, -100, 160), sticks, 6, True)
unreal.log('Gather Fiber (left) / Collect Sticks (right): look within 250 cm and press E/X. Inspect trees/rocks still does not harvest.')
