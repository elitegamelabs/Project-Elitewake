"""Opt-in fresh-water test surface in Lvl_M5PickupTest PIE. Never saves a map.

Lowers test survivors' hydration to 25%; normal gameplay has no automatic test grant.
Blue debug bounds identify the query surface; production ponds provide their own visuals.
Stop Play removes all fixtures and test state.
"""
import unreal

lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
assert worlds and all('Lvl_M5PickupTest' in w.get_name() for w in worlds), 'Start Play in Lvl_M5PickupTest first'
server = next(w for w in worlds if unreal.GameplayStatics.get_player_controller(w, 0).has_authority())
water_cls = unreal.load_class(None, '/Script/EW.EWWaterSource')
character_cls = unreal.load_class(None, '/Script/EW.EWCharacter')
for a in unreal.GameplayStatics.get_all_actors_of_class(server, water_cls): a.destroy_actor()
source = lib.spawn_verification_water_source(server, unreal.Vector(120, 100, 160))
assert source
for p in unreal.GameplayStatics.get_all_actors_of_class(server, character_cls): p.get_survival_component().set_hydration(25)
for w in worlds:
    unreal.SystemLibrary.draw_debug_box(w, unreal.Vector(120, 100, 160), unreal.Vector(50, 50, 10),
                                       unreal.LinearColor(0, .6, 1, 1), duration=600, thickness=2)
unreal.log('Fresh-water test surface: blue bounds at (120, 100, 160). Look within 250 cm and press E/X. Stop Play to remove.')
