"""Opt-in fixtures in fresh Lvl_M5PickupTest Play. Nothing is saved to a map.

Campfire uses a one-second draft hold; Smithy, Tree and Rock use Press.
All only acknowledge Inspect. Stop Play to remove them. No production content or yields.
"""
import unreal

lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert worlds, 'Start Play in Lvl_M5PickupTest first'
server = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w,0).has_authority())
assert 'Lvl_M5PickupTest' in server.get_path_name(), 'Fixtures are restricted to the isolated test map'
station_cls = unreal.load_class(None, '/Script/EW.EWStation')
for actor in unreal.GameplayStatics.get_all_actors_of_class(server, station_cls): actor.destroy_actor()
campfire = lib.spawn_verification_interactable(server, unreal.Vector(120,0,160), False, True)
smithy = lib.spawn_verification_interactable(server, unreal.Vector(200,100,160))
smithy.set_editor_property('station_type',unreal.EWStationType.SMITHY)
tree = lib.spawn_verification_interactable(server, unreal.Vector(200,-100,160), True)
rock = lib.spawn_verification_interactable(server, unreal.Vector(100,200,160), True)
rock.set_editor_property('resource_type',unreal.EWResourceNodeType.ROCK)
unreal.log('PIE-only Inspect fixtures spawned: Campfire (hold), Smithy, Tree and Rock. No crafting or harvesting.')
