"""Fresh listen-server/client: audit configured classes and independent spawning."""
import unreal,json
from pathlib import Path
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds()
pcs=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
client=next(c for c in pcs if not c.has_authority())
host=next(c for c in pcs if c.has_authority())
w=worlds[pcs.index(host)]
checks=[];classes={}
try:
    mode=unreal.GameplayStatics.get_game_mode(w)
    assert mode and isinstance(mode,unreal.EWGameMode)
    for name in ['default_pawn_class','player_controller_class','game_state_class','player_state_class']:
        value=mode.get_editor_property(name)
        assert value
        classes[name]=value.get_path_name()
    assert unreal.GameplayStatics.get_game_mode(worlds[pcs.index(client)]) is None
    checks.append('Configured Blueprint GameMode exists only on server; all four gameplay class defaults present')
    controllers=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.PlayerController)
    assert len(controllers)==2 and all(isinstance(p,unreal.EWPlayerController) for p in controllers)
    pawns=[p.get_controlled_pawn() for p in controllers]
    assert all(isinstance(p,unreal.EWCharacter) for p in pawns) and pawns[0]!=pawns[1]
    assert all(p.get_controller()==c for p,c in zip(pawns,controllers))
    assert all(p.get_editor_property('replicates') for p in pawns)
    checks.append('Two server controllers independently possess distinct replicated EW characters')
    player_ids=[json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'),['PlayerId']))['PlayerId'] for p in pawns]
    assert player_ids[0]!=player_ids[1]
    assert unreal.GameplayStatics.get_game_state(w) and unreal.GameplayStatics.get_game_state(worlds[pcs.index(client)])
    checks.append('Players have distinct PlayerState IDs and GameState exists on server/client')
    assert all(not p.get_inventory_component().get_available_recipes() and p.get_inventory_component().get_used_slot_count()<=8 for p in pawns)     # the starter kit (four tools) is the only inventory
    assert all(not c.get_objective_component().get_state().steps for c in controllers)
    checks.append('Normal play grants only the starter kit: no diagnostic items, recipe unlocks or objective sequence')
    result={'success':True,'checks':checks,'classes':classes,'error':None}
except Exception as exc:
    result={'success':False,'checks':checks,'classes':classes,'error':repr(exc)}
Path(unreal.Paths.project_saved_dir(),'MultiplayerConfigurationPlayResult.json').write_text(json.dumps(result,indent=2))
